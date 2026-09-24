# Final assessment

**Prior-art novelty classification: PARTIALLY_OVERLAPPING**
**Architecture recommendation: DO_NOT_BUILD_YET**
**Research decision: ADAPTIVE_NORMALITY_RESEARCH_REFRAME**

The broad problem of adapting anomaly detection to a “new normal” is already explicit in M2N2. Selective TTA, normal-pattern memory, dynamic normal models, model pools and drift-aware updates each have substantial prior art. This audit did not find one paper that verifies every one of the proposed ten components as a single system. That bounded search result does not justify saying the full idea is novel: the combination would need to demonstrate a capability that its close predecessors do not.

The central blocker for Problem B is semantics. Without a mode/command/maintenance label or an accepted human decision, a stable predictable regime may be either benign operation or a persistent anomaly. Common benchmarks that label normal versus attack or report statistical distribution shifts do not automatically resolve that distinction. Problem A remains a separate, useful test: can source pretraining lower the amount of confirmed-normal data needed on a held-out, same-dimensional machine?

## Requested questions

1. **Has essentially the same problem already been solved?**
   The broad new-normal problem has been studied by M2N2. More directly, ACM E-Energy 2026 studies the core Problem B task—separating normal operation, normal drift and attacks, then selectively updating only on normal/drift samples—in a smart-building setting using 100 labeled anchors per class. Thus the central benign-drift-versus-attack question has already been demonstrated under limited class supervision in one application. The proposed normal-only target warm-start curve is different and remains empirically testable; its novelty is not established.

2. **Has essentially the same architecture already been published?**
   The search did not locate one public paper with every listed component—recurrent multi-horizon predictor, source normal pretraining, confirmed-normal target warm start, protected stream state, quarantine, explicit candidate-new-normal promotion and historical regime retention. The closest pieces are CANDI, MemTTA, AnDri, ARCUS, WWW 2026 DESS/DynaME and the E-Energy 2026 normal/drift/attack selective-update system. Exact full-system identity is **not established**, but most mechanisms and the core Problem B behavior are already represented; architecture-level novelty risk is high.

3. **Which pieces are known and which combination, if any, is still novel?**
   Known: xLSTM forecasting and TSAD; recurrent multi-step online forecasting; unsupervised new-normal TTA; curated/selective TTA; normal prototypes; pseudo-anomaly prototypes; online memory writes; change-point/drift detection; dynamic normal-pattern sets; historical detector/model pools; continual adaptation. Potentially distinct but unresolved: a rigorous same-D cross-machine study that quantifies target-normal sample savings for a reusable recurrent model, and a metadata-conditioned evaluation of regime promotion against persistent faults. A novel block combination is not enough.

4. **Is xLSTM scientifically necessary or merely replaceable?**
   It is currently replaceable. xLSTMAD establishes it as a detector candidate, not a uniquely suited solution. The repository’s matched-LSTM study reproduces the G1-scale internal signal. A+ is an exploratory exception worth preserving: with the temporally matched residual control, the linear-probe increment is +0.026710 for xLSTM and +0.010220 for LSTM; A+S found the qualitative result stable, while the nonlinear residual control attenuated both and P1r found no resolved increment beyond its bounded input-derived summary. R0 then found no resolved real-SMD increment for either backbone. Together this does not establish xLSTM-specific value for transfer, forecasting or online state. Any such claim must compare matched LSTM and preferably GRU/SSM or simple predictors.

5. **Which completed work in this repository remains useful?**
   Reuse the matched and auditable LSTM/xLSTM baselines, G1 and post-hoc controls as claim boundaries, P1r as negative evidence against an internal-state foundation, the R0 SMD data/provenance utilities, machine/channel/scaler audits, source-paired analysis and fail-closed execution infrastructure. The R0 result is an important negative within-machine measurement, not a persistent-state or transfer result.

6. **Which previous work should be abandoned?**
   Abandon the claim that xLSTM hidden/internal summaries are the distinctive foundation for this direction, and abandon any framing that persistence/predictability alone identifies benign new normality. Keep prior data, code and records. Do not erase or reinterpret G1/A+/A+S/P1r/R0 findings. The new question may use recurrent state operationally, but that is a different hypothesis.

7. **What is the smallest next experiment?**
   After a separately approved research execution, M1 should compare an LSTM and xLSTM source-native causal one-step detector against last-value, moving-statistic, linear/AR and current xLSTMAD reconstruction on a small, well-documented source set. It tests whether forecasting earns its complexity before any target adaptation. For the most direct deployment claim, M4 is the first decisive study: same-D SMD leave-one-machine-out with a few target-normal sample sizes and scratch/pretrained baselines. No experiment is started by this audit.

8. **What result would kill this research direction immediately?**
   For automatic Problem B promotion, inability to acquire trusted benign-mode and persistent-fault labels/context kills the safety/discrimination claim; observation-only promotion should stop. For the narrower transfer direction, if source pretraining does not reduce target-normal sample requirements over scratch/normalization and matched recurrent controls on held-out machines—or does so only by damaging anomaly detection—the xLSTM transfer hypothesis should stop. If cheap moving-statistic/change-point systems match the detector and update policy, drop the complex architecture.

9. **What result would justify proceeding to the next stage?**
   M1 proceeds only if a causal forecaster gives repeatable event-level utility beyond simple controls on multiple source units and its score timing is valid. M4 proceeds beyond baseline research only if pretrained models reach a predeclared near-reference target utility with materially fewer unique confirmed-normal observations than scratch and normalization/calibration, with no concentrated machine failures. M6 requires M5 contamination controls and semantically annotated data.

10. **Is the new-normal problem observable/identifiable with the proposed datasets?**
    Not in general and not from SMD/AnoShift shift labels alone. The E-Energy 2026 building data provide semantic normal/drift/attack examples but need limited labeled anchors; they do not show that an unlabeled normal-only initialization suffices. SWaT/WADI/HAI anomaly labels and richer NoBOOM/Batch Distillation/DAYPSCI annotations may support restricted context-aware studies after checking for explicit allowed-mode transitions and persistent-fault truth. Where benign and anomalous regimes are observationally equivalent, only external operational evidence, labels or an explicit risk policy can separate them.

## Recommendation

Start only with the narrower, falsifiable target-normal transfer question after prior-art review and dataset semantics review. Keep LSTM as an equal comparator. Do not implement persistent regime memory, candidate promotion or an “anomaly memory.” If Problem A fails its sample-efficiency gate, stop the xLSTM research direction. If it succeeds, evaluate online contamination and contextual regime adaptation as independent claims.

ADAPTIVE_NORMALITY_RESEARCH_REFRAME
