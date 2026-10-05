import numpy as np
def quantile(groups,multiplicity,arm,q=.995):
    values=np.concatenate(groups)
    if arm=='trace_balanced':w=np.concatenate([np.full(len(g),1/len(g)) for g in groups])
    elif arm=='identity_deduplicated_pooled':w=np.ones(len(values))
    elif arm=='row_pooled':w=np.concatenate([np.full(len(g),m) for g,m in zip(groups,multiplicity)])
    else:raise ValueError(arm)
    order=np.argsort(values,kind='stable');cdf=np.cumsum(w[order])/sum(w);cdf[-1]=1
    return float(values[order][np.searchsorted(cdf,q,side='left')])
