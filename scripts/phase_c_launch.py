"""Sequential launch with durable stdout/stderr and a strict expansion gate."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT/'reports/phase_c'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--machine',required=True)
    p.add_argument('--alpha',required=True)
    p.add_argument('--mode',default='native')
    p.add_argument('--seed',type=int,default=0)
    a = p.parse_args()
    existing = [json.loads(f.read_text()) for f in (REPORT/'runs').glob('*.json')]
    if a.mode=='native':
        assert not any(r['mode']=='native' and r['status']!='PASS' for r in existing),'Reproduction expansion stopped: investigate first'
        if a.seed!=0:
            assert len([r for r in existing if r['mode']=='native' and r['seed']==0 and r['status']=='PASS'])==6,'Five-seed gate closed'
    tag = f'{a.machine}_alpha_{a.alpha}_seed_{a.seed}_{a.mode}'
    (REPORT/'logs').mkdir(parents=True,exist_ok=True)
    command = ['rtk',str(ROOT/'data/phase_c/venv/bin/python'),str(ROOT/'scripts/phase_c_run.py'),
               '--machine',a.machine,'--alpha',a.alpha,'--mode',a.mode,'--seed',str(a.seed)]
    with (REPORT/'commands.txt').open('a') as f:
        f.write(shlex.join(command)+'\n')
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE']='1'
    env['WANDB_MODE']='disabled'
    start = time.perf_counter()
    with (REPORT/'logs'/f'{tag}.stdout.log').open('x') as out, (REPORT/'logs'/f'{tag}.stderr.log').open('x') as err:
        result = subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=err)
    elapsed = time.perf_counter()-start
    (REPORT/'logs'/f'{tag}.launch.json').write_text(json.dumps(dict(command=command,returncode=result.returncode,
        total_process_wall_seconds=elapsed),indent=2)+'\n')
    print(tag,'returncode',result.returncode,'process_seconds',elapsed,flush=True)
    if result.returncode:
        print((REPORT/'logs'/f'{tag}.stderr.log').read_text()[-5000:])
        raise SystemExit(result.returncode)
    record = json.loads((REPORT/'runs'/f'{tag}.json').read_text())
    print({k:record.get(k) for k in ('status','observed','discrepancy','runtime_seconds','peak_gpu_allocated_bytes')})


if __name__=='__main__':
    main()
