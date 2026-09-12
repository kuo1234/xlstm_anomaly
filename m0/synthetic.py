"""D=8 causal latent VAR with evaluator-only semantic metadata."""
import json
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from .correlation import regimes, verify

CONFIG = json.loads((Path(__file__).resolve().parents[1]/'configs/synthetic_v1.json').read_text())


@dataclass(frozen=True)
class SyntheticStream:
    observations: np.ndarray
    labels: np.ndarray
    regime: np.ndarray
    drift_active: np.ndarray
    event_ids: np.ndarray
    events: tuple
    source_seed: int
    fold: str
    test_start: int
    scenario: str
    condition: str
    semantic: str


def generate(seed, scenario, condition='mixture', semantic='anomaly'):
    if scenario not in CONFIG['scenarios'] or condition not in CONFIG['conditions']:
        raise ValueError('Unknown preregistered scenario/condition')
    if semantic not in ('anomaly','legitimate'):
        raise ValueError('Unknown semantic control')
    folds = [f for f in ('train','validation','test') if seed in CONFIG[f+'_seeds']]
    if len(folds)!=1:
        raise ValueError('Seed outside disjoint registered source folds')
    verify(seed)  # deterministic guard; never reject seeds using sample moments
    a, covariances, _ = regimes(seed)
    rng = np.random.default_rng(seed)
    n = CONFIG['fit']+CONFIG['calibration']+CONFIG['test']
    start = CONFIG['fit']+CONFIG['calibration']
    onset, end = start+4096, start+8192
    weight = np.zeros(n)
    drift = np.zeros(n,dtype=bool)
    if scenario in ('abrupt','correlation'):
        weight[onset:] = 1
        drift[onset:onset+256] = True
    elif scenario=='gradual':
        weight[onset:end] = np.arange(1,end-onset+1)/(end-onset)
        weight[end:] = 1
        drift[onset:end] = True
    elif scenario=='recurring':
        weight[onset:end] = 1
        drift[onset:onset+256] = drift[end:end+256] = True
    regime = np.where(weight==0,0,np.where(weight==1,1,2)).astype(np.int8)
    state = rng.multivariate_normal(np.zeros(8),covariances[0])
    initial_chol = np.linalg.cholesky(covariances[0]-a@covariances[0]@a.T)
    for _ in range(CONFIG['burn_in']):
        state = a@state+initial_chol@rng.standard_normal(8)
    x = np.empty((n,8))
    # Pre-drawn innovations ensure counterfactual observational pairing.
    innovation = rng.standard_normal((n,8))
    cholesky = {0.:initial_chol}
    for t,w in enumerate(weight):
        if scenario=='correlation':
            covariance = (1-w)*covariances[0]+w*covariances[1]
            mean = np.zeros(8)
        else:
            covariance = (1+.5*w)**2*covariances[0]
            mean = np.full(8,w)
        if float(w) not in cholesky:
            cholesky[float(w)] = np.linalg.cholesky(covariance-a@covariance@a.T)
        state = a@state+(np.eye(8)-a)@mean+cholesky[float(w)]@innovation[t]
        x[t] = state
    clean = x.copy()
    labels = np.zeros(n,dtype=np.int8)
    event_ids = np.full(n,-1,dtype=np.int32)
    events = []
    kinds = ('spike','collective','dependency')
    for i in range(CONFIG['event_count']):
        kind = kinds[i%3]
        if condition=='none' or condition not in ('mixture',kind):
            continue
        severity = 1+(i//3)%3
        duration = 1 if kind=='spike' else CONFIG['durations'][i//9]
        left = start+CONFIG['event_first_onset']+CONFIG['event_spacing']*i
        right = left+duration
        channel = i%8
        if kind=='dependency':
            # Independent per-event RNG: changing condition cannot change another event.
            noise = np.random.default_rng(np.random.SeedSequence([seed,i,812])).standard_normal(duration)
            x[left:right,channel] += severity*(noise-clean[left:right,channel])/np.sqrt(2)
        else:
            x[left:right,channel] += severity
        labels[left:right] = int(semantic=='anomaly')
        event_ids[left:right] = i
        if semantic=='legitimate':
            drift[left:right] = True
        events.append(dict(id=i,start=left,end=right,type=kind,severity=severity,
                           duration=duration,channel=channel,semantic=semantic,stress_only=False))
    if condition!='none':
        left = start+CONFIG['persistent_fault_onset']
        right = left+CONFIG['persistent_fault_duration']
        x[left:right,0] += CONFIG['persistent_fault_severity']
        labels[left:right] = int(semantic=='anomaly')
        event_ids[left:right] = 27
        if semantic=='legitimate':
            drift[left:right] = True
        events.append(dict(id=27,start=left,end=right,type='persistent_fault',severity=2,
                           duration=1024,channel=0,semantic=semantic,stress_only=True))
    for array in (x,labels,regime,drift,event_ids):
        array.flags.writeable = False
    return SyntheticStream(x,labels,regime,drift,event_ids,tuple(events),seed,folds[0],start,
                           scenario,condition,semantic)


def opposite_label_control(seed=1000):
    """Same observations and event IDs, opposite semantic truth at event intervals."""
    return (generate(seed,'stationary','mixture','anomaly'),
            generate(seed,'stationary','mixture','legitimate'))


def save_stream(stream, directory):
    """Separate observations from evaluator truth; refuse accidental overwrites."""
    target = Path(directory)
    target.mkdir(parents=True,exist_ok=False)
    np.save(target/'observations.npy',stream.observations,allow_pickle=False)
    np.savez(target/'evaluator_truth.npz',labels=stream.labels,regime=stream.regime,
             drift_active=stream.drift_active,event_ids=stream.event_ids,
             overlap=stream.drift_active & stream.labels.astype(bool))
    (target/'evaluator_metadata.json').write_text(json.dumps(dict(
        source_seed=stream.source_seed,fold=stream.fold,test_start=stream.test_start,
        scenario=stream.scenario,condition=stream.condition,semantic=stream.semantic,
        events=stream.events,config=CONFIG),indent=2)+'\n')


def window_strata(stream, window=64):
    """Evaluator-only labels: mixed is separate; never passed into an algorithm."""
    result = []
    for t in range(max(stream.test_start,window-1),len(stream.labels)):
        anomaly = bool(stream.labels[t-window+1:t+1].any())
        drift = bool(stream.drift_active[t-window+1:t+1].any())
        result.append('mixed' if anomaly and drift else 'anomaly' if anomaly else 'drift' if drift else
                      'stable_new_normal' if stream.regime[t] else 'stationary_normal')
    return tuple(result)
