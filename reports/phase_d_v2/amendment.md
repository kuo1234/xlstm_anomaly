# D-v2 implementation-only amendment

Authorized after review6f20427. Commit/push before corrected outcomes. Causal
execution state is model + optimizer + Python/NumPy/Torch CPU/CUDA RNG + backend
flags/version/device identity. Scientific design is exactly reports/phase_d/
prospective.md at9018e86: W10, seeds/sources/scenarios/types/c/buffers, MLP/SANA,
optimizer/evaluation suffix and bootstrap/sign-flip/Holm/GO thresholds unchanged.
No quarantined grid result may enter any computation, plot or decision.

Official utils.misc.set_seeds(11), verified in this environment before outcomes,
establishes cudnn.deterministic=True, cudnn.benchmark=False. Other accepted defaults:
deterministic_algorithms=False, float32_matmul_precision=highest,
cuda.matmul.allow_tf32=False, cudnn.allow_tf32=True. Torch2.13.0+cu130,
CUDA13.0, cuDNN92000, NVIDIA GB10 capability12.1. Record full seal including driver,
CUDA device UUID when exposed. Do NOT enable deterministic_algorithms=True.
At each process startup record incoming flags, restore only these accepted values,
then assert full seal before model execution. Assert unchanged before/after every
arm and canary; do not change flags inside a run. Every row links immutable seal
SHA256 plus fingerprint. Restore model/optimizer/RNG from the old sealed states.

Reuse five backbones and scaler/calibration/SANA/SGD/RNG after verifying against
pre-failure manifests. Recompute calibration scores/threshold on the same clean
train-source calibration observations as an integrity check, never selection.
No retraining. Verify all160 paired buffer manifests by deterministic regeneration
without inspecting quarantined result metrics. v1 reports/arrays remain immutable.

Before grid: (1) fresh real SMD1-8 alpha5 capture/replay with unchanged official
code and exact loss/order/steps/tensors/optimizer/RNG/subsequent-score parity;
(2) three fresh-process D8 repeats, source3000 abrupt spike seed11 c10;
(3) separate fresh-process evaluator-label permutation of the same arm, exact
algorithm parity; (4) three fresh-process no-update repeats from the same state.
All must PASS bitwise; any failure STOP. Gates are technical diagnostics, not grid
rows. Capture every trainable tensor hash, optimizer/RNG hash and full score array.
Commit/push backend seal, reuse verification and gate results before full grid.

Run all4800 new rows in reports/phase_d_v2 and data/phase_d_v2; no v1 row reuse,
including dry-run rows. Same inherited update and buffer/evaluator code, only
versioned output routing and backend restore/assertion added. Run fixed canary
(same c10 arm) before grid, after each source3000..3009, after grid. Compare exact
score/model/optimizer/loss/buffer fingerprints to Gate2. On failure STOP and mark
all rows since last successful canary invalid; no silent retries. A resumable run
must revalidate its preceding canary and may never import v1 results.

No-update controls, c0 and all c/type positive/null/negative results reported.
c30 remains stress-only. Original16 controlled+6 unavailable natural p=1 Holm
family unchanged. Timing from gates and inherited24h conservative compute gate
may halt expansion, never shrink design. No later phases authorized. Final
decision is H1-HARM GO/STOP/INCONCLUSIVE by the original frozen semantics.
