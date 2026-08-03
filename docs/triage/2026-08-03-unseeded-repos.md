# Triage — 2026-08-03 unseeded repos from SYNTHESIS.md:131-141

This doc records the disposition for each repo that was listed in
SYNTHESIS.md but had no `targets/<slug>/build.sh` entry at the time
the 2026-08-03 ulw-research bundle was generated. Per lb-0099 / #85.

## Disposition table

| # | Repo | SYNTHESIS.md line | Disposition | Tag |
|---|------|-------------------|--------------|-----|
| 1 | fewtarius/CachyLLama | 131 (implied via lb-0093) | **seed** (lb-0093, closed in #80) | `roadmap/backlog` |
| 2 | spiritbuun/buun-llama-cpp | 132 (implied via lb-0092) | **seed** (lb-0092, closed in #79) | `roadmap/backlog` |
| 3 | Indras-Mirror/llama.cpp-turboq-mtp | 131 | **defer** (3+ months stale; perf claim 80-179 tok/s unverified per #83) | `roadmap/backlog` |
| 4 | openalchemy/llama.cpp | 131 | **defer** (+47% gen speed unverified per #83) | `roadmap/backlog` |
| 5 | atomicmilkshake/godzilla-llama.cpp | 131 | **defer** (no clear unique value-prop vs already-seeded forks) | `roadmap/backlog` |
| 6 | unixsysdev/llama-turboquant | 131 | **defer** (overlaps with TheTom-tq + AtomicBot-tq; duplicate TurboQuant axis) | `roadmap/backlog` |
| 7 | LL4nc33/llama-tq | 131 | **defer** (incompatible enum values; runtime opt-in; fork-of-fork) | `roadmap/backlog` |
| 8 | LyndonBlack/llama.cpp-Ternary-1.58Bit-and-TurboQuant | 131 | **skip** (aspirational; no published benchmark) | `meta/skip-rationale` |
| 9 | Anbeeld/beellama.cpp | 131 | **seed** as `lb-META-FOLLOWUP-1` (unique 1.58-bit ternary focus) | `roadmap/backlog` |
| 10 | onthenose-record446/turboquant-llama-lab | 131 | **skip** (Windows-only) | `meta/skip-rationale` |
| 11 | Aulora137/Lean_llama.cpp | 131 | **skip** (fork-of-fork — covered indirectly via `ik-llama-cpp`) | `meta/skip-rationale` |
| 12 | KV-cache repos (LMCache, kvpress, PegaFlow) | 132 | **out-of-scope** (heretek-manager concern, not llama-builds) | `meta/skip-rationale` |
| 13 | Alternative runtimes (openinfer, vmlx) | 133 | **out-of-scope** (Phase 4 ecosystem, separate spec) | `meta/skip-rationale` |

The issue counts "12 repos" — that aligns with rows 1–12 above (the
13th is a category bucket, not a repo).

## Out-of-scope rationale (heretek-manager vs llama-builds)

**KV-cache repos** (LMCache, kvpress, PegaFlow): these are KV cache
compression / migration layers that sit **between** llama-builds'
output binaries and a serving runtime (vLLM, TGI). They are heretek-
manager concern (install + serve orchestration), not llama-builds
concern (build the llama.cpp binary). Routing them through
heretek-manager install targets rather than llama-builds keeps the
build manifest focused on inference engines.

**Alternative runtimes** (openinfer, vmlx): these are competing
inference engines (Rust / Python), not llama.cpp forks. Routing them
through llama-builds would dilute the manifest's
"is_llama_cpp_fork=true" semantic. They belong to a separate
ecosystem-matrix spec (per SYNTHESIS.md:312-313).

## Status mapping

- `seed` rows 1–2 → already closed via #79, #80. Triage row remains
  for audit traceability.
- `seed` row 9 → tracked as `lb-META-FOLLOWUP-1` backlog entry;
  rationale doc goes under `docs/fork-rationale/anbeeld-beellama.md`
  when that target ships.
- `defer` rows 3–7 → tagged `roadmap/backlog`; revisit when their
  unverified perf claims (#83) clear or when upstream rebases.
- `skip` rows 8, 10, 11 → tagged `meta/skip-rationale`.
- `out-of-scope` rows 12, 13 → tagged `meta/skip-rationale`; tracked
  by heretek-manager (rows 12) and the ecosystem-matrix spec (row 13).

## Re-trigger criteria

- Any `defer` row's unverified perf claim gets verified → re-evaluate
  admission to the build manifest.
- `out-of-scope` rows change scope (e.g. KV-cache moves to llama.cpp
  upstream via FlashAttention) → reconsider.
- `skip` rows gain meaningful activity (stars, releases, benchmarks)
  → reconsider.
- New repos surface in SYNTHESIS updates → append rows.

## Cross-references

- SYNTHESIS.md:130-141 (gap analysis)
- lb-0096 / #83 (perf-claim verification) — drives row 3, 4 verdicts
- lb-0092 / #79 (buun-llama-cpp seed, closed)
- lb-0093 / #80 (CachyLLama seed, closed)
- lb-0097 / #84 (fork rationale docs — applies to row 9 when shipped)
