"""Orchestration/integrity tests for the R0 execution runner (synthetic data only).

Run on GB10:  python3 tests/test_real_data_r0_execute.py
Run locally:  python -m pytest tests/test_real_data_r0_execute.py
"""
from __future__ import annotations

import functools
import importlib.util
import inspect
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import real_data_r0_data as r0data  # noqa: E402
import real_data_r0_probe as r0probe  # noqa: E402


def load_runner(results_dir: Path, runs_dir: Path):
    os.environ["R0_RESULTS_DIR"] = str(results_dir)
    os.environ["R0_RUNS_DATA"] = str(runs_dir)
    try:
        spec = importlib.util.spec_from_file_location(f"r0_execute_{id(results_dir)}", ROOT / "scripts" / "real_data_r0_execute.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        os.environ.pop("R0_RESULTS_DIR", None)
        os.environ.pop("R0_RUNS_DATA", None)


class _Stub:
    def __init__(self, max_iter):
        self.max_iter = max_iter

    def fit(self, x, y):
        self.w = np.linalg.lstsq(np.c_[x[:, :3], np.ones(len(x))], y, rcond=None)[0]
        return self

    def predict_proba(self, x):
        p = np.c_[x[:, :3], np.ones(len(x))] @ self.w + (0.001 if self.max_iter == 300 else 0.0)
        return np.column_stack((1 - p, p))


def _ap(y, s):
    order = np.argsort(-np.asarray(s), kind="stable")
    y = np.asarray(y)[order]
    hits = np.cumsum(y)
    return float((hits[y == 1] / (np.flatnonzero(y == 1) + 1)).mean())


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.runner = load_runner(base / "results", base / "runs_data")
        r0data._LABEL_ACCESS_LOG.clear()
        self._orig_labels = r0data.load_test_labels
        self._orig_select = r0probe.select_and_evaluate

    def tearDown(self):
        r0data.load_test_labels = self._orig_labels
        r0probe.select_and_evaluate = self._orig_select
        r0data._LABEL_ACCESS_LOG.clear()
        self.tmp.cleanup()

    def test_planned_units(self):
        units = self.runner.planned_runs()
        self.assertEqual(len(units), 18)
        self.assertEqual(len(set(units)), 18)
        self.assertEqual({u[0] for u in units}, {"machine-1-8", "machine-2-1", "machine-1-4"})
        self.assertEqual({u[1] for u in units}, {"xlstm", "lstm"})
        self.assertEqual({u[2] for u in units}, {11, 22, 33})
        self.assertEqual(self.runner.MAX_CONCURRENT_DETECTOR_PROCESSES, 2)
        with self.assertRaises(r0data.ProtocolViolation):
            self.runner.schedule(3)

    def test_immutable_records(self):
        path = self.runner.RUN_RECORDS / "x.json"
        self.runner.write_immutable(path, {"a": 1})
        with self.assertRaises(r0data.ProtocolViolation):
            self.runner.write_immutable(path, {"a": 2})
        self.assertEqual(json.loads(path.read_text()), {"a": 1})

    def test_training_and_extraction_never_touch_labels(self):
        for function in (self.runner.train, self.runner.extract, self.runner._run_unit, self.runner.schedule,
                         self.runner.seal_features, self.runner._lstm_gate_v1_2, self.runner._xlstm_gate_v1_1,
                         self.runner.invalidate_v1_caches, self.runner.preflight_v1_1, self.runner.preflight_v1_2,
                         self.runner.invalidate_native_lstm):
            self.assertNotIn("load_test_labels", inspect.getsource(function), function.__name__)

    def test_no_deferred_methods_in_runner(self):
        import re

        source = (ROOT / "scripts" / "real_data_r0_execute.py").read_text().lower()
        for term in ("zero_shot", "zero-shot", "pseudo", "lora", "adapter", "test_time", "few_shot", "tta", "hai"):
            self.assertIsNone(re.search(rf"\b{re.escape(term)}\b", source), term)

    def test_block_indices_follow_sealed_blocks(self):
        for machine in r0data.MACHINES:
            n = r0data.CONFIG["dataset"]["expected"][machine]["test_N"]
            edges = r0data.test_window_edges(n)
            rows = self.runner._block_indices(edges, n)
            for block, index in rows.items():
                start, stop = r0data.design_b_blocks(n)[block]
                np.testing.assert_array_equal(edges[index], np.arange(start, stop))
            self.assertGreaterEqual(int(rows["train"].min()), r0data.FIRST_FINITE - r0data.FIRST_DECISION)

    def test_probe_requires_sealed_manifest_and_orders_label_reads(self):
        runner = self.runner
        with self.assertRaises(r0data.ProtocolViolation):
            runner.probe(require_committed_manifest=False)
        machine, backbone, seed = "machine-2-1", "xlstm", 11
        n = r0data.CONFIG["dataset"]["expected"][machine]["test_N"]
        edges = r0data.test_window_edges(n)
        rng = np.random.default_rng(0)
        point = (rng.random(n) < 0.01).astype(np.uint8)
        window = r0data.window_any_labels(point, edges)
        history = rng.normal(size=(len(edges), 14))
        history[:, 0] += 2.0 * window
        history[:31] = np.nan
        internal = rng.normal(size=(len(edges), 234))
        internal[:31] = np.nan
        cache_dir = runner._run_dir(machine, backbone, seed)
        cache_dir.mkdir(parents=True)
        np.savez(cache_dir / runner.CACHE_FILE, edges=edges, H=history, internal234=internal, score=history[:, 0])
        manifest = {"entries": [{"run": runner.run_name(machine, backbone, seed), "machine": machine, "backbone": backbone,
                                 "seed": seed, "feature_cache_relpath": runner._cache_relpath(machine, backbone, seed),
                                 "feature_cache_sha256": runner.sha_file(cache_dir / runner.CACHE_FILE)}]}
        runner.write_immutable(runner.FEATURE_MANIFEST, manifest)

        def fake_labels(m, *, purpose):
            if purpose not in r0data.LABEL_PURPOSES:
                raise r0data.ProtocolViolation("purpose")
            r0data._LABEL_ACCESS_LOG.append({"machine": m, "purpose": purpose})
            return point

        r0data.load_test_labels = fake_labels
        r0probe.select_and_evaluate = functools.partial(self._orig_select, estimator_factory=_Stub, ap=_ap)
        summary = runner.probe(require_committed_manifest=False)
        self.assertEqual(summary["cells"], 1)
        purposes = [row["purpose"] for row in summary["label_access_log"]]
        self.assertEqual(purposes, ["probe_fit_selection", "probe_final_evaluation", "probe_final_evaluation"])
        record = json.loads(runner._probe_record_path(runner.run_name(machine, backbone, seed)).read_text())
        self.assertAlmostEqual(record["delta_ap"], record["arms"]["H+I"]["test_ap"] - record["arms"]["H"]["test_ap"])
        self.assertEqual(record["embargo"], 96)
        self.assertEqual(record["rows"]["test"], r0data.design_b_blocks(n)["test"][1] - r0data.design_b_blocks(n)["test"][0])
        with self.assertRaises(r0data.ProtocolViolation):
            runner.probe(require_committed_manifest=False)  # labels already read / records immutable

    def test_aggregate_uses_sealed_estimand_functions(self):
        runner = self.runner
        rng = np.random.default_rng(1)
        for machine, backbone, seed in runner.planned_runs():
            name = runner.run_name(machine, backbone, seed)
            ap_h, ap_hi = float(rng.uniform(0.2, 0.6)), float(rng.uniform(0.2, 0.6))
            arms = {"H": {"test_ap": ap_h, "selected_max_iter": 100, "validation_ap": {"100": 0.5, "300": 0.4}},
                    "H+I": {"test_ap": ap_hi, "selected_max_iter": 300, "validation_ap": {"100": 0.4, "300": 0.5}}}
            runner.write_immutable(runner._probe_record_path(name), {"run": name, "arms": arms, "delta_ap": ap_hi - ap_h})
        runner.write_immutable(runner.FEATURE_MANIFEST, {"entries": []})
        result = runner.aggregate()
        for backbone in ("xlstm", "lstm"):
            matrix = runner._matrix({runner.run_name(*u): json.loads(runner._probe_record_path(runner.run_name(*u)).read_text())
                                     for u in runner.planned_runs()}, backbone)
            b = result["backbones"][backbone]
            np.testing.assert_array_equal(np.array(b["delta_ap_matrix"]), matrix)
            self.assertEqual(b["two_way_bootstrap"], r0probe.two_way_bootstrap(matrix, draws=10_000, seed=901))
            self.assertEqual(b["machine_only_bootstrap"], r0probe.machine_only_bootstrap(matrix, draws=10_000, seed=901))
            summary = r0probe.summarize_matrix(matrix, r0data.MACHINES, (11, 22, 33))
            self.assertEqual(b["classification"], r0probe.classify(summary, b["two_way_bootstrap"], b["machine_only_bootstrap"]))
            self.assertEqual(b["matrix_rows"], ["machine-1-8", "machine-2-1", "machine-1-4"])
        with self.assertRaises(r0data.ProtocolViolation):
            runner.aggregate()
        sanity = {"detectors": {runner.run_name(*u): {"ap": 0.3, "auroc": 0.7, "recall_at_threshold": 0.4,
                                                       "fpr_at_threshold": 0.05, "window_prevalence": 0.08,
                                                       "detector_weak_flag": False} for u in runner.planned_runs()},
                  "near_constant_channel_note": {m: {"zero_std_channels": [7], "smallest_std_channel": 17, "smallest_std": 1e-5}
                                                 for m in r0data.MACHINES}}
        runner.SANITY_JSON.write_text(json.dumps(sanity))
        text = runner.report()
        for u in runner.planned_runs():
            self.assertIn(runner.run_name(*u), text)
        self.assertIn("not calibrated population 95% CIs", text)


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
