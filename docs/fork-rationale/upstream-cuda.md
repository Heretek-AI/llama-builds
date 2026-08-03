# upstream-cuda rationale

## Why this fork

ggml-org/llama.cpp CUDA universal build — one binary that runs on every
CUDA-capable GPU via PTX fallback. Most users want "the CUDA build"
without picking a specific SM, and PTX ensures forward compatibility
with newer GPUs that don't have a native sm_X yet.

## Alternatives considered

| Fork | Reason rejected as the universal CUDA build |
|---|---|
| upstream-cuda-sm89 (RTX 40xx) | Native SM gives faster startup but breaks on RTX 30xx / H100 / B100. Ships as a separate variant for SM-pinning users. |
| ikawrakow/ik_llama.cpp (CUDA) | IQ*K + Trellis quants need 12.4+; not appropriate as the universal CUDA baseline. |
| croll83/llama.cpp-dgx | Adds NVFP4 + DFlash for sm_121a; DGX-only feature set. |
| NVIDIA-Merlin/HierarchicalKV | Different project scope (KV cache compression, not the inference engine). |

## What we ship

- `llama-server`, `llama-cli`, `llama-bench`, `llama-quantize`
- Universal PTX build — runs on sm_50 .. sm_120 and beyond
- `GGML_CUDA=ON`, no `CMAKE_CUDA_ARCHITECTURES` override (uses upstream default)

## Drift risk

Medium. CUDA itself is pinned to the rolling toolkit in this build;
see issue #82 for the per-target pin policy. NVCC version bumps can
break IQK kernels downstream (ik-llama-cpp-cuda is the canary).

## Cross-repo deps

- heretek-manager install target: `upstream-cuda`
- llama-manager: `heretek install llama-cpp` resolves to this on NVIDIA hosts

## Re-trigger criteria

When upstream llama.cpp tags a release that bumps the default
`CMAKE_CUDA_ARCHITECTURES` set or changes the PTX fallback policy.
Otherwise the rationale is stable.
