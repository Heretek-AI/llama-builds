# llama-builds — ulw-research 2026-08-03 roadmap

**Batch label:** `roadmap/ulw-research-2026-08-03`
**Sprint window:** 2026 Q3 (2026-07-01 → 2026-09-30)
**Source research:** `.omo/ulw-research/20260803-010124/{IMPLEMENTATION_PLAN.md,SYNTHESIS.md,hyperplan-bundle.md}`

This summary is the durable filter-recovery handle for future sessions
(see harness spec §6.5 rule 7). To re-derive the in-flight roadmap in
a fresh context: `gh issue list --label roadmap/ulw-research-2026-08-03`.

## TL;DR

7 tracking items surface the llama-builds-relevant work from the
2026-08-03 ulw-research bundle: 6 atomic implementation issues
(Tier-1 fork targets, IQK smoke test, CUDA pinning, perf-claim
verification, fork rationale docs) + 1 meta-issue that triages the
12 unseeded repos surfaced by SYNTHESIS.md:131-141.

## Per-issue table

| Seed ID | Title | Status | Source | Sprint? |
|---------|-------|--------|--------|---------|
| `lb-0092` | Add buun-llama-cpp as second Tier-1 fork target (CPU + CUDA sm_89) | status/backlog | `Write out a design doc for the project.md` §2.2 | yes |
| `lb-0093` | Add CachyLLama as heretek-manager install target (SSD KV cache feature) | status/backlog | `Write out a design doc for the project.md` §2.2 | yes |
| `lb-0094` | Add IQK smoke test to ik_llama.cpp targets using IQ4_KS fixture | status/backlog | `Write out a design doc for the project.md` §2.2 | yes |
| `lb-0095` | Pin CUDA toolkit version explicitly in ik_llama.cpp build scripts | status/backlog | `Write out a design doc for the project.md` §2.2 | yes |
| `lb-0096` | Verify or refute 4 unverified single-source perf claims before manifest promotion | status/backlog | `Write out a design doc for the project.md` §13 | partial |
| `lb-0097` | Document Q3 2026 fork selection rationale in manifest entry descriptions | status/backlog | `Write out a design doc for the project.md` §13 | yes |
| `lb-0099` | META — Triage the 12 unseeded repos from SYNTHESIS.md:131-141 | status/backlog | `Write out a design doc for the project.md` §13 | partial |

## Decided vs Deferred (from hyperplan-bundle.md)

**Adopted in scope:**
- Tier-1 fork target: buun-llama-cpp (lb-0092) — VBR/TCQ/TurboQuant codecs
- Tier-1 fork target: CachyLLama (lb-0093) — unique SSD KV cache value-prop
- ik_llama.cpp IQK smoke test (lb-0094) — already shipped target, smoke-test gap
- CUDA toolkit pinning (lb-0095) — addresses tech-debt F4 fragility

**Deferred (out of scope for this batch):**
- 12 unscheduled repos from SYNTHESIS.md — bundled into lb-0099 meta for triage
- 4 unverified single-source perf claims — bundled into lb-0096 for re-verification
  (CachyLLama 179x, Indras-Mirror 80-179 tok/s, AtomicBot +30-50%, openalchemy +47%).
  Until verified, METADATA descriptions must NOT repeat the claim.
- MLX backend — killed by user-value F2 + F7 + logic F5 (3 of 4 attackers).
- Third heretek repo — killed by all 4 attackers.
- N×M fork×backend matrix refactor — premature at 5-7 targets (tech-debt F1 + scope F1).
- Fork-of-fork CI requirement (tech-debt F6) — overgating, validate in our CI not theirs.

## Cross-repo pointers

- `lb-0092` / `lb-0093` depend on `hm-0094` (VRAM weight entries) so heretek-manager
  doesn't crash when running the new targets.
- `lb-0094` IQK smoke test depends on `hm-0094`/`hm-0095` for full asymmetric K/V
  validation when TurboQuant cache types land.

## Re-trigger criteria (when this batch closes)

- All 6 atomic issues reach `status/done`.
- Meta-issue `lb-0099` reaches a triaged state (one decision per unseeded repo documented).
- Or: 90 days elapse with no progress on any item.

## Open questions for future sessions

1. Which fork target gets Week 2 priority: buun-llama-cpp (lb-0092) or CachyLLama (lb-0093)?
   The original hyperplan-bundle recommended CachyLLama based on user signal, but
   that user signal is from 2026-08-03 and may have shifted.
2. Should `lb-0096` perf-claim verification run on user hardware or on CI runners?
   CI gives reproducibility but may not match real-world inference latency.
3. Does `lb-0097` fork rationale doc need a per-fork dedicated file, or can
   all rationales live in a single `docs/fork-rationale.md`?
