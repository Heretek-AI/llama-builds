# Perf claim: CachyLLama 179.1x speedup warm cache

**Claim source:** fewtarius/CachyLLama README + SYNTHESIS.md:31
**Claim text:** "179.1x speedup warm cache" (SSD-backed KV cache)
**Loop budget exhausted:** 2 web searches + 1 GitHub issue search on 2026-08-03

## Search evidence

| Query | Result |
|---|---|
| `CachyLLama 179x speedup warm cache SSD KV cache benchmark` | All 5 hits were either the CachyLLama repo itself, Sensenkawa/CachyLLama (a mirror), or generic KV-cache research papers unrelated to the specific 179.1x figure |
| `Indras-Mirror llama.cpp 80 179 tokens decode benchmark` | All 5 hits were the Indras-Mirror repo itself |
| `repo:Heretek-AI/llama-builds CachyLLama` | 6 hits — all existing roadmap issues (#83, #84, #85, #80 closed, #57 closed duplicate, #12 closed original). No benchmark artifacts. |

## Verdict

**Unverified — single-source.** The "179.1x" figure appears only in
CachyLLama's own README and downstream forks/mirrors that quote it.
No independent reproduction was found within the loop budget.

## Hardware baseline

The claim does not specify the comparison baseline. "Warm cache"
implies a re-warm from SSD vs full re-derivation; the headline ratio
depends critically on the system-prompt length, the SSD read bandwidth,
and the prior cold-cache time. None of these are pinned in the source.

## Disposition

METADATA must NOT repeat the "179.1x" figure. The fork may still be
admitted to the build matrix on the basis of the unique SSD-KV-cache
**feature** alone (lb-0093 already shipped this disposition).
Verification of the perf figure is deferred to a future batch with
dedicated hardware.

## Loop stop condition

Per the loop stop condition for #83: "perf-claim verification cannot
be confirmed or refuted within 2 web searches + 1 GitHub issue search
→ mark `status/blocked`, leave METADATA untouched, advance."
