# Existing repository evidence map

## Scope and provenance

The new research branch starts at exact commit ffae1da6e37b48076e2610390c249318acfbea2e. The map below reads the committed work at that base and the associated completed research records available in the repository snapshot. It adds no result or retrospective analysis. Main's unrelated local edits were left untouched.

Classification meanings:

- **DIRECTLY_REUSABLE:** evidence directly informs the new claim or its falsification.
- **REUSABLE_AS_BASELINE:** model or protocol provides a fair comparator.
- **REUSABLE_AS_INFRASTRUCTURE:** data, provenance, auditing or execution pieces can be reused.
- **NEGATIVE_EVIDENCE:** result limits or rejects a motivating claim and must remain visible.
- **NOT_RELEVANT:** does not test this research question.

## Results and scientific evidence

| Component | Classification | What it establishes | What is reusable / boundary |
|---|---|---|---|
| G1 recurrent internal-state study | **NEGATIVE_EVIDENCE** | The internal summary added a large decodable signal over score/history in the initial synthetic H2 analysis. | Relevant only as a feature-level observation under its frozen synthetic generator and probe. It did not test persistent state, online updates, safe adaptation, or target transfer. |
| Matched-LSTM post-hoc evidence | **NEGATIVE_EVIDENCE** | Reconstructed matched-LSTM own-history increment is +0.142966; positive in 50/50 source/seed units, 5/5 seed means and 10/10 source means. It is comparable in scale to xLSTM H2 +0.142519. | xLSTM-specific internal-state superiority is unsupported. It is exploratory and not an equivalence test. It does not imply all recurrent models are equivalent. |
| Strong observable control, including post-review addendum | **NEGATIVE_EVIDENCE** | Under fixed L2 probe, residual controls leave a positive conditional internal increment; however O1 is the stronger observable-only control and increments shrink to +0.039584 xLSTM and +0.015271 LSTM. The feature arms were not temporally matched: internal234 contains causal rolling 4/8/16/32-decision summaries not present in raw O1/O2. | Treat as evidence that some information improves the probe relative to these controls, with temporal-context confounding. Do not claim internal state contains information unavailable in observations. |
| A+ temporally matched observable control | **DIRECTLY_REUSABLE** | Under the fixed linear L2 probe, matching O1r's causal temporal span to internal234 leaves mean ΔAP +0.026710 xLSTM and +0.010220 matched LSTM; all source×seed effects are positive. | Exploratory synthetic evidence: xLSTM clears the historical descriptive reference but LSTM does not. It is a residual-derived control, not raw input; it is not a causal intervention or information-theoretic result, and it does not test online state. |
| A+S solver / convergence audit | **DIRECTLY_REUSABLE** | A+ interpretation survives a converged-refit and fixed C-grid sensitivity audit: xLSTM remains positive above the old +0.02 descriptive reference; matched LSTM remains positive below it. | This is a post-hoc robustness qualification, not a new experiment or confirmatory gate. It supports retaining A+ with grid/solver caveats; it does not establish a persistent detector. |
| Nonlinear observable control | **NEGATIVE_EVIDENCE** | A nonlinear tree comparator after O1r leaves +0.01516504 xLSTM / +0.01125203 LSTM, both below the historical +0.02 descriptive reference; effect is attenuated, not zero. | Do not frame linear residual controls as proving observable insufficiency. This is synthetic and exploratory, and it does not prove information unavailable in raw input. |
| P1r input-derived control | **NEGATIVE_EVIDENCE** | Increment beyond the bounded temporally matched input-derived P1r summary is unresolved: xLSTM −0.00023259 [−0.00076128,+0.00029149]; matched LSTM +0.00028937 [−0.00041494,+0.00095887]. | Internal234 is a deterministic function of causal input; this is not information-theoretic. It closes one frozen synthetic control stage, not all observables. |
| Real SMD R0 v1/v1.1 stops | **REUSABLE_AS_INFRASTRUCTURE** | Early versions stopped at parity/checkpoint gates before labels/probe fitting; they do not have a scientific outcome. | Preserve the exact distinction between execution failure and a negative result; reuse fail-closed audit patterns only. |
| Real SMD R0 v1.2 / final | **NEGATIVE_EVIDENCE** | Both xLSTM and capacity-matched auditable LSTM are R0_NO_RESOLVED_INCREMENT. xLSTM mean ΔAP +0.0416, 5/9 positive, exploratory two-way interval [−0.1035,+0.2010]; LSTM +0.0258, 5/9, [−0.2093,+0.2361]. | This is within-machine blocked Design B, not held-out machine transfer. It does not test persistent state, forecasting, online update or benign drift. Do not erase, repair post hoc or present as a backbone comparison. |
| R0 machine heterogeneity / preprocessing caveat | **NEGATIVE_EVIDENCE** | Machine effects vary. machine-1-4 positive cells are confounded by a near-constant channel 17 (fit std 1.69e-5, no variance floor; all six detectors share same recall/FPR at threshold). machine-1-8 and machine-2-1 are mixed/negative. | New studies need per-machine results and channel/scaler degeneracy audits. Do not explain the positive cell as recurrent benefit. |
| internal234 comparability audit | **DIRECTLY_REUSABLE** | Across independent model instances, 4/18 base features (52/234 expanded columns) have polarity ambiguity; all 18 have model-specific operating points. | Do not transfer raw internal-feature calibrations across machine-specific model instances. Prefer raw input/model outputs for transfer comparisons; if internal states are tested later, fit target calibration only on permitted target data. |
| R0 detector sanity and data audit | **REUSABLE_AS_INFRASTRUCTURE** | Exposes score scale, FPR and split heterogeneity, and preserves observation/label separation. | Reuse dataset manifest, causal split logic and per-machine audit design; revisit no scaling decision post hoc. |
| Real-data feasibility audit / acquisition review | **REUSABLE_AS_INFRASTRUCTURE** | Audited SMD feasibility, dataset access/provenance, dimensionality, split and channel compatibility before detector work. | Reuse the provenance checklist and the warning that same-D does not guarantee aligned channel semantics; this does not establish benign-regime labels. |
| R0 xLSTM and auditable matched-LSTM implementations | **REUSABLE_AS_BASELINE** | Capacity-matched and parity-audited recurrent detector baseline exists. Each W64 call starts fresh state. | Candidate baseline for windowed architecture comparison, subject to separate forecasting head and objective. It is not yet a persistent-state implementation. |
| R0 execution and provenance infrastructure | **REUSABLE_AS_INFRASTRUCTURE** | Sealed data manifests, hashes, fail-closed preflights and execution logs exist. | Useful for a later authorized study; no training or runner was invoked for this audit. |
| SMD dataset/provenance utilities | **REUSABLE_AS_INFRASTRUCTURE** | Source and machine identity, splits, features and labels have auditable records. | Useful for same-D held-machine transfer only after checking target sample semantics, raw timestamps and channel alignment. Existing R0 windows are not a transfer dataset protocol. |
| G1 execution infrastructure | **REUSABLE_AS_INFRASTRUCTURE** | Frozen synthetic feature extraction, source-disjoint splits and result audit tooling exist. | Could inform study governance, but the G1 synthetic generator is not ground truth for benign regime semantics. |
| xLSTMAD reconstruction code / R0 implementation | **REUSABLE_AS_BASELINE** | Existing encoder-decoder reconstruction detector and windowed extraction provide a starting comparator. | Reconstruction alone is not evidence for forecasting or persistent state; use unchanged as an explicitly named baseline if M1 is later authorized. |
| D0 / zero-shot work | **NOT_RELEVANT** | No D0 or zero-shot experiment is part of this audit. | Do not treat source-to-target warm-start with N>0 confirmed-normal data as zero-shot. |

## What can be carried forward

Directly useful evidence is chiefly negative and methodological: xLSTM is not established as uniquely valuable; rich residual/input-derived observables sharply attenuate the initial signal; the SMD R0 estimate is unresolved and heterogeneous; and internal feature semantics are not fully portable across independently trained detectors.

Useful assets include the auditable LSTM and xLSTM baselines, common SMD schema and provenance checks, source-level pairing, causal window/split code, and fail-closed run records. The raw checkpoint/training setup is not itself a transfer result. Any new use of these tools must preserve the difference between fresh per-window recurrent calls and a genuinely persistent stream state.

## Explicit non-reinterpretation

- G1's synthetic H2 result is not erased by the matched-LSTM result; the latter changes its architecture-specific interpretation.
- A+ residual-controlled effects are not claimed to survive every observable control.
- P1r is not an information-theoretic proof that hidden state contains no useful representation; it is a bounded decoder/control result.
- R0's positive machine-1-4 cells are not evidence of useful xLSTM state due to the disclosed scaler degeneracy.
- R0's negative/unresolved outcome does not test online persistent state or adaptive normality.
- No G1, P1r, A+, A+S or R0 history was modified.
