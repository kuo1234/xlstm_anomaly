"""r0-v1.1 amendment tests: single-backend xLSTM extraction, cache validation, unchanged experiment.

Run on GB10:  python3 tests/test_real_data_r0_v1_1.py
Run locally:  python -m pytest tests/test_real_data_r0_v1_1.py
"""
from __future__ import annotations

import ast
import hashlib
import inspect
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import real_data_r0_data as r0data  # noqa: E402
import real_data_r0_execute as runner  # noqa: E402
import real_data_r0_probe as r0probe  # noqa: E402

RESULTS = ROOT / "research" / "real_data_r0"
RUNNER_SOURCE = (ROOT / "scripts" / "real_data_r0_execute.py").read_text()
REUSED = ("machine-1-8_xlstm_11", "machine-1-8_xlstm_22", "machine-1-8_xlstm_33",
          "machine-2-1_xlstm_11", "machine-2-1_xlstm_22", "machine-2-1_xlstm_33")


def _called_names(source: str) -> set[str]:
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            f = node.func
            names.add(f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", ""))
    return names


def _v1_1_record(backbone: str = "xlstm") -> dict:
    plan = runner.extraction_plan(backbone)  # r0-v1.2 supersedes the LSTM plan; the xLSTM plan is the v1.1 one
    return {"protocol_version": plan["record_version"], "status": "PASS", "extraction_backend": plan["backend"],
            "gate": {"name": plan["gate"], "pass": True}, "label_read_count": 0,
            "dimensions": {"H": 14, "internal234": 234},
            "feature_cache": {"file": f"data/r0_runs/m/{backbone}_11/{plan['cache_file']}"}}


class AmendmentV11(unittest.TestCase):
    # 1. v1.1 xLSTM extraction never calls the CUDA overlay
    def test_xlstm_extraction_never_calls_cuda_overlay(self):
        called = _called_names(RUNNER_SOURCE)
        for forbidden in ("cuda_overlay_from_vanilla", "build_xlstm_cuda", "map_vanilla_weights", "FastStateObserver"):
            self.assertNotIn(forbidden, called)
        self.assertEqual(runner.extraction_plan("xlstm")["arch"], "xlstm_reference")
        extract_source = inspect.getsource(runner.extract)
        self.assertIn("_forbid_cuda_overlay(models)", extract_source)
        self.assertIn('model, arch = reference, plan["arch"]', extract_source)

        class FakeModels:
            def cuda_overlay_from_vanilla(self, *a):
                return "cuda"

        fake = FakeModels()
        runner._forbid_cuda_overlay(fake)
        with self.assertRaises(r0data.ProtocolViolation):
            fake.cuda_overlay_from_vanilla(None)
        with self.assertRaises(r0data.ProtocolViolation):
            fake.build_xlstm_cuda()

    # 2. v1.1 caches identify the backend as vanilla_reference
    def test_v1_1_records_identify_backend(self):
        self.assertEqual(runner.EXTRACTION_PLAN["xlstm"]["record_version"], "r0-v1.1")
        self.assertEqual(runner.extraction_plan("xlstm")["backend"], "vanilla_reference")
        runner.validate_extract_record(_v1_1_record("xlstm"), "xlstm")
        runner.validate_extract_record(_v1_1_record("lstm"), "lstm")
        self.assertIn('"extraction_backend": plan["backend"]', inspect.getsource(runner.extract))
        self.assertEqual(runner.CACHE_FILE, "features_v1_1.npz")

    # 3. old CUDA caches cannot pass v1.1 validation
    def test_v1_cuda_records_and_caches_rejected(self):
        for name in ("machine-1-8_xlstm_11", "machine-2-1_xlstm_33"):
            v1 = json.loads((RESULTS / "runs" / f"extract_{name}.json").read_text())
            with self.assertRaises(r0data.ProtocolViolation):
                runner.validate_extract_record(v1, "xlstm")
        forged = _v1_1_record("xlstm")
        forged["extraction_backend"] = "cuda_fast"
        with self.assertRaises(r0data.ProtocolViolation):
            runner.validate_extract_record(forged, "xlstm")
        forged = _v1_1_record("xlstm")
        forged["feature_cache"]["file"] = "data/r0_runs/m/xlstm_11/features.npz"
        with self.assertRaises(r0data.ProtocolViolation):
            runner.validate_extract_record(forged, "xlstm")
        forged = _v1_1_record("xlstm")
        forged["label_read_count"] = 1
        with self.assertRaises(r0data.ProtocolViolation):
            runner.validate_extract_record(forged, "xlstm")
        self.assertNotEqual(runner.INVALIDATED_V1_CACHE_FILE, runner.CACHE_FILE)
        amendment = json.loads((RESULTS / "amendment_v1_1.json").read_text())
        self.assertEqual(sum(1 for v in amendment["invalidated_v1_caches"].values() if v["v1_cache_sha256"]), 5)

    # 4. checkpoint identities unchanged
    def test_reused_checkpoint_identities(self):
        amendment = json.loads((RESULTS / "amendment_v1_1.json").read_text())
        self.assertEqual(set(amendment["reused_checkpoints"]["units"]), set(REUSED))
        self.assertFalse(amendment["reused_checkpoints"]["retraining"])
        for name in REUSED:
            record = json.loads((RESULTS / "runs" / f"train_{name}.json").read_text())
            reused = amendment["reused_checkpoints"]["units"][name]
            self.assertEqual(record["status"], "PASS")
            self.assertEqual(record["checkpoints"]["best.pt"], reused["best_checkpoint_sha256"])
            self.assertEqual(record["best_model_hash"], reused["best_model_hash"])
            self.assertEqual(record["parameter_count"], 75934)
            self.assertFalse(record["labels_read"])

    # 5. no labels during train/extract
    def test_no_label_access_in_train_extract_or_preflight(self):
        for function in (runner.train, runner.extract, runner._xlstm_gate_v1_1, runner._lstm_gate_v1_2,
                         runner.invalidate_v1_caches, runner.preflight_v1_1, runner.seal_features, runner._run_unit):
            self.assertNotIn("load_test_labels", inspect.getsource(function), function.__name__)

    # 6. original Design-B/probe rules unchanged
    def test_sealed_experiment_unchanged(self):
        sealed = json.loads((RESULTS / "preflight.json").read_text())["code_sha256"]
        for path, digest in sealed.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest, path)
        config = r0data.CONFIG
        self.assertEqual(config["probe"]["design"], "B")
        self.assertEqual(r0data.EMBARGO, 96)
        self.assertEqual(r0probe.MAX_ITER_GRID, (100, 300))
        self.assertEqual(config["estimand"]["two_way_bootstrap"]["draws"], 10_000)
        self.assertEqual(config["estimand"]["two_way_bootstrap"]["seed"], 901)
        self.assertEqual(config["estimand"]["machine_only_bootstrap"]["seed"], 901)
        self.assertEqual(runner.planned_runs(), [(m, b, s) for b in ("xlstm", "lstm") for m in r0data.MACHINES for s in (11, 22, 33)])
        probe_source = inspect.getsource(runner.probe)
        self.assertIn('purpose="probe_fit_selection"', probe_source)
        self.assertIn('purpose="probe_final_evaluation"', probe_source)
        self.assertIn("is_pushed()", probe_source)

    def test_cli_uses_v1_1_record_keys(self):
        main_source = inspect.getsource(runner.main)
        self.assertNotIn('record["parity"]', main_source)
        self.assertIn('record["gate"]["pass"]', main_source)

    # 7. (r0-v1.1) LSTM path unchanged — superseded for the matched LSTM by r0-v1.2; v1.1 LSTM evidence preserved
    def test_lstm_v1_1_evidence_preserved_and_superseded(self):
        stop = json.loads((RESULTS / "runs" / "stop_v1_1_machine-1-8_lstm_11.json").read_text())
        self.assertEqual(stop["status"], "STOP_OBSERVER_PARITY")
        self.assertEqual(stop["extraction_backend"], "lstm_manual_replay")
        self.assertTrue((RESULTS / "runs" / "diagnostic_v1_1_lstm_machine-1-8_11.json").exists())
        self.assertEqual(runner.extraction_plan("lstm")["backend"], "auditable_manual_v1_2")
        train_source = inspect.getsource(runner.train)
        self.assertIn("SeedSequence([seed, epoch, 1701])", train_source)
        self.assertIn("models.build_xlstm_vanilla(seed)", train_source)


def _main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--json", type=Path)
    args, _ = parser.parse_known_args()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {"tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
               "skipped": len(result.skipped), "failed": [str(t) for t, _ in result.failures + result.errors]}
    if args.json:
        args.json.write_text(json.dumps(summary, indent=2) + "\n")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(_main())
