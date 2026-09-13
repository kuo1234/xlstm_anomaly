"""Bounded diagnostic for quarantined LSTM seed-11; no training or labels."""
import json
import hashlib
import time
import numpy as np
import torch
from phase_f_v2_common import ROOT,REPORT,build,model_hash,sha,write_json,configure,backend_state
from phase_f_v2_parity import parity,compare

ATOL=1e-5; RTOL=1e-4
CHECKPOINT=ROOT/'data/phase_f_v2/runs/lstm_11/best.pt'
FIXTURE=ROOT/'data/phase_e2/verified/observations.npy'

def layer_capture(model,x,context):
    names=('input_projection','encoder.0','encoder.1','encoder.2','decoder.0','decoder.1','decoder.2','gelu','output_projection')
    modules=dict(model.named_modules()); handles=[]; records={name:[] for name in names}
    for name in names:
        def hook(module,args,output,name=name):
            value=output[0] if isinstance(output,tuple) else output
            records[name].append(value.detach().clone())
        handles.append(modules[name].register_forward_hook(hook))
    try:
        with context:
            full=model(x)
            parts=torch.cat([model(part) for part in x.split(1)])
    finally:
        for handle in handles: handle.remove()
    # The first record is B=131; following records are B=1 and are concatenated.
    result={}
    for name,values in records.items():
        assert len(values)==1+len(x) and values[0].shape[0]==len(x)
        partition=torch.cat(values[1:])
        result[name]=compare(values[0],partition)
    result['model_output']=compare(full,parts)
    return result

def run_condition(name,allow_tf32,enabled,fixture,parity_input):
    model=build('lstm',11); payload=torch.load(CHECKPOINT,map_location='cuda',weights_only=True); model.load_state_dict(payload['model']); model.eval()
    context=torch.backends.cudnn.flags(enabled=enabled,benchmark=False,deterministic=True,allow_tf32=allow_tf32)
    with context:
        state=dict(cudnn_enabled=torch.backends.cudnn.enabled,cudnn_deterministic=torch.backends.cudnn.deterministic,
            cudnn_benchmark=torch.backends.cudnn.benchmark,cudnn_allow_tf32=torch.backends.cudnn.allow_tf32,
            matmul_allow_tf32=torch.backends.cuda.matmul.allow_tf32)
        frozen=parity(model,'lstm')
        # The layer-wise diagnostic is specifically B128 versus B1. The
        # complete frozen parity runner still uses its original B131 fixture.
        layer_input=parity_input[:128]
        layer=layer_capture(model,layer_input,context=torch.backends.cudnn.flags(enabled=enabled,benchmark=False,deterministic=True,allow_tf32=allow_tf32))
        with torch.no_grad():
            fixture_out=model(fixture); fixture_score=(fixture_out-fixture).square().mean((1,2))
    # parity() is the original complete gate set; layer diagnostics are supplemental.
    return dict(condition=name,backend_state=state,model_hash=model_hash(model),parity=frozen,
        layer_partition_divergence=layer,fixture_output_hash=hashlib.sha256(fixture_out.detach().cpu().numpy().tobytes()).hexdigest(),
        fixture_score_hash=hashlib.sha256(fixture_score.detach().cpu().numpy().tobytes()).hexdigest(),
        original_frozen_gates_pass=frozen['status']=='PASS' and all(v['pass_'] for v in layer.values()))

def main():
    start=time.perf_counter(); environment=configure()
    assert CHECKPOINT.exists() and FIXTURE.exists()
    payload=torch.load(CHECKPOINT,map_location='cpu',weights_only=True)
    assert 'model' in payload
    fixture=torch.from_numpy(np.load(FIXTURE,allow_pickle=False)).cuda()
    gen=torch.Generator(device='cuda').manual_seed(710)
    parity_input=torch.randn(131,64,8,device='cuda',generator=gen)
    checkpoint_manifest=json.loads((REPORT/'runs/lstm_11/manifest.json').read_text())
    expected_hash=checkpoint_manifest['best_model_hash']
    loaded=build('lstm',11); loaded.load_state_dict(payload['model']); loaded.eval(); assert model_hash(loaded)==expected_hash
    # A is existing F-v2 CUDA+cuDNN; B disables cuDNN only while matched LSTM runs.
    a=run_condition('A_f2_cuda_cudnn_enabled',allow_tf32=False,enabled=True,fixture=fixture,parity_input=parity_input)
    b=run_condition('B_cuda_matched_lstm_cudnn_disabled',allow_tf32=False,enabled=False,fixture=fixture,parity_input=parity_input)
    required=['BWD','output_permutation','score_permutation','partition_B128_output','partition_B128_score','partition_B3_output','partition_B3_score','partition_B1_output','partition_B1_score','observer_output_bitwise','observer_score_bitwise','observer_rng','reference','finite_common18','reset_output','reset_features','feature_permutation','feature_partition','prefix_output','prefix_states','shorter_prefix_output','shorter_prefix_schema','no_native_predict','no_parameter_mutation']
    for result in (a,b):
        result['required_gate_summary']={name:result['parity']['checks'][name]['pass_'] for name in required}
        result['all_required_original_gate_checks']=all(result['required_gate_summary'].values())
    result=dict(status='PASS' if b['original_frozen_gates_pass'] and b['all_required_original_gate_checks'] else 'STOP',
        scope='quarantined data/phase_f_v2/runs/lstm_11/best.pt only; random unlabeled parity fixture; no training/labels/test/probes',
        environment=environment,checkpoint=str(CHECKPOINT.relative_to(ROOT)),checkpoint_sha256=sha(CHECKPOINT),
        checkpoint_model_hash=expected_hash,fixture=str(FIXTURE.relative_to(ROOT)),fixture_sha256=sha(FIXTURE),
        parity_input=dict(shape=list(parity_input.shape),seed=710,labels_used=False),conditions={'A':a,'B':b},
        tolerances={'atol':ATOL,'rtol':RTOL},v2_backend_unchanged=True,elapsed_seconds=time.perf_counter()-start,
        xLSTM_global_cudnn_disabled=False,optimizer_steps=0,labels_read=False,test_sources_used=False,probe_fit=False)
    write_json(REPORT/'spark_cudnn_diagnostic.json',result)
    write_json(REPORT/'spark_cudnn_diagnostic_code.json',{'script_sha256':sha(ROOT/'scripts/phase_f_v2_spark_cudnn_diagnostic.py'),'command':'rtk data/phase_e2/venv/bin/python scripts/phase_f_v2_spark_cudnn_diagnostic.py','checkpoint_sha256':sha(CHECKPOINT),'fixture_sha256':sha(FIXTURE)})
    print(json.dumps(dict(status=result['status'],A=a['original_frozen_gates_pass'],B=b['original_frozen_gates_pass'],
        B_required=b['all_required_original_gate_checks'],A_failures=[k for k,v in a['parity']['checks'].items() if not v['pass_']],
        B_failures=[k for k,v in b['parity']['checks'].items() if not v['pass_']],elapsed_seconds=result['elapsed_seconds']),indent=2))
    if result['status']!='PASS': raise SystemExit(2)

if __name__=='__main__': main()
