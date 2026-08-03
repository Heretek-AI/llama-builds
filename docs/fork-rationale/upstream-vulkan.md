# upstream-vulkan rationale

## Why this fork

ggml-org/llama.cpp Vulkan/SPIR-V build — runs on any GPU that has a
Vulkan 1.2+ driver (Intel Arc, AMD, NVIDIA, Mali, Adreno). Single
binary covers the long tail of consumer hardware that CUDA/ROCm don't
reach.

## Alternatives considered

| Fork | Reason rejected for Vulkan baseline |
|---|---|
| SYCL backend | Different build system; SYCL is a separate target if Intel-only. |
| Metal backend | Apple-only; not in scope for this Linux-centric manifest. |

## What we ship

- Vulkan SPIR-V build for any 1.2+ capable GPU
- `GGML_VULKAN=ON`

## Drift risk

Low. Vulkan ABI is stable.

## Cross-repo deps

- heretek-manager install target: `upstream-vulkan`

## Re-trigger criteria

When ggml-org ships a Vulkan 1.3+ feature dependency.
