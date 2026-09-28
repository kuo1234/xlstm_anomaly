"""Restricted ZIP adapter and process boundary for the sealed B2 label firewall.

This module accepts only the six pinned label members. It never extracts an
archive and publishes only the canonical SOURCE artifact and its checksum to
the method-facing directory. The full audit remains in a separate restricted
directory owned by the privileged caller.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import zipfile
from pathlib import Path
from typing import BinaryIO, Mapping

from research.p5_0b2.scripts import source_label_firewall as firewall


ALLOWED_MEMBERS = frozenset(
    f"{manufacturer}/{table}.csv"
    for manufacturer in firewall.MANUFACTURERS
    for table in firewall.TABLES
)


def _fail(category: str = "RESTRICTED_ARTIFACT_PUBLICATION") -> None:
    raise firewall.FirewallError(category) from None


def read_allowed_zip_members(archive: str | Path | BinaryIO) -> dict[str, bytes]:
    """Read exactly the allowlisted members without extracting any ZIP entry."""
    try:
        with zipfile.ZipFile(archive, "r") as zipped:
            counts = {name: 0 for name in ALLOWED_MEMBERS}
            for info in zipped.infolist():
                if info.filename in counts:
                    counts[info.filename] += 1
            if any(count != 1 for count in counts.values()):
                _fail("ARCHIVE_MEMBER_IO")
            # Exact names only; traversal entries and all other payloads are
            # never opened or written to disk.
            return {name: zipped.read(name) for name in sorted(ALLOWED_MEMBERS)}
    except firewall.FirewallError:
        raise
    except Exception:
        raise firewall.FirewallError("ARCHIVE_MEMBER_IO") from None


def run_firewall_from_members(
    members: Mapping[str, bytes],
    role_seal_bytes: bytes,
    restricted_output_dir: str | Path,
    method_output_dir: str | Path,
) -> dict[str, str]:
    """Run the sealed extractor and expose only canonical SOURCE bytes.

    `restricted_output_dir` is the privileged auditor destination and contains
    the three B2 firewall artifacts. `method_output_dir` contains only
    `source_labels.jsonl` and `source_labels.sha256`. The return value contains
    only the SOURCE artifact digest; in particular it omits the audit digest.
    """
    if set(members) != ALLOWED_MEMBERS:
        raise firewall.FirewallError("ARCHIVE_MEMBER_IO") from None
    if not isinstance(role_seal_bytes, bytes):
        raise firewall.FirewallError("ROLE_SEAL_OR_ROLE_INDEX") from None
    try:
        restricted = Path(restricted_output_dir)
        method = Path(method_output_dir)
        if restricted.resolve() == method.resolve() or restricted.exists() or method.exists():
            _fail()
        restricted.parent.mkdir(parents=True, exist_ok=True)
        method.parent.mkdir(parents=True, exist_ok=True)
    except firewall.FirewallError:
        raise
    except Exception:
        raise firewall.FirewallError("RESTRICTED_ARTIFACT_PUBLICATION") from None
    try:
        with tempfile.TemporaryDirectory(prefix="p5-0b3-firewall-input-") as temp_name:
            temp = Path(temp_name)
            role_path = temp / "role_seal.json"
            try:
                role_path.write_bytes(role_seal_bytes)
            except OSError:
                raise firewall.FirewallError("ROLE_SEAL_OR_ROLE_INDEX") from None
            label_paths: dict[tuple[str, str], Path] = {}
            for member in sorted(ALLOWED_MEMBERS):
                manufacturer, filename = member.split("/", 1)
                table = filename.removesuffix(".csv")
                path = temp / manufacturer / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(members[member])
                label_paths[(manufacturer, table)] = path
            result = firewall.execute_firewall(label_paths, role_path, restricted)
    except firewall.FirewallError:
        raise
    except OSError:
        raise firewall.FirewallError("ARCHIVE_MEMBER_IO") from None
    except Exception:
        raise firewall.FirewallError("UNCLASSIFIED") from None

    try:
        source_path = restricted / "source_labels.jsonl"
        digest_path = restricted / "source_labels.sha256"
        if {entry.name for entry in restricted.iterdir()} != {
            "source_labels.jsonl", "source_labels.sha256", "access_audit.json"
        }:
            _fail()
        source_payload = source_path.read_bytes()
        source_digest = hashlib.sha256(source_payload).hexdigest()
        if result.get("source_artifact_sha256") != source_digest:
            _fail("METHOD_ARTIFACT_COPY_OR_DIGEST")
        if digest_path.read_bytes() != (source_digest + "\n").encode("ascii"):
            _fail("METHOD_ARTIFACT_COPY_OR_DIGEST")

        method.mkdir(mode=0o700)
        os.chmod(method, 0o700)
        for name, content in (
            ("source_labels.jsonl", source_payload),
            ("source_labels.sha256", (source_digest + "\n").encode("ascii")),
        ):
            destination = method / name
            with destination.open("xb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        return {"source_artifact_sha256": source_digest}
    except firewall.FirewallError:
        raise
    except OSError:
        if method.exists():
            try:
                for child in method.iterdir():
                    child.unlink(missing_ok=True)
                method.rmdir()
            except OSError:
                pass
        raise firewall.FirewallError("METHOD_ARTIFACT_COPY_OR_DIGEST") from None
    except Exception:
        if method.exists():
            try:
                for child in method.iterdir():
                    child.unlink(missing_ok=True)
                method.rmdir()
            except OSError:
                pass
        raise firewall.FirewallError("UNCLASSIFIED") from None


def run_firewall_from_zip(
    archive: str | Path | BinaryIO,
    role_seal_bytes: bytes,
    restricted_output_dir: str | Path,
    method_output_dir: str | Path,
) -> dict[str, str]:
    """ZIP entry point for the dedicated privileged firewall process."""
    members = read_allowed_zip_members(archive)
    return run_firewall_from_members(
        members, role_seal_bytes, restricted_output_dir, method_output_dir
    )
