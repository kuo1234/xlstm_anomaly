# Safe normality adaptation for non-stationary multivariate TSAD

This repository is the research code and evidence ledger for a deliberately
adversarial study of safe normality adaptation in non-stationary multivariate
time-series anomaly detection (TSAD).

The central problem is an unlabeled stream in which a distribution shift may be
either a legitimate persistent new normal or a transient anomaly. Immediate
adaptation can absorb anomalies; never adapting can leave a detector with a
large post-shift false-positive rate. The project therefore asks which
observable evidence can support a causal adaptation decision, and how much
latency or contamination that evidence costs.

The working xLSTM hypothesis is intentionally falsifiable:

> xLSTM gate and recurrent-memory dynamics may contain additional historical
> information for distinguishing persistent drift from transient anomalies.

This is not a presumption that xLSTM is a better anomaly detector. The primary
confirmatory experiment compares a frozen, matched xLSTM/LSTM feature schema;
negative results are valid outcomes.

## Current status

Status is phase-gated. A phase marked **PASS** means its implementation and
specified evidence passed external review; it does not authorize every later
phase. The live G1 process is time-dependent, so its ledger is authoritative
until the run and its post-run audit are complete.

| Phase | Scope | Status | Evidence |
|---|---|---|---|
| M0 | Protocol, adversarial review and amendments | sealed | [reports/m0_protocol.md](reports/m0_protocol.md) |
| A1 | Strict SMD real-data anchor | PASS | [reports/phase_a/](reports/phase_a/) |
| A2 | TSB-drift released external stress set | PASS | [reports/phase_a_v4/README.md](reports/phase_a_v4/README.md) |
| B | Causal evaluator and D=8 generator | PASS | [reports/phase_b/README.md](reports/phase_b/README.md) |
| C1-P | Paper-fidelity reproduction | MISMATCH / UNRESOLVED_LINEAGE | [reports/phase_c/README.md](reports/phase_c/README.md) |
| C1-R | Released-artifact operational baseline | PASS | [reports/phase_c/README.md](reports/phase_c/README.md) |
| C2 | Independent CANDI audit | accepted | [reports/phase_c/README.md](reports/phase_c/README.md) |
| C3 | Cross-seed characterization | PASS; SEED-ACTIVE | [reports/phase_c3/README.md](reports/phase_c3/README.md) |
| D-v2 | Controlled synthetic CANDI-SANA intervention | D0 PASS; controlled H1 harm STOP | [reports/phase_d_v2/](reports/phase_d_v2/) |
| E | Original xLSTMAD v1 validity audit | BLOCKED | [reports/phase_e/](reports/phase_e/) |
| E2 | Improved official xLSTMAD validity/instrumentation | PASS | [reports/phase_e2/README.md](reports/phase_e2/README.md) |
| F-v4 | Matched xLSTM/LSTM training and validity | PASS | [reports/phase_f_v4/README.md](reports/phase_f_v4/README.md) |
| G0/G0.1 | Label-blind checkpoint, schema and CANDI-control seal | PASS | [reports/phase_g/prospective.md](reports/phase_g/prospective.md) |
| G1 | Labeled H2/H3a probes | executing at drafting time | [reports/phase_g/](reports/phase_g/) |

The current G1 execution was launched only after the exact pre-label seal
5622376087aaa97249ff9a055f201b250efbf1c2. Intermediate caches and progress
logs are operational artifacts, not scientific outcomes. H2/H3a must not be
interpreted until the run completes and the independent post-run audit passes.

## Research scope and non-goals

The study separates three questions:

1. **Admission:** do real or controlled candidate windows enter an adaptation
   buffer, and are they exposed to optimization?
2. **Information:** do internal recurrent summaries add drift-versus-anomaly
   information beyond score/history controls?
3. **Mechanism:** only if the information results justify it, can delayed,
   reversible normality adaptation be studied further?

