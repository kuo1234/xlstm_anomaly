"""Read-only replay of the exact2.0.5 scalar equations, never a replacement cell."""
import torch
from phase_e2_schema import SCALAR_CELLS,summarize

def scalar_reference(cell,x):
    B,T,_=x.shape;N=cell.config.num_heads;D=cell.config.head_dim
    kernel=cell._recurrent_kernel_int2ext(cell._recurrent_kernel).detach()
    bias=cell._bias_int2ext(cell._bias).detach().permute(1,0,2)
    h=x.new_zeros(B,N,D);c=h.clone();n=h.clone();m=h.clone()
    records={k:[] for k in ('hidden','input','retention','memory')};states=[]
    for t in range(T):
        raw=x[:,t].reshape(B,4,N,D)+torch.einsum('bni,nigo->bgno',h,kernel)+bias
        ir,fr,zr,orr=raw.unbind(1);fm=m+torch.nn.functional.logsigmoid(fr)
        m=ir if bool(torch.all(n==0)) else torch.maximum(ir,fm)
        # This upper cap is part of official xlstm2.0.5, unlike2.0.3.
        i=torch.minimum(torch.exp(ir-m),torch.ones_like(ir))
        f=torch.minimum(torch.exp(fm-m),torch.ones_like(ir))
        c=f*c+i*torch.tanh(zr);n=f*n+i;u=c/n;h=torch.sigmoid(orr)*u
        for key,v in zip(records,(h,i,f,u)):records[key].append(v)
        states.append(torch.stack([h,c,n,m]).reshape(4,B,-1))
    return {k:torch.stack(v,1) for k,v in records.items()},torch.stack(states,1)

class Observer:
    def __init__(self,model):self.model=model;self.handles=[];self.latest={};self.checks=[];self.calls={}
    def __enter__(self):
        cells={n:m for n,m in self.model.named_modules() if n.endswith('slstm_cell')}
        if set(cells)!=set(SCALAR_CELLS):raise ValueError('Unexpected actual scalar-cell schema')
        for name,cell in cells.items():
            def hook(module,args,output,name=name):
                with torch.no_grad():
                    traces,states=scalar_reference(module,args[0].detach());actual,final=output
                    expected=traces['hidden'].permute(0,2,1,3)
                    self.checks.append(dict(cell=name,sequence_length=args[0].shape[1],
                        hidden_close=bool(torch.allclose(expected,actual,atol=1e-5,rtol=1e-4)),
                        state_close=bool(torch.allclose(states[:,-1],final,atol=1e-5,rtol=1e-4)),
                        max_hidden_abs=float((expected-actual).abs().max()),max_state_abs=float((states[:,-1]-final).abs().max()),
                        finite=bool(torch.isfinite(states).all()) and all(bool(torch.isfinite(v).all()) for v in traces.values()),
                        all_float32=states.dtype==actual.dtype==final.dtype==torch.float32))
                    self.latest[name]=traces;self.calls[name]=self.calls.get(name,0)+1
            self.handles.append(cell.register_forward_hook(hook))
        return self
    def __exit__(self,*exc):
        for handle in self.handles:handle.remove()
    def summary(self):return summarize(self.latest)

def extract(model,x):
    """Observation-only scores/features; no label/scaler/threshold input or fitting."""
    with torch.no_grad(),Observer(model) as observer:
        output=model(x);features=observer.summary()
    if not all(c['hidden_close'] and c['state_close'] and c['finite'] and c['all_float32'] for c in observer.checks):
        raise RuntimeError('Scalar observer reference parity failed')
    return (output-x).square().mean((1,2)),features
