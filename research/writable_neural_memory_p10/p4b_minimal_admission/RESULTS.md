# P4-B results

**ADAPTATION_HARMS_RETENTION** — STOP after Issue #18 review. No Q met the joint safe-delay gate.

This minimal deterministic rank2 linearAE pilot tests candidate/sample selection under a shared decoder SGD operator, not official M2N2/CANDI performance or universal admission safety. All135 trajectories completed; no architecture/Q/schedule/threshold rescue. Scientific N=5 physical groups; one deterministic fit per group, not135 independent samples.

## Main result

Q1 is exactly immediate mutation with a formal endpoint name. It accepts clean settled-B before censor in5/5 groups (latencies18,7,1,3,7; median7), but does not reduce stationary anomaly FAR (both1.0). At the pre-first-anomaly snapshot, oldA probe FPR increases .2051–.2617 above initial. Same-commit deltas are small because earlier/ongoing updates already damage A; initial-vs-horizon comparison was frozen prospectively to avoid hiding cumulative harm.

Q64/128/256/512 have0/5 valid benign acceptance before firstB anomaly. Q64 blocks stationary anomaly writes completely, but also makes no stationary writes at all; zero-write is not adaptation success. Its five late promotions are on actual B anomalies, not settled-B acceptance. LargerQ families never mutate any stream. No post-hoc shorter/intermediateQ family added.

Frozen preanomaly cleanB FPR is .3828–.5078: new-normal false-alarm problem is expressed. Immediate/Q1 and M2N2-style reduce it on all five groups but harm oldA; CANDI-style has only small B utility with this fixed bottleneck/reference geometry. Event recall remains1.0, while point recall and written fractions show extensive fault assimilation. High event recall does not certify safe normality.

## All-policy Pareto table

Macro values across5 groups, with paired variants retained. Formal coverage/TTA for native-style no-commit arms are N/A_NATIVE; first effective exposure is separate. All-strata FAR includes benign2+stationary2+twin1 negative episodes per group (25 opportunities per policy), not independent repeated checkpoints.

| Policy | Valid coverage | Median TTA | B FPR preanomaly | Stationary FAR | Twin FAR | All-strata FAR | B event / point recall | OldA FPR delta preanomaly |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| FROZEN | 0.0000 | N/A | 0.4320 | 0.0000 | 0.0000 | 0.0000 | 1.0000 / 0.5531 | 0.0000 |
| IMMEDIATE_UPDATE | N/A_NATIVE | N/A | 0.1516 | 1.0000 | 1.0000 | 1.0000 | 1.0000 / 0.1622 | 0.2234 |
| M2N2_STYLE_CAUSAL | N/A_NATIVE | N/A | 0.1773 | 1.0000 | 1.0000 | 1.0000 | 1.0000 / 0.1450 | 0.1586 |
| CANDI_STYLE_CAUSAL | N/A_NATIVE | N/A | 0.4195 | 1.0000 | 1.0000 | 0.6400 | 1.0000 / 0.5166 | 0.0016 |
| QUARANTINE_1 | 1.0000 | 7.0000 | 0.1516 | 1.0000 | 1.0000 | 1.0000 | 1.0000 / 0.1622 | 0.2234 |
| QUARANTINE_64 | 0.0000 | N/A | 0.4320 | 0.0000 | 1.0000 | 0.4000 | 1.0000 / 0.4566 | 0.0000 |
| QUARANTINE_128 | 0.0000 | N/A | 0.4320 | 0.0000 | 0.0000 | 0.0000 | 1.0000 / 0.5531 | 0.0000 |
| QUARANTINE_256 | 0.0000 | N/A | 0.4320 | 0.0000 | 0.0000 | 0.0000 | 1.0000 / 0.5531 | 0.0000 |
| QUARANTINE_512 | 0.0000 | N/A | 0.4320 | 0.0000 | 0.0000 | 0.0000 | 1.0000 / 0.5531 | 0.0000 |

Coverage0, latency N/A for FROZEN or unreleasedQ means censored failure, not instantaneous successful acceptance. Q64 later all-cleanB FPR may improve after writing anomalous data: this is excluded from preanomaly adaptation utility, not called benign success.

## Contamination / ledger and duration evidence

| Policy | Stationary short / long admitted (each /5) | Stationary mutations | All-strata unique negative purity | Weighted negative exposure fraction | Twin fault PROMOTE count | Premature / invalid benign PROMOTE |
|---|---:|---:|---:|---:|---:|---:|
| FROZEN | 0 / 0 | 0 | N/A | N/A | 0 | 0 / 0 |
| IMMEDIATE_UPDATE | 5 / 5 | 615 | 0.5734 | 0.5734 | 0 | 0 / 0 |
| M2N2_STYLE_CAUSAL | 5 / 5 | 21980 | 0.3718 | 0.3718 | 0 | 0 / 0 |
| CANDI_STYLE_CAUSAL | 5 / 5 | 783 | 0.1061 | 0.1061 | 0 | 0 / 0 |
| QUARANTINE_1 | 5 / 5 | 615 | 0.5734 | 0.5734 | 750 | 52 / 210 |
| QUARANTINE_64 | 0 / 0 | 0 | 1.0000 | 1.0000 | 5 | 0 / 5 |
| QUARANTINE_128 | 0 / 0 | 0 | N/A | N/A | 0 | 0 / 0 |
| QUARANTINE_256 | 0 / 0 | 0 | N/A | N/A | 0 | 0 / 0 |
| QUARANTINE_512 | 0 / 0 | 0 | N/A | N/A | 0 | 0 / 0 |

Purity and weighted fraction have different denominators: unique effective IDs versus all nonzero optimization weights. Selected/pending not written. No-write purity=N/A. Native arms have zero formal PROMOTE count but can still admit negative data through parameter updates; FAR measures actual mutation, not endpoint labels.

Stationary long faults do not produce64 consecutive high-score points under this bottleneck, despite lasting512 samples. No claim that Q64 validates a legitimate regime: it filters uninterrupted alarm runs. UnderB, actual anomalies do yield long enough runs to triggerQ64 in5/5; retain both strata. Scores are mutable common-model outputs, not oracle segment truth.

## Frozen gate checks

| Q | Coverage | Median latency | Stationary FAR reduction | Improved physical groups | Max event recall drop | Max oldA FPR deterioration | All criteria |
|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 1.0000 | 7.0000 | 0.0000 | 0 | 0.0000 | 0.2617 | False |
| 64 | 0.0000 | N/A | 1.0000 | 5 | N/A | N/A | False |
| 128 | 0.0000 | N/A | 1.0000 | 5 | N/A | N/A | False |
| 256 | 0.0000 | N/A | 1.0000 | 5 | N/A | N/A | False |
| 512 | 0.0000 | N/A | 1.0000 | 5 | N/A | N/A | False |

Stationary-FAR criterion is false forQ≥64 despite lower FAR because stationary writes=0. Retention checks requiring valid acceptance remain N/A/failed when coverage0, not interpreted as perfect retention. Verdict priority was frozen before fits (PROTOCOL/config). This supports neither useful safe delay nor a universally necessary adaptation-harm conclusion beyond this operator.

## Every benign physical group

