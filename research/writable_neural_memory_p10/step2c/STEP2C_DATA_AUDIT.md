# Step 2c-A — Data / label exposure audit

2026-10-04; base `65c0ed9d010a79894528d1f653dfee7ec238ad44`, branch `research/p7-p10-segment-memory`.
Authorized by [Issue #15 review 5975468315](https://github.com/kuo1234/xlstm_anomaly/issues/15#issuecomment-5975468315) and the owner's detailed Step 2c task.
This is a static repository/history audit before **new Step 2c evaluation label access**. Historical reports already disclose label-derived values; reviewing them does not make the source unexposed. `unknown` means no affirmative evidence was located; it is not a proof of nonaccess.

## Search coverage and evidence

[exposure_evidence_index.json](exposure_evidence_index.json) inventories matching tracked research reports, results, scripts, tests, README and relevant all-ref commit history. Binary result traces are not evidence of raw label reads by themselves. The substantive records inspected were:

- `research/m1_reproducibility_redteam_2026q3/data_leakage_audit.md`: all 84 SMD train/test/label files acquired, all 28 vectors parsed; all-machine prevalence and contiguous-run inventory. The later `other_19_unopened` flag describes one evaluator pass, not project history.
- Historical `44b5c05:research/adaptive_normality_m1_smd/dataset_manifest.md`, `f7dd019:research/adaptive_normality_m1_smd/stage1a_machines.json` and `stage1a_futility_amendment.md`: train-row/name selection, no label selection in that screen; selected nine had subsequent metric evaluation (`2792b1e`, `f7dd019`). These historical files are no longer at their original HEAD paths.
- `reports/phase_a/downloads.json`, `scripts/phase_a_fetch.py`, `phase_a_audit.py`: original observation acquisition and two anchor labels; TSB archive labels were inspected but source provenance unresolved.
- `research/real_data_r0/dataset_manifest.json`, `runs/probe_label_access_log.json`, protocol and amendments: 1-4/1-8/2-1 label-consuming evaluation after feature seal. `2842198`, `b55eacc`, `4bb2b5b` record that chronology.
- Step 2a/2b reports, configs, runners, evaluators, result tables and access logs: 1-6/2-7/3-7 development exposure; Step 2b CV threshold was explicitly chosen from development labels (`0d0c4f1`, `65c0ed9`).
- `research/real_data_feasibility/{datasets.json,acquisition_status.md,provenance.md,label_semantics.md}` (`8f6ee87`); `scripts/real_data_acquire.py`, `real_data_inspect.py` and tests: AnDri IoT CSV bytes and point/onset contents inspected; HAI LFS acquisition absent; SWaT access gated.
- `research/new_normal_dataset_audit/` (`f71a250`, subsequently archived/consolidated), `research/adaptive_normality_xlstm/dataset_audit.md`, root/research README: source-level distinction between benign drift and attack; E-Energy 1,200-byte CSV range probe, no full datasets; PreDist README intervals; extended TEP schema unverified.

No independent OS-wide historical file-open log exists. Logs attest to their own runs only. Claims below therefore use affirmative recorded exposure or `unknown`, never global untouched status.

## Candidate audit

| Candidate | Raw observations previously acquired? | Actual program label reads / exposure level | Label-based selection history | Normal train | Fault / anomaly truth | Legitimate benign transition truth | Suitable estimands / claim |
|---|---|---|---|---|---|---|---|
| All 25 SMD machines outside Step 2a/2b | Yes, all 28 historically acquired | **Yes, point vectors parsed**; prevalence and run counts published | M1 screen documented train-row/name selection; other unrecorded selection `unknown`; no Step 2b feature/rule development on these 25 | Source-designated train, no independent train labels | Binary test anomaly labels; equipment fault identity not specified | **No** | Anomaly rejection / contamination only; new-normal and drift-vs-fault NOT EVALUABLE; **frozen exploratory machine-transfer** |
| HAI 22.04 | No true CSV acquired in recorded audit | No affirmative actual CSV-label read; attack metadata described. Current runtime `git lfs version` fails (not a git command) | None recorded / outside-repo unknown | Official normal train files | Official `Attack` flags, staged attack domain | No verified safe-transition annotation | **BLOCKED** acquisition. If later properly acquired: **external industrial attack-domain robustness** only |
| AnDri Sensor real IoT 1/2 | Yes; bytes compared to upstream | **Yes**, `anomaly_point`, `anomaly_pattern`, `change_point` contents inspected | Feasibility audit examined onset indices and anomaly composition; not clean holdout | No fixed independently normal train split established | Paper-asserted anomaly point/pattern flags | Sparse onset markers only, no approved stable-new-regime intervals; irregular cadence | Not compatible with frozen train/calibration/safe-transition protocol; future **frozen exploratory transfer** only after separate split protocol, not strict confirmatory |
| AnDri Climate / Traffic / SMD / SWaT derivatives | Inventory/schema described; full local acquisition not established | Metadata/rule-derived semantics inspected; exact point read history unknown except IoT | No documented policy selection, unknown otherwise | Dataset-dependent, unverified | Climate threshold / Traffic EWMA-calendar rules; SMD anomaly and SWaT attack derivatives | **No verified independently approved shift truth** | At most external robustness after provenance/split audit; derivatives not replacements for official SWaT |
| TSB / StrAD CD candidates | Yes, historical archive acquisition | **Yes**, labels parsed in Phase A candidate audit | Eligibility uses labels to verify normal prefix; source assignment constraints; historical STOP | Candidate prefixes tested | Binary benchmark labels; source identity unresolved for many | Series-level CD/type tags, **not interval benign truth** | Historical provenance STOP remains; not admitted to Step 2c |
| E-Energy smart buildings | Only 1,200-byte range probe previously; no full files | Three-class semantics and counts described; range contains example rows, so possible point exposure; no full-label parser documented | Historical source choice based on semantic suitability, not this policy; complete point history unknown | Paper describes 5,000 normal samples, frozen observation-only normal prefix not established | Control-logic attacks, label 2 | Paper distinguishes normal drift label 1; episode endpoints/settled regimes not independently verified | Closest semantic lead, but **not a proven unexposed, protocol-compatible Priority A set**; unresolved license/split, frozen exploratory only under a separately reviewed data protocol |
| PreDist v2 | Archive not acquired in recorded audit | README **interval metadata** (normal events / fault records) inspected, raw point contents not recorded | No policy development documented | Recommended ranges described, per-file completeness unverified | Incident records with uncertain onsets / missing reports | Normal-event intervals do not establish every unlabeled change as approved new normal | Promising external lead; concrete safe-transition/train schema not verified, **unknown** confirmatory eligibility; no substitution this run |
| Extended TEP / DTU | No 132.96 GB HDF5 acquired; README request 403 | Scenario metadata only, point labels unknown | None recorded | Normal reference scenarios described, aligned arrays unverified | Simulated process faults | Mode/setpoint scenarios described; exact in-stream ground truth unverified | Acquisition/schema unresolved; no verified Priority A stream, simulated robustness only if separately established |
| SWaT official Dec-2015 physical | **No**, access-restricted original files absent | Official attack metadata described; actual original vector reads not recorded | No Step 2b selection; derivatives excluded | Official normal run | Attack annotations | No verified benign transition truth | **BLOCKED — iTrust authorization/package required**; do not bypass, use mirrors, or substitute July-2019 derivatives |

## Individual SMD exposure and selection

Every machine below has historical **raw yes / point label read yes / source normal train yes / anomaly truth yes / benign truth no**. All are unsuitable for strict confirmatory claims. No per-machine label prevalence, episode durations, or detector scores enter this selection.

| Group | Excluded Step 2a/2b development | Other historical anchors excluded by this selection rule | Step 2c selected | Other audited machines, not run |
|---|---|---|---|---|
| 1 | 1-6 | 1-4, 1-8 | **1-1, 1-2, 1-3** | 1-5, 1-7 |
| 2 | 2-7 | 2-1 | **2-2, 2-3, 2-4** | 2-5, 2-6, 2-8, 2-9 |
| 3 | 3-7 | — | **3-1, 3-2, 3-3** | 3-4, 3-5, 3-6, 3-8, 3-9, 3-10, 3-11 |

Rule: exclude development IDs plus existing 1-4/1-8/2-1 anchors, choose first three numeric machine IDs per source group. 9 complete test streams, no cropping, no screening all 28 and retaining successes. 1-3/2-4/3-2 also participated in older M1 outcome evaluation, which further reinforces exploratory status; this is not Step 2b policy selection. Source groups are not proof of independence of physical installations; machine is the available entity unit, source dependencies unknown.

## Acquisition and decision

- SMD observations: official [OmniAnomaly pinned commit](https://github.com/NetManAIOps/OmniAnomaly/tree/7fb0e0acf89ea49908896bcc9f9e80fcfff6baf4/ServerMachineDataset). Retain source row/channel order, acquire only `train`/`test` preseal, raw files under ignored `data/step2c/observations/`; hash/shape/constant-channel inventory in `dataset_manifest.json`. Labels downloaded from the **same commit only after pushed seal**.
- HAI official [repository](https://github.com/icsdataset/hai), pinned `2a814cebc9a66b06c9e5cd545e2d72e65d383737`: Git LFS unavailable on this host at audit time → **BLOCKED**. No pointer is treated as observations; no Kaggle/fork fallback. Official release is attack-centric, not certified benign-drift truth.
- SWaT: use [iTrust request route](https://itrust.sutd.edu.sg/itrust-labs_datasets/) only; raw currently unavailable → **BLOCKED**.

**Priority A not established in the repo candidates. Proceed Priority B (9 SMD machines). Priority C secondary HAI BLOCKED. Strict confirmatory validation remains unavailable. New-normal promotion not identifiable from source labels.** Frozen policies can transfer-test anomaly safety and generic nonanomaly FPR, but cannot fully validate the stabilisation-to-approved-new-normal hypothesis.
