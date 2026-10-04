# P4-A — Admission benchmark qualification
Issue #17 authorizes protocol/dataset qualification only. Status: frozen inputs awaiting data-only audit; no detector, adaptation, memory writes or P4-B.

- CONTROLLED_PROTOCOL.md / controlled_config.json: independent traceable M2N2-style normative timing, five physical seeds, paired stationary and identical-X semantic-fault controls.
- TSB_AUDIT_PROTOCOL.md / tsb_audit_config.json: all 47 non-simulated original candidates; retain 28 source-simulated exclusions and every original tag in inventory. Historical label exposure, not confirmatory.
- PRIOR_ART_OVERLAP.md: sample buffering and selective adaptation are existing prior art.
- METRICS_CONTRACT.md: formal acceptance separated from actual baseline exposure.
- provenance/freeze_inputs.json: hashes frozen and pushed before full generation/masked audit.
- scripts/: dataset generation and offline distribution qualification only.

All raw data and computations remain on ssh kuo. Sources are ignored under data/p4a_admission_benchmark/. The existing official TSB archive is reused, never silently replaced. No TSB non-anomaly label becomes legitimate-new-normal truth; unsafe operation is not evaluable.

Reproduce after verifying the active research branch and installing existing audit dependencies:
    python3 research/writable_neural_memory_p10/p4a_admission_benchmark/scripts/acquire_sources.py
    python3 research/writable_neural_memory_p10/p4a_admission_benchmark/scripts/test_protocol.py
    python3 research/writable_neural_memory_p10/p4a_admission_benchmark/scripts/controlled.py
    OPENBLAS_NUM_THREADS=4 python3 research/writable_neural_memory_p10/p4a_admission_benchmark/scripts/tsb_audit.py

The acquisition helper fetches only pinned small official source files and verifies their frozen byte hashes; it does not acquire datasets or execute models. Missing original archive is a blocker. Final qualification docs are added after the audit. No future P4-B execution is authorized by this README.
