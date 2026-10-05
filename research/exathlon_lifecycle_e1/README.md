# Issue26 — Exathlon causal score recovery / lifecycle falsification

**Execution seal only — no detector training/inference yet. Push and verify this commit before running.**

This is E1 following [E0](../exathlon_semantic_failure_e0/README.md). Historical P4/P5/M0-S/D0/E0 reports are unchanged. Fixed PCA/SPE and a named causal LSTM reference;19 raw traces, native1s, whole-trace normal-only roles; optional TranAD skipped prospectively for unsealed compatibility.

- [EXECUTION_SEAL](EXECUTION_SEAL.md)
- [DATA_SPLIT](DATA_SPLIT.md)
- [CAUSAL_PREPROCESSING](CAUSAL_PREPROCESSING.md)
- [BASELINE_CONTRACT](BASELINE_CONTRACT.md)
- [SCORE_CONTRACT](SCORE_CONTRACT.md)
- [METRICS](METRICS.md)

Reproduce with Python3.12/PyTorch2.9/numpy2.5/pandas3.0 from provenance/runtime.json. `prepare.py` downloads/checks pinned archives and derives arrays; pushed seal proof must be created/verified before `run.py`; then `analyze.py`, `document.py --final`, `verify.py --final`. Full raw/checkpoint/score arrays remain ignored; artifact hashes and commands are tracked. No outcome-driven retry/tuning is authorized.
