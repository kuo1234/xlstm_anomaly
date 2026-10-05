"""Stationary A/B training only; calibration/test files absent from this stage."""
import time
import numpy as np
import torch
from common import load_config,configure,array_hash,write_json,sha,verify_freeze
from generator import sequences
from models import build,parameter_count
from evaluate import standardize


def train_one(job,artifacts):
    freeze=verify_freeze();configure();cfg=load_config();mechanism,group,backbone,seed=job
    name=f'{mechanism}_g{group}_{backbone}_s{seed}';directory=artifacts/name;directory.mkdir(parents=True,exist_ok=False)
    training=sequences(mechanism,group,'train',cfg['data']['train_sequences_per_regime'],cfg['data']['train_length'])
    validation=sequences(mechanism,group,'validation',cfg['data']['validation_sequences_per_regime'],cfg['data']['validation_length'])
    flat=training.reshape(-1,cfg['dimension']);scaler={'mean':flat.mean(axis=0,dtype=np.float64).astype(np.float32),'std':flat.std(axis=0,dtype=np.float64).astype(np.float32)}
    assert np.isfinite(scaler['std']).all() and np.all(scaler['std']>1e-6)
    inputs=torch.from_numpy(standardize(training,scaler)).float();valid=torch.from_numpy(standardize(validation,scaler)).float()
    model=build(backbone,seed);opt=torch.optim.Adam(model.parameters(),lr=cfg['training']['learning_rate'],weight_decay=cfg['training']['weight_decay'])
    generator=torch.Generator().manual_seed(seed+120000);best=float('inf');best_epoch=None;history=[];start=time.monotonic();updates=0
    warm=cfg['training']['warmup_tokens']
    for epoch in range(cfg['training']['epochs']):
        model.train();order=torch.randperm(len(inputs),generator=generator);total=0.;points=0
        for ids in order.split(cfg['training']['batch_size']):
            x=inputs[ids];opt.zero_grad(set_to_none=True)
            pred=model(x[:,:-1])
            loss=(pred[:,warm-1:]-x[:,warm:]).square().mean()
            assert torch.isfinite(loss), 'nonfinite training'
            loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),cfg['training']['gradient_clip_norm']);opt.step()
            total+=float(loss.detach())*len(ids);points+=len(ids);updates+=1
        model.eval()
        with torch.inference_mode():
            prediction=model(valid[:,:-1]);value=float((prediction[:,warm-1:]-valid[:,warm:]).square().mean())
        assert np.isfinite(value)
        if value<best:
            best=value;best_epoch=epoch+1
            torch.save({'model':model.state_dict(),'scaler':scaler,'job':job,'selected_epoch':best_epoch,'validation_mse':best},directory/'best.pt')
        history.append({'epoch':epoch+1,'train_mse':total/points,'validation_mse':value})
        if time.monotonic()-start>cfg['runtime']['max_training_seconds_per_run']:raise RuntimeError('prespecified training time limit exceeded; STOP')
    torch.save({'model':model.state_dict(),'job':job},directory/'final.pt')
    manifest={'job':list(job),'name':name,'freeze_commit':freeze['commit'],'train_hash':array_hash(training),'validation_hash':array_hash(validation),'scaler':{k:v.tolist() for k,v in scaler.items()},'scaler_hash':array_hash(scaler['mean'])+':'+array_hash(scaler['std']),
              'parameters':parameter_count(model),'selected_epoch':best_epoch,'best_validation_mse':best,'epochs':cfg['training']['epochs'],'optimizer_updates':updates,'sequences_per_regime':cfg['data']['train_sequences_per_regime'],'samples_per_regime':cfg['data']['train_sequences_per_regime']*cfg['data']['train_length'],
              'elapsed_seconds':time.monotonic()-start,'checkpoint_hashes':{'best.pt':sha(directory/'best.pt'),'final.pt':sha(directory/'final.pt')},'history':history,'labels_seen':False,'test_seen':False,'normal_training_only':True}
    write_json(directory/'training.json',manifest)
    print('TRAIN_COMPLETE '+name,flush=True)
    return manifest
