# upstream-cuda-sm89 rationale

## Why this fork

Ada Lovelace SM (sm_89) — RTX 40xx consumer, L4, L40S, RTX 6000 Ada.
Largest installed base for new CUDA installs in 2024-2026.

## Alternatives considered

| Fork | Reason rejected for sm_89 |
|---|---|
| upstream-cuda-sm90 | Hopper datacenter; SM 90 has TMA + thread-block clusters Ada doesn't. |

## What we ship

- Native sm_89 build
- `CMAKE_CUDA_ARCHITECTURES=89`

## Drift risk

Low. sm_89 is current-generation.

## Cross-repo deps

- heretek-manager install target: `upstream-cuda-sm89`

## Re-trigger criteria

When NVIDIA ships a Blackwell consumer part that supersedes sm_89.