The following are deliberately not implemented in M0/G1: rollback, stable/
plastic dual memory, a learned adaptation gate, a new xLSTM cell, a paper
architecture, or a production continual-learning system. H4 delayed evidence
and FIFO controls remain locked by the accepted protocol. ReCATS is not treated
as boundary-free unlabeled test-time adaptation: its published setup has a
pre-partitioned task stream and normal-only training data for every task.

## Scientific guardrails

The protocol is fail-closed and is the source of truth. In particular:

- score the current window before any update; emit an immutable causal record;
- keep evaluator labels, regime/event boundaries and generator metadata out of
  adaptation and observation-only feature extraction;
- separate candidate-selected, queue-admitted, committed-for-update and
  optimizer-loss exposures;
- use fixed fit/calibration data and no test-best threshold;
- use fixed update budgets and explicit candidate-to-commit latency semantics;
- do not use random overlapping-window probe splits; source realizations/events
  remain grouped and any temporal split uses the frozen purge;
- keep official CANDI reproduction unchanged; audits and compatibility fixes
  live in separate overlays;
- never tune architecture, feature families, C, thresholds, or cohorts on
  test outcomes;
- treat zero denominators as N/A, never as zero contamination or evidence of
  safety;
- if a post-label implementation defect is found, quarantine the affected
  outputs and stop rather than silently repairing and rerunning.

## Dataset contract

### A1: strict SMD anchor

The confirmatory real-data anchor is exactly:

- machine-1-8
- machine-2-1

The raw and preprocessed hashes are sealed. CANDI reproduction retains its
native preprocessing and metric semantics. These two series are the only strict
real-data anchor for natural admission and any future natural-SMD harm route.

### A2: TSB-drift external stress test

TSB-drift is an external nonstationarity stress test, not causal evidence for
H2/H3/H4a. The released selection is deterministic and outcome-blind: exactly
three files per bucket, with lexicographic optimization that first maximizes
global source-family diversity, then within-bucket diversity, then minimizes
the squared global family counts, with a final lexicographic filename tie-break.
Repeated source families are clustered in every statistical analysis.

| Bucket | Released files |
|---|---|
| Continuous | 154_SMAP_id_11_Sensor_tr_2117_1st_4770.csv; 171_SWaT_id_1_Sensor_tr_3749_1st_9522.csv; 173_GECCO_id_1_Sensor_tr_16165_1st_16265.csv |
| Change point | 009_MSL_id_8_Sensor_tr_714_1st_1390.csv; 018_Daphnet_id_1_HumanActivity_tr_9693_1st_20732.csv; 137_CreditCard_id_1_Finance_tr_500_1st_541.csv |
| Periodic | 059_SMD_id_3_Facility_tr_757_1st_857.csv; 065_SMD_id_9_Facility_tr_737_1st_837.csv; 075_SMD_id_19_Facility_tr_564_1st_664.csv |
| Random walk | 129_OPPORTUNITY_id_1_HumanActivity_tr_1801_1st_1901.csv; 132_OPPORTUNITY_id_4_HumanActivity_tr_895_1st_995.csv; 188_Exathlon_id_15_Facility_tr_12538_1st_12638.csv |

Source-family counts are SMD=3, OPPORTUNITY=2, and one each for SMAP, SWaT,
GECCO, MSL, Daphnet, CreditCard and Exathlon. The periodic bucket is therefore
single-family descriptive evidence only. Native trace/crop provenance is
explicitly recorded as native_provenance_unresolved where unresolved; that
flag is not reinterpreted as independence. Synthetic sources, contaminated
prefixes, duplicates, same-origin groups and fixed SMD overlaps are excluded.
See reports/phase_a_v4/ for the complete candidate inventory, exclusions,
metadata hashes and manifest.

### Controlled D=8 synthetic stream

The generator uses a non-diagonal stable VAR process with temporal and
cross-channel dependence, D=8, source-disjoint folds and evaluator-side truth.
The five scenario families are:

1. stationary process with anomaly controls;
2. abrupt mean/scale shift;
3. gradual shift;
4. recurring regime A→B→A;
5. correlation-only shift.

