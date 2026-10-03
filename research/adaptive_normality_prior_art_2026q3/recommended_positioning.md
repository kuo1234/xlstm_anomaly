# Recommended positioning

## Recommended research question

Under an explicitly stated operating assumption that some distribution shifts are benign and that external context may be unavailable or delayed, does separating confirmed recurrent normal states from quarantined candidate states improve the tradeoff between false promotion of persistent anomalies and delayed adaptation to recurring benign regimes, compared with score-gated TTA, uncertainty-window updates, and pattern/model-pool methods?

This question is narrower and falsifiable. It does not claim that the model can infer semantic normality from the time series alone.

## What could be a contribution

The contribution should be the operational specification and evidence for a lifecycle, if the implementation actually has these properties:

1. A confirmed state is immutable to candidate observations until an explicit promotion event.
2. Uncertain observations update only a distinct candidate state or evidence accumulator.
3. Promotion uses named criteria, such as dwell time, evidence accumulation, repeated coherent recurrence, and a contamination budget.
4. A promoted regime is versioned and does not erase the previous confirmed regimes.
5. A future observation can match and reactivate a prior regime under a declared similarity rule.
6. Failure to distinguish fault from benign shift leads to a reversible defer/alert decision rather than an unqualified normal label.
7. The lifecycle's costs are measured: false promotion, contamination, delay, false alarms under benign shift, recovery time, memory growth and forgetting.

These are design targets for a future method, not findings that the current detector implements them.

## Novelty sentence to use provisionally

“We study an explicit quarantine-and-promotion lifecycle for persistent recurrent normal-state regimes in unsupervised time-series anomaly detection, and quantify its contamination, adaptation-delay and regime-recovery tradeoffs against gated TTA, uncertainty-window updates, and recurring-pattern/model-pool baselines.”

Use this only if the method and experiments support every part. Avoid “first,” “safe,” “guarantees,” “anomaly-proof,” and “xLSTM uniquely enables” absent a much stronger survey and evidence.

## Required design precision before implementation

- Define the state transition diagram: confirmed, candidate, promoted, inactive, rejected, and any rollback states.
- Define what is written at each step: observation, representation, recurrent hidden/cell state, parameters, prototype, centroid, or optimizer state.
- State which updates are allowed while anomaly confidence is high, low, or unknown.
- Give exact promotion thresholds and how thresholds are selected without target labels.
- Specify candidate expiration, regime capacity, eviction and recurrence matching.
- State how the system behaves when benign drift and persistent anomaly are observationally indistinguishable.
- Separate detector score adaptation from representation-state adaptation in the ablations.

## Evidence needed before a paper claim

1. A literature recheck of AnDri, METER, CANDI, M2N2, ARCUS, MemStream, MemTTA, the smart-building method, and the unresolved SCALE lead.
2. Strong matched baselines with comparable history access, capacity, update frequency, and target-label access.
3. Synthetic or controlled streams where benign recurring shifts and persistent anomalies can be varied independently, followed by approved real-data evaluation under the M0 protocol.
4. Ablations removing quarantine, dwell/evidence criteria, state protection, recurrence matching, and rollback.
5. Metrics for false promotion and memory contamination, not only pointwise F1/AUROC; include adaptation delay, post-shift false alarms, old-regime recovery, and memory/compute cost.
6. An identifiability statement: what contextual signal or assumption permits a benign/anomalous decision, and what the detector does when it is unavailable.

## Positioning against alternatives

Treat xLSTM as one state encoder. Include an LSTM/GRU or compact recurrent baseline and a non-recurrent fixed-history/prototype baseline. If xLSTM does not materially improve the lifecycle tradeoff at matched capacity, the contribution should be described as architecture-agnostic.

The intended contrast with AnDri should be testable: a recurrent state is not inherently better than a clustered pattern. It may be useful as a compact task-trained temporal representation, but this needs a matched-history experiment. The intended contrast with METER should identify whether candidate state separation and reversible regime promotion help beyond uncertainty accumulation followed by a window update.

## Gate

Proceed only to design/specification work after the literature gap and evaluation plan are reviewed. This prior-art report grants no permission to train, launch GPU work, inspect labels, or bypass reports/m0_protocol.md.
