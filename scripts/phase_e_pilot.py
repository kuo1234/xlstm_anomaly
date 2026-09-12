"""Bounded label-free observation/reference diagnostic; never a trained model."""
import dataclasses,json,time,traceback
import numpy as np
import torch
from phase_e_common import *
from phase_e_observer import Observer,scalar_reference
from phase_e_schema import BASE_COLUMNS,EXPANDED_COLUMNS


def compare(a,b):
    return dict(exact=bool(torch.equal(a,b)),close=bool(torch.allclose(a,b,atol=1e-5,rtol=1e-4)),
        max_abs=float((a-b).abs().max()))

def native_scores(output,x):
    # EXACT upstream layout, intentionally not repaired.
    return (output.view(-1,x.shape[1]*x.shape[2])-x.view(-1,x.shape[1]*x.shape[2])).square().mean(1)

def main():
    configure();start=time.perf_counter();torch.set_num_threads(4)
    model=build(64,backend='vanilla',float32=True)
    assert all(p.dtype==torch.float32 for p in model.parameters())
    architecture=dict(official_commit='3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6',
        dependency='xlstm==2.0.3',native_entrypoint=dict(window=50,embedding=40,batch=128,lr=.005),
        common=dict(window=64,embedding=40,features=8,batch=128),
        config=dataclasses.asdict(model.lstm_encoder.config),
        trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad),
        parameters={k:list(p.shape) for k,p in model.named_parameters()},
        repr=repr(model),reference_overlay=dict(backend='vanilla',all_slstm_dtypes='float32'),
        cell_counts=dict(slstm=2,mlstm=4),state_carry_between_windows=False,
        decoder_recurrent_state_resets_each_singleton_call=True)
    (REPORT/'architecture.json').write_text(json.dumps(architecture,indent=2)+'\n')
    generator=torch.Generator(device='cuda').manual_seed(710)
    x=torch.randn(4,64,8,generator=generator,device='cuda');permutation=torch.tensor([2,0,3,1],device='cuda')
    tests={};artifacts={}
    with torch.no_grad():
        off=model(x)
        with Observer(model) as observer:on=model(x);features=observer.summary()
        tests['observer_output']=compare(off,on)
        tests['observer_scores']=compare(native_scores(off,x),native_scores(on,x))
        tests['reference_hidden_and_final_states']=dict(pass_all=all(r['hidden_close'] and r['final_state_close'] and r['finite'] for r in observer.errors),
            calls=observer.calls,max_hidden_abs=max(r['hidden_max_abs'] for r in observer.errors),
            max_final_state_abs=max(r['final_state_max_abs'] for r in observer.errors))
        tests['schema']=dict(shape=list(features.shape),finite=bool(torch.isfinite(features).all()),
            columns=BASE_COLUMNS,expanded_count=len(EXPANDED_COLUMNS))
        latest={k:{n:v.clone() for n,v in t.items()} for k,t in observer.latest.items()}
        model(torch.randn(3,64,8,generator=generator,device='cuda'))
        tests['reset_after_unrelated_window']=compare(off,model(x))
        swapped=model(x[permutation])
        tests['model_batch_permutation']=compare(swapped,off[:,permutation])
        tests['native_score_batch_permutation']=compare(native_scores(swapped,x[permutation]),native_scores(off,x)[permutation])
        individual=[model(x[i:i+1]) for i in range(4)]
        singleton=torch.cat(individual,dim=1)
        tests['model_batch_partition']=compare(off,singleton)
        single_scores=torch.cat([native_scores(individual[i],x[i:i+1]) for i in range(4)])
        tests['native_score_batch_partition']=compare(native_scores(off,x),single_scores)
        tests['final_batch_B3_shape']=list(model(x[:3]).shape)
        projected=model.encoder_projection(x)
        with Observer(model) as full:enc=model.lstm_encoder(projected)
        changed=projected.clone();changed[:,32:]=torch.randn(4,32,40,generator=generator,device='cuda')
        with Observer(model) as future:enc2=model.lstm_encoder(changed)
        tests['encoder_prefix_output']=compare(enc[:,:32],enc2[:,:32])
        scalar_name=next(iter(full.latest))
        tests['scalar_prefix']={k:compare(v[:,:32],future.latest[scalar_name][k][:,:32]) for k,v in full.latest[scalar_name].items()}
        with Observer(model) as shorter:prefix=model.lstm_encoder(projected[:,:32])
        tests['encoder_prefix_length']=compare(enc[:,:32],prefix)
        # Cell-level recurrence carries ONLY within one input window; no H3b.
        state=None;steps=[]
        for t in range(64):
            out,state=model.lstm_encoder.step(projected[:,t:t+1],state);steps.append(out)
        tests['encoder_parallel_vs_within_window_step']=compare(enc,torch.cat(steps,1))
        # mLSTM cell's native parallel vs native step, independent of sLSTM.
        mlstm=model.lstm_encoder.blocks[0].xlstm.mlstm_cell
        q,k,v=[torch.randn(4,64,80,generator=generator,device='cuda') for _ in range(3)]
        parallel=mlstm(q,k,v);state=None;outs=[]
        for t in range(64):
            out,state=mlstm.step(q[:,t:t+1],k[:,t:t+1],v[:,t:t+1],mlstm_state=state);outs.append(out)
        tests['mlstm_parallel_vs_recurrent']=compare(parallel,torch.cat(outs,1))
        tests['mlstm_memory_finite']=all(bool(torch.isfinite(s).all()) for s in state)
        # Diagnose readout indexing using model outputs only; do not fix model.
        tests['readout_layout']=dict(output_shape=list(off.shape),target_shape=list(x.shape),
            native_score=native_scores(off,x).tolist(),
            batch_partition_native_score=single_scores.tolist(),
            native_uses_view_without_time_batch_transpose=True)
        path=ROOT/'data/phase_e/pilot';path.mkdir(exist_ok=True)
        for name,tensor in dict(observations=x,output=off,scalar_summary=features).items():
            p=path/f'{name}.npy';np.save(p,tensor.cpu().numpy(),allow_pickle=False);artifacts[str(p.relative_to(ROOT))]=sha(p)
    # Bounded timing only, even when a native score diagnostic fails; no fitting.
    timings={};batch=torch.randn(128,64,8,generator=generator,device='cuda')
    for name,observe in [('observer_off',False),('observer_on',True)]:
        def forward():
            if observe:
                with Observer(model) as obs:model(batch);obs.summary()
            else:model(batch)
        with torch.no_grad():
            for _ in range(2):forward()
            torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();t=time.perf_counter()
            for _ in range(5):forward()
            torch.cuda.synchronize();elapsed=time.perf_counter()-t
        timings[name]=dict(batches_per_second=5/elapsed,decisions_per_second=640/elapsed,
            seconds=elapsed,batch_size=128,timed_batches=5,peak_allocated_bytes=torch.cuda.max_memory_allocated(),
            peak_reserved_bytes=torch.cuda.max_memory_reserved())
    model.train()
    def backward():
        model.zero_grad(set_to_none=True);output=model(batch)
        loss=torch.nn.functional.mse_loss(output.view(-1,512),batch.view(-1,512));loss.backward()
    backward();torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();t=time.perf_counter()
    for _ in range(3):backward()
    torch.cuda.synchronize();elapsed=time.perf_counter()-t
    timings['forward_backward_no_optimizer']=dict(batches_per_second=3/elapsed,seconds=elapsed,
        optimizer_steps=0,peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
    timings['observer_overhead_ratio']=timings['observer_off']['batches_per_second']/timings['observer_on']['batches_per_second']
    # Native W50 architecture is the same; run a shape/reset diagnostic, not fit.
    model50=build(50,backend='vanilla',float32=True)
    with torch.no_grad():
        x50=batch[:4,:50];a=model50(x50)
        with Observer(model50) as obs:b=model50(x50)
        tests['native_W50_reference_observer']=compare(a,b)
        tests['native_W50_reference_score_permutation']=compare(native_scores(model50(x50[permutation]),x50[permutation]),native_scores(a,x50)[permutation])
    result=dict(status='BLOCKED' if not tests['native_score_batch_permutation']['close'] else 'PENDING_NATIVE_PARITY',
        backend='xlstm2.0.3 vanilla float32 diagnostic, not native CUDA reproduction',tests=tests,
        timings=timings,artifacts=artifacts,seconds=time.perf_counter()-start,
        no_labels=True,no_optimizer_updates=True,no_probe_fit=True,no_matched_LSTM=True)
    (REPORT/'reference_pilot.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
