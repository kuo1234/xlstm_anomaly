"""Independent stable-ID validation and within-condition C3 characterization."""
from collections import Counter
import json
import hashlib
import csv
from pathlib import Path
import subprocess
import numpy as np
import yaml
import torch
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc
from phase_c3 import ROOT,REPORT,OFFICIAL,PIN,NOTE,pilot,record,trace
from phase_c_run import digest
import phase_c_v2 as v2


def stats(values):
    x = [v for v in values if v is not None]
    return dict(n=len(x),values=values,mean=float(np.mean(x)) if x else None,
        sample_sd=float(np.std(x,ddof=1)) if len(x)>1 else None,
        minimum=float(min(x)) if x else None,maximum=float(max(x)) if x else None)


def sources(machine,alpha,seed):
    if seed>0 or (machine=='SMD_1-8' and alpha in ('1.0','5.0')):
        r = record(machine,alpha,seed)
        report = REPORT
    else:
        mode = 'native_replay_1' if machine=='SMD_1-8' else 'native_v2'
        r = v2.record(machine,alpha,mode)
        report = v2.REPORT
    p = report/'runs'/f'{r["tag"]}.json'
    t = report/'logs'/f'{r["tag"]}.audit_events.json'
    return r,json.loads(t.read_text()),p,t


