# SOURCE-only detector and readiness development protocol

**P5-0B2R2 state:** Astra review is PASS; terminal status is
`P5_0B2R2_PROTOCOL_RESEALED`. P5-0B2R2 performed a result-blind protocol
reseal only. This terminal status authorizes only the P5-0B3 SOURCE-only
development/source model-readiness-parameter seal. TARGET labels, raw values,
scores, prefix adjudication, suffix evaluation, and efficacy remain
unauthorized.

## Scope and seal timing

This document fixes the development procedure; it does not authorize running
it in P5-0B2 or under this candidate. The next stage may use only the 74 entities already marked
SOURCE by the pinned role seal, their SOURCE operational rows, and the
canonical SOURCE-only label artifact emitted by the sealed firewall. It may
not inspect target rows, target labels, target missingness, target scores, or
target eligibility. A stratum that fails a gate below is reported
`SOURCE_MODEL_NOT_EVALUABLE`; it is never pooled with another stratum.

### Exact P5-0B3 information envelope

The SOURCE method process may read: the sealed protocol; SOURCE role digests
and their exact strata; the permitted value-free
`automated_common_feature_intersection` lists; the fixed global look/cap
constants; raw timestamps and sensor rows for SOURCE entities only; and the
canonical SOURCE-only firewall artifact. Resolve raw inputs through a
SOURCE-only projection of the committed `entity_manifest.csv`; its structural
inventory has one unique `raw_path` per entity. At the authorized P5-0B3
SOURCE-only gate, validate that no raw path is shared across role entries
before opening any operational file. The P5-0B2R2 candidate validator pins the existing
manifest digest without opening its path-bearing contents. Open and hash-check
only the 74 SOURCE paths. Do not pass target manifest rows or target raw paths
to the method process. If a later runtime cannot preserve this one-file-per-entity
boundary, stop before opening operational values and require a versioned
information-boundary amendment. The firewall process alone may
temporarily map raw manufacturer label rows to SOURCE/TARGET/unsupported
roles, and it emits only SOURCE intervals plus a restricted access audit.
Only the access auditor receives hashes of the full manufacturer-level
input tables; the method process receives the canonical SOURCE artifact hash
and released SOURCE-only audit fields.
Target starts, raw values, timestamps, scores, missingness, labels, event
intervals, prefix outcomes, and suffix outcomes are not released to the
SOURCE method process. The SOURCE process does not receive manufacturer
label CSV paths, target entity IDs or raw paths, target eligibility results, or
target-derived counts. Its output is one sealed model/readiness result per
exact SOURCE stratum and generic stratum failure codes only.

## Entity folds

The unit of splitting is the whole entity, never a row, window, or event.
Split separately within each exact `(manufacturer, configuration_type)`
stratum. For each SOURCE entity, compute

`fold_digest = SHA256(UTF8("P5-0B2-SOURCE-FOLD-v1|" + role_digest))`.

Sort by `(fold_digest, role_digest)` ascending and assign ranks round-robin to
five folds, starting at fold 0. This rule has no random state. The salt and
algorithm are fixed here; role digests are taken from the pinned role seal.
Every outer fold is a pseudo-target fold once; its entities are held out
entirely, and the other four folds alone fit that fold's detector. No entity
crosses the fit/evaluation boundary.

An exact stratum is source-evaluable only if it has at least six SOURCE
entities, at least four common evaluable held-out source pseudo-target
entities across all four detector candidates,
each outer fit split has at least four usable SOURCE entities, and every fit
split has at least 1,024 finite, annotation-clean SOURCE observations across
those entities. A usable fit entity must contribute at least 256 such rows.
A support row has no infinite or nonnumeric feature value and at least one
finite numeric feature; partial `NaN` values are allowed for the frozen source
imputer, while all-`NaN` rows are invalid.
A held-out pseudo-target task must have a valid first timestamp, have an
annotation-clean first 2,304 raw observations under the same
`REFERENCE_CLEAN_PRIMARY` interval rule, reach raw observation 2,304 within
64 days, have at least 200 finite prefix scores at #2304, provide a complete
fixed suffix whose timestamps are valid and nondecreasing through the final
row (duplicates allowed), at least 100 evaluator-confirmed normal suffix observations,
and at least one eligible fault report in the suffix. These are checked only against SOURCE data after
the firewall runs. Failure marks that stratum `SOURCE_MODEL_NOT_EVALUABLE`;
there is no cross-stratum borrowing or threshold borrowing.