The correlation scenario is constructed with a target stationary covariance and
discrete Lyapunov verification so stationary per-channel means/variances remain
matched while cross-channel covariance changes. Generator tests also verify
transition diagonal-variance stability, finite outputs and deterministic
regeneration. Anomaly conditions are point spike, short collective anomaly,
cross-channel dependency anomaly, and a fixed equal-type mixture. Persistent
faults and mixed drift+anomaly windows are stress/descriptive strata, not the
primary binary probe.

Synthetic source folds never cross:

| Fold | Generator seeds |
|---|---|
| Probe train | 1000–1009 |
| Probe validation | 2000–2004 |
| Probe test | 3000–3009 |

The initial clean fit/calibration prefix and all event schedules are frozen in
[configs/synthetic_v1.json](configs/synthetic_v1.json). Observations and truth
are stored separately. The identical-observation/opposite-semantic pair is a
negative non-identifiability control: changing semantic truth alone must not
change observation-only features or predictions.

## Fixed models and feature track

### Official CANDI baseline

CANDI is pinned to commit
28c9679e503832f59e351208cde63657fcb51cad. The released-artifact operational
baseline uses the sealed checkpoint, native preprocessing, native W=10/FPM/
SANA/update behavior, and TRAIN.ENABLE=False evaluation path. Paper-table
fidelity is reported separately from operational artifact fidelity; cached
author arrays are lineage evidence, not runnable experiment results.

Known native bookkeeping defects are preserved in the official baseline,
including final-batch offset misindexing, admission-counter versus committed/
optimizer-exposure differences, moderate-mask overwrite behavior, current-SANA
representation dependence, and the inactive USE_FPM=False iteration path.

### xLSTMAD and matched LSTM

The original xLSTMAD submission version was audited and blocked because its
[W,B,D] output was flattened against [B,W,D] targets and its dataset emitted
repeated tail windows. It is retained as immutable validity evidence, not fixed
and relabeled as a reproduction.

The valid common track uses the improved official implementation:

- repository: Nyderx/xlstmad;
- commit: e8b56ba27352733bb83729e85b1d6196dca70c99;
- dependencies: xlstm==2.0.5, lightning==2.6.1;
- backend: officially supported vanilla float32;
- input: D=8, W=64, embedding=40;
- trainable parameters: 73,504;
- fresh recurrent reset for every independent window; no cross-window carry.

The matched baseline is a standard full-window encoder-decoder LSTM with three
encoder and three decoder layers, H=38, GELU and an H→D output projection. It
has 71,790 parameters (−2.33% relative to xLSTM). Both models use the same
W64/B128/Adam/lr=0.001/50-epoch reconstruction training contract, clean source
folds and detector seeds {11,22,33,44,55}. F-v4 disables cuDNN TF32 for the
matched-LSTM scientific path because reference parity depended on backend
numerics; tolerances and all scientific rules remain unchanged.

The confirmatory internal schema is semantic and capacity-matched:

- history control: 14 columns (current score, first difference, and trailing
  mean/std/slope at widths 4, 8, 16 and 32);
- internal base: 18 columns (hidden 4, effective input gate 5, effective
  retention gate 5, scalar memory 4);
- causal expansion: hidden52, gate130, memory52, combined234;
- history + internal: 248 columns.

xLSTM uses only the four eligible scalar sLSTM cells/heads. LSTM pools all six
actual recurrent layers equally. No learned pooling, layer selection,
zero-padding, mLSTM-only confirmatory feature, or backbone-specific replacement
is allowed. Exploratory xLSTM-only statistics cannot qualify H2/H3a.

For H3a-C the shared CANDI history is the frozen D=8 Phase-D family, mapped by
detector seed to data/phase_d/backbone_{seed}/pre_intervention.pth. CANDI keeps
native W=10 while xLSTM/LSTM use W=64; both are aligned to the same right-edge
timestamp, with common decision stream starting at t=63. Only CANDI scores at
or after t=63 enter the shared 14-column history, and the exact same tensor and
row keys are reused in both backbone arms.