def summarize_row(r,t,p,tp):
    audit = r['audit']
    work = Path(r['working_directory'])
    labels = np.load(work/'results'/r['machine']/'MLP'/r['alpha']/'test_labels.npy')
    scores = np.load(v2.score_path(r))
    assert r['error'] is None and np.isfinite(scores).all() and len(scores)==len(labels)
    precision,recall,_ = precision_recall_curve(labels,scores)
    assert float(roc_auc_score(labels,scores))==r['observed']['AUROC']
    assert float(auc(recall,precision))==r['observed']['AUPRC']
    cfg = yaml.safe_load(r['resolved_config'])
    assert not cfg['TRAIN']['ENABLE'] and cfg['SEED']==r['seed'] and r['official_commit']==PIN
    steps = cfg['TEST']['TTA']['STEPS']
    events = t['selection_and_commit_events']
    commits = [e for e in events if 'commit_window' in e]
    selections = [e for e in events if e.get('kind')=='selection']
    exposures = t['loss_exposures']
    def summary(ids):
        assert all(0<=i<len(labels) for i in ids)
        counts = Counter(ids)
        total = len(ids)
        anomalous = sum(int(labels[i]) for i in ids)
        unique_anomalous = sum(int(labels[i]) for i in counts)
        return dict(count=total,unique_count=len(counts),anomalous=anomalous,
            contamination=anomalous/total if total else None,
            unique_anomalous=unique_anomalous,repeated_exposures=total-len(counts),
            repeated_anomalous_exposures=anomalous-unique_anomalous)
    queues = {}
    for q in ('hard','moderate','all'):
        def selected(e):
            return q=='all' or e['queue']==q
        ids = {name:[i for e in seq if selected(e) for i in e['ids']] for name,seq in (
            ('candidate',selections),('committed',commits),('gradient_exposure',exposures))}
        assert len(ids['candidate'])==len(set(ids['candidate']))
        assert len(ids['committed'])==len(set(ids['committed']))
        assert set(ids['committed'])<=set(ids['candidate'])
        pending = sorted(set(ids['candidate'])-set(ids['committed']))
        expected_exposures = Counter({i:steps for i in ids['committed']})
        assert Counter(ids['gradient_exposure'])==expected_exposures
        summ = {name:summary(v) for name,v in ids.items()}
        summ['pending'] = summary(pending)
        latencies = [e['commit_window']-i for e in commits if selected(e) for i in e['ids']]
        assert all(v>=0 for v in latencies)
        summ['latency_windows'] = dict(count=len(latencies),mean=float(np.mean(latencies)) if latencies else None,
            median=float(np.median(latencies)) if latencies else None,
            p95=float(np.percentile(latencies,95)) if latencies else None,
            maximum=max(latencies) if latencies else None,
            semantics='Commit batch last window ID minus selected window ID; units windows/raw stride1 samples; uncommitted tail censored')
        summ['update_count'] = sum(selected(e) for e in commits)
        summ['optimizer_steps'] = sum(selected(e) for e in exposures)
        candidate,committed = summ['candidate']['contamination'],summ['committed']['contamination']
        summ['committed_minus_candidate'] = committed-candidate if candidate is not None and committed is not None else None
        summ['material_delta_1pp'] = abs(summ['committed_minus_candidate'])>=.01 if summ['committed_minus_candidate'] is not None else None
        expected = audit if q=='all' else audit['queues'][q]
        for name in ('candidate','committed','gradient_exposure'):
            assert summ[name]['count']==expected[name]['windows_or_exposures']
            assert summ[name]['anomalous']==expected[name]['anomalous']
        if q!='all':
            assert len(pending)==expected['pending']['windows_or_exposures']
            assert latencies==expected['latency_windows']
        queues[q] = summ
    assert queues['all']['update_count']==audit['update_count']==r['official_counters']['n_adapt']
    assert queues['all']['optimizer_steps']==len(t['optimizer_steps'])==steps*audit['update_count']
    assert queues['all']['pending']['count']==audit['pending_total']
    assert all(e['buffer_size']>=16 and len(e['ids'])==e['buffer_size'] for e in commits)
    assert all(b['score_before_adapt'] for b in t['batches'])
    for rel,h in r['artifact_hashes'].items():
        assert digest(work/rel)==h
    assert digest(work/'final_model.pth')==r['final_checkpoint_sha256']
    # CPU-only tensor verification: adaptation must not change the released backbone.
    final_state = torch.load(work/'final_model.pth',map_location='cpu',weights_only=True)
    checkpoint = OFFICIAL/'results'/r['machine']/'MLP/checkpoint_best.pth'
    assert digest(checkpoint)==r['checkpoint_sha256']
    released = torch.load(checkpoint,map_location='cpu',weights_only=False)['model_state']
    assert all(k in final_state and torch.equal(value,final_state[k]) for k,value in released.items())
    h = hashlib.sha256()
    for k,value in sorted(released.items()):
        arr = value.contiguous().numpy()
        h.update(k.encode()+str(arr.dtype).encode()+str(arr.shape).encode()+arr.tobytes())
    backbone_hash = h.hexdigest()
    if audit.get('seed_initialization'):
        assert backbone_hash==audit['seed_initialization']['loaded_backbone_sha256']
    return dict(machine=r['machine'],alpha=r['alpha'],seed=r['seed'],metrics={k:r['observed'][k] for k in ('AUROC','AUPRC')},
        queues=queues,steps=steps,score_sha256=digest(v2.score_path(r)),final_model_sha256=r['final_model_sha256'],
        initial_model_sha256=audit['initial_model_sha256'],initial_rng_sha256=audit['initial_rng_sha256'],
        seed_initialization=audit.get('seed_initialization'),
        missing_initialization_note=None if 'seed_initialization' in audit else 'Reused sealed seed0: full initialized model hash measured; separated pre-backbone/SANA hashes not measured',
        runtime_seconds=r['runtime_seconds'],peak_gpu_allocated_bytes=r['peak_gpu_allocated_bytes'],
        peak_gpu_reserved_bytes=r['peak_gpu_reserved_bytes'],checkpoint_sha256=r['checkpoint_sha256'],
        record_path=str(p.relative_to(ROOT)),record_sha256=digest(p),trace_path=str(tp.relative_to(ROOT)),trace_sha256=digest(tp),
        native_offset_mismatch_batches=audit['offset_mismatch_batches'],
        reused_seed0=p.parent.parent!=REPORT,
        final_backbone_unchanged=True,released_backbone_tensor_sha256=backbone_hash,
        hard_gt_moderate={name:(queues['hard'][name]['contamination']>queues['moderate'][name]['contamination'])
            if queues['hard'][name]['contamination'] is not None and queues['moderate'][name]['contamination'] is not None else None
            for name in ('candidate','committed','gradient_exposure')})


