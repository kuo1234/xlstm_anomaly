# M0-E dataset fitness audit

Audit date: 2026-10-05. Scope: Issue #22 architecture/feasibility audit; no detector execution, training, benchmark-result values, or model-result CSV inspection. `CD.csv` is the permitted drift metadata exception. This assessment does not amend `reports/m0_protocol.md` or unlock its experiments.

## Decision

**REFRAME: TSB-drift is an auxiliary released-series anomaly stress set, not sufficient ground truth for a causal frozen-weight state-staleness/reset claim.** Controlled synthetic data with independently known legitimate regime boundaries and anomalies are necessary within the currently verified evidence base. Such synthetic evidence would establish only a controlled mechanism; real-world state-staleness/recovery validation remains unresolved. The prior A2 PASS establishes selection feasibility under its amended rules, not causal dataset fitness or current execution permission.

## Availability, shape, and actual composition

The [pinned StrAD README](https://github.com/magaliparrino/StrAD/blob/7078876bbd9398481a65c22b7689702ce9e0d558/README.md#tsb-drift) describes 75 selected drift series from TSB-AD-M. Current retrieval of the [pinned CD metadata](https://raw.githubusercontent.com/magaliparrino/StrAD/7078876bbd9398481a65c22b7689702ce9e0d558/results/benchmark_eval_results/CD.csv) confirms 180 rows and exactly 75 with `CD=1`; its SHA256 exactly matches the September local seal. Multi-tags are retained: continuous 45, change_point 53, periodic 8, random_walk 41; counts overlap.

**Were all 75 obtainable? Historically yes. Currently not independently re-established.** `reports/phase_a/README.md`, `downloads.json`, and the v4 inventory record acquisition and byte/numeric inspection of every candidate from the official multivariate ZIP. Its historically sealed size is 540,383,983 bytes and SHA256 is `7de86ac27f30eeb48d833bb061055670e3f3de07defd995cf2bd5db10ccc9a0d`. This ZIP is absent from this worktree. A current standard HTTP HEAD to the [official ZIP](https://www.thedatum.org/datasets/TSB-AD-M.zip) returned 403; no full GET or bulk download was attempted. A denied HEAD does not prove all legitimate download routes fail. The public link remains documented in the [pinned TSB dataset README](https://github.com/TheDatumOrg/TSB-AD/blob/6beac72e11d1155ade40870492c00d0d1cfdcaaf/Datasets/README.md). The mutable ZIP URL has no Git commit, and the historical hash does not prove identity to the StrAD authors' exact experimental snapshot.

Current recalculation **from the historical audit JSON**, not renewed raw-data inspection, gives:

| Property | Evidence and limit |
|---|---|
| Multivariate | All 75 have D=3–248; all recorded finite and binary-labeled. Dimensions were historically measured from bytes, not inferred from filenames. |
| Clean original TSB prefix | 65 pass; 10 fail (one SMD, one LTDB, eight TAO). Released cutoffs are not guaranteed native train/test splits. |
| Simulated sources | 28 rows: GHL 23 and CATSv2 5. The blanket description of all 75 as real measured series is not supported. |
| Final v4 eligibility | 37 after excluding the 28 simulations and 10 contaminated prefixes; these exclusion sets are disjoint. |
| Native identity | 15 SMD mappings historically verified by exact numeric containment; 60/75 native mappings unresolved. Filenames identify released files, not native machines/crops. |
| Prior v4 selection | 12 files, 9 released families, 9/12 unresolved native mappings. The 3 periodic files are all SMD: descriptive within-family evidence only. |
| Dependence | Four Exathlon files form one historically verified identical-feature group; at most one may be selected. Absence of another exact match does not prove independent physical sources. |

The [GHL original abstract](https://arxiv.org/abs/1612.06676v2) explicitly describes a Modelica-generated gasoil plant. The [CATS v2 creator record](https://zenodo.org/records/8338435) explicitly describes simulated system data. Both primary-source descriptions were rechecked in this audit. The counts and released-family attribution above come from the historical inventory, not a new native mapping exercise. `reports/m0_v3_source_correction.md` and `reports/m0_amendment_v4.md` retain the correction and final selection policy. The CreditCard catalog contradiction and other unresolved mappings remain unresolved.

## Label semantics and the staleness question

The only fields in current pinned `CD.csv` are `file, jsd, jsd_mean, CD, type, CD_rate`. Each row identifies a whole released series. There is no point index, annotated legitimate transition onset/end, stable new-normal interval, or independently labeled recovery boundary. `change_point` is a pattern tag, not an event timestamp. `CD_rate` must not be converted into a pointwise drift label.

The pinned README's selection method divides series into training-size batches, computes per-feature inter-batch Jensen–Shannon divergence, aggregates across dimensions, and ranks series. The [pinned implementation](https://github.com/magaliparrino/StrAD/blob/7078876bbd9398481a65c22b7689702ce9e0d558/TSB-drift/jsd_drift.py) exposes `make_batches_index`, per-feature histogram distributions, pairwise divergence matrices, and mean/max aggregation. This is distributional change evidence at a batch scale. It neither assigns benign/fault semantics nor establishes a model's state as stale. Since this implementation compares per-feature histograms, it is also not a complete detector of correlation-only changes with unchanged marginals. This last limitation follows from the inspected computation, not benchmark results.

The upstream example reads the separate `Label` column; historical raw audits verify binary anomaly labels for all 75. These permit anomaly detection metrics, conditional on those source annotations. They do **not** independently certify that each label-zero distribution change is a legitimate operating-mode transition or that anomalies never contributed to a high JSD. Deriving boundaries from model scores or resetting at retrospectively chosen JSD changes would not supply independent ground truth.

The pinned repository tree contains one released MSL example, synthetic demonstrations, drift computation scripts, and example matrix/heatmap assets under `TSB-drift/`; it is not a standalone checked-in set of all 75 raw series. Only its path inventory was inspected for the matrices/heatmaps; their output values were not read. No independently annotated real recovery boundaries were established by the inspected sources. This is a bounded evidence statement, not a claim that no original source could ever provide additional annotations.

## Metrics permitted by the available evidence

| Metric or claim | Current fitness |
|---|---|
| Point AP, AUROC, unadjusted recall/FPR | Supported by anomaly labels after a future authorized run with causal score alignment and frozen calibration; undefined class cases remain N/A. No values computed here. |
| Window metrics | Possible only with an explicit window-any-anomaly target matching the score unit; not interchangeable with endpoint point labels. |
| Overall false-alarm burden, score/reset trajectories | Descriptive auxiliary analyses; a distribution shift cannot automatically be called benign. |
| Shift-to-recovery latency; normal FPR in an exact post-shift horizon | **N/A on this release evidence**: no independently verified legitimate shift boundary or clean post-shift regime interval. |
| Drift-versus-anomaly classification | **N/A as real-data ground-truth validation** without independent frozen annotations. |
| Reset improves performance specifically by removing stale state | Not established by dataset membership or AP alone. Needs state-isolating paired interventions and known regimes; a gain may instead reflect changed history, warmup, normalization, or anomaly-state removal. |

The governing protocol specifies primary AP (not an ambiguous “PR-AUC”), separately named trapezoidal PR-AUC for reproduction, AUROC, unadjusted recall/FPR, optional fixed VUS-PR, no point adjustment, and source-family-first TSB inference. Its recovery definition uses the first of three consecutive non-overlapping 64-sample blocks meeting normal-point FPR≤0.10, with at least 32 clean endpoints per block; insufficient support is censored. Those definitions do not manufacture missing real boundaries. Numerical recovery targets or oracle boundaries never enter deployed reset decisions.

## Required evidence for a later controlled study

A future separately authorized design would need stationary controls, legitimate abrupt/gradual shifts, recurrence, and correlation changes, with evaluator-only regime/onset/end truth and independently injected anomalies, including overlap and duration/severity controls. Pair frozen-weight carry/reset trajectories on identical observations/checkpoints and a single causal input pass; hold scoring, threshold, normalization and warmup handling fixed. An oracle-boundary reset is a diagnostic upper bound, not a deployable solution. Recovery, anomaly sensitivity, and false resets must be reported together. Existing protocol safeguards remain binding, including its historical H3b gate; this audit does not run or authorize that diagnostic.

The synthetic component is necessary **for the causal question given these missing labels**, not proof that every possible real dataset is unsuitable. TSB's eligible measured subset can later test whether an effect survives heterogeneous anomaly streams, with conservative source-family grouping and provenance limits. It cannot convert a synthetic mechanism result into verified real-world benign-drift recovery. Remaining blockers are current all-series byte availability, independent legitimate transition/recovery annotations, unresolved native provenance, and an approved state-isolating experiment protocol. No performance conclusion or research GO follows from this document.

## Reproducibility record

`provenance/dataset_sources.json` records exact pinned URLs, current metadata/code hashes, historical archive evidence, current HTTP status, local audit hashes and recalculated inventory counts. Only metadata/documentation/source inspection and metadata arithmetic were performed. Historical raw-byte checks are explicitly historical; no detector or result artifact was opened. No native identity was inferred from released filename tokens.