| Group | Policy | Preanomaly B FPR | Valid commit / TTA | First B write / wholly cleanB write | Transition alarms / clean points (corrected endpoint) | Recovery confirmation | OldA preanomaly delta |
|---|---|---:|---|---|---|---|---:|
| 101 | FROZEN | 0.4180 | None / None (CENSORED) | None / None | 363 / 1024 | CENSORED | 0.0000 |
| 101 | IMMEDIATE_UPDATE | 0.1289 | None / None (N/A_NATIVE) | 2104 / 2304 | 159 / 1024 | CENSORED | 0.2246 |
| 101 | M2N2_STYLE_CAUSAL | 0.1797 | None / None (N/A_NATIVE) | 2048 / 2310 | 188 / 1024 | CENSORED | 0.1465 |
| 101 | CANDI_STYLE_CAUSAL | 0.4062 | None / None (N/A_NATIVE) | 2055 / 2496 | 359 / 1024 | CENSORED | 0.0020 |
| 101 | QUARANTINE_1 | 0.1289 | 2322 / 18 (VALID) | 2104 / 2304 | 0 / 56 | CENSORED | 0.2246 |
| 101 | QUARANTINE_64 | 0.4180 | None / None (CENSORED) | 3135 / None | 363 / 1024 | CENSORED | 0.0000 |
| 101 | QUARANTINE_128 | 0.4180 | None / None (CENSORED) | None / None | 363 / 1024 | CENSORED | 0.0000 |
| 101 | QUARANTINE_256 | 0.4180 | None / None (CENSORED) | None / None | 363 / 1024 | CENSORED | 0.0000 |
| 101 | QUARANTINE_512 | 0.4180 | None / None (CENSORED) | None / None | 363 / 1024 | CENSORED | 0.0000 |
| 202 | FROZEN | 0.5078 | None / None (CENSORED) | None / None | 419 / 1024 | CENSORED | 0.0000 |
| 202 | IMMEDIATE_UPDATE | 0.1484 | None / None (N/A_NATIVE) | 2228 / 2375 | 172 / 1024 | CENSORED | 0.2051 |
| 202 | M2N2_STYLE_CAUSAL | 0.1211 | None / None (N/A_NATIVE) | 2112 / 2368 | 150 / 1024 | CENSORED | 0.2891 |
| 202 | CANDI_STYLE_CAUSAL | 0.4883 | None / None (N/A_NATIVE) | 2131 / 2544 | 407 / 1024 | CENSORED | 0.0020 |
| 202 | QUARANTINE_1 | 0.1484 | 2375 / 7 (VALID) | 2228 / 2375 | 0 / 116 | CENSORED | 0.2051 |
| 202 | QUARANTINE_64 | 0.5078 | None / None (CENSORED) | 3186 / None | 419 / 1024 | CENSORED | 0.0000 |
| 202 | QUARANTINE_128 | 0.5078 | None / None (CENSORED) | None / None | 419 / 1024 | CENSORED | 0.0000 |
| 202 | QUARANTINE_256 | 0.5078 | None / None (CENSORED) | None / None | 419 / 1024 | CENSORED | 0.0000 |
| 202 | QUARANTINE_512 | 0.5078 | None / None (CENSORED) | None / None | 419 / 1024 | CENSORED | 0.0000 |
| 303 | FROZEN | 0.4688 | None / None (CENSORED) | None / None | 402 / 1024 | CENSORED | 0.0000 |
| 303 | IMMEDIATE_UPDATE | 0.1875 | None / None (N/A_NATIVE) | 1922 / 2177 | 188 / 1024 | CENSORED | 0.2617 |
| 303 | M2N2_STYLE_CAUSAL | 0.2227 | None / None (N/A_NATIVE) | 1920 / 2176 | 222 / 1024 | CENSORED | 0.1406 |
| 303 | CANDI_STYLE_CAUSAL | 0.4609 | None / None (N/A_NATIVE) | 1943 / 2567 | 400 / 1024 | CENSORED | 0.0039 |
| 303 | QUARANTINE_1 | 0.1875 | 2177 / 1 (VALID) | 1922 / 2177 | 0 / 2 | CENSORED | 0.2617 |
| 303 | QUARANTINE_64 | 0.4688 | None / None (CENSORED) | 3005 / None | 402 / 1024 | CENSORED | 0.0000 |
| 303 | QUARANTINE_128 | 0.4688 | None / None (CENSORED) | None / None | 402 / 1024 | CENSORED | 0.0000 |
| 303 | QUARANTINE_256 | 0.4688 | None / None (CENSORED) | None / None | 402 / 1024 | CENSORED | 0.0000 |
| 303 | QUARANTINE_512 | 0.4688 | None / None (CENSORED) | None / None | 402 / 1024 | CENSORED | 0.0000 |
| 404 | FROZEN | 0.3828 | None / None (CENSORED) | None / None | 347 / 1024 | CENSORED | 0.0000 |
| 404 | IMMEDIATE_UPDATE | 0.1406 | None / None (N/A_NATIVE) | 2280 / 2499 | 167 / 1024 | CENSORED | 0.2051 |
| 404 | M2N2_STYLE_CAUSAL | 0.1953 | None / None (N/A_NATIVE) | 2240 / 2496 | 208 / 1024 | CENSORED | 0.1016 |
| 404 | CANDI_STYLE_CAUSAL | 0.3750 | None / None (N/A_NATIVE) | 2253 / 2766 | 342 / 1024 | CENSORED | 0.0000 |
| 404 | QUARANTINE_1 | 0.1406 | 2499 / 3 (VALID) | 2280 / 2499 | 0 / 40 | CENSORED | 0.2051 |
| 404 | QUARANTINE_64 | 0.3828 | None / None (CENSORED) | 3357 / None | 347 / 1024 | CENSORED | 0.0000 |
| 404 | QUARANTINE_128 | 0.3828 | None / None (CENSORED) | None / None | 347 / 1024 | CENSORED | 0.0000 |
| 404 | QUARANTINE_256 | 0.3828 | None / None (CENSORED) | None / None | 347 / 1024 | CENSORED | 0.0000 |
| 404 | QUARANTINE_512 | 0.3828 | None / None (CENSORED) | None / None | 347 / 1024 | CENSORED | 0.0000 |
| 505 | FROZEN | 0.3828 | None / None (CENSORED) | None / None | 368 / 1024 | CENSORED | 0.0000 |
| 505 | IMMEDIATE_UPDATE | 0.1523 | None / None (N/A_NATIVE) | 2080 / 2279 | 172 / 1024 | CENSORED | 0.2207 |
| 505 | M2N2_STYLE_CAUSAL | 0.1680 | None / None (N/A_NATIVE) | 2016 / 2272 | 190 / 1024 | CENSORED | 0.1152 |
| 505 | CANDI_STYLE_CAUSAL | 0.3672 | None / None (N/A_NATIVE) | 2046 / 2590 | 355 / 1024 | CENSORED | 0.0000 |
| 505 | QUARANTINE_1 | 0.1523 | 2279 / 7 (VALID) | 2080 / 2279 | 0 / 64 | CENSORED | 0.2207 |
| 505 | QUARANTINE_64 | 0.3828 | None / None (CENSORED) | 3156 / None | 368 / 1024 | CENSORED | 0.0000 |
| 505 | QUARANTINE_128 | 0.3828 | None / None (CENSORED) | None / None | 368 / 1024 | CENSORED | 0.0000 |
| 505 | QUARANTINE_256 | 0.3828 | None / None (CENSORED) | None / None | 368 / 1024 | CENSORED | 0.0000 |
| 505 | QUARANTINE_512 | 0.3828 | None / None (CENSORED) | None / None | 368 / 1024 | CENSORED | 0.0000 |

Reporting correction: raw frozen metrics had five negative-duration Q1 burden intervals because first global PROMOTE occurred in A before transition. Those raw values remain in metrics.json; reporting_boundary_correction.json uses the first formal endpoint at/after transition, censors/clips empty intervals, and separately reports burden through valid B commit. No model/policy/gate rerun or cutoff change. Q1 has12 pre-transitionA formal endpoints and40 transition-premature endpoints; the original52 early count combines both. The above formal-burden zero forQ1 is until the first in-transition alarm/commit (exclusive), not zero transition false alarms. Through valid B commit there are46/41/40/39/36 alarms in274/263/257/259/263 clean points. Both endpoint choices are disclosed; this metric correction has no role in the frozen final gate.

Recovery is three original-timeline64-point blocks FPR≤.10,≥32 clean each, censored at firstB anomaly. It is not acceptance. METRICS/config give exact endpoints and valid-payload rules. Formal first commit can be premature/invalid even if a later new candidate has valid current-only payload; both counted.

## All135 trajectory outcomes

