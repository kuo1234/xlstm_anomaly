"""Bounded identical-buffer replay diagnosis after STOP; no harm comparisons."""
import json
import numpy as np
import torch
from phase_d_operator import ROOT,REPORT,update,object_hash,rng_state
from phase_d_grid import load,reset,score
from phase_d_buffers import compose
from phase_c_run import state_hash


def main():
    initial_flags=dict(cudnn_deterministic=torch.backends.cudnn.deterministic,
        cudnn_benchmark=torch.backends.cudnn.benchmark,deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
        float32_matmul_precision=torch.get_float32_matmul_precision())
    arms,x,y,mask,m=compose(3000,'abrupt','spike')
    adapter,state=load(11)
    mean=np.array(state['scaler']['scaler_mean']); scale=np.array(state['scaler']['scaler_scale'])
    buffer=torch.from_numpy(np.ascontiguousarray((arms[10]-mean)/scale,dtype=np.float32)).cuda()
    test=torch.from_numpy(np.ascontiguousarray((x-mean)/scale,dtype=np.float32))
    conditions=[]
    for deterministic in (False,True):
        torch.backends.cudnn.deterministic=deterministic
        torch.backends.cudnn.benchmark=False
        runs=[]; params=[]; scores=[]
        for repeat in range(3):
            reset(adapter,state)
            pre=dict(model=state_hash(adapter.model),optimizer=object_hash(adapter.optimizer.state_dict()),rng=object_hash(rng_state()))
            losses=update(adapter,buffer)
            s=score(adapter.model,test)
            runs.append(dict(repeat=repeat,pre=pre,losses=losses,model_sha256=state_hash(adapter.model),
                optimizer_sha256=object_hash(adapter.optimizer.state_dict()),score_tensor_sha256=object_hash(s)))
            params.append({k:p.detach().clone() for k,p in adapter.model.named_parameters() if p.requires_grad})
            scores.append(s)
        checks=[]
        for i in (1,2):
            checks.append(dict(reference=0,repeat=i,pre_states_exact=runs[0]['pre']==runs[i]['pre'],
                loss_exact=runs[0]['losses']==runs[i]['losses'],model_exact=runs[0]['model_sha256']==runs[i]['model_sha256'],
                optimizer_exact=runs[0]['optimizer_sha256']==runs[i]['optimizer_sha256'],scores_exact=bool(np.array_equal(scores[0],scores[i])),
                max_parameter_abs_difference=max(float((params[0][k]-params[i][k]).abs().max()) for k in params[0]),
                max_score_abs_difference=float(np.abs(scores[0]-scores[i]).max())))
        conditions.append(dict(cudnn_deterministic=deterministic,cudnn_benchmark=False,runs=runs,comparisons=checks))
    result=dict(scope='Six repeats of same existing c10 buffer, not new H1 curves; no AP or harm comparisons computed',
        fresh_process_flags=initial_flags,conditions=conditions,
        interpretation='Check whether missing cuDNN deterministic flag explains repeat failure; candidate repair only, no grid restart authorized by this diagnostic')
    (REPORT/'repeat_failure_diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
