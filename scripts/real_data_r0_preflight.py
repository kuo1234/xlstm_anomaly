"""R0 result-blind preflight (data, model/observer, assembly).

``data``      numpy only.  Hashes, schema, boundaries, finiteness, split, scaler
              isolation, window/label alignment, Design-B blocks and the label
              counts needed to confirm AP is mathematically defined.
``model``     torch on GB10.  D=38 builders, parameter counts, observer on/off
              parity, reference-vs-fast parity, end-to-end causality and the
              permutation/sign audit of the common18 reductions.  Random-init
              models only; inputs are N(0,1) canaries and fit-interval (train)
              windows.  Never reads labels or test observations.
``assemble``  merges both reports into research/real_data_r0/preflight.json and
              writes research/real_data_r0/dataset_manifest.json.

No detector or probe metric is computed; sklearn is never imported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import real_data_r0_data as r0data  # noqa: E402

CONFIG = r0data.CONFIG
OUT_DIR = ROOT / "research" / "real_data_r0"
PHASE_A_SEAL = ROOT / "reports" / "phase_a" / "smd_seal.json"
POLARITY_COLUMNS = ("hidden_mean", "hidden_std", "memory_mean", "memory_std")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _no_metric_guard() -> dict[str, bool]:
    return {"sklearn_imported": "sklearn" in sys.modules}


METRIC_NAMES = ("average_precision_score", "roc_auc_score", "precision_recall_curve", "roc_curve", "auc",
                "f1_score", "precision_score", "recall_score", "accuracy_score", "confusion_matrix")
_METRIC_CALLS: list[str] = []


def install_metric_trap() -> None:
    """Replace sklearn metric functions before any model code is imported.

    The official xLSTMAD/lightning import chain imports sklearn transitively, so
    the model stage cannot assert that sklearn is absent; instead every metric
    entry point (including names later bound by ``from sklearn.metrics import``)
    raises and is recorded.
    """
    import sklearn.metrics as metrics

    for name in METRIC_NAMES:
        def trap(*args, _name=name, **kwargs):
            _METRIC_CALLS.append(_name)
            raise r0data.ProtocolViolation(f"metric {_name} called during preflight")

        setattr(metrics, name, trap)


# =========================================================================== data


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    padded = np.concatenate(([0], mask.astype(np.int8), [0]))
    diff = np.diff(padded)
    return list(zip(np.flatnonzero(diff == 1).tolist(), np.flatnonzero(diff == -1).tolist()))


def data_preflight() -> dict[str, Any]:
    seal = {row["machine"]: row for row in json.loads(PHASE_A_SEAL.read_text())}
    hashes = r0data.verify_all()
    machines: dict[str, Any] = {}
    for machine in r0data.MACHINES:
        exp = CONFIG["dataset"]["expected"][machine]
        train = r0data.load_observations(machine, "train")
        test = r0data.load_observations(machine, "test")
        labels = r0data.load_test_labels(machine, purpose="preflight_counts")
        n_train, n_test = len(train), len(test)
        end = r0data.fit_end(n_train)
        scaler = r0data.fit_scaler(train)
        # Normalisation isolation: replacing every non-fit value cannot move the scaler.
        noisy = train.copy()
        noisy[end:] = np.random.default_rng(0).normal(size=noisy[end:].shape) * 1e3
        scaler_noisy = r0data.fit_scaler(noisy)
        isolation = bool(np.array_equal(scaler["mean"], scaler_noisy["mean"]) and np.array_equal(scaler["scale"], scaler_noisy["scale"]))
        scaled = {"fit": r0data.apply_scaler(train[:end], scaler), "validation": r0data.apply_scaler(train[end:], scaler),
                  "test": r0data.apply_scaler(test, scaler)}
        fit_edges = r0data.fit_window_edges(n_train)
        val_edges = r0data.validation_window_edges(n_train)
        test_edges = r0data.test_window_edges(n_test)
        window_any = r0data.window_any_labels(labels, test_edges)
        brute = np.array([labels[t - 63 : t + 1].max() for t in test_edges], dtype=np.uint8)
        blocks = r0data.design_b_blocks(n_test)
        block_info = {}
        for name, (start, stop) in blocks.items():
            rows = np.arange(start, stop)
            y = window_any[rows - r0data.FIRST_DECISION]
            block_info[name] = {"interval": [int(start), int(stop)], "rows": int(len(rows)), "window_any_positives": int(y.sum()),
                                "window_any_negatives": int(len(y) - y.sum()), "ap_defined": bool(0 < y.sum() < len(y)),
                                "positive_runs_in_block": len(_runs(y.astype(bool)))}
        point_runs = _runs(labels.astype(bool))
        straddle = {}
        for left, right in (("train", "validation"), ("validation", "test")):
            gap = (blocks[left][1], blocks[right][0])
            straddle[f"{left}|{right}"] = {
                "embargo_rows": [int(gap[0]), int(gap[1])],
                "point_anomaly_run_spans_embargo": any(s < blocks[left][1] and e > blocks[right][0] - 63 for s, e in point_runs),
            }
        seal_row = seal.get(machine)
        seal_check = None
        if seal_row is not None:
            seal_check = {"train_N": seal_row["train_N"] == n_train, "test_N": seal_row["test_N"] == n_test,
                          "fit_interval": seal_row["audit_fit_interval"] == [0, end],
                          "calibration_interval": seal_row["audit_calibration_interval"] == [end, n_train],
                          "concatenated_test_interval": seal_row["concatenated_test_interval"] == [n_train, n_train + n_test]}
        machines[machine] = {
            "D": int(train.shape[1]), "train_N": n_train, "test_N": n_test, "label_N": int(len(labels)),
            "expected_train_N": exp["train_N"], "expected_test_N": exp["test_N"],
            "finite_train": bool(np.isfinite(train).all()), "finite_test": bool(np.isfinite(test).all()),
            "binary_labels": bool(np.isin(labels, (0, 1)).all()),
            "raw_value_range": {"train": [float(train.min()), float(train.max())], "test": [float(test.min()), float(test.max())]},
            "fit_end": end, "expected_fit_end": CONFIG["split"]["expected_fit_end"][machine],
            "phase_a_seal_agreement": seal_check,
            "scaler": {"fit_rows": scaler["fit_rows"], "zero_std_channels": scaler["zero_std_channels"],
                       "min_nonzero_std": float(scaler["scale"][scaler["scale"] != 1.0].min()) if np.any(scaler["scale"] != 1.0) else None,
                       "isolated_from_non_fit_rows": isolation,
                       "scaled_max_abs": {k: float(np.abs(v).max()) for k, v in scaled.items()},
                       "scaled_finite": all(bool(np.isfinite(v).all()) for v in scaled.values())},
            "windows": {
                "fit": {"count": int(len(fit_edges)), "first_edge": int(fit_edges[0]), "last_edge": int(fit_edges[-1]),
                        "max_observation_index": int(fit_edges[-1]), "inside_fit": bool(fit_edges[-1] < end)},
                "validation": {"count": int(len(val_edges)), "first_edge": int(val_edges[0]), "last_edge": int(val_edges[-1]),
                               "min_observation_index": int(val_edges[0] - 63), "inside_validation": bool(val_edges[0] - 63 >= end)},
                "test": {"count": int(len(test_edges)), "first_edge": int(test_edges[0]), "last_edge": int(test_edges[-1]),
                         "source": "original test file only"},
                "straddling_windows": 0,
            },
            "labels": {"point_positives": int(labels.sum()), "point_prevalence": float(labels.mean()),
                       "window_any_positives_t63plus": int(window_any.sum()), "window_any_prevalence_t63plus": float(window_any.mean()),
                       "window_any_matches_bruteforce": bool(np.array_equal(window_any, brute)),
                       "point_anomaly_runs": len(point_runs), "labels_before_t63_positive": int(labels[:63].sum())},
            "design_b": {"blocks": block_info, "embargo": r0data.EMBARGO, "receptive_field": r0data.RECEPTIVE_FIELD,
                         "boundary_event_check": straddle,
                         "all_blocks_ap_defined": all(v["ap_defined"] for v in block_info.values())},
        }
    checks = {
        "raw_hashes_all_match": hashes["all_match"],
        "D38_all": all(m["D"] == 38 for m in machines.values()),
        "lengths_match_expected": all(m["train_N"] == m["expected_train_N"] and m["test_N"] == m["expected_test_N"] for m in machines.values()),
        "label_test_alignment": all(m["label_N"] == m["test_N"] for m in machines.values()),
        "finite_observations": all(m["finite_train"] and m["finite_test"] for m in machines.values()),
        "binary_labels": all(m["binary_labels"] for m in machines.values()),
        "fit_end_matches_frozen": all(m["fit_end"] == m["expected_fit_end"] for m in machines.values()),
        "phase_a_seal_agreement": all(all(v.values()) for m in machines.values() if m["phase_a_seal_agreement"] for v in [m["phase_a_seal_agreement"]]),
        "scaler_fit_only": all(m["scaler"]["isolated_from_non_fit_rows"] for m in machines.values()),
        "scaled_finite": all(m["scaler"]["scaled_finite"] for m in machines.values()),
        "no_straddling_windows": all(m["windows"]["fit"]["inside_fit"] and m["windows"]["validation"]["inside_validation"] for m in machines.values()),
        "window_any_labels_correct": all(m["labels"]["window_any_matches_bruteforce"] for m in machines.values()),
        "design_b_ap_defined_every_block": all(m["design_b"]["all_blocks_ap_defined"] for m in machines.values()),
    }
    return {"stage": "data", "hashes": hashes, "machines": machines, "checks": checks,
            "label_access_log": [{k: v for k, v in row.items() if k != "utc"} for row in r0data.label_access_log()],
            "metric_guard": _no_metric_guard(), "pass": all(checks.values()) and not _no_metric_guard()["sklearn_imported"]}


# =========================================================================== model


def _cmp(a, b, exact: bool = False) -> dict[str, Any]:
    import torch

    close = bool(torch.equal(a, b)) if exact else bool(torch.allclose(a, b, atol=1e-5, rtol=1e-4))
    return {"pass": close, "bitwise": bool(torch.equal(a, b)), "max_abs": float((a - b).abs().max().item())}


def _lstm_permute(model, generator):
    """Exact hidden-unit permutation of every LSTM layer (function-preserving)."""
    import torch

    layers = [*model.encoder, *model.decoder]
    width = layers[0].hidden_size
    device = layers[0].weight_ih_l0.device
    perms = [torch.randperm(width, generator=generator).to(device) for _ in layers]
    with torch.no_grad():
        previous = None
        for layer, perm in zip(layers, perms):
            rows = torch.cat([perm + g * width for g in range(4)])
            layer.weight_ih_l0.copy_(layer.weight_ih_l0[rows] if previous is None else layer.weight_ih_l0[rows][:, previous])
            layer.weight_hh_l0.copy_(layer.weight_hh_l0[rows][:, perm])
            layer.bias_ih_l0.copy_(layer.bias_ih_l0[rows])
            layer.bias_hh_l0.copy_(layer.bias_hh_l0[rows])
            previous = perm
        model.output_projection.weight.copy_(model.output_projection.weight[:, previous])
    return [p.cpu().tolist() for p in perms]


def _lstm_sign_flip(model, generator):
    """Exact per-unit sign reparameterisation of the five LSTM layers not followed by GELU."""
    import torch

    layers = [*model.encoder, *model.decoder]
    width = layers[0].hidden_size
    flips = []
    reference = layers[0].weight_ih_l0
    with torch.no_grad():
        previous = torch.ones(width).to(reference)
        for index, layer in enumerate(layers):
            if index < len(layers) - 1:
                sign = torch.where(torch.rand(width, generator=generator) < 0.5, -1.0, 1.0).to(reference)
            else:
                sign = torch.ones(width).to(reference)  # last layer feeds GELU (not odd): no exact sign symmetry
            row = torch.ones(4 * width).to(reference)
            row[2 * width : 3 * width] = sign  # PyTorch gate order i, f, g, o
            layer.weight_ih_l0.mul_(row[:, None] * previous[None, :])
            layer.weight_hh_l0.mul_(row[:, None] * sign[None, :])
            layer.bias_ih_l0.mul_(row)
            layer.bias_hh_l0.mul_(row)
            previous = sign
            flips.append(int((sign < 0).sum()))
    return flips


def _trace_reduction_audit(traces: dict, summarize, unit_axis_heads: bool, generator) -> dict[str, Any]:
    """Permutation invariance and polarity sensitivity of the frozen reductions on real traces."""
    import torch

    base = summarize(traces)
    permuted, flipped = {}, {}
    for cell, layer in traces.items():
        sample = layer["hidden"]
        units = sample.shape[-1]
        perm = torch.randperm(units, generator=generator).to(sample.device)
        sign = torch.where(torch.rand(units, generator=generator) < 0.5, -1.0, 1.0).to(sample.device, sample.dtype)
        head_perm = torch.randperm(sample.shape[2], generator=generator).to(sample.device) if unit_axis_heads else None
        permuted[cell], flipped[cell] = {}, {}
        for key, value in layer.items():
            v = value.index_select(-1, perm)
            if head_perm is not None:
                v = v.index_select(2, head_perm)
            permuted[cell][key] = v
            flipped[cell][key] = value * sign if key in ("hidden", "memory") else value
    after_perm = summarize(permuted)
    after_flip = summarize(flipped)
    from phase_e2_schema import BASE_COLUMNS

    delta = (after_flip - base).abs().amax(0)
    return {
        "permutation_invariant": _cmp(base, after_perm),
        "polarity_changed_columns": [BASE_COLUMNS[i] for i in range(18) if float(delta[i]) > 1e-5],
        "polarity_invariant_columns_close": bool(all(float(delta[i]) <= 1e-5 for i in range(18) if BASE_COLUMNS[i] not in POLARITY_COLUMNS)),
    }


def model_preflight() -> dict[str, Any]:
    install_metric_trap()
    import torch

    import real_data_r0_models as models
    from phase_g1_core import expand_internal234, history14

    environment = models.configure()
    report: dict[str, Any] = {"stage": "model", "environment": environment}
    det = CONFIG["detector"]
    width_rule = models.select_lstm_width(det["xlstm"]["trainable_parameters"])
    report["capacity"] = {"lstm_width_rule": width_rule,
                          "config_width": det["lstm"]["width"], "config_lstm_parameters": det["lstm"]["trainable_parameters"],
                          "config_xlstm_parameters": det["xlstm"]["trainable_parameters"]}
    # ------------------------------------------------------------- inputs (no labels, no test observations)
    generator = torch.Generator(device="cpu").manual_seed(710)
    canary = torch.randn(128, 64, 38, generator=generator).cuda()
    fit_batches = {}
    for machine in r0data.MACHINES:
        train = r0data.load_observations(machine, "train")
        scaler = r0data.fit_scaler(train)
        end = r0data.fit_end(len(train))
        scaled_fit = r0data.apply_scaler(train[:end], scaler)
        edges = r0data.fit_window_edges(len(train))
        pick = np.concatenate((edges[:64], edges[-64:]))
        fit_batches[machine] = torch.from_numpy(r0data.window_matrix(scaled_fit, pick)).cuda()
        if machine == r0data.MACHINES[0]:
            stream = scaled_fit[:400].copy()
    inputs = {"canary_N01": canary, **{f"fit_windows_{m}": b for m, b in fit_batches.items()}}
    # ------------------------------------------------------------- builders and parameter counts
    per_seed = {}
    models_by_seed = {}
    for seed in det["seeds"]:
        vanilla = models.build_xlstm_vanilla(seed).eval()
        overlay = models.cuda_overlay_from_vanilla(vanilla)
        lstm = models.build_lstm(seed).eval()
        for model in (vanilla, lstm):
            for parameter in model.parameters():
                parameter.requires_grad_(False)
        per_seed[str(seed)] = {
            "xlstm_vanilla_parameters": sum(p.numel() for p in vanilla.parameters()),
            "xlstm_cuda_parameters": sum(p.numel() for p in overlay.parameters()),
            "lstm_parameters": sum(p.numel() for p in lstm.parameters()),
            "xlstm_init_hash": models.model_hash(vanilla), "lstm_init_hash": models.model_hash(lstm),
            "xlstm_d_dependent": {n: list(p.shape) for n, p in vanilla.named_parameters() if 38 in p.shape},
            "lstm_modules": [n for n, m in lstm.named_modules() if isinstance(m, torch.nn.LSTM)],
        }
        models_by_seed[seed] = (vanilla, overlay, lstm)
    report["parameters"] = per_seed
    # ------------------------------------------------------------- parity
    parity = {}
    for seed, (vanilla, overlay, lstm) in models_by_seed.items():
        for name, x in inputs.items():
            with torch.no_grad():
                plain_v = vanilla(x)
                plain_c = overlay(x)
                plain_l = lstm(x)
            out_v, score_v, base_v = models.extract_batch(vanilla, "xlstm_reference", x)
            out_c, score_c, base_c = models.extract_batch(overlay, "xlstm", x)
            out_l, score_l, base_l = models.extract_batch(lstm, "lstm", x)
            parity[f"{seed}/{name}"] = {
                "xlstm_reference_observer_on_off": _cmp(plain_v, out_v, exact=True),
                "xlstm_fast_observer_on_off": _cmp(plain_c, out_c, exact=True),
                "lstm_observer_on_off": _cmp(plain_l, out_l, exact=True),
                "xlstm_vanilla_vs_cuda_output": _cmp(out_v, out_c),
                "xlstm_reference_vs_fast_score": _cmp(score_v, score_c),
                "xlstm_reference_vs_fast_common18": _cmp(base_v, base_c),
                "shapes": {"xlstm": list(base_c.shape), "lstm": list(base_l.shape)},
                "finite": bool(torch.isfinite(base_c).all() and torch.isfinite(base_l).all() and torch.isfinite(base_v).all()),
            }
    report["parity"] = parity
    # ------------------------------------------------------------- end-to-end causality and warmup (seed 11)
    vanilla, overlay, lstm = models_by_seed[det["seeds"][0]]
    edges = np.arange(63, len(stream), dtype=np.int64)
    cut = 250
    perturbed = stream.copy()
    perturbed[cut:] += np.random.default_rng(1).normal(size=perturbed[cut:].shape).astype(np.float32) * 5.0
    causality = {}
    for arch, model in (("xlstm", overlay), ("lstm", lstm)):
        a = models.extract_windows(model, arch, r0data.window_matrix(stream, edges))
        b = models.extract_windows(model, arch, r0data.window_matrix(perturbed, edges))
        ha, hb = history14(a["score"]), history14(b["score"])
        ia, ib = expand_internal234(a["internal_base18"]), expand_internal234(b["internal_base18"])
        before = edges < cut
        finite_rows = np.isfinite(ha).all(1) & np.isfinite(ia).all(1)
        causality[arch] = {
            "H_dim": int(ha.shape[1]), "internal234_dim": int(ia.shape[1]),
            "past_rows_bitwise_equal": bool(np.array_equal(a["score"][before], b["score"][before])
                                            and np.array_equal(a["internal_base18"][before], b["internal_base18"][before])
                                            and np.array_equal(ha[before], hb[before], equal_nan=True)
                                            and np.array_equal(ia[before], ib[before], equal_nan=True)),
            "past_rows_max_abs": float(max(np.abs(a["score"][before] - b["score"][before]).max(),
                                           np.abs(a["internal_base18"][before] - b["internal_base18"][before]).max())),
            "future_rows_changed": bool(not np.array_equal(a["score"][~before], b["score"][~before])),
            "first_finite_edge": int(edges[np.flatnonzero(finite_rows)[0]]),
            "warmup_rows_nonfinite": int((~finite_rows).sum()),
            "all_rows_finite_after_warmup": bool(finite_rows[edges >= r0data.FIRST_FINITE].all()),
        }
    report["causality"] = causality
    # ------------------------------------------------------------- permutation / sign audit
    audit_gen = torch.Generator(device="cpu").manual_seed(4242)
    x = fit_batches[r0data.MACHINES[0]]
    lstm_ref = models.build_lstm(det["seeds"][0]).eval()
    out0, score0, base0 = models.extract_batch(lstm_ref, "lstm", x)
    permuted = models.build_lstm(det["seeds"][0]).eval()
    perms = _lstm_permute(permuted, audit_gen)
    out1, score1, base1 = models.extract_batch(permuted, "lstm", x)
    flipped = models.build_lstm(det["seeds"][0]).eval()
    flips = _lstm_sign_flip(flipped, audit_gen)
    out2, score2, base2 = models.extract_batch(flipped, "lstm", x)
    from phase_e2_schema import BASE_COLUMNS

    flip_delta = (base2 - base0).abs().amax(0)
    report["semantic_audit"] = {
        "lstm_full_network_unit_permutation": {"output": _cmp(out0, out1), "common18": _cmp(base0, base1),
                                               "permutation_is_nontrivial": any(p != list(range(len(p))) for p in perms)},
        "lstm_full_network_sign_reparameterisation": {
            "flipped_units_per_layer": flips, "output": _cmp(out0, out2), "score": _cmp(score0, score2),
            "changed_columns": [BASE_COLUMNS[i] for i in range(18) if float(flip_delta[i]) > 1e-5],
            "max_abs_change_per_column": {BASE_COLUMNS[i]: float(flip_delta[i]) for i in range(18)},
        },
    }
    from phase_e2_observer import Observer as XRef
    from phase_e2_schema import summarize as x_summarize
    from phase_f_lstm_observer import Observer as LRef, summarize as l_summarize

    with torch.no_grad(), XRef(vanilla) as observer:
        vanilla(x)
        xtraces = {k: {n: t.clone() for n, t in v.items()} for k, v in observer.latest.items()}
    with torch.backends.cudnn.flags(enabled=False), torch.no_grad(), LRef(lstm) as observer:
        lstm(x)
        ltraces = {k: {n: t.clone() for n, t in v.items()} for k, v in observer.latest.items()}
    report["semantic_audit"]["xlstm_reduction_on_traces"] = _trace_reduction_audit(xtraces, x_summarize, True, audit_gen)
    report["semantic_audit"]["lstm_reduction_on_traces"] = _trace_reduction_audit(ltraces, l_summarize, False, audit_gen)
    report["semantic_audit"]["trace_shapes"] = {"xlstm": {k: list(v["hidden"].shape) for k, v in xtraces.items()},
                                                "lstm": {k: list(v["hidden"].shape) for k, v in ltraces.items()}}
    report["signatures"] = models.observation_only_signatures()
    sa = report["semantic_audit"]
    checks = {
        "xlstm_parameters_75934": all(v["xlstm_vanilla_parameters"] == v["xlstm_cuda_parameters"] == 75934 for v in per_seed.values()),
        "lstm_parameters_74100": all(v["lstm_parameters"] == 74100 for v in per_seed.values()),
        "lstm_width_rule_reproduces_38": width_rule["width"] == det["lstm"]["width"] == 38,
        "lstm_within_10pct": abs(width_rule["relative_difference"]) <= 0.10,
        "observer_on_off_bitwise": all(p[k]["bitwise"] for p in parity.values() for k in ("xlstm_reference_observer_on_off", "xlstm_fast_observer_on_off", "lstm_observer_on_off")),
        "reference_vs_fast_parity": all(p[k]["pass"] for p in parity.values() for k in ("xlstm_vanilla_vs_cuda_output", "xlstm_reference_vs_fast_score", "xlstm_reference_vs_fast_common18")),
        "common18_shape_and_finite": all(p["finite"] and p["shapes"] == {"xlstm": [128, 18], "lstm": [128, 18]} for p in parity.values()),
        "H14_internal234_dims": all(v["H_dim"] == 14 and v["internal234_dim"] == 234 for v in causality.values()),
        "end_to_end_causal": all(v["past_rows_bitwise_equal"] and v["future_rows_changed"] for v in causality.values()),
        "warmup_first_finite_edge_94": all(v["first_finite_edge"] == 94 and v["all_rows_finite_after_warmup"] for v in causality.values()),
        "reductions_permutation_invariant": sa["xlstm_reduction_on_traces"]["permutation_invariant"]["pass"] and sa["lstm_reduction_on_traces"]["permutation_invariant"]["pass"],
        "lstm_network_permutation_invariant": sa["lstm_full_network_unit_permutation"]["output"]["pass"] and sa["lstm_full_network_unit_permutation"]["common18"]["pass"],
        "lstm_sign_reparameterisation_function_preserving": sa["lstm_full_network_sign_reparameterisation"]["output"]["pass"],
        "no_label_parameters": not any(set(v) & {"label", "labels", "y", "target", "targets"} for v in report["signatures"].values()),
    }
    report["checks"] = checks
    report["label_access_log"] = r0data.label_access_log()
    report["metric_guard"] = {"sklearn_imported_transitively_by_official_stack": "sklearn" in sys.modules,
                              "metric_trap_installed_before_model_imports": True, "metric_calls": list(_METRIC_CALLS)}
    report["pass"] = all(checks.values()) and not report["label_access_log"] and not _METRIC_CALLS
    return report


# =========================================================================== assembly


def dataset_manifest(data: dict[str, Any], acquisition: dict[str, Any] | None) -> dict[str, Any]:
    ds = CONFIG["dataset"]
    routes = {}
    if acquisition:
        for row in acquisition["files"]:
            routes[f"{row['machine']}/{row['split']}"] = {
                "install_route": row["install_route"], "status": row["status"],
                "public_pinned_download_match": row["public_download"].get("match"),
                "feasibility_worktree_copy_match": row.get("staged_feasibility_copy", {}).get("match"),
            }
    rows = []
    for machine in ds["machines"]:
        m = data["machines"][machine]
        exp = ds["expected"][machine]
        rows.append({
            "machine": machine,
            "source_group": f"SMD/{machine}",
            "upstream": {"repository": ds["upstream_repository"], "commit": ds["upstream_commit"],
                         "urls": {s: r0data.source_url(machine, s) for s in ds["splits"]}},
            "sha256": {s: exp[s]["sha256"] for s in ds["splits"]},
            "bytes": {s: exp[s]["bytes"] for s in ds["splits"]},
            "hash_authority": exp["hash_authority"],
            "D": m["D"], "train_N": m["train_N"], "test_N": m["test_N"], "label_N": m["label_N"],
            "anomaly_prevalence": {"point": m["labels"]["point_prevalence"], "point_positives": m["labels"]["point_positives"],
                                   "window_any_t63plus": m["labels"]["window_any_prevalence_t63plus"],
                                   "window_any_positives_t63plus": m["labels"]["window_any_positives_t63plus"]},
            "original_train_test_boundary": {"train": [0, m["train_N"]], "test": [0, m["test_N"]],
                                             "concatenated_coordinates": [m["train_N"], m["train_N"] + m["test_N"]]},
            "detector_fit_interval": [0, m["fit_end"]], "detector_validation_interval": [m["fit_end"], m["train_N"]],
            "zero_std_fit_channels": m["scaler"]["zero_std_channels"],
            "train_normality": ds["train_normality"],
            "provenance_evidence": {
                "phase_a_seal": "reports/phase_a/smd_seal.json" if machine in ("machine-1-8", "machine-2-1") else None,
                "feasibility_audit": "research/real-data-feasibility-audit@8f6ee870e1c8d0809d4d1352e8fde0fd450b56d5 datasets.json" if machine in ("machine-2-1", "machine-1-4") else None,
                "r0_acquisition": {s: routes.get(f"{machine}/{s}") for s in ds["splits"]},
            },
            "selection_rationale": {"machine-1-8": "historical strict Phase-A anchor",
                                    "machine-2-1": "historical strict anchor; provenance independently rechecked",
                                    "machine-1-4": "included in the real-data feasibility work and the prelisted M2N2-overlap analysis"}[machine],
        })
    return {"stage": "R0", "protocol_version": CONFIG["protocol_version"], "base_main": CONFIG["base_main"],
            "dataset": ds["name"], "machines": rows,
            "forbidden_inputs": ds["forbidden_inputs"],
            "labels_support": "anomaly-versus-nonanomaly evaluation only; no drift/new-normal/transition labels are derived",
            "raw_bytes_location": "git-ignored data/external_real/r0_smd/ under the GB10 primary checkout (see data_acquisition.md)"}


def assemble(data_path: Path, model_path: Path, acquisition_path: Path | None, tests_path: Path | None) -> dict[str, Any]:
    data = json.loads(data_path.read_text())
    model = json.loads(model_path.read_text())
    acquisition = json.loads(acquisition_path.read_text()) if acquisition_path else None
    tests = json.loads(tests_path.read_text()) if tests_path else None
    code = {str(p.relative_to(ROOT)): _sha(p) for p in sorted((ROOT / "scripts").glob("real_data_r0_*.py"))}
    code["research/real_data_r0/config.json"] = _sha(r0data.CONFIG_PATH)
    code["tests/test_real_data_r0.py"] = _sha(ROOT / "tests" / "test_real_data_r0.py")
    design = {
        "selected": CONFIG["probe"]["design"],
        "blocks_frozen_before_models": True,
        "embargo": CONFIG["probe"]["embargo"],
        "embargo_covers_receptive_field": CONFIG["probe"]["embargo"] >= r0data.RECEPTIVE_FIELD,
        "per_machine_blocks": {m: {k: v["interval"] for k, v in data["machines"][m]["design_b"]["blocks"].items()} for m in r0data.MACHINES},
    }
    checks = {f"data.{k}": v for k, v in data["checks"].items()}
    checks.update({f"model.{k}": v for k, v in model["checks"].items()})
    checks["acquisition.all_verified"] = bool(acquisition and acquisition["status"] == "ACQUIRED_AND_VERIFIED")
    checks["design.embargo_covers_receptive_field"] = design["embargo_covers_receptive_field"]
    checks["tests.all_passed"] = bool(tests and tests.get("failures") == 0 and tests.get("errors") == 0)
    checks["no_metric_computed"] = not data["metric_guard"]["sklearn_imported"] and not model["metric_guard"]["metric_calls"]
    checks["model_stage_read_no_labels"] = not model["label_access_log"]
    return {
        "stage": "R0 preflight", "protocol_version": CONFIG["protocol_version"], "base_main": CONFIG["base_main"],
        "code_sha256": code, "design": design, "checks": checks, "pass": all(checks.values()),
        "data": data, "model": model, "tests": tests,
        "acquisition_summary": {"status": acquisition["status"], "blocked": acquisition["blocked"]} if acquisition else None,
        "statement": "Result-blind: no detector trained, no probe fitted, no AP/AUROC/recall computed.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="R0 result-blind preflight")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("data", "model"):
        p = sub.add_parser(name)
        p.add_argument("--out", type=Path, required=True)
    a = sub.add_parser("assemble")
    a.add_argument("--data", type=Path, required=True)
    a.add_argument("--model", type=Path, required=True)
    a.add_argument("--acquisition", type=Path)
    a.add_argument("--tests", type=Path)
    a.add_argument("--out", type=Path, default=OUT_DIR / "preflight.json")
    a.add_argument("--manifest", type=Path, default=OUT_DIR / "dataset_manifest.json")
    args = parser.parse_args(argv)
    if args.command == "assemble":
        result = assemble(args.data, args.model, args.acquisition, args.tests)
        acquisition = json.loads(args.acquisition.read_text()) if args.acquisition else None
        args.manifest.write_text(json.dumps(dataset_manifest(result["data"], acquisition), indent=2) + "\n")
    else:
        result = data_preflight() if args.command == "data" else model_preflight()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    failed = [k for k, v in result["checks"].items() if not v]
    print(json.dumps({"stage": args.command, "pass": result["pass"], "failed_checks": failed}))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
