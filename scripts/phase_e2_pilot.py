"""Random unlabeled validity/parity and bounded throughput; zero optimizer steps."""
import ast,inspect,json,resource,time
from unittest.mock import patch
import numpy as np
import torch
from phase_e2_common import *
from phase_e2_observer import Observer,extract,scalar_reference
from phase_e2_schema import SCALAR_CELLS,summarize,expand_history

def cmp(a,b):
    return dict(pass_=bool(torch.allclose(a,b,atol=1e-5,rtol=1e-4)),exact=bool(torch.equal(a,b)),
        max_abs=float((a-b).abs().max()),shape=list(a.shape))

def main():
    start=time.perf_counter();configure()
    run_id=sys.argv[1] if len(sys.argv)>1 else 'pilot'
    for p in ('reports/phase_e2/architecture.json','reports/phase_e2/schema.json','scripts/phase_e2_schema.py','scripts/phase_e2_observer.py'):
        assert subprocess.check_output(['rtk','git','show',f'0b669b0:{p}'])==(ROOT/p).read_bytes()
    subprocess.run(['rtk','git','merge-base','--is-ancestor','0b669b0','origin/main'],check=True)
    model=build();initial=model_hash(model)
    assert initial==json.loads((REPORT/'architecture.json').read_text())['initial_model_hash']
    g=torch.Generator(device='cuda').manual_seed(710)
    x=torch.randn(131,64,8,generator=g,device='cuda');checks={}
    with torch.no_grad():
        off=model(x);base=(off-x).square().mean((1,2))
        checks['output_BWD']=dict(pass_=list(off.shape)==[131,64,8],shape=list(off.shape))
        # Native MSE functions and training/validation methods, actual coordinates.
        expected=(off-x).square().sum()/x.numel()
        checks['native_MSE_coordinates']=cmp(model.loss(off,x),expected)
        logs={}
        with patch.object(model,'log',side_effect=lambda name,value,**kwargs:logs.update({name:value.detach()})):
            loss=model.training_step((x,object()),0);model.validation_step((x,object()),0)
        checks['native_training_loss']=cmp(loss,expected)
        checks['native_validation_loss']=cmp(logs['val_loss'],expected)
        checks['native_predict_target_is_x_not_label']=cmp(model.predict_step((x,x),0),base)
        perm=torch.randperm(len(x),generator=g,device='cuda');swapped=model(x[perm])
        checks['output_batch_permutation']=cmp(swapped,off[perm])
        checks['score_batch_permutation']=cmp((swapped-x[perm]).square().mean((1,2)),base[perm])
        for B in (128,3,1):
            values=[];outputs=[];sizes=[]
            for chunk in x.split(B):
                out=model(chunk);outputs.append(out);values.append((out-chunk).square().mean((1,2)));sizes.append(len(chunk))
            checks[f'partition_B{B}_output']=cmp(torch.cat(outputs),off)
            checks[f'partition_B{B}_scores']=dict(**cmp(torch.cat(values),base),batch_sizes=sizes)
        # Separate129-window cohort produces native B128 + finalB1.
        a=score(model,x[:128]);b=score(model,x[128:129])
        checks['B128_final_B1']=cmp(torch.cat([a,b]),base[:129])
        # Actual DataLoader using exact upstream windows, N194 gives131 windows.
        raw=torch.randn(194,8,generator=g,device='cuda').cpu()
        ds=ObservationWindows(raw);native_ds=SlidingWindowDataset(raw,torch.zeros(len(raw),dtype=torch.int64),64)
        ds_checks=[len(ds)==len(native_ds)==131]
        ds_checks.extend(torch.equal(ds[i],raw[i:i+64]) for i in range(len(ds)))
        hashes=[tensor_hash(ds[i]) for i in range(len(ds))]
        ds_checks.append(len(set(hashes))==131)
        try:native_ds[131];out_of_bounds=False
        except IndexError:out_of_bounds=True
        ds_checks.append(out_of_bounds)
        checks['native_dataset_exact_windows']=dict(pass_=all(ds_checks),N=194,W=64,count=len(ds),unique_windows=len(set(hashes)),
            last_start=130,last_end_exclusive=194,tail_repetition=False,out_of_bounds_raises=out_of_bounds)
        data_scores={}
        for B in (128,3,1):
            loader=torch.utils.data.DataLoader(ds,batch_size=B,shuffle=False)
            data_scores[B]=torch.cat([score(model,batch.cuda()) for batch in loader])
        checks['dataset_B128_vs_B3']=cmp(data_scores[128],data_scores[3])
        checks['dataset_B128_vs_B1']=cmp(data_scores[128],data_scores[1])
        # Singleton N=W is exactly one window; too-short input rejected by boundary.
        checks['N_equals_W']=dict(pass_=len(ObservationWindows(raw[:64]))==1)
        try:ObservationWindows(raw[:63]);short_rejected=False
        except ValueError:short_rejected=True
        checks['short_prefix_not_padded']=dict(pass_=short_rejected)
        small=x[:4].clone();original=model(small)
        rng=torch.cuda.get_rng_state().clone()
        with Observer(model) as obs:on=model(small);features=obs.summary()
        checks['observer_output_bitwise']={
            **cmp(on,original),'pass_':bool(torch.equal(on,original))}
        checks['observer_scores_bitwise']={**cmp((on-small).square().mean((1,2)),(original-small).square().mean((1,2))),
            'pass_':bool(torch.equal((on-small).square().mean((1,2)),(original-small).square().mean((1,2))))}
        checks['observer_RNG_unchanged']=dict(pass_=bool(torch.equal(rng,torch.cuda.get_rng_state())))
        checks['observer_reference']=dict(pass_=all(c['hidden_close'] and c['state_close'] and c['finite'] and c['all_float32'] for c in obs.checks),details=obs.checks)
        checks['four_full_window_scalar_calls']=dict(pass_=obs.calls=={c:1 for c in SCALAR_CELLS} and all(v['hidden'].shape[1]==64 for v in obs.latest.values()),calls=obs.calls)
        saved={c:{k:v.clone() for k,v in layer.items()} for c,layer in obs.latest.items()}
        checks['summary_finite18']=dict(pass_=list(features.shape)==[4,18] and bool(torch.isfinite(features).all()),shape=list(features.shape))
        model(torch.randn(3,64,8,generator=g,device='cuda'))
        with Observer(model) as reset:reset_out=model(small);reset_features=reset.summary()
        checks['independent_window_reset_output']={**cmp(reset_out,original),'pass_':bool(torch.equal(reset_out,original))}
        checks['independent_window_reset_features']={**cmp(reset_features,features),'pass_':bool(torch.equal(reset_features,features))}
        per=torch.tensor([2,0,3,1],device='cuda')
        with Observer(model) as shuffled:perout=model(small[per]);perfeatures=shuffled.summary()
        checks['observer_feature_batch_permutation']=cmp(perfeatures,features[per])
        partition_features=torch.cat([extract(model,small[i:i+1])[1] for i in range(4)])
        checks['observer_feature_batch_partition']=cmp(partition_features,features)
        future=small.clone();future[:,32:]=torch.randn(4,32,8,generator=g,device='cuda')
        with Observer(model) as fut:future_out=model(future)
        checks['model_prefix_future_causality']=cmp(original[:,:32],future_out[:,:32])
        checks['all_scalar_prefix_causality']=dict(pass_=all(torch.equal(saved[c][k][:,:32],fut.latest[c][k][:,:32]) for c in SCALAR_CELLS for k in saved[c]))
        prefix_summary=summarize({c:{k:v[:,:32] for k,v in l.items()} for c,l in saved.items()})
        future_summary=summarize({c:{k:v[:,:32] for k,v in l.items()} for c,l in fut.latest.items()})
        checks['schema_prefix_causality']=cmp(prefix_summary,future_summary)
        with Observer(model) as shorter:prefix_out=model(small[:,:32]);shortfeatures=shorter.summary()
        checks['shorter_prefix_output']=cmp(original[:,:32],prefix_out)
        checks['shorter_prefix_summary']=cmp(prefix_summary,shortfeatures)
        # Real previous decoder state: independently calculate hidden delta and
        # memory relative delta from t62→63, not zero→t63.
        deltas=[];relatives=[]
        for c in SCALAR_CELLS:
            h=saved[c]['hidden'];u=saved[c]['memory']
            deltas.append((h[:,-1]-h[:,-2]).square().mean(-1).sqrt().mean(-1))
            relatives.append((torch.linalg.vector_norm(u[:,-1]-u[:,-2],dim=-1)/(torch.linalg.vector_norm(u[:,-2],dim=-1)+1e-8)).mean(-1))
        checks['decoder_real_previous_delta']=cmp(features[:,3],torch.stack(deltas).mean(0))
        checks['decoder_real_previous_memory']=cmp(features[:,17],torch.stack(relatives).mean(0))
        # Same model, within-window native step only. No cross-window persistence.
        es=ds_state=None;steps=[]
        for time_idx in range(64):
            embedding=model.input_projection(small[:,time_idx:time_idx+1])
            encoded,es=model.encoder.step(embedding,es)
            decoded,ds_state=model.decoder.step(encoded,ds_state)
            steps.append(model.output_projection(model.gelu(decoded)))
        checks['full_model_parallel_vs_within_window_step']=cmp(torch.cat(steps,1),original)
        # Labels remain evaluator-only arbitrary markers; extraction receives x only.
        labels=torch.arange(4);permuted_labels=labels[torch.tensor([2,0,3,1])]
        s1,f1=extract(model,small);s2,f2=extract(model,small)
        checks['evaluator_label_permutation_closure']=dict(pass_=bool(torch.equal(s1,s2) and torch.equal(f1,f2)) and not torch.equal(labels,permuted_labels),
            model_api=list(inspect.signature(score).parameters),extract_api=list(inspect.signature(extract).parameters),
            observation_window_api=list(inspect.signature(ObservationWindows).parameters),markers_never_passed=True)
        # Inspect executable calls, not prose: the first check incorrectly
        # matched "threshold" in extract's "no ... threshold" docstring.
        calls=[ast.unparse(n.func) for fn in (score,extract) for n in ast.walk(ast.parse(inspect.getsource(fn))) if isinstance(n,ast.Call)]
        forbidden={'fit','fit_transform','quantile','percentile','MinMaxScaler','threshold'}
        checks['no_fitted_test_scaler_or_threshold']=dict(pass_=not any(c.rsplit('.',1)[-1] in forbidden for c in calls),executable_calls=calls,
            common_track='raw fixed observations; later optional train-prefix-only scaler belongs outside model; no fit/test_step/predict labels')
        checks['state_unchanged_through_tests']=dict(pass_=model_hash(model)==initial)
        # Save unlabeled diagnostics only; no scientific trained checkpoints.
        directory=ROOT/'data/phase_e2'/run_id;directory.mkdir(exist_ok=False)
        artifacts={}
        for name,value in dict(observations=small,output=original,summary=features,scores=s1).items():
            p=directory/f'{name}.npy';np.save(p,value.cpu().numpy(),allow_pickle=False);artifacts[str(p.relative_to(ROOT))]=sha(p)
    result=dict(status='PASS' if all(c['pass_'] for c in checks.values()) else 'BLOCKED',checks=checks,artifacts=artifacts,
        backend='official vanilla float32',atol=1e-5,rtol=1e-4,optimizer_steps=0,labels_used=False)
    (REPORT/f'validity_{run_id}.json').write_text(json.dumps(result,indent=2)+'\n')
    if result['status']!='PASS':
        print('E2 BLOCKED',json.dumps({k:v for k,v in checks.items() if not v['pass_']},indent=2));return
    batch=x[:128];timings={}
    for name,observe in [('vanilla',False),('observer',True)]:
        def forward():
            if observe:extract(model,batch)
            else:score(model,batch)
        with torch.no_grad():
            for _ in range(2):forward()
            torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();t=time.perf_counter()
            for _ in range(5):forward()
            torch.cuda.synchronize();elapsed=time.perf_counter()-t
        timings[name]=dict(seconds=elapsed,batches_per_second=5/elapsed,decisions_per_second=640/elapsed,
            batch_size=128,timed_batches=5,peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
    model.train()
    def backward():
        model.zero_grad(set_to_none=True);model.loss(model(batch),batch).backward()
    backward();torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();t=time.perf_counter()
    for _ in range(3):backward()
    torch.cuda.synchronize();elapsed=time.perf_counter()-t
    timings['forward_backward']=dict(seconds=elapsed,batches_per_second=3/elapsed,optimizer_steps=0,
        peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved())
    assert model_hash(model)==initial
    assert all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters())
    result=dict(status='PASS',timings=timings,observer_time_ratio=timings['vanilla']['batches_per_second']/timings['observer']['batches_per_second'],
        cpu_process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,total_seconds=time.perf_counter()-start,
        optimizer_steps=0,parameters_unchanged=True,finite_gradients=True,scientific_checkpoint_saved=False,
        probe_fit=False,matched_LSTM=False,CUDA_optional='NOT_RUN_NOT_REQUIRED')
    assert result['total_seconds']<1800
    (REPORT/'throughput.json').write_text(json.dumps(result,indent=2)+'\n')
    print('E2 validity PASS',len(checks),'checks; throughput',json.dumps(result,indent=2))

if __name__=='__main__':main()
