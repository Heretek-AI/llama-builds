# llama-cpp-dgx rationale

## Why this fork

croll83/llama.cpp-dgx adds NVFP4 + DFlash for NVIDIA's DGX Spark
platform (sm_121a Blackwell consumer). DFlash is a speculative-decoding
innovation not yet merged into upstream llama.cpp.

## Alternatives considered

| Fork | Reason rejected |
|---|---|
| upstream-cuda (universal) | No DFlash; misses the speculative-decoding speedup. |
| upstream-cuda-sm89 | Ada, not Blackwell consumer. |

## What we ship

- CUDA build for sm_90 + sm_121a (the DGX Spark APU)
- DFlash speculative decoding enabled at compile time
- `extra_cmake_flags=-DCMAKE_CUDA_ARCHITECTURES=90`
- Status: `active` (was `deprecated` in roadmap W1.0; revived in W3 per issue #54)

## Drift risk

Medium. DGX Spark is a recent platform (sm_121a shipped late 2025);
toolchain support is new and NVIDIA is still iterating on the driver.

## Cross-repo deps

- heretek-manager install target: `llama-cpp-dgx` (auto-selected when DGX Spark detected)

## Re-trigger criteria

When DGX Spark moves to a Blackwell successor (sm_12x), or when
DFlash is merged into upstream llama.cpp (in which case we deprecate
this variant and route via `upstream-cuda`).
