"""Recompute the A+ review's uncertainty numbers from committed artifacts only.

Review-scoped and read-only.  This script fits nothing, touches no cache, and
writes no result file: it consumes the committed 10x3 source-by-seed matrices in
``research/temporally_matched_observable_control/results.json`` and prints the
numbers quoted in ``independent_review.md``.

    python3 research/temporally_matched_observable_control/independent_review_recompute.py

The only substantive difference from the sealed ``_bootstrap()`` is the
resampling scheme: the sealed version draws seed indices independently inside
every sampled source slot (a nested design), whereas the same three detector
seeds are shared by all ten test sources (a crossed design).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

RESULTS = Path(__file__).resolve().parent / "results.json"
DRAWS, SEED = 10_000, 901


def nested(values: np.ndarray, draws: int = DRAWS, seed: int = SEED) -> np.ndarray:
    """The sealed scheme: seeds resampled independently within each source slot."""
    rng = np.random.default_rng(seed)
    source = rng.integers(0, values.shape[0], size=(draws, values.shape[0]))
    within = rng.integers(0, values.shape[1], size=(draws, values.shape[0], values.shape[1]))
    return values[source[:, :, None], within].mean(axis=(1, 2))


def crossed(values: np.ndarray, draws: int = DRAWS, seed: int = SEED) -> np.ndarray:
    """Two-way cluster bootstrap: resample source rows and seed columns once each."""
    rng = np.random.default_rng(seed)
    source = rng.integers(0, values.shape[0], size=(draws, values.shape[0]))
    column = rng.integers(0, values.shape[1], size=(draws, values.shape[1]))
    return values[source[:, :, None], column[:, None, :]].mean(axis=(1, 2))


def seeds_fixed(values: np.ndarray, draws: int = DRAWS, seed: int = SEED) -> np.ndarray:
    """Sources resampled, the three detector seeds treated as exhaustive."""
    rng = np.random.default_rng(seed)
    return values[rng.integers(0, values.shape[0], size=(draws, values.shape[0]))].mean(axis=(1, 2))


def components(values: np.ndarray) -> tuple[float, float, float]:
    """Source main effect, seed main effect, interaction rms (two-way, no replication)."""
    grand = values.mean()
    source = values.mean(1) - grand
    column = values.mean(0) - grand
    interaction = values - grand - source[:, None] - column[None, :]
    return float(source.std()), float(column.std()), float(np.sqrt((interaction ** 2).mean()))


def main() -> int:
    aggregate = json.loads(RESULTS.read_text())
    for architecture, block in aggregate["architectures"].items():
        matrix = np.asarray(block["source_seed_matrix"], dtype=np.float64)
        pooled = [block["per_seed"][key] for key in sorted(block["per_seed"], key=int)]
        published = aggregate["bootstrap"][architecture]["ci95"]
        src_sd, seed_sd, inter = components(matrix)
        n_src, n_seed = matrix.shape
        print(f"=== {architecture} ===")
        print(f"  source-level mean      {matrix.mean():+.6f}   (published mean {block['mean']:+.6f})")
        print(f"  mean of pooled seeds   {np.mean(pooled):+.6f}   gap {np.mean(pooled) - matrix.mean():+.6f}")
        print(f"  positive units {int((matrix > 0).sum())}/{matrix.size}   units >= 0.02 {int((matrix >= 0.02).sum())}/{matrix.size}")
        print(f"  published (nested)     [{published[0]:+.6f}, {published[1]:+.6f}]  width {published[1] - published[0]:.6f}")
        for label, draw in (("crossed source x seed", crossed), ("sources only, seeds fixed", seeds_fixed),
                            ("nested, reimplemented", nested)):
            means = draw(matrix)
            lo, hi = np.quantile(means, [0.025, 0.975])
            print(f"  {label:<22} [{lo:+.6f}, {hi:+.6f}]  width {hi - lo:.6f}  sd {means.std():.6f}")
        print(f"  variance components: source sd {src_sd:.6f}  seed sd {seed_sd:.6f}  interaction rms {inter:.6f}")
        print(f"  analytic sd  crossed {np.sqrt(src_sd**2/n_src + seed_sd**2/n_seed + inter**2/matrix.size):.6f}"
              f"   nested {np.sqrt(src_sd**2/n_src + (seed_sd**2 + inter**2)/matrix.size):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
