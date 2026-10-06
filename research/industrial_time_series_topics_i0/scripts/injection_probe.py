"""Frozen four-fit independent-quality feasibility: existing Ridge/split conformal."""
import csv,hashlib,io,json,math,platform,time,zipfile
from pathlib import Path
import numpy as np
ROOT=Path('research/industrial_time_series_topics_i0');CACHE=Path('data/industrial_time_series_topics_i0')
def read_num(s):return float(s.replace(',','.'))
def solve(x,y,predict):
 m=x.mean(0);sd=x.std(0);sd[sd==0]=1;x=(x-m)/sd;p=(predict-m)/sd;c=y.mean()
 matrix=x.T@x+10*np.eye(x.shape[1]);rhs=x.T@(y-c);w=np.linalg.solve(matrix,rhs);assert np.max(np.abs(matrix@w-rhs))<1e-7
 return p@w+c

def run():
 start=time.perf_counter();seal=json.loads((ROOT/'provenance/injection_probe_seal.json').read_text());p=CACHE/'injection_dataset1.zip'
 assert hashlib.sha256(p.read_bytes()).hexdigest()==seal['asset_sha256']
 assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==seal['script_sha256']
 with zipfile.ZipFile(p) as z:
  scalar=list(csv.DictReader(io.StringIO(z.read('dataset1/ds1_scalar_and_quality.csv').decode('utf-8-sig'))));scalar.sort(key=lambda r:int(r['cycle_counter']));ids=[r['cycle_counter'] for r in scalar];assert ids==seal['labelled_cycle_ids']
  names=[n for n in scalar[0] if n not in ['cycle_counter','weight','distanceA']];base=np.array([[read_num(r[n]) for n in names] for r in scalar]);target=np.array([read_num(r['weight']) for r in scalar]);extra=[]
  for name in ['injectionflow','injectionpressure']:
   reader=csv.reader(io.StringIO(z.read('dataset1/ds1_timeseries_'+name+'.csv').decode('utf-8-sig')));header=next(reader);rows=list(reader);a=np.array([[read_num(x) for x in row] for row in rows]);ts=a[:,0];columns={cid:i+1 for i,cid in enumerate(header[1:])};v=a[:,[columns[cid] for cid in ids]]
   integral=np.sum((v[:-1]+v[1:])*0.5*np.diff(ts)[:,None],axis=0)
   extra.extend([v.mean(0),v.std(0),v.max(0),integral])
 extra=np.array(extra).T;assert np.isfinite(base).all() and np.isfinite(extra).all() and np.isfinite(target).all()
 n=len(ids);a=int(n*.6);b=a+int(n*.2);out=[]
 for protocol in ['future_cycles','random_diagnostic']:
  index=np.arange(n) if protocol=='future_cycles' else np.random.default_rng(20261007).permutation(n)
  train,cal,test=index[:a],index[a:b],index[b:];assert not set(train)&set(test)
  for arm,x in [('scalars',base),('scalars_curves',np.column_stack([base,extra]))]:
   predictions=solve(x[train],target[train],x[np.concatenate([cal,test])]);pc,pt=predictions[:len(cal)],predictions[len(cal):]
   residual=np.sort(np.abs(target[cal]-pc));k=math.ceil((len(cal)+1)*.9);q=residual[k-1] if k<=len(cal) else np.inf
   y=target[test];mse=np.mean((y-pt)**2);den=np.mean((y-y.mean())**2);mean_mse=np.mean((y-target[train].mean())**2)
   out.append({'protocol':protocol,'arm':arm,'features':x.shape[1],'train_n':len(train),'calibration_n':len(cal),'test_n':len(test),'test_cycle_ids':[ids[i] for i in test],'mse':float(mse),'rmse':float(np.sqrt(mse)),'mae':float(np.mean(np.abs(y-pt))),'r2':float(1-mse/den) if den else None,'train_mean_mse':float(mean_mse),'relative_mse_gain_vs_train_mean_percent':float(100*(mean_mse-mse)/mean_mse) if mean_mse else None,'coverage90':float(np.mean(np.abs(y-pt)<=q)),'half_width':float(q),'width':float(2*q),'quantile_order':k,'precision_or_metrology_savings_claimed':False})
 d={'scope':'One author dataset/cell: weight regression and empirical split-conformal diagnostic, not new method or guaranteed metrology replacement','fit_count':len(out),'neural_runs':0,'runtime_seconds':time.perf_counter()-start,'numpy':np.__version__,'python':platform.python_version(),'arms':out,'limitations':['Random and future protocols have different test populations','No recovered day/DoE condition groups or native quality-return timestamps','Cycle correlation and shift invalidate unconditional exchangeability assumptions','Full cycle features: no early prediction lead-time claim','Actual drawing tolerances/inspection costs not provided']}
 (ROOT/'results/injection_probe.json').write_text(json.dumps(d,indent=2,allow_nan=False)+'\n');print(json.dumps({'fits':len(out),'arms':[{k:r[k] for k in ['protocol','arm','rmse','r2','coverage90','width']} for r in out]},indent=2))
if __name__=='__main__':run()
