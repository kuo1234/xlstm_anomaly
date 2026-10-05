"""Two-stage controlled study; abort on protocol faults without automatic repairs."""
import argparse
import concurrent.futures
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import time
import traceback
import numpy as np
import torch
from common import ROOT,load_config,write_json,configure,sha,verify_freeze,model_hash,array_hash
from generator import sequences,histories
from models import build
from train import train_one
from audit import model_audit
from evaluate import standardize,linear_ar_fit,b_support,paired_mechanism,calibration_threshold,anomaly_extension
from metrics import group_decision


def load_trained(job,artifacts):
    mechanism,group,backbone,seed=job;name=f'{mechanism}_g{group}_{backbone}_s{seed}'
    # This is a locally generated trusted checkpoint, not downloaded input.
    checkpoint=torch.load(artifacts/name/'best.pt',weights_only=False)
    model=build(backbone,seed);model.load_state_dict(checkpoint['model']);model.eval().requires_grad_(False)
    return name,model,checkpoint['scaler']


def evaluate_support(job,artifacts):
    verify_freeze();configure();cfg=load_config();mechanism,group,backbone,seed=job
    name,model,scaler=load_trained(job,artifacts);audit=model_audit(model);data=histories(mechanism,group)
    train=sequences(mechanism,group,'train',cfg['data']['train_sequences_per_regime'],cfg['data']['train_length'])
    b_train=standardize(train[cfg['data']['train_sequences_per_regime']:],scaler);ar=linear_ar_fit(b_train,cfg['baselines']['linear_ar_ridge'])
    before=model_hash(model)
    with torch.inference_mode():support,_,_=b_support(model,data,scaler,ar)
    assert model_hash(model)==before
    record={'job':list(job),'name':name,'b_support':support,'trained_random_state_audit':audit,'checkpoint_hash':sha(artifacts/name/'best.pt'),'common_b_suffix_hash':data['common_b_hash'],'parameters_frozen':True}
    write_json(artifacts/name/'support.json',record);print('SUPPORT_COMPLETE '+name,flush=True)
    return record


def evaluate_mechanism(job,artifacts,support):
    verify_freeze();configure();cfg=load_config();mechanism,group,backbone,seed=job
    name,model,scaler=load_trained(job,artifacts);data=histories(mechanism,group)
    train=sequences(mechanism,group,'train',cfg['data']['train_sequences_per_regime'],cfg['data']['train_length']);ar=linear_ar_fit(standardize(train[cfg['data']['train_sequences_per_regime']:],scaler),cfg['baselines']['linear_ar_ridge'])
    before=model_hash(model)
    with torch.inference_mode():
        support_again,pred,loss=b_support(model,data,scaler,ar)
        assert support_again==support['b_support']
        record=support|{'mechanism':paired_mechanism(model,data,scaler,pred,loss)}
    assert model_hash(model)==before
    write_json(artifacts/name/'mechanism.json',record);print('MECHANISM_COMPLETE '+name,flush=True)
    return record


def evaluate_anomalies(job,artifacts):
    verify_freeze();configure();cfg=load_config();mechanism,group,backbone,seed=job
    name,model,scaler=load_trained(job,artifacts);data=histories(mechanism,group)
    calibration=sequences(mechanism,group,'calibration',cfg['data']['calibration_sequences_per_regime'],cfg['data']['calibration_length'])
    before=model_hash(model)
    with torch.inference_mode():
        threshold=calibration_threshold(model,calibration,scaler)
        rows=anomaly_extension(model,data,scaler,mechanism,group,threshold)
    assert model_hash(model)==before
    record={'job':list(job),'name':name,'threshold':threshold,'calibration_hash':array_hash(calibration),'rows':rows,'parameters_frozen':True}
    write_json(artifacts/name/'anomalies.json',record);print('ANOMALIES_COMPLETE '+name,flush=True)
    return record


