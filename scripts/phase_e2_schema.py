"""E2 common18 binding: actual four full-window scalar cells, no v1 singleton rule."""
import torch

BASE_COLUMNS=['hidden_mean','hidden_std','hidden_rms','hidden_delta_rms',
    'input_mean','input_std','input_q10','input_q90','input_delta_mean',
    'retention_mean','retention_std','retention_q10','retention_q90','retention_delta_mean',
    'memory_mean','memory_std','memory_rms','memory_relative_delta_norm']
SCALAR_CELLS=tuple(f'{stack}.blocks.{i}.xlstm.slstm_cell' for stack in ('encoder','decoder') for i in (0,1))
ROLLING=(4,8,16,32)
EXPANDED_COLUMNS=[name for c in BASE_COLUMNS for name in
    [c,*[f'{c}_trailing_{k}_{s}' for k in ROLLING for s in ('mean','std','slope')]]]

def summarize(traces):
    """B,T,heads,width; actual previous timestamp at T-2 for encoder AND decoder.

    Equal per-head statistics then equal four layers. Only T=1 uses zero previous
    state; never treat the improved decoder's full window as singleton calls.
    """
    if set(traces)!=set(SCALAR_CELLS):raise ValueError('All four actual scalar layers required')
    layers=[]
    for cell in SCALAR_CELLS:
        layer=traces[cell]
        if set(layer)!={'hidden','input','retention','memory'}:raise ValueError('Missing common scalar feature')
        shape=layer['hidden'].shape
        if len(shape)!=4 or shape[1]<1 or any(v.shape!=shape or not torch.isfinite(v).all() for v in layer.values()):
            raise ValueError('Expected finite B,T,heads,width traces')
        cols=[]
        for name in ('hidden','input','retention','memory'):
            sequence=layer[name];v=sequence[:,-1]
            previous=sequence[:,-2] if shape[1]>1 else torch.zeros_like(v)
            cols.extend([v.mean(-1),v.std(-1,correction=0)])
            if name in ('input','retention'):
                cols.extend([torch.quantile(v,.1,dim=-1),torch.quantile(v,.9,dim=-1),(v-previous).mean(-1)])
            else:
                cols.append(v.square().mean(-1).sqrt())
                cols.append((v-previous).square().mean(-1).sqrt() if name=='hidden' else
                    torch.linalg.vector_norm(v-previous,dim=-1)/(torch.linalg.vector_norm(previous,dim=-1)+1e-8))
        layers.append(torch.stack(cols,-1).mean(1))
    return torch.stack(layers).mean(0)

def expand_history(base):
    """T,18; complete trailing decision windows only, NaN warmup excluded later."""
    if base.ndim!=2 or base.shape[1]!=18:raise ValueError('Expected T,18')
    out=[]
    for j in range(18):
        v=base[:,j];cols=[v]
        for k in ROLLING:
            pad=v.new_full((min(k-1,len(v)),),float('nan'))
            if len(v)<k:cols.extend([pad,pad,pad]);continue
            x=v.unfold(0,k,1);t=torch.arange(k,device=v.device,dtype=v.dtype);t=t-t.mean()
            for a in (x.mean(-1),x.std(-1,correction=0),(x*t).sum(-1)/t.square().sum()):cols.append(torch.cat([pad,a]))
        out.extend(cols)
    return torch.stack(out,-1)
