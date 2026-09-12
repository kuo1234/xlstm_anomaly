# Revised M0 protocol v1 — pre-experiment freeze

2026-09-12. This document supersedes implementation suggestions in m0_review.md. No outcomes have been observed. Thresholds below are prospective engineering decisions, not literature-derived guarantees. Protocol changes require a versioned amendment before affected results are inspected; negative results never authorize changing thresholds or datasets.

## Execution and scope

Order: A protocol commit → dataset eligibility audit and sealed concrete manifest → B causal evaluator + D=8 generator → C unchanged official CANDI reproduction → D contamination causal curves → E one pinned xLSTMAD version plus parity → F matched LSTM → G H2/H3a probes → H delay only if H1-harm passes → I persistent-state diagnostic only if H3a passes.

This first commit freezes the selection algorithm, not a fictitious completed 12-file inventory. Phase A remains incomplete until raw data, source identities, checksums and eligibility are verified and the concrete manifest is committed. No training before that second seal. Download failures remain missing-data blockers, never performance-independent excuses to substitute files.

No rollback, stable/plastic dual memory, new xLSTM cell, learned adaptation gate, paper architecture, or delay+revalidation is authorized in revised M0. Logistic probes are offline diagnostics and never control adaptation.

## Dataset manifest contract

SMD: exactly machine-1-8 and machine-2-1, original train/test separation; record both upstream raw hashes and official CANDI preprocessed hashes. Reproduction keeps official preprocessing unchanged. Audit normalizers independently before using a common causal track.

TSB-drift metadata: StrAD commit `7078876bbd9398481a65c22b7689702ce9e0d558`, path `results/benchmark_eval_results/CD.csv`. Use only CD=1; tokenize type on whitespace. Buckets in order: continuous, change_point, periodic, random_walk. Preserve all original tags. Exclude synthetic examples. Do not inspect model-result CSVs.

Eligibility: original multivariate D≥2, numeric finite observations and binary anomaly labels, documented source trace identity and train cutoff, at least 320 initial-prefix observations and 256 test observations. Require the entire original training prefix to be normal, as verified by the evaluator, without moving its boundary or mining normal points from test. Split that prefix chronologically at floor(0.8*n_train), giving ≥256 fit and ≥64 calibration observations. Do not require a test anomaly or a measured performance level to qualify. Constant channels remain recorded; do not remove them based on test behavior.

Group exact duplicate raw feature traces and documented same-origin/cropped traces before selection; a group can supply at most one of the 12 slots. Exclude groups overlapping the two fixed SMD machines. Unknown provenance must be resolved, not presumed independent. Within each bucket order eligible filenames lexicographically. Choose the lexicographically smallest concatenation of four internally sorted three-file lists that satisfies all 12 distinct-source constraints (global feasible assignment, not greedy selection). Multi-tag series occupy one selection bucket but retain all tags for descriptive reporting.

If fewer than three eligible sources in any bucket, or no feasible 12-source assignment, STOP phase A and report exact exclusions. Do not replace with univariate, synthetic, contaminated-prefix series or altered buckets. Manifest fields: selection bucket, original tags, source group, URL, upstream commit, raw SHA256, metadata SHA256, D, N, cutoff, fit/calibration intervals, exclusion/qualification reason. Record the full sorted candidate inventory and exclusions so selection is reproducible.

Real datasets support anomaly detection/admission analysis. No real-data drift-vs-anomaly probe labels or exact post-shift latency are invented. These metrics are N/A unless independent annotations already exist and are frozen before model results. Synthetic-family transfer is not described as real-world cross-dataset validation.

## Synthetic and causal evaluation contract

D=8; five scenarios: stationary+anomaly, abrupt mean/scale, gradual, A→B→A, correlation shift. Use non-diagonal stable VAR(1) with correlated innovations; spectral radius 0.8, diagonal variances normalized. Correlation-shift variant changes innovation correlation with constant marginal variance; verify resulting process marginal moments, disclose residual differences. Fit/calibration/test lengths 4096/1024/16384, burn-in 1024 excluded. Five detector seeds 11,22,33,44,55. Generator families use disjoint matrix/innovation seeds: 1000–1009 probe train, 2000–2004 probe validation, 3000–3009 test; each seed generates all five scenarios. Same source seed and its counterfactual variants never cross folds.

