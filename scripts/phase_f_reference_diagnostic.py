"""Unlabeled numerical diagnosis only; never selects/trains a scientific backend."""
import copy
import json
import time
import torch
from phase_f_common import configure,build,model_hash,REPORT,write_json
from phase_f_lstm_observer import Observer

def main():
    start=time.perf_counter(); environment=configure(); model=build('lstm',11).eval()
    initial=model_hash(model); gen=torch.Generator(device='cuda').manual_seed(710)
    x=torch.randn(131,64,8,device='cuda',generator=gen)[:4]
    rows={}
    with torch.no_grad():
        for name,tf32 in [('frozen_cudnn_tf32_true',True),('diagnostic_only_cudnn_tf32_false',False)]:
            # Each call gets fresh native zero recurrent states; no parameters change.
            torch.backends.cudnn.allow_tf32=tf32
            with Observer(model) as observer: output=model(x)
            rows[name]=dict(reference=observer.checks,output=output.cpu(),model_hash=model_hash(model))
        torch.backends.cudnn.allow_tf32=True
        cpu_model=copy.deepcopy(model).cpu()
        with Observer(cpu_model) as observer: cpu_output=cpu_model(x.cpu())
        rows['diagnostic_only_CPU']=dict(reference=observer.checks,output=cpu_output,model_hash=model_hash(cpu_model))
    base=rows['frozen_cudnn_tf32_true']['output']
    for row in rows.values():
        output=row.pop('output')
        row['reference_pass']=all(all(v if isinstance(v,bool) else v['pass_'] for v in r['checks'].values()) for r in row['reference'])
        row['max_output_difference_vs_frozen']=float((output-base).abs().max())
        assert row['model_hash']==initial
    assert torch.backends.cudnn.allow_tf32==environment['cudnn_allow_tf32']
    result=dict(scope='random-unlabeled reference diagnosis only; no backend amendment or scientific training',
        environment=environment,conditions=rows,seconds=time.perf_counter()-start,optimizer_steps=0,
        frozen_backend_restored=True,scientific_training_authorized_to_expand=False)
    write_json(REPORT/'reference_diagnostic.json',result)
    print(json.dumps({k:dict(reference_pass=v['reference_pass'],max_output_difference_vs_frozen=v['max_output_difference_vs_frozen']) for k,v in rows.items()},indent=2))

if __name__=='__main__': main()
