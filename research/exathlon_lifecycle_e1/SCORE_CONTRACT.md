# Score availability and lineage

Every score-table row contains raw_trace_id,target_timestamp,available_at,score,baseline_id,checkpoint_hash,preprocessing_hash,scaler_hash,fit_split_id,calibration_split_id,target_observed,role. Native timestamp is the target; available_at=target. NaN marks missing score rather than zero/normal. Primary finite score requires available_at<=target and observed target.

PCA computes with current t; LSTM forecasts before target then residual is available on target arrival. No future averaging, readout shifts, smoothing, EWMA or warm-up fill. Full history is bounded at the target, independent trace state resets. Post-seal tests compare actual model scores under a changed future suffix and independently rederive PCA/LSTM scores.

Complete compressed score arrays/checkpoints/scaler live in ignored data/exathlon_lifecycle_e1. Tracked artifact ledger hashes every output; scripts regenerate the files from pinned raw identities. Serialized-container hashes and canonical array hashes are distinguished. Deployment-source clocks/sensor transport delay are unknown; availability is the mathematical observation contract, not measured wall-clock latency.