| Group | Stratum | Policy | FAR | Purity | Weighted contamination | Updates / selected / optimization IDs | Formal PROMOTE / invalid | Event / point recall |
|---|---|---|---:|---:|---:|---|---|---|
| 101 | benign_B_with_anomalies | FROZEN | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.5563 |
| 101 | benign_B_with_anomalies | IMMEDIATE_UPDATE | 1.0000 | 0.1985 | 0.1985 | 544 / 544 / 544 | 0 / 0 | 1.0000 / 0.1688 |
| 101 | benign_B_with_anomalies | M2N2_STYLE_CAUSAL | 1.0000 | 0.1360 | 0.1360 | 4038 / 4038 / 4038 | 0 / 0 | 1.0000 / 0.1422 |
| 101 | benign_B_with_anomalies | CANDI_STYLE_CAUSAL | 0.0000 | 0.0000 | 0.0000 | 45 / 740 / 720 | 0 / 0 | 1.0000 / 0.4844 |
| 101 | benign_B_with_anomalies | QUARANTINE_1 | 1.0000 | 0.1985 | 0.1985 | 544 / 544 / 544 | 156 / 42 | 1.0000 / 0.1688 |
| 101 | benign_B_with_anomalies | QUARANTINE_64 | 0.5000 | 1.0000 | 1.0000 | 17 / 17 / 17 | 1 / 1 | 1.0000 / 0.4656 |
| 101 | benign_B_with_anomalies | QUARANTINE_128 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.5563 |
| 101 | benign_B_with_anomalies | QUARANTINE_256 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.5563 |
| 101 | benign_B_with_anomalies | QUARANTINE_512 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.5563 |
| 101 | stationary_A_with_anomalies | FROZEN | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2437 |
| 101 | stationary_A_with_anomalies | IMMEDIATE_UPDATE | 1.0000 | 0.4553 | 0.4553 | 123 / 123 / 123 | 0 / 0 | 1.0000 / 0.0875 |
| 101 | stationary_A_with_anomalies | M2N2_STYLE_CAUSAL | 1.0000 | 0.1290 | 0.1290 | 4427 / 4427 / 4427 | 0 / 0 | 1.0000 / 0.1078 |
| 101 | stationary_A_with_anomalies | CANDI_STYLE_CAUSAL | 1.0000 | 0.0258 | 0.0258 | 143 / 2306 / 2288 | 0 / 0 | 1.0000 / 0.2281 |
| 101 | stationary_A_with_anomalies | QUARANTINE_1 | 1.0000 | 0.4553 | 0.4553 | 123 / 123 / 123 | 44 / 44 | 1.0000 / 0.0875 |
| 101 | stationary_A_with_anomalies | QUARANTINE_64 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2437 |
| 101 | stationary_A_with_anomalies | QUARANTINE_128 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2437 |
| 101 | stationary_A_with_anomalies | QUARANTINE_256 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2437 |
| 101 | stationary_A_with_anomalies | QUARANTINE_512 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2437 |
| 101 | semantic_fault_twin | FROZEN | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4226 |
| 101 | semantic_fault_twin | IMMEDIATE_UPDATE | 1.0000 | 0.9982 | 0.9982 | 544 / 544 / 544 | 0 / 0 | 1.0000 / 0.1326 |
| 101 | semantic_fault_twin | M2N2_STYLE_CAUSAL | 1.0000 | 0.8764 | 0.8764 | 4038 / 4038 / 4038 | 0 / 0 | 1.0000 / 0.1360 |
| 101 | semantic_fault_twin | CANDI_STYLE_CAUSAL | 1.0000 | 0.6042 | 0.6042 | 45 / 740 / 720 | 0 / 0 | 1.0000 / 0.3940 |
| 101 | semantic_fault_twin | QUARANTINE_1 | 1.0000 | 0.9982 | 0.9982 | 544 / 544 / 544 | 156 / 156 | 1.0000 / 0.1326 |
| 101 | semantic_fault_twin | QUARANTINE_64 | 1.0000 | 1.0000 | 1.0000 | 17 / 17 / 17 | 1 / 1 | 1.0000 / 0.3440 |
| 101 | semantic_fault_twin | QUARANTINE_128 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4226 |
| 101 | semantic_fault_twin | QUARANTINE_256 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4226 |
| 101 | semantic_fault_twin | QUARANTINE_512 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4226 |
| 202 | benign_B_with_anomalies | FROZEN | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.7719 |
| 202 | benign_B_with_anomalies | IMMEDIATE_UPDATE | 1.0000 | 0.2091 | 0.2091 | 483 / 483 / 483 | 0 / 0 | 1.0000 / 0.1578 |
| 202 | benign_B_with_anomalies | M2N2_STYLE_CAUSAL | 1.0000 | 0.1337 | 0.1337 | 4158 / 4158 / 4158 | 0 / 0 | 1.0000 / 0.1313 |
| 202 | benign_B_with_anomalies | CANDI_STYLE_CAUSAL | 0.5000 | 0.0011 | 0.0011 | 56 / 898 / 896 | 0 / 0 | 1.0000 / 0.7453 |
| 202 | benign_B_with_anomalies | QUARANTINE_1 | 1.0000 | 0.2091 | 0.2091 | 483 / 483 / 483 | 133 / 36 | 1.0000 / 0.1578 |
| 202 | benign_B_with_anomalies | QUARANTINE_64 | 0.5000 | 1.0000 | 1.0000 | 9 / 9 / 9 | 1 / 1 | 1.0000 / 0.6734 |
| 202 | benign_B_with_anomalies | QUARANTINE_128 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.7719 |
| 202 | benign_B_with_anomalies | QUARANTINE_256 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.7719 |
| 202 | benign_B_with_anomalies | QUARANTINE_512 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.7719 |
| 202 | stationary_A_with_anomalies | FROZEN | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2359 |
| 202 | stationary_A_with_anomalies | IMMEDIATE_UPDATE | 1.0000 | 0.5109 | 0.5109 | 92 / 92 / 92 | 0 / 0 | 1.0000 / 0.0734 |
| 202 | stationary_A_with_anomalies | M2N2_STYLE_CAUSAL | 1.0000 | 0.1356 | 0.1356 | 4475 / 4475 / 4475 | 0 / 0 | 0.5000 / 0.0516 |
| 202 | stationary_A_with_anomalies | CANDI_STYLE_CAUSAL | 1.0000 | 0.0152 | 0.0152 | 160 / 2570 / 2560 | 0 / 0 | 1.0000 / 0.2266 |
| 202 | stationary_A_with_anomalies | QUARANTINE_1 | 1.0000 | 0.5109 | 0.5109 | 92 / 92 / 92 | 25 / 25 | 1.0000 / 0.0734 |
| 202 | stationary_A_with_anomalies | QUARANTINE_64 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2359 |
| 202 | stationary_A_with_anomalies | QUARANTINE_128 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2359 |
| 202 | stationary_A_with_anomalies | QUARANTINE_256 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2359 |
| 202 | stationary_A_with_anomalies | QUARANTINE_512 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2359 |
| 202 | semantic_fault_twin | FROZEN | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.5020 |
| 202 | semantic_fault_twin | IMMEDIATE_UPDATE | 1.0000 | 0.9938 | 0.9938 | 483 / 483 / 483 | 0 / 0 | 1.0000 / 0.1190 |
| 202 | semantic_fault_twin | M2N2_STYLE_CAUSAL | 1.0000 | 0.8639 | 0.8639 | 4158 / 4158 / 4158 | 0 / 0 | 1.0000 / 0.1091 |
| 202 | semantic_fault_twin | CANDI_STYLE_CAUSAL | 1.0000 | 0.5938 | 0.5938 | 56 / 898 / 896 | 0 / 0 | 1.0000 / 0.4777 |
| 202 | semantic_fault_twin | QUARANTINE_1 | 1.0000 | 0.9938 | 0.9938 | 483 / 483 / 483 | 133 / 133 | 1.0000 / 0.1190 |
| 202 | semantic_fault_twin | QUARANTINE_64 | 1.0000 | 1.0000 | 1.0000 | 9 / 9 / 9 | 1 / 1 | 1.0000 / 0.4368 |
| 202 | semantic_fault_twin | QUARANTINE_128 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.5020 |
| 202 | semantic_fault_twin | QUARANTINE_256 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.5020 |
| 202 | semantic_fault_twin | QUARANTINE_512 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.5020 |
| 303 | benign_B_with_anomalies | FROZEN | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.5406 |
| 303 | benign_B_with_anomalies | IMMEDIATE_UPDATE | 1.0000 | 0.1442 | 0.1442 | 659 / 659 / 659 | 0 / 0 | 1.0000 / 0.1484 |
| 303 | benign_B_with_anomalies | M2N2_STYLE_CAUSAL | 1.0000 | 0.1418 | 0.1418 | 3809 / 3809 / 3809 | 0 / 0 | 1.0000 / 0.1562 |
| 303 | benign_B_with_anomalies | CANDI_STYLE_CAUSAL | 0.0000 | 0.0000 | 0.0000 | 37 / 608 / 592 | 0 / 0 | 1.0000 / 0.5078 |
| 303 | benign_B_with_anomalies | QUARANTINE_1 | 1.0000 | 0.1442 | 0.1442 | 659 / 659 / 659 | 163 / 37 | 1.0000 / 0.1484 |
| 303 | benign_B_with_anomalies | QUARANTINE_64 | 0.5000 | 1.0000 | 1.0000 | 5 / 5 / 5 | 1 / 1 | 1.0000 / 0.4313 |
| 303 | benign_B_with_anomalies | QUARANTINE_128 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.5406 |
| 303 | benign_B_with_anomalies | QUARANTINE_256 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.5406 |
| 303 | benign_B_with_anomalies | QUARANTINE_512 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.5406 |
| 303 | stationary_A_with_anomalies | FROZEN | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.1734 |
| 303 | stationary_A_with_anomalies | IMMEDIATE_UPDATE | 1.0000 | 0.4344 | 0.4344 | 122 / 122 / 122 | 0 / 0 | 1.0000 / 0.0828 |
| 303 | stationary_A_with_anomalies | M2N2_STYLE_CAUSAL | 1.0000 | 0.1360 | 0.1360 | 4294 / 4294 / 4294 | 0 / 0 | 1.0000 / 0.0875 |
| 303 | stationary_A_with_anomalies | CANDI_STYLE_CAUSAL | 1.0000 | 0.0162 | 0.0162 | 170 / 2737 / 2720 | 0 / 0 | 1.0000 / 0.1656 |
| 303 | stationary_A_with_anomalies | QUARANTINE_1 | 1.0000 | 0.4344 | 0.4344 | 122 / 122 / 122 | 45 / 45 | 1.0000 / 0.0828 |
| 303 | stationary_A_with_anomalies | QUARANTINE_64 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.1734 |
| 303 | stationary_A_with_anomalies | QUARANTINE_128 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.1734 |
| 303 | stationary_A_with_anomalies | QUARANTINE_256 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.1734 |
| 303 | stationary_A_with_anomalies | QUARANTINE_512 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.1734 |
| 303 | semantic_fault_twin | FROZEN | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4508 |
| 303 | semantic_fault_twin | IMMEDIATE_UPDATE | 1.0000 | 0.9985 | 0.9985 | 659 / 659 / 659 | 0 / 0 | 1.0000 / 0.1558 |
| 303 | semantic_fault_twin | M2N2_STYLE_CAUSAL | 1.0000 | 0.9029 | 0.9029 | 3809 / 3809 / 3809 | 0 / 0 | 1.0000 / 0.1858 |
| 303 | semantic_fault_twin | CANDI_STYLE_CAUSAL | 1.0000 | 0.5676 | 0.5676 | 37 / 608 / 592 | 0 / 0 | 1.0000 / 0.4290 |
| 303 | semantic_fault_twin | QUARANTINE_1 | 1.0000 | 0.9985 | 0.9985 | 659 / 659 / 659 | 163 / 163 | 1.0000 / 0.1558 |
| 303 | semantic_fault_twin | QUARANTINE_64 | 1.0000 | 1.0000 | 1.0000 | 5 / 5 / 5 | 1 / 1 | 1.0000 / 0.3639 |
| 303 | semantic_fault_twin | QUARANTINE_128 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4508 |
| 303 | semantic_fault_twin | QUARANTINE_256 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4508 |
| 303 | semantic_fault_twin | QUARANTINE_512 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4508 |
| 404 | benign_B_with_anomalies | FROZEN | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4500 |
| 404 | benign_B_with_anomalies | IMMEDIATE_UPDATE | 1.0000 | 0.1861 | 0.1861 | 575 / 575 / 575 | 0 / 0 | 1.0000 / 0.1672 |
| 404 | benign_B_with_anomalies | M2N2_STYLE_CAUSAL | 1.0000 | 0.1347 | 0.1347 | 3882 / 3882 / 3882 | 0 / 0 | 1.0000 / 0.1828 |
| 404 | benign_B_with_anomalies | CANDI_STYLE_CAUSAL | 0.0000 | 0.0000 | 0.0000 | 45 / 746 / 720 | 0 / 0 | 1.0000 / 0.4281 |
| 404 | benign_B_with_anomalies | QUARANTINE_1 | 1.0000 | 0.1861 | 0.1861 | 575 / 575 / 575 | 146 / 49 | 1.0000 / 0.1672 |
| 404 | benign_B_with_anomalies | QUARANTINE_64 | 0.5000 | 1.0000 | 1.0000 | 4 / 4 / 4 | 1 / 1 | 1.0000 / 0.3484 |
| 404 | benign_B_with_anomalies | QUARANTINE_128 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4500 |
| 404 | benign_B_with_anomalies | QUARANTINE_256 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4500 |
| 404 | benign_B_with_anomalies | QUARANTINE_512 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4500 |
| 404 | stationary_A_with_anomalies | FROZEN | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2016 |
| 404 | stationary_A_with_anomalies | IMMEDIATE_UPDATE | 1.0000 | 0.4476 | 0.4476 | 143 / 143 / 143 | 0 / 0 | 1.0000 / 0.1000 |
| 404 | stationary_A_with_anomalies | M2N2_STYLE_CAUSAL | 1.0000 | 0.1290 | 0.1290 | 4379 / 4379 / 4379 | 0 / 0 | 1.0000 / 0.1172 |
| 404 | stationary_A_with_anomalies | CANDI_STYLE_CAUSAL | 1.0000 | 0.0165 | 0.0165 | 155 / 2489 / 2480 | 0 / 0 | 1.0000 / 0.2078 |
| 404 | stationary_A_with_anomalies | QUARANTINE_1 | 1.0000 | 0.4476 | 0.4476 | 143 / 143 / 143 | 47 / 47 | 1.0000 / 0.1000 |
| 404 | stationary_A_with_anomalies | QUARANTINE_64 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2016 |
| 404 | stationary_A_with_anomalies | QUARANTINE_128 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2016 |
| 404 | stationary_A_with_anomalies | QUARANTINE_256 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2016 |
| 404 | stationary_A_with_anomalies | QUARANTINE_512 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2016 |
| 404 | semantic_fault_twin | FROZEN | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.3878 |
| 404 | semantic_fault_twin | IMMEDIATE_UPDATE | 1.0000 | 0.9913 | 0.9913 | 575 / 575 / 575 | 0 / 0 | 1.0000 / 0.1460 |
| 404 | semantic_fault_twin | M2N2_STYLE_CAUSAL | 1.0000 | 0.8241 | 0.8241 | 3882 / 3882 / 3882 | 0 / 0 | 1.0000 / 0.1806 |
| 404 | semantic_fault_twin | CANDI_STYLE_CAUSAL | 1.0000 | 0.4028 | 0.4028 | 45 / 746 / 720 | 0 / 0 | 1.0000 / 0.3704 |
| 404 | semantic_fault_twin | QUARANTINE_1 | 1.0000 | 0.9913 | 0.9913 | 575 / 575 / 575 | 146 / 146 | 1.0000 / 0.1460 |
| 404 | semantic_fault_twin | QUARANTINE_64 | 1.0000 | 1.0000 | 1.0000 | 4 / 4 / 4 | 1 / 1 | 1.0000 / 0.3184 |
| 404 | semantic_fault_twin | QUARANTINE_128 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.3878 |
| 404 | semantic_fault_twin | QUARANTINE_256 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.3878 |
| 404 | semantic_fault_twin | QUARANTINE_512 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.3878 |
| 505 | benign_B_with_anomalies | FROZEN | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4469 |
| 505 | benign_B_with_anomalies | IMMEDIATE_UPDATE | 1.0000 | 0.1756 | 0.1756 | 615 / 615 / 615 | 0 / 0 | 1.0000 / 0.1688 |
| 505 | benign_B_with_anomalies | M2N2_STYLE_CAUSAL | 1.0000 | 0.1430 | 0.1430 | 3973 / 3973 / 3973 | 0 / 0 | 1.0000 / 0.1125 |
| 505 | benign_B_with_anomalies | CANDI_STYLE_CAUSAL | 0.0000 | 0.0000 | 0.0000 | 33 / 537 / 528 | 0 / 0 | 1.0000 / 0.4172 |
| 505 | benign_B_with_anomalies | QUARANTINE_1 | 1.0000 | 0.1756 | 0.1756 | 615 / 615 / 615 | 164 / 46 | 1.0000 / 0.1688 |
| 505 | benign_B_with_anomalies | QUARANTINE_64 | 0.5000 | 1.0000 | 1.0000 | 3 / 3 / 3 | 1 / 1 | 1.0000 / 0.3641 |
| 505 | benign_B_with_anomalies | QUARANTINE_128 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4469 |
| 505 | benign_B_with_anomalies | QUARANTINE_256 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4469 |
| 505 | benign_B_with_anomalies | QUARANTINE_512 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4469 |
| 505 | stationary_A_with_anomalies | FROZEN | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2094 |
| 505 | stationary_A_with_anomalies | IMMEDIATE_UPDATE | 1.0000 | 0.3630 | 0.3630 | 135 / 135 / 135 | 0 / 0 | 1.0000 / 0.0766 |
| 505 | stationary_A_with_anomalies | M2N2_STYLE_CAUSAL | 1.0000 | 0.1348 | 0.1348 | 4405 / 4405 / 4405 | 0 / 0 | 0.5000 / 0.0719 |
| 505 | stationary_A_with_anomalies | CANDI_STYLE_CAUSAL | 1.0000 | 0.0185 | 0.0185 | 155 / 2499 / 2480 | 0 / 0 | 1.0000 / 0.1812 |
| 505 | stationary_A_with_anomalies | QUARANTINE_1 | 1.0000 | 0.3630 | 0.3630 | 135 / 135 / 135 | 55 / 55 | 1.0000 / 0.0766 |
| 505 | stationary_A_with_anomalies | QUARANTINE_64 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2094 |
| 505 | stationary_A_with_anomalies | QUARANTINE_128 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2094 |
| 505 | stationary_A_with_anomalies | QUARANTINE_256 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2094 |
| 505 | stationary_A_with_anomalies | QUARANTINE_512 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.2094 |
| 505 | semantic_fault_twin | FROZEN | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4060 |
| 505 | semantic_fault_twin | IMMEDIATE_UPDATE | 1.0000 | 0.9951 | 0.9951 | 615 / 615 / 615 | 0 / 0 | 1.0000 / 0.1483 |
| 505 | semantic_fault_twin | M2N2_STYLE_CAUSAL | 1.0000 | 0.8842 | 0.8842 | 3973 / 3973 / 3973 | 0 / 0 | 1.0000 / 0.1490 |
| 505 | semantic_fault_twin | CANDI_STYLE_CAUSAL | 1.0000 | 0.4545 | 0.4545 | 33 / 537 / 528 | 0 / 0 | 1.0000 / 0.3789 |
| 505 | semantic_fault_twin | QUARANTINE_1 | 1.0000 | 0.9951 | 0.9951 | 615 / 615 / 615 | 164 / 164 | 1.0000 / 0.1483 |
| 505 | semantic_fault_twin | QUARANTINE_64 | 1.0000 | 1.0000 | 1.0000 | 3 / 3 / 3 | 1 / 1 | 1.0000 / 0.3350 |
| 505 | semantic_fault_twin | QUARANTINE_128 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4060 |
| 505 | semantic_fault_twin | QUARANTINE_256 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4060 |
| 505 | semantic_fault_twin | QUARANTINE_512 | 0.0000 | N/A | N/A | 0 / 0 / 0 | 0 / 0 | 1.0000 / 0.4060 |

