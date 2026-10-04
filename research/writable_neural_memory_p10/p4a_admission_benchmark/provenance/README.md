# Provenance and exposure chronology
All acquisition and audits are on ssh kuo. No local raw download.
Official repository sources are pinned, byte-hashed with acquisition UTC in source_files.json. M2N2: no LICENSE in pinned tree (UNKNOWN, no code redistributed). CANDI: modified MIT Non-Commercial with Permission. StrAD: AGPL-3.0 with upstream notices; source code remains ignored.

TSB archive was previously acquired from official thedatum.org. Existing reports/phase_a/downloads.json records acquisition and archive hash; reused bytes are verified before each audit. Per-CSV hashes are checked against prior reports/phase_a/candidate_inventory.json. Public derivative SWaT release availability does not resolve underlying raw-source terms. No restricted source bypass or mirrors.

All 75 TSB-drift candidate labels were exposed historically during M0. This task also inspected prior metadata (including anomaly-prefix counts) before new mask computations. All 47 non-simulated candidates are preselected by source status, not favorable label outcomes; 28 GHL/CATSv2 simulation-source exclusions retain full metadata. Native SMD source mappings and exact Exathlon feature duplicates come from prior source_groups.json / trace_relations.json. Unknown physical independence remains unknown.

Full controlled generation and TSB masked qualification require freeze_inputs.json to exist, all frozen input hashes to match, and its commit to be an ancestor of the verified remote research branch. Small hand-crafted unit fixtures exercised only data contracts before the freeze. No model scores, model training, detector feature selection, online policies or memory writes occur.

qualification_access_log.json after execution records each actual CSV label read, frozen commit and remote SHA. This is prospective frozen-method exploratory qualification on previously exposed data, never strict confirmatory. Generator normative truth is disclosed synthetic intent, never operational unsafe truth.
