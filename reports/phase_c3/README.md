# C3 — cross-seed characterization

C3-A: **SEED-ACTIVE**. Released backbone is identical; fresh SANA initialization and causal adaptation trajectory change with SEED.
C3-B: complete, seeds0–4 within each of six fixed conditions. H1-admission is evaluated separately; **H1-harm NOT TESTED**. Phase D remains locked.

Prospective commit `8b554c5` was pushed before pilot execution. Pinned CANDI `28c9679e503832f59e351208cde63657fcb51cad` and released checkpoints/config/preprocessing unchanged except SEED; TRAIN.ENABLE=False; no retraining/tuning.

## Pilot and integrity

Seed0 integrity rerun exactly matches the accepted alpha5 native control in scores, final state and full observer trajectory. Pre-backbone, SANA-in/out, and global RNG before/after hashes are recorded in seed_effectiveness_pilot.json. RNG differences alone are not the activity criterion. Native CANDIAdapter.__init__ constructs new SANA input/output modules after the pretrained backbone is loaded; their Conv1d/Linear/attention initialization consumes the seeded Torch RNG. The seed0 alpha1 rerun fills a previously missing stable-ID audit and exactly matches its original scores/model/metrics. Neither technical rerun is an extra replicate.

## Within-condition seed variation

AUROC and native trapezoidal PR-AUC: mean ± sample SD over five effective adaptation seeds. Committed contamination gives min–max across seeds; no configurations are pooled.

| Machine | alpha | AUROC | PR-AUC | Committed contamination range | Admission seeds |
|---|---:|---:|---:|---:|---:|
| SMD_1-8 | 0.5 | 0.859316 ± 0.004471 | 0.447313 ± 0.005433 | 3.776–3.977% | 5/5 |
| SMD_1-8 | 1.0 | 0.860283 ± 0.004671 | 0.448305 ± 0.005996 | 3.864–4.057% | 5/5 |
| SMD_1-8 | 5.0 | 0.870656 ± 0.004542 | 0.452829 ± 0.004095 | 3.780–4.025% | 5/5 |
| SMD_2-1 | 0.5 | 0.691483 ± 0.000447 | 0.306608 ± 0.000254 | 1.884–1.976% | 5/5 |
| SMD_2-1 | 1.0 | 0.708467 ± 0.004260 | 0.313771 ± 0.001108 | 1.725–1.860% | 5/5 |
| SMD_2-1 | 5.0 | 0.730266 ± 0.029897 | 0.323701 ± 0.018297 | 1.583–1.703% | 5/5 |

Full seed-level values, all queues/denominators, latency summaries, pending/update counts, repeated exposures, hashes and provenance are in replication_results.json; seed_results.csv provides a flattened table (blank cells mean N/A). Full stable-ID event/optimizer traces remain in logs or referenced sealed Phase C v2 paths. Historical inherited per-run COMPLETE_PENDING_V2_VERIFICATION status is only a runner placeholder; this C3 report and verification.json contain the final C3 conclusions.

## Admission and exposure characterization

These statements use stable window IDs and true evaluator labels after execution, never native anomaly counters. Nonzero admission does not demonstrate performance harm. Hard/moderate comparisons with empty queues are N/A.

- SMD_1-8 alpha0.5: hard > moderate candidate contamination in 5/5 defined seeds; committed comparison: N/A (no comparable committed queues). Candidate→commit difference ≥1 percentage point by queue (seed IDs): {'all': [], 'hard': [], 'moderate': []}. Repeated anomalous loss exposures (seed0–4): [0, 0, 0, 0, 0].
- SMD_1-8 alpha1.0: hard > moderate candidate contamination in 5/5 defined seeds; committed comparison: 4/4 defined seeds. Candidate→commit difference ≥1 percentage point by queue (seed IDs): {'all': [], 'hard': [], 'moderate': []}. Repeated anomalous loss exposures (seed0–4): [0, 0, 0, 0, 0].
- SMD_1-8 alpha5.0: hard > moderate candidate contamination in 5/5 defined seeds; committed comparison: 5/5 defined seeds. Candidate→commit difference ≥1 percentage point by queue (seed IDs): {'all': [], 'hard': [], 'moderate': []}. Repeated anomalous loss exposures (seed0–4): [0, 0, 0, 0, 0].
- SMD_2-1 alpha0.5: hard > moderate candidate contamination in 5/5 defined seeds; committed comparison: 5/5 defined seeds. Candidate→commit difference ≥1 percentage point by queue (seed IDs): {'all': [], 'hard': [], 'moderate': []}. Repeated anomalous loss exposures (seed0–4): [1192, 1252, 1148, 1148, 1204].
- SMD_2-1 alpha1.0: hard > moderate candidate contamination in 5/5 defined seeds; committed comparison: 5/5 defined seeds. Candidate→commit difference ≥1 percentage point by queue (seed IDs): {'all': [], 'hard': [0, 1, 2, 4], 'moderate': []}. Repeated anomalous loss exposures (seed0–4): [1116, 1156, 1068, 1136, 1108].
- SMD_2-1 alpha5.0: hard > moderate candidate contamination in 5/5 defined seeds; committed comparison: 5/5 defined seeds. Candidate→commit difference ≥1 percentage point by queue (seed IDs): {'all': [], 'hard': [0, 1, 2, 4], 'moderate': []}. Repeated anomalous loss exposures (seed0–4): [712, 748, 660, 716, 668].

The ≥1 percentage-point materiality threshold is descriptive, prospectively fixed, not a new GO gate. Queue-specific deltas are also reported. STEPS repeats are exposures of the same committed windows, not new independent anomalies. Pending-tail selection differences are not decontamination evidence.

## Validity and scope

All five initialized-model/score/final-state hashes are checked for distinctness within each condition, with identical loaded backbones wherever newly instrumented. Reused seed0 rows retain their measured full initialization hash and explicitly N/A separated SANA/backbone hashes. No absent measurement is fabricated. Variation is conditional on the fixed released backbone and data; it is not training-seed or dataset replication.

No test-informed tuning, no paper-metric chasing. Paper fidelity remains MISMATCH / UNRESOLVED_LINEAGE. The official native label-passing API and known bookkeeping defects remain unchanged; the previously validated label-isolated overlay remains separate. C3 uses the accepted native passive observer with new read-only initialization hashes.

New execution count: 26; four sealed seed0 rows reused. Measured native-entry runtime including observers: 704.986 s; peak allocated/reserved GPU memory 2.523/3.342 GiB. Per-run process wall times and native-entry CUDA event spans are logged; event spans include host gaps, not pure kernel time.

No controlled contamination, Phase D, xLSTM/LSTM, probes, H4 or H3b executed. Return for external review before any next phase.
