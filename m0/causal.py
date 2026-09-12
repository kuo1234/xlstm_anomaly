"""Labels never enter the algorithm API; no concrete detector is supplied."""
from dataclasses import dataclass
import numpy as np


def frozen_copy(x):
    # Immutable bytes backing prevents writeable=True from exposing upstream data.
    a = np.asarray(x,dtype=np.float64)
    return np.frombuffer(a.tobytes(),dtype=np.float64).reshape(a.shape)


@dataclass(frozen=True)
class Decision:
    time: int
    score: float


@dataclass(frozen=True)
class Trace:
    decisions: tuple
    candidates: tuple
    committed: tuple
    timeline: tuple


@dataclass(frozen=True)
class FixedScaler:
    mean: np.ndarray
    scale: np.ndarray

    @classmethod
    def fit(cls, fit_observations):
        x = np.asarray(fit_observations,dtype=float)
        if x.ndim!=2 or not len(x) or not np.isfinite(x).all():
            raise ValueError('Invalid fit observations')
        return cls(frozen_copy(x.mean(0)),frozen_copy(np.where(x.std(0)>0,x.std(0),1)))

    def transform(self,x):
        return (np.asarray(x)-self.mean)/self.scale


def calibration_threshold(calibration_scores):
    scores = np.asarray(calibration_scores,dtype=float)
    if scores.ndim!=1 or not len(scores) or not np.isfinite(scores).all():
        raise ValueError('Invalid calibration scores')
    return float(np.quantile(scores,.95,method='linear'))


def run_stream(observations, algorithm_factory, test_start, window=64):
    """Fresh algorithm per run. score->emit->select->update->normalizer update.

    Factory owns any prefit checkpoint clone/RNG reset. This generic scaffold
    cannot certify future framework/model/optimizer reset without adapter tests.
    update() returns committed candidate IDs, never labels. Delayed policies and
    CANDI queues are not implemented here.
    """
    x = np.asarray(observations,dtype=float)
    if x.ndim!=2 or not np.isfinite(x).all() or window<1 or not 0<=test_start<len(x):
        raise ValueError('Invalid stream')
    algorithm = algorithm_factory()
    decisions, candidates, committed, timeline = [],[],[],[]
    for t in range(max(test_start,window-1),len(x)):
        current = frozen_copy(x[t-window+1:t+1])
        score = float(algorithm.score(current,t))
        if not np.isfinite(score):
            raise ValueError('Nonfinite score')
        timeline.append(('score',t))
        decision = Decision(t,score)
        decisions.append(decision)
        timeline.append(('emit',t))
        selected = bool(algorithm.select(current,t,score))
        timeline.append(('select',t))
        if selected:
            candidates.append(t)
        ids = tuple(algorithm.update(current,t,selected))
        if any(i not in candidates or i>t for i in ids):
            raise ValueError('Commit without a causally available candidate')
        committed.extend((int(i),t) for i in ids)
        timeline.append(('update',t))
        algorithm.observe_normalizer(current[-1],t)
        timeline.append(('normalizer',t))
    return Trace(tuple(decisions),tuple(candidates),tuple(committed),tuple(timeline))


def aligned_labels(trace, labels, window=64, semantics='window_any'):
    """Evaluator-only; reconstruction-window and endpoint labels stay distinct."""
    y = np.asarray(labels)
    if y.ndim!=1 or not np.isin(y,[0,1]).all() or semantics not in ('window_any','endpoint'):
        raise ValueError('Invalid labels/semantics')
    if any(d.time>=len(y) or d.time<window-1 for d in trace.decisions):
        raise ValueError('Label alignment out of bounds')
    return np.array([int(y[d.time-window+1:d.time+1].any()) if semantics=='window_any' else int(y[d.time])
                     for d in trace.decisions])


def admission_audit(trace,labels,window=64):
    """Separate denominators. Repeated commits are exposures, not unique windows."""
    y = np.asarray(labels)
    if y.ndim!=1 or not np.isin(y,[0,1]).all():
        raise ValueError('Invalid evaluator labels')
    def summary(ids):
        if any(i<window-1 or i>=len(y) for i in ids):
            raise ValueError('Invalid candidate ID')
        admitted = sum(bool(y[i-window+1:i+1].any()) for i in ids)
        coverage = {t for i in ids for t in range(i-window+1,i+1)}
        return dict(exposures=len(ids),unique_windows=len(set(ids)),raw_point_coverage=len(coverage),
                    anomaly_exposures=admitted,rate=admitted/len(ids) if ids else None)
    ids = [i for i,_ in trace.committed]
    return dict(candidate=summary(trace.candidates),committed=summary(ids),
                pending=summary([i for i in trace.candidates if i not in ids]),
                candidate_to_commit=[t-i for i,t in trace.committed])
