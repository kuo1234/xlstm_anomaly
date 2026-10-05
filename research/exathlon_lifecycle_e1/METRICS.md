# Frozen primary metrics and gates

RCI=[start,end], EEI=(end,effect_end], pre/recovery300s. Unknown, point, crash descriptors, no-impact CPU and missing EEI stay excluded/secondary. Other event supports are removed from unique attribution. Native missing targets remain N/A; no interval widening.

Z_RCI=(medianRCI−medianpre)/IQR_normal_cal; Z_EEI=(medianEEI−medianpre)/IQR_normal_cal; Delta_effect=Z_EEI−Z_RCI. Degenerate IQR→N/A. Raw eligibility and1IQR material margin are in [protocol](configs/protocol.json). No p-value/significance claim. Event medians aggregate first by trace; retain type/app counts and shared-run dependence.

Effect-only: no eligible RCI alarm plus>=1 EEI alarm, only complete expected native RCI score coverage; otherwiseN/A. Root observed alarms and alarm-time fractions remain descriptive under incomplete support. Delay requires complete native RCI/EEI and no overlap. Threshold normal-calibration q.995, linear; app-normal thresholds secondary, deployment app ID known. No per-trace oracle or test-label tuning.

Heldout-normal controls preserve each event’s RCI/EEI durations with300s pre:10 equally spaced placements per heldout trace when available, no score-based selection, overlapping controls are not independent samples. Same-trace pre-controls end301s before event, exclude labeled contamination. No-impact post60s is explicitly pseudo-effect, not missing GT EEI fabricated. Crash only tests censoring.

Controls, normalFPR, raw continuity, fragments, dropout/alarm fraction and duration-matched observed capture are all reported. Frozen gate prioritizes execution/resolution; threshold-only excess before no-gap; then model-specific, context confounds, and positive corroboration. Context verdict describes confounding, not a causal proof. Positive mechanism gate never authorizes novelty or method design.
