"""External observers plus diagnostic-label-only removal overlay.

Selection masks, FPM/SANA, queues, losses, optimizer steps and ordering remain
official code. Stable IDs come from actual batch lengths, never native offset.
"""
import difflib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
import torch
from phase_c_run import OFFICIAL, REPORT, state_hash


class Audit:
    def __init__(self,mode,tag):
        self.mode,self.tag = mode,tag
        self.offset = 0
        self.queues = {'hard':[],'moderate':[]}
        self.candidates = {'hard':[],'moderate':[]}
        self.events,self.losses,self.steps,self.batches = [],[],[],[]
        self.seen_updates = set()
        self.score_pending = False
        self.last_scores = None

    def install(self,predictor):
        source_path = OFFICIAL/'tta/candi/adapter_candi.py'
        source = source_path.read_text()
        removed = ('self.test_labels = kwargs[', 'selected_labels_hard = self.test_labels[',
                   'selected_labels_moderate = self.test_labels[', 'self.total_anomalies_in_hard +=',
                   'self.total_anomalies_in_moderate +=')
        isolated = ''.join(line for line in source.splitlines(keepends=True) if not any(s in line for s in removed))
        directory = REPORT/'overlays'
        directory.mkdir(parents=True,exist_ok=True)
        path = directory/'adapter_labels_isolated.py'
        path.write_text(isolated)
        (directory/'label_isolation.patch').write_text(''.join(difflib.unified_diff(source.splitlines(True),isolated.splitlines(True),
            fromfile='official/tta/candi/adapter_candi.py',tofile='overlay/adapter_labels_isolated.py')))
        spec = importlib.util.spec_from_file_location('tta.candi.adapter_candi',path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        self.instrument(module,predictor)

    def instrument(self,module,predictor):
        original_construct = predictor.construct_adapter
        def construct(cfg,model,thresholder,**kwargs):
            native = self.mode.startswith('native_')
            if native:
                import hashlib, pickle, random
                def rng_hash():
                    return hashlib.sha256(pickle.dumps((random.getstate(),np.random.get_state(),
                        torch.get_rng_state().tolist(),[s.tolist() for s in torch.cuda.get_rng_state_all()]))).hexdigest()
                self.initial_rng_hash = rng_hash()
                original_labels = np.array(kwargs['test_labels'],copy=True)
                if self.mode=='native_label_permuted':
                    kwargs['test_labels'] = np.random.default_rng(902).permutation(original_labels)
                self.label_changes = int(np.sum(original_labels!=kwargs['test_labels']))
                self.permutation_preserved_global_rng = rng_hash()==self.initial_rng_hash
                assert self.permutation_preserved_global_rng
                if self.mode=='native_c3':
                    self.loaded_backbone_hash = state_hash(model)
                    self.loaded_backbone_keys = list(model.state_dict())
            else:
                kwargs.pop('test_labels')  # evaluator array never reaches adapter
            adapter = original_construct(cfg,model,thresholder,**kwargs)
            if self.mode=='native_c3':
                self.post_construct_rng_hash = rng_hash()
                self.adaptation_hashes = {name:state_hash(getattr(model,name)) for name in ('sana_in','sana_out')}
                h = hashlib.sha256()
                for name,value in sorted(self.adaptation_hashes.items()):
                    h.update(name.encode()+value.encode())
                self.adaptation_combined_hash = h.hexdigest()
                self.adaptation_parameter_names = [name for name,p in model.named_parameters() if p.requires_grad]
                assert all(name.startswith(('sana_in.','sana_out.')) for name in self.adaptation_parameter_names)
            assert thresholder.test_labels is None
            if not native:
                assert not hasattr(adapter,'test_labels')
            self.adapter = adapter
            self.initial_model_hash = state_hash(model)
            original_score = model.get_anomaly_scores
            def score(x):
                out = original_score(x)
                self.last_scores = out.detach().clone()
                self.score_pending = True
                return out
            model.get_anomaly_scores = score
            original_step = adapter.optimizer.step
            def step(*args,**kw):
                result = original_step(*args,**kw)
                self.steps.append(dict(batch=self.offset,update=int(adapter.n_adapt),
                                       model_sha256=state_hash(model)))
                return result
            adapter.optimizer.step = step
            return adapter
        predictor.construct_adapter = construct
        original_adapt = module.CANDIAdapter.adapt
        def adapt(adapter,x,scores):
            assert self.score_pending and torch.equal(scores,self.last_scores)
            self.score_pending = False
            self.batch_size = len(x)
            self.batch_end = self.offset+len(x)-1
            self.current_ids = list(range(self.offset,self.offset+len(x)))
            before = {q:len(self.queues[q]) for q in self.queues}
            original_adapt(adapter,x,scores)
            for q in self.queues:
                assert len(self.queues[q])==getattr(adapter,f'n_samples_to_adapt_{q}')
            self.batches.append(dict(first_window=self.offset,last_window=self.batch_end,
                available_raw_timestamp=self.batch_end+adapter.cfg.DATA.WIN_SIZE-1,size=len(x),
                score_before_adapt=True,buffer_before=before,buffer_after={q:len(self.queues[q]) for q in self.queues},
                model_sha256=state_hash(adapter.model)))
            self.offset += len(x)
        module.CANDIAdapter.adapt = adapt
        original_loss = module.MLPAdapter.calculate_loss
        def loss(adapter,x):
            q = 'hard' if x is adapter.samples_to_adapt_hard else 'moderate'
            key = (adapter.n_adapt,q)
            if key not in self.seen_updates:
                ids = list(self.queues[q])
                assert len(ids)==len(x)>=adapter.cfg.TEST.TTA.CANDI.MIN_SAMPLES
                self.active_ids = ids
                self.events.append(dict(update=int(adapter.n_adapt),queue=q,ids=ids,
                    commit_window=self.batch_end,available_raw_timestamp=self.batch_end+adapter.cfg.DATA.WIN_SIZE-1,
                    buffer_size=len(ids)))
                self.queues[q] = []
                self.seen_updates.add(key)
            self.losses.append(dict(update=int(adapter.n_adapt),queue=q,ids=list(self.active_ids),batch=self.offset))
            return original_loss(adapter,x)
        module.MLPAdapter.calculate_loss = loss
        target = module.CANDIAdapter.get_samples_to_adapt.__wrapped__.__code__
        def trace(frame,event,arg):
            if frame.f_code is not target:
                return None
            if event=='return':
                values = frame.f_locals
                adapter = values['self']
                for q in ('hard','moderate'):
                    mask = values.get(f'mask_{q}')
                    if mask is None:
                        continue
                    indices = mask.nonzero(as_tuple=True)[0].cpu().tolist()
                    ids = [self.offset+i for i in indices]
                    self.candidates[q].extend(ids)
                    self.queues[q].extend(ids)
                    official_offset = (adapter.iter-1)*len(values['scores'])
                    self.events.append(dict(kind='selection',queue=q,ids=ids,queue_admitted_ids=ids,
                        batch_first=self.offset,official_offset=official_offset,
                        official_indices=[official_offset+i for i in indices],offset_mismatch=official_offset!=self.offset))
            return trace
        sys.settrace(trace)

    def finish(self,p):
        sys.settrace(None)
        labels = np.array(p.test_labels,copy=True)
        raw = np.array(p.test_loader.dataset.test_labels,copy=True)
        if self.mode=='audit_permuted':
            labels = np.random.default_rng(902).permutation(labels)
            raw = np.random.default_rng(903).permutation(raw)
        w = p.cfg.DATA.WIN_SIZE
        def summarize(ids):
            ids = list(ids)
            anomalous = sum(int(labels[i]) for i in ids)
            timestamps = {t for i in ids for t in range(i,i+w) if raw[t]==1}
            return dict(windows_or_exposures=len(ids),unique_windows=len(set(ids)),anomalous=anomalous,
                        contamination=anomalous/len(ids) if ids else None,
                        unique_raw_anomaly_timestamp_coverage=len(timestamps))
        queues = {}
        for q in ('hard','moderate'):
            committed = [i for e in self.events if e.get('queue')==q and 'commit_window' in e for i in e['ids']]
            exposures = [i for e in self.losses if e['queue']==q for i in e['ids']]
            queues[q] = dict(candidate=summarize(self.candidates[q]),queue_admitted=summarize(self.candidates[q]),
                committed=summarize(committed),gradient_exposure=summarize(exposures),pending=summarize(self.queues[q]),
                repeated_exposures=len(exposures)-len(set(exposures)),
                latency_windows=[e['commit_window']-i for e in self.events if e.get('queue')==q and 'commit_window' in e for i in e['ids']])
        committed = [i for e in self.events if 'commit_window' in e for i in e['ids']]
        exposures = [i for e in self.losses for i in e['ids']]
        result = dict(label_policy='Evaluator-only; adapter has no test_labels attribute or argument',
            queues=queues,candidate=summarize(self.candidates['hard']+self.candidates['moderate']),
            committed=summarize(committed),gradient_exposure=summarize(exposures),
            repeated_exposures=len(exposures)-len(set(exposures)),update_count=len(self.seen_updates),
            optimizer_step_count=len(self.steps),score_before_update=all(b['score_before_adapt'] for b in self.batches),
            initial_model_sha256=self.initial_model_hash,
            pending_total=sum(len(v) for v in self.queues.values()),
            offset_mismatch_batches=sorted({e['batch_first'] for e in self.events if e.get('offset_mismatch')}),
            native_counter_note='Only diagnostic-label reads/increments removed; official selection totals and queue counters unchanged',
            id_semantics='Window ID = zero-based start in raw native test; batch scores all available at last window end. Latency = commit batch last window ID minus selected window ID.')
        details = dict(selection_and_commit_events=self.events,loss_exposures=self.losses,optimizer_steps=self.steps,batches=self.batches)
        (REPORT/'logs'/f'{self.tag}.audit_events.json').write_text(json.dumps(details,indent=2)+'\n')
        if self.mode.startswith('native_'):
            result.update(label_policy='Untouched native label-passing adapter; true labels used only at observer finish for scientific counts',
                native_counter_note='Native counters untouched; stable observer IDs separate from native offsets',
                initial_rng_sha256=self.initial_rng_hash,adapter_label_positions_changed=self.label_changes,
                permutation_preserved_global_rng=self.permutation_preserved_global_rng)
        if self.mode=='native_c3':
            result['seed_initialization'] = dict(loaded_backbone_sha256=self.loaded_backbone_hash,
                loaded_backbone_keys=self.loaded_backbone_keys,adaptation_module_sha256=self.adaptation_hashes,
                adaptation_combined_sha256=self.adaptation_combined_hash,
                adaptation_trainable_parameter_names=self.adaptation_parameter_names,
                global_rng_before_adapter_sha256=self.initial_rng_hash,
                global_rng_after_adapter_sha256=self.post_construct_rng_hash,
                semantics='Backbone before construct_adapter; fresh SANA after construction and before test iteration; canonical tensor bytes. RNG is Python/NumPy/Torch CPU/all CUDA states.')
        return result
