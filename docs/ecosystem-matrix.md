# Ecosystem Matrix

Reference document tracking the full llama.cpp fork/binding/orchestrator landscape.
Targets in `targets/` are **build targets** (produce binaries). Everything here is
**reference-only** — not built by this registry.

## Build Targets (in `targets/`)

| Slug              | Repo                   | Backend | Status     | Notes                                               |
| ----------------- | ---------------------- | ------- | ---------- | --------------------------------------------------- |
| upstream-cpu      | ggml-org/llama.cpp     | cpu     | active     | Upstream baseline                                   |
| upstream-cuda     | ggml-org/llama.cpp     | cuda    | active     | Upstream CUDA                                       |
| upstream-rocm     | ggml-org/llama.cpp     | rocm    | active     | Upstream ROCm                                       |
| upstream-vulkan   | ggml-org/llama.cpp     | vulkan  | active     | Upstream Vulkan                                     |
| ik-llama-cpp      | ikawrakow/ik_llama.cpp | cpu     | active     | SOTA IQ*K quants, last synced Aug 2024              |
| ik-llama-cpp-cuda | ikawrakow/ik_llama.cpp | cuda    | active     | CUDA variant (sm_89)                                |
| llama-cpp-dgx     | croll83/llama.cpp-dgx  | cuda    | deprecated | DFlash+TurboQuant, maintainer deprecated 2026-05-25 |

## Rejected Targets (not llama.cpp forks)

| Issue | Repo                         | Why Rejected                                                                                                                            |
| ----- | ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| #11   | sgl-project/sglang           | Python serving framework (pip/PyTorch/flashinfer), not a llama.cpp fork. Uses llama.cpp only as optional backend via `sglang[llamacpp]` |
| #14   | lemonade-sdk/llamacpp-rocm   | CI recipe for upstream+ROCm7 with ephemeral S3 nightly tarballs. No forked source code                                                  |
| #15   | TheTom/llama-cpp-turboquant  | Fork of AtomicBot-ai/atomic-llama-cpp-turboquant — exists but WHT+TCQ quantization not distinct enough for separate target             |
| #17   | spiritbuun/buun-llama-cpp    | Exists but NOT a llama.cpp fork (`isFork: false`) — fails `is_llama_cpp_fork` gate                                                      |
| #18   | huawei-csl/KVarN             | Exists but is a vLLM KV-cache backend, not a llama.cpp fork                                                                             |
| #20   | microsoft/BitNet             | 1-bit inference engine. Has CMakeLists.txt but may not be a llama.cpp fork — needs verification. Build requires clang-18+               |
| #21   | NVIDIA-Merlin/HierarchicalKV | CUDA header-only RecSys KV library (Bazel/CMake, SM8+), not a llama.cpp fork                                                            |

## Phantom Repos (verified 2026-08-02)

| Issue | Repo                        | Status                                                                                     |
| ----- | --------------------------- | ------------------------------------------------------------------------------------------ |
| #15   | TheTom/llama-cpp-turboquant | Exists (fork of AtomicBot-ai/atomic-llama-cpp-turboquant) — see Rejected Targets           |
| #17   | spiritbuun/buun-llama-cpp   | Exists but NOT a llama.cpp fork — rejected per `is_llama_cpp_fork` gate                     |
| #18   | huawei-csl/KVarN            | Exists but is a vLLM KV-cache backend, not a llama.cpp fork — rejected                     |

## Bindings (reference-only, not build targets)

Every binding vendors its own llama.cpp — none consumes prebuilt binaries from this registry.
They belong in native package managers (PyPI, NuGet, go get), not here.

| Issue | Repo                     | Language | Distribution          |
| ----- | ------------------------ | -------- | --------------------- |
| #22   | abetlen/llama-cpp-python | Python   | PyPI (cibuildwheel)   |
| #23   | shakfu/cyllama           | Cython   | pip                   |
| #24   | gotzmann/llama.go        | Go       | go get                |
| #25   | SciSharp/LLamaSharp      | C#       | NuGet                 |
| #27   | tarsilabs/llama_ros      | ROS2     | colcon (FetchContent) |

## Orchestrators / Tools (reference-only)

These consume llama.cpp binaries but are not llama.cpp forks.

| Issue | Repo                  | Type                                     |
| ----- | --------------------- | ---------------------------------------- |
| #28   | hiyouga/LlamaFactory  | Python fine-tuning framework (Gradio UI) |
| #29   | mostlygeek/llama-swap | Go model swap orchestrator               |
| #30   | intentee/paddler      | Rust load balancer (prefill/decode)      |
| #31   | containers/ramalama   | OCI container tool                       |

## Out-of-Scope (cannot build in CI)

| Issue | Repo                                | Why                                                  |
| ----- | ----------------------------------- | ---------------------------------------------------- |
| #26   | bostrot/llama.cpp-d                 | Delphi bindings — non-free compiler, manual DLL copy |
| #32   | nmoroz/ic-canister-wasm             | IC SDK not available in GitHub Actions               |
| #33   | hogeheer499/strix-halo-ttm          | Needs AMD Strix Halo hardware (ROCm 7, gfx1151)      |
| #19   | carlosfundora/llama.cpp-1-bit-turbo | Needs AMD gfx1030 hardware (ROCm 6.x, HIP)           |

## Governance

- This document is maintained alongside `targets/` to explain ingestion decisions
- When a target is promoted from reference to build target, move it to the Build Targets table
- When a repo is verified as 404 or non-fork, add it to the appropriate rejection table
- The `is_llama_cpp_fork` gate in `scripts/metadata_parser.py` enforces the fork requirement at manifest generation time
