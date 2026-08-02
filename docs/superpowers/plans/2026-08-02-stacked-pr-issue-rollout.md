# llama-builds Stacked-PR Rollout Plan

**Goal:** Convert 35 open issues into a mergeable, TDD-driven stack of PRs that land the CI/build tooling (PR1), validate it on real upstream packages (PR2-3), then fan out parallel packaging PRs for the remaining 28 issues. Hardware-deferred issues get `status/deferred-hardware` label and a follow-up tracking issue.

**Date:** 2026-08-02 · **Mode:** ultrawork-ready, stacked-PR

---

## 0. Repository state snapshot (must reconcile before PR1)

| Item                                                      | State                                                     | Action                                                               |
| --------------------------------------------------------- | --------------------------------------------------------- | -------------------------------------------------------------------- |
| `feat/ci-matrix-workflow`                                 | 1 commit ahead of `main` (`9c7fe77` docs)                 | Land into `main` first (separate cleanup PR)                         |
| `scripts/lib/cli`                                         | Referenced by `init-harness.sh`, absent                   | Vendor or stub before PR1 ships                                      |
| `schemas/manifest.schema.json`                            | Referenced by codegen skill, absent                       | Land in PR1                                                          |
| `scripts/generate_manifest.py`, `scripts/audit_matrix.py` | Referenced, absent                                        | Land in PR1                                                          |
| `targets/`, `src/`, `tests/`                              | Absent                                                    | Scaffold empty + gitkeep in PR1                                      |
| `sonarcloud.yml` action pins (`@v4`/`@v5`)                | Out of step with `@v7` elsewhere                          | Migrate in its own micro-PR **before** PR1                           |
| Working tree                                              | `.mcp.json` deleted, `.omc/`, `.docs/`, `.omc/` untracked | Commit `.mcp.json` deletion; gitignore `.omc/`, `.omo/`; add `docs/` |

---

## 1. PR stacking — full order with rationale

### Micro-PR 0: `chore/ci/sonarcloud-action-bump`

**Issue:** none (housekeeping) · **Risk:** low
**Why:** sonarcloud.yml still on `@v4`/`@v5`; mixing with feature work conflates risk.
**Commits:** 1 atomic commit `ci: bump sonarcloud actions to v7`.
**Acceptance:** sonarcloud.yml uses `actions/checkout@v7`, `actions/setup-python@v7`; CI green.

---

### Micro-PR 0.5: `chore/repo/state-cleanup`

**Issue:** none · **Risk:** low
**Why:** Working-tree dirt blocks clean stacked-PR diffs.
**Commits:** 2 atomic — `chore: remove stale .mcp.json` + `chore: track docs/ and scaffold scripts/tests/src/targets/schemas directories`.
**Acceptance:** Clean working tree; `.gitignore` covers `.omc/`, `.omo/`, `dist/`, `*.egg-info/`.

---

### PR 1: `feat/ci/manifest-foundation` (THE FOUNDATION)

**Issues closed:** `#3 #2 #5 #6 #35 #36` · **Risk:** medium-high (touches CI + skills + docs)
**Blocks:** PR2, PR3, PR4, PR5, all package PRs (P6+).
**Branch off:** `main` after M0/M0.5 merged.

**Atomic commits (TDD order):**

1. `test(schemas): add manifest.schema.json with golden fixture` — red.
2. `feat(schemas): manifest.schema.json (JSON Schema draft 2020-12)` — green; validates repo, target, backend, arch, build, manifest fields.
3. `test(scripts): unit tests for generate_manifest.py scraping targets/*/build.sh` — red.
4. `feat(scripts): generate_manifest.py with header-comment contract`.
5. `test(scripts): audit_matrix.py validates manifest vs matrix.yml + schema` — red.
6. `feat(scripts): audit_matrix.py`.
7. `feat(matrix): add empty CUDA + ROCm + Vulkan matrix entries (#2)` — `include:` clauses with `disabled: true`.
8. `chore(ci): wire GITLEAKS + super-linter + SonarCloud + pre-commit enforcement (#6)` — branch-protection config via repo settings doc.
9. `docs(README): add tracking pointer to seed file (#35)`.
10. `docs(runbooks): seed-issues.sh runbook (#36)`.

