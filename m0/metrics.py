"""Unadjusted evaluator metrics; AP is not trapezoidal PR-AUC."""
import numpy as np


def metrics(labels,scores,threshold):
    y, s = np.asarray(labels),np.asarray(scores,dtype=float)
    if y.ndim!=1 or s.shape!=y.shape or not np.isin(y,[0,1]).all() or not np.isfinite(s).all() or not np.isfinite(threshold):
        raise ValueError('Invalid labels/scores/fixed threshold')
    n, p = len(y),int(y.sum())
    negative = n-p
    alarm = s>threshold
    result = dict(n=n,positives=p,negatives=negative,prevalence=p/n if n else None,
                  recall=float(y[alarm].sum()/p) if p else None,
                  fpr=float((1-y[alarm]).sum()/negative) if negative else None,
                  ap=None,pr_auc_trapezoidal=None,auroc=None)
    if not n:
        return result
    order = np.argsort(-s,kind='stable')
    y,s = y[order],s[order]
    ends = np.r_[np.flatnonzero(s[1:]!=s[:-1]),n-1]
    tp = np.cumsum(y)[ends]
    fp = ends+1-tp
    if p:
        precision = tp/(ends+1)
        recall = tp/p
        result['ap'] = float(np.sum(np.diff(np.r_[0,recall])*precision))
        result['pr_auc_trapezoidal'] = float(np.trapezoid(np.r_[1,precision],np.r_[0,recall])) if hasattr(np,'trapezoid') else float(np.trapz(np.r_[1,precision],np.r_[0,recall]))
    if p and negative:
        result['auroc'] = float(np.trapz(np.r_[0,tp/p],np.r_[0,fp/negative]))
    return result


def post_shift(decisions,labels,threshold,onset):
    """Endpoint FPR only; missing boundaries N/A. Recovery measured at confirmation."""
    if onset is None:
        return dict(fpr=None,normal_n=0,recovery_latency=None,censored=True)
    y = np.asarray(labels)
    scores = {d.time:d.score for d in decisions}
    if y.ndim!=1 or not np.isin(y,[0,1]).all() or not 0<=onset<len(y):
        raise ValueError('Invalid shift audit labels/onset')
    normal = [t for t in range(onset,min(onset+256,len(y))) if not y[t] and t in scores]
    fpr = sum(scores[t]>threshold for t in normal)/len(normal) if normal else None
    streak = 0
    for left in range(onset,len(y)-63,64):
        times = [t for t in range(left,left+64) if not y[t] and t in scores]
        good = len(times)>=32 and sum(scores[t]>threshold for t in times)/len(times)<=.1
        streak = streak+1 if good else 0
        if streak==3:
            return dict(fpr=fpr,normal_n=len(normal),recovery_latency=left+63-onset,
                        recovery_start_latency=left-128-onset,censored=False)
    return dict(fpr=fpr,normal_n=len(normal),recovery_latency=None,censored=True)
