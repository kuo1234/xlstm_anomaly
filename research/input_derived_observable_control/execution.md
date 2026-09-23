# Execution record — P1r

## Host and location

- **Remote machine.** Compute target `kuo`, the GB10 cache host. Its hostname is `spark-3994`,
  recorded in every run sidecar. Platform `Linux-6.17.0-1026-nvidia-aarch64-with-glibc2.39`;
  `/usr/bin/python3` 3.12.3, NumPy 1.26.4, SciPy 1.17.1, scikit-learn 1.9.0.
- **Repository.** `~/home/xlstm_anomaly` (`/home/p76141495/home/xlstm_anomaly`).
- **Worktree.** Execution ran in `~/home/xlstm_anomaly/.worktrees/input-derived-observable-control`.
  The user approved this before execution. The primary checkout was on `main@caa9b3c` with four
  uncommitted tracked modifications (`AGENTS.md` and three files in
  `reports/mlstm_mechanism_audit/`), so it could not provide a clean tree on the P1r branch
  without touching those edits. The worktree was created with
  `git worktree add --track -b experiment/input-derived-observable-control …
  origin/experiment/input-derived-observable-control`. It shares the repository's object store,
  which is the same arrangement A+, A+S and the nonlinear audit used. The primary checkout was
  not modified.
- **A+ cache.** Read-only at
  `.worktrees/strong-observable-control/data/strong_observable_control_cache_v1`. It was not
  moved or regenerated.

## Pre-fit integrity

Checked in the worktree immediately before the job, and again inside the job script
(fail-closed):

- HEAD `4c22e52c876e5e6345b7553063f2fb2e97da2114`, clean tree.
- `git diff 90b2470 HEAD -- scripts tests research/input_derived_observable_control/protocol.md`
  empty.
- `require_preflights('90b2470…')` passed: `preflight.json` PASS and `host_preflight.json` PASS
  under the seal, with sealed-file hashes identical and 500 host fingerprints.

## Job

Compute job `ace76551-d758-4c98-8bef-8d43c5062a78`, run in a single sequential job script.

- **Fit command.** For each of `xlstm:11 xlstm:22 xlstm:33 lstm:11 lstm:22 lstm:33`:

  ```text
  PYTHONPATH=.:scripts /usr/bin/python3 scripts/input_derived_observable_control.py fit-one \
    --cache-root <A+ cache> --architecture <a> --seed <s> \
    --output research/input_derived_observable_control/runs/results_<a>_<s>.json \
    --protocol-seal 90b2470b45b1f8e52aa95ee8677b855b2e3c4e4d
  ```

- **Per-run checkpoint.** After each run, the wrapper wrote an execution sidecar
  `runs/execution_<a>_<s>.json`, then committed and pushed the pair immediately. The sidecar
  records host, platform, package versions, HEAD before the run, start/end UTC, wall seconds,
  result SHA256, and a cache listing snapshot before and after. The wrapper is not part of the
  sealed code and does not touch the result computation.
- **Aggregate.** After all six runs, the sealed `aggregate` command was run and committed.
- **Integrity.** All fit and aggregate logs are empty: no warnings or errors. The cache listing
  snapshot (3,012 files, names, sizes and mtimes, plus the six manifest files) was identical
  before the job, after every run, and after the job:
  `listing_sha256=0cd1a78c4e4bdc9a08edfb02ab92df7809bad9d578c93f74d6635b633179ca49`,
  `manifests_sha256=1d9e95ff4554c31d5fa55f7a1f59caf725492da0f386064449ffdb38d1da9e2b`.

| run | wall seconds | commit |
|---|---:|---|
| xLSTM seed 11 | 1264 | `4745f3234d257b870a68782e55f9db962b6c56fb` |
| xLSTM seed 22 | 1293 | `08f34f9959c692296ef3bc1d2cabde39bbfafb1c` |
| xLSTM seed 33 | 1291 | `a683ab4be0e364e4598d808c5eb729fe6491842c` |
| LSTM seed 11 | 1282 | `e383dcb93a8b488ab36a310f55ecb7628b625ad0` |
| LSTM seed 22 | 1256 | `b5533cb2ab57e66a327e6f0b5396e7030bda50c2` |
| LSTM seed 33 | 1272 | `32ee5979e36cacbcb70e0e102ace769cc1a7b445` |
| aggregate | — | `af6cc474cabe03640dfad6402f06329309d85942` |

The harvested copies of all run files, sidecars and `results.json` are byte-identical to the
committed files.

## Chronology

Seal `90b2470` → preflight `4c22e52` → six run commits → aggregate `af6cc47` → results and
assessments → red-team → consolidation. There was no squash or rewrite.

The earlier preflight job `f0d2800a-caa0-4574-a266-4658c79eec1b` also ran on the same host; see
`preflight.md`.
