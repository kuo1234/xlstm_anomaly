# Input-derived observable control (P1r) — protocol

Status: **sealed before any fit.** Exploratory. P1r is the **last bounded input-derived
control** of the synthetic observable-control ladder. Branch
`experiment/input-derived-observable-control`, based on consolidated `main@855c34d`.

## Question

Does `internal234` retain **additional predictive/decodable utility under the fixed decoder**
beyond a temporally matched, bounded **input-derived observable summary** (P1r)?

P1r is a bounded summary of the scaled raw input window, not the complete observation
information. `internal234` is a deterministic function of the causal input window, so
information-theoretic superiority over the full observation is out of scope in principle. This
protocol cannot establish information-theoretic, causal or backbone-superiority claims.

## Frozen P1r definition

Implementation: `scripts/input_derived_observable_control.py`. Every inherited operator is
imported unchanged. Nothing is re-implemented.

1. **Streams.** Regenerate the deterministic synthetic observation streams with
   `m0.synthetic.generate(source, scenario, condition)` (default `anomaly` semantic) for the A+
   grid: train `1000..1009`, validation `2000..2004` and test `3000..3009`; scenarios
   `abrupt, gradual, recurring, correlation`; conditions
   `none, spike, collective, dependency, mixture`. That is 500 streams. Observations are cast
   to a `float32` copy exactly as the cache extractor did.
2. **Scaler.** Use the existing source-specific input scaler
   `strong_observable_control._scaler(source)`: per-channel mean and population std of the first
   4,096 observations of `generate(source, "stationary", "none")`, with zero std replaced by 1.
   Scaled input is `scale_input(observations, scaler)` (`float32`).
3. **Windows.** Use the exact `[64, 8]` right-edge windows from `dense_windows`, with decision
   timestamps `t = 63 … N−1` and stride 1.
4. **P1 base.** Apply the frozen 128-column O1 statistic family
   (`strong_observable_control.residual_o1`, the same function used on residuals) to each
   scaled input window:
   - per channel: mean, std, rms, mean-abs, final, abs-final, slope and lag-1
     autocorrelation (8 × 8 = 64);
   - the covariance upper triangle including the diagonal (36);
   - the correlation strict upper triangle (28).
5. **P1r.** Apply `temporally_matched_observable_control.expand_o1r` to the P1 base. This is
   the identical causal current + mean/std/slope expansion at decision widths 4/8/16/32,
   feature-major, giving **128 × 13 = 1,664 columns**. The raw union is `[t−94, t]`, and the
   first fully finite decision is `t = 94` (decision index 31).
6. **Independence.** P1r depends only on observations and the source scaler. It is computed
   once per stream and is identical across backbones and detector seeds for the same
   source/timestamp. It uses no labels, events, regimes, semantics or future samples.

## Rows

The rows are exactly the A+ cohort: same folds, sources, scenarios, conditions, right-edge
rows, warmup (decision index ≥ 31) and primary anomaly-versus-legitimate-drift stratum.
`H` (14) and `internal234` (234) are read from the read-only A+ cache through the A+ record
builder. The ordered row-key SHA256 must equal the A+ `row_meta`:

| fold | rows | key SHA256 |
|---|---:|---|
| train | 697,430 | `71191e06ef47a9843ae1cc1e141d01fbbb541238514bce7b9d5e0a0683415fdd` |
| validation | 348,715 | `77ab6914c34b16262fe9afc80780a8fec079325ca88083b0bbd52751027f697c` |
| test | 697,430 | `fb90782494e416d25563f666a4b79a2a24a1968f90821bb36c57287228b4ac6d` |

Backbones are xLSTM and matched LSTM, with detector seeds `11, 22, 33`: six runs.

## Arms

| arm | columns | dimension |
|---|---|---:|
| `H+P1r` | `H`, `P1r` | 1,678 |
| `H+P1r+internal234` | `H`, `P1r`, `internal234` | 1,912 |

No scaler is fitted.

## Decoder and selection

The decoder is exactly the frozen HGB family from the nonlinear audit, imported from
`scripts/nonlinear_observable_control.py`:

```python
HistGradientBoostingClassifier(
    loss="log_loss", learning_rate=0.1, max_leaf_nodes=31, max_depth=6,
    min_samples_leaf=100, l2_regularization=1.0, max_bins=255,
    categorical_features=None, early_stopping=False, random_state=901,
    class_weight=None, max_iter=max_iter,
)
```

- The only candidates are `max_iter ∈ {100, 300}`. Each is fitted on train only and scored on
  pooled validation AP. The higher validation AP is selected, and an exact tie selects 100.
- Test predictions are generated once, after selection.
- There is no internal validation split, no early stopping, no new decoder and no new
  hyperparameter.

## Primary estimand and uncertainty

For each backbone, source and seed:

```text
AP(H+P1r+internal234) − AP(H+P1r)
```

