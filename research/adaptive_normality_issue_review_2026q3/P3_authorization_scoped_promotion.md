# P3 — Authorization-scoped normality promotion under coincident faults

**Source issue:** [GitHub #7](https://github.com/kuo1234/xlstm_anomaly/issues/7)

**Assessment date:** 2026-09-27
**Status:** Literature and design only; no simulator runs or data downloads were performed.

## Feasibility assessment

**Algorithmic feasibility: high. Empirical feasibility: medium in a simulator, low for a real-plant claim without a partner. Novelty: narrow and at risk.** The core rule is implementable: treat a trusted operation authorization as a bounded prediction of expected process effects, then keep monitoring both the residual inside that scope and every signal outside it. A blanket “authorized, therefore normal” rule is unsafe by construction.

The novelty claim cannot be “use context during process transitions.” Multimode monitoring, context-conditioned limits, expert-knowledge fusion, and transition-fault monitoring already exist. In particular, Wang et al. (2020) monitor the trajectory and transition speed during a Tennessee Eastman mode 4-to-2 transition, generate operational faults from HAZOP, and report false/missed alarms plus detection and rescue time. That is close prior art for catching faults during an authorized transition. The possible residual is more specific: an independently sourced, time-bounded authorization carries an explicit effect scope, and the monitor tests whether observed changes stay within that scope while retaining sensitivity to a coincident fault. This is a **provisional novelty hypothesis**: a full-text search of industrial command-scoped suppression, maintenance-window handling, and authenticated control context is still required. Even this narrower claim needs a head-to-head test against transition-trajectory and conditional process monitors.

The best first test is controlled simulation, not a public observational dataset. Tennessee Eastman Process (TEP) simulators provide multiple operating modes, setpoint changes, injected fault timing, and process/control signals. pyTEP supports interactive process reconfiguration; COSTEP provides an open, instrumented Simulink implementation with configurable fault activation. The extended TEP reference dataset covers six modes and 28 faults, but it does not supply real authenticated work orders or authorization objects. A simulator can therefore establish mechanism behavior under known scenarios, not prove that a plant's authorization semantics or causal scope are correct. The COSTEP simulator was introduced in a 2025 SoftwareX paper; a 2026 paper describes its use for process monitoring and fault analysis. [pyTEP paper](https://doi.org/10.1016/j.softx.2022.101053), [COSTEP simulator paper](https://doi.org/10.1016/j.softx.2025.102217), [COSTEP monitoring paper](https://doi.org/10.1016/j.dche.2026.100328), [COSTEP repository](https://github.com/kennyuren/COSTEP), [extended TEP dataset](https://tulaut.github.io/ds_ExtendedTennesseeEastman)

## Closest prior art and what remains open

| Work | Overlap with P3 | Consequence for novelty |
|---|---|---|
| Wang, Zheng & Wong, *Trajectory-based operation monitoring of transition procedure in multimode process* (2020) | Monitors a prescribed transition trajectory and transition speed; evaluates HAZOP-derived operating faults during a TEP mode 4-to-2 change and reports false alarms, misses, detection time, and rescue time. | The strongest overlap. Reproduce or compare to this transition-monitoring baseline. A new claim must show benefit from authenticated, field/effect-scoped authority during coincident independent faults, not merely improved transition monitoring. [Paper](https://doi.org/10.1016/j.jprocont.2020.09.008) |
| *Statistical Monitoring of Processes with Multiple Operating Modes* (IFAC DYCOPS, 2019) | Learns multiple normal modes and updates monitoring for a new mode while still monitoring for faults. | Mode adaptation and distinguishing a new mode from fault behavior are established. [Paper](https://doi.org/10.1016/j.ifacol.2019.06.134) |
| Steenwinckel et al., *FLAGS: A methodology for adaptive anomaly detection and root cause analysis on sensor data streams by fusing expert knowledge with machine learning* (2021) | Combines sensor streams, contextual data, expert knowledge, semantic fault rules, anomaly detection, and feedback-driven adaptation. | Semantic context and expert-knowledge fusion are not novel by themselves. P3 must specify the bounded authorization contract and show the coincident-fault safety property. [Paper](https://doi.org/10.1016/j.future.2020.10.015) |
| Anzai & Pinto, *Distinguishing Process Faults from Model Drift Through Variable Contribution Analysis* (2026) | Explicitly separates operating-mode/model drift from process fault contributions and tests five TEP mode transitions. | Directly occupies the broad “legitimate change versus fault” framing. P3 needs to add the independent authorization contract and evaluate simultaneous faults, not just classify a mode shift after detection. [Paper](https://doi.org/10.3390/pr14050859) |
| Wadinger & Kvasnica, *Adaptable and Interpretable Framework for Anomaly Detection in SCADA-based industrial systems* (2024) | Uses dynamic conditional-probability limits, self-adaptation, and a physics-based model; case studies include changing conditions and hardware faults. | Context-adjusted limits plus physical-model residuals are an important baseline, especially for the scoped residual arm. [Paper](https://doi.org/10.1016/j.eswa.2024.123200) |
| Hayes & Capretz, *Contextual anomaly detection framework for big sensor data* (2015) | Separates content-level anomaly candidates from context-level filtering. | Context used to prune alerts is longstanding; P3 must show why an authorization's semantics and scope improve safety over generic context filtering. [Paper](https://doi.org/10.1186/s40537-014-0011-y) |
| Reinartz et al., *An extended Tennessee Eastman simulation dataset for fault-detection and decision support systems* (2021) | Provides repeated normal/fault simulations across operating modes and transition conditions. | Useful for baseline evaluation, but not a source of real authorization provenance. [Dataset paper](https://doi.org/10.1016/j.compchemeng.2021.107281) |

More generally, a full-text novelty check should search for maintenance-window masking, alarm suppression during transitions, mode-conditioned residual monitoring, and signed command/authorization context in industrial control systems.

## Proposed research question

Given a process stream and a separately authenticated, time-limited operation authorization, can a monitor issue scope-limited **would-promote** decisions—testing residuals within the named effect scope and continuing ordinary monitoring elsewhere—so that legitimate transitions cause fewer false alarms without admitting fault-affected observations into the normal pool?

An authorization is not inferred from the sensor stream and does not contain a fault class or test label. Represent it as a versioned record containing at least the asset, trusted issuer, unique command/record ID, approved setpoint/mode change, issue time, valid start and expiry, expected direction/range/ramp, revocation/cancellation status, and a predeclared list or graph of process variables allowed to respond. Authentication establishes record provenance and integrity under a stated issuer/key trust assumption; it does **not** prove that the scope is semantically correct or that the command was actually executed. Bind the record to controller acknowledgement and observed manipulated-variable behavior, and treat a validly signed but incorrect scope as a trust-boundary failure: without an external authority to verify semantics, the detector may not identify this error. A sensor-derived or detector-generated “authorization” would make the design circular. Missing, stale, replayed, unsigned, revoked, out-of-range, or asset-mismatched records fail closed. Here, “fail closed” means disable authorization-based discounting and promotion while continuing the ordinary detector; it does not mean suppressing all monitoring.

For authorized variables, condition a normal-response envelope on the approved command and transition phase, then monitor normalized residuals against that envelope. Variables outside the scope continue through the ordinary detector. Define the candidate promotion unit as a whole multivariate window: if any in-scope residual breaches its envelope or any out-of-scope channel alarms, the entire window is ineligible. The primary study audits this `WOULD_PROMOTE` decision and does not apply model updates, so it makes no claim about downstream model contamination or adaptation harm. An adaptive follow-up would be a separate study and authorization.

## Proposed experimental architecture

### 1. Simulator and scenario manifest

Use one pinned TEP simulator as the primary testbed. pyTEP is the most direct option for interactive setpoint changes; COSTEP is an alternative with an open Simulink model, internal process access, and configurable fault activation. Record software/version, controller, mode-transition procedure, random seeds, sampling cadence, measured/manipulated signals, fault injection point/time, and full command/authentication log. Represent authorization provenance in the simulator with an explicit synthetic trust field; this is not a cryptographic validation or a real issuer trust study. MATLAB/Simulink licensing and version requirements are a practical constraint for both simulator routes.

Before generating test traces, freeze the authorization schema and the effect-scope map from the simulator's control procedure and process documentation. Domain engineers define which variables may change, the allowed envelopes, and their expiry; do not choose these based on test fault outcomes. Where causal descendants are used, use a graph obtained from simulator equations/control documentation or normal-only training runs, then freeze it.

Build a factorial, run-level scenario set:

- stable normal operation with no command;
- valid authorized setpoint/mode transition with no fault;
- fault-only/no-transition runs paired by fault type, simulator seed, and severity with coincident-fault transition runs;
- a transition with an independent process fault starting before, during, or after the command;
- faults whose measured effects overlap, lie outside, or mix across the authorization scope; classify these groups from simulator documentation/normal-only analysis before detector outcomes are opened;
- an unauthorized or out-of-envelope change with no valid token;
- malformed-context stress: delayed, expired, replayed, wrong-asset, magnitude-mismatched, missing, and partially corrupted records, plus a validly signed but deliberately incorrect scope. Treat the last case as an issuer/trust failure: provenance checks cannot establish that a correctly signed scope is semantically right;
- an identical-observation semantic control: pair the same sensor trace with different authorization records and show that a sensor-only method cannot distinguish authorization status. This matches M0's explicit identical-observation/opposite-semantic-label control and demonstrates only that the side-channel adds semantic information; it does not establish that a coincident fault is detectable when it is indistinguishable from an allowed response under the same record.

Include the published TEP 4-to-2 transition and its transition-fault cases if the simulator/version supports a faithful reproduction. Add at least one different transition path and independent injected process faults only after they are specified from the simulator/control procedure. HAZOP-style operation mistakes and independent equipment/process faults should be separately labeled: they are different causal questions.

### 2. Split and comparison arms

Split entire simulation runs and random seeds. Keep transition paths and selected fault classes out of threshold selection; use held-out paths/fault classes as stress tests where support permits. Never split overlapping windows from a run across training and test. Fit normal response envelopes only on fault-free simulations and freeze all context mappings before opening held-out fault outcomes.

Compare at matched benign-transition false-alarm operating points. The key context-conditioned comparator receives the **same authenticated command, timestamps, validity checks, normal training data, and predictive model** as the proposed method; vary only whether an explicit effect-scope restriction is enforced. Add an authentication ablation that disables record-validity checks while holding the rest fixed, so provenance checking and scope restriction are not conflated.

- sensor-only global detector;
- command/mode-conditioned detector or per-mode limits;
- published trajectory-based transition monitoring (slow feature analysis) and stage-based sub-PCA comparator where reproducible;
- blanket authorization/grace-period suppression, as an intentionally unsafe negative baseline;
- context-conditioned predictive residual monitoring without a bounded effect scope, but with the same command information and predictor as the scoped arm;
- proposed authorization-scoped residual monitor, with in-scope residual checks and ordinary out-of-scope monitoring;
- an oracle authorization/scope condition only as a labeled upper bound, never as a deployable method.

Keep the first proposal deterministic and rule-based. A learned promotion gate would introduce a separate adaptation policy, require its own source-only development split, and is unnecessary to test the stated semantic-scope hypothesis.

### 3. Outcomes and analysis

Keep distinct outcomes for (a) false alarms per benign-transition episode, (b) **would-promote contamination**: the fraction of fault-affected windows the frozen rule marks eligible for inclusion in the normal pool, and (c) episode-level missed detection by a fixed horizon. Detection delay is reported separately for detected episodes; episodes with no alarm by the horizon are right-censored there and counted as misses. Since no updates are applied, would-promote contamination is not evidence of actual model contamination. Report each outcome separately for preclassified in-scope, out-of-scope, and mixed fault effects and for each context-integrity failure. Also report transition-settling time, missed-operation/fault counts, normal-period false alarms, and alarms per operating hour.

Predeclare paired comparisons: scoped monitoring should reduce benign transition alarms versus sensor-only monitoring while meeting a chosen noninferiority margin on coincident-fault detection; and it should reduce would-promote contamination versus blanket suppression while matching benign-transition performance. The decisive novelty contrast is against the equal-information context-conditioned comparator: both receive the same authorization and predictor, with only scope enforcement differing. Select thresholds and operating points on benign validation runs, freeze them, and report held-out test frontiers descriptively; never tune a test threshold from fault outcomes. Pair fault-only and coincident-fault runs by fault, seed, and severity, and treat each shared-seed scenario block as the paired inference unit; events and windows remain nested within its simulation runs. A later sealed protocol must set numerical margins, the detection horizon and censoring rule, run count/power, and minimum support per comparison before any simulator test outcomes are generated or opened.

### 4. Feasibility gates and kill criteria

Proceed to a sealed protocol draft only if source-code/documentation inspection (without running the simulator) confirms reproducible command records and fault injection at controlled offsets during the same transition; the effect scopes can be justified without looking at test fault labels; and the closest transition-monitoring baseline can be run or fairly reconstructed. This gate authorizes only protocol drafting: any simulator execution still needs separate approval and a sealed scenario manifest.

Stop, narrow, or reframe if:

- a context-conditioned residual or published trajectory monitor is shown, with adequate support, to be equivalent to the scoped method within a predeclared practical margin at the same false-alarm rate and coincident-fault detection performance, or the scoped method fails to establish a useful gain; wide intervals are inconclusive, not equivalence;
- the claimed scope is selected using known fault labels, or authorization records reveal the injected fault class;
- the simulator cannot represent simultaneous transitions and faults with auditable timing;
- normal-transition false alarms improve only by allowing a material rise in would-promote contamination, missed detections, or detection delay;
- no plant partner can provide trusted command/work-order provenance, in which case claims remain about simulator-generated authorization events rather than real operations;
- context-integrity failures cause the monitor to suppress alarms instead of failing closed.

## Current recommendation

P3 is technically straightforward to prototype as a controlled simulation, but its publication novelty is at serious risk: transition monitoring with HAZOP-generated operational faults on the TEP already exists, alongside broader contextual and knowledge-based anomaly detection and recent work distinguishing mode drift from process faults. The remaining novelty is provisional until the full-text search is complete. The strongest defensible next step is a benchmark study of whether an independent, scope-limited authorization changes the would-promote/missed-detection tradeoff over equal-information context and transition-monitoring baselines. This first study audits eligibility decisions rather than updating a model, so it cannot establish adaptation safety. Do not frame the contribution as “context-aware detection,” and do not present a simulator-generated token as evidence of plant authorization. A real deployment claim needs command/work-order provenance from an operator or industrial partner.

No implementation or experiment is authorized by this proposal. M0 remains unchanged; its current authorization does not permit a P3 simulator run, adaptation gate, or model promotion. Any future execution requires a separate approved protocol and sealed scenario/data manifest.

## Sources checked for this pass

- [GitHub issue #7: P3 proposal](https://github.com/kuo1234/xlstm_anomaly/issues/7)
- Wang, Zheng & Wong 2020, [Trajectory-based operation monitoring of transition procedure in multimode process](https://doi.org/10.1016/j.jprocont.2020.09.008)
- IFAC DYCOPS 2019, [Statistical Monitoring of Processes with Multiple Operating Modes](https://doi.org/10.1016/j.ifacol.2019.06.134)
- Steenwinckel et al. 2021, [FLAGS: Fusing expert knowledge with machine learning](https://doi.org/10.1016/j.future.2020.10.015)
- Hayes & Capretz 2015, [Contextual anomaly detection framework for big sensor data](https://doi.org/10.1186/s40537-014-0011-y)
- Anzai & Pinto 2026, [Distinguishing Process Faults from Model Drift Through Variable Contribution Analysis](https://doi.org/10.3390/pr14050859)
- Wadinger & Kvasnica 2024, [Adaptable and Interpretable Framework for Anomaly Detection in SCADA-based industrial systems](https://doi.org/10.1016/j.eswa.2024.123200)
- Reinartz, Kulahci & Ravn 2021, [An extended Tennessee Eastman simulation dataset](https://doi.org/10.1016/j.compchemeng.2021.107281)
- Reinartz & Enevoldsen 2022, [pyTEP: A Python package for interactive simulations](https://doi.org/10.1016/j.softx.2022.101053)
- Vosloo, Uren & van Schoor 2025, [A complete and open Simulink model of the Tennessee Eastman process (COSTEP)](https://doi.org/10.1016/j.softx.2025.102217)
- Vosloo, Uren & van Schoor 2026, [A complete and open Simulink model of the Tennessee Eastman Process (COSTEP) for the purpose of control and process monitoring](https://doi.org/10.1016/j.dche.2026.100328); [repository](https://github.com/kennyuren/COSTEP)
- [Extended TEP dataset description](https://tulaut.github.io/ds_ExtendedTennesseeEastman)

## Astra review log

**Review 1: `REVISE` (gpt-6-astra).** The reviewer required a separate accounting of would-promote eligibility versus missed alarms and delay; an equal-information contextual baseline that differs only in scope; explicit trust/identifiability limits for authorization records; paired fault-only/coincident scenarios and predeclared evaluation operating points; a provisional novelty claim; a documentation-only feasibility gate before separately authorized runs; and correct separation of the 2025 COSTEP simulator paper from its 2026 monitoring paper. The changes above incorporate these findings.

**Review 2: `PASS` (gpt-6-astra), literature/design assessment only.** The reviewer found the outcomes, equal-information comparison, trust/identifiability limits, paired controls and inference, provisional novelty scope, COSTEP citations, and M0 boundary coherent. This PASS does not authorize simulator execution, a model-promotion gate, or adaptation experiments; those still require separate authorization and a sealed protocol.

**Authorization boundary:** current M0 does not authorize a P3 simulator, model-promotion, or adaptation-gate experiment. A future execution requires separate authorization, an approved protocol, and a sealed scenario/data manifest before simulator outcomes are inspected.