**Risks:** schema mismatch with future targets; matrix.yml discover job may mis-detect empty dirs. **Mitigation:** first `targets/cpu/build.sh` is gitkeep + header comment so discover produces a single empty entry.

**Acceptance criteria:**

- `pytest` runs and passes (`tests/` non-empty).
- `pre-commit run --all-files` green.
- `super-linter` green.
- `sonarcloud` green (sources=`src/`, tests=`tests/`).
- `betterleaks` green.
- Matrix workflow runs with 3 disabled entries (no jobs spawned).
- `generate_manifest.py` produces valid manifest against schema for an empty targets tree.
- `audit_matrix.py --matrix .github/workflows/matrix.yml --manifest manifest.json --schema schemas/manifest.schema.json` exits 0.
- README links to `docs/superpowers/runbooks/seed-issues.sh.md`.

---

### PR 2: `feat/build/upstream-baseline` (validates foundation)

**Issues closed:** `#7 #8 #9` · **Risk:** medium
**Blocks:** PR3+ (proves the pipeline). **Can run in parallel with:** PR4 (manifest publish), PR5 (build fixtures).
**Why second:** first PR to drive the matrix from "disabled" to "exercised". Validates the whole toolchain end-to-end before any fan-out.

**Atomic commits:**

1. `test(templates): snapshot test for upstream target header + build.sh contract`.
2. `feat(targets/cpu): upstream llama.cpp CPU baseline build.sh (#7)`.
3. `feat(targets/cuda): upstream llama.cpp CUDA sm_89/90a build.sh (#8)`.
4. `feat(targets/vulkan): upstream llama.cpp Vulkan build.sh (#9)`.
5. `chore(scripts): generate_manifest + audit_matrix handle new entries`.
6. `test(integration): end-to-end matrix discover→build→manifest on PR runner`.

**Acceptance:**

- 3 matrix entries enabled, run on `ubuntu-latest` (CPU), self-hosted CUDA runner (CUDA), `ubuntu-latest` (Vulkan).
- Generated `manifest.json` lists all three with real SHAs.
- `audit_matrix.py` exits 0.

**HW note:** CUDA entry requires self-hosted runner. Until then, label `ci/requires-self-hosted-cuda` and gate via `runs-on: [self-hosted, cuda]` matrix rule.

---

### PR 3: `feat/ci/manifest-pages-publish`

**Issue closed:** `#4` · **Risk:** low · **Blocks:** none (independent).
**Why early:** zero code-conflict risk; validates Pages deploy pattern ahead of artifact volume.

**Atomic commits:**

1. `test(workflow): workflow_run manifest-publish dry-run emits artifact`.
2. `feat(workflow): .github/workflows/manifest-pages.yml with upload-pages-artifact + deploy-pages`.
3. `chore(docs): Pages publish runbook`.

**Acceptance:** On tag push, `manifest.json` + per-target sub-manifests land at `https://heretek-ai.github.io/llama-builds/manifest.json`. No secrets in artifact. heretek-manager's `/api/registry` endpoint can fetch and parse the manifest.

---

### PR 4: `chore/build/cpu-fixtures`

**Issue closed:** none · **Risk:** low · **Why:** seed-target fixtures so package PRs have a contract example.

**Commits:**

1. `feat(templates): targets/_template/build.sh` — header comment contract.
2. `test(scripts): header-parser tolerates missing optional fields`.

**Acceptance:** PR5+ can copy `_template/` and fill in 1 commit per target.

---

### PR 5: `feat/tools/upstream-sha-tester`

**Issue closed:** none · **Risk:** low · **Why:** closes the loop on `heretek-upstream-sync` skill (calls audit_matrix).

**Commits:**

1. `feat(scripts): upstream_sha_tester.py drives audit_matrix.py`.
2. `test(scripts): tester rejects non-pinned SHAs`.

