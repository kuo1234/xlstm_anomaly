# Phase G1 post-label execution incident — v1

Status: **QUARANTINED / STOP_RESULT_UNRESOLVED**

This is a fail-closed incident record for the first labeled G1 execution. It
does not repair, summarize, or reinterpret any scientific outcome. The record
is committed so that the implementation amendment can be reviewed before any
cache post-processing or rerun.

## Execution exposure

- pre-label seal: 5622376087aaa97249ff9a055f201b250efbf1c2
- execution process: one fresh process; no retry, resume or overwrite
- expected labelled streams: 2,625
- completed labelled streams: 2,625
- process terminal event: process_exception
- ledger SHA256 at failure: 67e6a30d518011e8d06307e7d1b305449b4787602f3bd1701f8989a7dadeab0a
- preserved cache: reports/phase_g/g1_primary_cache/
- preserved ledger: reports/phase_g/g1_execution_ledger.jsonl

Evaluator labels were joined while constructing the stream records. Therefore
this is a post-label implementation incident even though no scientific summary
was successfully written.

## Failure and localization

After all stream extraction/label joins completed, the runner attempted to
construct the primary probe manifest. The relative output directory supplied to
the launcher remained a relative Path:

    reports/phase_g/g1_primary_cache

The manifest code called primary_cache_dir.relative_to(ROOT), where ROOT is
absolute. Python raised:

    ValueError: 'reports/phase_g/g1_primary_cache' is not in the subpath of
    '/home/p76141495/home/xlstm_anomaly'

This occurs at the primary-cache path serialization boundary, before the
primary probe-fitting loop, AP computation, confirmatory statistics, secondary
pass and decision-writing block. No g1_results.json, g1_statistics.json or
g1_decision.* from this attempt is authoritative.

## Quarantine and permitted amendment

All v1 labelled caches and generated logs remain preserved but are
QUARANTINED; they must not enter probe estimation, confidence intervals,
p-values, plots or GO/STOP decisions. The old pre-label seal and all historical
phase evidence remain immutable.

The narrowly scoped amendment canonicalizes output_dir to an absolute path at
the runner boundary before any manifest serialization. It changes no
observations, labels, features, model state, optimizer state, cohort,
statistics or decision rule. A regression fixture verifies relative-path
canonicalization without loading test data or fitting a probe.

This amendment is submitted for external red-check. It must not be used to
post-process or rerun the quarantined labeled cache until the review authorizes
the next step.
