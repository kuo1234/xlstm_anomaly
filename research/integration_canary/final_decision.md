# Integration canary decision

## Decision

**BLOCKED**.

Canary A passed feature-level V0/FastObserver equivalence on the real frozen
seed-11 checkpoint at B=1/8/128. Canary B produced a material real training
speedup (about 5.24x) and finite, decreasing losses, but CUDA validation MSE
was not equivalent to vanilla across the three executed epochs under the
predeclared 1% criterion: 0.191%, 1.088%, and 3.649% symmetric differences.

Consequently the CUDA backend is not approved for new scientific training, and
the optional real-pipeline FastObserver extraction was not run. Existing
Phase-F/G checkpoints, results, and conclusions were not modified. No G1 rerun,
long-context experiment, five-seed training, mixed precision, or mLSTM study
was started.

## Required interpretation

The result establishes that the repaired CUDA path is fast and finite on GB10,
but this bounded real training canary does not establish trajectory fidelity.
The divergence must be diagnosed before using CUDA for scientific training.
The validated FastObserver itself remains feature-equivalent to V0 in this
checkpoint canary.