def main():
    result = pilot()
    (REPORT/'seed_effectiveness_pilot.json').write_text(json.dumps(result,indent=2)+'\n')
    if result['status']=='SEED-INERT':
        (REPORT/'README.md').write_text('# C3-A — SEED-INERT STOP\n\nNo seeds2–4 or C3-B expansion. '
            'Different nominal seeds do not establish replication. H1-admission 4/5 criterion not evaluated. '
            'Phase D remains locked; return for protocol amendment. See seed_effectiveness_pilot.json.\n')
        seal()
        return
    rows,conditions = [],[]
    for machine in ('SMD_1-8','SMD_2-1'):
        for alpha in ('0.5','1.0','5.0'):
            records = [sources(machine,alpha,s) for s in range(5)]
            group = [summarize_row(*r) for r in records]
            rows.extend(group)
            configs = [yaml.safe_load(r[0]['resolved_config']) for r in records]
            for seed,c in enumerate(configs):
                assert c.pop('SEED')==seed
            assert all(c==configs[0] for c in configs)
            assert len({r['checkpoint_sha256'] for r in group})==1
            measured_init = [r['seed_initialization'] for r in group if r['seed_initialization']]
            assert len({i['loaded_backbone_sha256'] for i in measured_init})==1
            diversity = {key:len({r[key] for r in group}) for key in (
                'initial_model_sha256','initial_rng_sha256','score_sha256','final_model_sha256','trace_sha256')}
            effective = diversity['initial_model_sha256']==5 and diversity['score_sha256']==5 and diversity['final_model_sha256']==5
            admissions = [r['queues']['all']['committed']['anomalous']>0 for r in group]
            condition = dict(machine=machine,alpha=alpha,seeds=list(range(5)),diversity=diversity,
                seed_effectiveness='SEED-ACTIVE' if effective else 'INVESTIGATE_NOT_FIVE_DISTINCT_REPLICATES',
                measured_separate_initialization_count=len(measured_init),
                metrics={k:stats([r['metrics'][k] for r in group]) for k in ('AUROC','AUPRC')},
                contamination={q:{k:stats([r['queues'][q][k]['contamination'] for r in group])
                    for k in ('candidate','committed','gradient_exposure')} for q in ('hard','moderate','all')},
                hard_gt_moderate={k:dict(values=[r['hard_gt_moderate'][k] for r in group],
                    true=sum(r['hard_gt_moderate'][k] is True for r in group),
                    defined=sum(r['hard_gt_moderate'][k] is not None for r in group))
                    for k in ('candidate','committed','gradient_exposure')},
                material_commit_candidate_delta={q:dict(values=[r['queues'][q]['committed_minus_candidate'] for r in group],
                    material_seeds=[r['seed'] for r in group if r['queues'][q]['material_delta_1pp'] is True]) for q in ('hard','moderate','all')},
                repeated_anomalous_exposures={q:[r['queues'][q]['gradient_exposure']['repeated_anomalous_exposures'] for r in group] for q in ('hard','moderate','all')},
                admission_seeds_positive=sum(admissions),H1_admission='PASS_ADMISSION_ONLY' if effective and sum(admissions)>=4 else 'NOT_CONFIRMED',
                H1_harm='NOT_TESTED',inference_unit='Seed stochastic adaptation, conditional on this fixed machine/alpha/released checkpoint; configurations not replicates')
            conditions.append(condition)
    # Missing-audit seed0 rerun must exactly preserve sealed alpha1 native outputs.
    original = v2.record('SMD_1-8','1.0','native')
    rerun = record('SMD_1-8','1.0',0)
    assert v2.equal_runs(original,rerun,False)
    new = [json.loads(p.read_text()) for p in (REPORT/'runs').glob('*.json')]
    assert len(new)==26  # 24 new seeds + two justified seed0 integrity completions
    summary = dict(C3_A=result['status'],C3_B='COMPLETE',prospective_commit=NOTE,conditions=conditions,
        characterized_rows=30,new_executions=26,reused_seed0_rows=4,
        H1_admission='PASS_ADMISSION_ONLY' if any(c['H1_admission']=='PASS_ADMISSION_ONLY' for c in conditions) else 'NOT_CONFIRMED',
        H1_harm='NOT_TESTED',phase_D_locked=True,no_controlled_contamination=True,
        new_runtime_seconds=sum(r['runtime_seconds'] for r in new),
        peak_gpu_allocated_bytes=max(r['peak_gpu_allocated_bytes'] for r in new),
        peak_gpu_reserved_bytes=max(r['peak_gpu_reserved_bytes'] for r in new),
        warning='No pooled n=30, no independent backbone retraining, no harm inferred from contamination; no cross-machine generalized CI')
    (REPORT/'replication_results.json').write_text(json.dumps(dict(summary=summary,rows=rows),indent=2)+'\n')
    flat = []
    for r in rows:
        line = {k:r[k] for k in ('machine','alpha','seed','steps','score_sha256','final_model_sha256','runtime_seconds',
            'peak_gpu_allocated_bytes','peak_gpu_reserved_bytes','record_path','trace_path')}
        line.update(r['metrics'])
        for q,summ in r['queues'].items():
            for kind in ('candidate','committed','gradient_exposure','pending'):
                for field in ('count','anomalous','contamination','repeated_anomalous_exposures'):
                    line[f'{q}_{kind}_{field}'] = summ[kind][field]
            for field in ('update_count','optimizer_steps','committed_minus_candidate','material_delta_1pp'):
                line[f'{q}_{field}'] = summ[field]
            for field in ('mean','median','p95','maximum'):
                line[f'{q}_commit_latency_{field}_windows'] = summ['latency_windows'][field]
        flat.append(line)
    with (REPORT/'seed_results.csv').open('w',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=list(flat[0]),lineterminator='\n')
        writer.writeheader()
        writer.writerows(flat)
    write_readme(summary,rows,result)
    seal()
    print(json.dumps(summary,indent=2))


