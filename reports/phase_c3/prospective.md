# C3 — prospective cross-seed characterization

Authorized after external review of b0e03a6. This note must be committed/pushed
before any new seed execution. Seeds are fixed to {0,1,2,3,4}. Immutable released
checkpoints, official CANDI commit 28c9679e503832f59e351208cde63657fcb51cad,
official scripts/config/preprocessing and the frozen Phase C environment remain
unchanged except SEED. TRAIN.ENABLE=False; no retraining or tuning. Each run
starts in a fresh process with independent model/optimizer/RNG state. Historical
paper fidelity remains MISMATCH / UNRESOLVED_LINEAGE, independently of C1-R.

## C3-A: seed-effectiveness pilot

SMD_1-8 alpha5, seeds0 and1. Capture pretrained backbone tensor hash immediately
before adapter construction, freshly initialized adaptation parameter hashes
immediately afterward, and global Python/NumPy/Torch CPU/CUDA RNG fingerprints
before and after construction. Hash each SANA module separately and together.
Compare full score arrays, candidate/commit IDs, update timing, every optimizer
step and final model hash, metrics, contamination/exposure counts.

SEED-ACTIVE requires changed adaptation initialization and/or causal adaptation
trajectory with unchanged pretrained backbone/config/observations. Different RNG
fingerprints or SEED metadata alone are insufficient. SEED-INERT means identical
initialization and behavior despite different nominal seeds: STOP expansion and
return for amendment; do not run seeds2–4 or interpret nominal n=5 as replication.
Unexpected backbone/config/data mismatch is INVESTIGATE, not seed effectiveness.

A seed0 integrity rerun is necessary for the pilot's new pre-construction
backbone and separated SANA hashes; compare its entire trajectory to the sealed
native alpha5 control. It is a technical repeat, not a sixth replicate.

## C3-B: conditional replication

Only after C3-A SEED-ACTIVE, characterize all six fixed machine/alpha conditions
(SMD_1-8 and SMD_2-1 × alpha0.5,1,5) for seeds0–4. Reuse sealed seed0 records and
stable-ID traces where available. The original 1-8 alpha1 seed0 lacks an audit
trace, so one integrity/audit completion rerun is allowed, requiring exact score
and final-state parity with its sealed original. Reuse the seed1 pilot row.

For each row report native AUROC/trapezoidal PR-AUC, candidate/committed/gradient
exposure contamination, hard/moderate separately, unique/repeated anomalous
exposures, update/pending counts, candidate-to-commit latency, score/model hashes,
runtime and GPU allocator peaks. Native diagnostic anomaly counters are not the
scientific source: independent stable IDs and evaluator-only truth are used.
Retain all official bugs unchanged. Zero denominator is N/A.

Report per-condition seed values, mean/sample SD/range and distinct initialization
and trajectory hashes where measured; never pool six conditions as n=30. Verify
seed effectiveness within each condition as well; nominal seeds with identical
initialization/trajectory do not count as independent stochastic replicates.
Existing seed0 rows lacking separated initialization hashes retain explicit N/A,
not inferred measurements. Cross-seed inference is conditional on fixed released
backbone, stream and environment, not independent training/data replication.

Evaluate preregistered H1-admission only with effective seeds: nonzero independently
audited committed anomalies on either SMD in at least4/5 seeds within a fixed
machine/alpha condition. Report all six conditions, not a pooled success fraction.
This is admission evidence only; H1-harm is NOT tested. Report hard-versus-moderate
contamination directions per seed and queue support. Report candidate-to-commit
contamination deltas; describe >=0.01 absolute as materially different (descriptive
one percentage-point threshold, not a new GO gate). Explicitly count repeated
anomalous loss exposures when STEPS>1; these are not additional independent events.

No controlled contamination, Phase D, xLSTM/LSTM, probes, H4 or H3b. Commit/push
the bounded C3 results and return for external review, including SEED-INERT STOP
if applicable. No adaptation-harm conclusion is authorized from contamination.
