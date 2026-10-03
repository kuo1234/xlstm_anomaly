"""Step 2b data access (issue #15 comment 5970197497).  Same label-access pattern as p10_step2a_data:

* observations are loaded by p10_step2a_data.load_observations (never accepts / opens a label file);
* test labels are reachable only through ``load_test_labels`` below, which requires the allow-listed purpose
  ``step2b_dev_evaluation`` AND the Step 2b score seal (SHA-256 of seal.json and of every sealed file), and logs
  every access.

The three machines are a DEVELOPMENT / exploratory set: their labels were exposure-visible before (Step 2a and earlier
audits), so nothing evaluated through this module is confirmatory.
"""
from __future__ import annotations

import datetime as _dt
import json
import urllib.request
from pathlib import Path

import numpy as np

from p10_step2a_data import MACHINES, URL, ProtocolViolation, load_observations, sha256  # noqa: F401

LABEL_PURPOSES = frozenset({"step2b_dev_evaluation"})
_LOG: list[dict] = []


def load_test_labels(machine: str, *, purpose: str, seal_path, label_root, expected_seal_sha: str) -> np.ndarray:
    if purpose not in LABEL_PURPOSES:
        raise ProtocolViolation(f"label purpose {purpose!r} not allow-listed")
    seal_path = Path(seal_path)
    if not seal_path.exists() or sha256(seal_path) != expected_seal_sha:
        raise ProtocolViolation("score seal missing or SHA mismatch: labels stay closed")
    seal = json.loads(seal_path.read_text())
    if seal.get("stage") != "step2b_label_blind_scores" or seal.get("labels_read") != 0:
        raise ProtocolViolation("not a Step 2b label-blind seal")
    for rel, h in seal["files"].items():
        if sha256(seal_path.parent / rel) != h:
            raise ProtocolViolation(f"sealed file {rel} changed after the seal")
    if machine not in seal["machines"]:
        raise ProtocolViolation(f"{machine} not in the sealed run")
    p = Path(label_root) / f"{machine}_test_label.txt"
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL.format(split="test_label", machine=machine), p)
    y = np.loadtxt(p, dtype=np.float64, ndmin=1)
    if not np.isin(y, (0.0, 1.0)).all():
        raise ProtocolViolation("labels not binary")
    _LOG.append(dict(machine=machine, purpose=purpose,
                     utc=_dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                     label_sha256=sha256(p), seal_sha256=expected_seal_sha))
    return y.astype(np.uint8)


def label_access_log():
    return list(_LOG)
