# R0 data acquisition and preservation

Status: **ACQUIRED_AND_VERIFIED** — 9/9 raw files match the frozen SHA256 and byte counts. No historical Phase-A
record was resealed or overwritten; `research/real-data-feasibility-audit` was not modified; no `git worktree prune`
was run; no CANDI pickle was read.

## Stable location

GB10 (`ssh:kuo`) primary checkout, git-ignored: `data/external_real/r0_smd/` under `~/home/xlstm_anomaly`
(`data/` is in `.gitignore`; the primary checkout's tracked files are unchanged). The R0 worktree
`.worktrees/real-data-r0-protocol` reaches it through the git-ignored symlink `data/external_real`. A local
`local_manifest.json` in that directory records, per file: canonical URL, pinned commit, bytes, SHA256, local path,
install route, status and UTC timestamp (host paths are kept only in that git-ignored file). The directory can be
overridden with `R0_DATA_ROOT`; every load re-verifies the hash and fails closed.

Files: `{machine}_{train,test,test_label}.txt` for machine-1-8, machine-2-1, machine-1-4 (pinned URL pattern
`https://raw.githubusercontent.com/NetManAIOps/OmniAnomaly/7fb0e0acf89ea49908896bcc9f9e80fcfff6baf4/ServerMachineDataset/{split}/{machine}.txt`).

## Routes and evidence

| machine | install route | public pinned URL re-download | feasibility-worktree bytes | legacy `data/phase_a/smd_raw` on GB10 | hash authority |
|---|---|---|---|---|---|
| machine-1-8 | public pinned reacquisition (required by brief) | match (3/3) | not present there | match (3/3) | Phase-A seal (`reports/phase_a/smd_seal.json`) |
| machine-2-1 | feasibility-worktree copy | match (3/3) | match (3/3) | match (3/3) | Phase-A seal; feasibility audit `datasets.json` agrees |
| machine-1-4 | feasibility-worktree copy | match (3/3) | match (3/3) | test file only: match | feasibility audit `datasets.json` @ `8f6ee87` |

* The feasibility-worktree bytes live on the user's workstation at the separate worktree of
  `research/real-data-feasibility-audit@8f6ee870e1c8d0809d4d1352e8fde0fd450b56d5`, under
  `data/external_real/smd/` (that worktree's HEAD is `8f6ee87`). They were hashed in place (read-only), compared with
  the audit records, and transferred to GB10 as the install source for machine-2-1 and machine-1-4.
* Every file was also downloaded independently from the pinned public URL on GB10; all nine public downloads match,
  so the audited public route alone reproduces the exact bytes.
* Byte counts for machine-1-4 (train 8,107,452; test 8,107,794; test_label 47,414) come from the feasibility audit's
  git-ignored local manifest; its SHA256 values come from the committed `datasets.json`.

## Verified identities

| file | bytes | SHA256 |
|---|---:|---|
| machine-1-8_train | 8104716 | `3b46e9754ec06bebd0bf3fe68dbe28b2a4b67298e795c9501d97f42083e337fc` |
| machine-1-8_test | 8105058 | `b8784c3b4169f8a0a2ed9f47b00070d72ed214dae0307553b8cfdb80c712d779` |
| machine-1-8_test_label | 47398 | `8019476032c4c5b4b80127cfb9e74ee7d57fbbd558aa15097518713e16463a47` |
| machine-2-1_train | 8103006 | `d6eb13ff74a537cf33686319fffdd4cdcb394862570a3acd519b4c37af97cd2e` |
| machine-2-1_test | 8103348 | `2d103661799271be958227907950a1c76803356442d60a4070671cc0abbefb20` |
| machine-2-1_test_label | 47388 | `416dd20a447f38b8d9394382293ed44f509c1c3f99c4aa2fbff179498626dbdc` |
| machine-1-4_train | 8107452 | `2ec56c43f91684aa4751a6b72d359669266712dd69bdc7efda3dc60c0ade1156` |
| machine-1-4_test | 8107794 | `98ade00e57eac63e8f81a506a8e848803b58590835ab2b3cf53d1f0459900bd3` |
| machine-1-4_test_label | 47414 | `a470a3f7b66ec3d080fc5ee3d9565e0f3bfcfa16a1650259f771736327fa9a8b` |

## Is the old feasibility worktree still needed?

No longer as the *only* copy: the exact bytes are now preserved at the stable GB10 location and are independently
reproducible from the pinned public URL. The worktree also holds non-SMD feasibility files (AnDri, NASA) that R0
does not cover, so whether to prune it remains a separate decision for the user; this task did not prune it.

## Reproduce

```
python3 scripts/real_data_r0_data.py acquire [--staged DIR] --report acquisition_report.json
python3 scripts/real_data_r0_data.py verify
```

`acquire` never overwrites a differing file and exits non-zero with `DATA_PROVENANCE_BLOCKED` on any mismatch.