def map_jobs(function,jobs,workers,*args):
    records=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(function,job,*args):job for job in jobs}
        for future in concurrent.futures.as_completed(futures):records.append(future.result())
    return sorted(records,key=lambda r:r['name'])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--artifacts',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    configure();cfg=load_config();seal=verify_freeze();start=time.monotonic()
    assert not args.artifacts.exists(), 'fresh artifact directory required; no silent restart'
    args.artifacts.mkdir(parents=True)
    environment={'python':platform.python_version(),'platform':platform.platform(),'packages':{k:importlib.metadata.version(k) for k in ['torch','numpy','xlstm']},'device':'cpu','deterministic_algorithms':True,'threads':cfg['training']['threads'],'workers':cfg['runtime']['workers'],'cuda_used':False}
    write_json(args.output/'environment.json',environment)
    jobs=[(m,g,b,s) for m in cfg['mechanisms'] for g in cfg['groups'] for b in cfg['backbones'] for s in cfg['model_seeds']]
    training=map_jobs(train_one,jobs,cfg['runtime']['workers'],args.artifacts);write_json(args.output/'training.json',training)
    support=map_jobs(evaluate_support,jobs,cfg['runtime']['workers'],args.artifacts);write_json(args.output/'support.json',support)
    eligible=[];support_gate={}
    for m in cfg['mechanisms']:
        support_gate[m]={}
        for b in cfg['backbones']:
            passed=[]
            for g in cfg['groups']:
                row=[r for r in support if r['job'][:3]==[m,g,b]]
                passed.append(sum(r['b_support']['pass'] for r in row)>=cfg['gates']['model_seeds_required'])
            ok=sum(passed)>=cfg['gates']['support_groups_required'];support_gate[m][b]={'group_pass':passed,'groups_passed':sum(passed),'pass':ok}
        # Entire matched comparison requires adequate support in both backbones.
        if all(support_gate[m][b]['pass'] for b in cfg['backbones']):eligible.extend(j for j in jobs if j[0]==m)
    write_json(args.output/'support_gate.json',support_gate)
    mechanism=[]
    for job in eligible:
        row=next(r for r in support if r['job']==list(job));mechanism.append(evaluate_mechanism(job,args.artifacts,row))
        if time.monotonic()-start>cfg['runtime']['max_total_wall_seconds']:raise RuntimeError('prespecified total time limit exceeded')
    write_json(args.output/'mechanism.json',mechanism)
    groups={};anomaly_jobs=[]
    for m in cfg['mechanisms']:
        groups[m]={}
        for b in cfg['backbones']:
            grouped=[]
            for g in cfg['groups']:
                rows=[r for r in mechanism if r['job'][:3]==[m,g,b]]
                if rows:grouped.append({'group':g,**group_decision(rows)})
            groups[m][b]=grouped
        # AD is executed only if xLSTM passes the pre-AD mechanism gate in >=4/5 groups.
        if sum(g['mechanism_pre_ad'] for g in groups[m]['xlstm'])>=cfg['gates']['support_groups_required']:
            anomaly_jobs.extend(j for j in eligible if j[0]==m)
    write_json(args.output/'group_gates.json',groups)
    anomalies=map_jobs(evaluate_anomalies,anomaly_jobs,cfg['runtime']['workers'],args.artifacts) if anomaly_jobs else []
    write_json(args.output/'anomalies.json',anomalies)
    write_json(args.output/'execution.json',{'freeze_commit':seal['commit'],'config_sha256':sha(ROOT/'configs/protocol.json'),'training_runs':len(training),'support_runs':len(support),'mechanism_runs':len(mechanism),'anomaly_runs':len(anomalies),'anomaly_status':'RUN_GATED_MECHANISMS_ONLY' if anomalies else 'NOT_RUN_GATED','elapsed_seconds':time.monotonic()-start,'scientific_N_per_mechanism':len(cfg['groups']),'model_seeds':cfg['model_seeds'],'test_replicates_per_group':cfg['data']['test_replicates'],'status':'EXECUTION_COMPLETE_REQUIRES_SUMMARY'})
    print('EXECUTION_COMPLETE',flush=True)


if __name__=='__main__':
    try:main()
    except BaseException as exc:
        print('PROTOCOL_FAIL '+repr(exc),flush=True)
        traceback.print_exc()
        raise
