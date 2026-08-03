# upstream-cpu rationale

## Why this fork

ggml-org/llama.cpp is the canonical reference implementation. The
CPU baseline is the simplest possible build and serves as the
foundation for every other backend (CUDA, ROCm, Vulkan) — it has the
smallest surface area, the broadest platform support (x86_64 Linux,
Windows, macOS, BSDs), and is the regression target for higher-level
projects.

## Alternatives considered

| Fork | Reason rejected for CPU baseline |
|---|---|
| ikawrakow/ik_llama.cpp | SOTA IQ*K custom quants, but the CPU build path is largely identical; we ship ik-llama-cpp separately as a variant. |
| ggml-org/llama.cpp (master vs pinned) | We pin to a specific SHA in METADATA `ref=` for reproducibility; master is not shipped. |
| ggml-org/llama.cpp + CUDA | separate target `upstream-cuda`; the CPU target stays CUDA-free. |

## What we ship

- `llama-server`, `llama-cli`, `llama-bench`, `llama-quantize`
- CPU-only build with `GGML_NATIVE=ON`
- Multi-arch (x86_64 primarily; aarch64 is supported by upstream)

## Drift risk

Low. ggml-org/llama.cpp ships a stable tagged release every few weeks;
upstream-watch.yml detects new SHAs and triggers a re-build. The
`drift_risk_note` for this target is empty.

## Cross-repo deps

- heretek-manager install target: `upstream-cpu`
- llama-manager: consumed by the build-llama composite action

## Re-trigger criteria

When upstream llama.cpp tags a new minor release, run upstream-watch
and re-evaluate the pinned SHA. The rationale is stable; only the
SHA rotates.
