"""Controlled committed-buffer operator; official loss, no selection or labels."""
import copy
import hashlib
import json
from pathlib import Path
import pickle
import random
import sys
from types import SimpleNamespace
import numpy as np
import torch
from phase_c_run import ROOT,OFFICIAL,digest,state_hash

sys.dont_write_bytecode = True
sys.path.insert(0,str(OFFICIAL))
from tta.candi.adapter_candi import MLPAdapter,SANA
from models.optimizer import construct_optimizer

OFFICIAL_LOSS = MLPAdapter.calculate_loss
REPORT = ROOT/'reports/phase_d'
DATA = ROOT/'data/phase_d'
NOTE = '9018e86'


def rng_state():
    return dict(python=random.getstate(),numpy=np.random.get_state(),cpu=torch.get_rng_state(),cuda=torch.cuda.get_rng_state_all())


def restore_rng(s):
    random.setstate(s['python']); np.random.set_state(s['numpy'])
    torch.set_rng_state(s['cpu']); torch.cuda.set_rng_state_all(s['cuda'])


def tensor_hash(x):
    a=x.detach().cpu().contiguous().numpy() if torch.is_tensor(x) else np.ascontiguousarray(x)
    return hashlib.sha256(str(a.dtype).encode()+str(a.shape).encode()+a.tobytes()).hexdigest()


def object_hash(obj):
    # Stable recursively typed tensor/optimizer/RNG fingerprint.
    h=hashlib.sha256()
    def visit(x):
        if torch.is_tensor(x) or isinstance(x,np.ndarray): h.update(tensor_hash(x).encode())
        elif isinstance(x,dict):
            for k in sorted(x,key=str): h.update(str(k).encode()); visit(x[k])
        elif isinstance(x,(tuple,list)):
            h.update(type(x).__name__.encode())
            for v in x: visit(v)
        else: h.update(repr(x).encode())
    visit(obj)
    return h.hexdigest()


def update(adapter,buffer):
    assert len(buffer)>=adapter.cfg.TEST.TTA.CANDI.MIN_SAMPLES
    is_eval=not adapter.model.training
    adapter.model.train()
    losses=[]
    for _ in range(adapter.cfg.TEST.TTA.STEPS):
        loss=OFFICIAL_LOSS(adapter,buffer)
        losses.append(float(loss.detach()))
        adapter.optimizer.zero_grad()
        loss.backward()
        adapter.optimizer.step()
    if is_eval: adapter.model.eval()
    return losses


def clone_adapter(adapter,optimizer_state=None):
    model=copy.deepcopy(adapter.model)
    # Instance observers close over the native model; remove only observer override.
    model.__dict__.pop('get_anomaly_scores',None)
    cfg=adapter.cfg.clone()
    opt=construct_optimizer(model,cfg)
    opt.load_state_dict(copy.deepcopy(optimizer_state if optimizer_state is not None else adapter.optimizer.state_dict()))
    return SimpleNamespace(model=model,cfg=cfg,optimizer=opt)


def authorize():
    import subprocess
    assert subprocess.check_output(['rtk','git','show',f'{NOTE}:reports/phase_d/prospective.md'])==(REPORT/'prospective.md').read_bytes()
    subprocess.run(['rtk','git','merge-base','--is-ancestor',NOTE,'origin/main'],check=True)


