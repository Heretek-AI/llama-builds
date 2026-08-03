# upstream-cuda-sm90 rationale

## Why this fork

Hopper SM (sm_90) — H100, H200. Datacenter flagship with TMA + cluster
launch + FP8 tensor cores. Workloads on Hopper that benefit from these
features lose 20-30% perf if compiled for a generic arch.

## Alternatives considered

| Fork | Reason rejected for sm_90 |
|---|---|
| upstream-cuda-sm100 | sm_100 is Blackwell datacenter (B100/B200); separate target. |

## What we ship

- Native sm_90 build
- `CMAKE_CUDA_ARCHITECTURES=90`

## Drift risk

Low. sm_90 is current datacenter flagship.

## Cross-repo deps

- heretek-manager install target: `upstream-cuda-sm90`

## Re-trigger criteria

When Hopper is superseded by Blackwell datacenter (sm_100 is already
shipping; rationale will need to revisit when the install base shifts).
