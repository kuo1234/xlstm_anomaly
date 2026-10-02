# P10 / T1 occupancy audit, deployment side (attack points 3, 4, 5 and reset-per-window)

Date: 2026-10-02. Scope: 39 works screened (CSV `p10_occupancy_deployment.csv`), 22 with extracted full text, 17 at abstract/snippet level. No experiments were run.
Depth caveat (provisional): full-text review was passage/keyword-targeted on the extracted PDFs (state/reset/streaming/contamination/poison/memory-update patterns plus method and limitation passages), not cover-to-cover, except Patched-DeltaNet, which was read in full in the earlier session. Absence claims below rest on this screen of ~39 works and on web/Semantic Scholar searches that were partly rate-limited (OpenAlex and Semantic Scholar bulk screening did not complete; arXiv listing API timed out). All absence verdicts are therefore provisional.

## 摘要（繁體中文）
1. 沒有找到任何 TSAD 論文把 SSM / Mamba / xLSTM / DeltaNet / Titans 偵測器的狀態跨視窗保留（persistent streaming），並量測遮蔽或適應效果。39 篇中，架構類論文（Mamba 系 8 篇、xLSTMAD、Patched-DeltaNet、Reverso、MOMEMTO、MEMTO、TimeRCD、THEMIS）全是視窗內推論，等同每窗重置。
2. 持久狀態只出現在三類：online 學習（HTM、Saurav 2018、OML-AD）、test-time 參數更新（M2N2、CANDI、COMET）、kNN 記憶庫（MemStream、TTAMB）。它們都把「異常污染記憶／模型」當作設計問題處理，沒有把它當成可量測的反事實效應。
3. 最強的反駁：T1 只是舊的 memory poisoning / adaptation-vs-absorption 取捨換成新層；delta rule 下遮蔽可由閉式預測；神經核等同學習度量的 kNN-append（TTAMB 已部署）。要反駁必須同時證明 WIM 偏離閉式預測、神經核寬度與配對容量的 kNN-append 不同，且 RQ0 顯示持久狀態有益。
4. RQ0 必須做：沒有任何 linear-RNN 偵測器證明過跨窗持久的好處（只有參數／kNN 型有 +2 pp 到大幅 F1 提升的證據）。

## 1. Verdict per attack point

| Attack point | Verdict | Closest papers | Reason |
|---|---|---|---|
| 5a. Linear-RNN/SSM/xLSTM/TTT/Titans/DeltaNet TSAD deployed with state carried across windows, reporting adaptation or masking | OPEN (provisional) | Adaptive State-Space Mamba 2503.22743 (snippet), Patched-DeltaNet 2605.27992, xLSTMAD 2506.22837, Titans 2501.00663 | Eight Mamba-family TSAD papers (abstract-level), xLSTMAD, Patched-DeltaNet and Reverso all process finite windows. Only 2503.22743 describes a per-sample hidden-state update in a streaming loop, on synthetic spikes, with no reset-vs-carry ablation visible. Titans carries memory across chunks but is evaluated only on forecasting. |
| 5b. TSFM in-context contamination (Chronos/TimesFM/Moirai/TimeRCD/Reverso-style) | OPEN for TSAD recurrence; PARTIAL for in-window absorption | TimeRCD 2509.21190, TSFM adversarial robustness 2505.19397, GLAFF NeurIPS 2024 | TimeRCD states that frequent outliers inside one window can be partly absorbed into the local reference pattern (limitation remark only). Adversarial work shows longer context increases susceptibility. Reverso's UCR protocol slides the forecaster so earlier anomalies sit in later contexts, with no analysis. No study injects A1 then A2 with delay. |
| 5c. TS-Memory, MOMEMTO, TTAMB streaming behaviour | PARTIAL (TTAMB), OPEN (others) | TTAMB/TimeRep 2509.12650, MOMEMTO 2509.18751, TS-Memory 2602.11550 | MOMEMTO keeps its memory fixed at inference. TS-Memory is a static distilled module, streaming updates are future work. TTAMB appends representations whose nearest-neighbour distance exceeds the 80th percentile of training distances, so likely anomalies are admitted by construction. Reported effect is +2.0 pp Top-1 on UCR (75.6 to 77.6, center-aligned), but UCR has one anomaly per series so recurrence masking cannot be observed. |
| 3. T1 reduces to neural twin-freak | PARTIAL threat, not refuted | TTAMB, DAMP (prior knowledge, not re-read), MemStream, Patched-DeltaNet | See section 3. A kNN-append memory with a novelty gate is already deployed in TSFM AD. T1 survives only if the neural masking kernel differs measurably from matched kNN-append. |
| 4. T1 reduces to existing memory poisoning | PARTIAL threat, concept OCCUPIED for kNN/AE memory | MemStream 2106.03837, Saurav 2018, COMET, M2N2, CANDI, event-scoped fine-tune (Neural Networks 2026) | Poisoning, gated writes and self-correction are established for kNN/AE memory and for weight updates. Not occupied: write-induced counterfactual masking (F-sub/F-skip/F-decay) with a delay curve on linear-RNN or matrix-memory state. |
| 6. Reset-per-window is the de-facto standard (RQ0 mandatory?) | YES, standard; RQ0 mandatory | all within-window rows in CSV (24 of 39) | Every window/SSM/xLSTM/TSFM detector in the screen performs window-independent inference. Persistent state exists only in online-learning, TTA and kNN-memory families. Nobody has shown a persistence benefit for linear-RNN detectors, and TTT-on-video shows carry-over beats reset only under temporal smoothness. |