**Acceptance:** Skill `heretek-upstream-sync` end-to-end runnable on a sample SHA.

---

## 2. Package PRs — fan-out (parallel after PR2)

Each package gets its own PR following the same template. Labels: `type/feature`, `area/build`, `status/ready` (or `status/deferred-hardware`).

### Group A — Upstream variants (parallel, independent)

| PR  | Issue                 | Target                   | Atomic commits                                      |
| --- | --------------------- | ------------------------ | --------------------------------------------------- |
| P6  | #10 (drop dep on #11) | `ikawrakow/ik_llama.cpp` | Trellis+FlashMLA tested in CI smoke (no sglang dep) |
| P7  | #11                   | `sgl-project/sglang`     | FlashInfer+Triton install                           |
| P8  | #12                   | `fewtarius/CachyLLama`   | SSD-backed KV cache test                            |
| P9  | #13                   | `croll83/llama.cpp-dgx`  | DFlash+NVFP4                                        |

### Group B — Quantization (parallel, independent)

| PR  | Issue | Target                                   | Notes                                               |
| --- | ----- | ---------------------------------------- | --------------------------------------------------- |
| P10 | #14   | lemonade-sdk/llamacpp-rocm               | **HARDWARE-DEFERRED**: needs Strix Halo ROCm runner |
| P11 | #15   | TheTom/llama-cpp-turboquant              | WHT+TCQ                                             |
| P12 | #16   | AtomicBot-ai/atomic-llama-cpp-turboquant | fork packaging                                      |
| P13 | #17   | spiritbuun/buun-llama-cpp                |                                                     |
| P14 | #18   | huawei-csl/KVarN                         | Hadamard+variance normalization                     |
| P15 | #19   | carlosfundora/llama.cpp-1-bit-turbo      | **HARDWARE-DEFERRED**: RDNA2 gfx1030                |
| P16 | #20   | artalis-io/bitnet.c                      | 1-bit/ternary                                       |
| P17 | #21   | NVIDIA-Merlin/HierarchicalKV             |                                                     |

### Group C — Bindings (parallel, independent)

| PR   | Issue                 | Target                               | Notes                            |
| ---- | --------------------- | ------------------------------------ | -------------------------------- |
| P18  | #22 (drop dep on #11) | abetlen/llama-cpp-python             | cibuildwheel manylinux+musllinux |
| P19  | #23                   | shakfu/cyllama                       | Cython                           |
| P20a | #24a                  | go-skynet/go-llama.cpp               | sibling PR (split from #24)      |
| P20b | #24b                  | gotzmann/llama.go                    | sibling PR (split from #24)      |
| P20c | #24c                  | hybridgroup/yzma                     | sibling PR (split from #24)      |
| P21  | #25                   | SciSharp/LLamaSharp                  | .NET                             |
| P22  | #26                   | Cypheros-de/Delphi11LlamaCppBindings | Delphi                           |
| P23  | #27                   | mgonzs13/llama_ros                   | ROS 2 Humble/Iron                |

### Group D — Frontends (parallel, independent)

| PR  | Issue | Target                                                                         |
| --- | ----- | ------------------------------------------------------------------------------ |
| P24 | #28   | hiyouga/LlamaFactory UI                                                        |
| P25 | #29   | mostlygeek/llama-swap                                                          |
| P26 | #30   | intentee/paddler                                                               |
| P27 | #31   | containers/ramalama OCI runtime                                                |
| P28 | #32   | onicai/llama_cpp_canister (Wasm)                                               |
| P29 | #33   | Lychee-Technology/llama-cpp-for-strix-halo — **HARDWARE-DEFERRED**: TTM unlock |
| P30 | #34   | GetNyrex/strix-halo-guide docs automation                                      |

**Common package-PR commit template (5 commits, all required):**

1. `test(targets): snapshot test for new target's manifest entry` — red.
2. `feat(targets/<name>): build.sh with full header contract`.
3. `feat(manifest): regenerate with new entry`.
4. `test(audit): audit_matrix accepts entry`.
5. `docs(readme): add entry to packages table`.

---

