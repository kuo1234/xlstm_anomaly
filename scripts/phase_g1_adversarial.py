"""Run the bounded Phase-G1 adversarial tests without requiring pytest."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "tests" / "test_phase_g1.py"
sys.path.insert(0, str(ROOT / "scripts"))


def run() -> dict:
    spec = importlib.util.spec_from_file_location("phase_g1_test_module", TEST)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Phase-G1 test module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    names = sorted(name for name in dir(module) if name.startswith("test_"))
    results = []
    for name in names:
        function = getattr(module, name)
        try:
            function()
        except Exception as exc:  # fail closed and retain exact fixture name
            results.append({"name": name, "status": "FAIL", "error": repr(exc)})
        else:
            results.append({"name": name, "status": "PASS"})
    failed = [row for row in results if row["status"] != "PASS"]
    return {
        "status": "PASS" if not failed else "STOP",
        "test_count": len(results),
        "results": results,
        "failed": failed,
        "real_phase_g_labels_read": False,
        "ap_or_auroc_computed": False,
        "probe_fitted": False,
        "optimizer_steps": False,
    }


def main() -> None:
    result = run()
    path = ROOT / "reports" / "phase_g1" / "adversarial_tests.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "test_count": result["test_count"], "failed": result["failed"]}, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
