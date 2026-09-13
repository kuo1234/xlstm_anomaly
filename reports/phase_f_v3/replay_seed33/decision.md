# F3-R decision

`STOP_AFTER_DIAGNOSIS`

The seed33 epoch-29 replay exactly reproduces sealed epochs 1--28.  The
non-raising canary has one raw-output element outside the frozen allclose rule,
while reconstruction score, common18, all six recurrent manual/native
reference checks, finite/gate checks, observer on/off, reset, and prefix
causality all pass.  Stage localization shows the first failed comparison at
`output_projection`; `GELU` and every encoder/decoder LSTM stage pass.

This is an implementation failure localization, not an anomaly-performance or
scientific-hypothesis result.  No backend/tolerance/architecture change is
authorized.  No F-v4 is created automatically.

