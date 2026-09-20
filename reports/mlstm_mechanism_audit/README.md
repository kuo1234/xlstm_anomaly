# Frozen-checkpoint mLSTM mechanism audit

This branch is an engineering plus exploratory mechanism audit.  It uses the
vanilla-trained seed-11/22/33 xLSTMAD checkpoints and the existing CUDA
inference overlay only.  CUDA training is explicitly out of scope.

The actual xLSTM 2.0.5 architecture, state semantics, frozen compact schema,
inference canary, and observer benchmark are documented in the neighboring
reports.  `scripts/mlstm_observer.py` captures q/k/v and replays C/n/m/h
read-only; it does not alter the model equations or output.

The final exploratory decision is `M1_REPLICATED_SIGNAL`: mLSTM summaries add
clear information beyond score/history across the three-seed funnel, while the
increment beyond sLSTM is positive but heterogeneous.  This is not H3b and
does not reopen the previous H3a STOP.  No G1 artifact was rerun or modified.
