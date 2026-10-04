"""Official range preparation and seal-gated evaluator; raw arrays stay on ssh kuo."""
import json, hashlib, subprocess, datetime
from pathlib import Path
import h5py
import numpy as np
from p10_step2d_tep_inspect import OfficialRangeFile, observations

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/writable_neural_memory_p10/step2e'
RAW=ROOT/'data/step2e'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
def git(*a):return subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()

def prepare():
    official=ROOT/'data/step2d/official';api=json.loads((official/'article_v1.json').read_text())
    assert api['doi']=='10.11583/DTU.13385936.v1'
    selection=json.loads((OUT/'selection.json').read_text())
    info=next(x for x in api['files'] if x['name']=='TEP_Mode1.h5')
    rf=OfficialRangeFile(info,official/'ranges_mode1')
    datasets=[];meta=[]
    with h5py.File(rf,'r') as f:
        for item in selection['cases']:
            # Literal preselected path; no replacement or outcome filtering.
            if item['path'] not in f:raise ValueError('missing fixed case: '+item['id'])
            g=f[item['path']]
            if int(g.attrs['simTerminatedSuccessfully'][0])!=1:raise ValueError('preselected case stopped')
            t,x=observations(g['processdata'][()]);n=int(np.searchsorted(t,20))
            assert n>=320 and np.all(t[:n]<20) and np.all(t[n:]>=20)
            files={}
            for name,arr in [('train',x[:n]),('test',x[n:]),('timestamps',t[n:])]:
                p=RAW/f'{item["id"]}_{name}.npy';np.save(p,arr);files[name]={'file':p.name,'sha256':sha(p),'shape':list(arr.shape)}
            datasets.append({'id':item['id'],'files':files,'dimension':53,'train_count':n,'train_end_hours':20})
            profiles={k:g[k][()].tolist() for k in ('idv_init','setpoint_init','time_info')}
            meta.append({**item,'native_seed':int(g.attrs['seed'][0]),'profiles':profiles,'initial_mode':int(g.attrs['modeAtInit'][0]),'t_ramp_hours':float(g.attrs['tRampSetpoint'][0])})
            print(item['id'],len(t),n,flush=True)
    ranges=[{'offset':p.stem,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(rf.root.glob('*.bin'))]
    save(OUT/'dataset_manifest.json',{'utc':utc(),'datasets':datasets,'official_doi':api['doi'],'selection_sha256':sha(OUT/'selection.json'),'source_api_sha256':sha(official/'article_v1.json'),'range_blocks':ranges,'full_hdf5_hash_verified':False,'raw_host':'spark-3994','raw_downloaded_locally':False})
    save(OUT/'evaluator_metadata.json',{'cases':meta,'source':selection['source'],'states':{'setpoint':['NORMAL_A','TRANSITION','NORMAL_B'],'fault':['NORMAL_A','FAULT']},'boundaries_hours':[30,70],'warmup_choice':'no source warmup exclusion; first 20h normal is train, last 10h pre-event is held-out test'})

def states(time,arm):
    t=np.asarray(time);assert arm in ('setpoint','fault')
    return np.where(t<30,'NORMAL_A',np.where((t>=70)&(arm=='setpoint'),'NORMAL_B','TRANSITION' if arm=='setpoint' else 'FAULT'))

def verify(run):
    run=Path(run);s=json.loads((run/'seal.json').read_text())
    assert s['labels_read_by_runner']==0 and s['cv_max']==.10 and not s['posthoc']
    assert s['frozen_config']['cv_max']==.10
    assert git('hash-object',str(OUT/'evaluator_metadata.json'))==s['evaluator_metadata_git_blob']
    for p,h in s['files'].items():assert sha(run/p)==h,'sealed artifact changed '+p
    for p,h in s['code'].items():assert sha(ROOT/p)==h,'sealed code changed '+p
    for p,h in s['raw'].items():assert sha(RAW/p)==h,'raw changed '+p
    # The exact seal blob must occur in a commit already reachable on GitHub.
    path=str((run/'seal.json').relative_to(ROOT));commit=git('log','-1','--format=%H','--',path)
    assert commit
    assert git('hash-object',str(run/'seal.json'))==git('rev-parse',commit+':'+path)
    remote=git('ls-remote','origin','refs/heads/research/p7-p10-segment-memory').split()[0]
    subprocess.run(['git','merge-base','--is-ancestor',commit,remote],cwd=ROOT,check=True)
    return {'seal_commit':commit,'seal_sha256':sha(run/'seal.json'),'remote_sha':remote,'utc':utc()}

if __name__=='__main__':prepare()
