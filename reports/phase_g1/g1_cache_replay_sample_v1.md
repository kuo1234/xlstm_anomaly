# G1-R1 bounded cache replay sample

This sample is sealed before any quarantined cache array value is opened. It is
not chosen using labels, outcomes or cache contents.

The deterministic sample is the Cartesian product of:

- detector seeds 11 and 55;
- source seeds 1000, 2000 and 3000;
- scenarios abrupt and correlation;
- conditions none and mixture;
- architectures xLSTM and LSTM.

The fixed ordering is detector seed, source seed, scenario, condition and
architecture, yielding 48 stream/backbone pairs. Replay compares only
provenance and observation-derived arrays: ordered row keys, evaluator labels,
reconstruction scores, internal18, history14, combined234,
history+combined248 and the CANDI history where applicable. No AP, AUROC,
class-prevalence summary, probe fit, C selection or other scientific metric is
permitted during this replay.
