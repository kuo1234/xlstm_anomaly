"""Segment-composition checks for the Step 1b boundary pilot."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from p10_step1b_boundary import CFG1B, composition, segments  # noqa: E402


def test_composition_table():
    c = lambda o, L: tuple(composition(o, L, 30, 8).values())
    assert c(-16, 38) == (16, 22, 0)
    assert c(0, 38) == (0, 30, 8)
    assert c(30, 38) == (30, 0, 8)
    assert c(0, 16) == (0, 16, 0)
    assert c(0, 62) == (24, 30, 8)
    assert c(8, 38) == (8, 22, 8)


def test_segments_fit_before_eval_window():
    ends = [o + L for _, o, L in segments(CFG1B)]
    assert max(ends) + 16 <= CFG1B["eval_start"]
    assert min(CFG1B["deltas"]) + CFG1B["a_len"] >= CFG1B["eval_start"] - 0   # A2 starts after segment + guard
