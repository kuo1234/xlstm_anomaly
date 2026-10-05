"""Stationary Gaussian VAR(1) mechanisms; metadata never enters model API."""
import numpy as np
from common import load_config, array_hash

MECHANISMS = ('mean', 'dynamics', 'correlation')
SPLITS = ('train', 'validation', 'calibration', 'test', 'anomaly')


def process(mechanism, group, regime):
    cfg = load_config()
    assert mechanism in MECHANISMS and group in cfg['groups'] and regime in ('A','B')
    d, g = cfg['dimension'], cfg['generator']
    rng = np.random.default_rng(g['group_seed_base'] + group)
    order = rng.permutation(d)
    p = np.eye(d)[np.roll(np.arange(d),1)]
    p = p[order][:,order]
    signs = rng.choice([-1.0,1.0],d)
    p = signs[:,None] * p * signs[None,:]
    rho = g['group_rho_b_dynamics'][group] if mechanism=='dynamics' and regime=='B' else g['group_rho'][group]
    a = rho*p
    corr = g['corr_b'] if mechanism=='correlation' and regime=='B' else g['corr_a']
    # Signed equicorrelation is invariant to the signed cycle matrix P.
    covariance = (1-corr)*np.eye(d) + corr*np.outer(signs,signs)
    mean = np.zeros(d)
    if mechanism=='mean':
        mean = signs*g['group_mean_magnitude'][group]*(1 if regime=='B' else -1)
    q = covariance - a@covariance@a.T
    return {'a': a, 'mean': mean, 'sigma': covariance, 'q': q, 'group': group, 'mechanism': mechanism, 'regime': regime}


def invariants(spec):
    a, s, q = spec['a'], spec['sigma'], spec['q']
    return {'spectral_radius': float(max(abs(np.linalg.eigvals(a)))), 'min_sigma_eigenvalue': float(np.linalg.eigvalsh(s).min()), 'min_q_eigenvalue': float(np.linalg.eigvalsh(q).min()), 'lyapunov_max_abs': float(abs(s-a@s@a.T-q).max()), 'symmetry_max_abs': float(max(abs(s-s.T).max(),abs(q-q.T).max())), 'diagonal_variance_max_deviation': float(abs(np.diag(s)-1).max())}


def process_seed(mechanism, group, split, regime, realization):
    cfg = load_config()
    # Unique arithmetic addresses in disjoint split blocks; no outcome-dependent sampling.
    base = cfg['generator']['split_seed_base'][split]
    assert 0 <= realization < 100
    return base + MECHANISMS.index(mechanism)*2000 + group*300 + (100 if regime=='B' else 0) + realization


def stationary(mechanism, group, split, regime, realization, length):
    spec = process(mechanism,group,regime)
    seed = process_seed(mechanism,group,split,regime,realization)
    rng = np.random.default_rng(seed)
    state = rng.multivariate_normal(spec['mean'],spec['sigma'])
    burn = load_config()['generator']['burn_in']
    innovations = rng.multivariate_normal(np.zeros(len(state)),spec['q'],size=burn+length)
    values = np.empty((length,len(state)),dtype=np.float64)
    for i, noise in enumerate(innovations):
        state = spec['mean'] + spec['a']@(state-spec['mean']) + noise
        if i>=burn:
            values[i-burn]=state
    return values.astype(np.float32)


def sequences(mechanism,group,split,count,length):
    return np.stack([stationary(mechanism,group,split,regime,i,length) for regime in ('A','B') for i in range(count)])


def histories(mechanism,group):
    cfg=load_config()['data']; n=cfg['test_replicates']; p=cfg['prefix_length']; s=cfg['suffix_length']
    # Both paired prefixes are independent of their exact common suffix.
    # Equal splice discontinuities avoid privileged B-prefix/suffix correlation.
    a_prefix = np.stack([stationary(mechanism,group,'test','A',i,p) for i in range(n)])
    b_prefix = np.stack([stationary(mechanism,group,'test','B',i,p) for i in range(n)])
    a_suffix = np.stack([stationary(mechanism,group,'test','A',i+n,s) for i in range(n)])
    b_suffix = np.stack([stationary(mechanism,group,'test','B',i+n,s) for i in range(n)])
    physical_a = np.stack([stationary(mechanism,group,'test','A',i+2*n,p+s) for i in range(n)])
    physical_b = np.stack([stationary(mechanism,group,'test','B',i+2*n,p+s) for i in range(n)])
    return {'a_prefix': a_prefix, 'b_prefix': b_prefix, 'a_suffix': a_suffix, 'b_suffix': b_suffix,
            'physical_a': physical_a, 'physical_b': physical_b,
            'common_b_hash': array_hash(b_suffix), 'common_a_hash': array_hash(a_suffix)}


def contaminated_suffix(clean,mechanism,group,kind,onset,scale):
    cfg=load_config(); spec=next(x for x in cfg['anomalies']['types'] if x['name']==kind)
    length=spec['duration']; altered=clean.copy(); labels=np.zeros(clean.shape[:2],dtype=np.int64); events=[]
    for r in range(clean.shape[0]):
        rng=np.random.default_rng(process_seed(mechanism,group,'anomaly','B',r))
        channels=np.sort(rng.choice(cfg['dimension'],cfg['anomalies']['affected_channels'],replace=False))
        direction=rng.choice([-1.,1.],size=len(channels))
        delta=cfg['anomalies']['amplitude_train_std']*scale[channels]*direction
        altered[r,onset:onset+length,channels] += delta[:,None]
        labels[r,onset:onset+length]=1
        events.append({'replicate':r,'onset':onset,'duration':length,'channels':channels.tolist(),'delta':delta.tolist()})
    return altered,labels,events
