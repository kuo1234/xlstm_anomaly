# Issue26 — Exathlon causal score recovery / lifecycle falsification

**NO_ROOT_EFFECT_GAP; method_design_GO=false; STOP for reviewer.**

This is E1 following [E0](../exathlon_semantic_failure_e0/README.md). Historical P4/P5/M0-S/D0/E0 reports are unchanged. Fixed PCA/SPE and a named causal LSTM reference;19 raw traces, native1s, whole-trace normal-only roles; optional TranAD skipped prospectively for unsealed compatibility.

- [EXECUTION_SEAL](EXECUTION_SEAL.md)
- [DATA_SPLIT](DATA_SPLIT.md)
- [CAUSAL_PREPROCESSING](CAUSAL_PREPROCESSING.md)
- [BASELINE_CONTRACT](BASELINE_CONTRACT.md)
- [SCORE_CONTRACT](SCORE_CONTRACT.md)
- [METRICS](METRICS.md)
- [RESULTS](RESULTS.md)
- [FINAL_GATE](FINAL_GATE.md)

Exact executed Python/PyTorch/numpy/pandas versions are in provenance/runtime.json. `prepare.py` downloads/checks pinned archives and derives arrays; pushed seal proof must be created/verified before `run.py`; then `analyze.py`, `document.py --final`, `verify.py --final`. Full raw/checkpoint/score arrays remain ignored; artifact hashes and commands are tracked. No outcome-driven retry/tuning is authorized.

[Review and limitations](REVIEW_NOTES.md), [verification](provenance/result_verification.json), [independent checks](provenance/independent_checks.json), [verification amendment01](AMENDMENT_01.md) / [amendment02](AMENDMENT_02.md), [figure PDF](results/lifecycle_contrast.pdf).

Current cached-evidence audit commands (repository-root cwd):

```sh
E1_PY=/tmp/m0e-issue22/venv/bin/python
$E1_PY research/exathlon_lifecycle_e1/scripts/verify.py --final
$E1_PY research/exathlon_lifecycle_e1/scripts/independent_checks.py
```

`run.py` intentionally refuses another training run once the remote branch advances beyond its verified execution seal. Full retraining needs a reviewer-authorized new execution branch/seal; a negative result does not authorize a rerun. To recover missing raw/prepared assets, first use E0 `sources.py` to restore its source/ground-truth cache, then E1 `prepare.py`. Complete score arrays/checkpoints remain local ignored assets;38 score hashes and saved-checkpoint hashes are tracked. Metric replay uses cached scores and does not retrain. The final renderer adds descriptive figure/review links and uses the exact executed runtime record (Python3.14.6) instead of an earlier documentation-only3.12 shorthand; no scientific config/execution/metric changes.
