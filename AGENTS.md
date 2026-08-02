# llama-builds

## Project summary
CI/CD registry for llama.cpp family builds.

## Stack & runtime targets
- Languages: Python 3.11+
- Package managers: pip, setuptools
- OS/arch: Linux x86_64
- Outputs: pre-compiled distributed bundles and/or a local CLI runtime.

## Build, test, lint, run commands
- Build: `python -m build`
- Test: `pytest`
- Lint: `ruff check .`
- Run: `python -m heretek_builds --help`
- Generate manifest: `python -m scripts.generate_manifest`
- Audit matrix: `python -m scripts.audit_matrix`

## Project structure
```
llama-builds/
├── action.yml              Composite GitHub Action for building llama.cpp forks
├── .github/
│   ├── workflows/
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── .claude/
│   ├── skills/
│   ├── settings.json
│   └── hooks/
├── targets/                Build targets (targets/*/build.sh with METADATA headers)
│   ├── _template/          Template for new targets
│   └── upstream-cpu/       First real target: llama.cpp CPU baseline
├── schemas/                JSON Schema definitions (manifest.schema.json)
├── scripts/                CI tooling
│   ├── generate_manifest.py
│   ├── audit_matrix.py
│   ├── upstream_sha_tester.py
│   └── version_tag.py      Version tag generation utility
├── tests/                  Test suite (93 tests)
├── docs/                   Design docs, specs, and runbooks
├── AGENTS.md
├── CLAUDE.md
├── manifest.json           Generated build manifest (v2)
├── sonar-project.properties
├── .pre-commit-config.yaml
└── README.md
```

## Conventions
- Code style: enforced by pre-commit + super-linter.
- Branch naming: `feat/<scope>`, `fix/<scope>`, `chore/<scope>`.
- Commit messages: Conventional Commits.
- PRs require a linked GitHub Issue (`Closes #<id>` or `Issue: #<id>`).

## Do / Don't list
- DO validate build outputs against the manifest schema.
- DO run the four required CI checks locally before pushing.
- DON'T push directly to `main`; PRs only.
- DON'T commit build artifacts or `.env` files.

## Pointer block
- GitHub Project: https://github.com/orgs/Heretek-AI/projects/1
- SonarCloud project: https://sonarcloud.io/project/overview?id=Heretek-AI_llama-builds
- Super-linter config: .github/linters/
- Skills index: `.claude/skills/manifest.json`
- Issue templates: `.github/ISSUE_TEMPLATE/`
- Spec doc: `docs/superpowers/specs/`
