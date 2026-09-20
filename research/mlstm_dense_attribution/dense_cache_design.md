# Dense mLSTM attribution cache

This worktree is an exploratory follow-up to the frozen seed-11 mLSTM screen
at `b9a1a80e09aa4fe061878d4d66d67bc6ba22f490`. It does not modify G1, retrain
the detector, or reopen H3b.

The cache is produced once with the frozen vanilla-trained xLSTM seed-11
checkpoint, the validated CUDA inference adapter, `D=8`, `W=64`, and the
observation-only FastObserver/mLSTM observer path. Every valid right-edge
timestamp (`t=63,...,21503`) is extracted at decision stride one. Each stream
file stores only:

* `timestamp` (int64);
* reconstruction `score`;
* sLSTM `s_base18`;
* named mLSTM families `mh_base4`, `mc_base6`, `mn_base4`, `mm_base4`.

The cache deliberately contains no labels, event metadata, regime identity,
or evaluator strata. Those are regenerated only by the offline analysis after
the model/observer call has returned. The named families permit selecting a
stride and constructing causal rolling summaries without another model run.

The mLSTM columns retain the pinned order: hidden/readout (`Mh`, four), matrix
memory C (`MC`, six), normalizer n (`Mn`, four), and stabilizer m (`Mm`, four).
Each base column is expanded as current value plus causal mean/std/slope at
widths 4, 8, 16, and 32 decisions. Sparse stride-32 analysis first subsamples
the dense base sequence (`63,95,127,...`) and only then constructs rolling
features; this is required to reproduce the prior semantics.

Extraction used batch 256 after a bounded B128/B256 feature-equivalence
canary passed at the existing `atol=1e-5`, `rtol=1e-4` contract. No labels or
test metrics were used for that choice.

Post-extraction validation rehashed all 500 files, checked the exact seven
array names/shapes, finite values, and timestamp sequence; it passed in
`cache_validation.json`.
