"""Prospectively gated C3 runner; seed effectiveness is not nominal seed count."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
import numpy as np
from phase_c_run import ROOT,OFFICIAL,PIN,digest
import phase_c_v2 as v2

REPORT = ROOT/'reports/phase_c3'
NOTE = '8b554c5'


def record(machine,alpha,seed):
    return json.loads((REPORT/'runs'/f'{machine}_alpha_{alpha}_seed_{seed}_native_c3.json').read_text())


def trace(r):
    return json.loads((REPORT/'logs'/f'{r["tag"]}.audit_events.json').read_text())


def environment():
    previous = v2.REPORT
    v2.REPORT = REPORT
    try:
        v2.environment()
    finally:
        v2.REPORT = previous
    path = REPORT/'environment.json'
    data = json.loads(path.read_text())
    data.update(amendment_commit=NOTE,seeds=[0,1,2,3,4],fresh_process_per_run=True)
    driver = subprocess.check_output(['rtk','nvidia-smi','--query-gpu=name,driver_version','--format=csv,noheader'],text=True).strip()
    assert driver=='NVIDIA GB10, 580.173.02'
    data['gpu_driver_verified'] = driver
    path.write_text(json.dumps(data,indent=2)+'\n')


def pilot():
    a,b = [record('SMD_1-8','5.0',s) for s in (0,1)]
    assert a['error'] is None and b['error'] is None
    ia,ib = [r['audit']['seed_initialization'] for r in (a,b)]
    assert ia['loaded_backbone_sha256']==ib['loaded_backbone_sha256']
    # Normalize only SEED for configuration equality; never ignore other changes.
    import yaml
    ca,cb = [yaml.safe_load(r['resolved_config']) for r in (a,b)]
    assert ca.pop('SEED')==0 and cb.pop('SEED')==1
    assert ca==cb and a['checkpoint_sha256']==b['checkpoint_sha256']
    old = v2.record('SMD_1-8','5.0','native_label_control')
    assert np.array_equal(np.load(v2.score_path(a)),np.load(v2.score_path(old)))
    assert a['final_model_sha256']==old['final_model_sha256']
    assert trace(a)==v2.events(old)
    ta,tb = trace(a),trace(b)
    def event_kind(t,kind):
        return [e for e in t['selection_and_commit_events'] if ('commit_window' in e)==(kind=='commit')]
    checks = dict(loaded_backbone_equal=ia['loaded_backbone_sha256']==ib['loaded_backbone_sha256'],
        fresh_adaptation_equal=ia['adaptation_combined_sha256']==ib['adaptation_combined_sha256'],
        rng_before_equal=ia['global_rng_before_adapter_sha256']==ib['global_rng_before_adapter_sha256'],
        rng_after_equal=ia['global_rng_after_adapter_sha256']==ib['global_rng_after_adapter_sha256'],
        scores_equal=np.array_equal(np.load(v2.score_path(a)),np.load(v2.score_path(b))),
        score_hash_equal=digest(v2.score_path(a))==digest(v2.score_path(b)),
        candidate_events_equal=event_kind(ta,'selection')==event_kind(tb,'selection'),
        commit_events_equal=event_kind(ta,'commit')==event_kind(tb,'commit'),
        update_timing_equal=[(e['batch'],e['update']) for e in ta['optimizer_steps']]==[(e['batch'],e['update']) for e in tb['optimizer_steps']],
        per_step_model_equal=ta['optimizer_steps']==tb['optimizer_steps'],
        final_model_equal=a['final_model_sha256']==b['final_model_sha256'],metrics_equal=a['observed']==b['observed'],
        contamination_counts_equal=all(a['audit'][k]==b['audit'][k] for k in ('candidate','committed','gradient_exposure','queues')))
    active = not checks['fresh_adaptation_equal'] or any(not checks[k] for k in (
        'scores_equal','candidate_events_equal','commit_events_equal','update_timing_equal','per_step_model_equal','final_model_equal'))
    result = dict(status='SEED-ACTIVE' if active else 'SEED-INERT',checks=checks,
        seed0_integrity_full_trace_parity=True,
        initialization={str(r['seed']):r['audit']['seed_initialization'] for r in (a,b)},
        observations={str(r['seed']):dict(metrics=r['observed'],score_sha256=digest(v2.score_path(r)),
            final_model_sha256=r['final_model_sha256'],counts={k:r['audit'][k] for k in ('candidate','committed','gradient_exposure','update_count','pending_total')}) for r in (a,b)})
    return result


def authorize(machine,alpha,seed):
    assert machine in ('SMD_1-8','SMD_2-1') and alpha in ('0.5','1.0','5.0') and seed in range(5)
    assert subprocess.check_output(['rtk','git','show',f'{NOTE}:reports/phase_c3/prospective.md'])==(REPORT/'prospective.md').read_bytes()
    subprocess.run(['rtk','git','merge-base','--is-ancestor',NOTE,'origin/main'],check=True)
    if (machine,alpha)==('SMD_1-8','5.0') and seed in (0,1):
        return
    assert pilot()['status']=='SEED-ACTIVE','SEED-INERT: expansion locked'
    # Sealed seed0 reuse mandatory except missing 1-8 alpha1 audit completion.
    assert seed!=0 or (machine,alpha)==('SMD_1-8','1.0')


def launch(machine,alpha,seed):
    authorize(machine,alpha,seed)
    tag = f'{machine}_alpha_{alpha}_seed_{seed}_native_c3'
    (REPORT/'logs').mkdir(parents=True,exist_ok=True)
    command = ['rtk',str(ROOT/'data/phase_c/venv/bin/python'),str(ROOT/'scripts/phase_c_run.py'),
        '--machine',machine,'--alpha',alpha,'--seed',str(seed),'--mode','native_c3']
    with (REPORT/'commands.txt').open('a') as f:
        f.write('PYTHONDONTWRITEBYTECODE=1 WANDB_MODE=disabled '+shlex.join(command)+'\n')
    start = time.perf_counter()
    with (REPORT/'logs'/f'{tag}.stdout.log').open('x') as out,(REPORT/'logs'/f'{tag}.stderr.log').open('x') as err:
        r = subprocess.run(command,cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',WANDB_MODE='disabled'),stdout=out,stderr=err)
    (REPORT/'logs'/f'{tag}.launch.json').write_text(json.dumps(dict(command=command,returncode=r.returncode,
        process_wall_seconds=time.perf_counter()-start,harness_hashes={p:digest(ROOT/p) for p in (
            'scripts/phase_c_run.py','scripts/phase_c_audit.py','scripts/phase_c3.py')}),indent=2)+'\n')
    if r.returncode:
        print((REPORT/'logs'/f'{tag}.stderr.log').read_text()[-5000:])
        raise SystemExit(r.returncode)
    result = record(machine,alpha,seed)
    assert result['error'] is None
    print(json.dumps({k:result[k] for k in ('tag','observed','runtime_seconds')}),flush=True)
    if (machine,alpha,seed)==('SMD_1-8','5.0',1):
        p = pilot()
        (REPORT/'seed_effectiveness_pilot.json').write_text(json.dumps(p,indent=2)+'\n')
        print('PILOT',p['status'],p['checks'],flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--machine')
    p.add_argument('--alpha')
    p.add_argument('--seed',type=int)
    p.add_argument('--expand',action='store_true')
    a = p.parse_args()
    if a.expand:
        assert pilot()['status']=='SEED-ACTIVE'
        for machine in ('SMD_1-8','SMD_2-1'):
            for alpha in ('0.5','1.0','5.0'):
                for seed in range(5):
                    path = REPORT/'runs'/f'{machine}_alpha_{alpha}_seed_{seed}_native_c3.json'
                    if path.exists():
                        assert json.loads(path.read_text())['error'] is None
                        continue
                    if seed==0 and (machine,alpha)!=('SMD_1-8','1.0'):
                        continue
                    launch(machine,alpha,seed)
    else:
        launch(a.machine,a.alpha,a.seed)


if __name__=='__main__':
    main()