## Annotation use and SOURCE pseudo-target tasks

The source firewall's sealed interval parser is the only component that may
read manufacturer label tables. It emits SOURCE-only, typed interval rows.
For AE fitting, use only SOURCE observations outside the inclusive union of
`KNOWN_FAULT`, `DISTURBANCE_FAULT`, and `DISTURBANCE_OTHER` intervals.
`normal_events` rows are retained as provenance labels but do not certify
unannotated periods. No event description, fault name, or target-derived
training interval is used.

For source AP/AUROC qualification, a scored raw observation is positive only
inside the inclusive union of `KNOWN_FAULT` intervals, negative only inside a
`REFERENCE_NORMAL_EVENT` interval and outside every fault/disturbance
interval, and otherwise omitted as unlabeled. If normal and fault/disturbance
intervals overlap, the observation is excluded from this classification
metric. Disturbance intervals are not a positive class. Compute AP as the
non-interpolated average-precision sum over descending score thresholds and
AUROC with average ranks for tied scores. Both metrics are macro-averaged
over the common held-out entity set defined below.

For each held-out SOURCE entity, timestamps through raw row 2,304 must be
nondecreasing in raw-row order (duplicates are allowed); a decreasing or
invalid timestamp makes that pseudo-target ineligible. The commissioning
stream starts at its first raw row and uses the same raw looks, recorded-time
64-day cap, and suffix boundary as the target contract. Its fixed suffix is
raw rows 2,305 through its final row.
The readiness code receives only the SOURCE pseudo-target scores available
by each look. After those score/READY trajectories are sealed, a separate
SOURCE evaluator may use that entity's annotation intervals and suffix scores
strictly after raw observation 2,304 to compute normal-side and event
outcomes. Future-normal points are timestamps
inside `REFERENCE_NORMAL_EVENT` intervals and outside every fault/disturbance
interval. Eligible fault reports are `faults.csv` rows with `efd_possible=true` whose
existing parsed intervals overlap suffix observations. Each row is one report;
duplicates are retained without semantic deduplication. A hit is any suffix
score strictly above threshold within the report interval. `eligible fault-report recall`
is report-level, not unique physical-fault recall or the paper's repeat-filtered
event set. TARGET evaluation and
`Recall_min_source_q10`/`Recall_min_effective` use the same unit. Freeze
`PRIMARY_ABSOLUTE_FPR_CAP = 0.03` and
`PRIMARY_ABSOLUTE_FAULT_REPORT_RECALL_FLOOR = 0.50`; every SOURCE primary
joint-success task requires READY within budget, future-normal pointwise FPR
at most 0.03, and eligible fault-report recall at least
`Recall_min_effective`, where
`Recall_min_effective = max(0.50, Recall_min_source_q10)`. This floor is a
protocol non-degeneracy rule and is not derived from or equated to any
paper-reported 60% result.
Disturbance intervals are not separate reports. Suffix features and scores never enter fitting, readiness features,
or threshold updates. Predeclared source evaluator outcomes may enter
SOURCE-only detector/readiness candidate selection and margin calibration, as
specified below; they are unavailable to the per-entity readiness process.
The sequence is identical for every candidate.

## Preprocessing, model candidates, and fit budget