## Phase evidence and decision gates

### CANDI admission and H1

C3 established that adaptation seeds are genuinely active and independently
audited committed anomaly windows were reproducible in all five effective seeds
for each of the six fixed SMD machine/alpha conditions. This is admission
evidence, not evidence of performance harm.

The controlled D-v2 single-update synthetic intervention passed all parity and
canary gates but did not meet the frozen practical harm margin. The route-
qualified status is:

    H1_controlled_harm = STOP
    H1_natural_harm    = NOT_RUN
    H1_harm_overall    = UNRESOLVED

The natural-SMD counterfactual remains an unexecuted alternative; the controlled
negative result must not be generalized to it. H4a/H4b remain locked.

### H2: additional xLSTM internal information

The primary contrast is:

    AP(xLSTM history+combined) - AP(xLSTM history)

H2 requires, simultaneously, a pooled mean gain ≥0.02, paired 95% CI lower
bound >0, Holm-adjusted p<0.05, positive direction in at least 4/5 detector
seeds and 3/4 shifted scenarios, and passing the prespecified duration/severity
robustness strata. AP is the primary metric; AUROC and descriptive strata are
secondary. If any required condition fails, H2 is STOP.

The supportive robustness analysis is test-only evaluation of the same frozen
pooled probe. Positive anomaly rows are stratified by duration
{1, 16, 64, 256} or severity {1, 2, 3}; negatives are the same eligible
anomaly-free drift/transition cohort and receive no invented duration or
severity. No stratum refitting, rescaling, bin merging or threshold tuning is
allowed. H2 requires an equal-weight duration macro gain ≥0.02 with at least
3/4 positive duration strata and an equal-weight severity macro gain ≥0.02 with
at least 2/3 positive severity strata. Unsupported strata are
INSUFFICIENT_SUPPORT and cannot pass. The observation-identical/opposite-
semantic pair is a separate expected non-identifiability negative control and
can never support H2.

### H3a: xLSTM specificity

H3a is interpreted only if H2 is GO. It requires the frozen practical,
confidence, multiplicity, reproducibility and robustness rules for all required
comparisons:

- A: xLSTM combined234 minus LSTM combined234 ≥0.02;
- B: xLSTM internal incremental gain minus LSTM internal incremental gain >0;
- C: the same incremental comparison with the shared frozen CANDI history.

The confirmatory Holm family is exactly four members: H2, H3a-A, H3a-B and
H3a-C. Bootstrap draws=10,000 use seed 901; source-cluster sign-flips use seed
902; source realizations are resampled before detector seeds. Windows are not
independent statistical replicates. H3b is locked unless H3a is GO.

H2/H3a establish information content in this frozen synthetic experiment only.
They do not prove safe continual adaptation, real-world deployment safety, or
superiority of a complete xLSTM detector.

### H3b and H4 boundary

H3b is a minimal, synthetic persistent-state diagnostic only if H3a passes: the
same xLSTM is compared with independent window resets versus recurrent state
carried across chunks. It is not xLSTMAD reproduction. H4a tests whether causal
future evidence through K={4,8,16,32} provides additional information; H4b is a
FIFO scheduling/latency control and cannot claim decontamination merely because
waiting changes endogenous selection. Neither branch is currently authorized.

## Repository layout

    configs/                 Frozen generator, training and G1 protocol configs
    m0/                      Causal evaluator, synthetic generator, correlation and metrics
    scripts/                 Phase runners, audits, sealers and statistical utilities
    tests/                   Unit and adversarial tests
    reports/                 Versioned protocols, manifests, logs, hashes and decisions
    data/                    Large datasets, checkpoints and generated caches (ignored)

Every accepted phase has a phase-specific README and machine-readable manifests
where applicable. data/ is intentionally not a portable source distribution;
use the sealed manifests and SHA256 files to resolve artifacts.

## Environment and reproducibility

