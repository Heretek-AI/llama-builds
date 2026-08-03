# llama-builds fork rationale index

Per issue #84 (lb-0097), each Tier-1 fork target ships a per-fork
rationale doc explaining why it was chosen over the alternatives
surfaced by SYNTHESIS.md. The manifest `description` field links back
to the doc for that target.

| Target | Rationale | Notes |
|---|---|---|
| `upstream-cpu` | [upstream-cpu.md](./upstream-cpu.md) | ggml-org/llama.cpp CPU baseline |
| `upstream-cuda` | [upstream-cuda.md](./upstream-cuda.md) | ggml-org/llama.cpp CUDA universal |
| `upstream-cuda-sm80` | [upstream-cuda-sm80.md](./upstream-cuda-sm80.md) | Ampere datacenter (A100, A30) |
| `upstream-cuda-sm86` | [upstream-cuda-sm86.md](./upstream-cuda-sm86.md) | Ampere consumer (RTX 30xx, A10) |
| `upstream-cuda-sm89` | [upstream-cuda-sm89.md](./upstream-cuda-sm89.md) | Ada Lovelace (RTX 40xx, L4, L40S) |
| `upstream-cuda-sm90` | [upstream-cuda-sm90.md](./upstream-cuda-sm90.md) | Hopper (H100, H200) |
| `upstream-rocm` | [upstream-rocm.md](./upstream-rocm.md) | AMD ROCm baseline |
| `upstream-vulkan` | [upstream-vulkan.md](./upstream-vulkan.md) | Cross-vendor Vulkan SPIR-V |
| `ik-llama-cpp` | [ik-llama-cpp.md](./ik-llama-cpp.md) | ikawrakow IQ*K + Trellis quants |
| `ik-llama-cpp-cuda` | [ik-llama-cpp-cuda.md](./ik-llama-cpp-cuda.md) | ik_llama.cpp CUDA backend |
| `llama-cpp-dgx` | [llama-cpp-dgx.md](./llama-cpp-dgx.md) | croll83 DGX Spark variant |

Each rationale doc follows the same six-section template:

1. **Why this fork** — the specific value-prop vs upstream llama.cpp.
2. **Alternatives considered** — the 3-5 forks from SYNTHESIS.md that
   compete on the same axis.
3. **What we ship** — concrete capabilities and binaries.
4. **Drift risk** — how often this target's upstream breaks and how
   we cope.
5. **Cross-repo deps** — heretek-manager install target / llama-manager
   wiring, where applicable.
6. **Re-trigger criteria** — when to revisit this rationale.
