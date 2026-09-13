"""Finite mechanical preflight; no optimizer steps or scientific checkpoint."""
import inspect
import json
import resource
import time
import torch
from phase_f_common import *
from phase_f_parity import parity
from phase_f_lstm_observer import LAYERS, BASE_COLUMNS, EXPANDED_COLUMNS, summarize, expand_history

def main():
    environment=configure(); start=time.perf_counter()
    batch=load_windows('train')[:128]; rows={}; defaults=[]
    for arch in ('xlstm','lstm'):
        model=build(arch,11).train(); initial=model_hash(model); opt=optimizer(model)
        settings={k:v for k,v in opt.defaults.items()}; defaults.append(settings)
        torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats(); t=time.perf_counter()
        with forbid_native_predict() as trap:
            loss=reconstruction_loss(model,batch); loss.backward()
            _=score(model,batch)
        torch.cuda.synchronize(); seconds=time.perf_counter()-t
        grads={n:float(p.grad.norm()) for n,p in model.named_parameters() if recurrent_name(n) and p.grad is not None}
        gate=dict(finite_loss=bool(torch.isfinite(loss)),finite_gradients=all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in model.parameters()),
            nonzero_recurrent_gradient=any(v>0 for v in grads.values()),unchanged_parameters=model_hash(model)==initial,
            no_predict_calls=trap.call_count==0,observation_only_api=list(inspect.signature(reconstruction_loss).parameters)==['model','observations'])
        if arch=='xlstm':
            gate['E2_seed11_initial_hash']=initial==json.loads((ROOT/'reports/phase_e2/architecture.json').read_text())['initial_model_hash']
        rows[arch]=dict(gates=gate,initial_model_hash=initial,recurrent_gradient_norms=grads,
            loss=float(loss.detach()),seconds_forward_backward_plus_score=seconds,optimizer_steps=0,
            peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),
            optimizer_defaults=settings,parameters=sum(p.numel() for p in model.parameters()))
        model.zero_grad(set_to_none=True)
        rows[arch]['untrained_parity']=parity(model,arch)
        del model,opt
    # Negative control proves the guard actually rejects native predict calls.
    model=build('xlstm',11)
    try:
        with forbid_native_predict(): model.predict_step((batch,batch),0)
        blocked=False
    except RuntimeError as exc: blocked='Native predict_step forbidden' in str(exc)
    rejected=[]
    for seed in (3000,3009,999):
        try: allowed_prefix(seed); rejected.append(False)
        except ValueError: rejected.append(True)
    # No labels: synthetic scalar traces exercise equal six-layer summary/rolling.
    traces={name:{k:torch.full((2,2,38),float(i+1)) for k in ('hidden','input','retention','memory')} for i,name in enumerate(LAYERS)}
    summary=summarize(traces)
    schema_checks=dict(equal_six_layer_pool=bool(torch.equal(summary[:,0],torch.full((2,),3.5))),
        zero_same_state_delta=bool(torch.equal(summary[:,3],torch.zeros(2))),
        columns18=summary.shape==(2,18),expanded234=expand_history(torch.ones(40,18)).shape==(40,234),
        full_rolling_warmup=bool(torch.isnan(expand_history(torch.ones(40,18))[:31,-1]).all()))
    schema=dict(base_columns=BASE_COLUMNS,expanded_columns=EXPANDED_COLUMNS,layers=LAYERS,
        mapping=dict(hidden='h_t',input='sigmoid(i_raw)',retention='sigmoid(f_raw)',memory='c_t'),
        width=38,heads=None,pooling='within full H38 then equal all six layers',previous='actual t-1 within same window, zero only T1',
        epsilon=1e-8,statistics='population std; linear quantiles; RMS; no learned weights',
        rolling='unchanged E2 expand_history 4/8/16/32',
        code_sha256=sha(ROOT/'scripts/phase_f_lstm_observer.py'),expansion_code_sha256=sha(ROOT/'scripts/phase_e2_schema.py'),
        labels_extracted=False,unit_checks=schema_checks)
    write_json(REPORT/'lstm_common18_schema.json',schema)
    ok=blocked and all(rejected) and defaults[0]==defaults[1] and all(schema_checks.values()) and all(all(r['gates'].values()) and r['untrained_parity']['status']=='PASS' for r in rows.values())
    estimate=sum(r['seconds_forward_backward_plus_score']*(316*50*5) for r in rows.values())/3600
    result=dict(status='PASS' if ok else 'STOP',architectures=rows,native_predict_negative_control=blocked,
        forbidden_sources_rejected=all(rejected),optimizer_semantics_equal=defaults[0]==defaults[1],
        environment=environment,total_seconds=time.perf_counter()-start,cpu_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        conservative_cold_single_batch_full_training_hours=estimate,
        estimate_caveat='one cold batch includes backward plus another score, excludes Adam/validation; E2 warm pilot also reported; not measured full runtime',
        scientific_optimizer_steps=0,test_sources_used=False,labels_read=False)
    write_json(REPORT/'mechanical_gates.json',result)
    print(json.dumps(dict(status=result['status'],hours_estimate=estimate,total_seconds=result['total_seconds'],
        gate_failures={a:[k for k,v in r['gates'].items() if not v] for a,r in rows.items()},
        parity_failures={a:[k for k,v in r['untrained_parity']['checks'].items() if not v['pass_']] for a,r in rows.items()}),indent=2))
    if not ok: raise SystemExit(2)
    if estimate>160: raise SystemExit('Compute estimate exceeds prospective escalation limit')

if __name__=='__main__': main()