Each scenario includes spike, collective, dependency anomalies, plus fixed equal-type mixture as a separately reported condition. Severity levels 1,2,3 in initial-normal standard deviation units; anomaly event durations 1 for spikes and 16,64,256 for collective/dependency. Include short legitimate excursions with the latter durations and matching mean/correlation perturbations, plus persistent faults. Onset schedules, balanced class counts, channels, overlap, and generation equations must be committed in generator configuration before training; never tune them on detector outcomes. Include stationary-no-anomaly and identical-observation/opposite-semantic-label controls. The latter has exactly paired identical features and is expected to be non-identifiable.

Metadata stores regime, drift-active interval, anomaly interval/type, event IDs and overlap separately. Probe drift class comprises anomaly-free windows within the first 256 samples of a regime change or active gradual transition; anomaly class comprises windows containing anomaly. Mixed drift/anomaly windows are a separate stress stratum, not double-labeled binary training data. Stable new-normal and stationary-normal specificity are reported separately. Evaluate duration/severity-matched subsets and natural-prevalence results separately.

Common causal track: window 64, stride 1, decision timestamp at right edge. Scalar window reconstruction score is evaluated against window-any-anomaly label; endpoint point scores and point labels are separate metrics, never mixed. No retrospective score filling. Score current input using pre-update state, emit immutable output, then select/update; any normalizer update occurs after the score. Initial fit data sets scaler; calibration fixes 95th-percentile threshold and references (no test-best threshold). Official reproduction may have different native semantics, retained and labeled.

Adaptation API contains x/time/algorithm state only. Labels/event boundaries are evaluator-only. Audit must establish label permutation cannot change scores, selections or updates. Exclude prefix/warmup/padding from test metrics. All model/optimizer/RNG state resets at independent run boundaries.

Metrics: primary average precision (AP); also trapezoidal PR-AUC explicitly named for CANDI reproduction, AUROC, unadjusted recall/FPR, optional VUS-PR with fixed implementation and buffer range 0–64. No point adjustment. Report per-series macro summaries and anomaly prevalence. Undefined metrics stay N/A with denominators.

Post-shift horizon: 256 samples from transition start, clean normal endpoints only. Sustained recovery: first of three consecutive non-overlapping 64-sample blocks with normal-point FPR≤0.10; require ≥32 clean endpoints per block, otherwise censored. Log candidate-to-commit, shift-to-first-update, shift-to-recovery and alarm latency separately; unavailable real boundaries are N/A.

## Reproduction, audit, and new experiments

Reproduction: CANDI commit `28c9679e503832f59e351208cde63657fcb51cad`, original scripts for both SMD machines at alpha 0.5/1/5; retain all upstream defaults, seeds, FPM, SANA, batching and counters. Save commands, resolved configs, environment/hardware, patches (empty algorithm diff), logs and checkpoint hashes. Report published versus observed AUROC/PR-AUC; >0.02 absolute discrepancy is a reproduction investigation trigger, not permission to tune test results. Additional five-seed replication is separately labeled. Official code remains immutable.

Audit: independent timestamps/IDs, label isolation, actual committed exposures, short-batch counter checks, moderate-mask behavior and normalization review. Any code fix, CPU/device compatibility patch or causal alignment adjustment lives in a distinct version/overlay; report score/selection differences. Candidate, committed, pending and rejected counts use separate denominators; report unique windows, raw point coverage and repeated loss exposure. Zero updates never count as 0% contamination success.

xLSTMAD starting version: `v1-submission-version` commit `3a1b0b5aab747bf6381fa4e5a90d895f06ed2fc6`; use reconstruction-MSE variant with original window resets. Native reproduction configuration and the common W=64 configuration are separate. Freeze dependency SHAs and resolved architecture before training. If the pinned version cannot support the required sLSTM/mLSTM observations, report E blocked; do not silently select another version based on probe performance. Compatibility fixes preserve architecture, objective, reset behavior and outputs and are labeled audited variants.

Instrumentation parity: float32, atol=1e-5 and rtol=1e-4 for output/hidden reference comparison; on/off observer outputs must be identical on deterministic same-backend runs. Verify finite states, prefix causality, independent window reset, batch permutation and parallel/recurrent agreement. Failure stops E until understood without changing the cell. Do not interpret parallel combination matrices as recurrent memory.

