"""F-v2 pre-training gates and sealed E2 cross-backend comparison.

This script performs no optimizer step. Its outputs are written only under the
versioned reports/phase_f_v2 directory; reports/phase_f is immutable F-v1
evidence.
"""
import hashlib
import json
import resource
import time
import torch
import numpy as np
from phase_f_v2_common import *
from phase_f_v2_parity import parity, compare
from phase_f_lstm_observer import LAYERS, BASE_COLUMNS, EXPANDED_COLUMNS, summarize, expand_history
from phase_e2_common import build as e2_build, configure as e2_configure, model_hash as e2_model_hash
from phase_e2_observer import Observer as XObserver

ATOL=1e-5; RTOL=1e-4

def tensor_compare(a,b):
    return dict(exact=bool(torch.equal(a,b)),allclose=bool(torch.allclose(a,b,atol=ATOL,rtol=RTOL)),
        max_abs=float((a-b).abs().max()),shape=list(a.shape),dtype_a=str(a.dtype),dtype_b=str(b.dtype))

def capture_xlstm(model, x, allow_tf32):
    with backend_state(allow_tf32), torch.no_grad(), XObserver(model) as observer:
        output=model(x); score=(output-x).square().mean((1,2)); features=observer.summary()
    traces={cell:{name:value.clone() for name,value in vals.items()} for cell,vals in observer.latest.items()}
    checks=[dict(row) for row in observer.checks]
    return dict(output=output,score=score,features=features,traces=traces,checks=checks)

def build_old_e2():
    with backend_state(True):
        e2_configure(); model=e2_build(); model.eval()
    return model

def cross_backend():
    fixture_dir=ROOT/'data/phase_e2/verified'
    observations=torch.from_numpy(np.load(fixture_dir/'observations.npy',allow_pickle=False)).cuda()
    expected_output=torch.from_numpy(np.load(fixture_dir/'output.npy',allow_pickle=False)).cuda()
    expected_score=torch.from_numpy(np.load(fixture_dir/'scores.npy',allow_pickle=False)).cuda()
    expected_summary=torch.from_numpy(np.load(fixture_dir/'summary.npy',allow_pickle=False)).cuda()
    old=build_old_e2(); old_hash=e2_model_hash(old)
    new=build('xlstm',11); new.eval(); new_hash=model_hash(new)
    old_capture=capture_xlstm(old,observations,True)
    new_capture=capture_xlstm(new,observations,False)
    out={
        'fixture': {k:sha(fixture_dir/(k+'.npy')) for k in ('observations','output','scores','summary')},
        'old_e2_model_hash':old_hash,
        'new_f2_model_hash':new_hash,
        'expected_old_initial_hash':json.loads((ROOT/'reports/phase_e2/architecture.json').read_text())['initial_model_hash'],
        'old_fixture_output':tensor_compare(old_capture['output'],expected_output),
        'old_fixture_score':tensor_compare(old_capture['score'],expected_score),
        'old_fixture_common18':tensor_compare(old_capture['features'],expected_summary),
        'output':tensor_compare(new_capture['output'],old_capture['output']),
        'reconstruction_score':tensor_compare(new_capture['score'],old_capture['score']),
        'common18_features':tensor_compare(new_capture['features'],old_capture['features']),
        'scalar_hidden_and_final':{},
        'scalar_gate_memory_traces':{},
        'backend': {'old_cudnn_allow_tf32':True,'new_cudnn_allow_tf32':False,'atol':ATOL,'rtol':RTOL},
    }
    for cell in sorted(old_capture['traces']):
        for key in ('hidden','input','retention','memory'):
            out['scalar_gate_memory_traces'][f'{cell}.{key}']=tensor_compare(new_capture['traces'][cell][key],old_capture['traces'][cell][key])
        out['scalar_hidden_and_final'][cell]=tensor_compare(new_capture['traces'][cell]['hidden'][:,-1],old_capture['traces'][cell]['hidden'][:,-1])
    # The frozen fixture is B=4; exercise full and B3/B1 partitions under both flags.
    out['batch_partition']={}
    for b in (3,1):
        with backend_state(True), torch.no_grad(): old_parts=torch.cat([old(part) for part in observations.split(b)])
        with backend_state(False), torch.no_grad(): new_parts=torch.cat([new(part) for part in observations.split(b)])
        out['batch_partition'][f'B{b}']={
            'old_self_invariant':tensor_compare(old_parts,old_capture['output']),
            'new_self_invariant':tensor_compare(new_parts,new_capture['output']),
            'cross_backend':tensor_compare(new_parts,old_parts)}
    # Prefix causality uses the exact fixture prefix and a deterministic suffix-only replacement.
    changed=observations.clone(); changed[:,32:]=observations[:,32:].flip(1)
    with backend_state(True), torch.no_grad(): old_changed=old(changed)
    with backend_state(False), torch.no_grad(): new_changed=new(changed)
    out['prefix_causality']={
        'old_self':tensor_compare(old_changed[:,:32],old_capture['output'][:,:32]),
        'new_self':tensor_compare(new_changed[:,:32],new_capture['output'][:,:32]),
        'cross_original_prefix':tensor_compare(new_capture['output'][:,:32],old_capture['output'][:,:32]),
        'cross_changed_prefix':tensor_compare(new_changed[:,:32],old_changed[:,:32])}
    out['old_observer_checks']=old_capture['checks']; out['new_observer_checks']=new_capture['checks']
    out['all_required_cross_comparisons_pass']=all([
        old_capture['output'].shape==expected_output.shape,
        out['old_fixture_output']['allclose'],out['old_fixture_score']['allclose'],out['old_fixture_common18']['allclose'],
        out['output']['allclose'],out['reconstruction_score']['allclose'],out['common18_features']['allclose'],
        all(v['allclose'] for v in out['scalar_hidden_and_final'].values()),
        all(v['allclose'] for v in out['scalar_gate_memory_traces'].values()),
        all(v['cross_backend']['allclose'] and v['old_self_invariant']['allclose'] and v['new_self_invariant']['allclose'] for v in out['batch_partition'].values()),
        out['prefix_causality']['old_self']['allclose'],out['prefix_causality']['new_self']['allclose'],
        out['prefix_causality']['cross_original_prefix']['allclose'],out['prefix_causality']['cross_changed_prefix']['allclose']])
    return out

