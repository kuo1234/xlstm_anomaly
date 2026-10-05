# E1 amendment01 — verification-only path repair

Execution stopped after final verifier failed with `TypeError: PosixPath object is not subscriptable` at the independent fit-only scaler rederivation. The verifier wrote `REPO[path]` instead of `REPO/path`. Nineteen raw/array identities, nine contract tests,38 score artifact/readout checks and actual-model future-suffix assertions had passed before the failure; final verification was incomplete.

**Scientific exposure: YES.** Training/scoring/phase analysis had completed. Observed verdict `NO_ROOT_EFFECT_GAP`, trace-macro Delta −0.12078079781520895 (PCA) and −1.131805478416729 (LSTM). This amendment must be committed/pushed before resuming verification. [Exposure/output fingerprint record](provenance/amendment01.json).

Repair only the independent verifier’s path composition, reusing each prepared array once; add explicit checkpoint/scaler SHA checks. No raw/feature/split/model/seed/budget/threshold/metric/gate change. All models and score arrays are retained. **No retraining or detector score regeneration.** Resume verification and deterministic metric/report replay only. Pre-amendment output hashes permit checking that this repair changes no scientific result.

This is a software verification amendment, not permission to rescue the negative gate. Future results retain original execution seal SHA and cite this amendment. Stop the lifecycle route after final evidence reporting under the frozen kill rule.
