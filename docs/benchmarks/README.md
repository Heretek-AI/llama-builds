# Perf claim verification verdict — 2026-08-03

**Loop budget:** 2 web searches + 1 GitHub issue search.

| # | Claim | Source | Verdict | Artifact |
|---|---|---|---|---|
| 1 | CachyLLama 179.1x warm cache speedup | SYNTHESIS.md:31 | **Unverified — single-source** | `docs/benchmarks/cachyllama-179x-speedup.md` |
| 2 | Indras-Mirror 80-179 tok/s decode | SYNTHESIS.md:30 | **Unverified — single-source** | `docs/benchmarks/indras-mirror-80-179-tps.md` |
| 3 | AtomicBot-tq +30-50% | SYNTHESIS.md:33 | **Unverified — single-source** | `docs/benchmarks/atomicbot-tq-30-50pct.md` |
| 4 | openalchemy +47% gen speed | SYNTHESIS.md:36 | **Unverified — single-source** | `docs/benchmarks/openalchemy-47pct-gen-speed.md` |

All four claims trace to the fork's own README. No independent
reproduction was found within the loop budget. Per the loop stop
condition, this issue is **status/blocked** and the loop advances.

## METADATA

The current `targets/*/build.sh` METADATA files do NOT contain any of
the four perf figures — no stripping required. The figures are not
admitted to any fork's METADATA description.

## Forward action

When hardware is available, re-run this verification with proper
benchmark harnesses (llama-bench for tok/s; warm-cache delta for
CachyLLama SSD-KV). Update each `docs/benchmarks/<claim>.md` with
measured numbers and a `verified-on: <date>` line. Until then,
all four claims remain unverified.
