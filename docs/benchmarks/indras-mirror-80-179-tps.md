# Perf claim: Indras-Mirror 80-179 tok/s decode

**Claim source:** Indras-Mirror/llama.cpp-turboq-mtp README + SYNTHESIS.md:30
**Claim text:** "80-179 tok/s decode (325 effective) with lossless 4.25 bpv KV cache at 262K context on RTX 4090 24GB"
**Loop budget exhausted:** 2 web searches + 1 GitHub issue search on 2026-08-03

## Search evidence

| Query | Result |
|---|---|
| `CachyLLama 179x speedup warm cache SSD KV cache benchmark` | No Indras-Mirror hits |
| `Indras-Mirror llama.cpp 80 179 tokens decode benchmark` | All 5 hits were the Indras-Mirror repo itself (README, source code, tags, GitHub user page, branch compare). No independent reproduction. |
| `repo:Heretek-AI/llama-builds CachyLLama` | No Indras-Mirror discussion. |

## Verdict

**Unverified — single-source.** The "80-179 tok/s" range appears only
in Indras-Mirror's own README. The (325 effective) qualifier in
parentheses is undefined in the source (no measurement methodology).
No independent reproduction was found within the loop budget.

## Hardware pinning

The figure is tied to RTX 4090 24GB at 262K context. The repo is
marked stale (3+ months inactive, per SYNTHESIS.md). Reproducing the
claim requires a 24 GB Ada card and a 262K-context workload; both
are out of scope for this loop (issue text: "Hardware procurement for
repeatability" is out-of-scope).

## Disposition

Per SYNTHESIS.md triage, Indras-Mirror is `defer` — repo is stale,
not admitted to the manifest until independently re-verified. METADATA
must NOT repeat the "80-179 tok/s" figure.

## Loop stop condition

Per the loop stop condition for #83: 2 web searches + 1 GH issue
search exhausted without finding independent verification.
Status → blocked, advance to next issue.
