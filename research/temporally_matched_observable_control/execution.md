# A+ execution record

* Starting scientific commit: `2810c346d40ceb3e011625f6fbf63db8833d9572`.
* Protocol/implementation seal: `de76db7` (the vectorized expansion is exactly
  the same feature-major transform covered by the tests).
* Cache: existing dense strong-observable cache, opened read-only through the
  local ignored symlink `data/strong_observable_control_cache_v1`.
* No model forward pass, checkpoint load, training, G1 continuation, or write
  to `reports/phase_g1` occurred.

The six fixed runs used the same command with these exact pairs:

| architecture | seed | cache directory | output |
|---|---:|---|---|
| LSTM | 11 | `data/strong_observable_control_cache_v1/lstm_11` | `results_lstm_11.json` |
| LSTM | 22 | `data/strong_observable_control_cache_v1/lstm_22` | `results_lstm_22.json` |
| LSTM | 33 | `data/strong_observable_control_cache_v1/lstm_33` | `results_lstm_33.json` |
| xLSTM | 11 | `data/strong_observable_control_cache_v1/xlstm_11` | `results_xlstm_11.json` |
| xLSTM | 22 | `data/strong_observable_control_cache_v1/xlstm_22` | `results_xlstm_22.json` |
| xLSTM | 33 | `data/strong_observable_control_cache_v1/xlstm_33` | `results_xlstm_33.json` |

Each invocation was:

```text
python3 scripts/temporally_matched_observable_control.py analyze \
  --cache-dir <cache directory> --seed <seed> --architecture <architecture> \
  --output research/temporally_matched_observable_control/results/<output>
```
The aggregate was then produced by the script's `aggregate` command with the
fixed bootstrap seed 901.  Only compact JSON summaries, hashes and reports are
tracked; no dense feature matrix or prediction array is copied into the branch.
