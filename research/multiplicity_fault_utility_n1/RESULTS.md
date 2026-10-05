# N1 — fault utility result

**FAULT_SCORE_SUPPORT_INSUFFICIENT. Neither positive nor negative utility mechanism established. Overall research goal remains active.**

Seal `dd59bc0d2c4f3f323afd06d91ae79c713805dab5` preceded new inference. Models/scaler/N0 thresholds remained fixed; no retraining/threshold tuning/lifecycle rescue. Seven released events include4 known/3 unknown; unknowns excluded from utility.

| app | driver native event seconds | PCA available | LSTM available | extra targets blocked by history32 |
|---|---:|---:|---:|---:|
|6|64|54|22|32|
|9|69|42|10|32|
|10|64|46|14|32|

All3 driver events violate>=95% coverage: PCA84.38%/60.87%/71.88%, LSTM34.38%/14.49%/21.88%. Only the executor event in app9 is eligible (327/328 in both). A single eligible trace cannot support the prospective3-app utility comparison. Conditional fractions for ineligible events are recorded but never promoted to primary evidence.

Eligible app9 executor event has up to36.39percentage-point PCA alarm-fraction variation versus0.92pp LSTM across fixed doses; this is not a replicated2-family effect. Neither this event nor a lower coverage/margin can rescue N1. [All operating points](results/event_operating_points.csv), [gate](results/gate.json).

## Prospective availability diagnostic — exploratory mechanism clue

Direct raw-feature enumeration exactly reproduces both score-validity masks for all targets in all3 traces: PCA requires observed/finite current vector; LSTM additionally requires finite32-step history. Each driver event has exactly32 otherwise-scorable targets blocked only by history. Input losses include3/4/3 absent source timestamps and7/23/15 observed but invalid feature vectors. Executor and unknown events show0 additional history-blocked targets. This supports a code-level explanation in these observed records, not a novel universal mechanism, causal repair benefit or unseen replication.

Next independent experiment should freeze availability amplification and matched healthy controls before opening remaining driver-failure traces. It must separate generic missing-data handling (occupied) from a verified fault-selective benchmark/evaluation risk. Do not change LSTM window, fill policy or evaluate repaired detection on these exposed traces as if prospective.

[Independent verification](provenance/verification.json):288 direct event/threshold counts,14 availability checks,6 score hashes; unchanged inherited operating points/checkpoint inputs. Tests cover missing scores and closed ranges. [Diagnostic decomposition](results/availability_diagnostic.json). No synthetic-normal replacement, iid significance, first-onset timing, xLSTM advantage, noveltyGO or methodGO claimed.
