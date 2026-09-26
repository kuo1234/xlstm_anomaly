# Dataset requirements

This file builds on the Issue #2 audit (`research/new_normal_dataset_audit/`, status `SEMANTIC_M6_DATA_PARTIALLY_AVAILABLE`). No dataset was downloaded or opened for this report, and no label was inspected. The central constraint is unchanged: no verified public dataset combines grounded benign regime changes, persistent-fault episodes with identity and duration, A→B→A recurrence, context truth and event-disjoint splits. The stories below are chosen so that the primary paper does not need such a dataset.

## Per-story requirements

| Story | Minimum data | Existing sufficient? | Candidate sources (from the Issue #2 audit unless noted) | Main gap |
|---|---|---|---|---|
| P1 | Generator with six episode types (stationary, transient anomaly, persistent predictable fault, benign A→B, benign A→B→A, ambiguous) × three identifiability strata × a context channel of controllable reliability | **Yes for the primary claim**, once a new generator is written | New generator, independent of protocol-frozen `m0.synthetic`; semi-real anchors: e-Energy smart-building (normal / normal-drift / attack), Exathlon recovery intervals ([Jacob et al. 2020](https://arxiv.org/abs/2010.05073)), SCAR/STAD generators for comparability | A real anchor with decision-level labels; e-Energy licence and event IDs unresolved |
| P2 | P1 streams plus a delayed-confirmation channel (latency L, coverage c) | Yes (synthetic) | P1 generator; e-Energy as a partial real check | Real confirmation latencies are unknown; they must be swept rather than estimated |
| P3 | Authorisation events (setpoint, mode, recipe, work order) with timestamps, benign responses and coincident faults | **No** | Extended TEP (DTU) can simulate mode changes and faults; e-Energy has setpoint semantics; SWaT/WADI carry commands but only attacks | No public stream with authorisation truth and coincident faults |
| P4 | Fleet of ≥ 20 same-schema entities with documented fleet-wide benign changes and entity-specific faults | **No** (for semantics); SMD machine groups only for label-free descriptive co-occurrence | SMD (28 machines, groups 1–3); public wind-turbine SCADA fleets (not yet audited); Borg traces (no fault labels) | Change logs for fleet-wide benign events |
| P5 | ≥ 2 entity families with the same dimensionality inside each family, verified-normal prefixes and held-out labeled suffixes | Partly | SMD leave-one-machine-out (exploratory only: Issue #4 found all 28 label vectors had been parsed); PreDist substations (group by configuration); C-MAPSS engine subsets; wind-turbine fleets used by [Jonas & Meyer 2025](https://arxiv.org/abs/2504.17709) / [Roelofs et al. 2024](https://arxiv.org/abs/2404.03011) (availability to be checked) | A confirmatory family with untouched labels |
| N1 | Attackable streams with white-box access to gates | Yes (synthetic); SWaT/WADI under access terms | Synthetic; SWaT/WADI | Access grants |
| N3 | Controllable simulator with actuators | Only a simulator | Extended TEP | Safe-probe definitions |

## Generator requirements for P1 (design constraints, not an implementation)

1. **Equivalence by construction.** For the non-identifiable stratum, benign and fault episodes must be generated from the same law for the full observation history, with the semantic label drawn independently. Leakage is tested by the K3 classifier suite.
2. **Context-separable stratum.** Benign and fault share the X-law but differ in the context law. Context reliability ρ controls how often the context channel reports the truth.
3. **X-separable stratum.** The laws differ in X by a controlled effect size, so that sensitivity is measurable.
4. **Decision-level truth.** Every timestamp carries the semantic truth, and the evaluator also tracks the detector's promotion state. This makes absorption time, false promotion, masking on paired fault classes, and recovery delay after A→B→A computable.
5. **Episode-disjoint splits** and pre-registered seeds, following the project's sealing conventions.
6. **Independence from M0/M1 code.** The protocol-frozen `m0.synthetic` generator is reproducible bit-for-bit only on the GB10 stack. P1 should use a new, separately versioned generator and should cite the old one only as design lineage.

## Licensing and access actions (before any P3 or P5 work)

- e-Energy smart-building data: resolve the licence, pin CSV hashes, and reconstruct event IDs from the paper's scenario protocol (open action from Issue #2).
- PreDist: pin the version and select stations by configuration.
- Wind-turbine fleets: audit the public SCADA fleets used in the transfer literature. They were not covered by Issue #2.
- SWaT/WADI: manual access grants are still required.
