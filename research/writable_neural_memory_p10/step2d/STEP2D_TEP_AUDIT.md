# Step 2d — Extended TEP acquisition / semantic / subset audit

**TEP_PROTOCOL_PARTIAL — pending review.** Official range acquisition and the observation parser are feasible. Source-verified activation-row, warm-up and settled-normal semantics remain incomplete; this audit does not certify a PROMOTE-safe interval or authorize a benchmark/RL run.

## Authorization and execution record

- Task: [Issue #15, Step 2d](https://github.com/kuo1234/xlstm_anomaly/issues/15#issuecomment-5977904614); preceding [Step 2c review](https://github.com/kuo1234/xlstm_anomaly/issues/15#issuecomment-5977728169) accepts protocol PASS / PARTIAL_TRANSFER and explicitly withholds RL GO.
- Branch `research/p7-p10-segment-memory`, parent `d5ecc07064909c976400d024056ee67ef436966a`.
- All acquisition, raw caches, extraction, inspection, tests and Git edits ran through `ssh kuo` on `spark-3994`. Remote worktree: `/home/p76141495/home/xlstm_anomaly/.worktrees/p7-p10-segment-memory`. Main was not edited. `/home/p76141495/.codex/RTK.md` was absent.
- Initial schema probe inspected channel names, groups and example attrs, without running a detector. [selection.json](selection.json) fixed five literal paths at **2026-10-04 08:14:42 UTC**, before reading their full observations. Selected-profile inspection followed; final parser smoke began **08:19:12 UTC**. Metadata/ground-truth profiles were deliberately exposed for this audit; no label-blind experiment or strict confirmation is claimed.
- Zero detector runs, scaler fits, CV calculations, classifier training or RL runs. Existing Step 2c policy/config/code are untouched; `cv<=0.10` unchanged. No Step 3 execution.

## Official provenance and acquisition

Canonical version: [DTU dataset v1](https://data.dtu.dk/articles/dataset/Tennessee_Eastman_Reference_Data_for_Fault-Detection_and_Decision_Support_Systems/13385936/1); DOI [10.11583/DTU.13385936.v1](https://doi.org/10.11583/DTU.13385936.v1). Author-maintained README and file inventory obtained from [versioned official API](https://api.figshare.com/v2/articles/13385936/versions/1). License **CC0**, as specified by the API and README. API publication date 2021-03-12; modified 2023-07-12, version remains 1.

Publication: Reinartz, Kulahci & Ravn (2021), *An extended Tennessee Eastman simulation dataset for fault-detection and decision support systems*, Computers & Chemical Engineering 149, 107281; DOI [10.1016/j.compchemeng.2021.107281](https://doi.org/10.1016/j.compchemeng.2021.107281). [DTU publication record](https://orbit.dtu.dk/en/publications/an-extended-tennessee-eastman-simulation-dataset-for-fault-detect/) confirms the dataset relationship and healthy/faulty simulations across modes. The publisher full-text request returned **403**; DTU record offers no full-text file and [LTU author-affiliated record](https://ltu.diva-portal.org/smash/record.jsf?pid=diva2:1567937) says no full text. No bypass or unverified paper/mirror substituted. The abstract does not independently certify settling times.

| Official file | Bytes | Official MD5 | Official SHA256 |
|---|---:|---|---|
| TEP_Mode1.h5 | 23,924,710,848 | c79ecc6d12a5ccb49caffcd8f531feae | not provided |
| TEP_Mode2.h5 | 23,897,125,720 | 72ee75fdf6da8e59327f04fd4fd49662 | not provided |
| TEP_Mode3.h5 | 23,921,551,744 | 5f4bf0d87e7f9ff81ee632f84f2d9050 | not provided |
| TEP_Mode4.h5 | 23,219,369,960 | c1e76a74022230450dc14fe904451236 | not provided |
| TEP_Mode5.h5 | 23,890,304,712 | 8f3c1a1ebeb80ad78089f82a7d521fda | not provided |
| TEP_Mode6.h5 | 23,907,566,544 | d01e032a1f3ff9ca3afaa1f74c52e1a6 | not provided |
| Readme.html | 8,493 | 963359b135036c0b19951929798a8b46 | not provided |

The API supplies separate official `ndownloader.figshare.com/files/<id>` URLs; these are the DTU platform's backing downloads, not a replacement mirror. Total **142,760,638,021 bytes = 142.76 GB / 132.96 GiB**. The smallest whole file is Mode4 at 23.22 GB, but downloading it is unnecessary: Mode4's initial 512-byte probe and Mode1's subsequent bounded requests returned HTTP 206, exact Content-Range and HDF5 bytes. Mode1 was chosen for the same-starting-mode subset, not detection outcomes.

**Acquired:** full API JSON and README; **9,437,184 bytes (9 MiB)** of distinct Mode1 range blocks, plus two small extracted observation NPZs on the remote host. The initial Mode4 512-byte probe was inspected in memory and not retained as a raw file. Not acquired: any complete HDF5, six-file bundle, alternate-source data or local raw data. The acquisition code caps range cache/transfer at 64 MiB, rejects whole-file HTTP 200, wrong ranges, altered cache and oversized reads. An early schema probe failed on a refused range; restarting canonical official requests succeeded, without accepting incorrect bytes or changing source.

All retained range blocks have individual SHA256 and exact byte offsets in [inspection.json](inspection.json). README MD5 matches the API. SHA256 of full README: `68f3b03ea10732ec631a720be614b44267e7b61c10eb2f141d95c8fb1293b460`; saved API JSON: `327f4c141bdebbc103c3dc1b8d1f61f8b410fbadd8fac93a9cef80817ae021f4`. The official whole-HDF5 MD5 and an unavailable whole-HDF5 SHA256 **have not been verified** by partial acquisition. Partial-block hashes establish retained-byte identity, not the complete file checksum. Raw files are ignored under remote `data/step2d/official/`.

## Observed hierarchy and per-run metadata

Mode1 is verified from bytes; the README describes the same structure for all six files. Other modes' full hierarchy is **not independently inspected**.

```text
/Processdata_Labels                 channel names, not anomaly labels
/Additional_Meas_Labels             channel names, not anomaly labels
/Mode1/ModeTransition/{SimulationCompleted,SimulationStopped}/Mode1ToMode{2..6}/TransitionTime{10,20,30,40}
/Mode1/SingleFault/{SimulationCompleted,SimulationStopped}/IDV{1..28}/Mode1_IDVInfo_<id>_<magnitude>/Run<n>
/Mode1/SpVariation/{SimulationCompleted,SimulationStopped}/SP{1..12}/tRamp_<hours>/SpMagnitude<percent>
```

Not every combination is completed. Mode1→3 and Mode1→6 at 10 h occur **only under SimulationStopped**; their completed groups have 20/30/40 h. All four requested Mode1→2 durations are completed. Emergency-stopped runs cannot be called benign new-normal examples.

| Needed field | Inspected evidence | Qualification |
|---|---|---|
| Initial mode | `modeAtInit=[1]`, Mode1 path | available |
| Target mode | `Mode1ToMode2` / `Mode1ToMode3` path | mode path available; target values in profile |
| Target setpoint | `setpoint_init`, shape 3×12 | profile available, row schema not named |
| Event family | ModeTransition / SpVariation / SingleFault path | available, evaluator only |
| Activation time | profile third row contains 30 on changed columns | **candidate 30 h, row meaning not independently certified** |
| Ramp duration | `tRampSetpoint=[10]`, README TransitionTime10 | 10 h command ramp, not physical settling |
| Fault ID/magnitude | IDV1/IDV2, 100% path; one nonzero target in `idv_init` | family/presence available; onset-row contract pending |
| Native random seed | `seed` attr | available; Run1 is not seed 1 |
| Shutdown | group and `simTerminatedSuccessfully` | completion status available; exact stop-time semantics not audited |
| Settled endpoint / warm-up | no named fields or README guarantee | **unknown** |

Inspected run attrs also contain mean operating cost, production and quality. These summarize the entire simulation and would leak future information if used by a policy; they are excluded along with all event metadata.

## Deterministic subset (no outcome selection)

[tep_subset_manifest.json](tep_subset_manifest.json) preserves original paths, seeds and missing slots; [selection.json](selection.json) is the pre-array selector snapshot. All cases start in Mode1; no mode-ID feature is supplied.

| Preselected case | Native seed | Status | Full observation smoke |
|---|---:|---|---|
| Mode1→2, 10 h, completed | 91000 | inspected; fault profile entirely zero | yes |
| Mode1→3, 10 h, completed | unknown | **missing**; stopped counterpart exists | no replacement |
| SP1 ramp 10 h to 105%, completed | 3010001 | inspected; fault profile entirely zero | no |
| IDV1 100%, Run1, completed | 21812 | inspected | yes |
| IDV2 100%, Run1, completed | 20819 | inspected | no |

This is **same-mode intervention pairing**, not a common-random-number or identical-initial-trajectory causal pair. The native seeds differ, and only one selected physical run exists per condition. Seed/operator/window replicas must never inflate independent N. There are four available preselected runs; the fifth slot remains missing. No slower ramp or alternative seed was substituted after inspecting completion status. This small audit is not evidence of statistical benchmark adequacy.

## Evaluator-only semantics and readiness

Machine-readable contract: [tep_label_semantics.json](tep_label_semantics.json). Its four target states are explicitly conditional on source verification; the executable guard returns UNKNOWN when profile axes/warm-up are unverified or a run stopped.

- **NORMAL_A:** `[verified warmup_end, verified event_start)`, only when the initial mode is healthy and fault-free. No warm-up cutoff is invented from the 30 h pre-event prefix. `time_info=[0,100,.05,.0005,70]` is retained as internal metadata; the meaning of 70 is unknown, not assumed to be a warm-up or settling time.
- **TRANSITION:** command interval `[event_start, event_start+tRampSetpoint)`. Candidate interpretation for the selected completed ramp is **[30,40) h**. Activation row meaning remains unverified; the half-open rule itself is fixed. WAIT during the command ramp is a conservative **proposed protocol decision**, not a source-provided correct-action label.
- **NORMAL_B / PROMOTE-safe:** settled endpoint is **null / NOT IDENTIFIABLE**. After candidate 40 h, label only `POST_RAMP_UNVERIFIED`; never infer settled normal from command completion, finite values, CV, detector score or successful simulation termination.
- **FAULT:** source fault family/presence are identifiable. Conditional onset interpretation is `[30 h, observed_end + dt)`, right-censored at the stream boundary; no recovery is fabricated. Fault-run `tRampSetpoint=1` does not prove a one-hour fault ramp. This audit does not certify profile-row onset semantics.
- **Shutdown:** retain a separate shutdown-censored stratum; exclude it from benign PROMOTE-safe/new-normal-starvation evaluation, never fill observations beyond stop. Exact shutdown-time semantics require source verification.

README identifies production-mode changes separately from programmed faults; inspected completed transition/SP cases have zero fault profiles. This supports a **commanded fault-free transition candidate**, not an unconditional healthy-operation or settled-normal guarantee. In particular, the same class of mode commands also produces emergency shutdowns. Source semantics currently do not justify calling every transition nominal/healthy.

| P7 question | Audit answer |
|---|---|
| Fault poisoning evaluator? | Structurally feasible: fault ID/magnitude/profile and observations exist. Timed poisoning intervals require activation-row and warm-up source verification before execution. |
| New-normal starvation? | **Not yet legally identifiable**: no verified settled-normal/PROMOTE-safe endpoint. No performance metric computed. |
| WAIT during transition? | Proposed conservative WAIT for the metadata ramp; not a learned/source reward claim. |
| PROMOTE after settled Mode B? | Conceptually yes if independently certified settling time exists; none established here. |
| Same initial mode to avoid shortcut? | Yes, four available Mode1 cases; seeds/paths/mode IDs removed from input. |
| Non-oracle policy interface? | Yes, numeric measured/manipulated channels only; evaluator gets profiles/attrs separately. |

## Minimal smoke and Step 2c interface

[Parser](../../../scripts/p10_step2d_tep_inspect.py) reads exactly one transition candidate and one fault observation run. The channel-name vector has 54 entries: Time + **53** original measured/manipulated variables. Additional measurements have 32 channels and are not included in the frozen observation interface.

| Run | processdata | Policy observations | Time range | Sampling |
|---|---|---|---|---|
| Mode1→2,10 h | 2000×54 | 2000×53 | 0.05–100 h | 0.05 h = 3 min |
| IDV1,100%,Run1 | 2001×54 | 2001×53 | 0–100 h | 0.05 h = 3 min |

Both full smoke arrays are finite, strictly ordered and uniformly sampled. Constant observation columns (zero-based after removing Time) **45,49,52** are retained. No interpolation, resampling, normalization or label fitting. `economic_data` is 2001×5 in both cases, while transition additional measurements are 2000×32 and fault additional measurements 2001×32: blindly joining by row index would be unsafe. Each run's actual Time column governs boundaries. Under the **uncertified** 30 h activation interpretation, the first event point is zero-based row 599 in transition and 600 in fault; the candidate 40 h command endpoint is row 799 in transition. No shared hardcoded offset is permitted.

The Step 2c observation arrays accept numeric N×D inputs, but its SMD dataset acquisition/label paths cannot be used directly. Future authorized integration would instantiate dimension-matched random ReLU φ for **53×8=424 input dimensions**, dk=128, seeds 11/22/33, retaining W1/W2 f=.995/W3 β=.1 and the frozen policy. This is shape compatibility only: φ, scaler, τ and memory operators were **not instantiated/run** in this task. A verified normal fit/calibration split is not yet available; test statistics must not fit normalization or thresholds. Physical checkpoint durations also change at 3-min sampling: 256 points = 12.8 h, every128 = 6.4 h; these are protocol costs to review, not permission to tune ages.

Reproduce on `ssh kuo`, from the remote worktree:

```bash
python3 scripts/p10_step2d_tep_inspect.py --raw-dir data/step2d/official \
  --selection research/writable_neural_memory_p10/step2d/selection.json \
  --output research/writable_neural_memory_p10/step2d/inspection.json
python3 -m unittest discover -s tests -p test_p10_step2d_tep.py -v
```

Fresh acquisition prerequisites are official API JSON and README saved under `--raw-dir`, with their version/hash checked against the manifest. The script deliberately has no bulk-download fallback; retained remote cache has block hashes and is checked before reuse. NPZ whole-file hashes are extraction hashes; stable array/timestamp hashes are separately recorded, because NPZ serialization bytes may differ on regeneration. The tracked inspection output stores schema, profiles, attrs, hashes and validation checks, **not observation arrays**.

Verification: **9 tests PASS**, covering exact ranges/cache corruption, refusal of whole-file/wrong-range responses, official URL restriction/budgets, numeric-only input and timestamp validation, half-open onset/end, unknown warm-up/axes/shutdown guards, and selector hash binding. No benchmark metrics, CV distributions or adaptation claims were generated.

## Remaining gates and verdict

Review must resolve: (1) 2021 profile row/activation contract; (2) source-defined warm-up; (3) which commanded transitions qualify as healthy, including shutdown handling; (4) an independent settled-normal endpoint; (5) adequacy of the small unpaired subset / missing second transition before a prospective experiment. Full-file checksum verification remains unavailable under partial acquisition and should be required if complete-file provenance is a future gate.

This completes the authorized **audit**, with concrete negative/unknown findings. Acquisition and parsing work; a complete fault-vs-settled-benign reward/evaluation target is not yet certified. Stop for Issue #15 review; no benchmark or RL advancement.

**TEP_PROTOCOL_PARTIAL**
