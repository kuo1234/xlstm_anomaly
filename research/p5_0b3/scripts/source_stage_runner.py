"""Auditor-side staged launcher for the sealed P5-0B3 SOURCE procedure.

This process handles structural inputs and the private firewall audit. The
method subprocess receives only a SOURCE projection and canonical SOURCE
labels. Running requires an explicit commit seal and a clean committed tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

EXPECTED_PROTOCOL_STATUS = "P5_0B2R2_PROTOCOL_RESEALED"
PINNED_ROLE_SEAL_SHA256 = "00e0cec62d238c78f2d0b3c79910c0ffaf1122d1582c28c8848022fb3e10e33f"
ARCHIVE_PATH = Path("/tmp/predist_dataset-v2-19496480.zip")
ARCHIVE_SIZE = 266_814_500
RUNTIME_LOCK_SHA256 = "5cc46d5a1b2dc63dd4ec1f879babd337a97481f1af8595603ea9ed97ecfad9a5"
PROPAGATED_TERMINAL_TOKENS = frozenset({
    "P5_0B3_FIREWALL_BLOCKED",
    "P5_0B3_BACKBONE_NOT_ADMISSIBLE",
})


class StageFailure(RuntimeError):
    pass


def _fail():
    raise StageFailure("P5_0B3_STAGE_BLOCKED") from None


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_preflight_is_pinned(record: dict) -> bool:
    return (
        record.get("status") == "PASS"
        and record.get("code", {}).get("runtime_lock_sha256") == RUNTIME_LOCK_SHA256
        and record.get("code", {}).get("efd_commit") == "ced470e1386066931bad32f3cb6e24bac9c5bb89"
        and record.get("code", {}).get("python") == "3.12.3"
        and record.get("runtime", {}).get("tensorflow") == "2.18.1"
        and record.get("runtime", {}).get("keras") == "3.15.1"
        and record.get("runtime", {}).get("numpy") == "1.26.4"
        and record.get("runtime", {}).get("device") == "CPU"
        and record.get("runtime", {}).get("deterministic_ops") is True
        and record.get("runtime", {}).get("intra_threads") == 1
        and record.get("runtime", {}).get("inter_threads") == 1
    )


def verify_implementation_seal(root: Path) -> None:
    """Require a committed seal covering every method/test Python file."""
    try:
        path = root / "research/p5_0b3/implementation_seal.json"
        seal = json.loads(path.read_text(encoding="utf-8"))
        if (seal.get("status") != "P5_0B3_PREACCESS_CODE_SEALED"
                or seal.get("runtime_preflight_result_sha256") !=
                "e5ea82ab60d69e1578d4cef835e815c83e1d0fdb63eaa17a645557cbac9cb939"
                or seal.get("runtime_lock_sha256") != RUNTIME_LOCK_SHA256):
            _fail()
        entries = seal.get("sealed_files")
        if not isinstance(entries, list) or not entries:
            _fail()
        expected = {
            item.relative_to(root).as_posix()
            for base in (root / "research/p5_0b3/scripts", root / "research/p5_0b3/tests")
            for item in base.rglob("*.py") if item.is_file()
        }
        seen = set()
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
                _fail()
            relative = entry["path"]
            digest = entry["sha256"]
            if (not isinstance(relative, str) or relative not in expected
                    or relative in seen or not isinstance(digest, str)
                    or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest)):
                _fail()
            seen.add(relative)
            file_path = root / relative
            allowed_roots = ((root / "research/p5_0b3/scripts").resolve(),
                             (root / "research/p5_0b3/tests").resolve())
            resolved = file_path.resolve(strict=True)
            if (file_path.is_symlink()
                    or not any(resolved.is_relative_to(base) for base in allowed_roots)
                    or _sha(file_path) != digest):
                _fail()
        if seen != expected:
            _fail()
    except StageFailure:
        raise
    except Exception:
        _fail()


def _run_synthetic_runtime_preflight(root: Path, efd_source: Path,
                                    pinned_record: dict, stderr_path: Path) -> None:
    """Run the synthetic deterministic fit with this exact child interpreter."""
    try:
        env = os.environ.copy()
        env.update({"PYTHONHASHSEED": "17", "CUDA_VISIBLE_DEVICES": "-1",
                    "TF_DETERMINISTIC_OPS": "1", "TF_NUM_INTRAOP_THREADS": "1",
                    "TF_NUM_INTEROP_THREADS": "1", "PYTHONDONTWRITEBYTECODE": "1",
                    "P5_EFD_SOURCE": str(efd_source.resolve()),
                    "PYTHONPATH": str(root.resolve()) + os.pathsep + os.environ.get("PYTHONPATH", "")})
        result = subprocess.run(
            [sys.executable, "-m", "research.p5_0b3.scripts.runtime_preflight"],
            cwd=root, env=env, check=False, capture_output=True, text=True,
        )
        stderr_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        stderr_path.write_text(result.stderr, encoding="utf-8")
        os.chmod(stderr_path, 0o600)
        if result.returncode != 0 or len(result.stdout.splitlines()) != 1:
            _fail()
        current = json.loads(result.stdout)
        if (current.get("status") != "PASS"
                or current.get("code") != pinned_record.get("code")
                or current.get("runtime") != pinned_record.get("runtime")
                or current.get("result") != pinned_record.get("result")):
            _fail()
    except StageFailure:
        raise
    except Exception:
        _fail()


def preflight(root: Path, sealed_commit: str, archive: Path, efd_source: Path,
              *, runtime_stderr_path: Path):
    """Verify committed-code/protocol/runtime identity without opening data."""
    try:
        head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
                              capture_output=True, text=True).stdout.strip()
        status = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
                                check=True, capture_output=True, text=True).stdout
        if not sealed_commit or head != sealed_commit or status.strip():
            _fail()
        verify_implementation_seal(root)
        seal_path = root / "research/p5_0b2/protocol_seal.json"
        seal = json.loads(seal_path.read_text(encoding="utf-8"))
        if (seal.get("status") != EXPECTED_PROTOCOL_STATUS
                or seal.get("role_seal_sha256") != PINNED_ROLE_SEAL_SHA256
                or seal.get("target_access", {}).get("target_label_access") != "NOT_AUTHORIZED"):
            _fail()
        if archive.resolve() != ARCHIVE_PATH.resolve() or archive.stat().st_size != ARCHIVE_SIZE:
            _fail()
        runtime = root / "research/p5_0b3/runtime_preflight_result.json"
        runtime_lock = root / "research/p5_0b3/runtime.lock"
        record_bytes = runtime.read_bytes()
        lock_bytes = runtime_lock.read_bytes()
        record = json.loads(record_bytes)
        implementation_seal = json.loads(
            (root / "research/p5_0b3/implementation_seal.json").read_text(encoding="utf-8")
        )
        if (not runtime_preflight_is_pinned(record)
                or hashlib.sha256(record_bytes).hexdigest() != implementation_seal.get("runtime_preflight_result_sha256")
                or hashlib.sha256(lock_bytes).hexdigest() != implementation_seal.get("runtime_lock_sha256")):
            _fail()
        _run_synthetic_runtime_preflight(root, efd_source, record, runtime_stderr_path)
        efd_head = subprocess.run(["git", "-C", str(efd_source), "rev-parse", "HEAD"], check=True,
                                  capture_output=True, text=True).stdout.strip()
        if efd_head != "ced470e1386066931bad32f3cb6e24bac9c5bb89":
            _fail()
    except StageFailure:
        raise
    except Exception:
        _fail()


def _run(command: list[str], env: dict[str, str], expected_prefix: str,
         *, cwd: Path, private_stderr_path: Path) -> str:
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True,
                                 env=env, cwd=cwd)
        private_stderr_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        private_stderr_path.write_text(result.stderr, encoding="utf-8")
        os.chmod(private_stderr_path, 0o600)
        lines = result.stdout.splitlines()
        if result.returncode != 0 and len(lines) == 1 and lines[0] in PROPAGATED_TERMINAL_TOKENS:
            raise StageFailure(lines[0])
        if result.returncode != 0 or len(lines) != 1 or not lines[0].startswith(expected_prefix):
            _fail()
        return lines[0]
    except StageFailure:
        raise
    except Exception:
        _fail()


def run_stage(root: Path, *, sealed_commit: str, archive: Path, efd_source: Path,
              output_root: Path, private_audit_root: Path) -> None:
    """Run firewall then method subprocesses with non-overlapping outputs."""
    root = root.resolve()
    output_root = output_root.resolve()
    private_audit_root = private_audit_root.resolve()
    if (output_root == private_audit_root or output_root in private_audit_root.parents
            or private_audit_root in output_root.parents or output_root.exists()
            or private_audit_root.exists()):
        _fail()
    if any(path == root or root in path.parents or path in root.parents
           for path in (output_root, private_audit_root)):
        _fail()
    preflight(root, sealed_commit, archive, efd_source,
              runtime_stderr_path=private_audit_root / "runtime_preflight.stderr")
    output_root.mkdir(parents=True, mode=0o700)
    # The preflight stores its stderr inside the private root, creating the
    # directory before this point. Reaffirm its restricted permissions after
    # that write instead of trying to create it a second time.
    private_audit_root.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(private_audit_root, 0o700)
    projection_path = output_root / "source_projection.json"
    firewall_restricted = private_audit_root / "firewall"
    method_labels = output_root / "method_labels"
    env = os.environ.copy()
    env.update({"PYTHONHASHSEED": "17", "CUDA_VISIBLE_DEVICES": "-1",
                "TF_DETERMINISTIC_OPS": "1", "TF_NUM_INTRAOP_THREADS": "1",
                "TF_NUM_INTEROP_THREADS": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    env["PYTHONPATH"] = str(root.resolve()) + os.pathsep + env.get("PYTHONPATH", "")
    role_seal = root / "research/p5_0b1r/role_split_seal.json"
    if _sha(role_seal) != PINNED_ROLE_SEAL_SHA256:
        _fail()
    projection_line = _run([sys.executable, "-m", "research.p5_0b3.scripts.source_projection",
                            "--output", str(projection_path)], env,
                           "P5_0B3_SOURCE_PROJECTION_OK ", cwd=root,
                           private_stderr_path=private_audit_root / "source_projection.stderr")
    projection_sha = _sha(projection_path)
    if projection_line.split()[-1] != projection_sha:
        _fail()
    firewall_line = _run([sys.executable, "-m", "research.p5_0b3.scripts.firewall_process",
                          "--archive", str(archive), "--role-seal", str(role_seal),
                          "--restricted-output", str(firewall_restricted),
                          "--method-output", str(method_labels)], env, "P5_0B3_FIREWALL_OK ",
                         cwd=root, private_stderr_path=private_audit_root / "firewall.stderr")
    label_path = method_labels / "source_labels.jsonl"
    checksum_path = method_labels / "source_labels.sha256"
    label_sha = _sha(label_path)
    if checksum_path.read_text(encoding="ascii") != label_sha + "\n" or firewall_line.split()[-1] != label_sha:
        _fail()
    method_out = output_root / "method_output"
    # The method receives no restricted audit path or full structural table.
    _run([sys.executable, "-m", "research.p5_0b3.scripts.source_method_process",
          "--projection", str(projection_path), "--projection-sha256", projection_sha,
         "--archive", str(archive), "--labels", str(label_path), "--labels-sha256", label_sha,
          "--output", str(method_out), "--efd-source", str(efd_source)],
         env, "P5_0B3_METHOD_OK ", cwd=root,
         private_stderr_path=private_audit_root / "method.stderr")


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--root", required=True)
    parser.add_argument("--sealed-commit", required=True)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--efd-source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--private-audit", required=True)
    try:
        args = parser.parse_args(argv)
        run_stage(Path(args.root), sealed_commit=args.sealed_commit,
                  archive=Path(args.archive), efd_source=Path(args.efd_source),
                  output_root=Path(args.output), private_audit_root=Path(args.private_audit))
        print("P5_0B3_STAGE_OK")
        return 0
    except StageFailure as exc:
        if str(exc) in PROPAGATED_TERMINAL_TOKENS:
            print(str(exc))
        else:
            print("P5_0B3_STAGE_BLOCKED")
        return 2
    except Exception:
        print("P5_0B3_STAGE_BLOCKED")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
