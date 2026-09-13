"""Fail-fast launcher for the eight fresh F-v4 runs.

The two eligible LSTM runs are represented by a sealed reference-only
manifest; their F3 checkpoint files are never copied into the F4 namespace.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs/phase_f_v4.json"
REPORT = ROOT / "reports/phase_f_v4"
PYTHON = ROOT / "data/phase_e2/venv/bin/python"


def _sha(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_carry_forward(cfg: dict) -> dict:
    rows = []
    for entry in cfg["carry_forward"]:
        source = ROOT / entry["source"]
        manifest_path = ROOT / entry["manifest"]
        parity_path = ROOT / entry["post_parity"]
        if not source.is_file() or not manifest_path.is_file() or not parity_path.is_file():
            raise SystemExit(f"Missing sealed carry-forward artifact: {entry['run']}")
        manifest = json.loads(manifest_path.read_text())
        parity = json.loads(parity_path.read_text())
        if manifest.get("status") != "PASS" or parity.get("status") != "PASS":
            raise SystemExit(f"Carry-forward source is not PASS: {entry['run']}")
        if manifest.get("epochs") != cfg["epochs"] or manifest.get("architecture") != "lstm":
            raise SystemExit(f"Carry-forward metadata mismatch: {entry['run']}")
        rows.append({
            "run": entry["run"],
            "architecture": "lstm",
            "seed": int(entry["run"].rsplit("_", 1)[1]),
            "status": "CARRIED_FORWARD",
            "source_phase": "phase_f_v3",
            "source_checkpoint": entry["source"],
            "source_checkpoint_sha256": _sha(source),
            "source_manifest": entry["manifest"],
            "source_manifest_sha256": _sha(manifest_path),
            "source_post_training_parity": entry["post_parity"],
            "source_post_training_parity_sha256": _sha(parity_path),
            "best_model_hash": manifest.get("best_model_hash"),
            "selected_epoch": manifest.get("selected_epoch"),
            "epochs": manifest.get("epochs"),
            "checkpoint_copied": False,
            "retrained": False,
            "labels_used": False,
            "test_sources_used": False,
            "probe_fitting": False,
        })
    return {"status": "REFERENCE_ONLY", "policy": cfg["carry_forward_policy"], "runs": rows}


def _terminate(active):
    for item in active:
        process = item["process"]
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass


def main() -> None:
    cfg = json.loads(CONFIG_PATH.read_text())
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / "logs").mkdir(exist_ok=True)
    carry = _verify_carry_forward(cfg)
    (REPORT / "carry_forward_manifest.json").write_text(json.dumps(carry, indent=2) + "\n")

    queue = list(cfg["fresh_runs"])
    active = []
    completed = []
    started = time.time()
    max_concurrent = int(cfg["max_concurrent_processes"])
    try:
        while queue or active:
            while queue and len(active) < max_concurrent:
                run_name = queue.pop(0)
                architecture, seed_text = run_name.rsplit("_", 1)
                seed = int(seed_text)
                log_path = REPORT / "logs" / f"{run_name}.log"
                if log_path.exists():
                    raise SystemExit(f"Refusing to reuse existing log: {log_path}")
                log = log_path.open("x")
                command = [str(PYTHON), "-u", str(ROOT / "scripts/phase_f_v4_train.py"), architecture, str(seed)]
                process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                active.append({"run": run_name, "process": process, "log": log, "command": command, "started": time.time()})
                print("START", run_name, process.pid, flush=True)

            for item in active[:]:
                process = item["process"]
                if process.poll() is None:
                    continue
                item["log"].close()
                active.remove(item)
                row = {"run": item["run"], "command": item["command"], "exit_code": process.returncode, "seconds": time.time() - item["started"]}
                completed.append(row)
                (REPORT / "execution.json").write_text(json.dumps({"status": "RUNNING", "completed": completed, "remaining": queue, "active": [v["run"] for v in active], "wall_seconds": time.time() - started}, indent=2) + "\n")
                print("END", item["run"], process.returncode, flush=True)
                if process.returncode:
                    raise SystemExit(f"F-v4 STOP: failed fresh run {item['run']}")
            time.sleep(2)
    except BaseException:
        _terminate(active)
        for item in active:
            item["log"].close()
        raise

    if len(completed) != len(cfg["fresh_runs"]):
        raise SystemExit("F-v4 incomplete fresh-run queue")
    (REPORT / "execution.json").write_text(json.dumps({"status": "PASS", "completed": completed, "remaining": [], "active": [], "wall_seconds": time.time() - started}, indent=2) + "\n")


if __name__ == "__main__":
    main()
