"""Official bounded source curator; healthy output contains preevent observations only."""
import json,subprocess,re
from pathlib import Path
import h5py,numpy as np
from p10_step2e_data import ROOT,sha,save,git,utc,states
from p10_step2d_tep_inspect import OfficialRangeFile,observations
from p10_decision_pilot1_data import check_profiles
OUT=ROOT/'research/writable_neural_memory_p10/left_point_pilot';RAW=ROOT/'data/left_point_pilot';UP=RAW/'upstream'

def check_upstream():
 manifest=json.loads((OUT/'upstream_manifest.json').read_text());assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=UP,text=True).strip()==manifest['commit']
 for f,h in manifest['files'].items():assert sha(UP/f)==h
 for anchor,name in [('PSM','primary'),('SMD','robustness')]:
  c=json.loads((UP/f'configs/{anchor}/model_configs_Left.json').read_text());c['enc_in']=53;assert c==json.loads((OUT/f'left_config_{name}.json').read_text())

def prepare():
 check_upstream();official=ROOT/'data/step2d/official';api=json.loads((official/'article_v1.json').read_text());assert api['doi']=='10.11583/DTU.13385936.v1'
 selected=json.loads((OUT/'selection.json').read_text());rf=OfficialRangeFile(next(i for i in api['files'] if i['name']=='TEP_Mode1.h5'),official/'ranges_mode1')
 (RAW/'arrays').mkdir(exist_ok=True);healthy=[];events=[];meta=[];logs=[]
 with h5py.File(rf,'r') as f:
  for item in selected['healthy']+selected['events']:
   logs.append({'id':item['id'],'utc':utc(),'purpose':'source profile/normal-prefix/provenance compatibility curation, not model outcome','source_metadata_read':True});save(OUT/'curation_access_log.json',logs)
   if item['path'] not in f:raise ValueError('BLOCKED missing fixed path '+item['path'])
   g=f[item['path']];assert int(g.attrs['simTerminatedSuccessfully'][0])==1,'BLOCKED stopped';assert int(g.attrs['modeAtInit'][0])==1
   profiles={k:g[k][()].tolist() for k in ('idv_init','setpoint_init','time_info')};seed=int(g.attrs['seed'][0]);ramp=float(g.attrs['tRampSetpoint'][0])
   if 'role' in item:
    # Validate source profiles BEFORE materializing strictly nominal prefix; never read fault processdata rows.
    check_profiles({'arm':'fault','path':item['path']},profiles,ramp)
    t,x=observations(g['processdata'][:600]);keep=t<30;t=t[keep];x=x[keep];assert len(x)>=599 and t[-1]<30
    path=RAW/'arrays'/f'{item["id"]}.npy';np.save(path,x)
    healthy.append({'id':item['id'],'role':item['role'],'file':path.name,'sha256':sha(path),'shape':list(x.shape),'native_seed':seed,'source_path':item['path'],'normal_source':'initial Mode1 and verified source IDV activation30h; saved t<30 only','time_first':float(t[0]),'time_last':float(t[-1])})
   else:
    check_profiles(item,profiles,ramp);t,x=observations(g['processdata'][()]);n=int(np.searchsorted(t,20));assert n>=399 and t[-1]>=99
    files={}
    for key,a in [('train',x[:n]),('test',x[n:]),('timestamps',t[n:])]:
     path=RAW/'arrays'/f'{item["id"]}_{key}.npy';np.save(path,a);files[key]={'file':path.name,'sha256':sha(path),'shape':list(a.shape)}
    events.append({'id':item['id'],'files':files,'train_count':n,'test_count':len(x)-n,'fit_count':int(n*.8)});meta.append({**item,'native_seed':seed,'ramp_hours':ramp,'profiles':profiles})
   print(item['id'],'acquired nominal-only' if 'role' in item else 'acquired event',flush=True)
 # Role seed overlap blocks instead of replacing outcomes. Duplicate realization within same role is disclosed.
 for role in ('validation','calibration'):
  others={d['native_seed'] for d in healthy if d['role']!=role};assert not any(d['native_seed'] in others for d in healthy if d['role']==role),'BLOCKED shared healthy role seed'
 assert not ({d['native_seed'] for d in healthy}&{d['native_seed'] for d in meta}),'BLOCKED training/test seed overlap'
 save(OUT/'healthy_train_manifest.json',{'datasets':healthy,'roles':'50train/4validation/4calibration physically/native-seed disjoint; strictly nominal prefix t<30','selection_sha256':sha(OUT/'selection.json')})
 save(OUT/'healthy_numeric_manifest.json',{'datasets':[{k:d[k] for k in ('id','role','file','sha256','shape')} for d in healthy]})
 save(OUT/'dataset_manifest.json',{'datasets':events,'doi':api['doi'],'source_api_sha256':sha(official/'article_v1.json'),'range_blocks':[{'file':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(rf.root.glob('*.bin'))],'full_hdf5_hash_verified':False,'raw_host':'ssh kuo','local_download':False})
 save(OUT/'evaluator_metadata.json',{'cases':meta,'boundaries':[30,70],'source':'Author A.3.2 30-40-30 split; curation access before runner disclosed'})

def healthy_numeric(role):
 manifest=json.loads((OUT/'healthy_numeric_manifest.json').read_text());rows=[d for d in manifest['datasets'] if d['role']==role];assert rows
 arrays=[]
 for d in rows:
  path=RAW/'arrays'/d['file'];assert sha(path)==d['sha256'];a=np.load(path);assert a.shape[1]==53 and np.isfinite(a).all();arrays.append(a)
 return arrays

def event_numeric(d):
 for f in d['files'].values():assert sha(RAW/'arrays'/f['file'])==f['sha256']
 return [np.load(RAW/'arrays'/d['files'][k]['file']) for k in ('train','test')]

def verify():
 check_upstream();run=OUT/'run';s=json.loads((run/'seal.json').read_text());assert s['labels_read_by_runner']==0
 for p,h in s['files'].items():assert sha(run/p)==h
 for p,h in s['code'].items():assert sha(ROOT/p)==h
 for p,h in s['protocol_files'].items():assert sha(OUT/p)==h
 for p,h in s['raw'].items():assert sha(RAW/'arrays'/p)==h
 for p,h in s['checkpoints'].items():assert sha(RAW/'checkpoints'/p)==h
 path=str((run/'seal.json').relative_to(ROOT));commit=git('log','-1','--format=%H','--',path);assert commit
 assert git('hash-object',str(run/'seal.json'))==git('rev-parse',commit+':'+path)
 remote=git('ls-remote','origin','refs/heads/research/p7-p10-segment-memory').split()[0];subprocess.run(['git','merge-base','--is-ancestor',commit,remote],cwd=ROOT,check=True)
 return {'seal_commit':commit,'remote_sha':remote,'seal_sha256':sha(run/'seal.json'),'utc':utc()}
if __name__=='__main__':prepare()