- Report the 10 × 3 source × seed matrix and its source-level mean (the primary summary).
- Report the crossed bootstrap (source rows and seed columns resampled independently once per
  replicate, 10,000 draws, seed 901) and the source-only bootstrap (conditional on the three
  seeds). Three seed levels are too few for calibrated population intervals, and both
  intervals are exploratory.
- Pooled per-seed AP, scenario strata, the `+0.02` reference and any comparison with the
  committed nonlinear `H+O1r` APs are descriptive only.

## Label-blind preflight (fail closed)

There are two stages. `fit-one` refuses to run unless both are `PASS` under this protocol seal
and the sealed files are byte-identical to those recorded.

**Stage 1 — repository preflight** (`preflight`; no cache, no fit, no metric):

| gate | requirement |
|---|---|
| G1 | sealed code hashes recorded; generator code equals `reports/generator_validation_v4` |
| G2 | regenerated observations of all 500 streams and 25 scaler streams equal the sealed cache-host generator hashes |
| G3 | scaled input, P1 base and P1r are bit-identical across two independent computations; scalers deterministic |
| G4 | regenerated timestamps reproduce the A+ rows: per-fold row count, timestamp range and ordered row-key SHA256 equal A+ `row_meta` |
| G5 | the feature path takes only `(observations, scaler)`; no label, event, regime or semantic name occurs in it; the anomaly/legitimate semantic variants give identical observations |
| G6 | feature functions take no backbone, seed, cache or model argument |
| G7 | perturbing one input sample `s` changes exactly the decisions `t ∈ [s, s+94]`; no backward leakage; first fully finite decision `t = 94` |
| G8 | frozen dimensions 128 / 1,664 / 1,678 / 1,912 |
| G9 | candidates see train and validation only, test is predicted once after selection, and scikit-learn is not imported during the preflight |

The only truth-derived quantity in stage 1 is membership of the inherited A+ primary cohort,
used to reproduce row keys. No label value is joined to any feature, and no metric is computed.

**Stage 2 — cache-host preflight** (`host-preflight`, on the host holding the read-only A+
cache, before any fit):

- stage 1 is `PASS` under the same seal and the sealed code is unchanged;
- inputs are bit-identical to stage 1;
- P1r fingerprints match stage 1 (bit-identical, or sum/sum-of-squares within 1e-9 relative);
- all six cache manifests are complete;
- every cached timestamp array equals the regenerated one;
- no fit takes place.

At fit time, every stream's P1r must equal the stage-2 fingerprint bit-exactly, and the fitted
rows must reproduce the A+ row keys.

## Frozen outcome wording (predeclared)

Classification per backbone uses the crossed 95 % interval of the source-level mean.

| outcome | condition | admissible sentence |
|---|---|---|
| `ADDITIONAL_UTILITY_BEYOND_P1R` | lower > 0 | "Under the frozen HGB decoder, `internal234` retains additional predictive/decodable utility beyond the temporally matched input-derived observable summary P1r for ⟨backbone⟩: source-level ΔAP ⟨x⟩ [⟨lo⟩, ⟨hi⟩] (exploratory; three detector seeds; one synthetic generator)." |
| `NO_RESOLVED_ADDITIONAL_UTILITY` | interval contains 0 | "Under the frozen HGB decoder, no additional predictive/decodable utility of `internal234` beyond the input-derived observable summary P1r is resolved for ⟨backbone⟩: source-level ΔAP ⟨x⟩ [⟨lo⟩, ⟨hi⟩]." |
| `NEGATIVE_INCREMENT` | upper < 0 | "Under the frozen HGB decoder, adding `internal234` to `H+P1r` lowers AP for ⟨backbone⟩ (source-level ΔAP ⟨x⟩ [⟨lo⟩, ⟨hi⟩]); no additional predictive/decodable utility beyond P1r." |

Allowed conclusions are bounded to predictive/decodable utility beyond the frozen input-derived
P1r summary under the frozen decoder. The following are never admissible, whatever the result:

- that the observations are information-insufficient;
- that internal state contains information the observations lack;
- that P1r rules out every observable alternative;
- unqualified "beyond observables";
- xLSTM superiority or a backbone-specific mechanism;
- causal or safe-adaptation claims.

Any comparison between backbones is descriptive.

## Last control — nothing further is authorised from this branch

P1r is predeclared as the **last synthetic observable-control experiment**. Whatever the
result, none of the following is authorised from this branch:

- a decoder zoo;
- an HGB budget sweep;
- MLP/CNN decoders;
- W128/W256;
- persistent state;
- a new observable summary.

After P1r, the synthetic result is written up.

## Boundaries

- No detector inference, training or retraining.
- No write to the A+ cache.
- No change to `reports/`, M0/G1, the historical A+ / A+S / nonlinear result JSON, their
  protocols, run files, configs or checkpoints.
- H2/H3a/H3b are not reopened. No real-data experiment.