## 3. Dependency graph (text)

```
M0 (sonar bump) ──► M0.5 (cleanup) ──► PR1 (foundation) ──► PR2 (baseline) ──► P6..P30 (parallel)
                                          │                  │
                                          ├──► PR3 (Pages)  ├──► P5 (upstream tester)
                                          └──► PR4 (template)
```

- **PR1** is the hard gate. Nothing else can land before it.
- **PR2** validates the toolchain end-to-end. Package PRs should not start until PR2 builds successfully.
- **PR3, PR4, PR5** are independent and may ship in any order after PR1; merge before PR2 to keep PR2's verification surface minimal.
- **P6..P30** are all leaf nodes — no inter-package deps. Safe to parallelize across workers / forks.

---

## 4. Risk register (per PR)

| PR            | Top risk                                        | Mitigation                                                         |
| ------------- | ----------------------------------------------- | ------------------------------------------------------------------ |
| M0            | sonar action upgrade silently breaks scan       | Re-run baseline scan before/after                                  |
| M0.5          | gitignore mistakes commit `.omc/`               | `git check-ignore` before add; exclude harness state explicitly    |
| PR1           | schema under-spec'd → future targets break      | Add `additionalProperties: false`; require new schema version bump |
| PR1           | matrix.yml discover job mis-fires on empty dirs | Add gitkeep + `_disabled` marker convention                        |
| PR2           | CUDA self-hosted runner unavailable             | Gate with `runs-on: [self-hosted, cuda]` + soft-fail annotation    |
| PR3           | Pages artifact contains secret metadata         | Pre-upload redaction step; allowlist of fields                     |
| P6, P22       | Suspect seed-deps on #11 cause confusion        | Drop dep in PR body; comment on #10 + #22                          |
| P10, P15, P29 | No hardware in CI                               | `status/deferred-hardware` label + standalone tracking issue       |
| P20           | Three packages in one PR (size)                 | Split into three sibling PRs                                       |

---

## 5. Hardware deferral list (label `status/deferred-hardware`)

| Issue | Target                                                  | Why deferred                               | Follow-up                                                            |
| ----- | ------------------------------------------------------- | ------------------------------------------ | -------------------------------------------------------------------- |
| #14   | lemonade-sdk/llamacpp-rocm (Strix Halo ROCm)            | Strix Halo / gfx1151 not in CI runner pool | Open tracking issue: provision self-hosted Strix Halo runner via ARC |
| #19   | carlosfundora/llama.cpp-1-bit-turbo (RDNA2 gfx1030)     | RDNA2 not in CI runner pool                | Same ARC tracking issue; partition by accelerator label              |
| #33   | Lychee-Technology/llama-cpp-for-strix-halo (TTM unlock) | Requires Strix Halo + TTM hardware path    | Same ARC tracking issue                                              |

**Label convention:** `status/deferred-hardware` + `ci/needs-self-hosted-runner`. Deferral PRs contain the `build.sh` and manifest entry but the matrix entry is gated with `if: false` until the runner pool is provisioned.

---

## 6. Acceptance criteria — global

Every PR in the stack must independently satisfy all of:

1. `pre-commit run --all-files` → exit 0
2. `ruff check .` + `ruff format --check .` → exit 0
3. `pytest` → exit 0, coverage delta ≥ 0 (no regression)
4. SonarCloud quality gate → PASS
5. super-linter → green
6. betterleaks → green
7. Branch named `feat|fix|chore/<scope>`
8. Conventional Commits across all commits
9. PR body contains `Closes #<id>` (or `Issue: #<id>`)
10. No `.env`, `dist/`, `*.egg-info/`, `.omc/`, `.omo/` in diff
11. Generated `manifest.json` validates against `schemas/manifest.schema.json`
12. `audit_matrix.py` exits 0 for the resulting matrix+manifest

---

## 7. Atomic-commit strategy (universal)

Each PR's diff is decomposed into ≤10 commits, each commit:

- Is independently `git checkout`-able on top of its parent (CI green between commits when feasible — at minimum the final commit is green).
- Touches a single concern (schema, script, target, workflow, docs).
- Has a Conventional Commit subject ≤72 chars.
- Includes a `test:` commit **before** its `feat:` companion where the change has observable behavior in Python.
- May bundle `docs:` and `chore:` only when the change is trivial.

Test-before-feature rule (TDD): applied to every Python module under `heretek_builds/`, `scripts/`, and to manifest/snapshot tests. Not applied to pure YAML / shell-script / docs commits (no behavior to red-green).

---

## 8. TDD application matrix

| Surface                            | Test layer                                 | First test commit lives in |
| ---------------------------------- | ------------------------------------------ | -------------------------- |
| `schemas/manifest.schema.json`     | JSON Schema fixture tests                  | PR1                        |
| `scripts/generate_manifest.py`     | pytest unit (header parsing, error paths)  | PR1                        |
| `scripts/audit_matrix.py`          | pytest unit + golden fixtures              | PR1                        |
| `scripts/upstream_sha_tester.py`   | pytest unit                                | PR5                        |
| `targets/<name>/build.sh`          | snapshot test on generated manifest entry  | each P-PR                  |
| `.github/workflows/*.yml`          | `actionlint` + workflow_run dry-run        | PR1, PR3                   |
| Bindings (`llama-cpp-python` etc.) | packaging smoke test (wheel build)         | P18-P23                    |
| Hardware-deferred entries          | `pytest -k '<name>_disabled' returns skip` | P10/P15/P29                |

---

## 9. Suggested labels to add to `.github/labels.yml`

- `status/deferred-hardware` — color `#d93f0b`
- `status/seed-template` — color `#cccccc` (28 issues)
- `ci/needs-self-hosted-runner` — color `#fbca04`
- `area/packaging` — color `#0e8a16` (subset of `area/build`)

Open one chore PR adding these labels before PR1 lands.

---

## 10. Issue-triage work that runs in parallel with M0

- Comment on #10 and #22: "Seed-script dep on #11 (sglang) is incorrect — ik_llama.cpp and llama-cpp-python are independent C/C++ builds. Closing this dep edge."
- Comment on #14, #19, #33: "Marked `status/deferred-hardware`; gated in matrix.yml until self-hosted runner provisioned (see tracking issue #TBD)."
- Comment on #24: split into three follow-up issues (#24a go-llama.cpp, #24b llama.go, #24c yzma).

---

## 11. Rollout timeline (target)

| Day | Activity                                                                   |
| --- | -------------------------------------------------------------------------- |
| 0   | M0 + M0.5 merged                                                           |
| 1   | PR1 opened, reviews, merged                                                |
| 2   | PR3, PR4, PR5 opened (parallel)                                            |
| 3   | PR2 opened (depends on PR3 for Pages)                                      |
| 4-5 | P6..P30 opened as drafts; reviewers assigned in waves of 5                 |
| 6+  | Self-hosted runner provisioning kicks off (parallel track for #14/#19/#33) |

---

## 12. Decisions (confirmed)

1. **PR-per-package:** #24 splits into 3 sibling PRs (go-llama.cpp, llama.go, yzma).
2. **Label:** `status/deferred-hardware` — matches org convention.
3. **Manifest consumer:** `https://github.com/Heretek-AI/heretek-manager` (sibling program reads manifest via `/api/registry`). #4 (Pages publish) is MUST.

---

## 13. Summary counts

| Category                 | Count  | Notes                                                |
| ------------------------ | ------ | ---------------------------------------------------- |
| Micro-PRs (housekeeping) | 2      | M0, M0.5                                             |
| Foundation PR            | 1      | PR1 (closes 6 issues)                                |
| Validation PRs           | 2      | PR2, PR3                                             |
| Fixture/tool PRs         | 2      | PR4, PR5                                             |
| Package PRs (parallel)   | 27     | P6–P30 (P20 split into 3 siblings)                   |
| Hardware-deferred        | 3      | P10, P15, P29                                        |
| **Total PRs**            | **34** | (35 issues → 34 PRs after merges + #24 split into 3) |