LSTM matches fit data/objective/window/readout, training steps and validation selection; choose nearest feasible width to ±10% trainable parameters before results, report unavoidable structural differences. Use equal detector seed and tuning budgets. Freeze a finite resolved training config before fitting; no test-informed architecture search. M2N2 is optional: at most one engineering day for original compatibility; CANDI's M2N2 adapter is labeled as that comparison version.

New experiments: synthetic generator, controlled-buffer interventions, H2/H3a probes, conditional FIFO delay and conditional H3b. None is called an official reproduction.

## H1 causal contamination intervention and delay

For each anomaly type and equal mixture, c={0,5,10,20,30}% refers to anomaly-window proportion in a 100-window update buffer. Pair runs on identical initial checkpoint, RNG, normal counterpart windows and subsequent evaluation stream. Replace exactly 0/5/10/20/30 buffer entries with matched corrupted counterparts; one fixed optimizer step per buffer, same number of buffers and example exposures. This oracle intervention diagnoses causal harm, not deployable candidate selection. Evaluate after the intervention, before further updates on the held-out evaluation segment; report no-update and all-clean controls. Match normal regime/age and anomaly duration/severity, preserve counterfactual source grouping.

Only H1-harm GO unlocks H. Keep K={0,4,8,16,32}; K counts decision windows, not selected candidates. K=0 is no extra delay on top of official MIN_SAMPLES=16 hard/moderate queues. An arrival at t matures at t+K; score first, then append matured candidates in original selection order to original queues and preserve hard-before-moderate update order. Do not revalidate or reject. Track age plus original batch latency, and do not flush tail using future data. Mature-cohort comparison uses candidates arriving by T−32 for every K, alongside full online results and all pending counts.

Fixed-update-budget diagnostic replays the same prespecified candidate batches/step counts on a common future evaluation segment; changing timing does not authorize more training or different examples. Pure FIFO may change endogenous selection through model trajectory, but no claim of decontamination follows just from fewer tail commits.

## H2 / H3a probes and conditional H3b

Positive class anomaly; offline L2 logistic regression only. StandardScaler fitted on probe-train; C∈{0.01,0.1,1,10}, selected by validation AP, ties choose smaller C. Never choose layer, feature family or seed on test. Group by source realization/event; no random overlapping-window split. For any temporal split purge 64+32=96 observations on either side and keep complete events together.

Prespecified six groups: score/history control; hidden only; gate only; memory only; combined internal; history+combined. Control: current score, first difference, trailing mean/std/slope over 4,8,16,32 decisions (14 features). Hidden summaries: mean/std/RMS and delta RMS. Gate summaries: mean/std/q10/q90 of input and retention effective gates plus their mean changes; logits logged for audit only. Memory: mean/std/RMS and relative delta norm for normalized sLSTM c/n and mLSTM readout-related normalized state; n and stabilizer logged separately for numerical audit. Pool each statistic equally across heads/layers, with scalar/matrix memory families reported separately; no flattened state matrices. LSTM uses corresponding c/h/i/f statistics. Missing families are N/A, never learned replacements. Combined is all prespecified available summaries. Apply the same 4/8/16/32 trailing summaries to both architectures and controls; freeze exact column schema and normalization formula in E before extracting any labeled probe features.

H3a is strictly window-local xLSTMAD reset. External rolling summaries have equal history budgets in LSTM/control. H3b is gated on H3a GO and is synthetic only: same frozen xLSTM weights, same non-overlapping 64-sample chunks, same input/history budget, reset at every chunk versus causal carry of all recurrent/conv states. Carry only within a source stream; no optimizer updates. Fresh probe fits use the existing train/validation/test partition. Do not compare carry with overlapping-window replay (which double-consumes observations). Reuse parity tests; no architecture change. This is a diagnostic, not xLSTMAD reproduction or a production detector.

## Decision rules frozen before outcomes

