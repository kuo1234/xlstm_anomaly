# Dense stride-1 result

This is the original G1 temporal interpretation: every right edge from
`t=63` onward is a decision, and widths 4/8/16/32 refer to consecutive dense
decisions. Mixed drift+anomaly rows are excluded from the primary binary
cohort. All arms use identical row construction and source/event order.

| arm | dimension | test AP |
|---|---:|---:|
| H | 14 | 0.789781 |
| H+S | 248 | 0.933408 |
| H+M_full | 248 | 0.935443 |
| H+S+M_full | 482 | 0.950065 |
| H+Mh | 66 | 0.878984 |
| H+MC | 92 | 0.905477 |
| H+Mn+Mm | 118 | 0.925963 |
| H+M_noC | 170 | 0.936035 |
| H+S+M_noC | 404 | 0.943456 |

The key increments are:

* `M_full|H = +0.145661`;
* `M_full|H+S = +0.016657`;
* `S|H = +0.143627`.

Thus the mLSTM-layer signal survives dense decisions, although its conditional
gain after sLSTM is smaller than in the sparse screen. The dimension-matched
`H+M_full` versus `H+S` difference is only `+0.002034`, not evidence of a
backbone ranking.

Scenario conditional increments (`M_full|H+S`) are:

| scenario | increment |
|---|---:|
| abrupt | +0.004481 |
| gradual | +0.025967 |
| recurring | +0.018866 |
| correlation | +0.007554 |

The gradual case has the largest conditional `M_full|H+S` increment, while
recurring has the largest unconditional `M_full|H` increment. Recurring is
therefore not uniquely dominant under dense semantics. No confirmatory
p-values are reported for this one-seed exploratory screen.

Machine-readable outputs: `stride1_results.json`,
the excluded `stride1_results.predictions.npz`, and
`stride1_results_strata.json`.
