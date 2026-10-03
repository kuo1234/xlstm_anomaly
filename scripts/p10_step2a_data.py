"""Step 2a data access (issue #15 comment 5969872677).  Follows the repo label-access pattern of
scripts/real_data_r0_data.py:

* observations (train / test) are loaded by functions that never accept or open a label file;
* test labels are reachable only through ``load_test_labels``, which requires an allow-listed purpose AND a sealed
  score manifest (``seal.json``) whose SHA-256 matches the recorded value, and appends every access to a log;
* label files are downloaded only inside ``load_test_labels`` (i.e. after the seal), never at acquisition time.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import urllib.request
from pathlib import Path

import numpy as np

MACHINES = ("machine-3-7", "machine-1-6", "machine-2-7")
URL = "https://raw.githubusercontent.com/NetManAIOps/OmniAnomaly/master/ServerMachineDataset/{split}/{machine}.txt"
LABEL_PURPOSES = frozenset({"step2a_final_evaluation"})
_LOG: list[dict] = []


class ProtocolViolation(RuntimeError):
    pass


def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _utc():
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_observations(machine: str, split: str, root) -> np.ndarray:
    if machine not in MACHINES or split not in ("train", "test"):
        raise ProtocolViolation(f"not allow-listed: {machine}/{split}")
    p = Path(root) / f"{machine}_{split}.txt"
    if "label" in p.name:
        raise ProtocolViolation("observation loader refuses label files")
    x = np.loadtxt(p, delimiter=",", dtype=np.float64)
    if x.ndim != 2 or not np.isfinite(x).all():
        raise ProtocolViolation(f"corrupt observations {p.name}")
    return x


def load_test_labels(machine: str, *, purpose: str, seal_path, label_root, expected_seal_sha: str) -> np.ndarray:
    if purpose not in LABEL_PURPOSES:
        raise ProtocolViolation(f"label purpose {purpose!r} not allow-listed")
    seal_path = Path(seal_path)
    if not seal_path.exists() or sha256(seal_path) != expected_seal_sha:
        raise ProtocolViolation("score seal missing or SHA mismatch: labels stay closed")
    seal = json.loads(seal_path.read_text())
    for rel, h in seal["files"].items():
        if sha256(seal_path.parent / rel) != h:
            raise ProtocolViolation(f"sealed trace {rel} changed after the seal")
    if machine not in seal["machines"]:
        raise ProtocolViolation(f"{machine} not in the sealed run")
    p = Path(label_root) / f"{machine}_test_label.txt"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL.format(split="test_label", machine=machine), p)
    y = np.loadtxt(p, dtype=np.float64, ndmin=1)
    if not np.isin(y, (0.0, 1.0)).all():
        raise ProtocolViolation("labels not binary")
    _LOG.append(dict(machine=machine, purpose=purpose, utc=_utc(), label_sha256=sha256(p),
                     seal_sha256=expected_seal_sha))
    return y.astype(np.uint8)


def label_access_log():
    return list(_LOG)