Use the fixed feature order from `feature_projection.json`, derived solely
from the pinned committed common-feature intersection: ASCII lexical ordered
temperatures/setpoints, control-valve position/setpoint, `*_meter_flow`, and
`*_meter_heat_power`. Exclude `*_meter_energy` and `*_meter_volume`; do not
apply CounterDiffTransformer or value-based reconsideration. In ASCII lexical
stratum order, D changes from `[10, 13, 10, 14, 10]` to
`[8, 11, 8, 12, 8]`. Recompute all D-dependent widths from this reduced
projection. Raw columns outside this projection, including categorical/status
fields, are discarded before the strict projected-schema check; do not inspect
target values or derive target-specific schema/missingness statistics. The
preprocessing candidate set is a singleton: source-fit
per-feature median imputation followed by source-fit mean/standard-deviation
scaling (`ddof=0`); no clipping, feature filtering, residual scaling, or
target-fit operation. A non-finite/zero source scale fails that stratum.

Use the generic EFD v0.7.1 `MultilayerAutoencoder` directly, not the
`FaultDetector.fit` wrapper or PreDist loader. The model-level `fit` accepts
Keras fit kwargs, so set `shuffle=False` explicitly; the wrapper does not
forward that argument. Use the per-row RMSE contract.
For fixed input dimension `D`, set encoder widths to `[4D, 2D]`; the finite
AE candidate grid is the Cartesian product:

| Parameter | Candidates |
|---|---|
| Encoder widths | `[4D, 2D]` |
| Bottleneck width | `max(2, ceil(D/4))`, `max(2, ceil(D/2))` |
| Decoder widths | Mirror encoder: `[2D, 4D]` |
| Hidden activation / output | PReLU / linear |
| Kernel initialization | He normal |
| Objective | Mean of per-row feature-mean squared reconstruction errors |
| Optimizer | Adam |
| Learning rate | `0.0003`, `0.001` |
| Batch size | `128` |
| Epochs | Exactly `100`; no early stopping |
| Denoising noise | `0` |
| Score candidate | Per-row RMSE only |

Freeze Adam parameters to `beta_1=0.9`, `beta_2=0.999`, `epsilon=1e-7`,
`amsgrad=false`, with no weight decay. Dense biases are zero-initialized;
PReLU slopes use the layer's zero initializer and are unshared across its
feature axis. Use the pinned EFD encoder/decoder topology with only the widths
above overridden. Run a deterministic batch pass per epoch with the final
short batch retained, `x_val=None`, and no validation split.

This is four configurations; reset Python, NumPy, and TensorFlow seed to `17`
before constructing and fitting each candidate in each outer fit fold. This
fixed dimensional recipe is a project candidate grid, not the
manufacturer-specific PreDist notebook configuration. No architecture,
score, or preprocessing candidate is added after SOURCE outcomes are seen.
Candidate IDs are `ae-bottleneck-{integer}-adam-lr-{rate}`, with rate encoded
as the exact four-decimal strings `0.0003` or `0.0010`.
Training rows are ordered by `(role_digest,
timestamp, raw_row_index)` and batching is deterministic with shuffling off.
For each fit entity, use at most 8,192 annotation-clean observations; if there
are more, select exactly 8,192 by the deterministic midpoint ranks
`floor((j + 0.5) * M / 8192)`, `j=0..8191`, from that entity's clean rows in
chronological order. All usable source entities therefore contribute equally
by entity cap. Fewer than 256 rows from any required fit entity fails the
stratum support gate.

Set Python, NumPy, and TensorFlow seed to 17; CPU only; deterministic TensorFlow
operations enabled; intra-op and inter-op thread counts set to 1; no GPU,
distributed training, or mixed precision. Record exact OS, Python, TensorFlow,
CUDA visibility, and dependency lock hashes. If repeat fits of a fixed source
fold/configuration in the same pinned runtime do not produce byte-identical
preprocessed arrays and numerically identical scores at `atol=1e-7,
rtol=1e-7`, stop with `BACKBONE_NOT_ADMISSIBLE`; do not loosen the contract
using target evidence.

The official v0.7.1 default pipeline is not used: it clips and filters
features, uses row-shuffled validation without a seed, and may fit a clipper
before its normal-row mask. The paper's manufacturer/event-specific notebook
settings are not candidates.

## Model selection and tie-break

