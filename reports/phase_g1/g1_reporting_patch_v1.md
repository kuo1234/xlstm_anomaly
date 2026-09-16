# G1-R1 post-label reporting-patch authorization

Status: **PENDING_CACHE_AUDIT**

This record is a post-label exception for one narrowly scoped path/reporting
patch. It is not a new pre-label seal and does not retroactively extend the
PASS_FOR_LABEL_ACCESS review to the patched commit.

## Fixed lineage

- original implementation commit: fe507084b9a1aba0c67a4536c5bb938ea89a4945
- original pre-label review seal: 5622376087aaa97249ff9a055f201b250efbf1c2
- reporting-patch commit: 2c79cbf62574df498f1c9fd39d1bee9aa495e41a
- incident: reports/phase_g1/g1_postlabel_failure_v1.json
- quarantined ledger SHA256: 67e6a30d518011e8d06307e7d1b305449b4787602f3bd1701f8989a7dadeab0a

The exact seven files changed between the original pre-label seal and the
reporting patch, with old/new hashes and classifications, are enumerated in
g1_reporting_patch_v1.json. The only scientific executable path changed is
scripts/phase_g1_run.py; its only allowed change is canonicalizing output_dir
once at run entry before repository-relative manifest links are serialized.
The README, incident/amendment records and adversarial-test JSON are
documentation or label-blind test artifacts. tests/test_phase_g1.py adds only a
label-blind path regression fixture.

The historical pre-label review file
reports/phase_g1/g1_self_review_prelabel_v2.json is byte-identical to the
original seal and has not been overwritten. The patched commit is therefore a
post-label reporting exception, not a new pre-label approval.

## Scientific equivalence requirement

An AST/source-diff audit must verify that the patch changes no source
generation, observations, labels, scalers, checkpoints, CANDI/backbone
extraction, row keys, feature tensors, probe fitting, metrics, statistics,
robustness, semantic control or Boolean decision rule. Any difference outside
the output-path handling is a hard failure.

## Cache boundary

The first labeled execution completed all 2,625 stream extractions but stopped
at primary probe-manifest construction. Its 118 GB cache is preserved and
QUARANTINED. No AP, probe fit, validation-C choice, bootstrap, sign-flip, Holm
correction or H2/H3a result may be computed until the cache-integrity audit
returns PASS_CACHE_REUSABLE and a later external review authorizes
continuation.