## Every physical negative episode

| Group | Stratum | Policy | Episode [start,end) | Effective write fraction | Event / point recall | First alarm delay |
|---|---|---|---|---:|---|---:|
| 101 | benign_B_with_anomalies | FROZEN | collective_under_B [3072,3200) | 0.0000 | 1 / 0.9922 | 0 |
| 101 | benign_B_with_anomalies | FROZEN | long_anomaly_under_B [4096,4608) | 0.0000 | 1 / 0.4473 | 0 |
| 101 | benign_B_with_anomalies | IMMEDIATE_UPDATE | collective_under_B [3072,3200) | 0.3516 | 1 / 0.3516 | 4 |
| 101 | benign_B_with_anomalies | IMMEDIATE_UPDATE | long_anomaly_under_B [4096,4608) | 0.1230 | 1 / 0.1230 | 0 |
| 101 | benign_B_with_anomalies | M2N2_STYLE_CAUSAL | collective_under_B [3072,3200) | 0.5312 | 1 / 0.4688 | 2 |
| 101 | benign_B_with_anomalies | M2N2_STYLE_CAUSAL | long_anomaly_under_B [4096,4608) | 0.9395 | 1 / 0.0605 | 0 |
| 101 | benign_B_with_anomalies | CANDI_STYLE_CAUSAL | collective_under_B [3072,3200) | 0.0000 | 1 / 0.9844 | 0 |
| 101 | benign_B_with_anomalies | CANDI_STYLE_CAUSAL | long_anomaly_under_B [4096,4608) | 0.0000 | 1 / 0.3594 | 0 |
| 101 | benign_B_with_anomalies | QUARANTINE_1 | collective_under_B [3072,3200) | 0.3516 | 1 / 0.3516 | 4 |
| 101 | benign_B_with_anomalies | QUARANTINE_1 | long_anomaly_under_B [4096,4608) | 0.1230 | 1 / 0.1230 | 0 |
| 101 | benign_B_with_anomalies | QUARANTINE_64 | collective_under_B [3072,3200) | 0.1328 | 1 / 0.8125 | 0 |
| 101 | benign_B_with_anomalies | QUARANTINE_64 | long_anomaly_under_B [4096,4608) | 0.0000 | 1 / 0.3789 | 0 |
| 101 | benign_B_with_anomalies | QUARANTINE_128 | collective_under_B [3072,3200) | 0.0000 | 1 / 0.9922 | 0 |
| 101 | benign_B_with_anomalies | QUARANTINE_128 | long_anomaly_under_B [4096,4608) | 0.0000 | 1 / 0.4473 | 0 |
| 101 | benign_B_with_anomalies | QUARANTINE_256 | collective_under_B [3072,3200) | 0.0000 | 1 / 0.9922 | 0 |
| 101 | benign_B_with_anomalies | QUARANTINE_256 | long_anomaly_under_B [4096,4608) | 0.0000 | 1 / 0.4473 | 0 |
| 101 | benign_B_with_anomalies | QUARANTINE_512 | collective_under_B [3072,3200) | 0.0000 | 1 / 0.9922 | 0 |
| 101 | benign_B_with_anomalies | QUARANTINE_512 | long_anomaly_under_B [4096,4608) | 0.0000 | 1 / 0.4473 | 0 |
| 101 | stationary_A_with_anomalies | FROZEN | collective_under_B [3072,3200) | 0.0000 | 1 / 0.6484 | 1 |
| 101 | stationary_A_with_anomalies | FROZEN | long_anomaly_under_B [4096,4608) | 0.0000 | 1 / 0.1426 | 0 |
| 101 | stationary_A_with_anomalies | IMMEDIATE_UPDATE | collective_under_B [3072,3200) | 0.3047 | 1 / 0.3047 | 1 |
| 101 | stationary_A_with_anomalies | IMMEDIATE_UPDATE | long_anomaly_under_B [4096,4608) | 0.0332 | 1 / 0.0332 | 0 |
| 101 | stationary_A_with_anomalies | M2N2_STYLE_CAUSAL | collective_under_B [3072,3200) | 0.5391 | 1 / 0.4609 | 1 |
| 101 | stationary_A_with_anomalies | M2N2_STYLE_CAUSAL | long_anomaly_under_B [4096,4608) | 0.9805 | 1 / 0.0195 | 0 |
| 101 | stationary_A_with_anomalies | CANDI_STYLE_CAUSAL | collective_under_B [3072,3200) | 0.1562 | 1 / 0.6562 | 1 |
| 101 | stationary_A_with_anomalies | CANDI_STYLE_CAUSAL | long_anomaly_under_B [4096,4608) | 0.0762 | 1 / 0.1211 | 0 |
| 101 | stationary_A_with_anomalies | QUARANTINE_1 | collective_under_B [3072,3200) | 0.3047 | 1 / 0.3047 | 1 |
| 101 | stationary_A_with_anomalies | QUARANTINE_1 | long_anomaly_under_B [4096,4608) | 0.0332 | 1 / 0.0332 | 0 |
| 101 | stationary_A_with_anomalies | QUARANTINE_64 | collective_under_B [3072,3200) | 0.0000 | 1 / 0.6484 | 1 |
| 101 | stationary_A_with_anomalies | QUARANTINE_64 | long_anomaly_under_B [4096,4608) | 0.0000 | 1 / 0.1426 | 0 |
| 101 | stationary_A_with_anomalies | QUARANTINE_128 | collective_under_B [3072,3200) | 0.0000 | 1 / 0.6484 | 1 |
| 101 | stationary_A_with_anomalies | QUARANTINE_128 | long_anomaly_under_B [4096,4608) | 0.0000 | 1 / 0.1426 | 0 |
| 101 | stationary_A_with_anomalies | QUARANTINE_256 | collective_under_B [3072,3200) | 0.0000 | 1 / 0.6484 | 1 |
| 101 | stationary_A_with_anomalies | QUARANTINE_256 | long_anomaly_under_B [4096,4608) | 0.0000 | 1 / 0.1426 | 0 |
| 101 | stationary_A_with_anomalies | QUARANTINE_512 | collective_under_B [3072,3200) | 0.0000 | 1 / 0.6484 | 1 |
| 101 | stationary_A_with_anomalies | QUARANTINE_512 | long_anomaly_under_B [4096,4608) | 0.0000 | 1 / 0.1426 | 0 |
| 101 | semantic_fault_twin | FROZEN | persistent_nonbenign_twin [2048,6144) | 0.0000 | 1 / 0.4226 | 56 |
| 101 | semantic_fault_twin | IMMEDIATE_UPDATE | persistent_nonbenign_twin [2048,6144) | 0.1326 | 1 / 0.1326 | 56 |
| 101 | semantic_fault_twin | M2N2_STYLE_CAUSAL | persistent_nonbenign_twin [2048,6144) | 0.8640 | 1 / 0.1360 | 34 |
| 101 | semantic_fault_twin | CANDI_STYLE_CAUSAL | persistent_nonbenign_twin [2048,6144) | 0.1062 | 1 / 0.3940 | 56 |
| 101 | semantic_fault_twin | QUARANTINE_1 | persistent_nonbenign_twin [2048,6144) | 0.1326 | 1 / 0.1326 | 56 |
| 101 | semantic_fault_twin | QUARANTINE_64 | persistent_nonbenign_twin [2048,6144) | 0.0042 | 1 / 0.3440 | 56 |
| 101 | semantic_fault_twin | QUARANTINE_128 | persistent_nonbenign_twin [2048,6144) | 0.0000 | 1 / 0.4226 | 56 |
| 101 | semantic_fault_twin | QUARANTINE_256 | persistent_nonbenign_twin [2048,6144) | 0.0000 | 1 / 0.4226 | 56 |
| 101 | semantic_fault_twin | QUARANTINE_512 | persistent_nonbenign_twin [2048,6144) | 0.0000 | 1 / 0.4226 | 56 |
| 202 | benign_B_with_anomalies | FROZEN | collective_under_B [3136,3264) | 0.0000 | 1 / 0.9453 | 0 |
| 202 | benign_B_with_anomalies | FROZEN | long_anomaly_under_B [4160,4672) | 0.0000 | 1 / 0.7285 | 10 |
| 202 | benign_B_with_anomalies | IMMEDIATE_UPDATE | collective_under_B [3136,3264) | 0.3750 | 1 / 0.3750 | 0 |
| 202 | benign_B_with_anomalies | IMMEDIATE_UPDATE | long_anomaly_under_B [4160,4672) | 0.1035 | 1 / 0.1035 | 14 |
| 202 | benign_B_with_anomalies | M2N2_STYLE_CAUSAL | collective_under_B [3136,3264) | 0.4844 | 1 / 0.5156 | 0 |
| 202 | benign_B_with_anomalies | M2N2_STYLE_CAUSAL | long_anomaly_under_B [4160,4672) | 0.9648 | 1 / 0.0352 | 20 |
| 202 | benign_B_with_anomalies | CANDI_STYLE_CAUSAL | collective_under_B [3136,3264) | 0.0078 | 1 / 0.9453 | 0 |
| 202 | benign_B_with_anomalies | CANDI_STYLE_CAUSAL | long_anomaly_under_B [4160,4672) | 0.0000 | 1 / 0.6953 | 12 |
| 202 | benign_B_with_anomalies | QUARANTINE_1 | collective_under_B [3136,3264) | 0.3750 | 1 / 0.3750 | 0 |
| 202 | benign_B_with_anomalies | QUARANTINE_1 | long_anomaly_under_B [4160,4672) | 0.1035 | 1 / 0.1035 | 14 |
| 202 | benign_B_with_anomalies | QUARANTINE_64 | collective_under_B [3136,3264) | 0.0703 | 1 / 0.8125 | 0 |
| 202 | benign_B_with_anomalies | QUARANTINE_64 | long_anomaly_under_B [4160,4672) | 0.0000 | 1 / 0.6387 | 12 |
| 202 | benign_B_with_anomalies | QUARANTINE_128 | collective_under_B [3136,3264) | 0.0000 | 1 / 0.9453 | 0 |
| 202 | benign_B_with_anomalies | QUARANTINE_128 | long_anomaly_under_B [4160,4672) | 0.0000 | 1 / 0.7285 | 10 |
| 202 | benign_B_with_anomalies | QUARANTINE_256 | collective_under_B [3136,3264) | 0.0000 | 1 / 0.9453 | 0 |
| 202 | benign_B_with_anomalies | QUARANTINE_256 | long_anomaly_under_B [4160,4672) | 0.0000 | 1 / 0.7285 | 10 |
| 202 | benign_B_with_anomalies | QUARANTINE_512 | collective_under_B [3136,3264) | 0.0000 | 1 / 0.9453 | 0 |
| 202 | benign_B_with_anomalies | QUARANTINE_512 | long_anomaly_under_B [4160,4672) | 0.0000 | 1 / 0.7285 | 10 |
| 202 | stationary_A_with_anomalies | FROZEN | collective_under_B [3136,3264) | 0.0000 | 1 / 0.5547 | 0 |
| 202 | stationary_A_with_anomalies | FROZEN | long_anomaly_under_B [4160,4672) | 0.0000 | 1 / 0.1562 | 16 |
| 202 | stationary_A_with_anomalies | IMMEDIATE_UPDATE | collective_under_B [3136,3264) | 0.2656 | 1 / 0.2656 | 0 |
| 202 | stationary_A_with_anomalies | IMMEDIATE_UPDATE | long_anomaly_under_B [4160,4672) | 0.0254 | 1 / 0.0254 | 14 |
| 202 | stationary_A_with_anomalies | M2N2_STYLE_CAUSAL | collective_under_B [3136,3264) | 0.7422 | 1 / 0.2578 | 0 |
| 202 | stationary_A_with_anomalies | M2N2_STYLE_CAUSAL | long_anomaly_under_B [4160,4672) | 1.0000 | 0 / 0.0000 | None |
| 202 | stationary_A_with_anomalies | CANDI_STYLE_CAUSAL | collective_under_B [3136,3264) | 0.1172 | 1 / 0.5391 | 0 |
| 202 | stationary_A_with_anomalies | CANDI_STYLE_CAUSAL | long_anomaly_under_B [4160,4672) | 0.0469 | 1 / 0.1484 | 16 |
| 202 | stationary_A_with_anomalies | QUARANTINE_1 | collective_under_B [3136,3264) | 0.2656 | 1 / 0.2656 | 0 |
| 202 | stationary_A_with_anomalies | QUARANTINE_1 | long_anomaly_under_B [4160,4672) | 0.0254 | 1 / 0.0254 | 14 |
| 202 | stationary_A_with_anomalies | QUARANTINE_64 | collective_under_B [3136,3264) | 0.0000 | 1 / 0.5547 | 0 |
| 202 | stationary_A_with_anomalies | QUARANTINE_64 | long_anomaly_under_B [4160,4672) | 0.0000 | 1 / 0.1562 | 16 |
| 202 | stationary_A_with_anomalies | QUARANTINE_128 | collective_under_B [3136,3264) | 0.0000 | 1 / 0.5547 | 0 |
| 202 | stationary_A_with_anomalies | QUARANTINE_128 | long_anomaly_under_B [4160,4672) | 0.0000 | 1 / 0.1562 | 16 |
| 202 | stationary_A_with_anomalies | QUARANTINE_256 | collective_under_B [3136,3264) | 0.0000 | 1 / 0.5547 | 0 |
| 202 | stationary_A_with_anomalies | QUARANTINE_256 | long_anomaly_under_B [4160,4672) | 0.0000 | 1 / 0.1562 | 16 |
| 202 | stationary_A_with_anomalies | QUARANTINE_512 | collective_under_B [3136,3264) | 0.0000 | 1 / 0.5547 | 0 |
| 202 | stationary_A_with_anomalies | QUARANTINE_512 | long_anomaly_under_B [4160,4672) | 0.0000 | 1 / 0.1562 | 16 |
| 202 | semantic_fault_twin | FROZEN | persistent_nonbenign_twin [2112,6144) | 0.0000 | 1 / 0.5020 | 116 |
| 202 | semantic_fault_twin | IMMEDIATE_UPDATE | persistent_nonbenign_twin [2112,6144) | 0.1190 | 1 / 0.1190 | 116 |
| 202 | semantic_fault_twin | M2N2_STYLE_CAUSAL | persistent_nonbenign_twin [2112,6144) | 0.8909 | 1 / 0.1091 | 117 |
| 202 | semantic_fault_twin | CANDI_STYLE_CAUSAL | persistent_nonbenign_twin [2112,6144) | 0.1319 | 1 / 0.4777 | 116 |
| 202 | semantic_fault_twin | QUARANTINE_1 | persistent_nonbenign_twin [2112,6144) | 0.1190 | 1 / 0.1190 | 116 |
| 202 | semantic_fault_twin | QUARANTINE_64 | persistent_nonbenign_twin [2112,6144) | 0.0022 | 1 / 0.4368 | 116 |
| 202 | semantic_fault_twin | QUARANTINE_128 | persistent_nonbenign_twin [2112,6144) | 0.0000 | 1 / 0.5020 | 116 |
| 202 | semantic_fault_twin | QUARANTINE_256 | persistent_nonbenign_twin [2112,6144) | 0.0000 | 1 / 0.5020 | 116 |
| 202 | semantic_fault_twin | QUARANTINE_512 | persistent_nonbenign_twin [2112,6144) | 0.0000 | 1 / 0.5020 | 116 |
| 303 | benign_B_with_anomalies | FROZEN | collective_under_B [2944,3072) | 0.0000 | 1 / 0.9531 | 0 |
| 303 | benign_B_with_anomalies | FROZEN | long_anomaly_under_B [3968,4480) | 0.0000 | 1 / 0.4375 | 8 |
| 303 | benign_B_with_anomalies | IMMEDIATE_UPDATE | collective_under_B [2944,3072) | 0.3359 | 1 / 0.3359 | 0 |
| 303 | benign_B_with_anomalies | IMMEDIATE_UPDATE | long_anomaly_under_B [3968,4480) | 0.1016 | 1 / 0.1016 | 12 |
| 303 | benign_B_with_anomalies | M2N2_STYLE_CAUSAL | collective_under_B [2944,3072) | 0.5234 | 1 / 0.4766 | 0 |
| 303 | benign_B_with_anomalies | M2N2_STYLE_CAUSAL | long_anomaly_under_B [3968,4480) | 0.9238 | 1 / 0.0762 | 0 |
| 303 | benign_B_with_anomalies | CANDI_STYLE_CAUSAL | collective_under_B [2944,3072) | 0.0000 | 1 / 0.9531 | 0 |
| 303 | benign_B_with_anomalies | CANDI_STYLE_CAUSAL | long_anomaly_under_B [3968,4480) | 0.0000 | 1 / 0.3965 | 8 |
| 303 | benign_B_with_anomalies | QUARANTINE_1 | collective_under_B [2944,3072) | 0.3359 | 1 / 0.3359 | 0 |
| 303 | benign_B_with_anomalies | QUARANTINE_1 | long_anomaly_under_B [3968,4480) | 0.1016 | 1 / 0.1016 | 12 |
| 303 | benign_B_with_anomalies | QUARANTINE_64 | collective_under_B [2944,3072) | 0.0391 | 1 / 0.8672 | 0 |
| 303 | benign_B_with_anomalies | QUARANTINE_64 | long_anomaly_under_B [3968,4480) | 0.0000 | 1 / 0.3223 | 9 |
| 303 | benign_B_with_anomalies | QUARANTINE_128 | collective_under_B [2944,3072) | 0.0000 | 1 / 0.9531 | 0 |
| 303 | benign_B_with_anomalies | QUARANTINE_128 | long_anomaly_under_B [3968,4480) | 0.0000 | 1 / 0.4375 | 8 |
| 303 | benign_B_with_anomalies | QUARANTINE_256 | collective_under_B [2944,3072) | 0.0000 | 1 / 0.9531 | 0 |
| 303 | benign_B_with_anomalies | QUARANTINE_256 | long_anomaly_under_B [3968,4480) | 0.0000 | 1 / 0.4375 | 8 |
| 303 | benign_B_with_anomalies | QUARANTINE_512 | collective_under_B [2944,3072) | 0.0000 | 1 / 0.9531 | 0 |
| 303 | benign_B_with_anomalies | QUARANTINE_512 | long_anomaly_under_B [3968,4480) | 0.0000 | 1 / 0.4375 | 8 |
| 303 | stationary_A_with_anomalies | FROZEN | collective_under_B [2944,3072) | 0.0000 | 1 / 0.6094 | 3 |
| 303 | stationary_A_with_anomalies | FROZEN | long_anomaly_under_B [3968,4480) | 0.0000 | 1 / 0.0645 | 25 |
| 303 | stationary_A_with_anomalies | IMMEDIATE_UPDATE | collective_under_B [2944,3072) | 0.2969 | 1 / 0.2969 | 1 |
| 303 | stationary_A_with_anomalies | IMMEDIATE_UPDATE | long_anomaly_under_B [3968,4480) | 0.0293 | 1 / 0.0293 | 0 |
| 303 | stationary_A_with_anomalies | M2N2_STYLE_CAUSAL | collective_under_B [2944,3072) | 0.5703 | 1 / 0.4297 | 3 |
| 303 | stationary_A_with_anomalies | M2N2_STYLE_CAUSAL | long_anomaly_under_B [3968,4480) | 0.9980 | 1 / 0.0020 | 25 |
| 303 | stationary_A_with_anomalies | CANDI_STYLE_CAUSAL | collective_under_B [2944,3072) | 0.1719 | 1 / 0.6016 | 3 |
| 303 | stationary_A_with_anomalies | CANDI_STYLE_CAUSAL | long_anomaly_under_B [3968,4480) | 0.0430 | 1 / 0.0566 | 25 |
| 303 | stationary_A_with_anomalies | QUARANTINE_1 | collective_under_B [2944,3072) | 0.2969 | 1 / 0.2969 | 1 |
| 303 | stationary_A_with_anomalies | QUARANTINE_1 | long_anomaly_under_B [3968,4480) | 0.0293 | 1 / 0.0293 | 0 |
| 303 | stationary_A_with_anomalies | QUARANTINE_64 | collective_under_B [2944,3072) | 0.0000 | 1 / 0.6094 | 3 |
| 303 | stationary_A_with_anomalies | QUARANTINE_64 | long_anomaly_under_B [3968,4480) | 0.0000 | 1 / 0.0645 | 25 |
| 303 | stationary_A_with_anomalies | QUARANTINE_128 | collective_under_B [2944,3072) | 0.0000 | 1 / 0.6094 | 3 |
| 303 | stationary_A_with_anomalies | QUARANTINE_128 | long_anomaly_under_B [3968,4480) | 0.0000 | 1 / 0.0645 | 25 |
| 303 | stationary_A_with_anomalies | QUARANTINE_256 | collective_under_B [2944,3072) | 0.0000 | 1 / 0.6094 | 3 |
| 303 | stationary_A_with_anomalies | QUARANTINE_256 | long_anomaly_under_B [3968,4480) | 0.0000 | 1 / 0.0645 | 25 |
| 303 | stationary_A_with_anomalies | QUARANTINE_512 | collective_under_B [2944,3072) | 0.0000 | 1 / 0.6094 | 3 |
| 303 | stationary_A_with_anomalies | QUARANTINE_512 | long_anomaly_under_B [3968,4480) | 0.0000 | 1 / 0.0645 | 25 |
| 303 | semantic_fault_twin | FROZEN | persistent_nonbenign_twin [1920,6144) | 0.0000 | 1 / 0.4508 | 2 |
| 303 | semantic_fault_twin | IMMEDIATE_UPDATE | persistent_nonbenign_twin [1920,6144) | 0.1558 | 1 / 0.1558 | 2 |
| 303 | semantic_fault_twin | M2N2_STYLE_CAUSAL | persistent_nonbenign_twin [1920,6144) | 0.8142 | 1 / 0.1858 | 2 |
| 303 | semantic_fault_twin | CANDI_STYLE_CAUSAL | persistent_nonbenign_twin [1920,6144) | 0.0795 | 1 / 0.4290 | 2 |
| 303 | semantic_fault_twin | QUARANTINE_1 | persistent_nonbenign_twin [1920,6144) | 0.1558 | 1 / 0.1558 | 2 |
| 303 | semantic_fault_twin | QUARANTINE_64 | persistent_nonbenign_twin [1920,6144) | 0.0012 | 1 / 0.3639 | 2 |
| 303 | semantic_fault_twin | QUARANTINE_128 | persistent_nonbenign_twin [1920,6144) | 0.0000 | 1 / 0.4508 | 2 |
| 303 | semantic_fault_twin | QUARANTINE_256 | persistent_nonbenign_twin [1920,6144) | 0.0000 | 1 / 0.4508 | 2 |
| 303 | semantic_fault_twin | QUARANTINE_512 | persistent_nonbenign_twin [1920,6144) | 0.0000 | 1 / 0.4508 | 2 |
| 404 | benign_B_with_anomalies | FROZEN | collective_under_B [3264,3392) | 0.0000 | 1 / 0.9766 | 0 |
| 404 | benign_B_with_anomalies | FROZEN | long_anomaly_under_B [4288,4800) | 0.0000 | 1 / 0.3184 | 11 |
| 404 | benign_B_with_anomalies | IMMEDIATE_UPDATE | collective_under_B [3264,3392) | 0.2969 | 1 / 0.2969 | 0 |
| 404 | benign_B_with_anomalies | IMMEDIATE_UPDATE | long_anomaly_under_B [4288,4800) | 0.1348 | 1 / 0.1348 | 1 |
| 404 | benign_B_with_anomalies | M2N2_STYLE_CAUSAL | collective_under_B [3264,3392) | 0.5078 | 1 / 0.4922 | 0 |
| 404 | benign_B_with_anomalies | M2N2_STYLE_CAUSAL | long_anomaly_under_B [4288,4800) | 0.8945 | 1 / 0.1055 | 0 |
| 404 | benign_B_with_anomalies | CANDI_STYLE_CAUSAL | collective_under_B [3264,3392) | 0.0000 | 1 / 0.9766 | 0 |
| 404 | benign_B_with_anomalies | CANDI_STYLE_CAUSAL | long_anomaly_under_B [4288,4800) | 0.0000 | 1 / 0.2910 | 11 |
| 404 | benign_B_with_anomalies | QUARANTINE_1 | collective_under_B [3264,3392) | 0.2969 | 1 / 0.2969 | 0 |
| 404 | benign_B_with_anomalies | QUARANTINE_1 | long_anomaly_under_B [4288,4800) | 0.1348 | 1 / 0.1348 | 1 |
| 404 | benign_B_with_anomalies | QUARANTINE_64 | collective_under_B [3264,3392) | 0.0312 | 1 / 0.9062 | 0 |
| 404 | benign_B_with_anomalies | QUARANTINE_64 | long_anomaly_under_B [4288,4800) | 0.0000 | 1 / 0.2090 | 10 |
| 404 | benign_B_with_anomalies | QUARANTINE_128 | collective_under_B [3264,3392) | 0.0000 | 1 / 0.9766 | 0 |
| 404 | benign_B_with_anomalies | QUARANTINE_128 | long_anomaly_under_B [4288,4800) | 0.0000 | 1 / 0.3184 | 11 |
| 404 | benign_B_with_anomalies | QUARANTINE_256 | collective_under_B [3264,3392) | 0.0000 | 1 / 0.9766 | 0 |
| 404 | benign_B_with_anomalies | QUARANTINE_256 | long_anomaly_under_B [4288,4800) | 0.0000 | 1 / 0.3184 | 11 |
| 404 | benign_B_with_anomalies | QUARANTINE_512 | collective_under_B [3264,3392) | 0.0000 | 1 / 0.9766 | 0 |
| 404 | benign_B_with_anomalies | QUARANTINE_512 | long_anomaly_under_B [4288,4800) | 0.0000 | 1 / 0.3184 | 11 |
| 404 | stationary_A_with_anomalies | FROZEN | collective_under_B [3264,3392) | 0.0000 | 1 / 0.7188 | 0 |
| 404 | stationary_A_with_anomalies | FROZEN | long_anomaly_under_B [4288,4800) | 0.0000 | 1 / 0.0723 | 5 |
| 404 | stationary_A_with_anomalies | IMMEDIATE_UPDATE | collective_under_B [3264,3392) | 0.3438 | 1 / 0.3438 | 0 |
| 404 | stationary_A_with_anomalies | IMMEDIATE_UPDATE | long_anomaly_under_B [4288,4800) | 0.0391 | 1 / 0.0391 | 2 |
| 404 | stationary_A_with_anomalies | M2N2_STYLE_CAUSAL | collective_under_B [3264,3392) | 0.4219 | 1 / 0.5781 | 0 |
| 404 | stationary_A_with_anomalies | M2N2_STYLE_CAUSAL | long_anomaly_under_B [4288,4800) | 0.9980 | 1 / 0.0020 | 156 |
| 404 | stationary_A_with_anomalies | CANDI_STYLE_CAUSAL | collective_under_B [3264,3392) | 0.1719 | 1 / 0.7188 | 0 |
| 404 | stationary_A_with_anomalies | CANDI_STYLE_CAUSAL | long_anomaly_under_B [4288,4800) | 0.0371 | 1 / 0.0801 | 4 |
| 404 | stationary_A_with_anomalies | QUARANTINE_1 | collective_under_B [3264,3392) | 0.3438 | 1 / 0.3438 | 0 |
| 404 | stationary_A_with_anomalies | QUARANTINE_1 | long_anomaly_under_B [4288,4800) | 0.0391 | 1 / 0.0391 | 2 |
| 404 | stationary_A_with_anomalies | QUARANTINE_64 | collective_under_B [3264,3392) | 0.0000 | 1 / 0.7188 | 0 |
| 404 | stationary_A_with_anomalies | QUARANTINE_64 | long_anomaly_under_B [4288,4800) | 0.0000 | 1 / 0.0723 | 5 |
| 404 | stationary_A_with_anomalies | QUARANTINE_128 | collective_under_B [3264,3392) | 0.0000 | 1 / 0.7188 | 0 |
| 404 | stationary_A_with_anomalies | QUARANTINE_128 | long_anomaly_under_B [4288,4800) | 0.0000 | 1 / 0.0723 | 5 |
| 404 | stationary_A_with_anomalies | QUARANTINE_256 | collective_under_B [3264,3392) | 0.0000 | 1 / 0.7188 | 0 |
| 404 | stationary_A_with_anomalies | QUARANTINE_256 | long_anomaly_under_B [4288,4800) | 0.0000 | 1 / 0.0723 | 5 |
| 404 | stationary_A_with_anomalies | QUARANTINE_512 | collective_under_B [3264,3392) | 0.0000 | 1 / 0.7188 | 0 |
| 404 | stationary_A_with_anomalies | QUARANTINE_512 | long_anomaly_under_B [4288,4800) | 0.0000 | 1 / 0.0723 | 5 |
| 404 | semantic_fault_twin | FROZEN | persistent_nonbenign_twin [2240,6144) | 0.0000 | 1 / 0.3878 | 40 |
| 404 | semantic_fault_twin | IMMEDIATE_UPDATE | persistent_nonbenign_twin [2240,6144) | 0.1460 | 1 / 0.1460 | 40 |
| 404 | semantic_fault_twin | M2N2_STYLE_CAUSAL | persistent_nonbenign_twin [2240,6144) | 0.8194 | 1 / 0.1806 | 40 |
| 404 | semantic_fault_twin | CANDI_STYLE_CAUSAL | persistent_nonbenign_twin [2240,6144) | 0.0743 | 1 / 0.3704 | 40 |
| 404 | semantic_fault_twin | QUARANTINE_1 | persistent_nonbenign_twin [2240,6144) | 0.1460 | 1 / 0.1460 | 40 |
| 404 | semantic_fault_twin | QUARANTINE_64 | persistent_nonbenign_twin [2240,6144) | 0.0010 | 1 / 0.3184 | 40 |
| 404 | semantic_fault_twin | QUARANTINE_128 | persistent_nonbenign_twin [2240,6144) | 0.0000 | 1 / 0.3878 | 40 |
| 404 | semantic_fault_twin | QUARANTINE_256 | persistent_nonbenign_twin [2240,6144) | 0.0000 | 1 / 0.3878 | 40 |
| 404 | semantic_fault_twin | QUARANTINE_512 | persistent_nonbenign_twin [2240,6144) | 0.0000 | 1 / 0.3878 | 40 |
| 505 | benign_B_with_anomalies | FROZEN | collective_under_B [3040,3168) | 0.0000 | 1 / 0.9219 | 0 |
| 505 | benign_B_with_anomalies | FROZEN | long_anomaly_under_B [4064,4576) | 0.0000 | 1 / 0.3281 | 0 |
| 505 | benign_B_with_anomalies | IMMEDIATE_UPDATE | collective_under_B [3040,3168) | 0.3203 | 1 / 0.3203 | 14 |
| 505 | benign_B_with_anomalies | IMMEDIATE_UPDATE | long_anomaly_under_B [4064,4576) | 0.1309 | 1 / 0.1309 | 27 |
| 505 | benign_B_with_anomalies | M2N2_STYLE_CAUSAL | collective_under_B [3040,3168) | 0.6875 | 1 / 0.3125 | 17 |
| 505 | benign_B_with_anomalies | M2N2_STYLE_CAUSAL | long_anomaly_under_B [4064,4576) | 0.9375 | 1 / 0.0625 | 37 |
| 505 | benign_B_with_anomalies | CANDI_STYLE_CAUSAL | collective_under_B [3040,3168) | 0.0000 | 1 / 0.9219 | 0 |
| 505 | benign_B_with_anomalies | CANDI_STYLE_CAUSAL | long_anomaly_under_B [4064,4576) | 0.0000 | 1 / 0.2910 | 0 |
| 505 | benign_B_with_anomalies | QUARANTINE_1 | collective_under_B [3040,3168) | 0.3203 | 1 / 0.3203 | 14 |
| 505 | benign_B_with_anomalies | QUARANTINE_1 | long_anomaly_under_B [4064,4576) | 0.1309 | 1 / 0.1309 | 27 |
| 505 | benign_B_with_anomalies | QUARANTINE_64 | collective_under_B [3040,3168) | 0.0234 | 1 / 0.8672 | 0 |
| 505 | benign_B_with_anomalies | QUARANTINE_64 | long_anomaly_under_B [4064,4576) | 0.0000 | 1 / 0.2383 | 0 |
| 505 | benign_B_with_anomalies | QUARANTINE_128 | collective_under_B [3040,3168) | 0.0000 | 1 / 0.9219 | 0 |
| 505 | benign_B_with_anomalies | QUARANTINE_128 | long_anomaly_under_B [4064,4576) | 0.0000 | 1 / 0.3281 | 0 |
| 505 | benign_B_with_anomalies | QUARANTINE_256 | collective_under_B [3040,3168) | 0.0000 | 1 / 0.9219 | 0 |
| 505 | benign_B_with_anomalies | QUARANTINE_256 | long_anomaly_under_B [4064,4576) | 0.0000 | 1 / 0.3281 | 0 |
| 505 | benign_B_with_anomalies | QUARANTINE_512 | collective_under_B [3040,3168) | 0.0000 | 1 / 0.9219 | 0 |
| 505 | benign_B_with_anomalies | QUARANTINE_512 | long_anomaly_under_B [4064,4576) | 0.0000 | 1 / 0.3281 | 0 |
| 505 | stationary_A_with_anomalies | FROZEN | collective_under_B [3040,3168) | 0.0000 | 1 / 0.6641 | 12 |
| 505 | stationary_A_with_anomalies | FROZEN | long_anomaly_under_B [4064,4576) | 0.0000 | 1 / 0.0957 | 29 |
| 505 | stationary_A_with_anomalies | IMMEDIATE_UPDATE | collective_under_B [3040,3168) | 0.2578 | 1 / 0.2578 | 12 |
| 505 | stationary_A_with_anomalies | IMMEDIATE_UPDATE | long_anomaly_under_B [4064,4576) | 0.0312 | 1 / 0.0312 | 27 |
| 505 | stationary_A_with_anomalies | M2N2_STYLE_CAUSAL | collective_under_B [3040,3168) | 0.6406 | 1 / 0.3594 | 14 |
| 505 | stationary_A_with_anomalies | M2N2_STYLE_CAUSAL | long_anomaly_under_B [4064,4576) | 1.0000 | 0 / 0.0000 | None |
| 505 | stationary_A_with_anomalies | CANDI_STYLE_CAUSAL | collective_under_B [3040,3168) | 0.0938 | 1 / 0.6562 | 12 |
| 505 | stationary_A_with_anomalies | CANDI_STYLE_CAUSAL | long_anomaly_under_B [4064,4576) | 0.0664 | 1 / 0.0625 | 30 |
| 505 | stationary_A_with_anomalies | QUARANTINE_1 | collective_under_B [3040,3168) | 0.2578 | 1 / 0.2578 | 12 |
| 505 | stationary_A_with_anomalies | QUARANTINE_1 | long_anomaly_under_B [4064,4576) | 0.0312 | 1 / 0.0312 | 27 |
| 505 | stationary_A_with_anomalies | QUARANTINE_64 | collective_under_B [3040,3168) | 0.0000 | 1 / 0.6641 | 12 |
| 505 | stationary_A_with_anomalies | QUARANTINE_64 | long_anomaly_under_B [4064,4576) | 0.0000 | 1 / 0.0957 | 29 |
| 505 | stationary_A_with_anomalies | QUARANTINE_128 | collective_under_B [3040,3168) | 0.0000 | 1 / 0.6641 | 12 |
| 505 | stationary_A_with_anomalies | QUARANTINE_128 | long_anomaly_under_B [4064,4576) | 0.0000 | 1 / 0.0957 | 29 |
| 505 | stationary_A_with_anomalies | QUARANTINE_256 | collective_under_B [3040,3168) | 0.0000 | 1 / 0.6641 | 12 |
| 505 | stationary_A_with_anomalies | QUARANTINE_256 | long_anomaly_under_B [4064,4576) | 0.0000 | 1 / 0.0957 | 29 |
| 505 | stationary_A_with_anomalies | QUARANTINE_512 | collective_under_B [3040,3168) | 0.0000 | 1 / 0.6641 | 12 |
| 505 | stationary_A_with_anomalies | QUARANTINE_512 | long_anomaly_under_B [4064,4576) | 0.0000 | 1 / 0.0957 | 29 |
| 505 | semantic_fault_twin | FROZEN | persistent_nonbenign_twin [2016,6144) | 0.0000 | 1 / 0.4060 | 64 |
| 505 | semantic_fault_twin | IMMEDIATE_UPDATE | persistent_nonbenign_twin [2016,6144) | 0.1483 | 1 / 0.1483 | 64 |
| 505 | semantic_fault_twin | M2N2_STYLE_CAUSAL | persistent_nonbenign_twin [2016,6144) | 0.8510 | 1 / 0.1490 | 64 |
| 505 | semantic_fault_twin | CANDI_STYLE_CAUSAL | persistent_nonbenign_twin [2016,6144) | 0.0581 | 1 / 0.3789 | 64 |
| 505 | semantic_fault_twin | QUARANTINE_1 | persistent_nonbenign_twin [2016,6144) | 0.1483 | 1 / 0.1483 | 64 |
| 505 | semantic_fault_twin | QUARANTINE_64 | persistent_nonbenign_twin [2016,6144) | 0.0007 | 1 / 0.3350 | 64 |
| 505 | semantic_fault_twin | QUARANTINE_128 | persistent_nonbenign_twin [2016,6144) | 0.0000 | 1 / 0.4060 | 64 |
| 505 | semantic_fault_twin | QUARANTINE_256 | persistent_nonbenign_twin [2016,6144) | 0.0000 | 1 / 0.4060 | 64 |
| 505 | semantic_fault_twin | QUARANTINE_512 | persistent_nonbenign_twin [2016,6144) | 0.0000 | 1 / 0.4060 | 64 |

