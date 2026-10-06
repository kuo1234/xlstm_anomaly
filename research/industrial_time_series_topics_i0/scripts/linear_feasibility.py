"""Sealed, bounded existing Ridge feasibility diagnostic; run only after seal push.

Uses NumPy only. This is one product code / factory, not a method benchmark.
"""
import csv
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import resource
import time
import zipfile
import numpy as np

ROOT = Path('research/industrial_time_series_topics_i0')
CACHE = Path('data/industrial_time_series_topics_i0')
CHANNELS = ['tbl_speed','fom','main_comp','tbl_fill','SREL','pre_comp','produced','waste','cyl_main','cyl_pre','stiffness','ejection']
MATERIALS = ['api_water','api_total_impurities','api_l_impurity','api_content','api_ps01','api_ps05','api_ps09','lactose_water','lactose_sieve0045','lactose_sieve015','lactose_sieve025','smcc_water','smcc_td','smcc_bd','smcc_ps01','smcc_ps05','smcc_ps09','starch_ph','starch_water']

def number(x):
    try:
        value = float(x)
        return value if math.isfinite(value) else np.nan
    except ValueError:
        return np.nan

def summaries(rows, cutoff):
    start = min(dt.datetime.fromisoformat(r['timestamp']) for r in rows)
    admitted = [r for r in rows if cutoff is None or dt.datetime.fromisoformat(r['timestamp']) <= start + dt.timedelta(minutes=cutoff)]
    times = np.array([(dt.datetime.fromisoformat(r['timestamp'])-start).total_seconds()/60 for r in admitted])
    features = []
    for column in CHANNELS:
        values = np.array([number(r[column]) for r in admitted]); valid = np.isfinite(values)
        if not valid.any():
            features.extend([np.nan]*4 + [0.0]); continue
        v, t = values[valid], times[valid]
        denominator = float(np.sum((t-t.mean())**2))
        slope = float(np.sum((t-t.mean())*(v-v.mean())) / denominator) if denominator else 0.0
        features.extend([float(v.mean()),float(v.std()),float(v[-1]),slope,float(valid.mean())])
    return features

def fit_predict(train_x, train_y, predict_x, alpha):
    med = np.array([np.median(c[np.isfinite(c)]) if np.isfinite(c).any() else 0.0 for c in train_x.T])
    tx = np.where(np.isfinite(train_x),train_x,med); px = np.where(np.isfinite(predict_x),predict_x,med)
    mean, scale = tx.mean(axis=0), tx.std(axis=0); scale[scale == 0] = 1.0
    tx, px = (tx-mean)/scale, (px-mean)/scale
    center = train_y.mean()
    gram = tx.T @ tx + alpha*np.eye(tx.shape[1]); rhs = tx.T @ (train_y-center)
    coef = np.linalg.solve(gram,rhs)
    assert np.max(np.abs(gram@coef-rhs)) < 1e-7
    return px@coef + center

def metrics(actual,predicted):
    mse=float(np.mean((actual-predicted)**2));mae=float(np.mean(np.abs(actual-predicted)))
    variance=float(np.mean((actual-actual.mean())**2))
    return {'mse_original_scale':mse,'mae_original_scale':mae,'rmse_original_scale':math.sqrt(mse),'r2':1-mse/variance if variance else None,'n_batches':len(actual)}

