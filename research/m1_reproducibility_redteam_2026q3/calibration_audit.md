# Calibration and model-integrity audit

**Scope:** static review of the frozen protocol, source, and committed audit reports at AUDITED_M1_SHA. No labels, model forwards, training, or tests were run by this audit.

## Verdict

**PASS for the default calibration and fixed fusion design.** The code uses train-only fit/validation/calibration partitions, derives tail references and thresholds from disjoint halves of the train calibration block, uses q=0.99 with method higher, and keeps test labels out of calibration.

**DOCUMENTATION_ONLY:** parameter counts are internally consistent, but the claim that width 40 is the nearest width in a configured search range is not reproducible because the range is not recorded.

## Calibration boundaries and threshold rule

Train-relative blocks are [0,70%), [70%,85%), and [85%,100%); the robust transform uses the fit block only. Evidence: scripts/adaptive_normality_m1_data.py:233-275 and research/adaptive_normality_m1_smd/protocol.md:19-35.

Stage-1A uses the three cheap controls (last-value, moving median, and VAR(1)), xLSTMAD-F, and diagnostic LSTM-F. Its first calibration half supplies tail references for the three cheap controls and xLSTMAD-F; the second half supplies raw threshold samples for the five raw scores and both fixed fusions. The cheap fusion is the maximum of the three cheap-control severities; the forecast-plus-cheap fusion adds xLSTMAD-F. LSTM-F receives its own raw-score threshold and does not enter either fusion. Evidence: scripts/adaptive_normality_m1_stage1a.py:293-323; constants and inventories at lines 46-55.

For the full M1 score inventory, calibration_fusions() instead uses five controls (the three cheap controls plus R-native-window and R-endpoint) and xLSTMAD-F for tail references, while retaining LSTM-F as a raw score with its own threshold. It makes the control-only and forecast-plus-control max fusions. Evidence: scripts/adaptive_normality_m1_execute.py:435-498. The Stage1B-R integration reuses the Stage-1A references for non-R arms, fits R references from the first half, and freezes full score thresholds from the second half. Evidence: scripts/adaptive_normality_m1_stage1b_r.py:150-203, 454-483.

The threshold function calls NumPy quantile with method higher. Stage-1A validation recomputes q=.99 thresholds and verifies half boundaries and tail-reference hashes. Evidence: scripts/adaptive_normality_m1_scores.py:135-150; scripts/adaptive_normality_m1_stage1a.py:196-226, 229-290. Stage1B-R has equivalent checks for its full inventory at scripts/adaptive_normality_m1_stage1b_r.py:454-483.

Tail severity is computed against a frozen first-half empirical normal reference using the upper-tail count; there is no learned fusion weight. Evidence: scripts/adaptive_normality_m1_scores.py:143-191.

## Model integrity and capacity

The frozen baseline specification separates current xLSTMAD-R reconstruction from the historical xLSTMAD-F forecasting architecture and states each objective and input behavior. Evidence: research/adaptive_normality_m1_smd/baseline_spec.md:25-54.

The committed constructor/count audit reports 80,510 parameters for xLSTMAD-F and 81,838 for M1 LSTM-F, a 1.65% difference inside the frozen ±10% criterion. The count formula is 48w² + 125w + 38 for D=38 and w=40. Reported xLSTMAD-R count is 75,934. Evidence: research/adaptive_normality_m1_smd/baseline_spec.md:42-54 and research/adaptive_normality_m1_smd/forecasting_implementation_audit.md:50-63.

The historical parity evidence is limited: the implementation report describes loading the historical class from a pinned Git object, loading the same state dict into both implementations, and checking exact output parity on a synthetic p=1 forward path. The report also states no per-window normalization and fresh state. This supports that constructor/forward path, not identical training dynamics, multi-step behavior, backend determinism, or all inputs. This red-team audit did not rerun parity.

Fresh-window behavior is consistent with the protocol’s independent-window rule. The LSTM decoder and xLSTM implementation report reset/zero state per window, and protocol says no state is carried between windows. This was statically reviewed only.

## Documentation gap

baseline_spec.md:46 says width 40 is “the nearest width in the configured search range.” The document does not declare that range, and source inspection found no frozen width-search list. The formula and count can be independently recomputed and width satisfies ±10%; the missing search-range rationale is therefore a documentation/reproducibility issue, not evidence the capacity gate failed.

## Assumptions and limits

The protocol assumes train normality under benchmark convention because there is no train-label file. That assumption affects the interpretation of calibration false-positive thresholds and is not independently established row by row.

No unit or integration tests were run. Calibration correctness here means source and committed artifact checks match the frozen design by static inspection, not a new execution-level reproduction.
