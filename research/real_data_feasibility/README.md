# Real-data feasibility audit (2026-09-22)

Independent, data-only audit based on `main@2810c346d40ceb3e011625f6fbf63db8833d9572`. This does **not** amend [the revised M0 protocol](../../reports/m0_protocol.md), open any conditional gate, or authorize a model run. Existing Phase A seals and G1 reports are read-only. No preprocessing, resampling, anomaly scoring, or experiment results are produced here.

Read [the machine-readable inventory](datasets.json), [source chains](provenance.md), [label interpretation](label_semantics.md), [acquisition status](acquisition_status.md), [four-tier matrix](comparison_matrix.md), and [small proposed suite](recommended_suite.md). `unknown` means the source/file was not checked; it is not a negative result. A role marked usable in the manifest means *potentially*, conditional on a separate prospective protocol and source/split verification.

The ignored `data/external_real/` holds acquired bytes and a local-only `local_manifest.json` (absolute paths, byte counts, SHA256, source URLs). `data/phase_a` in the main project has historical seals but its raw archive is **not** present in either checkout at audit time. The worktree does not duplicate those absent assets. To repeat public acquisitions, from this worktree:

```bash
python3 -B scripts/real_data_acquire.py --dataset smd-1-4
python3 -B scripts/real_data_acquire.py --dataset smd-2-1
python3 -B scripts/real_data_acquire.py --dataset andri-sensor
python3 -B scripts/real_data_acquire.py --dataset nasa-labels
python3 -B scripts/real_data_acquire.py --dataset inventory
python3 -B scripts/real_data_inspect.py all
```

The downloader fails rather than overwrites a conflicting file; `smd-2-1` has independent Phase A hash expectations. `--dataset nasa` tries the author-linked legacy archive, currently HTTP 403. [Telemanom now points to a Kaggle-hosted archive](https://github.com/khundman/telemanom); a different archive is not silently treated as byte-equivalent. `--dataset hai` requires Git LFS and checks for real CSV bytes, not pointer text. SWaT/WADI/Yahoo/CreditCard are explicit manual-access failures. The inspector prints JSON to stdout and never writes or transforms data; `.npy` requires NumPy, and its labels remain source intervals rather than silently expanded points.

Inspection snapshot: SMD 1-4 train `(23706,38)`, test `(23707,38)`, test labels 720 positive; SMD 2-1 train `(23693,38)`, test `(23694,38)`, labels 1170 positive. IoT 1 has 1531 rows and 2 `change_point` markers, IoT 2 has 1538 rows and 1. Those IoT timestamps are irregular in the actual files despite the extended paper's "hourly" description. All intervals reported by the inspector use zero-based half-open row indices; source NASA interval endpoint semantics remain unverified.
