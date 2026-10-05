import ast,hashlib,json,sys,re,subprocess,datetime
from pathlib import Path
import numpy as np
root=Path('research/drift_aware_xlstm_m0s');sys.path.insert(0,str(root/'scripts'))
from metrics import group_decision
from common import load_config
cfg=load_config();results=root/'results'
read=lambda name:json.loads((results/name).read_text())
training,support,mechanism=read('training.json'),read('support.json'),read('mechanism.json')
gates,summary,execution=read('group_gates.json'),read('summary.json'),read('execution.json')
assert len(training)==90 and len(support)==90 and len(mechanism)==30
assert read('anomalies.json')==[] and execution['anomaly_status']=='NOT_RUN_GATED'
assert execution['elapsed_seconds']<=cfg['runtime']['max_total_wall_seconds']
expected={(m,g,b,s) for m in cfg['mechanisms'] for g in cfg['groups'] for b in cfg['backbones'] for s in cfg['model_seeds']}
assert set(tuple(r['job']) for r in training)==expected
assert set(tuple(r['job']) for r in support)==expected
assert set(tuple(r['job']) for r in mechanism)=={j for j in expected if j[0]=='dynamics'}
sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
for r in training:
 assert r['epochs']==30 and r['optimizer_updates']==120 and len(r['history'])==30
 assert r['selected_epoch']==min(range(30),key=lambda i:r['history'][i]['validation_mse'])+1
 assert r['normal_training_only'] and not r['labels_seen'] and not r['test_seen']
 assert r['elapsed_seconds']<=cfg['runtime']['max_training_seconds_per_run']
 for file,digest in r['checkpoint_hashes'].items():assert sha(Path('data/m0s-v1-a1')/r['name']/file)==digest
for r in support:
 assert r['checkpoint_hash']==sha(Path('data/m0s-v1-a1')/r['name']/'best.pt')
 assert r['parameters_frozen'] and all(v=='PASS' for k,v in r['trained_random_state_audit'].items() if isinstance(v,str))
for m in cfg['mechanisms']:
 for g in cfg['groups']:
  rr=[r for r in training if r['job'][:2]==[m,g]]
  assert len(set(r['train_hash'] for r in rr))==1 and len(set(r['validation_hash'] for r in rr))==1 and len(set(r['scaler_hash'] for r in rr))==1
  rr=[r for r in support if r['job'][:2]==[m,g]]
  assert len(set(r['common_b_suffix_hash'] for r in rr))==1
for b in cfg['backbones']:
 for g in cfg['groups']:
  rr=[r for r in mechanism if r['job'][:3]==['dynamics',g,b]]
  assert {'group':g,**group_decision(rr)}==gates['dynamics'][b][g]
  for r in rr:
   q=r['mechanism'];curve=np.array(q['suffix_trace']['history_harm_normalized'])
   assert abs(curve[32:64].mean()-q['history_harm_normalized'])<1e-8
   assert q['same_suffix_hash']==r['common_b_suffix_hash'] and q['primary_offsets']==[32,64]
assert summary['final_gate']=='NO_STATE_STALENESS_SIGNAL'
assert not any(r['mechanism']['history_harm_normalized']>=.05 for r in mechanism if r['job'][2]=='xlstm')
for b in cfg['backbones']:assert sum(g['mechanism_pre_ad'] for g in gates['dynamics'][b])==0
for p in root.rglob('*.json'):json.loads(p.read_text())
for p in root.rglob('*.py'):ast.parse(p.read_text())
seal=json.loads((root/'provenance/remote_freeze.json').read_text())
for path,digest in seal['files'].items():assert sha(path)==digest,path
old='ec87d80846f58caf504800079c17839e5a3acba0'
for path in ['configs/protocol.json']+['scripts/'+n+'.py' for n in ['generator','models','train','evaluate','metrics','summarize']]:
 original=subprocess.check_output(['git','show',old+':'+str(root/path)])
 assert (root/path).read_bytes()==original,path
for p in root.glob('*.md'):
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' not in link and not link.startswith('#'):assert (p.parent/link.split('#')[0]).exists(),(p,link)
value={'date':'2026-10-05','original_protocol_commit':old,'amended_execution_commit':seal['commit'],'final_gate':summary['final_gate'],
       'checks':{'complete_design':True,'training_epochs_updates_selection':True,'training_data_validation_scalers_matched':True,'raw_checkpoints_byte_verified':180,'trained_state_causality_audits':90,'common_suffix_hashes_matched':True,'group_gates_independently_recomputed':True,'curve_primary_metrics_recomputed':True,'frozen_files_unchanged_through_execution':True,'scientific_files_identical_to_original_freeze':True,'json_syntax_local_links':True,'visual_qa':'PASS: gate panels explicitly missing; physical-group range labeled, not CI'},
       'runs':{'training':90,'support':90,'paired_mechanism':30,'anomaly':0},'optimizer_updates':10800,'scientific_n':5,
       'limitations':['mean/correlation fail matched-LSTM B-support; no mechanism inference','AD NOT_RUN_GATED; anomaly-sensitivity/safety unknown','B-support does not independently prove equally adequate forecasting in A','bounded VAR(1) setup and finite history; no claim of universal absence','initial pre-update CPU/fork failure preserved; formal execution-only amendment'],
       'artifact_sha256':{str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='verification.json'}}
(root/'provenance/verification.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps({k:v for k,v in value.items() if k!='artifact_sha256'},indent=2))
