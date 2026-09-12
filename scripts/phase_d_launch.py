"""Durable logging for Phase D commands; runs are explicitly chosen by caller."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/phase_d'


def main():
    tag,script,*args=sys.argv[1:]
    command=['rtk',str(ROOT/'data/phase_c/venv/bin/python'),str(ROOT/script),*args]
    (REPORT/'logs').mkdir(parents=True,exist_ok=True)
    with (REPORT/'commands.txt').open('a') as f: f.write(shlex.join(command)+'\n')
    t=time.perf_counter()
    with (REPORT/'logs'/f'{tag}.stdout.log').open('x') as out,(REPORT/'logs'/f'{tag}.stderr.log').open('x') as err:
        r=subprocess.run(command,cwd=ROOT,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',WANDB_MODE='disabled'),stdout=out,stderr=err)
    (REPORT/'logs'/f'{tag}.launch.json').write_text(json.dumps(dict(command=command,returncode=r.returncode,wall_seconds=time.perf_counter()-t),indent=2)+'\n')
    print((REPORT/'logs'/f'{tag}.stdout.log').read_text()[-4000:])
    if r.returncode: print((REPORT/'logs'/f'{tag}.stderr.log').read_text()[-4000:])
    raise SystemExit(r.returncode)


if __name__=='__main__': main()
