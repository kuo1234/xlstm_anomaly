"""Frozen source-cluster statistics; no pooling windows as independent units."""
import itertools
import numpy as np


def paired_summary(delta):
    d=np.asarray(delta,dtype=float)
    assert d.shape==(10,5,4) and np.isfinite(d).all()
    rng=np.random.default_rng(901)
    source_indices=rng.integers(0,10,size=(10000,10))
    seed_indices=rng.integers(0,5,size=(10000,10,5))
    draws=d[source_indices[:,:,None],seed_indices,:].mean(axis=(1,2,3))
    means=d.mean(axis=(1,2))
    signs=np.array(list(itertools.product([-1,1],repeat=10)))
    null=(signs*means[None,:]).mean(axis=1)
    observed=float(d.mean())
    p=float(np.mean(np.abs(null)>=abs(observed)-1e-15))
    lo,hi=np.quantile(draws,[.025,.975])
    return dict(mean=observed,ci95=[float(lo),float(hi)],p_two_sided=p,
        detector_seed_means=d.mean(axis=(0,2)).tolist(),scenario_means=d.mean(axis=(0,1)).tolist(),
        positive_detector_seeds=int((d.mean(axis=(0,2))>0).sum()),
        positive_scenarios=int((d.mean(axis=(0,1))>0).sum()))


def holm(pvalues):
    p=np.asarray(pvalues,dtype=float); order=np.argsort(p,kind='stable')
    adjusted=np.minimum(1,np.maximum.accumulate(p[order]*(len(p)-np.arange(len(p)))))
    out=np.empty_like(p); out[order]=adjusted
    return out.tolist()
