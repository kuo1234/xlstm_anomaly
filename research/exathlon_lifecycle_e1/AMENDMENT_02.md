# E1 amendment02 — complete verification path repair

The amendment01 recheck passed saved-checkpoint/scaler SHA,38 score readouts, actual-model future-suffix invariance and independently rederived fit-only mean/std. It then stopped at the calibration threshold checker, where a second `REPO[path]` expression remained. Amendment01 fixed one site and did not catch the repeated defect.

**Scientific exposure: YES, unchanged.** The same `NO_ROOT_EFFECT_GAP` result and score arrays remain retained. This amendment is committed/pushed before resuming checks. Repair the second path expression and add an AST regression scanning every E1 script for subscripted Path constants. New regression failed on the old code and passes after repair. Contract tests now total10; original nine scientific tests are unchanged.

No model/data/preprocessing/seed/budget/threshold/metric/gate change; no retraining or score regeneration. [Unchanged scientific output hashes](provenance/amendment02.json). Resume independent threshold checks and deterministic metric replay. The negative lifecycle route remains stopped after evidence reporting; these are verifier repairs, not outcome-driven protocol changes.