The validated execution environment is Python 3.12.3 on an NVIDIA GB10 with
CUDA 13.0 compatibility and PyTorch 2.13.0+cu130. The principal pins are:

    xlstm        2.0.5
    lightning    2.6.1
    torchmetrics 1.9.0
    CANDI        28c9679e503832f59e351208cde63657fcb51cad
    xLSTMAD      e8b56ba27352733bb83729e85b1d6196dca70c99

Use an isolated environment and consult the phase environment/dependency
manifests before installing. In this development workspace commands are often
wrapped by rtk; a normal Python invocation is equivalent outside that wrapper.
Representative label-blind checks are:

    python scripts/run_phase_b_tests.py
    python scripts/phase_a_v4.py
    python scripts/phase_g1_stage_a.py
    python scripts/phase_g1_adversarial.py

The labeled G1 launcher requires the exact review seal and an explicit
--label-access flag. It must not be rerun into an existing output directory or
with a different commit/config. For reference, the sealed form is:

    python scripts/phase_g1_run.py --prelabel-seal 5622376087aaa97249ff9a055f201b250efbf1c2 --label-access --output-dir reports/phase_g

Do not use that command to overwrite a live or completed execution. The current
run's g1_execution_ledger.jsonl, stdout/stderr and cache are progress/evidence
artifacts; AP, probe and decision files become authoritative only after the
run and post-run audit finish.

For long jobs, the optional hourly monitor in
reports/phase_g/hourly_monitor.sh records process/ledger progress, exceptions,
disk usage and cache size only. It does not read labels, predictions, AP,
statistics or decision outcomes.

For every experiment, preserve:

- commit SHA and exact source-file hashes;
- resolved config, seed, dependency, hardware/backend and runtime metadata;
- raw/preprocessed/scaler/checkpoint SHA256 hashes;
- ordered row-key and label/prediction hashes after label access;
- logs and quarantine records for failed attempts.

Official upstream checkouts remain immutable. Compatibility patches, observers
and corrected audits must be stored as explicit overlays and never replace the
official baseline.

## Reading results safely

Start with reports/m0_protocol.md, then read the phase README and its decision
file. Treat the following distinctions as mandatory:

- paper fidelity is not the same as released-artifact operational fidelity;
- candidate contamination is not committed or gradient-exposure contamination;
- nonzero anomaly admission is not adaptation harm;
- TSB-drift source families are not independent native traces;
- a descriptive ablation is not a confirmatory test;
- an H2/H3a result is not proof of safe adaptation.

If a report says **STOP**, **INCONCLUSIVE**, **UNRESOLVED_LINEAGE** or
**QUARANTINED**, retain that status in downstream summaries. Do not merge old
quarantined Phase-D-v1 rows, repaired xLSTMAD-v1 artifacts, author cache arrays,
or partial checkpoints into a later estimate.

## Prior-art positioning

The protocol reviews xLSTM, xLSTMAD, M2N2, CANDI, StrAD/TSB-drift and ReCATS.
Their roles are deliberately separated:

- CANDI is the principal released-artifact adaptation baseline and its hard
  SMD adaptation samples can contain true anomalies;
- StrAD/TSB-drift motivates testing static and streaming failure modes rather
  than assuming adaptation is always beneficial;
- ReCATS studies task-incremental continual MTSAD with known task partitions
  and clean per-task normal training data, not boundary-free unlabeled TTA;
- xLSTMAD supplies the pinned architecture/instrumentation path after the
  original submission implementation was found invalid;
- M2N2 and the original xLSTM paper are comparison context, not evidence that
  the present gate-informed hypothesis is true.

The detailed citations, commit pins and reproduction semantics are maintained
in the phase reports instead of being inferred from a model result.

## License and contribution

No repository license is currently declared. Treat the code, generated data,
upstream artifacts and reports as research material; check upstream licenses
before redistribution. Contributions should preserve the fail-closed protocol,
add tests and manifests, and never rewrite historical evidence or silently
change a frozen scientific definition.