def mechanical():
    environment=configure(); sealed=verify_sealed_inputs(); start=time.perf_counter(); rows={}; defaults=[]
    batch=load_windows('train')[:128]
    for architecture in ('xlstm','lstm'):
        model=build(architecture,11).train(); initial=model_hash(model); opt=optimizer(model); defaults.append(opt.defaults.copy())
        torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats(); tick=time.perf_counter()
        with forbid_native_predict() as trap:
            loss=reconstruction_loss(model,batch); loss.backward(); _=score(model,batch)
        torch.cuda.synchronize()
        recurrent_grads={n:float(p.grad.norm()) for n,p in model.named_parameters() if recurrent_name(n) and p.grad is not None}
        gates=dict(finite_loss=bool(torch.isfinite(loss)),finite_gradients=all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in model.parameters()),
            nonzero_recurrent_gradient=any(v>0 for v in recurrent_grads.values()),no_native_predict=trap.call_count==0,
            no_parameter_mutation=model_hash(model)==initial)
        rows[architecture]=dict(gates=gates,initial_model_hash=initial,recurrent_gradient_norms=recurrent_grads,
            loss=float(loss.detach()),seconds_forward_backward_plus_score=time.perf_counter()-tick,
            optimizer_steps=0,peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),
            optimizer_defaults=opt.defaults.copy(),parameter_count=sum(p.numel() for p in model.parameters()))
        model.zero_grad(set_to_none=True); rows[architecture]['parity']=parity(model,architecture)
        if architecture=='xlstm': rows[architecture]['E2_seed11_initial_hash']=initial==json.loads((ROOT/'reports/phase_e2/architecture.json').read_text())['initial_model_hash']
        del model,opt
    schema_checks=dict(columns18=summarize({name:{k:torch.ones(2,2,38) for k in ('hidden','input','retention','memory')} for name in LAYERS}).shape==(2,18),
        expanded234=expand_history(torch.ones(40,18)).shape==(40,234),
        all_six_layers=len(LAYERS)==6)
    write_json(REPORT/'schema_binding.json',dict(base_columns=BASE_COLUMNS,expanded_columns=EXPANDED_COLUMNS,layers=LAYERS,
        mapping={'hidden':'h_t','input':'sigmoid(input gate)','retention':'sigmoid(forget gate)','memory':'c_t'},
        width=38,pooling='equal all six real layers; full H38 statistics',rolling='4/8/16/32',
        labels_extracted=False,unit_checks=schema_checks,source_schema_sha256=sha(ROOT/'reports/phase_f/lstm_common18_schema.json')))
    cross=cross_backend(); write_json(REPORT/'cross_backend.json',cross)
    gates_ok=all(all(v for v in row['gates'].values()) and row['parity']['status']=='PASS' and (row.get('E2_seed11_initial_hash',True)) for row in rows.values())
    result=dict(status='PASS' if gates_ok and all(schema_checks.values()) and cross['all_required_cross_comparisons_pass'] and defaults[0]==defaults[1] else 'STOP',
        backend='F-v2 cudnn.allow_tf32=False',environment=environment,sealed_inputs=sealed,architectures=rows,
        optimizer_semantics_equal=defaults[0]==defaults[1],schema_checks=schema_checks,cross_backend_status=cross['all_required_cross_comparisons_pass'],
        total_seconds=time.perf_counter()-start,cpu_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        scientific_optimizer_steps=0,labels_read=False,test_sources_used=False,probe_fit=False)
    write_json(REPORT/'mechanical_gates.json',result)
    print(json.dumps(dict(status=result['status'],total_seconds=result['total_seconds'],cross_backend=result['cross_backend_status'],
        failures={a:[k for k,v in r['gates'].items() if not v] for a,r in rows.items()},
        parity_failures={a:[k for k,v in r['parity']['checks'].items() if not v['pass_']] for a,r in rows.items()}),indent=2))
    if result['status']!='PASS': raise SystemExit(2)

if __name__=='__main__': mechanical()
