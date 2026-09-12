# Complete pre-model CPU generator validation

Final result: **125/125 base cases PASS, 0 failures; 625 condition checks PASS** in 188.77 seconds wall time on CPU. All **28 regression tests PASS**, with no errors or skips. A1 and historical audit seals were reverified unchanged.

The unchanged accepted generator/configuration was validated across all 25 registered source seeds × five scenarios: **125 base cases**. Train: 50; validation: 25; test: 50. No seed, schedule, model, or generator parameter was tuned. This is software/data validation, not model evidence.

Every base case covers all five conditions (none, spike, collective, dependency, mixture): 625 condition checks. Each condition generates the anomaly-semantic stream twice for exact regeneration and its legitimate-semantic counterpart once: 1,875 generation calls. Both semantic variants are validated and separately serialized, giving 1,250 variant hash records. The none condition has no event labels to oppose; it checks identity and absence of events, not a fictitious opposite-label event.

Checks per case/condition:

- finite D=8 observations and numeric truth; binary labels; exact deterministic observation/truth/event regeneration;
- clean fit/calibration prefix (4096+1024), fixed test length 16384, source-fold separation using exact registered seed lists;
- exact event onsets, bounds, channels and half-open durations; reconstructed event IDs/labels; event-event coverage never above one;
- all 1/2/3 severities, duration 1 for spikes and full severity × duration {16,64,256} coverage for collective/dependency; persistent fault separately marked stress-only;
- analytical correlation invariants at each seed, including independent Lyapunov solution, stationary moments, correlation difference and bidirectional 256-step diagonal stability;
- paired anomaly/legitimate observations and event IDs exactly identical, with opposite semantic labels on event intervals;
- round-trip observation-only .npy separated from evaluator labels/regime/drift/event/overlap .npz and evaluator metadata JSON. No model receives those truth files.

`cases.json` is the complete per-case/per-condition record, including checks and hashes, not a selected subset. `summary.json` contains final pass/failure counts, elapsed CPU wall time, environment and code/configuration hashes. Canonical array hashes encode dtype and shape before C-order bytes; saved-file hashes cover every serialized variant. Temporary sample files were removed after validation; all hashes and the unchanged generation inputs are retained. No sample-based normalization, seed selection or empirical moment acceptance occurred.

Run `rtk python3 scripts/validate_generator_full.py`, followed by `rtk python3 scripts/seal_v4.py`. The latter verifies unchanged historical audit/A1 seals, checks source hashes and records regression tests separately without rewriting previous test reports. `SHA256SUMS` covers every artifact in this directory.

No detector/model-result file was inspected, no scoring/probe/fitting experiment was run, and no GPU/model training occurred. The existing arithmetic software fixtures remain unit tests only. Phase C must await external review of this delivery.
