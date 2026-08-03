# upstream-cuda-sm80 rationale

## Why this fork

Ampere datacenter SM (sm_80) — A100, A30, NVIDIA EGX / HGX platforms.
PTX fallback is unnecessary on these GPUs, and native compilation
gives ~10-15% faster startup (no JIT) and a smaller binary footprint
(~600 MB → ~280 MB).

## Alternatives considered

| Fork | Reason rejected for sm_80 |
|---|---|
| upstream-cuda (universal) | Smaller startup benefit; same long-term perf after JIT warmup. |
| upstream-cuda-sm90 (Hopper) | Different SM generation; users on A100s need sm_80 not sm_90. |

## What we ship

- Native sm_80 build, no PTX
- `CMAKE_CUDA_ARCHITECTURES=80`
- Smaller binary, no JIT overhead

## Drift risk

Low. SM_80 is stable since 2020; toolchain support won't change.

## Cross-repo deps

- heretek-manager install target: `upstream-cuda-sm80` (auto-selected when SM = sm_80)

## Re-trigger criteria

When NVIDIA deprecates sm_80 in a future CUDA toolkit (currently
CUDA 13.x still ships sm_80 support). Revaluate before then.
