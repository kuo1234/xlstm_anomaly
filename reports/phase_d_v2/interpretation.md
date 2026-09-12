# Post-analysis interpretation; no change to decision rules

H1-HARM STOP for the frozen single-update synthetic intervention. None of the
12 c<=20 comparisons reaches the AP loss margin 0.02; all corresponding paired
95% CI upper bounds are below that margin. The largest mean loss is collective
c20, approximately 0.000028 (CI [0.000017,0.000040], Holm p=0.042969,
positive in 5/5 detector seeds and 3/4 scenarios). This is a detectable small
effect, not a practically qualifying effect and not evidence of exactly zero harm.

The intervention also has limited sensitivity/generalizability: spike macro AP
is approximately 0.008, and the fixed-threshold post-shift normal FPR remains
approximately 0.49 after updating. These weak detection/calibration outcomes
must not be presented as evidence that the backbone is robust or that the safe
adaptation problem is solved. No-update versus clean-update AP improvements are
small, and this experiment has only one native SANA optimizer step. It does not
test accumulation over repeated contaminated updates or natural-SMD causal harm.

All conditions, null/negative results, stress-only c30 and no-update controls
remain in decision.md, curves.json and all_results.csv. No result-dependent
rescaling, retuning, extra training or statistical modification was performed.
The practical margin must not be lowered retrospectively. H1-admission remains
GO from C3; H1-harm has not met GO. Return for external review without starting
H4, other models/probes or any additional harm intervention.