All differences are paired, macro across test source realizations; 5 detector seeds. Use 10,000 hierarchical bootstrap draws (seed 901), resample source realizations first and detector seeds second, retaining whole events/windows. Report 95% CIs. For multiple tested alternatives use Holm-adjusted paired tests at familywise 0.05 in addition to practical margins: H1's 4 positive c × 4 anomaly conditions; H4's 4 nonzero K. H2/H3a combined comparisons are confirmatory; individual feature-family results are descriptive. Do not promote a winning ablation when the combined test fails.

| Hypothesis | GO threshold | Otherwise |
|---|---|---|
| H1-admission | Nonzero independently audited committed anomaly windows on either fixed SMD, reproducible across ≥4/5 seeds; report magnitude, not just existence | Unconfirmed; does not unlock H |
| H1-harm | At ≥1 prespecified c/type, AP(clean)−AP(contaminated)≥0.02, paired CI lower bound>0 and multiplicity test passes; direction positive in ≥4/5 seeds and ≥3/4 shifted synthetic scenarios | H remains locked; inconclusive and evidence against harm distinguished |
| H2 additional window-local signal | AP(history+combined)−AP(history)≥0.02, CI lower bound>0; ≥4/5 seeds and ≥3/4 shifted scenarios positive; passes duration/severity-matched analysis too | STOP internal-signal claim for M0 |
| H3a xLSTM-specific signal | H2 passes; AP(xLSTM combined)−AP(LSTM combined)≥0.02 with CI lower bound>0, and xLSTM incremental gain over its history control exceeds LSTM incremental gain with CI lower bound>0; both reproducibility conditions as H2 | STOP xLSTM-specific branch; H3b locked, even if H2 passes |
| H3b persistent history | Conditional only: carry−reset AP≥0.02, CI lower bound>0, ≥4/5 seeds and ≥3/4 shifted scenarios positive; duration-matched result also positive | STOP persistent-history claim |
| H4 delay frontier | At least one K at its declared latency budget reduces committed contamination ≥0.02 absolute (CI lower bound>0, corrected test passes), with AP noninferiority lower bound>−0.01 and post-shift FPR increase upper bound<0.01, on mature cohorts; same direction ≥4/5 seeds and fixed-budget diagnostic. No claim of strict domination over lower-latency K=0 | STOP delay branch; no rollback escalation |
| H5 further reversible-adaptation research | H1-harm AND H4 pass; bounded synthetic evidence supports only further investigation. xLSTM-specific continuation additionally requires H3a; persistent-state claims additionally require H3b | Safe-adaptation or xLSTM branch decisions may differ; no complex system implementation |

H4 is improvement in robustness at explicitly paid latency, not cost-free dominance. Plot the entire measured frontier, including negative results, false-negative/recall effects and latency censoring. A late-recovery cost cannot be hidden by a single AP number. Report all K even if one passes. Metrics absent on real data are N/A; without external event labels, H2/H3 results remain synthetic-only and real-world GO is withheld. If CIs are wide, operational STOP means insufficient evidence to expand, not proof of no effect.

## Compute estimate and first measurement gate

Observed local hardware on 2026-09-12: one NVIDIA GB10, driver 580.173.02; nvidia-smi reports CUDA 13.0 compatibility and no active GPU process. This is not proof that PyTorch/xLSTM CUDA kernels are installed or supported. No timing pilot has run.

Planning envelope, not measured throughput: dataset/evaluator audits 2–8 CPU hours; CANDI 2 machines × 5 seeds with shared checkpoints and three alpha settings 4–24 GPU hours; paired contamination curves 4–24 GPU hours; xLSTMAD/LSTM training and feature extraction 12–72 GPU hours; logistic/bootstrap 1–8 CPU hours; conditional delay 4–24 GPU hours; conditional H3b 2–12 GPU hours. Total roughly 20–120 GPU hours before conditional branches, 26–156 including both; 2–7 days elapsed with engineering/runtime compatibility uncertainty. Reference sLSTM fallback could exceed this range substantially.

After protocol and data-manifest commits, run only a short throughput/parity pilot (≤30 minutes per backbone, ≤2 GPU hours total). Estimate full cost from measured training batches/sec, test decisions/sec, gate-observation overhead and actual eligible sequence lengths. Record environment, memory and extrapolation before long jobs; if estimate exceeds 160 GPU hours or reference backend is >5× slower, report and revise the execution budget without changing scientific thresholds. Never assert these estimates are benchmarked performance.
