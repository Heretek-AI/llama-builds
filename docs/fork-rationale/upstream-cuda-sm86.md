# upstream-cuda-sm86 rationale

## Why this fork

Ampere consumer SM (sm_86) — RTX 30xx series, A10. Same story as sm_80
but for the consumer Ampere parts that don't include the data-center
features.

## Alternatives considered

| Fork | Reason rejected for sm_86 |
|---|---|
| upstream-cuda-sm80 | Same generation but different feature set; sm_86 has consumer-only RTX extensions. |

## What we ship

- Native sm_86 build, no PTX
- `CMAKE_CUDA_ARCHITECTURES=86`

## Drift risk

Low. sm_86 is stable.

## Cross-repo deps

- heretek-manager install target: `upstream-cuda-sm86` (auto-selected when SM = sm_86)

## Re-trigger criteria

When NVIDIA deprecates sm_86.
