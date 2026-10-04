"""Fixed official acquisition and seal gate; metadata curation is explicitly logged."""
import json,subprocess,re
from pathlib import Path
import h5py,numpy as np
from p10_step2e_data import ROOT,sha,save,git,utc,states
from p10_step2d_tep_inspect import OfficialRangeFile,observations
OUT=ROOT/'research/writable_neural_memory_p10/decision_pilot1'
RAW=ROOT/'data/decision_pilot1'
CONFIG={'cases':[f'pilot0{i}' for i in range(1,7)],'seeds':[11,22,33],'ops':['W1','W2_f0995','W3_b01'],'views':['fit_only_clip','fit_only_no_clip'],'w':8,'dk':128,'k':5,'fit_frac':.8,'sd_floor':.02,'clip':20.,'window':256,'stride':128,'start_end':256,'features':['log_score','cv','top5_energy'],'direction':'fault-high top5','primary':'seed11/W1/fit_only_clip','cv_descriptive':.10,'neural_training':False,'test_writes':0}

def check_profiles(item,profiles,ramp):
 idv=np.array(profiles['idv_init']);sp=np.array(profiles['setpoint_init']);time=np.array(profiles['time_info'])[0]
 assert idv.shape==(3,28) and sp.shape==(3,12)
 assert np.all(idv[0]==0) and np.allclose(time[:3],[0,100,.05])
 if item['arm']=='setpoint':
  assert np.all(idv==0);idx=int(re.search(r'/SP(\d+)/',item['path']).group(1))-1
  mag=int(re.search(r'SpMagnitude(\d+)$',item['path']).group(1))/100
  expected=sp[0].copy();expected[idx]*=mag;assert np.allclose(sp[1],expected)
  assert np.all(sp[2]==30) and ramp==int(re.search(r'tRamp_(\d+)/',item['path']).group(1))
 else:
  idx=int(re.search(r'/IDV(\d+)/',item['path']).group(1))-1
  expected=np.zeros_like(idv);expected[1,idx]=1;expected[2,idx]=30
  assert np.array_equal(idv,expected) and np.array_equal(sp[0],sp[1])
 return True

def prepare():
 official=ROOT/'data/step2d/official';api=json.loads((official/'article_v1.json').read_text());assert api['doi']=='10.11583/DTU.13385936.v1'
 selected=json.loads((OUT/'selection.json').read_text())['cases'];assert [i['id'] for i in selected]==CONFIG['cases']
 RAW.mkdir(exist_ok=True);rf=OfficialRangeFile(next(i for i in api['files'] if i['name']=='TEP_Mode1.h5'),official/'ranges_mode1')
 rows=[];metadata=[];log=[]
 with h5py.File(rf,'r') as f:
  for item in selected:
   log.append({'case':item['id'],'utc':utc(),'purpose':'source compatibility/provenance curator only; no detector outcome selection','source_profiles_read':True});save(OUT/'curation_access_log.json',log)
   if item['path'] not in f: raise ValueError('BLOCKED missing fixed path '+item['path'])
   g=f[item['path']];assert int(g.attrs['simTerminatedSuccessfully'][0])==1,'BLOCKED stopped';assert int(g.attrs['modeAtInit'][0])==1
   profiles={k:g[k][()].tolist() for k in ('idv_init','setpoint_init','time_info')}
   check_profiles(item,profiles,float(g.attrs['tRampSetpoint'][0]))
   t,x=observations(g['processdata'][()]);n=int(np.searchsorted(t,20));assert n>=320 and t[-1]>=99 and np.isfinite(x).all()
   files={}
   for name,a in [('train',x[:n]),('test',x[n:]),('timestamps',t[n:])]:
    path=RAW/f'{item["id"]}_{name}.npy';np.save(path,a);files[name]={'file':path.name,'sha256':sha(path),'shape':list(a.shape)}
   rows.append({'id':item['id'],'files':files,'fit_count':int(n*.8),'cal_count':n-int(n*.8),'test_count':len(x)-n,'train_count':n})
   metadata.append({**item,'native_seed':int(g.attrs['seed'][0]),'t_ramp_hours':float(g.attrs['tRampSetpoint'][0]),'profiles':profiles})
   print(item['id'],'source acquired',flush=True)
 save(OUT/'evaluator_metadata.json',{'cases':metadata,'states_source':'Author thesis A.3.2 applies30-40-30 split to faults/SP; source metadata curator access prior to runner seal disclosed.'})
 save(OUT/'dataset_manifest.json',{'datasets':rows,'raw_host':'ssh kuo','local_download':False,'official_doi':api['doi'],'source_api_sha256':sha(official/'article_v1.json'),'full_hdf5_hash_verified':False,'range_blocks':[{'file':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(rf.root.glob('*.bin'))],'selection_sha256':sha(OUT/'selection.json'),'config':CONFIG})
 save(OUT/'representation_config.json',CONFIG)

def load_numeric(d):
 for f in d['files'].values():assert sha(RAW/f['file'])==f['sha256']
 tr=np.load(RAW/d['files']['train']['file']);te=np.load(RAW/d['files']['test']['file']);n=d['fit_count']
 assert tr.shape[1]==te.shape[1]==53 and np.isfinite(tr).all() and np.isfinite(te).all()
 return tr[:n],tr[n:],te

def verify():
 run=OUT/'run';s=json.loads((run/'seal.json').read_text());assert s['labels_read_by_runner']==0 and s['config']==CONFIG
 for p,h in s['files'].items():assert sha(run/p)==h,'artifact modified'
 for p,h in s['code'].items():assert sha(ROOT/p)==h,'code modified'
 for p,h in s['raw'].items():assert sha(RAW/p)==h,'raw modified'
 for p,h in s['protocol_files'].items():assert sha(OUT/p)==h,'protocol modified'
 path=str((run/'seal.json').relative_to(ROOT));commit=git('log','-1','--format=%H','--',path);assert commit
 assert git('hash-object',str(run/'seal.json'))==git('rev-parse',commit+':'+path)
 remote=git('ls-remote','origin','refs/heads/research/p7-p10-segment-memory').split()[0]
 subprocess.run(['git','merge-base','--is-ancestor',commit,remote],cwd=ROOT,check=True)
 return {'seal_commit':commit,'remote_sha':remote,'seal_sha256':sha(run/'seal.json'),'utc':utc()}
if __name__=='__main__':prepare()
