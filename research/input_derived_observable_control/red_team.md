# Red-team review — P1r (result-affecting issues only)

| question | finding |
|---|---|
| Protocol seal unchanged? | Yes. `git diff 90b2470 <head> -- scripts tests research/input_derived_observable_control/protocol.md` is empty, and all six run files and sidecars carry `protocol_seal = 90b2470b45b1f8e52aa95ee8677b855b2e3c4e4d`. |
| All six runs on machine `kuo`? | Yes. Every sidecar records `execution_host = spark-3994` (the GB10 cache host) and Linux aarch64, and was produced by job `ace76551` on target `kuo`. |
| P1r identical across backbone and seed for matching source/timestamp? | Yes, by enforced check. For every stream in every run, `fit-one` compared the recomputed P1r (float32 SHA256) with the single stage-2 host fingerprint manifest and would have raised on mismatch. All six runs completed, so all 500 streams matched the same manifest in each run. P1r's feature functions take no backbone, seed, cache or model argument (preflight G6). |
| Row keys exact? | Yes. Both arms of all six runs record train/validation/test keys `71191e06…` / `77ab6914…` / `fb907824…`, equal to the A+ `row_meta`. Dimensions are 1,678 / 1,912. |
| P1r fingerprints exact? | Yes. Stage-2 fingerprints were bit-identical to stage 1 (500/500), and fit time enforced bit-exact equality with stage 2. |
| Validation alone selected the HGB budget? | Yes. In all 12 arm fits the selected `max_iter` equals the arg-max of validation AP (tie → 100), and no candidate record contains a test metric. |
| Test evaluated only after selection? | Yes. The sealed fit path (AST gate G9) calls `_fit_candidate(train, validation, max_iter)` for candidates, then `_fit_selected(test, train, selected_max_iter)` once. |
| Crossed bootstrap correct? | Yes. It is the nonlinear-audit function: rows and columns drawn once per replicate, 10,000 draws, seed 901. An independent recomputation from the committed matrices reproduced both the crossed and the source-only intervals exactly for both backbones. |
| Source-level mean primary? | Yes. `results.json` classifies on the crossed interval of the source-level mean. Pooled per-seed deltas are labelled descriptive. |
| Any historical A+/A+S/nonlinear/G1 artifact changed? | No. `reports/`, `m0/`, `configs/`, `data/` and the A+, A+S, nonlinear, strong-control, framing-refresh and consolidation-review directories are object-identical to pre-P1r `main@855c34d` (see `p1r_consolidation_validation.json`). The A+ cache listing and manifests were unchanged across the job. |
| Conclusion obeys the preregistered wording? | Yes. Both backbones are reported as `NO_RESOLVED_ADDITIONAL_UTILITY` with the frozen sentence, and no insufficiency, information-theoretic, superiority, mechanism, causal or deployment wording is used. |

## Limitations

These are recorded, not acted on.

- All 12 arm fits selected the upper frozen budget `max_iter = 300`. Whether a larger budget
  would change the increment is not assessed and is not authorised; the grid was fixed before
  the result.
- There are three detector seeds and one synthetic generator. The intervals are exploratory.
- P1r is one bounded input-derived summary. The null outcome is specific to it and to the
  frozen decoder.
- Execution used a dedicated worktree instead of the primary checkout, with the user's approval.
  The two share the same repository and object store, and the primary checkout was untouched.
  This does not affect results.

No new analysis was introduced in response to the result. The descriptive tables in
`results.md` come from `summarize_results.py`, which was written before any run file was read.
