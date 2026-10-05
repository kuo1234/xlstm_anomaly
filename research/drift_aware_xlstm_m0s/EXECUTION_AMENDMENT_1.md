# Execution amendment A1 — CPU process initialization

Original prospective Commit A: `ec87d80846f58caf504800079c17839e5a3acba0` (pushed and remotely verified before execution). The first attempt is retained as **PROTOCOL_FAIL (runtime)** in `provenance/failed_v1_execution.log`. The caller launched a Linux default fork process pool; torch2.13's Adam accelerator health check tried to initialize CUDA in a fork worker even though all scientific tensors/models were CPU. It raised `Cannot re-initialize CUDA in forked subprocess` before performing the first Adam update.

Filesystem inspection after stop:90 job directories, **zero files, zero checkpoints, zero training manifests**. No selected checkpoint, validation/test/support/paired/anomaly results were produced or inspected. All child attempts failed at that first pre-update check. Do not treat the attempted job directory count as completed training. Failure is not a negative scientific outcome.

Issue #23 explicitly requires STOP and amendment for protocol bugs. Execution was stopped; this versioned amendment is committed/pushed and its new remote SHA must be verified **before** another scientific attempt. It changes only process/environment initialization: explicit multiprocessing `spawn`, and `CUDA_VISIBLE_DEVICES=''` set before Python import. `configure()` rejects visible CUDA in the CPU protocol. This prevents a CPU optimizer's accelerator readiness probe from creating CUDA context. A random-input/no-label CPU Adam-readiness unit test is added; it does not inspect scientific generator outcomes or checkpoints.

**Unchanged scientific freeze:** `configs/protocol.json`, generator.py, models.py, train.py, evaluate.py, metrics.py and summarize.py are byte-identical to original Commit A. Thus all data/architecture/optimizer/update budgets, seeds, L, anomalies, effects, metrics and kill gates remain fixed. Only common.py/run.py/test_contract.py process guards/readiness differ. Historical failures and logs are preserved; no harder group, outcome or scientific checkpoint is deleted. This is not permission to adapt the protocol after results.

The replacement run uses a distinct ignored artifact path `data/m0s-v1-a1` so the failed empty directories remain untouched. Total/per-run caps remain the same; previous failed attempt is disclosed and excluded from claimed optimizer counts. Separate actual execution time records distinguish attempts.

Amended exact commands on a clean isolated checkout at the **remotely verified A1 commit**, with the new SHA/file seal:

```sh
export CUDA_VISIBLE_DEVICES=''
export M0S_FREEZE_SEAL=/tmp/m0s-issue23-a1-remote-freeze.json
M0S_PY=/home/p76141495/home/xlstm_anomaly/data/phase_e2/venv/bin/python
$M0S_PY -m unittest discover -s research/drift_aware_xlstm_m0s/tests -v
$M0S_PY research/drift_aware_xlstm_m0s/scripts/run.py --artifacts data/m0s-v1-a1 --output research/drift_aware_xlstm_m0s/results
$M0S_PY research/drift_aware_xlstm_m0s/scripts/summarize.py --results research/drift_aware_xlstm_m0s/results --report research/drift_aware_xlstm_m0s/RESULTS.md
```

The original PROTOCOL.md remains the scientific specification; only its process initialization and launch command are superseded here. Freeze verification still checks all committed files and unchanged installed xlstm2.0.5 source hashes. Any subsequent runtime/state/causality/pairing fault stops, preserves evidence and requires a fresh explicit amendment. There is no permission to silently retry or change scientific choices.
