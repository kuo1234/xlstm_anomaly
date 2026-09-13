"""F-v3 pre-training gates; no optimizer step and no test/anomaly data."""
import json
import resource
import time
import torch
from phase_f_v3_common import *
from phase_f_v2_parity import parity
from phase_f_v3_canary import canary
from phase_f_lstm_observer import LAYERS,BASE_COLUMNS,EXPANDED_COLUMNS,summarize,expand_history

def main():
    start=time.perf_counter(); environment=configure(); sealed=verify_sealed_inputs()
    diagnostic=json.loads((ROOT/'reports/phase_f_v2/spark_cudnn_diagnostic.json').read_text())
    assert diagnostic['status']=='PASS' and diagnostic['conditions']['B']['all_required_original_gate_checks'] is True
    batch=load_windows('train')[:128]; fixed_canary=canary_input(); rows={}; defaults=[]
    for architecture in ('xlstm','lstm'):
        model=build(architecture,11).train(); initial=model_hash(model); opt=optimizer(model); defaults.append(opt.defaults.copy())
        torch.cuda.reset_peak_memory_stats(); tick=time.perf_counter()
        with forbid_native_predict() as trap:
            loss=reconstruction_loss(model,batch); loss.backward()
            finite_grads=all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in model.parameters())
            if not finite_grads: raise RuntimeError('Nonfinite gradient')
        torch.cuda.synchronize(); recurrent_grads={n:float(p.grad.norm()) for n,p in model.named_parameters() if recurrent_name(n)}
        gates=dict(finite_loss=bool(torch.isfinite(loss)),finite_gradients=finite_grads,
            nonzero_recurrent_gradient=any(v>0 for v in recurrent_grads.values()),no_native_predict=trap.call_count==0,
            no_parameter_mutation=model_hash(model)==initial)
        if architecture=='lstm': gates['scoped_cudnn_disabled']=model.last_cudnn_enabled is False
        else: gates['xLSTM_global_cudnn_enabled']=torch.backends.cudnn.enabled is True
        rows[architecture]=dict(gates=gates,initial_model_hash=initial,recurrent_gradient_norms=recurrent_grads,
            loss=float(loss.detach()),seconds_forward_backward=time.perf_counter()-tick,optimizer_steps=0,
            peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved(),
            optimizer_defaults=opt.defaults.copy(),parameter_count=sum(p.numel() for p in model.parameters()))
        model.zero_grad(set_to_none=True); rows[architecture]['parity']=parity(model,architecture)
        rows[architecture]['pretraining_canary']=canary(model,architecture,fixed_canary)
        if architecture=='xlstm': rows[architecture]['E2_seed11_initial_hash']=initial==json.loads((ROOT/'reports/phase_e2/architecture.json').read_text())['initial_model_hash']
        del model,opt
    schema_checks=dict(columns18=summarize({name:{k:torch.ones(2,2,38) for k in ('hidden','input','retention','memory')} for name in LAYERS}).shape==(2,18),
        expanded234=expand_history(torch.ones(40,18)).shape==(40,234),all_six_layers=len(LAYERS)==6)
    write_json(REPORT/'schema_binding.json',dict(base_columns=BASE_COLUMNS,expanded_columns=EXPANDED_COLUMNS,layers=LAYERS,
        mapping={'hidden':'h_t','input':'sigmoid(input gate)','retention':'sigmoid(forget gate)','memory':'c_t'},width=38,
        pooling='equal all six real layers; full H38 statistics',rolling='4/8/16/32',labels_extracted=False,
        unit_checks=schema_checks,source_schema_sha256=sha(ROOT/'reports/phase_f/lstm_common18_schema.json'),
        canary={'seed':CONFIG['canary']['seed'],'shape':CONFIG['canary']['shape'],'after_every_epoch':True,
            'code_sha256':sha(ROOT/'scripts/phase_f_v3_canary.py')}))
    all_gates=all(all(bool(v) for v in row['gates'].values()) and row['parity']['status']=='PASS' and row['pretraining_canary']['pass_'] and row.get('E2_seed11_initial_hash',True) for row in rows.values())
    result=dict(status='PASS' if all_gates and all(schema_checks.values()) and defaults[0]==defaults[1] else 'STOP',
        backend='F-v3 global F2 flags; scoped matched-LSTM cuDNN disabled',environment=environment,sealed_inputs=sealed,
        diagnostic_reference={'path':'reports/phase_f_v2/spark_cudnn_diagnostic.json','sha256':sha(ROOT/'reports/phase_f_v2/spark_cudnn_diagnostic.json'),'B_pass':True},
        architectures=rows,optimizer_semantics_equal=defaults[0]==defaults[1],schema_checks=schema_checks,
        total_seconds=time.perf_counter()-start,cpu_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        scientific_optimizer_steps=0,labels_read=False,test_sources_used=False,probe_fit=False)
    write_json(REPORT/'mechanical_gates.json',result)
    print(json.dumps(dict(status=result['status'],total_seconds=result['total_seconds'],
        failures={a:[k for k,v in r['gates'].items() if not v] for a,r in rows.items()},
        parity_failures={a:[k for k,v in r['parity']['checks'].items() if not v['pass_']] for a,r in rows.items()},
        canary_failures={a:[k for k,v in r['pretraining_canary']['checks'].items() if not v['pass_']] for a,r in rows.items()}),indent=2))
    if result['status']!='PASS': raise SystemExit(2)

if __name__=='__main__': main()
