"""Engineering-only xLSTMAD CUDA correctness and throughput benchmark.

The script uses fresh random weights and synthetic observations.  It never
loads Phase-F/G checkpoints or scientific data.  CUDA compilation is isolated
to a caller-provided torch extension directory and the installed xlstm package
is monkey-patched only in this process.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import torch


PROJECT_ROOT = Path(
    os.environ.get("XLSTM_PROJECT_ROOT", "/home/p76141495/home/xlstm_anomaly")
).resolve()
OFFICIAL = PROJECT_ROOT / "data" / "phase_e2" / "official_xlstmad"
sys.path.insert(0, str(PROJECT_ROOT / ".worktrees" / "cuda-spark" / "research" / "cuda_spark"))
sys.path.insert(0, str(OFFICIAL))

from slstm_cuda_fixture import install_loader  # noqa: E402
import xlstmad as native  # noqa: E402


def _float32_config_factory(original):
    def factory(*args, **kwargs):
        config = original(*args, **kwargs)
        for name in ("dtype", "dtype_b", "dtype_r", "dtype_w", "dtype_g", "dtype_s", "dtype_a"):
            setattr(config.slstm_block.slstm, name, "float32")
        return config

    return factory


def build_model(backend: str, seed: int, extension_dir: Path | None = None):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    if backend == "cuda":
        if extension_dir is None:
            raise ValueError("extension_dir is required for CUDA")
        import xlstm.blocks.slstm.cell as cell_mod

        install_loader(
            arch="121",
            code="sm_121",
            static_stub="false",
            rdc=False,
            extension_dir=extension_dir,
        )
        cell_mod.sLSTMCellCUDA.mod.clear()
    original = native.create_config
    native.create_config = _float32_config_factory(original)
    try:
        model = native.xLSTMAD(
            embedding_dim=40,
            features_no=8,
            window_size=64,
            lr=0.001,
            slstm_backend=backend,
        ).float().cuda()
    finally:
        native.create_config = original
    return model


def _max_abs(a: torch.Tensor, b: torch.Tensor) -> tuple[float, float, int]:
    diff = (a.detach().float() - b.detach().float()).abs()
    return float(diff.max()), float(diff.mean()), int((diff > 0).sum())


def _load_vanilla_weights_into_cuda(vanilla, cuda) -> None:
    """Map the public vanilla recurrent layout to CUDA's internal layout.

    The two official backend implementations expose the same equations but
    store the recurrent matrix differently.  Loading the raw state dict would
    therefore compare different tensors; this explicit, deterministic adapter
    preserves the vanilla external matrix before the CUDA backend reshapes it.
    """
    state = {name: value.detach().clone() for name, value in vanilla.state_dict().items()}
    vanilla_modules = dict(vanilla.named_modules())
    cuda_modules = dict(cuda.named_modules())
    for name in list(state):
        if name.endswith(".slstm_cell._recurrent_kernel_"):
            module_name = name[: -len("._recurrent_kernel_")]
            source = vanilla_modules[module_name]
            target = cuda_modules[module_name]
            external = source._recurrent_kernel_int2ext(state[name])
            state[name] = target._recurrent_kernel_ext2int(external)
        elif name.endswith(".slstm_cell._bias_"):
            module_name = name[: -len("._bias_")]
            source = vanilla_modules[module_name]
            target = cuda_modules[module_name]
            external = source._bias_int2ext(state[name])
            state[name] = target._bias_ext2int(external)
    cuda.load_state_dict(state, strict=True)


def compare(extensions: Path) -> dict:
    # Build identical random models through independent backend paths.
    vanilla = build_model("vanilla", seed=710).train()
    cuda = build_model("cuda", seed=711, extension_dir=extensions).train()
    _load_vanilla_weights_into_cuda(vanilla, cuda)
    base = torch.randn(8, 64, 8, device="cuda", dtype=torch.float32)
    xv = base.detach().clone().requires_grad_(True)
    xc = base.detach().clone().requires_grad_(True)
    yv = vanilla(xv)
    yc = cuda(xc)
    lv = (yv - xv).square().mean()
    lc = (yc - xc).square().mean()
    lv.backward()
    lc.backward()
    param_rows = []
    vanilla_modules = dict(vanilla.named_modules())
    cuda_modules = dict(cuda.named_modules())
    for (name_v, p_v), (name_c, p_c) in zip(vanilla.named_parameters(), cuda.named_parameters()):
        if name_v != name_c:
            raise AssertionError(f"parameter ordering mismatch: {name_v} != {name_c}")
        if p_v.grad is None or p_c.grad is None:
            continue
        grad_c = p_c.grad
        if name_v.endswith(".slstm_cell._recurrent_kernel_"):
            module_name = name_v[: -len("._recurrent_kernel_")]
            external = cuda_modules[module_name]._recurrent_kernel_int2ext(grad_c)
            grad_c = vanilla_modules[module_name]._recurrent_kernel_ext2int(external)
        elif name_v.endswith(".slstm_cell._bias_"):
            module_name = name_v[: -len("._bias_")]
            external = cuda_modules[module_name]._bias_int2ext(grad_c)
            grad_c = vanilla_modules[module_name]._bias_ext2int(external)
        ma, me, nz = _max_abs(p_v.grad, grad_c)
        param_rows.append({"name": name_v, "grad_max_abs": ma, "grad_mean_abs": me, "grad_nonzero_diff": nz})
    with torch.no_grad():
        repeat_a = cuda(base)
        repeat_b = cuda(base)
    repeat_max, repeat_mean, repeat_n = _max_abs(repeat_a, repeat_b)
    output_max, output_mean, output_n = _max_abs(yv, yc)
    input_grad_max, input_grad_mean, input_grad_n = _max_abs(xv.grad, xc.grad)
    return {
        "batch": 8,
        "window": 64,
        "output": {"max_abs": output_max, "mean_abs": output_mean, "different_elements": output_n},
        "loss": {"vanilla": float(lv.detach()), "cuda": float(lc.detach()), "abs_diff": abs(float(lv - lc))},
        "input_gradient": {"max_abs": input_grad_max, "mean_abs": input_grad_mean, "different_elements": input_grad_n},
        "parameter_gradient_max_abs": max((r["grad_max_abs"] for r in param_rows), default=0.0),
        "parameter_gradient_rows": param_rows,
        "cuda_repeat": {"max_abs": repeat_max, "mean_abs": repeat_mean, "different_elements": repeat_n},
        "finite": {
            "vanilla_output": bool(torch.isfinite(yv).all()),
            "cuda_output": bool(torch.isfinite(yc).all()),
            "vanilla_grad": bool(torch.isfinite(xv.grad).all()),
            "cuda_grad": bool(torch.isfinite(xc.grad).all()),
        },
    }


def _step_time(model, batch: int, steps: int, warmup: int) -> dict:
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    x = torch.randn(batch, 64, 8, device="cuda", dtype=torch.float32)
    for _ in range(warmup):
        optimizer.zero_grad(set_to_none=True)
        loss = (model(x) - x).square().mean()
        loss.backward()
        optimizer.step()
    torch.cuda.synchronize()
    start_evt = torch.cuda.Event(enable_timing=True)
    end_evt = torch.cuda.Event(enable_timing=True)
    start_evt.record()
    losses = []
    timing_events = []
    for _ in range(steps):
        optimizer.zero_grad(set_to_none=True)
        f_start = torch.cuda.Event(enable_timing=True)
        f_end = torch.cuda.Event(enable_timing=True)
        b_start = torch.cuda.Event(enable_timing=True)
        b_end = torch.cuda.Event(enable_timing=True)
        o_start = torch.cuda.Event(enable_timing=True)
        o_end = torch.cuda.Event(enable_timing=True)
        f_start.record()
        output = model(x)
        loss = (output - x).square().mean()
        f_end.record()
        b_start.record()
        loss.backward()
        b_end.record()
        o_start.record()
        optimizer.step()
        o_end.record()
        timing_events.append((f_start, f_end, b_start, b_end, o_start, o_end))
        losses.append(float(loss.detach()))
    end_evt.record()
    end_evt.synchronize()
    elapsed_s = start_evt.elapsed_time(end_evt) / 1000.0
    forward_s = sum(a.elapsed_time(b) for a, b, _, _, _, _ in timing_events) / 1000.0
    backward_s = sum(a.elapsed_time(b) for _, _, a, b, _, _ in timing_events) / 1000.0
    optimizer_s = sum(a.elapsed_time(b) for _, _, _, _, a, b in timing_events) / 1000.0
    return {
        "batch": batch,
        "steps": steps,
        "warmup": warmup,
        "elapsed_s": elapsed_s,
        "step_s": elapsed_s / steps,
        "samples_per_s": batch * steps / elapsed_s,
        "windows_per_s": batch * steps / elapsed_s,
        "forward_s_per_step": forward_s / steps,
        "backward_s_per_step": backward_s / steps,
        "optimizer_s_per_step": optimizer_s / steps,
        "loss_first": losses[0],
        "loss_last": losses[-1],
        "loss_decreased": losses[-1] < losses[0],
        "peak_memory_bytes": torch.cuda.max_memory_allocated(),
    }


def benchmark(extensions: Path, batches: list[int], steps: int, warmup: int) -> list[dict]:
    rows = []
    # A separate model is used for each batch so no shape-dependent state is
    # silently carried between measurements.
    for backend in ("vanilla", "cuda"):
        for batch in batches:
            torch.cuda.reset_peak_memory_stats()
            model = build_model(backend, seed=710 + batch, extension_dir=extensions if backend == "cuda" else None)
            try:
                row = _step_time(model, batch, steps=steps, warmup=warmup)
                row.update({"backend": backend, "status": "PASS"})
            except RuntimeError as exc:
                if "out of memory" not in str(exc).lower():
                    raise
                torch.cuda.empty_cache()
                row = {"backend": backend, "batch": batch, "status": "OOM", "error": str(exc)}
            rows.append(row)
            del model
            torch.cuda.empty_cache()
    return rows


def inference_benchmark(extensions: Path, batch: int, steps: int, warmup: int, observer: bool) -> list[dict]:
    if observer:
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from phase_e2_observer import extract
    rows = []
    for backend in ("vanilla", "cuda"):
        model = build_model(backend, seed=1710 + batch, extension_dir=extensions if backend == "cuda" else None).eval()
        x = torch.randn(batch, 64, 8, device="cuda", dtype=torch.float32)
        with torch.no_grad():
            for _ in range(warmup):
                if observer:
                    extract(model, x)
                else:
                    model(x)
        torch.cuda.synchronize()
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        with torch.no_grad():
            for _ in range(steps):
                if observer:
                    scores, features = extract(model, x)
                else:
                    output = model(x)
                    scores = (output - x).square().mean((1, 2))
        end.record()
        end.synchronize()
        elapsed_s = start.elapsed_time(end) / 1000.0
        rows.append({
            "backend": backend,
            "observer": observer,
            "batch": batch,
            "steps": steps,
            "warmup": warmup,
            "elapsed_s": elapsed_s,
            "batches_per_s": steps / elapsed_s,
            "decisions_per_s": batch * steps / elapsed_s,
            "peak_memory_bytes": torch.cuda.max_memory_allocated(),
            "finite": bool(torch.isfinite(scores).all()),
        })
        del model
        torch.cuda.empty_cache()
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extension-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("compare", "benchmark", "inference"), required=True)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--batches", default="128,256,512,1024")
    parser.add_argument("--utilization-log", type=Path, default=None)
    parser.add_argument("--observer", action="store_true")
    args = parser.parse_args()
    torch.set_float32_matmul_precision("highest")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    print(
        json.dumps(
            {
                "torch": torch.__version__,
                "cuda": torch.version.cuda,
                "device": torch.cuda.get_device_name(0),
                "capability": torch.cuda.get_device_capability(0),
                "backend": "vanilla or CUDA sm_121 static-global-template-stub=false",
            },
            sort_keys=True,
        ),
        flush=True,
    )
    sampler = None
    sample_file = None
    if args.utilization_log is not None:
        args.utilization_log.parent.mkdir(parents=True, exist_ok=True)
        sample_file = args.utilization_log.open("w")
        sampler = subprocess.Popen(
            [
                "nvidia-smi",
                "--query-gpu=timestamp,name,utilization.gpu,utilization.memory,memory.used",
                "--format=csv,noheader,nounits",
                "--loop-ms=200",
            ],
            stdout=sample_file,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    try:
        if args.mode == "compare":
            result = compare(args.extension_dir)
        elif args.mode == "inference":
            result = inference_benchmark(args.extension_dir, int(args.batches.split(",")[0]), args.steps, args.warmup, args.observer)
        else:
            result = benchmark(args.extension_dir, [int(x) for x in args.batches.split(",")], args.steps, args.warmup)
    finally:
        if sampler is not None:
            sampler.terminate()
            sampler.wait(timeout=5)
        if sample_file is not None:
            sample_file.close()
    print(json.dumps(result, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