def write_readme(s,rows,p):
    text = ['# C3 — cross-seed characterization','',
        'C3-A: **SEED-ACTIVE**. Released backbone is identical; fresh SANA initialization and causal adaptation trajectory change with SEED.',
        'C3-B: complete, seeds0–4 within each of six fixed conditions. H1-admission is evaluated separately; **H1-harm NOT TESTED**. Phase D remains locked.',
        '',f'Prospective commit `{NOTE}` was pushed before pilot execution. Pinned CANDI `{PIN}` and released checkpoints/config/preprocessing unchanged except SEED; TRAIN.ENABLE=False; no retraining/tuning.',
        '', '## Pilot and integrity', '',
        'Seed0 integrity rerun exactly matches the accepted alpha5 native control in scores, final state and full observer trajectory. Pre-backbone, SANA-in/out, and global RNG before/after hashes are recorded in seed_effectiveness_pilot.json. RNG differences alone are not the activity criterion. Native CANDIAdapter.__init__ constructs new SANA input/output modules after the pretrained backbone is loaded; their Conv1d/Linear/attention initialization consumes the seeded Torch RNG. The seed0 alpha1 rerun fills a previously missing stable-ID audit and exactly matches its original scores/model/metrics. Neither technical rerun is an extra replicate.',
        '', '## Within-condition seed variation', '',
        'AUROC and native trapezoidal PR-AUC: mean ± sample SD over five effective adaptation seeds. Committed contamination gives min–max across seeds; no configurations are pooled.', '',
        '| Machine | alpha | AUROC | PR-AUC | Committed contamination range | Admission seeds |',
        '|---|---:|---:|---:|---:|---:|']
    for c in s['conditions']:
        a,b = [c['metrics'][k] for k in ('AUROC','AUPRC')]
        cc = c['contamination']['all']['committed']
        text.append(f'| {c["machine"]} | {c["alpha"]} | {a["mean"]:.6f} ± {a["sample_sd"]:.6f} | {b["mean"]:.6f} ± {b["sample_sd"]:.6f} | {100*cc["minimum"]:.3f}–{100*cc["maximum"]:.3f}% | {c["admission_seeds_positive"]}/5 |')
    text += ['', 'Full seed-level values, all queues/denominators, latency summaries, pending/update counts, repeated exposures, hashes and provenance are in replication_results.json; seed_results.csv provides a flattened table (blank cells mean N/A). Full stable-ID event/optimizer traces remain in logs or referenced sealed Phase C v2 paths. Historical inherited per-run COMPLETE_PENDING_V2_VERIFICATION status is only a runner placeholder; this C3 report and verification.json contain the final C3 conclusions.',
        '', '## Admission and exposure characterization', '',
        'These statements use stable window IDs and true evaluator labels after execution, never native anomaly counters. Nonzero admission does not demonstrate performance harm. Hard/moderate comparisons with empty queues are N/A.', '']
    for c in s['conditions']:
        comp = c['hard_gt_moderate']['committed']
        cand = c['hard_gt_moderate']['candidate']
        material = {q:c['material_commit_candidate_delta'][q]['material_seeds'] for q in ('all','hard','moderate')}
        repeats = c['repeated_anomalous_exposures']['all']
        committed_comparison = f'{comp["true"]}/{comp["defined"]} defined seeds' if comp['defined'] else 'N/A (no comparable committed queues)'
        candidate_comparison = f'{cand["true"]}/{cand["defined"]} defined seeds' if cand['defined'] else 'N/A'
        text.append(f'- {c["machine"]} alpha{c["alpha"]}: hard > moderate candidate contamination in {candidate_comparison}; committed comparison: {committed_comparison}. Candidate→commit difference ≥1 percentage point by queue (seed IDs): {material}. Repeated anomalous loss exposures (seed0–4): {repeats}.')
    text += ['', 'The ≥1 percentage-point materiality threshold is descriptive, prospectively fixed, not a new GO gate. Queue-specific deltas are also reported. STEPS repeats are exposures of the same committed windows, not new independent anomalies. Pending-tail selection differences are not decontamination evidence.',
        '', '## Validity and scope', '',
        'All five initialized-model/score/final-state hashes are checked for distinctness within each condition, with identical loaded backbones wherever newly instrumented. Reused seed0 rows retain their measured full initialization hash and explicitly N/A separated SANA/backbone hashes. No absent measurement is fabricated. Variation is conditional on the fixed released backbone and data; it is not training-seed or dataset replication.',
        '', 'No test-informed tuning, no paper-metric chasing. Paper fidelity remains MISMATCH / UNRESOLVED_LINEAGE. The official native label-passing API and known bookkeeping defects remain unchanged; the previously validated label-isolated overlay remains separate. C3 uses the accepted native passive observer with new read-only initialization hashes.',
        '',f'New execution count: {s["new_executions"]}; four sealed seed0 rows reused. Measured native-entry runtime including observers: {s["new_runtime_seconds"]:.3f} s; peak allocated/reserved GPU memory {s["peak_gpu_allocated_bytes"]/2**30:.3f}/{s["peak_gpu_reserved_bytes"]/2**30:.3f} GiB. Per-run process wall times and native-entry CUDA event spans are logged; event spans include host gaps, not pure kernel time.',
        '', 'No controlled contamination, Phase D, xLSTM/LSTM, probes, H4 or H3b executed. Return for external review before any next phase.', '']
    (REPORT/'README.md').write_text('\n'.join(text))