## Causality, truth isolation and reproducibility

Pre-result freeze commit bd89ca252a1a84a3e68f38467984a05d0d2ea096; pushed trace commit 374a0081fff1ec5777f80555a1fec72748f0d308. Each remote SHA was verified before progressing. All runtime observations/model artifacts are hash-checked, no truth paths reach Runtime.step(x,t); runtime model config strips physical/arm IDs. Evaluator logs access only after trace manifest commit is a verified remote ancestor. Historical P4-A truth was already exposed; not strict confirmatory.

45/45 benign/fault-twin full-ledger and parameter equality;15/15 Q1/immediate parameter parity. Semantic twin failure is mandatory and included above: successful benign actions mirror fault actions. FROZEN/largerQ absence of twin errors arises from no adaptation, not better legitimacy identification.

16 tests passed before fits;3 additional reporting-boundary regression tests after outcomes (not a policy retune). Post-result independent audit verifies pre-update scores from previous snapshots, exact full-state hashes, weighted decoder SGD arithmetic and every effective ID at all622080 rows; this audit does not refit/run policies/change cutoffs. Full mutation ledger files and every timestep decoder snapshot are ignored onssh kuo; hashes/row counts/schema tracked in run_manifest and postrun_verification. Rollback NOT_IMPLEMENTED. No adapters, momentum state, scaler/EMA/reference/threshold/encoder mutations.

Exact commands/environment/model/data/config hashes: provenance/environment.json, freeze.json, trace_seal.json and results/run_manifest.json. Complete metrics, oldA score quantiles pre/post/horizon/final, weighted exposures and access logs are JSON artifacts. Reproduce via frozen inputs and raw P4-A files; no local raw acquisition.

Limitations: rank2 current-point model and gap0 candidate may reject benign intermittently alarming regimes; all Q≥64 censoring demonstrates this. Decoder-only adaptation has no regime partitioning and can trade new-mean utility for forgettingA. CANDI-style references in a fixed2D latent are not official end-to-end learned representations or SANA. One deterministic solver has no technical RNG replication;five source groups cover physical noise/fit variation only. Only this controlled generator/scoring/operator/gap/Q family was tested. Native official paths and TSB NOT_RUN; real timing/unsafe truth NOT_EVALUABLE. No RL, new feature/CV, classifier, generator changes or learned stopping.

STOP: reviewer should decide whether external/context evidence or post-write verification merits a separately frozen task. Results do not authorize tuning intermediateQ, adding gap tolerance, changing representation, recurrence or RL.
