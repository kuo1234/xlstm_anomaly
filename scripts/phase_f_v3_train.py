"""One fixed F-v3 training condition; matched LSTM uses scoped cuDNN-off calls."""
import argparse
import hashlib
import json
import random
import resource
import subprocess
import time
import numpy as np
import torch
from phase_f_v3_common import *
from phase_f_v2_parity import parity
from phase_f_v3_canary import canary

def cpu_state(model): return {k:v.detach().cpu().clone() for k,v in model.state_dict().items()}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('architecture',choices=('xlstm','lstm')); parser.add_argument('seed',type=int); args=parser.parse_args()
    start=time.perf_counter(); environment=configure(); sealed=verify_sealed_inputs()
    gates=json.loads((REPORT/'mechanical_gates.json').read_text())
    if gates.get('status')!='PASS': raise SystemExit('F-v3 mechanical gates are not PASS; training forbidden')
    if args.seed not in CONFIG['detector_seeds']: raise ValueError('Unregistered detector seed')
    orderinfo=sealed['orders'][str(args.seed)]; orders=np.load(ROOT/orderinfo['path'],allow_pickle=False)
    assert orders.shape==(50,40330)
    for epoch,row in enumerate(orders):
        assert hashlib.sha256(row.tobytes()).hexdigest()==orderinfo['epoch_sha256'][epoch]
        assert np.array_equal(np.sort(row),np.arange(40330))
    run_name=f'{args.architecture}_{args.seed}'; data_dir=ROOT/'data/phase_f_v3'/'runs'/run_name; report_dir=REPORT/'runs'/run_name
    data_dir.mkdir(parents=True,exist_ok=False); report_dir.mkdir(parents=True,exist_ok=False)
    train=load_windows('train'); validation=load_windows('validation'); fixed_canary=canary_input()
    canary_hash=hashlib.sha256(fixed_canary.detach().cpu().numpy().tobytes()).hexdigest()
    model=build(args.architecture,args.seed); model.train(); opt=optimizer(model)
    expected={k:(tuple(v) if k=='betas' else v) for k,v in CONFIG['optimizer'].items()}; assert all(opt.defaults[k]==v for k,v in expected.items())
    initial=cpu_state(model); initial_hash=model_hash(model); torch.save(initial,data_dir/'initial.pt')
    order_hasher=hashlib.sha256(); curves=[]; best=float('inf'); best_epoch=None; optimizer_steps=0; exposures=0
    torch.cuda.reset_peak_memory_stats(); training_start=time.perf_counter()
    with forbid_native_predict() as trap:
        for epoch in range(50):
            epoch_start=time.perf_counter(); model.train(); total=torch.zeros((),device='cuda',dtype=torch.float64)
            order=orders[epoch]; order_hasher.update(order.tobytes()); ids=torch.from_numpy(order.copy()).cuda()
            for batch_ids in ids.split(128):
                observations=train[batch_ids]; opt.zero_grad(set_to_none=True); loss=reconstruction_loss(model,observations)
                if not bool(torch.isfinite(loss)): raise RuntimeError('Nonfinite training loss')
                loss.backward()
                if not all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in model.parameters()): raise RuntimeError('Nonfinite training gradient')
                opt.step(); optimizer_steps+=1; exposures+=len(batch_ids); total+=loss.detach().double()*len(batch_ids)
            model.eval(); val_total=torch.zeros((),device='cuda',dtype=torch.float64)
            with torch.no_grad():
                for observations in validation.split(128):
                    val_loss=reconstruction_loss(model,observations)
                    if not bool(torch.isfinite(val_loss)): raise RuntimeError('Nonfinite validation loss')
                    val_total+=val_loss.double()*len(observations)
            train_mse=float(total/len(train)); validation_mse=float(val_total/len(validation))
            # Fixed canary is diagnostic/fail-fast only. It cannot affect loss,
            # optimizer state, epoch selection, or checkpoint selection.
            canary_result=canary(model,args.architecture,fixed_canary)
            if validation_mse<best:
                best=validation_mse; best_epoch=epoch+1; torch.save(dict(model=cpu_state(model),epoch=best_epoch,validation_mse=best),data_dir/'best.pt')
            row=dict(epoch=epoch+1,train_mse=train_mse,validation_mse=validation_mse,training_order_sha256=hashlib.sha256(order.tobytes()).hexdigest(),
                optimizer_steps_this_epoch=316,train_windows=len(train),validation_windows=len(validation),seconds=time.perf_counter()-epoch_start,
                canary=canary_result)
            curves.append(row); write_json(report_dir/'curves.json',curves); print(json.dumps(dict(run=run_name,**row)),flush=True)
        if trap.call_count: raise RuntimeError('Native predict_step called by scientific path')
    torch.cuda.synchronize(); training_seconds=time.perf_counter()-training_start
    assert optimizer_steps==15800 and exposures==2016500
    final=cpu_state(model); final_hash=model_hash(model)
    torch.save(dict(model=final,optimizer=opt.state_dict(),epoch=50,rng={'torch':torch.get_rng_state(),'cuda':torch.cuda.get_rng_state_all(),'numpy':np.random.get_state(),'python':random.getstate()}),data_dir/'final.pt')
    best_payload=torch.load(data_dir/'best.pt',map_location='cpu',weights_only=True); model.load_state_dict(best_payload['model']); model.eval(); best_hash=model_hash(model)
    post=parity(model,args.architecture); write_json(report_dir/'post_training_parity.json',post)
    del train,validation,opt
    recurrent_changes={}
    for name,state in initial.items():
        if recurrent_name(name): recurrent_changes[name]=dict(initial_norm=float(state.norm()),best_delta_norm=float((best_payload['model'][name]-state).norm()),final_delta_norm=float((final[name]-state).norm()),best_changed=not torch.equal(best_payload['model'][name],state))
    artifacts={str(p.relative_to(ROOT)):sha(p) for p in sorted(data_dir.iterdir())}
    result=dict(status='PASS' if post['status']=='PASS' else 'STOP_POST_TRAIN_PARITY',architecture=args.architecture,seed=args.seed,
        implementation_commit=subprocess.check_output(['rtk','git','rev-parse','HEAD'],text=True).strip(),environment=environment,sealed_inputs=sealed,
        initial_model_hash=initial_hash,final_model_hash=final_hash,best_model_hash=best_hash,artifacts=artifacts,
        training_order_file_sha256=orderinfo['sha256'],consumed_order_sha256=order_hasher.hexdigest(),optimizer_config=CONFIG['optimizer'],epochs=50,
        optimizer_steps=optimizer_steps,window_exposures=exposures,parameter_count=CONFIG['parameters'][args.architecture],selected_epoch=best_epoch,
        best_validation_mse=best,recurrent_changes=recurrent_changes,canary=dict(seed=CONFIG['canary']['seed'],shape=CONFIG['canary']['shape'],input_sha256=canary_hash,after_every_epoch=True,fail_fast=True,affects_optimization=False),
        training_seconds=training_seconds,total_seconds=time.perf_counter()-start,peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),
        cpu_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,native_predict_calls=trap.call_count,labels_used=False,test_sources_used=False,probe_fitting=False,
        post_training_parity=post)
    write_json(report_dir/'manifest.json',result); print(json.dumps(dict(run=run_name,status=result['status'],selected_epoch=best_epoch,total_seconds=result['total_seconds'])),flush=True)
    if result['status']!='PASS': raise SystemExit(3)

if __name__=='__main__': main()
