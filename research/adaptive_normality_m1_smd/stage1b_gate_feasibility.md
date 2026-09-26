# Stage 1B-R final-gate feasibility note

This note is frozen before any Stage 1B-R model is trained or evaluated. It
records a deterministic consequence of the original, unchanged 28-machine
Stage-1 standalone xLSTMAD-F gate. It introduces no stopping rule and does not
change the final protocol.

The Stage-1A result committed at
`2792b1ee2b74bec97c6e70996a808ea1f3bba974` already records three of its nine
machines with xLSTMAD-F normal-point FPR greater than 0.05:

| Machine | xLSTMAD-F normal-point FPR |
|---|---:|
| machine-2-8 | 0.3490938761487589 |
| machine-3-11 | 0.3478153105304157 |
| machine-3-7 | 0.2583972871675888 |

The frozen full Stage-1 gate permits at most two such machines. The standalone
xLSTMAD-F route therefore cannot pass that component on the complete 28-machine
family.

The sum of all nine observed xLSTMAD-F normal-point FPR values is
`1.014164845328001`. Even if each of the remaining 19 machines had FPR exactly
zero, the best possible 28-machine equal-machine macro FPR would be

`1.014164845328001 / 28 = 0.036220173047428604`,

which exceeds the original gate limit of `0.02`. This independently makes the
standalone route impossible under the frozen macro-FPR component.

This note applies only to standalone xLSTMAD-F. The frozen full
`forecast_control_fusion` complement route remains subject to its original
28-machine gates and will be assessed separately after the Stage 1B-R score
seal. This is a feasibility statement, not an efficacy result.
