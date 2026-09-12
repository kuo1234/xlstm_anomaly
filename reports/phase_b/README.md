# Phase B CPU scaffolding and software tests

Scope: new evaluator/generator software, not official CANDI reproduction, not a detector experiment, and not evidence for any H1–H5 GO. Authorized independently of A2 native-provenance completion after valid A1 seal and the v3 rule commit/push. No CANDI/xLSTM/LSTM training or GPU pilot occurred; no model-result file was inspected.

## Implementation

- `m0/causal.py`: immutable decision records; window=64/stride=1 causal stream; score and emit before selection/update/normalizer update; a fresh adapter factory per run; fit-only fixed scaler and 95th-percentile calibration utility; distinct window-any/endpoint evaluator labels; candidate/committed/pending exposure denominators, unique-window and raw-point coverage, candidate-to-commit latency. Algorithm callbacks receive only x/time/state/score, never labels or event metadata.
- `m0/synthetic.py` and `configs/synthetic_v1.json`: D=8 temporally/cross-channel dependent VAR, five scenarios, clean initial fit/calibration, fixed source-disjoint seed families, spikes/collective/dependency events and equal-type-mixture slots, severity/duration controls, separate persistent-fault stress interval, paired legitimate excursions, stationary-no-anomaly and identical-observation/opposite-label controls. Truth and observations save to separate files; no overwrite. Event/regime/drift/overlap metadata stays evaluator-side.
- `m0/correlation.py`: analytic covariance construction plus independent SciPy discrete-Lyapunov solve. Tests were committed before any generated observations were inspected. Both directions of the 256-step transition and five fixed channel permutations are verified without sample-based acceptance.
- `m0/metrics.py`: AP, explicitly distinct trapezoidal PR-AUC, AUROC with tied scores grouped, fixed-threshold FPR/recall, prevalence and undefined-case denominators; endpoint post-shift normal FPR and censored recovery. Recovery reports both the first qualifying block start and the later three-block confirmation time; neither uses retrospective alarm changes.

## Test results

`rtk python3 scripts/run_phase_b_tests.py` records 25 passing tests: 18 Phase B tests (2 correlation, 7 causal, 5 generator, 4 metrics), 2 revised-manifest tests and 5 original Phase A regression tests. Exact outcome, runtime and package versions are in `test_results.json`; individual names/results in `tests.log`.

Verified invariants include symmetry ≤1e-12, positive-definite covariance/innovation matrices, stable A, Lyapunov residual ≤1e-10, independently solved stationary mean/variance equality ≤1e-10, off-diagonal correlation difference ≥0.2, and all 256 transition diagonal errors ≤1e-10. Fixed-seed permutation results are recorded, not selected. Generator tests check every scenario on seed 1000, exact regeneration, finite D=8 outputs, clean prefix, recurring boundary, all three severities/durations, counterfactual event pairing, no injected-anomaly feedback into latent state, source-fold disjointness and saved truth separation. This is not a full seed sweep or empirical sample-moment study.

The non-identifiability test verifies paired equal observations/opposite semantic labels and chance AP/AUROC for a fixed arithmetic observable. Causal tests use an arithmetic state-mutation spy, not a trained or benchmark detector. Permuting evaluator labels cannot change any emitted score, selected ID, commit or timeline; changing future observations cannot change earlier outputs. Metrics tests cover ties, no positives/no negatives, empty inputs and recovery censoring.

## Deliberate limitations / next gate

This is scaffolding, not a production detector or reproduction claim. No actual model/optimizer/RNG adapter parity is established; factories must clone pretrained state and reset RNG in later adapter tests. API separation protects against accidental leakage, not malicious arbitrary Python code. Scaler/calibration utilities require the caller to supply the frozen fit/calibration intervals; there is no test-threshold search. Post-shift helper expects endpoint scores, not scalar reconstruction-window scores. VUS-PR, family-clustered resampling implementations, probes and real-data loaders/adapters are not implemented or reported as tested. Their inference rules remain frozen in v3.

Generator perturbations express severity in initial-normal marginal SD units. Dependency anomalies can change marginal variance, and are not claimed to be correlation-only. Only the latent correlation-shift scenario has analytically equal marginal moments. Short legitimate perturbations and anomalies intentionally have exactly paired observable counterexamples, limiting any duration-based identifiability claim. Persistent-fault events are stress-only, excluded from equal-type-mixture summaries.

Original `reports/phase_a/` remains byte-identical to ad97c4a. A1 passed its seal; A2 requires a further selection-rule review after GHL's synthetic origin was established. Do not begin Phase C or GPU experiments. Return this review first.
