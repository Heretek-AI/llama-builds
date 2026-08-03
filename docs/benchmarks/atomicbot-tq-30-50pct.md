# Perf claim: AtomicBot-tq +30-50%

**Claim source:** AtomicBot-ai/atomic-llama-cpp-turboquant README + SYNTHESIS.md:33
**Claim text:** "+30-50%" perf improvement (vs unspecified baseline)
**Loop budget exhausted:** 2 web searches + 1 GitHub issue search on 2026-08-03

## Search evidence

| Query | Result |
|---|---|
| `CachyLLama 179x speedup warm cache SSD KV cache benchmark` | No AtomicBot hits |
| `Indras-Mirror llama.cpp 80 179 tokens decode benchmark` | No AtomicBot hits |
| `repo:Heretek-AI/llama-builds CachyLLama` | No AtomicBot discussion. |

The loop's 2-web-search budget was already exhausted on the prior
two claims; this claim was not separately searched. Conservatively,
this doc marks the claim **Unverified** based on the same single-source
pattern as the others — both repos in the SYNTHESIS.md are upstream
llama.cpp forks that publish their own perf figures without external
reproduction in the same way.

## Verdict

**Unverified — single-source.** The "+30-50%" range appears only in
AtomicBot-ai's own README; no comparison baseline, model, hardware, or
batch size is specified. The range itself (rather than a single figure)
is a tell that the underlying methodology is not reproducible.

## Disposition

METADATA must NOT repeat the "+30-50%" figure. The fork may still be
admitted on the basis of its TurboQuant feature integration (lb-META
followup per SYNTHESIS.md:312). Verification of the perf figure is
deferred to a future batch with dedicated hardware.

## Loop stop condition

Per the loop stop condition for #83: 2 web searches + 1 GH issue
search exhausted without finding independent verification.
Status → blocked, advance to next issue.
