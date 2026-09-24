# R0 final red-team (before sealing)

Rule: any unresolved result-affecting issue → `R0_BLOCKED`. Each item below is classified **resolved** (the protocol
or preflight removes it), **scoped** (inherent to the frozen design and carried into the wording) or **disclosed**
(a fixed, result-blind property reported with the results; not a validity defect).

| # | risk | finding | status |
|---|---|---|---|
| 1 | Dataset cherry-picking | The three machines were fixed by the brief with recorded rationale before any R0 model existed; no machine may be added, dropped or replaced; no detector/probe result exists. | resolved |
| 2 | Provenance mismatch | 9/9 files match frozen SHA256 and bytes; every file also re-downloaded from the pinned public URL and matches; machine-1-8 matches the Phase-A seal, machine-2-1 both Phase-A and the feasibility audit, machine-1-4 the feasibility audit. Loaders re-hash on every read. | resolved |
| 3 | Raw/preprocessed substitution | Only OmniAnomaly `.txt` train/test/test_label files; CANDI pickles forbidden and never read; loaders accept only the frozen file names and hashes. Upstream's own value normalisation is outside R0's control and identical for every arm. | resolved |
| 4 | Test-label leakage | Detectors see only the train split; model-facing APIs have no label parameter; labels are purpose-gated and logged; execution seals feature caches before any label read; probe-test labels are read once, after selection and prediction. The model preflight read no label. | resolved |
| 5 | Train normalisation leakage | Scaler uses the fit interval only (verified by replacing all non-fit rows); threshold uses validation windows only and never enters the probe. | resolved |
| 6 | Same-machine supervised leakage | Design B trains and tests each probe on one machine's rows, so it measures within-machine decodability of that machine's anomaly repertoire. Blocks are chronological with a 96-row embargo; no point-anomaly run spans an embargo. Claim is scoped to within-machine; never unseen-machine transfer. | scoped |
| 7 | Overlapping-window leakage | Embargo 96 ≥ complete receptive field 95 (W64 + 31 history rows); verified that no observation, window, history row or window-any label window crosses blocks; no training window straddles train/test or fit/validation. | resolved |
| 8 | Hidden-coordinate alignment | common18 has no raw coordinates and is permutation invariant, but 4/18 statistics are polarity-dependent (exact LSTM sign symmetry; unconstrained in xLSTM) and operating points are instance-specific → Design A rejected, Design B selected. | resolved |
| 9 | D=38 architecture mismatch | D-parameterised builders differ from the sealed D=8 builders only in `features_no`/projection sizes; the three D-dependent xLSTM tensors are identified; observers bind unchanged; observer on/off bitwise and reference-vs-fast parity pass at D=38. Parity must be re-run on every trained checkpoint (execution gate). | resolved (with execution gate) |
| 10 | xLSTM/LSTM capacity mismatch | 75,934 vs 74,100 (−2.415%), nearest width under the repository ±10% rule; R0 does not compare backbones. | resolved |
| 11 | Label/window alignment | Label length = test length for all machines; window-any labels equal brute force; right-edge convention identical for features and labels; warm-up rows excluded identically in both arms. | resolved |
| 12 | Probe-selection leakage | Frozen HGB family (identical to the nonlinear/P1r parameters), grid {100, 300}, validation-only selection, tie → 100, one probe-test evaluation, no refit, no scaler; isolation unit-tested (selection invariant to probe-test labels). | resolved |
| 13 | Overclaiming SMD as benign drift | SMD labels are anomaly/non-anomaly only; no drift labels derived; claim boundary forbids benign-drift, P1r-contradiction, raw-input-information, backbone-superiority and deployment claims. | resolved |
| 14 | Near-constant fit channels | machine-1-4 channel 17 (fit std 1.69e-5) scales to \|x\| ≈ 5.9e4 on test under the sealed zero-std-only rule; scores on that machine may be dominated by one channel. Observed before any model result; keeping the sealed rule avoids a new free parameter; affects H and H+I of the same detector at the input identically; reported beside the detector-sanity table. | disclosed |
| 15 | Few anomaly events per block | Positive rows per block 138–1,518 from 2–8 runs (machine-2-1 probe-train: 2 runs). Probe-test AP rests on few events; uncertainty is exploratory; the wording map requires both resampling intervals and ≥ 7/9 cells. | disclosed |
| 16 | Validation reused for checkpoint selection and threshold | Repository convention (M0); the threshold is diagnostic only, so the probe estimand is unaffected. | resolved |
| 17 | Training/extraction backend difference (xLSTM vanilla vs CUDA overlay) | Validated parity at D=38 (max output \|Δ\| 1.6e-6, common18 3.6e-7); repeated per checkpoint before extraction. | resolved (with execution gate) |
| 18 | Detector-sanity numbers inviting post-hoc choices | Computed only after the probe matrix is sealed; never used to select seeds, backbones, machines or cells; weak detectors (AUROC ≤ 0.55) flagged and retained. | resolved |
| 19 | Execution runner not yet written | The frozen contract (config, data/model/probe library functions, execution order, stop rules) is sealed; the runner must call only these functions and record any deviation in `execution.md`. A runner deviation that changes the contract is a protocol violation, not a design choice. | resolved (procedural) |
| 20 | Engineering side effect | The first preflight attempt ran the sLSTM JIT build in the shared `/tmp/xlstm_cuda_full121_false` directory with a missing header path; that build failed before linking, so the existing `slstm.so` was not replaced, but its `build.ninja` was rewritten and other lines will trigger an automatic rebuild from identical sources on their next load. R0 now uses the dedicated `/tmp/xlstm_cuda_r0_sm121_false`. No R0 or historical result is affected. | disclosed |

No unresolved result-affecting issue remains.

**Status: `R0_READY_FOR_EXECUTION`.**
