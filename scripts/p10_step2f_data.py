"""Step2f-A numeric splits and pushed-seal gate. Neural path deliberately disabled."""
import json,subprocess
from pathlib import Path
import numpy as np
from p10_step2e_data import ROOT,sha,save,git,utc
OUT=ROOT/'research/writable_neural_memory_p10/step2f'
RAW=ROOT/'data/step2e'
CONFIG={'phase':'A','neural_training':False,'cases':[f'case{i:02}' for i in range(1,6)],'seeds':[11,22,33],
 'ops':['W1','W2_f0995','W3_b01'],'w':8,'dk':128,'k':5,'fit_frac':.8,'sd_floor':.02,'clip':20.,
 'views':['step2e_regression_clip','fit_only_clip','fit_only_no_clip'],'window':256,'stride':128,'start_end':256,
 'manifold_shrinkage':.1,'manifold_ridge':1e-6,'near_constant_raw_sd':.02,'top_k':5,'pca_components':5,
 'clean_gap':'third-clean-block close (gap>2); no test writes in evidence-only frozen M0',
 'A0':['log_score','cv'],'A1_extra':[f'mean_r_{j}' for j in range(53)],
 'A2_extra':['maha_mean','maha_centroid','cov_distance','corr_distance','manip_energy','near_constant_energy','top5_energy','direction_cosine'],
 'probe_C':1.,'probe_seed':731,'probe_max_iter':2000,
 'folds':[{'train':['case03','case05'],'test':['case01','case02','case04']},{'train':['case01','case02','case04'],'test':['case03','case05']}],
 'probe_claim':'diagnostic supervised upper bound only; no shared run/SP-intervention family per fold; SP seed family still shared across folds',
 'primary':'seed11/W1; windows matched by exact end index and wholly FAULT vs wholly NORMAL_B',
 'cv_diagnostic_threshold':.10}

def prepare():
 OUT.mkdir(exist_ok=True)
 old=json.loads((ROOT/'research/writable_neural_memory_p10/step2e/dataset_manifest.json').read_text())
 rows=[]
 for d in old['datasets']:
  n=d['train_count'];f=int(n*.8)
  rows.append({'id':d['id'],'fit_rows':[0,f],'cal_rows':[f,n],'test_rows':[0,d['files']['test']['shape'][0]],'files':d['files'],
    'fit_source':'source-normal prefix first80%; CAL last20% entirely held out from primary scaler/memory/manifold fitting',
    'regression_only_exception':'old Step2e scaler full train replays prior sealed control; not a new primary fitted arm'})
 save(OUT/'data_split_manifest.json',{'datasets':rows,'event_runs':'same five sealed Step2e literal cases; not new holdout','raw_host':'ssh kuo / spark-3994','no_local_raw_download':True,'source_metadata_git_blob':git('rev-parse','HEAD:research/writable_neural_memory_p10/step2e/evaluator_metadata.json'),'old_seal_sha256':sha(ROOT/'research/writable_neural_memory_p10/step2e/run/seal.json')})
 save(OUT/'representation_config.json',CONFIG)

def load_numeric(d):
 for f in d['files'].values():assert sha(RAW/f['file'])==f['sha256']
 tr=np.load(RAW/d['files']['train']['file']);te=np.load(RAW/d['files']['test']['file'])
 assert tr.shape[1]==te.shape[1]==53 and np.isfinite(tr).all() and np.isfinite(te).all()
 a,b=d['fit_rows'];c,e=d['cal_rows'];assert a==0 and b==c and e==len(tr)
 return tr[:b],tr[b:],te

def verify():
 run=OUT/'run';s=json.loads((run/'seal.json').read_text());assert s['labels_read']==0 and s['config']==CONFIG
 for p,h in s['files'].items():assert sha(run/p)==h
 for p,h in s['code'].items():assert sha(ROOT/p)==h
 for p,h in s['raw'].items():assert sha(RAW/p)==h
 assert git('hash-object',str(ROOT/'research/writable_neural_memory_p10/step2e/evaluator_metadata.json'))==s['source_metadata_git_blob']
 path=str((run/'seal.json').relative_to(ROOT));commit=git('log','-1','--format=%H','--',path);assert commit
 assert git('hash-object',str(run/'seal.json'))==git('rev-parse',commit+':'+path)
 remote=git('ls-remote','origin','refs/heads/research/p7-p10-segment-memory').split()[0]
 subprocess.run(['git','merge-base','--is-ancestor',commit,remote],cwd=ROOT,check=True)
 return {'seal_commit':commit,'remote_sha':remote,'seal_sha256':sha(run/'seal.json'),'utc':utc()}

if __name__=='__main__':prepare()
