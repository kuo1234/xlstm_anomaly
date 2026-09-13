"""Fixed random-unlabeled B128-vs-B1 epoch canary; never affects optimization."""
import torch
from phase_f_v2_parity import compare
from phase_e2_observer import Observer as XObserver
from phase_f_lstm_observer import Observer as LObserver

def canary(model,architecture,x):
    model.eval(); Observer=XObserver if architecture=='xlstm' else LObserver
    with torch.no_grad():
        with Observer(model) as full_observer: full_output=model(x); full_features=full_observer.summary()
        pieces=[]; feature_pieces=[]; reference=[]
        for part in x.split(1):
            with Observer(model) as observer:
                pieces.append(model(part)); feature_pieces.append(observer.summary()); reference.extend(observer.checks)
        partition_output=torch.cat(pieces); partition_features=torch.cat(feature_pieces)
    full_score=(full_output-x).square().mean((1,2)); partition_score=(partition_output-x).square().mean((1,2))
    checks={
        'raw_output':compare(full_output,partition_output),
        'reconstruction_score':compare(full_score,partition_score),
        'common18':compare(full_features,partition_features),
        'full_shape_finite':dict(pass_=list(full_output.shape)==list(x.shape) and list(full_features.shape)==[len(x),18] and bool(torch.isfinite(full_output).all()) and bool(torch.isfinite(full_features).all())),
        'partition_shape_finite':dict(pass_=bool(torch.isfinite(partition_output).all()) and bool(torch.isfinite(partition_features).all())),
    }
    if architecture=='xlstm': reference_pass=all(c['hidden_close'] and c['state_close'] and c['finite'] and c['all_float32'] for c in full_observer.checks+reference)
    else: reference_pass=all(all(v if isinstance(v,bool) else v['pass_'] for v in c['checks'].values()) for c in full_observer.checks+reference)
    checks['observer_reference']=dict(pass_=reference_pass)
    passed=all(v['pass_'] for v in checks.values())
    result=dict(pass_=passed,checks=checks,batch_size=len(x),partition_batch_size=1,seed=710,labels_used=False,affects_optimization=False)
    if not passed: raise RuntimeError('F-v3 epoch canary failed: '+','.join(k for k,v in checks.items() if not v['pass_']))
    return result
