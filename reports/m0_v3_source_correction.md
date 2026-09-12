# v3 eligibility evidence correction: GHL is simulated

2026-09-12, no detector results generated or inspected. The frozen v3 assignment rule remains unchanged.

The initial uncommitted A2 manifest built from the strict audit's synthetic flags selected GHL 032. A subsequent source-type verification found that the **original authors** generated the GHL data using a Modelica model of a gasoil plant: [Filonov, Lavrentyev, Vorontsov, arXiv:1612.06676](https://arxiv.org/abs/1612.06676). The abstract states the simulation origin; no model-performance section was inspected. This was missed in the strict audit, whose files remain unchanged as required.

The standing no-synthetic criterion therefore excludes all 23 GHL candidates, in addition to CATSv2. This changes an evidence fact, not an optimization objective or scientific threshold. The initial manifest is explicitly rejected and preserved under `reports/phase_a_v3/rejected_provisional/`; it must never be used for experiments. Commit this evidence correction before rerunning assignment. Released dataset-family identity does not turn a simulation into real measurements.

Expected feasibility issue, determined solely from metadata: periodic requires all three remaining SMD files. The random_walk bucket has three eligible families (SMD, OPPORTUNITY, Exathlon), and v3's committed hard diversity constraint requires one from each. No unused periodic-tagged SMD file remains for random_walk. If the exact solver confirms infeasibility, STOP A2 without relaxing that constraint. One possible future amendment is to optimize bucket diversity **subject to globally feasible file allocation**, rather than requiring each bucket's standalone maximum; this is a proposal only, not implemented here.

A1 remains valid and Phase B CPU scaffolding remains authorized independently of A2 completion under the user's v3 authorization. No GPU training, detector fitting or Phase C is authorized.