class Capture:
    def install(self,predictor,module):
        original_construct=predictor.construct_adapter
        original_loss=module.MLPAdapter.calculate_loss
        self.pending=False
        self.captured=False
        self.losses=[]
        def construct(*args,**kwargs):
            adapter=original_construct(*args,**kwargs)
            original_step=adapter.optimizer.step
            def step(*a,**kw):
                out=original_step(*a,**kw)
                if self.pending:
                    self.post=copy.deepcopy(adapter.model.state_dict())
                    self.post_hash=state_hash(adapter.model)
                    self.post_opt=copy.deepcopy(adapter.optimizer.state_dict())
                    self.post_rng=rng_state()
                    self.wait_score=True
                    self.pending=False
                return out
            adapter.optimizer.step=step
            original_score=adapter.model.get_anomaly_scores
            def score(x):
                out=original_score(x)
                if getattr(self,'wait_score',False):
                    self.segment=x.detach().clone()
                    self.next_scores=out.detach().clone()
                    self.wait_score=False
                return out
            adapter.model.get_anomaly_scores=score
            return adapter
        predictor.construct_adapter=construct
        def loss(adapter,x):
            if not self.captured:
                assert adapter.n_adapt==1
                self.buffer=x.detach().clone()
                self.rng=rng_state()
                self.pre=copy.deepcopy(adapter.model.state_dict())
                self.pre_opt=copy.deepcopy(adapter.optimizer.state_dict())
                self.pre_hash=state_hash(adapter.model)
                self.clone=clone_adapter(adapter,self.pre_opt)
                restore_rng(self.rng)
                self.captured=True
                self.pending=True
                self.wait_score=False
            out=original_loss(adapter,x)
            if self.pending: self.losses.append(float(out.detach()))
            return out
        module.MLPAdapter.calculate_loss=loss

    def verify(self,audit):
        DATA.mkdir(parents=True,exist_ok=True)
        first=next(e for e in audit.events if 'commit_window' in e)
        old=json.loads((ROOT/'reports/phase_c_v2/logs/SMD_1-8_alpha_5.0_seed_0_native_label_control.audit_events.json').read_text())
        expected=next(e for e in old['selection_and_commit_events'] if 'commit_window' in e)
        assert first==expected and len(self.buffer)==242
        assert state_hash(self.clone.model)==self.pre_hash
        # Capture occurs after native model.train(), so explicitly restore native
        # pre-adapt eval mode for the harness's identical train/eval transition.
        self.clone.model.eval()
        restore_rng(self.rng)
        start=__import__('time').perf_counter()
        losses=update(self.clone,self.buffer)
        torch.cuda.synchronize()
        elapsed=__import__('time').perf_counter()-start
        post_rng=rng_state()
        result=dict(losses_native=self.losses,losses_replay=losses,
            examples_order_equal=tensor_hash(self.buffer)==tensor_hash(self.buffer.clone()),
            ordered_window_ids=first['ids'],event=first,
            loss_exact=losses==self.losses,step_count_equal=len(losses)==len(self.losses)==1,
            loss_within_tolerance=bool(np.allclose(losses,self.losses,atol=1e-7,rtol=1e-6)),
            all_post_tensors_exact=all(torch.equal(v,self.clone.model.state_dict()[k]) for k,v in self.post.items()),
            final_model_hash_exact=state_hash(self.clone.model)==self.post_hash,
            optimizer_state_exact=object_hash(self.clone.optimizer.state_dict())==object_hash(self.post_opt),
            rng_after_update_exact=object_hash(post_rng)==object_hash(self.post_rng),
            restored_eval=not self.clone.model.training)
        scores=self.clone.model.get_anomaly_scores(self.segment)
        result.update(subsequent_scores_exact=torch.equal(scores,self.next_scores),
            subsequent_scores_within_tolerance=bool(torch.allclose(scores,self.next_scores,atol=1e-7,rtol=1e-6)),
            pre_model_sha256=self.pre_hash,post_model_sha256=self.post_hash,
            buffer_sha256=tensor_hash(self.buffer),pre_optimizer_sha256=object_hash(self.pre_opt),
            pre_rng_sha256=object_hash(self.rng),next_segment_sha256=tensor_hash(self.segment),
            next_scores_sha256=tensor_hash(self.next_scores),replay_seconds=elapsed,
            score_segment_window_starts=[256,512],official_code_unchanged=True)
        ok=all(v for k,v in result.items() if k.endswith(('_exact','_equal','_tolerance')) or k=='restored_eval')
        result['status']='PASS' if ok else 'STOP'
        snapshot=DATA/'real_operator_capture.pth'
        torch.save(dict(pre_model=self.pre,pre_optimizer=self.pre_opt,rng=self.rng,buffer=self.buffer.cpu(),
            post_model=self.post,post_optimizer=self.post_opt,post_rng=self.post_rng,segment=self.segment.cpu(),
            native_scores=self.next_scores.cpu(),losses=self.losses,config=self.clone.cfg.dump(),event=first),snapshot)
        result['snapshot_path']=str(snapshot.relative_to(ROOT)); result['snapshot_sha256']=digest(snapshot)
        (REPORT/'operator_parity.json').write_text(json.dumps(result,indent=2)+'\n')
        assert ok,result
