# ik-llama-cpp-cuda rationale

## Why this fork

ikawrakow/ik_llama.cpp compiled for NVIDIA GPUs. Same IQ*K + Trellis
quant advantage as the CPU variant, but on the CUDA backend. For
servers running IQ*K-quantized models on H100/A100/L40S, this is the
correct target.

## Alternatives considered

| Fork | Reason rejected |
|---|---|
| ik-llama-cpp (CPU) | Cannot serve IQ*K models above ~5 tok/s on consumer GPUs; CUDA path is the production choice. |
| upstream-cuda + IQ*K dequant in app | Llama-quantize + the existing CUDA build can't read IQ*K GGUF; not a substitute. |

## What we ship

- CUDA build of ik_llama.cpp with native sm_89 compile
- IQ*K dequant + matmul kernels (332 files) on the GPU
- `extra_cmake_flags=-DCMAKE_CUDA_ARCHITECTURES=89`
- CUDA toolkit pinned to **12.4.0** (per issue #82 / PR #87)

## Drift risk

High. Triple-source risk: (1) ik_llama.cpp fork lag, (2) ggml-org core
bump, (3) NVIDIA CUDA toolkit bump. The CUDA pin mitigates (3); the
smoke test (issue #81 / PR #86) exercises the IQK kernels end-to-end
so (1) and (2) regressions surface in CI.

## Cross-repo deps

- heretek-manager install target: `ik-llama-cpp-cuda`
- heretek-manager VRAM weight entries (`hm-0094`) gate production use
  so heretek-manager doesn't crash when running the new targets.

## Re-trigger criteria

When ik_llama.cpp rebases onto a new ggml-org release, when NVIDIA
ships CUDA 12.5/13.x and ikawrakow confirms IQK kernel compatibility,
or when an IQK kernel regresses on the smoke test.
