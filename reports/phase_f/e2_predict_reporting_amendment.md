# E2 predict-interface clarification — reporting only

The accepted E2 evidence at `4d49f1d` is preserved without modification or
recomputation. Its `native_predict_target_is_x_not_label` check exercised
`model.predict_step((x, x), 0)`, **not** upstream dataset/predict integration.
The official SlidingWindowDataset instead supplies `(window, endpoint_label)`.
Consequently upstream predict_step remains interface-inconsistent with that
dataset. The old check establishes only the explicitly supplied `(x,x)` case.

This does not invalidate the common observation-only score path, which computes
MSE(model(x), x) and never calls predict_step. Native training_step and
validation_step reconstruct x against x; test_step also computes reconstruction
error against x. Phase F uses direct forward reconstruction, not native predict.
A fail-closed guard and negative-control test must prevent native predict_step
from being called by the scientific path. This clarification makes no change
to sealed E2 arrays, tests, schema, hashes, architecture, or backend.
