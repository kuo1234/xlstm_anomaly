# R0 scientific assessment

## r0-v1.2 (current): `SMD_R0_V1_2_COMPLETE`

R0 has a scientific outcome. Under the final implementation amendment r0-v1.2 (xLSTM features carried forward from
r0-v1.1; capacity-matched auditable LSTM implementation, one recurrence for training and extraction) all 18
detectors passed their gates, the 18 feature caches were sealed and pushed before any execution-stage label read,
and the unchanged probe / aggregate / sanity / report stages ran once.

| backbone | classification | mean ΔAP | positive cells | two-way interval | machine-only interval |
|---|---|---:|---:|---|---|
| xLSTM | `R0_NO_RESOLVED_INCREMENT` | +0.0416 | 5 / 9 | [−0.1035, +0.2010] | [−0.0652, +0.2178] |
| capacity-matched auditable LSTM (R0-v1.2) | `R0_NO_RESOLVED_INCREMENT` | +0.0258 | 5 / 9 | [−0.2093, +0.2361] | [−0.1289, +0.2361] |

Intervals are exploratory resampling intervals (10,000 draws, seed 901; 3 machines × 3 seeds), never calibrated
population 95 % CIs. The only permitted statement, for each backbone:

> R0 does not resolve additional real-data predictive utility of internal state beyond score/history under the
> frozen diagnostic.

**Claim ladder.** L1d (source-native real-data measurement replication over score/history, Design B) is
**NOT SUPPORTED at R0 resolution** for both backbones (L1d is supported only for a backbone classified
`R0_POSITIVE_INCREMENT`). L1a, L1c-P and P1r are unchanged; R0 neither contradicts nor rescues P1r.

**Structure of the matrices (descriptive; no post-hoc re-analysis).**

* Machine heterogeneity dominates. machine-1-4 is positive in all six cells (xLSTM +0.148 to +0.306; LSTM +0.112 to
  +0.391; machine means +0.218 / +0.236). machine-2-1 is negative in all three xLSTM cells (mean −0.065) and in two
  of three LSTM cells (mean −0.030). machine-1-8 is mixed with large negative cells (xLSTM seed 33 −0.201; LSTM seeds
  22 / 33 −0.317 / −0.181; machine means −0.028 / −0.129). With three machines, the machine-only interval cannot
  exclude zero unless every machine mean is positive.
* Validation and test blocks disagree. In several cells the H+internal234 arm had a much higher validation AP than
  the H arm but a lower test AP (e.g. machine-1-8 / LSTM / 22: validation 0.737 vs 0.105, test 0.135 vs 0.451). The
  Design-B blocks contain different anomaly segments (window-positive rows train / validation / test: machine-1-8
  968 / 523 / 516; machine-2-1 138 / 269 / 1,518; machine-1-4 211 / 468 / 797), so within-machine increments were not
  stable across blocks under this probe.
* The two backbones give the same classification and similar cell patterns. Their means (+0.042 vs +0.026) are a
  parallel measurement, not a comparison; no backbone ranking is made.

**Detector-sanity context (computed after `results.json` was committed; never used for selection).** No detector is
`DETECTOR_WEAK` (test AUROC 0.561–0.860). On machine-1-4 all six detectors have identical recall / FPR at threshold
(0.1145 / 0.0254), consistent with scores dominated by the disclosed near-constant fit channel 17 (smallest non-zero
fit std 1.69e-5; sealed zero-std-only scaler, no variance floor). The machine-1-4 positive cells are therefore
measured against an H arm built from a score dominated by one channel; R0 cannot distinguish recurrent-state utility
from compensation for that score degeneracy, and no repair is applied post hoc. On machine-1-8 the FPR at threshold
is 0.61–0.72 for all detectors (eight channels have zero fit variance), indicating a fit-to-test shift in the score.

**What this outcome is not.** It is not evidence that internal state carries no information on SMD, not a
statement about unseen machines (Design B is within-machine), not a backbone comparison, and not a statement about
drift, deployment, alarm quality or online adaptation. The auditable matched LSTM replaces native `nn.LSTM`
(mathematically equivalent recurrence; methods label "capacity-matched auditable LSTM implementation (R0-v1.2)").

The next step is the owner's review of this completed SMD R0 result. Zero-shot work, test-time adaptation and HAI R1
remain deferred until that review. ZERO_SHOT_NOT_STARTED.

## r0-v1.1 (historical record, unchanged)

**R0 still has no scientific outcome.** Under the owner-authorised amendment r0-v1.1 all nine xLSTM detectors were
trained or reused and extracted on the single vanilla/reference path, but execution stopped fail-closed at the
sealed matched-LSTM observer parity check (machine-1-8 / LSTM / seed 11) before any feature cache was sealed, any
probe was fitted or any test label was read. L1d remains **untested**; this is not `R0_NO_RESOLVED_INCREMENT`, and
no ΔAP, interval or classification may be inferred from the partial runs. Validation MSEs in the run records are
train-split training diagnostics only. P1r remains terminal and unchanged. ZERO_SHOT_NOT_STARTED.

## r0-v1 (historical record, unchanged)

**R0 has no scientific outcome.** Execution stopped fail-closed at the checkpoint parity gate of machine-2-1 /
xLSTM / seed 22 before any feature cache was sealed, any probe was fitted or any test label was read.

Under the frozen claim boundary this means:

* L1d (source-native real-data measurement replication) is **untested** — neither supported nor unsupported.
* The stop is **not** `R0_NO_RESOLVED_INCREMENT`; no ΔAP matrix, interval or classification exists for either
  backbone, and none may be inferred from the partial runs.
* Detector validation MSEs in the run records are training diagnostics on the train split; they say nothing about
  anomaly detection or about the internal-state increment.
* P1r remains terminal and unchanged (L1c-P NOT SUPPORTED at its resolution); nothing in R0 bears on it.
* No claim of xLSTM superiority, information beyond raw input, benign-drift detection, unseen-machine or cross-domain
  generality, test-time adaptation or deployment readiness is made or implied.

The next scientific step is an owner decision on a result-blind amendment (`execution.md`); until then R0 remains
blocked. ZERO_SHOT_NOT_STARTED.