## 2. What the screen says about state scope (CSV column `state_scope`)
- within-window: 24 works (all Mamba TSAD, xLSTMAD, Patched-DeltaNet, Reverso, MOMEMTO, MEMTO, TimeRCD, THEMIS, Hundman 2018, TSFM robustness).
- persistent-streaming: 14 works (HTM, Saurav 2018, OML-AD, AnDri, MemStream, M2N2, CANDI, COMET, TTAMB, Titans, Abbas, the event-scoped fine-tuning pipeline, ASSM, TTT-video).
- within-sequence: 1 (Titans Revisited, chunked forecasting).
Detail on the nearest cases:
- Patched-DeltaNet: L=100, P=10, state inside one window, SMD, PA-F1. Its stated mechanism (state is written exactly when the delta is non-zero, i.e. on anomalous drifts) is the premise T1 tests, but it never carries the state forward.
- Hundman et al. (NASA, KDD 2018): evaluation in 70-minute batches with a sequence length l_s per prediction; no hidden-state carry statement found.
- Saurav et al. 2018 (abstract only): online RNN whose update damps short outliers but adapts to sustained error. This is the absorption-vs-adaptation trade-off stated as a design goal.
- Neural Networks 2026 online fine-tuning for anomaly prediction (snippet): says online adaptation degrades performance after return to normal and restricts the fine-tuned model to a single anomaly event, which is an event-scoped reset analogous to F-skip.

## 3. Strongest reviewer counterargument, and the experiment that would refute it
**Counterargument (single strongest).** "Write-induced masking is the known memory-poisoning / adaptation-versus-absorption trade-off (MemStream 2022, Saurav 2018, HTM, event-scoped fine-tuning 2026), restated for modern layers. For delta-rule memories it is also predictable in closed form: after writing (k1, v1), the readout error for a recurrence with key overlap <k1,k2> shrinks in proportion to write strength and overlap, and decays with the forget gate (my reading of the update in Patched-DeltaNet Eqs. 1 to 3; not verified numerically). The resulting 'masking kernel' is then a similarity kernel, i.e. a learned-metric kNN-append, which TTAMB already deploys with a novelty gate. T1 therefore measures a known effect that the architecture formula already predicts, with a twin-freak interpretation."
**Experiment that refutes it (pre-registered, all four must hold).**
1. Prediction mismatch: compute the closed-form delta-rule prediction of s2 reduction from the model's actual (k, beta, decay) at A1 and A2, and show measured WIM_sub(Delta) departs from it beyond seed CIs in at least one architecture (deep memory with momentum, mLSTM normalizer, input normalization such as RevIN). If measured WIM equals the formula, T1 is a corollary and should STOP.
2. Kernel width: against a kNN-append memory with the same write gate (TTAMB-style novelty threshold) and matched capacity, show the neural WIM-versus-sim(A1,A2) curve differs (width or shape) with non-overlapping bootstrap CIs. If not wider or different, it is a neural twin-freak, STOP.
3. Gate sufficiency: show a MemStream-style write gate (F-skip) removes WIM only at a measurable cost on benign-drift utility (a Pareto frontier of masking versus drift adaptation). If the gate is free, the finding collapses to "known remedy works".
4. RQ0: persistent state beats per-window reset on benign drift by a pre-declared margin over a trivial adaptive baseline (EMA normalization / M2N2-type update). If it does not, the masking phenomenon is irrelevant in practice.

## 4. Implications for the P10 design
- RQ0 is mandatory (section 1, row 6). Include the window-only/reset arm and a one-liner baseline (cf. "When Foundation Models are One-Liners").
- Use TTAMB's novelty-gated append as the named kNN-append comparator for RQ2 prime, and MemStream's gate as the named remedy comparator for the F-skip branch.
- Cite as motivating, not as prior art for the estimand: Patched-DeltaNet, Titans, Reverso.
- Reduce claim risk: describe the contribution as a counterfactual measurement protocol (WIM_sub, delay in update steps and in units of half-life), not as discovery that memory absorbs anomalies.
- Not re-verified this session (carried from the earlier audit): DAMP KDD 2022, METER/DyMETER, Du et al. CCS 2019, TTAMB's relation to DAMP numbers (TTAMB reports 77.6 versus DAMP 63.2 on UCR in its Table 1, which supports kNN-append being strong).

## 5. Limitations and deviations
- OpenAlex key was granted but bulk screening was not completed. Semantic Scholar searches were rate-limited (most of the 20 planned queries returned empty results before the run was stopped) and the arXiv listing API timed out; coverage therefore relies on web searches plus targeted PDF retrieval. Screened n=39, below the 40-paper target of the combined final audit but above the ≥20 required for this track.
- Full text for arXiv:2503.22743 could not be fetched (404 on arxiv.org/pdf); its verdict uses a search snippet only.
- Seventeen rows are abstract/snippet-level (marked in `full_text_status`), including Saurav 2018, M2N2 (described via citing papers), and several Mamba TSAD papers; their `state_scope` and OPEN verdicts are inferred from abstract-level descriptions and should be treated as provisional.
- Downloaded PDFs (2509.18751, 2602.11550, 2509.12650, 2509.21190, 2506.22837, 2106.03837, 2604.01845, 2602.01635, 2501.00663, 2510.09551, 2312.02530, 2510.03911, 1607.02480, 1802.04431, 2409.09742, 2408.03747, 2506.15831, 2505.19397) are in `paper/ (local, git-excluded) ` named `arXiv_<id>_<short>.pdf`, not to be committed.
