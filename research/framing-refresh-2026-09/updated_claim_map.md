# Updated claim map (post-G1, 2026-09)

Supersedes `research/claim_map.md` tiers B and C for the purpose of *writing*. The pre-G1 file is
unchanged and remains the record of what was claimable before G1 adjudicated.

Evidence keys used below:

- **G1** — authoritative Phase G1 decision (`research/CURRENT_STATUS.md`, `main` `caa9b3c`):
  H2 GO, mean ΔAP `+0.14251889179304736`; H3a STOP; H3b LOCKED.
- **LD** — post-hoc standalone-LSTM diagnostic (`research/lstm_standalone_diagnostic/`, `caa9b3c`):
  `Delta_L_own` mean `+0.14296629419144774`, 50/50 source×seed units positive, 5/5 seeds, 10/10
  sources, bootstrap CI `[0.137904, 0.147702]` (10,000 draws, seed 901), sign-flip raw p
  `0.001953125`. Algebraically reconstructed as `h2 − h3a_b`; **post-hoc, not in the Holm family.**
- **SC** — strong observable control (`research/strong_observable_control/`,
  `experiment/strong-observable-control` `f9014a2`): seeds 11/22/33, both backbones; recomputed
  arm table in `evidence_red_team.md` §0.
- **MD** — dense stride-1 mLSTM attribution (`research/mlstm_dense_attribution/`, `caa9b3c`), seed
  11 only, classification `DENSE_MLSTM_SIGNAL_NOT_MATRIX_SPECIFIC`.

---

## Part 1 — The L1–L5 ladder, reassessed

`L1` is split because the post-G1 evidence separates three claims the original level merged.

| Level | Claim | Status | Exact evidence | What is missing |
|---|---|---|---|---|
| **L1a** | Frozen recurrent internal summaries add information about anomaly-vs-drift beyond a **score/history** control, same backbone. | **SUPPORTED** | G1: H2 GO, mean ΔAP `+0.142519`, all frozen gates (margin, CI, Holm, ≥4/5 seeds, ≥3/4 scenarios, duration and severity strata). Independently reproduced in SC's sanity arm: `I|H` = `+0.142270` (xLSTM) and `+0.141634` (LSTM) over three fresh pooled-seed evaluations. | Nothing for this exact statement. It is synthetic-bound (see L1d). |
| **L1b** | The same increment survives a strong **within-window observable residual** control. | **PARTIALLY SUPPORTED** (exploratory) | SC primary `I|H+O2`: `+0.071218` (xLSTM), `+0.053027` (LSTM); 30/30 source×seed units positive for each backbone; source-first bootstrap 95% intervals `[+0.056497, +0.084523]` and `[+0.046168, +0.058372]`. | Under the *stronger* O1 control the increment is `+0.039584` (xLSTM, 3/3 seeds above the `0.02` reference) and `+0.015271` (LSTM, **0/3** seeds). The defensible number is the minimum over controls, and for the LSTM it is below margin. |
| **L1c** | The increment survives an observable control **matched on temporal span** (and on observations, not only residuals). | **NOT TESTED** | — | `O1`/`O2` enter the probe raw while `I` carries a 13x causal rolling expansion at widths 4/8/16/32 (`scripts/strong_observable_control.py`, lines 295–303 vs 329–330). No arm contains the input window. See `evidence_red_team.md` §1. |
| **L1d** | The L1 measurement describes real systems. | **NOT TESTED** | — | One synthetic generator (D=8, W64, 10 test sources, 4 scenarios × 5 conditions). No public dataset with per-timestamp drift-vs-anomaly truth was found in either sweep. |
| **L2** | Internal state is usable for an online adaptation decision without evaluator labels. | **NOT TESTED** | — | Every probe is offline, label-supervised, fit on source-disjoint folds, with one test evaluation. No operating point, no cost asymmetry, no label-free rule, no downstream safety/utility metric. New external obstacle: `arXiv:2608.30502` (see `direct_prior_art.md`). |
| **L3** | The evidence is **xLSTM-specific**. | **UNSUPPORTED** | G1 H3a STOP. LD: matched LSTM `+0.142966` ≥ xLSTM `+0.142519`, 50/50 units positive. SC absolute ceilings favour LSTM: `H+O1+I` `0.946744` vs `0.937717`; `H+O2+I` `0.946596` vs `0.935319`. | A single unresolved datum points the other way: under O1, xLSTM clears the `0.02` reference 3/3 seeds and LSTM 0/3. Confounded by xLSTM's `0.033339` weaker `H+O1` baseline; not a pre-registered contrast. |
| **L3'** | An **mLSTM-layer** channel adds information beyond the validated sLSTM schema. | **PARTIALLY SUPPORTED** (one seed, exploratory) | MD: `M_full|H+S` = `+0.016657` dense stride-1; stride-32 reproduction gate passed (`M|H` `+0.150513` vs prior `+0.150454`). | No dimension-matched control (482 vs 248 columns; the study's own dimension-matched contrast `H+M_full − H+S` is `+0.002034`), no residual control, one seed, and the mLSTM state is replayed from zero state rather than read natively. |
| **L3''** | The mLSTM channel is **matrix-memory-`C`-specific**. | **UNSUPPORTED** | MD: `ΔC_history` = `−0.000592`; `ΔC_given_sLSTM` = `+0.006610`; `H+M_noC` = `0.936035` ≥ `H+M_full` = `0.935443`. | The repository's own classification already says this. Do not revive it. |
| **L4** | Selective/deferred adaptation on internal evidence improves contamination robustness or the safety/latency frontier. | **NOT TESTED** | Adjacent facts only: H1-admission GO (contamination is real, 1.58–4.06% committed); D-v2 single-step controlled contamination below the `0.02` margin at c ≤ 20%; H1 natural harm `NOT_RUN`; H4a/H4b LOCKED. | No adaptation mechanism has been implemented. There is no demonstrated harm to improve on, so there is no baseline for a safety claim. |
| **L5** | Safe continual normality adaptation works in deployment. | **NOT TESTED** | — | Everything. |

