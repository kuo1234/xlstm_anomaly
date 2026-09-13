"""Read-only standard nn.LSTM gate replay; all six real layers, no fake heads."""
import torch
from phase_e2_schema import BASE_COLUMNS, EXPANDED_COLUMNS, expand_history

LAYERS=tuple(f'{stack}.{i}' for stack in ('encoder','decoder') for i in range(3))

def replay(layer, x):
    B,T,_=x.shape
    h=x.new_zeros(B,38); c=h.clone()
    traces={k:[] for k in ('hidden','input','retention','memory')}
    for t in range(T):
        raw=torch.nn.functional.linear(x[:,t],layer.weight_ih_l0,layer.bias_ih_l0)+torch.nn.functional.linear(h,layer.weight_hh_l0,layer.bias_hh_l0)
        ir,fr,gr,orr=raw.chunk(4,-1)
        i=ir.sigmoid(); f=fr.sigmoid()
        c=f*c+i*gr.tanh(); h=orr.sigmoid()*c.tanh()
        for name,value in zip(traces,(h,i,f,c)): traces[name].append(value)
    return {k:torch.stack(v,1) for k,v in traces.items()}

def summarize(traces):
    if set(traces)!=set(LAYERS): raise ValueError('All six LSTM layers required')
    layers=[]
    for name in LAYERS:
        cols=[]
        for key in ('hidden','input','retention','memory'):
            seq=traces[name][key]
            if seq.ndim!=3 or seq.shape[-1]!=38 or not torch.isfinite(seq).all():
                raise ValueError('Expected finite B,T,H38 scalar traces')
            v=seq[:,-1]; previous=seq[:,-2] if seq.shape[1]>1 else torch.zeros_like(v)
            cols.extend([v.mean(-1),v.std(-1,correction=0)])
            if key in ('input','retention'):
                cols.extend([torch.quantile(v,.1,dim=-1),torch.quantile(v,.9,dim=-1),(v-previous).mean(-1)])
            else:
                cols.append(v.square().mean(-1).sqrt())
                cols.append((v-previous).square().mean(-1).sqrt() if key=='hidden' else
                    torch.linalg.vector_norm(v-previous,dim=-1)/(torch.linalg.vector_norm(previous,dim=-1)+1e-8))
        layers.append(torch.stack(cols,-1))
    return torch.stack(layers).mean(0)

class Observer:
    def __init__(self, model): self.model=model; self.handles=[]; self.latest={}; self.checks=[]
    def __enter__(self):
        layers={n:m for n,m in self.model.named_modules() if isinstance(m,torch.nn.LSTM)}
        if set(layers)!=set(LAYERS): raise ValueError('Unexpected recurrent layer binding')
        for name,layer in layers.items():
            def hook(module,args,output,name=name):
                with torch.no_grad():
                    traces=replay(module,args[0].detach())
                    sequence,(h,c)=output
                    checks={}
                    for key,expected,actual in [('sequence_h',traces['hidden'],sequence),('final_h',traces['hidden'][:,-1],h[0]),('final_c',traces['memory'][:,-1],c[0])]:
                        checks[key]=dict(pass_=bool(torch.allclose(expected,actual,atol=1e-5,rtol=1e-4)),max_abs=float((expected-actual).abs().max()))
                    checks['finite']=all(bool(torch.isfinite(v).all()) for v in traces.values())
                    checks['gate_range']=all(bool(((traces[k]>=0)&(traces[k]<=1)).all()) for k in ('input','retention'))
                    self.checks.append(dict(layer=name,checks=checks))
                    self.latest[name]=traces
            self.handles.append(layer.register_forward_hook(hook))
        return self
    def __exit__(self,*exc):
        for handle in self.handles: handle.remove()
    def summary(self): return summarize(self.latest)

def extract(model, observations):
    with torch.no_grad(),Observer(model) as observer:
        output=model(observations); features=observer.summary()
    if not all(all(v if isinstance(v,bool) else v['pass_'] for v in row['checks'].values()) for row in observer.checks):
        raise RuntimeError('LSTM manual recurrence parity failed')
    return (output-observations).square().mean((1,2)),features
