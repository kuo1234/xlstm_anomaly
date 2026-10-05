"""Post-push-only execution. Training code never reads GT or event manifests."""
import hashlib,json,platform,subprocess,sys,time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from models import Predictor,target_ids,windows,pca_fit,pca_score,infer_lstm
from prepare import ROOT,REPO,CACHE,sha,save

def verify_seal():
    proof=json.loads((CACHE/'execution_authorization.json').read_text())
    remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/'+proof['branch']],text=True).split()[0]
    assert remote==proof['seal_commit']
    for name,digest in proof['sealed_files'].items():assert sha(REPO/name)==digest,name
    return proof

def main():
    proof=verify_seal();p=json.loads((ROOT/'configs/protocol.json').read_text());manifest=json.loads((ROOT/'configs/data_manifest.json').read_text())
    torch.set_num_threads(2);torch.use_deterministic_algorithms(True);torch.manual_seed(p['seed']);np.random.seed(p['seed'])
    arrays={};start=time.time()
    for m in manifest:
        assert sha(REPO/m['local_path'])==m['sha256']
        d=np.load(REPO/m['prepared_path']);t=d['t'];x=d['x'];obs=d['observed']
        assert hashlib.sha256(t.tobytes()+x.tobytes()+obs.tobytes()).hexdigest()==m['prepared_array_sha256']
        arrays[m['trace']]=(t,x,obs)
    fit=[m for m in manifest if m['role']=='fit'];assert all(m['trace'].split('_')[1]=='0' for m in fit)
    xf=np.concatenate([arrays[m['trace']][1][arrays[m['trace']][2]&np.isfinite(arrays[m['trace']][1]).all(axis=1)] for m in fit])
    mean=xf.mean(axis=0,dtype=np.float64);std=xf.std(axis=0,dtype=np.float64);std[std==0]=1
    scale=CACHE/'scaler.npz';np.savez(scale,mean=mean,std=std);scaler_hash=sha(scale)
    scaled={name:((x-mean)/std).astype(np.float32) for name,(t,x,obs) in arrays.items()}
    pca=pca_fit(np.concatenate([scaled[m['trace']][arrays[m['trace']][2]&np.isfinite(scaled[m['trace']]).all(axis=1)] for m in fit]),p['pca']['components'])
    pca_path=CACHE/'pca.npz';np.savez(pca_path,basis=pca)
    w=p['lstm']['window'];hx=[];ys=[]
    for m in fit:
        x=scaled[m['trace']];ids=target_ids(x,arrays[m['trace']][2],w)[::p['lstm']['fit_window_stride']]
        hx.append(windows(x,ids,w));ys.append(x[ids])
    hx=np.concatenate(hx);ys=np.concatenate(ys)
    if len(hx)>p['lstm']['max_fit_windows']:
        ids=np.linspace(0,len(hx)-1,p['lstm']['max_fit_windows'],dtype=int);hx=hx[ids];ys=ys[ids]
    h=torch.from_numpy(hx);y=torch.from_numpy(ys);model=Predictor(hidden=p['lstm']['hidden_size'])
    opt=torch.optim.Adam(model.parameters(),lr=p['lstm']['learning_rate']);logs=[]
    validation=[]
    for m in manifest:
        if m['role']=='validation':
            x=scaled[m['trace']];ix=target_ids(x,arrays[m['trace']][2],w)
            ix=ix[np.linspace(0,len(ix)-1,min(len(ix),p['lstm']['validation_max_windows']),dtype=int)]
            validation.append((torch.from_numpy(windows(x,ix,w)),torch.from_numpy(x[ix])))
    for epoch in range(p['lstm']['epochs']):
        model.train();order=torch.randperm(len(h));losses=[]
        for ids in order.split(p['lstm']['batch_size']):
            opt.zero_grad();loss=torch.mean((model(h[ids])-y[ids])**2);assert torch.isfinite(loss)
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),p['lstm']['clip_grad_norm']);opt.step();losses.append(loss.item())
        model.eval()
        with torch.no_grad():
            vl=[torch.mean((model(hh[j:j+512])-yy[j:j+512])**2).item() for hh,yy in validation for j in range(0,len(hh),512)]
        logs.append({'epoch':epoch+1,'fit_mean_batch_loss':float(np.mean(losses)),'normal_validation_mean_batch_loss':float(np.mean(vl))})
        print('epoch',logs[-1],flush=True)
    checkpoint=CACHE/'lstm.pt';torch.save(model.state_dict(),checkpoint)
    score_records=[];hashes={};score_cache={}
    prep_hash=sha(ROOT/'scripts/prepare.py');fit_id=hashlib.sha256('|'.join(m['trace'] for m in fit).encode()).hexdigest()
    cal_id=hashlib.sha256('|'.join(m['trace'] for m in manifest if m['role']=='calibration').encode()).hexdigest()
    for baseline in p['baselines']:
        cp=pca_path if baseline=='PCA_SPE' else checkpoint;hashes[baseline]=sha(cp)
        for m in manifest:
            name=m['trace'];t,x,obs=arrays[name];z=scaled[name]
            if baseline=='PCA_SPE':
                score=np.full(len(t),np.nan);good=obs&np.isfinite(z).all(axis=1);score[good]=pca_score(z[good],pca)
            else:score=infer_lstm(model,z,obs,w)
            assert np.isfinite(score[~np.isnan(score)]).all()
            # Every saved target row has explicit availability/provenance fields.
            table=pd.DataFrame({'raw_trace_id':name,'target_timestamp':t,'available_at':t,'score':score,'baseline_id':baseline,'checkpoint_hash':sha(cp),'preprocessing_hash':prep_hash,'scaler_hash':scaler_hash,'fit_split_id':fit_id,'calibration_split_id':cal_id,'target_observed':obs,'role':m['role']})
            dest=CACHE/'scores'/baseline/f'{name}.csv.gz';dest.parent.mkdir(parents=True,exist_ok=True);table.to_csv(dest,index=False,compression={'method':'gzip','mtime':0})
            score_records.append({'baseline':baseline,'trace':name,'role':m['role'],'path':str(dest.relative_to(REPO)),'sha256':sha(dest),'rows':len(t),'finite_scores':int(np.isfinite(score).sum()),'checkpoint_hash':sha(cp),'scaler_hash':scaler_hash})
            score_cache[(baseline,name)]=score
        print('scores',baseline,flush=True)
    thresholds=[]
    for baseline in p['baselines']:
        for app in [None]+p['selected_apps']:
            values=np.concatenate([score_cache[(baseline,m['trace'])] for m in manifest if m['role']=='calibration' and (app is None or int(m['trace'].split('_')[0])==app)])
            values=values[np.isfinite(values)];q=np.quantile(values,[.25,.5,.75,.995],method='linear')
            thresholds.append({'baseline':baseline,'app':app,'count':len(values),'q25':float(q[0]),'median':float(q[1]),'q75':float(q[2]),'IQR':float(q[2]-q[0]),'threshold':float(q[3])})
    save(ROOT/'results/training.json',{'seal_commit':proof['seal_commit'],'runtime':{'python':sys.version,'torch':torch.__version__,'numpy':np.__version__,'pandas':pd.__version__,'hardware':platform.platform(),'threads':2,'device':'cpu'},'fit_points':len(xf),'fit_windows':len(h),'epochs':logs,'checkpoints':hashes,'scaler_hash':scaler_hash,'fit_split_id':fit_id,'calibration_split_id':cal_id,'seconds':time.time()-start,'seeds':[p['seed']],'checkpoint_selection':'final epoch; val diagnostic only'})
    save(ROOT/'provenance/score_artifacts.json',score_records);save(ROOT/'results/thresholds.json',thresholds)
    print('execution complete',time.time()-start,flush=True)
if __name__=='__main__':main()