**Net movement since the pre-G1 map.** L1 got stronger and then split — L1a is now confirmatory
rather than "under test", and L1b is a genuine new exploratory result. L3 moved from "under test"
to UNSUPPORTED. L2/L4/L5 are unchanged at NOT TESTED, and L2's route is harder than it looked.

---

## Part 2 — OUTPUT 1: updated claim map

| claim | current evidence | strongest support | strongest threat | prior-art overlap | allowed wording | unsupported wording | next required test |
|---|---|---|---|---|---|---|---|
| **C1.** Internal recurrent summaries add AP for anomaly-vs-drift beyond score/history, same frozen backbone | SUPPORTED (confirmatory) | G1 H2 GO, ΔAP `+0.142519`, all frozen gates; SC sanity arms reproduce `+0.142270` / `+0.141634` | Score/history is a weak control; the effect is large on one synthetic family | Construct occupied (CANDI latent similarity; MD-RS reservoir states; iADCPS latent dynamics). Measurement not occupied | "Under a frozen detector and a pre-registered probe, internal-state summaries add ≈0.14 AP over a score/history control on the synthetic drift-vs-anomaly cohort." | "Internal state is informative about drift versus anomaly." (unqualified) | none — this claim is closed |
| **C2.** That increment survives a strong observable residual control | PARTIALLY SUPPORTED (exploratory) | SC `I|H+O2` `+0.071218` / `+0.053027`, 30/30 units positive each | Temporal-span mismatch (§1a red team); minimum-over-controls is `+0.039584` / `+0.015271`, the LSTM value below the `0.02` reference | Nothing measures this contrast; MD-RS is the nearest (state vs prediction error, but anomaly-vs-normal) | "After a 1,024-column within-window residual-trajectory control, a positive increment remains under the same L2 probe (exploratory)." | "Observable residuals are insufficient." / "matched controls" | **E1** — temporally matched observable control |
| **C3.** The increment reflects recurrent internal *dynamics* rather than temporal context or nonlinearity | NOT TESTED | — | Scenario strata concentrate the increment in gradual+recurring, exactly where only the internal arm has cross-window context | Gate/state-semantics readings are prohibited by the pre-G1 map (E3) and nothing has changed | nothing yet | "recurrent dynamics encode drift semantics"; "the memory carries the evidence" | **E1** then **E2** (bounded nonlinear probe on both arms) |
| **C4.** The effect is generic across recurrent architectures | SUPPORTED for the common scalar schema | LD `+0.142966` (50/50 units, 5/5 seeds, 10/10 sources); SC both backbones survive O2 | Two architectures is not "generic"; no GRU, no SSM, no transformer control | No prior art either way | "The common recurrent-state effect is not xLSTM-specific: a capacity-matched LSTM shows an equal or larger increment." | "All recurrent models contain this information." | optional: one third backbone (GRU) at the same protocol |
| **C5.** xLSTM's internal state is more useful than a matched LSTM's | UNSUPPORTED | — | H3a STOP; LD; SC absolute ceilings favour LSTM | xLSTM-TSAD literature is two papers, neither on internal state | "H3a is STOP; no xLSTM-specific advantage was established under the frozen common-capacity comparison." | any xLSTM-superiority claim, including "under stronger controls xLSTM retains more" | **E1** with both backbones and paired source-level contrasts |
| **C6.** xLSTM internal state is harder to replace by residual statistics than a matched LSTM's | NOT TESTED (hypothesis) | SC: `I|H+O1` clears `0.02` in 3/3 xLSTM seeds and 0/3 LSTM seeds | Fully confounded with the `0.033339` weaker xLSTM `H+O1` baseline; not pre-registered; 3 seeds | none | "An unresolved divergence under the O1 control is recorded as a hypothesis." | stating it as a result | **E1**, pre-registering the cross-architecture contrast |
| **C7.** An mLSTM-layer channel complements the sLSTM schema | PARTIALLY SUPPORTED (1 seed) | MD `M_full|H+S` `+0.016657`; stride-32 gate passed | No dimension control, no residual control, replayed state, one seed; the dimension-matched contrast is `+0.002034` | none retrieved | "An exploratory one-seed screen found a small positive mLSTM-layer increment after sLSTM." | "xLSTM's hybrid memory adds a complementary channel." | **E3** — three-seed dense replication *with* a random-feature dimension control and the O1 residual control |
| **C8.** Matrix memory `C` is the source of the mLSTM signal | UNSUPPORTED | — | `ΔC_history` `−0.000592`; `H+M_noC` ≥ `H+M_full` | none | "The screen does not isolate matrix memory C; `M_noC` already preserves the gain." | any matrix-memory mechanism claim | none — closed unless E3 changes it |
| **C9.** Internal-state evidence can drive an online adapt/defer/reject decision | NOT TESTED | — | No label-free rule, no operating point, no cost model; `arXiv:2608.30502` documents the borrowed statistics failing on real streams (135/135 clean-stream fires) | Occupied as a construct by METER, HTM+SPRT, martingale gating, SCALE, the safety-gated CPS framework | nothing | anything in the "usable online" family | **E4** (not scheduled) — label-free rule + calibration set + cost asymmetry + paired comparison against always-adapt and never-adapt |
| **C10.** Deferred/gated adaptation reduces contamination harm | NOT TESTED | — | No demonstrated harm to improve on (H1 natural `NOT_RUN`; D-v2 single step below margin) | Occupied: ADA-ADF, AnDri, safety-gated CPS, METER, Quilt | "No contamination-harm result exists in this project." | "delay decontaminates"; "gating prevents absorption" | H1 natural harm first, then an intervention |
| **C11.** The project's framing ("learn the new normal without learning the anomaly") is new | UNSUPPORTED | — | SCALE, AnDri, ADA-ADF, the safety-gated CPS framework all occupy it | Direct | "The framing is established; the contribution is the measurement and the accounting." | any framing-level novelty claim | none — settled |
| **C12.** Reversing one normality commitment while preserving others is unoccupied | **WITHDRAWN** (was the pre-G1 map's cleanest gap) | — | AnDri's dynamic normal model activates, deactivates and adds normal patterns | Direct (`arXiv:2506.15831`) | "Reset semantics under normality change is occupied by pattern-level activation/deactivation; only its *accounting* is open." | "no prior work reverses a single normality commitment" | none — settled |

---

## Part 3 — Prohibited wording, refreshed

Carry forward E1–E9 from `research/claim_map.md` unchanged, and add:

| ID | Prohibited now | Why |
|---|---|---|
| **E10** | "Observable residuals are insufficient" / "matched observable controls" | The control arms carry no cross-window rolling expansion and no observations. Until E1 runs, "matched" is false. |
| **E11** | "Internal state adds beyond what is observable" | Only *residual* observables were controlled. The input window was never in any arm. |
| **E12** | "xLSTM retains more internal information under stronger controls" | The increment gap tracks a weaker xLSTM observable baseline; the absolute ceiling favours the LSTM. |
| **E13** | "The mLSTM layer contributes a complementary state channel" | One seed, no dimension control, no residual control, replayed state. |
| **E14** | "Our reset semantics / deactivation of a single learned normal is new" | AnDri. |
| **E15** | Any claim that borrows conformal/e-value gating as if its guarantee transfers to a deployed detector's score stream | `arXiv:2608.30502` measured the transfer and it failed. |
