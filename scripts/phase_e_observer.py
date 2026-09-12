"""Read-only scalar-cell observation via independently replayed float32 equations.

No output replacement, parameter mutation, labels, recurrent carry or learned gate.
Observed reference states are usable only after numerical parity with that cell.
"""
import torch
from phase_e_schema import summarize


def scalar_reference(cell,x):
    B,T,_=x.shape;N=cell.config.num_heads;D=cell.config.head_dim
    kernel=cell._recurrent_kernel_int2ext(cell._recurrent_kernel).detach()
    bias=cell._bias_int2ext(cell._bias).detach().permute(1,0,2)
    h=x.new_zeros(B,N,D);c=h.clone();n=h.clone();m=h.clone()
    records={k:[] for k in ('hidden','input','retention','memory')};states=[]
    for t in range(T):
        recurrent=torch.einsum('bni,nigo->bgno',h,kernel)
        raw=x[:,t].reshape(B,4,N,D)+recurrent+bias
        ir,fr,zr,orr=raw.unbind(1)
        fm=m+torch.nn.functional.logsigmoid(fr)
        m=ir if bool(torch.all(n==0)) else torch.maximum(ir,fm)
        i=torch.exp(ir-m);f=torch.exp(fm-m)
        c=f*c+i*torch.tanh(zr);n=f*n+i;u=c/n;h=torch.sigmoid(orr)*u
        for key,v in zip(records,(h,i,f,u)):records[key].append(v)
        states.append(torch.stack([h,c,n,m]).reshape(4,B,-1))
    return {k:torch.stack(v,1) for k,v in records.items()},torch.stack(states,1)


class Observer:
    def __init__(self,model):
        self.model=model;self.handles=[];self.latest={};self.errors=[];self.calls={}
    def __enter__(self):
        for name,cell in self.model.named_modules():
            if not name.endswith('slstm_cell'):continue
            def hook(module,args,output,name=name):
                with torch.no_grad():
                    traces,states=scalar_reference(module,args[0].detach())
                    expected=traces['hidden'].permute(0,2,1,3)
                    actual,final=output
                    self.errors.append(dict(name=name,hidden_max_abs=float((expected-actual).abs().max()),
                        hidden_close=bool(torch.allclose(expected,actual,atol=1e-5,rtol=1e-4)),
                        final_state_max_abs=float((states[:,-1]-final).abs().max()),
                        final_state_close=bool(torch.allclose(states[:,-1],final,atol=1e-5,rtol=1e-4)),
                        finite=bool(torch.isfinite(states).all()) and all(bool(torch.isfinite(v).all()) for v in traces.values())))
                    self.latest[name]=traces;self.calls[name]=self.calls.get(name,0)+1
            self.handles.append(cell.register_forward_hook(hook))
        return self
    def __exit__(self,*exc):
        for h in self.handles:h.remove()
    def summary(self):return summarize([self.latest[k] for k in sorted(self.latest)])
