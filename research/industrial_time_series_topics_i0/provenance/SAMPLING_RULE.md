# Pre-data qualification rule

2026-10-06. Active user goal: investigate industrial time-series application gaps and propose feasible topics, no longer limited to anomaly detection. User prioritizes process quality / soft sensing. This audit does not reopen any historical research STOP or permit a new architecture or large experiments.

Search broadly across quality/soft sensors, batch manufacturing, machining/assembly, maintenance, energy/control. First qualify data/labels/clock and prior-art; do not select by local model outcomes.

Bounded first acquisition:
1. Official InduTS-SS repository pinned metadata/tree/README and at most two lexicographic small real-process data assets <=5MB each; no simulated TE as evidence of natural industrial generality. Do not run training loaders or import upstream models.
2. Pharmaceutical dataset official Figshare collection: resolve explicitly v1/v3 identity; retrieve collection/article metadata, Laboratory.csv and one lexicographic process-time-series asset <=10MB if available. Keep full-batch extracted features distinct from prefix features. No lab timestamps inferred from plateaus or filenames.
3. PyScrew official repo/Zenodo metadata; at most one <=5MB example or metadata table for physical operation/workpiece/condition identities. Do not download all34000 traces.
4. Other machining/maintenance/energy sources: metadata/method sections only initially; acquire a tiny official asset only if exact version/labels are justified and fits10MB cap.

No predictive fit/correlation/source ranking, no new network, no control action, no message to authors. Raw data/text under ignored data/industrial_time_series_topics_i0/. Source/byte/schema feasibility is distinct from novelty and predictive utility; blocked or unsupported claims stay unknown.