For each candidate, obtain SOURCE out-of-fold per-observation RMSE scores.
Use the common set of held-out entities that have both SOURCE label classes
and finite scores for every candidate; all four candidates are compared on
exactly that same set. Compute average precision (AP) and AUROC on each
common evaluable held-out SOURCE entity using only that entity's SOURCE
semantic labels. The primary model selection value is macro mean AP across
common evaluable held-out entities; ties
within `1e-12` use higher macro mean AUROC, then smaller bottleneck width,
then lower learning rate, then lexical candidate ID. AP/AUROC are source
qualification/background only; they are not target success outcomes. If an
entity lacks both classes or any candidate cannot produce finite scores,
exclude it for every candidate rather than assigning a fabricated metric. If
fewer than four common evaluable entities remain, the stratum is
`SOURCE_MODEL_NOT_EVALUABLE`.

These out-of-fold metrics select the detector candidate and are development
measurements, not independent confirmatory estimates. After selecting the
detector by the AP rule above, use only that selected candidate's OOF score
streams for readiness tuning and for the readiness distance scale. Compute
`IQR_SOURCE` from its OOF scores on SOURCE observations outside known
fault/disturbance intervals, using `Q75-Q25` with NumPy type-7 quantiles in
float64. Seal this source-only scale per stratum with the selected-candidate
OOF score hash. If it is non-finite or `<=1e-12`, the stratum is not
evaluable for readiness development. Do not pool score streams across AE
candidates.

Use only the selected detector candidate's five outer-fold pseudo-target
score streams to tune the frozen readiness candidate grid below, by the
predeclared objective in
`readiness_rule_contract.md`. No target is used to select detector or
readiness parameters. After selection, refit one final AE per evaluable
stratum using the selected configuration, seed 17, and exactly 100 epochs.
Apply the same per-entity cap to the annotation-clean SOURCE rows and use
those exact capped rows both to fit the final imputer/scaler and the AE; do
not fit preprocessing on uncapped rows. Seal feature order/hash, source role
membership hash, firewall artifact hash, fitted preprocessing/model hashes,
source metrics, selected readiness rule/parameters, runtime, and failure
states before TARGET prefix adjudication.

## Source-label firewall boundary

The source development process may read only the canonical SOURCE-only label
artifact and SOURCE operational data. It must not open or receive the
manufacturer label CSVs. The only process allowed to read those raw label
tables is the sealed firewall process in `source_label_firewall.md`; its
output is SOURCE-only. The firewall code, dependency identity, synthetic
tests, and hashes must be sealed before this stage is run.

## Terminal conditions

- Any source-support, schema, runtime, parser, determinism, or score failure
  yields `SOURCE_MODEL_NOT_EVALUABLE` for that exact stratum, unless the
  upstream detector itself violates the frozen inference contract, in which
  case the phase stops `BACKBONE_NOT_ADMISSIBLE`.
- If every readiness candidate has zero pseudo-targets satisfying all frozen
  primary joint-success conditions within a stratum, do not seal a
  lexicographic winner; mark that stratum `SOURCE_MODEL_NOT_EVALUABLE` and
  follow the negative-result path. Never lower the 0.50 recall floor, relax
  the 0.03 FPR cap, or change the candidate grid to create a success. Any
  affected stratum bars a pooled five-stratum success claim.
- No condition permits merging strata, tuning on target values, reopening
  public README exposure, or exposing a target-specific source-development
  failure reason to the method-selection process.
- Source-only execution seals the model and readiness parameters. It does
  not authorize target label access. The terminal
  `P5_0B2R2_PROTOCOL_RESEALED` status authorizes only the P5-0B3 SOURCE-only
  development/source model-readiness-parameter seal. TARGET labels, raw
  values, scores, prefix adjudication, suffix evaluation, and efficacy remain
  unauthorized. The resealed amendment records
  `RAW_PATH_METADATA_READ=STRUCTURAL_METADATA_DEVIATION`,
  `SEMANTIC_BOUNDARY_BREACH=NO`, and `OUTCOME_LEAKAGE=NO`; no operational
  manifest content, data, or labels are accessed by this documentation work.
