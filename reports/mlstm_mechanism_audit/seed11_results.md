# Seed-11 exploratory screen

This is the predeclared Stage-A screen, not a confirmatory test and not H3b.
The fixed observation-only extraction used the four shifted scenarios, five
conditions, source-disjoint 1000..1009 / 2000..2004 / 3000..3009 folds, W=64,
and a deterministic every-32nd timestamp cohort.  Labels were joined only
after each observation-only extraction returned.

Test AP:

| arm | AP |
|---|---:|
| H | 0.830556 |
| H+S | 0.947755 |
| H+M | 0.981010 |
| H+S+M | 0.973903 |

The increments are `M|H = +0.150454`, `M|H+S = +0.026148`, and
`S|H = +0.117199`.  The M|S increment is positive in all four scenario
strata (abrupt +0.0106, gradual +0.0272, recurring +0.0958, correlation
+0.0044).  Duration/severity values are retained in the machine-readable
result, but are descriptive only for this exploratory screen.

This clear seed-11 signal triggered the predeclared 11/22/33 replication
funnel.  No p-value or confirmatory gate is claimed.
