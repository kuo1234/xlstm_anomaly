"""Small isolated sLSTM CUDA build/forward/backward fixture.

This is an engineering diagnostic only. It does not import or mutate any
scientific checkpoint/configuration. The package sources remain untouched; the
fixture replaces only the package's JIT loader in-process so compiler variants
can be compared in separate extension caches.
"""
from __future__ import annotations

import argparse
import os
import traceback
from pathlib import Path

import torch
from torch.utils.cpp_extension import load as cpp_load

import xlstm.blocks.slstm.cell as cell_mod
from xlstm.blocks.slstm.cell import sLSTMCell, sLSTMCellConfig


ROOT = Path(__file__).resolve().parents[2]
PY_HEADERS = Path(
    os.environ.get(
        "XLSTM_PY_HEADERS_ROOT",
        str(ROOT / "data" / "phase_e" / "python_headers" / "usr" / "include"),
    )
)


def _sources() -> list[str]:
    curdir = Path(cell_mod.curdir)
    return [
        str(curdir / "src" / "cuda" / "slstm.cc"),
        str(curdir / "src" / "cuda" / "slstm_forward.cu"),
        str(curdir / "src" / "cuda" / "slstm_backward.cu"),
        str(curdir / "src" / "cuda" / "slstm_backward_cut.cu"),
        str(curdir / "src" / "cuda" / "slstm_pointwise.cu"),
        str(curdir / "src" / "util" / "blas.cu"),
        str(curdir / "src" / "util" / "cuda_error.cu"),
    ]


def install_loader(
    *, arch: str, code: str, static_stub: str | None, rdc: bool, extension_dir: Path
) -> None:
    extension_dir.mkdir(parents=True, exist_ok=True)
    include_flags = ["-isystem", str(PY_HEADERS / "python3.12"), "-isystem", str(PY_HEADERS)]

    def load_variant(*, name, sources, extra_cflags=(), extra_cuda_cflags=(), **kwargs):
        cuda_flags = [
            '-Xptxas="-v"',
            "-gencode",
            f"arch=compute_{arch},code={code}",
            "-res-usage",
            "--use_fast_math",
            "-O3",
            "-Xptxas -O3",
            "--extra-device-vectorization",
            *extra_cuda_cflags,
            *include_flags,
        ]
        if static_stub is not None:
            cuda_flags.append(f"--static-global-template-stub={static_stub}")
        if rdc:
            cuda_flags.append("-rdc=true")
        cflags = [*extra_cflags, *include_flags]
        print(
            "loader_variant",
            {"arch": arch, "code": code, "static_global_template_stub": static_stub,
             "extension_dir": str(extension_dir), "sources": sources},
            flush=True,
        )
        return cpp_load(
            name=name,
            sources=sources,
            verbose=True,
            with_cuda=True,
            extra_cflags=cflags,
            extra_cuda_cflags=cuda_flags,
            extra_ldflags=["-L/usr/local/cuda/lib", "-lcublas"],
            build_directory=str(extension_dir),
            **kwargs,
        )

    cell_mod.load = load_variant
    cell_mod.sLSTMCellCUDA.mod.clear()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arch", default="80")
    parser.add_argument("--code", default="compute_80")
    parser.add_argument("--static-stub", choices=("true", "false"), default=None)
    parser.add_argument("--rdc", action="store_true")
    parser.add_argument("--extension-dir", type=Path, required=True)
    args = parser.parse_args()

    os.environ.setdefault("MAX_JOBS", "1")
    os.environ.setdefault("XLSTM_EXTRA_INCLUDE_PATHS", str(PY_HEADERS / "python3.12") + ":" + str(PY_HEADERS))
    torch.manual_seed(710)
    torch.cuda.manual_seed_all(710)
    print("fixture", {"torch": torch.__version__, "cuda": torch.version.cuda,
                       "device": torch.cuda.get_device_name(0),
                       "capability": torch.cuda.get_device_capability(0)}, flush=True)
    install_loader(
        arch=args.arch,
        code=args.code,
        static_stub=args.static_stub,
        rdc=args.rdc,
        extension_dir=args.extension_dir,
    )
    config = sLSTMCellConfig(
        hidden_size=40,
        num_heads=4,
        backend="cuda",
        dtype="float32",
        dtype_b="float32",
        dtype_r="float32",
        dtype_w="float32",
        dtype_s="float32",
        dtype_a="float32",
        enable_automatic_mixed_precision=False,
        batch_size=2,
        input_shape="BSGNH",
        output_shape="BSH",
    )
    try:
        cell = sLSTMCell(config).cuda().train()
        x = torch.randn(2, 64, 160, device="cuda", dtype=torch.float32, requires_grad=True)
        y, state = cell(x)
        loss = y.square().mean()
        loss.backward()
        torch.cuda.synchronize()
        print(
            "fixture_pass",
            {"output_shape": tuple(y.shape), "state_shape": tuple(state.shape),
             "loss": float(loss.detach()), "finite_output": bool(torch.isfinite(y).all()),
             "finite_grad": bool(torch.isfinite(x.grad).all())},
            flush=True,
        )
        return 0
    except Exception as exc:
        print("fixture_fail", type(exc).__name__, str(exc), flush=True)
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
