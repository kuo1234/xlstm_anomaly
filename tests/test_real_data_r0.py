"""R0 protocol/preflight unit tests (unittest-compatible; torch tests skip without torch).

Run on GB10:  python3 -m unittest tests.test_real_data_r0 -v
Run locally:  python -m pytest tests/test_real_data_r0.py
No real R0 data, label or model output is used here; all arrays are synthetic.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import real_data_r0_data as r0data  # noqa: E402
import real_data_r0_models as r0models  # noqa: E402
import real_data_r0_probe as r0probe  # noqa: E402
from phase_g1_core import expand_internal234, history14  # noqa: E402

HAS_TORCH = importlib.util.find_spec("torch") is not None
HAS_SKLEARN = importlib.util.find_spec("sklearn") is not None
CONFIG = r0data.CONFIG


class ConfigContract(unittest.TestCase):
    def test_frozen_scope(self):
        self.assertEqual(r0data.MACHINES, ("machine-1-8", "machine-2-1", "machine-1-4"))
        self.assertEqual(CONFIG["detector"]["seeds"], [11, 22, 33])
        self.assertEqual(CONFIG["detector"]["backbones"], ["xlstm", "lstm"])
        self.assertEqual(CONFIG["detector"]["fits_planned"], 3 * 2 * 3)
        self.assertEqual(CONFIG["probe"]["design"], "B")
        self.assertEqual(CONFIG["base_main"], "b7ae44fafc4e9ea6671647c5cb73156ddaf26e5e")
        self.assertEqual(set(CONFIG["probe"]["arms"]), {"H", "H+I"})
        self.assertEqual(CONFIG["probe"]["hgb_fits_planned"], 3 * 3 * 2 * 2 * 2)

    def test_window_constants(self):
        self.assertEqual((r0data.W, r0data.FIRST_DECISION, r0data.FIRST_FINITE, r0data.RECEPTIVE_FIELD), (64, 63, 94, 95))
        self.assertGreaterEqual(r0data.EMBARGO, r0data.RECEPTIVE_FIELD)

    def test_raw_files_are_original_text_not_candi(self):
        for machine in r0data.MACHINES:
            for split in r0data.SPLITS:
                self.assertTrue(r0data.raw_path(machine, split).name.endswith(".txt"))
                self.assertIn("NetManAIOps/OmniAnomaly/7fb0e0ac", r0data.source_url(machine, split))

    def test_hgb_family_identical_to_frozen_nonlinear_line(self):
        from nonlinear_observable_control import MAX_ITER_GRID, estimator_parameters

        self.assertEqual(tuple(r0probe.MAX_ITER_GRID), tuple(MAX_ITER_GRID))
        for max_iter in MAX_ITER_GRID:
            self.assertEqual(r0probe.estimator_parameters(max_iter), estimator_parameters(max_iter))


class Capacity(unittest.TestCase):
    def test_formula_reproduces_sealed_d8_count(self):
        self.assertEqual(r0models.lstm_parameter_count(38, d=8), 71790)

    def test_d38_width_rule(self):
        rule = r0models.select_lstm_width(CONFIG["detector"]["xlstm"]["trainable_parameters"])
        self.assertEqual(rule["width"], 38)
        self.assertEqual(rule["parameters"], 74100)
        self.assertLessEqual(abs(rule["relative_difference"]), 0.10)
        self.assertEqual(CONFIG["detector"]["lstm"]["trainable_parameters"], 74100)


class SplitsAndScaler(unittest.TestCase):
    def test_fit_end(self):
        for machine, value in CONFIG["split"]["expected_fit_end"].items():
            self.assertEqual(r0data.fit_end(CONFIG["dataset"]["expected"][machine]["train_N"]), value)

    def test_phase_a_seal_intervals(self):
        seal = {row["machine"]: row for row in json.loads((ROOT / "reports/phase_a/smd_seal.json").read_text())}
        for machine in ("machine-1-8", "machine-2-1"):
            n = CONFIG["dataset"]["expected"][machine]["train_N"]
            self.assertEqual(seal[machine]["audit_fit_interval"], [0, r0data.fit_end(n)])
            self.assertEqual(seal[machine]["audit_calibration_interval"], [r0data.fit_end(n), n])
            for split in r0data.SPLITS:
                asset = next(a for a in seal[machine]["assets"] if a["path"].endswith(f"{machine}_{split}.txt"))
                self.assertEqual(asset["bytes"], CONFIG["dataset"]["expected"][machine][split]["bytes"])

    def test_scaler_fit_only_and_zero_std(self):
        rng = np.random.default_rng(0)
        x = rng.normal(size=(500, 38))
        x[:, 5] = 0.25
        scaler = r0data.fit_scaler(x)
        self.assertEqual(scaler["zero_std_channels"], [5])
        self.assertEqual(scaler["scale"][5], 1.0)
        y = x.copy()
        y[r0data.fit_end(500):] = 1e6
        other = r0data.fit_scaler(y)
        np.testing.assert_array_equal(scaler["mean"], other["mean"])
        np.testing.assert_array_equal(scaler["scale"], other["scale"])
        self.assertEqual(r0data.apply_scaler(x, scaler).dtype, np.float32)


class WindowsAndLabels(unittest.TestCase):
    def test_edges_do_not_straddle(self):
        n = 1000
        end = r0data.fit_end(n)
        fit, val = r0data.fit_window_edges(n), r0data.validation_window_edges(n)
        self.assertEqual(fit[0], 63)
        self.assertLess(fit[-1], end)
        self.assertGreaterEqual(val[0] - 63, end)
        self.assertEqual(len(fit) + len(val), n - 2 * 63)

    def test_window_matrix(self):
        x = np.arange(200 * 38, dtype=np.float32).reshape(200, 38)
        edges = np.array([63, 100, 199])
        windows = r0data.window_matrix(x, edges)
        for row, t in enumerate(edges):
            np.testing.assert_array_equal(windows[row], x[t - 63 : t + 1])

    def test_window_any_labels(self):
        labels = (np.random.default_rng(1).random(700) < 0.02).astype(np.uint8)
        edges = r0data.test_window_edges(700)
        expected = np.array([labels[t - 63 : t + 1].max() for t in edges])
        np.testing.assert_array_equal(r0data.window_any_labels(labels, edges), expected)

    def test_design_b_blocks(self):
        for n in [CONFIG["dataset"]["expected"][m]["test_N"] for m in r0data.MACHINES] + [1000, 5003]:
            blocks = r0data.design_b_blocks(n)
            self.assertEqual(blocks["train"][0], 94)
            self.assertEqual(blocks["test"][1], n)
            self.assertEqual(blocks["validation"][0] - blocks["train"][1], 96)
            self.assertEqual(blocks["test"][0] - blocks["validation"][1], 96)
            last_train = r0data.receptive_interval(blocks["train"][1] - 1)
            first_val = r0data.receptive_interval(blocks["validation"][0])
            self.assertLess(last_train[1], first_val[0])
            # window-any label windows (t-63..t) are also disjoint across blocks
            self.assertLess(blocks["train"][1] - 1, blocks["validation"][0] - 63)

    def test_label_guard(self):
        with self.assertRaises(r0data.ProtocolViolation):
            r0data.load_test_labels("machine-1-8", purpose="training")
        with self.assertRaises(TypeError):
            r0data.load_test_labels("machine-1-8")  # purpose is keyword-only and mandatory

    def test_model_facing_apis_take_no_labels(self):
        forbidden = r0models.FORBIDDEN_PARAMETER_NAMES
        for name, params in r0models.observation_only_signatures().items():
            self.assertFalse(set(params) & forbidden, name)


class FeatureCausality(unittest.TestCase):
    def test_history_and_internal_warmup_and_causality(self):
        rng = np.random.default_rng(2)
        n = 337  # right edges 63..399
        score, base = rng.random(n), rng.normal(size=(n, 18))
        h, i = history14(score), expand_internal234(base)
        self.assertEqual((h.shape[1], i.shape[1]), (14, 234))
        finite = np.isfinite(h).all(1) & np.isfinite(i).all(1)
        self.assertEqual(int(np.flatnonzero(finite)[0]), r0data.FIRST_FINITE - r0data.FIRST_DECISION)
        self.assertTrue(finite[31:].all())
        cut = 200
        score2, base2 = score.copy(), base.copy()
        score2[cut:] += 10
        base2[cut:] -= 10
        np.testing.assert_array_equal(history14(score2)[:cut], h[:cut])
        np.testing.assert_array_equal(expand_internal234(base2)[:cut], i[:cut])


class _Stub:
    def __init__(self, max_iter, values):
        self.max_iter, self.values = max_iter, values

    def fit(self, x, y):
        return self

    def predict_proba(self, x):
        p = np.full(len(x), self.values[self.max_iter])
        return np.column_stack((1 - p, p))


class ProbeIsolation(unittest.TestCase):
    def _run(self, values, test_labels, calls):
        x = np.zeros((10, 3))
        y = np.array([0, 1] * 5)

        def loader():
            calls.append("test_labels")
            return test_labels

        return r0probe.select_and_evaluate(
            x, y, x, y, x, loader,
            estimator_factory=lambda m: _Stub(m, values),
            ap=lambda yy, ss: float(ss.mean()) if len(calls) == 0 else float(np.mean(yy)),
        )

    def test_tie_selects_100_and_labels_read_once_after_selection(self):
        calls = []
        result = self._run({100: 0.5, 300: 0.5}, np.array([0, 1] * 5), calls)
        self.assertEqual(result["selected_max_iter"], 100)
        self.assertTrue(result["tie"])
        self.assertEqual(calls, ["test_labels"])

    def test_selection_is_invariant_to_test_labels(self):
        a = self._run({100: 0.4, 300: 0.6}, np.array([0, 1] * 5), [])
        b = self._run({100: 0.4, 300: 0.6}, np.array([1, 0] * 5), [])
        self.assertEqual(a["selected_max_iter"], 300)
        self.assertEqual(a["selected_max_iter"], b["selected_max_iter"])
        self.assertEqual(a["validation_ap"], b["validation_ap"])

    @unittest.skipUnless(HAS_SKLEARN, "sklearn unavailable")
    def test_real_hgb_on_synthetic_data(self):
        rng = np.random.default_rng(3)
        x = rng.normal(size=(900, 248))
        y = (x[:, 0] + 0.5 * rng.normal(size=900) > 1).astype(int)
        calls = []

        def loader():
            calls.append(1)
            return y[600:]

        result = r0probe.select_and_evaluate(x[:400], y[:400], x[400:600], y[400:600], x[600:], loader)
        self.assertIn(result["selected_max_iter"], (100, 300))
        self.assertEqual(calls, [1])


class EstimandAndWording(unittest.TestCase):
    machines, seeds = ("machine-1-8", "machine-2-1", "machine-1-4"), (11, 22, 33)

    def _classify(self, matrix):
        summary = r0probe.summarize_matrix(matrix, self.machines, self.seeds)
        two = r0probe.two_way_bootstrap(matrix, draws=2000)
        one = r0probe.machine_only_bootstrap(matrix, draws=2000)
        return r0probe.classify(summary, two, one)["class"], summary, two, one

    def test_positive_negative_null(self):
        self.assertEqual(self._classify(np.full((3, 3), 0.05))[0], "R0_POSITIVE_INCREMENT")
        self.assertEqual(self._classify(np.full((3, 3), -0.05))[0], "R0_NEGATIVE_INCREMENT")
        mixed = np.array([[0.05, 0.04, 0.06], [-0.02, -0.01, -0.03], [0.01, -0.01, 0.0]])
        self.assertEqual(self._classify(mixed)[0], "R0_NO_RESOLVED_INCREMENT")

    def test_bootstrap_deterministic(self):
        m = np.random.default_rng(4).normal(size=(3, 3))
        self.assertEqual(r0probe.two_way_bootstrap(m), r0probe.two_way_bootstrap(m))
        self.assertEqual(r0probe.machine_only_bootstrap(m), r0probe.machine_only_bootstrap(m))

    def test_summary_fields(self):
        _, summary, _, _ = self._classify(np.arange(9.0).reshape(3, 3) - 4)
        self.assertEqual(summary["positive_cells"], 4)
        self.assertEqual(set(summary["machine_means"]), set(self.machines))


class MetricTrap(unittest.TestCase):
    @unittest.skipUnless(HAS_SKLEARN, "sklearn unavailable")
    def test_metric_trap_blocks_metric_calls_in_a_fresh_process(self):
        import subprocess

        code = ("import sys; sys.path.insert(0, 'scripts'); import real_data_r0_preflight as pf; pf.install_metric_trap(); "
                "from sklearn.metrics import average_precision_score as ap\n"
                "try:\n    ap([0, 1], [0.1, 0.9])\nexcept Exception as e:\n    print(type(e).__name__, pf._METRIC_CALLS)\n")
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        self.assertIn("ProtocolViolation ['average_precision_score']", out)


def _random_lstm_traces(torch, generator, batch=6, steps=5, width=38):
    from phase_f_lstm_observer import LAYERS

    traces = {}
    for layer in LAYERS:
        traces[layer] = {"hidden": torch.randn(batch, steps, width, generator=generator, dtype=torch.float64),
                         "input": torch.rand(batch, steps, width, generator=generator, dtype=torch.float64),
                         "retention": torch.rand(batch, steps, width, generator=generator, dtype=torch.float64),
                         "memory": torch.randn(batch, steps, width, generator=generator, dtype=torch.float64)}
    return traces


@unittest.skipUnless(HAS_TORCH, "torch unavailable")
class SemanticAudit(unittest.TestCase):
    polarity = {"hidden_mean", "hidden_std", "memory_mean", "memory_std"}

    def _check(self, traces, summarize, heads):
        import torch
        from phase_e2_schema import BASE_COLUMNS

        generator = torch.Generator().manual_seed(7)
        base = summarize(traces)
        perm_traces, flip_traces = {}, {}
        for cell, layer in traces.items():
            units = layer["hidden"].shape[-1]
            perm = torch.randperm(units, generator=generator)
            sign = torch.where(torch.rand(units, generator=generator) < 0.5, -1.0, 1.0).to(torch.float64)
            head_perm = torch.randperm(layer["hidden"].shape[2], generator=generator) if heads else None
            perm_traces[cell] = {}
            flip_traces[cell] = {}
            for key, value in layer.items():
                v = value.index_select(-1, perm)
                perm_traces[cell][key] = v.index_select(2, head_perm) if heads else v
                flip_traces[cell][key] = value * sign if key in ("hidden", "memory") else value
        torch.testing.assert_close(summarize(perm_traces), base, atol=1e-10, rtol=1e-10)
        delta = (summarize(flip_traces) - base).abs().amax(0)
        changed = {BASE_COLUMNS[i] for i in range(18) if float(delta[i]) > 1e-9}
        self.assertEqual(changed, self.polarity)

    def test_lstm_reduction(self):
        import torch
        from phase_f_lstm_observer import summarize

        self._check(_random_lstm_traces(torch, torch.Generator().manual_seed(1)), summarize, heads=False)

    def test_xlstm_reduction(self):
        import torch
        from phase_e2_schema import SCALAR_CELLS, summarize

        g = torch.Generator().manual_seed(2)
        traces = {cell: {"hidden": torch.randn(6, 5, 4, 10, generator=g, dtype=torch.float64),
                         "input": torch.rand(6, 5, 4, 10, generator=g, dtype=torch.float64),
                         "retention": torch.rand(6, 5, 4, 10, generator=g, dtype=torch.float64),
                         "memory": torch.randn(6, 5, 4, 10, generator=g, dtype=torch.float64)} for cell in SCALAR_CELLS}
        self._check(traces, summarize, heads=True)

    def test_lstm_d38_network_symmetries_on_cpu(self):
        import torch
        import real_data_r0_preflight as pf
        from phase_f_lstm_observer import extract

        model = r0models.build_lstm(11, device="cpu").eval()
        self.assertEqual(sum(p.numel() for p in model.parameters()), 74100)
        x = torch.randn(8, 64, 38, generator=torch.Generator().manual_seed(3))
        score0, base0 = extract(model, x)
        out0 = model(x).detach()
        permuted = r0models.build_lstm(11, device="cpu").eval()
        pf._lstm_permute(permuted, torch.Generator().manual_seed(5))
        score1, base1 = extract(permuted, x)
        torch.testing.assert_close(permuted(x).detach(), out0, atol=1e-5, rtol=1e-4)
        torch.testing.assert_close(base1, base0, atol=1e-5, rtol=1e-4)
        flipped = r0models.build_lstm(11, device="cpu").eval()
        pf._lstm_sign_flip(flipped, torch.Generator().manual_seed(6))
        score2, base2 = extract(flipped, x)
        torch.testing.assert_close(flipped(x).detach(), out0, atol=1e-5, rtol=1e-4)
        torch.testing.assert_close(score2, score0, atol=1e-5, rtol=1e-4)
        from phase_e2_schema import BASE_COLUMNS

        delta = (base2 - base0).abs().amax(0)
        changed = {BASE_COLUMNS[i] for i in range(18) if float(delta[i]) > 1e-5}
        self.assertEqual(changed, self.polarity)


def _main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path)
    args, rest = parser.parse_known_args()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {"tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
               "skipped": len(result.skipped), "torch_available": HAS_TORCH, "sklearn_available": HAS_SKLEARN,
               "failed": [str(t) for t, _ in result.failures + result.errors]}
    if args.json:
        args.json.write_text(json.dumps(summary, indent=2) + "\n")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(_main())
