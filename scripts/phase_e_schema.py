"""Frozen common scalar H3a schema; no labels, model fitting or matrix fallback."""
import torch

BASE_COLUMNS=['hidden_mean','hidden_std','hidden_rms','hidden_delta_rms',
    'input_mean','input_std','input_q10','input_q90','input_delta_mean',
    'retention_mean','retention_std','retention_q10','retention_q90','retention_delta_mean',
    'memory_mean','memory_std','memory_rms','memory_relative_delta_norm']
ROLLING=(4,8,16,32)
EXPANDED_COLUMNS=[name for c in BASE_COLUMNS for name in
    [c,*[f'{c}_trailing_{k}_{s}' for k in ROLLING for s in ('mean','std','slope')]]]


def summarize(layers):
    """Each layer has B,T,heads,width tensors hidden,input,retention,memory.

    Summary per head then equal means over heads/layers; final invocation only.
    A one-timestep call has its own zero previous state (never decoder carry).
    """
    if not layers:raise ValueError('Missing scalar recurrent cells blocks H3a')
    summaries=[]
    for layer in layers:
        if set(layer)!={'hidden','input','retention','memory'}:
            raise ValueError('All common scalar features required; no substitution')
        shape=layer['hidden'].shape
        if len(shape)!=4 or any(t.shape!=shape or not torch.isfinite(t).all() for t in layer.values()):
            raise ValueError('Expected finite equally shaped B,T,heads,width scalar traces')
        cols=[]
        for name in ('hidden','input','retention','memory'):
            trace=layer[name];v=trace[:,-1];prev=trace[:,-2] if trace.shape[1]>1 else torch.zeros_like(v)
            cols.extend([v.mean(-1),v.std(-1,correction=0)])
            if name in ('input','retention'):
                cols.extend([torch.quantile(v,.1,dim=-1),torch.quantile(v,.9,dim=-1),(v-prev).mean(-1)])
            else:
                cols.append(v.square().mean(-1).sqrt())
                cols.append((v-prev).square().mean(-1).sqrt() if name=='hidden' else
                    torch.linalg.vector_norm(v-prev,dim=-1)/(torch.linalg.vector_norm(prev,dim=-1)+1e-8))
        summaries.append(torch.stack(cols,-1).mean(1))
    return torch.stack(summaries).mean(0)


def expand_history(base):
    """T,18 ordered decisions; NaN warmup must be excluded by evaluator."""
    if base.ndim!=2 or base.shape[1]!=18:raise ValueError('Expected T,18')
    out=[]
    for j in range(18):
        v=base[:,j];cols=[v]
        for k in ROLLING:
            pad=v.new_full((min(k-1,len(v)),),float('nan'))
            if len(v)<k:
                cols.extend([pad,pad,pad]);continue
            x=v.unfold(0,k,1);t=torch.arange(k,device=v.device,dtype=v.dtype);t=t-t.mean()
            for a in (x.mean(-1),x.std(-1,correction=0),(x*t).sum(-1)/t.square().sum()):
                cols.append(torch.cat([pad,a]))
        out.extend(cols)
    return torch.stack(out,-1)