def seal():
    tests = json.loads((REPORT/'cpu_test_results.json').read_text())
    assert tests['successful'] and tests['tests_run']==7
    for directory in (ROOT/'reports/phase_c',ROOT/'reports/phase_c_v2'):
        for line in (directory/'SHA256SUMS').read_text().splitlines():
            h,p = line.split('  ',1)
            assert digest(ROOT/p)==h,p
    hashes = json.loads((ROOT/'reports/phase_c/official_code_hashes.json').read_text())
    assert all(digest(OFFICIAL/p)==h for p,h in hashes.items())
    assert subprocess.check_output(['rtk','git','-C',str(OFFICIAL),'rev-parse','HEAD'],text=True).strip()==PIN
    assert not subprocess.check_output(['rtk','git','-C',str(OFFICIAL),'status','--porcelain'],text=True).strip()
    (REPORT/'verification.json').write_text(json.dumps(dict(official_immutable=True,previous_C_Cv2_seals_unchanged=True,
        cpu_tests=tests,
        prospective_commit=subprocess.check_output(['rtk','git','rev-parse',NOTE],text=True).strip(),
        checks=['pilot seed0 control full trace parity','same loaded backbone across seeds',
            'same configs apart from SEED','independent stable-ID admission/exposure recount',
            'MIN_SAMPLES and candidate/commit/pending reconciliation','STEPS exposure multiplicity',
            'finite score arrays and output artifact hashes','native AUROC/trapezoidal PR-AUC independently recomputed',
            'frozen released backbone tensor equality after adaptation','seed0 alpha1 missing-audit integrity parity',
            'per-condition initialized/score/final hashes diversity; no pooled replicates'],
        harness_hashes={p:digest(ROOT/p) for p in ('scripts/phase_c3.py','scripts/phase_c3_finalize.py',
            'scripts/phase_c_run.py','scripts/phase_c_audit.py','scripts/test_phase_c3.py')}),indent=2)+'\n')
    paths = sorted(p for p in REPORT.rglob('*') if p.is_file() and p.name!='SHA256SUMS')
    (REPORT/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(ROOT)}\n' for p in paths))


if __name__=='__main__':
    main()
