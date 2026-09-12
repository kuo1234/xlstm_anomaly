"""Bounded native fidelity investigation; no retraining or seed expansion."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time
import numpy as np
from phase_c_run import ROOT, OFFICIAL, PIN, digest

REPORT = ROOT/'reports/phase_c_v2'
OLD = ROOT/'reports/phase_c'
AMENDMENT = 'a8e0730'


def record(machine,alpha,mode):
    directory = OLD if mode=='native' else REPORT
    return json.loads((directory/'runs'/f'{machine}_alpha_{alpha}_seed_0_{mode}.json').read_text())


def score_path(r):
    return Path(r['working_directory'])/'results'/r['machine']/'MLP'/r['alpha']/'test_scores_w_tta.npy'


def events(r):
    return json.loads((REPORT/'logs'/f'{r["tag"]}.audit_events.json').read_text())


def equal_runs(a,b,trace=True):
    checks = dict(scores_exact=np.array_equal(np.load(score_path(a)),np.load(score_path(b))),
        score_file_hash_equal=digest(score_path(a))==digest(score_path(b)),
        final_model_equal=a['final_model_sha256']==b['final_model_sha256'],
        metrics_equal=a['observed']==b['observed'],
        update_count_equal=a['official_counters']['n_adapt']==b['official_counters']['n_adapt'],
        config_equal=a['resolved_config']==b['resolved_config'],
        checkpoint_equal=a['checkpoint_sha256']==b['checkpoint_sha256'])
    if trace:
        checks.update(all_selection_commit_exposure_step_batch_events_equal=events(a)==events(b),
            initial_model_equal=a['audit']['initial_model_sha256']==b['audit']['initial_model_sha256'],
            initial_rng_equal=a['audit']['initial_rng_sha256']==b['audit']['initial_rng_sha256'])
    assert all(checks.values()),checks
    return checks


def replay_gate():
    original = record('SMD_1-8','0.5','native')
    a,b = [record('SMD_1-8','0.5',m) for m in ('native_replay_1','native_replay_2')]
    return dict(status='PASS',original_vs_replay1=equal_runs(original,a,False),
                original_vs_replay2=equal_runs(original,b,False),replay1_vs_replay2=equal_runs(a,b))


def authorize(machine,alpha,mode):
    committed = subprocess.check_output(['rtk','git','show',f'{AMENDMENT}:reports/phase_c_v2/amendment.md'])
    assert committed==(REPORT/'amendment.md').read_bytes()
    subprocess.run(['rtk','git','merge-base','--is-ancestor',AMENDMENT,'origin/main'],check=True)
    if mode in ('native_replay_1','native_replay_2'):
        assert (machine,alpha)==('SMD_1-8','0.5')
    elif mode=='native_v2':
        assert machine=='SMD_2-1' and alpha in ('0.5','1.0','5.0')
        replay_gate()
    elif mode in ('native_label_control','native_label_permuted'):
        assert (machine,alpha)==('SMD_1-8','5.0')
        replay_gate()
    else:
        raise AssertionError('Not authorized')


def environment():
    import torch
    frozen = json.loads((OLD/'environment.json').read_text())
    assert sys.version==frozen['python']
    code = json.loads((OLD/'official_code_hashes.json').read_text())
    assert all(digest(OFFICIAL/p)==h for p,h in code.items())
    packages = {d.metadata['Name']:d.version for d in importlib.metadata.distributions()}
    differences = {k:(v,packages.get(k)) for k,v in frozen['packages'].items() if packages.get(k)!=v}
    assert not differences, differences
    current = dict(torch=torch.__version__,cuda=torch.version.cuda,cudnn=torch.backends.cudnn.version(),
        gpu=torch.cuda.get_device_name(),capability=list(torch.cuda.get_device_capability()))
    assert all(current[k]==frozen[k] for k in current),(current,frozen)
    current.update(packages=packages,python=sys.version,amendment_commit=AMENDMENT,
        frozen_environment_sha256=digest(OLD/'environment.json'),frozen_package_versions_equal=True,
        official_commit=PIN,compatibility_patches=[],telemetry='WANDB_MODE=disabled; official WANDB.ENABLE=False')
    (REPORT/'environment.json').write_text(json.dumps(current,indent=2)+'\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--machine',required=True)
    p.add_argument('--alpha',required=True)
    p.add_argument('--mode',required=True)
    a = p.parse_args()
    authorize(a.machine,a.alpha,a.mode)
    tag = f'{a.machine}_alpha_{a.alpha}_seed_0_{a.mode}'
    (REPORT/'logs').mkdir(parents=True,exist_ok=True)
    command = ['rtk',str(ROOT/'data/phase_c/venv/bin/python'),str(ROOT/'scripts/phase_c_run.py'),
        '--machine',a.machine,'--alpha',a.alpha,'--mode',a.mode,'--seed','0']
    with (REPORT/'commands.txt').open('a') as f:
        f.write('PYTHONDONTWRITEBYTECODE=1 WANDB_MODE=disabled '+shlex.join(command)+'\n')
    env = dict(os.environ,PYTHONDONTWRITEBYTECODE='1',WANDB_MODE='disabled')
    start = time.perf_counter()
    with (REPORT/'logs'/f'{tag}.stdout.log').open('x') as out,(REPORT/'logs'/f'{tag}.stderr.log').open('x') as err:
        r = subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=err)
    (REPORT/'logs'/f'{tag}.launch.json').write_text(json.dumps(dict(command=command,returncode=r.returncode,
        process_wall_seconds=time.perf_counter()-start),indent=2)+'\n')
    if r.returncode:
        print((REPORT/'logs'/f'{tag}.stderr.log').read_text()[-6000:])
        raise SystemExit(r.returncode)
    result = record(a.machine,a.alpha,a.mode)
    print(json.dumps({k:result[k] for k in ('tag','status','observed','runtime_seconds','final_model_sha256')}))
    if a.mode=='native_replay_2':
        gate = replay_gate()
        (REPORT/'deterministic_replay.json').write_text(json.dumps(gate,indent=2)+'\n')
        print('Deterministic replay:',gate)


if __name__=='__main__':
    main()
