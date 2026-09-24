"""NON_GATING_ENGINEERING_DIAGNOSTIC for R0-v1.2 (random initialisation only; never an acceptance criterion).

Documents that the auditable LSTM implements the same mathematical architecture as the native matched LSTM:
(i) whether seeded initial parameters coincide, (ii) the output difference on the N(0,1) canary after copying
identical parameters.  No checkpoint, label, test observation or R0 metric is used.  This file is outside the
scientific path and is the only R0-v1.2 code that constructs ``torch.nn.LSTM``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import real_data_r0_lstm_v1_2 as auditable  # noqa: E402
import real_data_r0_models as models  # noqa: E402


def main(out: Path) -> dict:
    models.configure()
    manual = auditable.build(11, device="cpu")
    native = models.build_lstm(11, device="cpu")
    mapping = {}
    for name in auditable.LAYERS:
        for tensor in ("weight_ih", "weight_hh", "bias_ih", "bias_hh"):
            mapping[f"{name}.{tensor}"] = f"{name}.{tensor}_l0"
    for tensor in ("input_projection.weight", "input_projection.bias", "output_projection.weight", "output_projection.bias"):
        mapping[tensor] = tensor
    ms, ns = manual.state_dict(), native.state_dict()
    init_equal = {k: bool(torch.equal(ms[k], ns[v])) for k, v in mapping.items()}
    with torch.no_grad():
        for k, v in mapping.items():
            ns[v].copy_(ms[k])
    manual, native = manual.cuda().eval(), native.cuda().eval()
    generator = torch.Generator(device="cpu").manual_seed(710)
    x = torch.randn(128, 64, 38, generator=generator).cuda()
    with torch.no_grad():
        a = manual(x)
        b = native(x)
    result = {"label": "NON_GATING_ENGINEERING_DIAGNOSTIC", "seed": 11, "input": "N(0,1) canary [128,64,38], seed 710",
              "initial_parameters_identical": init_equal, "all_initial_parameters_identical": all(init_equal.values()),
              "output_max_abs_difference": float((a - b).abs().max()), "output_max_abs": float(a.abs().max()),
              "use": "documents mathematical equivalence only; not an acceptance criterion; no tuning"}
    out.write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    print(json.dumps({k: v for k, v in main(Path(sys.argv[1])).items() if k != "initial_parameters_identical"}))