def run():
    started=time.perf_counter();manifest=json.loads((ROOT/'provenance/linear_probe_seal.json').read_text())
    assert manifest['status']=='FROZEN_BEFORE_FIT'
    for asset in manifest['assets']:
        assert hashlib.sha256(Path(asset['path']).read_bytes()).hexdigest()==asset['sha256']
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==manifest['script_sha256']
    lab={r['batch']:r for r in csv.DictReader(io.StringIO((CACHE/'Laboratory.csv').read_text()),delimiter=';')}
    with zipfile.ZipFile(CACHE/'Process.zip') as archive:
        raw=archive.read(manifest['archive_member']);assert hashlib.sha256(raw).hexdigest()==manifest['member_sha256']
        rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig')),delimiter=';'))
    grouped={}
    for row in rows:grouped.setdefault(row['batch'],[]).append(row)
    starts={key:min(r['timestamp'] for r in value) for key,value in grouped.items()}
    ids=sorted(grouped,key=lambda key:(starts[key],int(key)));assert ids==manifest['ordered_batch_ids']
    assert len(ids)==95 and all(r['code']=='1' for values in grouped.values() for r in values)
    target=np.array([number(lab[key][manifest['target']]) for key in ids]);assert np.isfinite(target).all()
    base=np.array([[number(lab[key][f]) for f in MATERIALS]+[number(lab[key]['size']),number(''.join(c for c in lab[key]['strength'] if c.isdigit() or c=='.'))] for key in ids])
    prefixes={cut:np.array([summaries(grouped[key],cut) for key in ids]) for cut in [15,60,None]}
    feature_seconds=time.perf_counter()-started
    sham=np.random.default_rng(manifest['sham_seed']).normal(size=prefixes[60].shape)
    variants={'materials_recipe':base,'prefix15':np.column_stack([base,prefixes[15]]),'prefix60':np.column_stack([base,prefixes[60]]),'sham_capacity':np.column_stack([base,sham]),'whole_batch_oracle':np.column_stack([base,prefixes[None]])}
    train=slice(0,66);valid=slice(66,75);test=slice(75,95);fit_count=0
    outputs={'training_mean':{'test':metrics(target[test],np.full(20,target[:75].mean())),'trainable_parameters':1}}
    for name,values in variants.items():
        trials=[]
        for alpha in manifest['alphas']:
            pred=fit_predict(values[train],target[train],values[valid],alpha);fit_count+=1
            trials.append((metrics(target[valid],pred)['mse_original_scale'],-alpha,alpha))
        chosen=min(trials)[2]
        pred=fit_predict(values[:75],target[:75],values[test],chosen);fit_count+=1
        outputs[name]={'features':values.shape[1],'trainable_parameters':values.shape[1]+1,'chosen_alpha':chosen,'validation_trials':[{'alpha':r[2],'mse':r[0]} for r in trials],'test':metrics(target[test],pred)}
    assert fit_count==20 and fit_count<=manifest['max_ridge_fits']
    material_mse=outputs['materials_recipe']['test']['mse_original_scale']
    for name in ['prefix15','prefix60','sham_capacity','whole_batch_oracle']:
        outputs[name]['relative_mse_gain_vs_materials_percent']=100*(material_mse-outputs[name]['test']['mse_original_scale'])/material_mse if material_mse else None
    output={'scope':'Exploratory feasibility only: one fixed product code and source family; no method novelty or multi-factory inference','target':manifest['target'],'target_unit':'percent drug release as described by primary data descriptor','split_batches':[66,9,20],'ordered_batch_ids':ids,'fit_count':fit_count,'neural_runs':0,'variants':outputs,'runtime':{'python':platform.python_version(),'numpy':np.__version__,'system':platform.platform(),'feature_and_data_seconds':feature_seconds,'total_seconds':time.perf_counter()-started,'ru_maxrss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'ru_maxrss_unit':'bytes on Darwin, KiB otherwise'},'assumptions':['Raw-material certificate fields and planned size/strength assumed known at batch start; native release timestamps absent','Cutoff is source-time since first logged batch record, not measured arrival time','Whole-batch is an unavailable-future oracle diagnostic','No all-raw-lot-disjoint claim; shared-material dependencies remain','One9-batch validation block is noisy; no significance claim']}
    out=ROOT/'results';out.mkdir(exist_ok=True);(out/'linear_feasibility.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'fit_count':fit_count,'variants':{key:value.get('relative_mse_gain_vs_materials_percent') for key,value in outputs.items()},'total_seconds':output['runtime']['total_seconds']},indent=2))

if __name__=='__main__':run()
