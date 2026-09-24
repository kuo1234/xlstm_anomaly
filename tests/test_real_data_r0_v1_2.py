"""r0-v1.2 tests: single-implementation auditable matched LSTM (no labels, no R0 outcomes).

Run on GB10:  python3 tests/test_real_data_r0_v1_2.py      (torch tests run)
Run locally:  python -m pytest tests/test_real_data_r0_v1_2.py   (torch tests skip without torch)
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import real_data_r0_data as r0data  # noqa: E402

HAS_TORCH = importlib.util.find_spec("torch") is not None
RESULTS = ROOT / "research" / "real_data_r0"
AUDITABLE_SOURCE = (ROOT / "scripts" / "real_data_r0_lstm_v1_2.py").read_text()
RUNNER_SOURCE = (ROOT / "scripts" / "real_data_r0_execute.py").read_text()
BASE_COLUMNS = ['hidden_mean', 'hidden_std', 'hidden_rms', 'hidden_delta_rms', 'input_mean', 'input_std', 'input_q10',
                'input_q90', 'input_delta_mean', 'retention_mean', 'retention_std', 'retention_q10', 'retention_q90',
                'retention_delta_mean', 'memory_mean', 'memory_std', 'memory_rms', 'memory_relative_delta_norm']


def _calls(source: str) -> set[str]:
    out = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            f = node.func
            out.add(f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", ""))
    return out


class StaticV12(unittest.TestCase):
    def test_native_implementations_never_called_in_scientific_path(self):
        calls = _calls(AUDITABLE_SOURCE) | _calls(RUNNER_SOURCE)
        for name in ("LSTM", "LSTMCell", "replay", "Observer", "build_lstm", "cuda_overlay_from_vanilla"):
            self.assertNotIn(name, calls, name)
        self.assertNotIn('"lstm", x)', RUNNER_SOURCE)  # no sealed native-LSTM observer path

    def test_amendment_pins_and_invalidation(self):
        a = json.loads((RESULTS / "amendment_v1_2.json").read_text())
        self.assertEqual(a["protocol_version"], "r0-v1.2")
        self.assertEqual(a["matched_lstm"]["trainable_parameters"], 74_100)
        units = a["carried_forward_xlstm"]["units"]
        self.assertEqual(len(units), 9)
        for name, pin in units.items():
            record = RESULTS / "runs" / f"extract_v1_1_{name}.json"
            self.assertEqual(hashlib.sha256(record.read_bytes()).hexdigest(), pin["extraction_record_sha256"])
            train = json.loads((RESULTS / "runs" / f"train_{name}.json").read_text())
            self.assertEqual(train["checkpoints"]["best.pt"], pin["best_checkpoint_sha256"])
            self.assertEqual(train["best_model_hash"], pin["best_model_hash"])
            self.assertEqual(json.loads(record.read_text())["feature_cache"]["sha256"], pin["feature_cache_sha256"])
        native = a["invalidated_native_lstm"]["machine-1-8_lstm_11"]
        self.assertEqual(native["status"], "INVALIDATED_BY_R0_V1_2_SINGLE_IMPLEMENTATION_LSTM_AMENDMENT")
        self.assertIn("not because of any result", native["reason"])

    def test_sealed_experiment_unchanged(self):
        sealed = json.loads((RESULTS / "preflight.json").read_text())["code_sha256"]
        for path, digest in sealed.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest, path)


@unittest.skipUnless(HAS_TORCH, "torch unavailable")
class AuditableLSTM(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch

        import real_data_r0_lstm_v1_2 as auditable

        cls.torch, cls.auditable = torch, auditable

    def _layer(self):
        torch = self.torch
        layer = self.auditable.AuditableLSTMLayer(3, 2).double()
        with torch.no_grad():
            layer.weight_ih.copy_(torch.linspace(-0.8, 0.9, 24, dtype=torch.float64).reshape(8, 3))
            layer.weight_hh.copy_(torch.linspace(0.7, -0.6, 16, dtype=torch.float64).reshape(8, 2))
            layer.bias_ih.copy_(torch.linspace(-0.3, 0.4, 8, dtype=torch.float64))
            layer.bias_hh.copy_(torch.linspace(0.2, -0.1, 8, dtype=torch.float64))
        return layer

    def test_equation_correctness_one_step(self):
        torch = self.torch
        layer = self._layer()
        x = torch.tensor([[0.5, -1.0, 2.0]], dtype=torch.float64)
        h0 = torch.tensor([[0.1, -0.2]], dtype=torch.float64)
        c0 = torch.tensor([[0.3, 0.05]], dtype=torch.float64)
        W, U = layer.weight_ih.detach().numpy(), layer.weight_hh.detach().numpy()
        raw = W @ x[0].numpy() + layer.bias_ih.detach().numpy() + U @ h0[0].numpy() + layer.bias_hh.detach().numpy()
        sig = lambda v: 1 / (1 + np.exp(-v))  # noqa: E731
        i, f, g, o = sig(raw[0:2]), sig(raw[2:4]), np.tanh(raw[4:6]), sig(raw[6:8])
        c = f * c0[0].numpy() + i * g
        h = o * np.tanh(c)
        h1, c1, gates = layer.step(x, h0, c0)
        for key, value in {"i": i, "f": f, "g": g, "o": o}.items():
            np.testing.assert_allclose(gates[key][0].detach().numpy(), value, rtol=0, atol=1e-12)
        np.testing.assert_allclose(c1[0].detach().numpy(), c, rtol=0, atol=1e-12)
        np.testing.assert_allclose(h1[0].detach().numpy(), h, rtol=0, atol=1e-12)
        self.assertTrue(math.isclose(float(gates["o"][0, 0]), float(sig(raw[6])), abs_tol=1e-12))

    def test_multi_step_equals_sequence_api(self):
        torch = self.torch
        layer = self._layer()
        x = torch.randn(4, 7, 3, generator=torch.Generator().manual_seed(0), dtype=torch.float64)
        seq, traces = layer(x, capture=True)
        h = c = torch.zeros(4, 2, dtype=torch.float64)
        hs, cs, fs = [], [], []
        for t in range(7):
            h, c, gates = layer.step(x[:, t], h, c)
            hs.append(h), cs.append(c), fs.append(gates["f"])
        self.assertTrue(torch.equal(seq, torch.stack(hs, 1)))
        self.assertTrue(torch.equal(traces["memory"], torch.stack(cs, 1)))
        self.assertTrue(torch.equal(traces["retention"], torch.stack(fs, 1)))

    def test_trace_capture_does_not_change_output(self):
        torch = self.torch
        model = self.auditable.build(11, device="cpu").eval()
        x = torch.randn(8, 64, 38, generator=torch.Generator().manual_seed(3))
        with torch.no_grad():
            off = model(x)
            on, traces = model(x, capture=True)
        self.assertTrue(torch.equal(off, on))
        self.assertEqual(set(traces), set(self.auditable.LAYERS))
        for layer in traces.values():
            self.assertEqual(set(layer), {"hidden", "input", "retention", "memory"})
            self.assertEqual(tuple(layer["hidden"].shape), (8, 64, 38))

    def test_parameter_count_and_seed_determinism(self):
        torch = self.torch
        for seed in (11, 22, 33):
            a, b = self.auditable.build(seed, device="cpu"), self.auditable.build(seed, device="cpu")
            self.assertEqual(sum(p.numel() for p in a.parameters() if p.requires_grad), 74_100)
            for (ka, va), (kb, vb) in zip(a.state_dict().items(), b.state_dict().items()):
                self.assertEqual(ka, kb)
                self.assertTrue(torch.equal(va, vb), ka)
        self.assertFalse(torch.equal(self.auditable.build(11, device="cpu").encoder[0].weight_ih,
                                     self.auditable.build(22, device="cpu").encoder[0].weight_ih))

    def test_feature_schema_and_causality(self):
        torch = self.torch
        from phase_g1_core import expand_internal234, history14

        model = self.auditable.build(11, device="cpu").eval()
        rng = np.random.default_rng(5)
        stream = rng.normal(size=(200, 38)).astype(np.float32)
        perturbed = stream.copy()
        perturbed[150:] += 3.0
        edges = np.arange(63, 200)
        ra = self.auditable.extract_windows(model, r0data.window_matrix(stream, edges))
        rb = self.auditable.extract_windows(model, r0data.window_matrix(perturbed, edges))
        self.assertEqual(ra["internal_base18"].shape, (len(edges), 18))
        h, i = history14(ra["score"]), expand_internal234(ra["internal_base18"])
        self.assertEqual((h.shape[1], i.shape[1]), (14, 234))
        before = edges < 150
        np.testing.assert_array_equal(ra["score"][before], rb["score"][before])
        np.testing.assert_array_equal(ra["internal_base18"][before], rb["internal_base18"][before])
        np.testing.assert_array_equal(h[before], history14(rb["score"])[before])
        self.assertFalse(np.array_equal(ra["score"][~before], rb["score"][~before]))
        from phase_e2_schema import BASE_COLUMNS as sealed_columns

        self.assertEqual(list(sealed_columns), BASE_COLUMNS)

    def test_runtime_native_exclusion(self):
        code = ("import sys; sys.path.insert(0, 'scripts'); import torch, real_data_r0_lstm_v1_2 as a; a.forbid_native_lstm(); "
                "m = a.build(11, device='cpu'); m(torch.zeros(2, 64, 38)); ok = []\n"
                "for f in (lambda: torch.nn.LSTM(2, 2), lambda: torch.nn.LSTMCell(2, 2)):\n"
                "    try:\n        f()\n    except Exception as e:\n        ok.append(type(e).__name__)\n"
                "import phase_f_lstm_observer as p\ntry:\n    p.replay(None, None)\nexcept Exception as e:\n    ok.append(type(e).__name__)\n"
                "print(ok)")
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        self.assertIn("['ProtocolViolation', 'ProtocolViolation', 'ProtocolViolation']", out)

    def test_label_isolation(self):
        import real_data_r0_execute as runner

        for function in (runner.train, runner.extract, runner._lstm_gate_v1_2, runner.preflight_v1_2,
                         runner.invalidate_native_lstm, runner.seal_features):
            self.assertNotIn("load_test_labels", inspect.getsource(function), function.__name__)
        for function in (self.auditable.extract_windows, self.auditable.extract_batch, self.auditable.build):
            self.assertFalse(set(inspect.signature(function).parameters) & {"label", "labels", "y", "target"})

    def test_runner_plan_for_lstm(self):
        import real_data_r0_execute as runner

        plan = runner.extraction_plan("lstm")
        self.assertEqual((plan["backend"], plan["record_version"], plan["cache_file"]),
                         ("auditable_manual_v1_2", "r0-v1.2", "features_v1_2.npz"))
        self.assertEqual(runner._train_record_path("machine-1-8_lstm_11").name, "train_v1_2_machine-1-8_lstm_11.json")
        self.assertEqual(runner._train_record_path("machine-1-8_xlstm_11").name, "train_machine-1-8_xlstm_11.json")
        self.assertEqual(runner._run_dir("machine-1-8", "lstm", 11).name, "lstm_v1_2_11")
        native_record = json.loads((RESULTS / "runs" / "train_machine-1-8_lstm_11.json").read_text())
        self.assertNotIn("protocol_version", native_record)  # the native record can never satisfy a v1.2 lookup


def _main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path)
    args, _ = parser.parse_known_args()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {"tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
               "skipped": len(result.skipped), "torch_available": HAS_TORCH,
               "failed": [str(t) for t, _ in result.failures + result.errors]}
    if args.json:
        args.json.write_text(json.dumps(summary, indent=2) + "\n")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(_main())
