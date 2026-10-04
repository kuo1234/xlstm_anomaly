# Common mechanism track
All9 arms share one initial linearAE per physical group, immutable A scaler/encoder/tau/cal references, stateless decoder SGD operator and identical pre-score ordering. Arms differ only in sample selection/timing and formal endpoint.

| Arm | Selected / pending | Effective mutation | Formal acceptance |
|---|---|---|---|
| FROZEN | none | none | N/A_NO_COMMIT, censored coverage0 |
| IMMEDIATE_UPDATE | current alarm point | immediate current-point SGD | N/A_NATIVE |
| M2N2_STYLE_CAUSAL | current score<=tau | predicted-normal SGD | N/A_NATIVE |
| CANDI_STYLE_CAUSAL | frozen A latent similarity plus hard-high/moderate-normal gate | selected buffer16 batch-SGD; queued selection alone is not exposure | N/A_NATIVE |
| Q1/64/128/256/512 | consecutive alarm evidence, no evidence replay | Q-th point PROMOTE SGD, then current alarm UPDATE until any clean reset | evaluator validates current payload and timestamp; premature separately |

Q1/IMMEDIATE mutation parity expected; action endpoint names differ. Quarantine counters are evidence only, do not affect detector state before release. No per-Q learning rates or representations. All buffered sample weights are1/16 at actual flush, current writes weight1. Every incoming observation's alarm uses the state before any mutation.

CANDI-style is a restricted common-operator version of latent-reference curation with MIN_SAMPLES buffering, not official reproduction. M2N2-style matches predicted-normal selection, not native EMA-before-score loop. Official native capacity/order differs and is NOT_RUN. No adapter/optimizer momentum/scaler/reference changes occur here; ledger explicitly logs them as absent/frozen. Weighted exposure count is distinct from effective update count and unique IDs.

No claim that delay, cache or selective updating is novel. No rollback implementation. Semantic twins must match the entire runtime trace and final parameter state; mirrored erroneous admission/exposure is included in metrics and aggregate negative-opportunity denominator.
