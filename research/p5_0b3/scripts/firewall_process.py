"""Small CLI to run the pinned SOURCE label firewall in its own process."""

from __future__ import annotations

import hashlib
from pathlib import Path
import sys

from research.p5_0b3.scripts.firewall_runner import run_firewall_from_zip


PINNED_ROLE_SEAL_SHA256 = "00e0cec62d238c78f2d0b3c79910c0ffaf1122d1582c28c8848022fb3e10e33f"
PINNED_ARCHIVE_BYTES = 266_814_500
PINNED_ARCHIVE_PATH = Path("/tmp/predist_dataset-v2-19496480.zip")


def _verify_firewall_pin() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    protocol = repository_root / "research/p5_0b2/protocol_seal.json"
    import json

    seal = json.loads(protocol.read_text(encoding="utf-8"))
    if seal.get("status") != "P5_0B2R2_PROTOCOL_RESEALED":
        raise RuntimeError
    expected = seal.get("source_development", {}).get("source_label_firewall_sha256")
    code_path = repository_root / "research/p5_0b2/scripts/source_label_firewall.py"
    if not expected or hashlib.sha256(code_path.read_bytes()).hexdigest() != expected:
        raise RuntimeError


def _arguments(argv: list[str]) -> dict[str, str]:
    allowed = {"--archive", "--role-seal", "--restricted-output", "--method-output"}
    if len(argv) != 8 or len(argv) % 2:
        raise RuntimeError
    values = dict(zip(argv[::2], argv[1::2]))
    if len(values) != 4 or set(values) != allowed or any(not value for value in values.values()):
        raise RuntimeError
    return values


def main(argv: list[str] | None = None) -> int:
    try:
        args = _arguments(list(sys.argv[1:] if argv is None else argv))
        _verify_firewall_pin()
        archive_path = Path(args["--archive"]).resolve()
        if (archive_path != PINNED_ARCHIVE_PATH.resolve() or
                archive_path.stat().st_size != PINNED_ARCHIVE_BYTES):
            raise RuntimeError
        role_bytes = Path(args["--role-seal"]).read_bytes()
        if hashlib.sha256(role_bytes).hexdigest() != PINNED_ROLE_SEAL_SHA256:
            raise RuntimeError
        result = run_firewall_from_zip(
            archive_path, role_bytes,
            args["--restricted-output"], args["--method-output"]
        )
        source_hash = result["source_artifact_sha256"]
        if len(source_hash) != 64:
            raise RuntimeError
        print(f"P5_0B3_FIREWALL_OK {source_hash}")
        return 0
    except Exception:
        # Firewall protocol requires exception details and input paths redacted.
        print("P5_0B3_FIREWALL_BLOCKED")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
