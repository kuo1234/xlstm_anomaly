# P4-B minimal causal admission pilot
**ADAPTATION_HARMS_RETENTION / pending review — STOP.**
Issue #18 only; RESULTS.md contains all135 trajectories, allQ Pareto/physical-group tables and every negative episode.

5 physical groups ×3 strata ×9 policies, one deterministic train-only rank2 linearAE per group; same fixed decoder SGD operator. Q1 equals immediate mutation:5/5 valid B commits, medianTTA7, stationaryFAR1.0 and oldA FPR deterioration .2051–.2617. Q≥64 coverage0/5; Q64 has5 fault promotions underB, largerQ never write. No joint safe-delay gate passes. Paired fault-twin failures remain included.

Pre-result freeze bd89ca252a1a84a3e68f38467984a05d0d2ea096; observation-only trace seal374a0081fff1ec5777f80555a1fec72748f0d308 pushed before normative evaluator.16 pre-result tests,45 exact twin pairs,15 Q1/immediate parameter parity pairs; independent audit verifies622080 ledger rows and75725 updates. Raw artifacts stay ignored onssh kuo; no local raw download. No native M2N2/CANDI exact reproduction, TSB admission, RL or rescue.

Reporting-boundary defect disclosed: five frozen raw Q1 transition durations were negative because a globalA PROMOTE preceded B. Additive correction (3 tests) distinguishes pre-transitionA and transition-premature endpoints; rawmetrics and finalgate unchanged. See results/reporting_boundary_correction.json and RESULTS.md.

Reproduce in existing ssh kuo checkout:
    OPENBLAS_NUM_THREADS=1 python3 research/writable_neural_memory_p10/p4b_minimal_admission/tests/test_pilot.py
    OPENBLAS_NUM_THREADS=1 python3 research/writable_neural_memory_p10/p4b_minimal_admission/scripts/run.py
    # Commit/push run_manifest + trace seal before evaluator.
    OPENBLAS_NUM_THREADS=1 python3 research/writable_neural_memory_p10/p4b_minimal_admission/scripts/eval.py
    OPENBLAS_NUM_THREADS=1 python3 research/writable_neural_memory_p10/p4b_minimal_admission/scripts/audit_results.py
    OPENBLAS_NUM_THREADS=1 python3 research/writable_neural_memory_p10/p4b_minimal_admission/tests/test_reporting_boundary.py
    OPENBLAS_NUM_THREADS=1 python3 research/writable_neural_memory_p10/p4b_minimal_admission/scripts/reporting_boundary.py
    OPENBLAS_NUM_THREADS=1 python3 research/writable_neural_memory_p10/p4b_minimal_admission/scripts/report.py

Hashes/environment/source roles: configs,provenance and results/run_manifest.json. Primary policy/evaluator frozen scripts unchanged after outcomes. Reporting/audit additions do not control policies. Historic P4-A truth exposure means not strict confirmatory. Benchmark readiness is accepted; safe-delay benefit is not supported. Next task requires reviewer scope; no automatic RL or architecture/gap/Q changes.
