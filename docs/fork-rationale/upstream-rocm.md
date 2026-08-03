# upstream-rocm rationale

## Why this fork

ggml-org/llama.cpp ROCm/HIP build for AMD Instinct (MI200/MI300) and
Radeon (RX 7000 series) GPUs. Same rationale as upstream-cuda but for
AMD's ROCm/HIP stack.

## Alternatives considered

| Fork | Reason rejected for ROCm baseline |
|---|---|
| lemonade-sdk/llamacpp-rocm | Strix-Halo-specific gfx1151 build; upstream-rocm supports gfx110X + gfx120X. |
| fewtarius/CachyLLama | Adds SSD KV cache; orthogonal feature, ship separately if needed. |
| Lychee-Technology/llama-cpp-for-strix-halo | TTM unlock hack; only relevant for specific Strix Halo boards. |

## What we ship

- ROCm/HIP build for gfx1100/1101/1102/1103/1150/1151/1200/1201
- `GGML_HIP=ON`, no GPU_TARGETS override (uses upstream defaults)

## Drift risk

Medium. AMD ships ROCm minor versions frequently; matrix.yml's
ROCm install step pulls the latest nightly tarball. Re-baseline
monthly.

## Cross-repo deps

- heretek-manager install target: `upstream-rocm`
- llama-manager: `heretek install llama-cpp` resolves to this on AMD hosts

## Re-trigger criteria

When upstream llama.cpp bumps the ROCm HIP API level (currently 5.x).
