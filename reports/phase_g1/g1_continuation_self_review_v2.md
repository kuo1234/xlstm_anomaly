# G1-R1 continuation exact-commit self-review v2

Verdict: **PASS_CONTINUATION_FOR_EXTERNAL_REVIEW**

Reviewed exact implementation commit: `25a67addabf2de30c706824e47e8e280c2ab4ff3`.

The prior report-only seal `205feb5...` is preserved but invalidated for
continuation use after its live guard exposed a missing `_sha_bytes` helper.
That failure was fail-closed before cache inventory loading or any scientific
metric. This v2 review is a fresh review of the corrected exact commit.

## Exact reviewed bytes

The required reviewed executable set is fixed to:

- `scripts/phase_g1_continue_from_cache.py`
- `scripts/phase_g1_cache_audit.py`
- `scripts/phase_g1_reporting_patch_audit.py`
- `scripts/phase_g1_run.py`

Working-tree bytes and `git show 25a67addabf2de30c706824e47e8e280c2ab4ff3:path` bytes match the hashes in the
JSON report. The implementation delta from the invalidated seal is limited to
the missing SHA256 helper and the versioned v2 review-report path. The
cardinality, exact-seal, ancestry, executable-byte, review-byte, and output
path guards remain fail-closed. The dry-run and test entrypoints are recorded
as additional reviewed sources.

## Real inventory dry-run

The v2 metric-free dry-run passed on the real sealed inventory:

- 120,000 inventory records;
- 40,000 primary cache chunk references;
- per detector seed: train 3,200, validation 1,600, test 3,200, total 8,000;
- per arm/architecture: train 200, validation 100, test 200;
- the old arm × architecture × source formula is explicitly rejected;
- no cache arrays were decoded, no labels read, no predictions or metrics
  computed, and no probe path entered.

## Adversarial evidence

- Existing Phase-G1 label-blind suite: 37/37 PASS.
- Continuation-specific fixtures: 13/13 PASS, including current continuation or
  audit hash mutation, unreviewed descendant, wrong/missing seal, review-byte
  mutation, widened/shrunk hash set, output outside ROOT/cache, CLI omission,
  cardinality formula, and metric-free source checks.
- Existing cache-audit mutation fixtures: 10/10 PASS.
- Python compilation: PASS.

No probe fitting, AP/AUROC, prediction, bootstrap, sign-flip, Holm, H2 or
H3a computation was performed. The 118 GB cache remains read-only and no
re-extraction occurred.

## Seal boundary

A future continuation invocation must supply the new report-only review-seal
SHA explicitly. Runtime requires `HEAD == --continuation-seal`, verifies the
reviewed implementation ancestry and all four committed executable byte
snapshots, then checks the accepted historical reporting-patch/cache guards.
This v2 review does not authorize probe fitting; it only establishes the
continuation orchestration gate for external review.
