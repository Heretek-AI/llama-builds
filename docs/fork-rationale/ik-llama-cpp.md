# ik-llama-cpp rationale

## Why this fork

ikawrakow/ik_llama.cpp adds SOTA custom quantization types (IQ*K,
Trellis IQ*KT, IQ*KL) on top of llama.cpp. For models quantized with
these types, the upstream ggml-org dequant path is materially slower
(2-5x) than ik_llama.cpp's optimized kernels. With 332 IQK files in
the fork, the quantization quality is the SOTA for sub-4-bit
quantization.

## Alternatives considered

| Fork | Reason rejected as the IQ*K baseline |
|---|---|
| ggml-org/llama.cpp | Doesn't ship IQ*K kernels at all. |
| TheTom/llama-cpp-turboquant | WHT + TCQ is a different quantization family; not a substitute. |
| AtomicBot-ai/atomic-llama-cpp-turboquant | TurboQuant variant; performance claim (+30-50%) is unverified per issue #83. |
| spiritbuun/buun-llama-cpp | Adds VBR/TCQ/TurboQuant codecs on top of upstream; orthogonal feature. |
| LL4nc33/llama-tq | Incompatible enum values; runtime opt-in only. |

## What we ship

- `llama-server`, `llama-cli`, `llama-quantize`, `llama-bench`
- IQ*K + Trellis IQ*KT + IQ*KL quants (all `iq_k` capability)
- CPU backend with `GGML_NATIVE=ON`

## Drift risk

High. ikawrakow's master branch was last synced with upstream Aug 2024
(per METADATA `drift_risk_note`). The fork ships 332 IQK files that
need manual reconciliation when ggml-org bumps core ggml APIs.
`fork-health.yml` audits staleness weekly.

## Cross-repo deps

- heretek-manager install target: `ik-llama-cpp`
- IQK smoke test: PR #86 (issue #81)

## Re-trigger criteria

When ikawrakow rebases onto a new ggml-org release and ships a tag,
or when an upstream ggml API breaks an IQK kernel (currently watched
by fork-health.yml).
