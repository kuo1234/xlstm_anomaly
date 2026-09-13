"""Launch the fixed ten-condition Phase F-v2 grid, at most two fresh processes."""
import json
import subprocess
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; REPORT=ROOT/'reports/phase_f_v2'

def main():
    config=json.loads((ROOT/'configs/phase_f_v2.json').read_text()); gates=json.loads((REPORT/'mechanical_gates.json').read_text())
    if gates.get('status')!='PASS': raise SystemExit('F-v2 mechanical gates are not PASS; launch forbidden')
    queue=[(arch,seed) for seed in config['detector_seeds'] for arch in ('xlstm','lstm')]
    (REPORT/'logs').mkdir(parents=True,exist_ok=True); active=[]; completed=[]; started=time.time()
    while queue or active:
        while queue and len(active)<config['max_concurrent_processes']:
            arch,seed=queue.pop(0); name=f'{arch}_{seed}'; log=(REPORT/'logs'/f'{name}.log').open('x')
            command=['rtk',str(ROOT/'data/phase_e2/venv/bin/python'),'-u',str(ROOT/'scripts/phase_f_v2_train.py'),arch,str(seed)]
            proc=subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
            active.append(dict(name=name,proc=proc,log=log,command=command,start=time.time())); print('START',name,'pid',proc.pid,flush=True)
        for item in active.copy():
            code=item['proc'].poll()
            if code is None: continue
            item['log'].close(); active.remove(item); completed.append(dict(run=item['name'],command=item['command'],exit_code=code,seconds=time.time()-item['start']))
            print('END',item['name'],'exit',code,flush=True)
            (REPORT/'execution.json').write_text(json.dumps(dict(completed=completed,remaining=queue,active=[v['name'] for v in active],wall_seconds=time.time()-started),indent=2)+'\n')
            if code:
                for other in active: other['proc'].terminate()
                for other in active: other['proc'].wait(); other['log'].close()
                raise SystemExit('Phase F-v2 STOP: failed run; active jobs terminated')
        time.sleep(2)
    if len(completed)!=10: raise SystemExit('Phase F-v2 incomplete grid')
    print('Phase F-v2 fixed grid complete',flush=True)

if __name__=='__main__': main()
