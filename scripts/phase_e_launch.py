"""Fresh bounded Phase E processes with durable logs and explicit environment."""
import json,os,shlex,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/phase_e'
if __name__=='__main__':
    tag,script,*args=sys.argv[1:]
    command=['rtk',str(ROOT/'data/phase_e/venv/bin/python'),str(ROOT/script),*args]
    (REPORT/'logs').mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',WANDB_MODE='disabled',MAX_JOBS='2',
        PATH=str(ROOT/'data/phase_e/venv/bin')+os.pathsep+os.environ['PATH'],
        TORCH_EXTENSIONS_DIR=str(ROOT/'data/phase_e/torch_extensions'))
    if tag.startswith('headers_'):
        env['XLSTM_EXTRA_INCLUDE_PATHS']=str(ROOT/'data/phase_e/python_headers/usr/include/python3.12')+':'+str(ROOT/'data/phase_e/python_headers/usr/include')
    with (REPORT/'commands.txt').open('a') as f:f.write(shlex.join(command)+'\n')
    start=time.perf_counter()
    with (REPORT/'logs'/f'{tag}.stdout.log').open('x') as out,(REPORT/'logs'/f'{tag}.stderr.log').open('x') as err:
        try:rc=subprocess.run(command,cwd=ROOT,env=env,stdout=out,stderr=err,timeout=1800).returncode
        except subprocess.TimeoutExpired:rc=124
    (REPORT/'logs'/f'{tag}.launch.json').write_text(json.dumps(dict(command=command,returncode=rc,
        wall_seconds=time.perf_counter()-start,timeout_seconds=1800,MAX_JOBS=2),indent=2)+'\n')
    print((REPORT/'logs'/f'{tag}.stdout.log').read_text()[-3000:])
    if rc:print((REPORT/'logs'/f'{tag}.stderr.log').read_text()[-3000:])
    raise SystemExit(rc)
