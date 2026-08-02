# seed-issues.sh Runbook

How to invoke `seed-issues.sh`, recover from partial failures, and add new repo slugs.

## Overview

`seed-issues.sh` reads a YAML seed file and creates GitHub issues via the `gh` CLI.
Re-running with the same seed is idempotent — issues are matched by a seed-id HTML
comment embedded in each issue body.

## Prerequisites

- `gh` CLI authenticated (`gh auth status`)
- `yq` for YAML parsing
- Repo clone with push access

## Basic invocation

```bash
# Seed issues for this repo
./scripts/seed-issues.sh seeds/llama-builds.yaml

# Dry-run (show what would be created)
DRY_RUN=1 ./scripts/seed-issues.sh seeds/llama-builds.yaml
```

## Seed file format

```yaml
- seed-id: lb-0001
  title: "Issue title"
  body: |
    ## Goal
    Description of what needs to happen.
  labels:
    - phase/1-ci-setup
    - component/ci
    - status/backlog
```

### Per-repo slug convention

Each seed file is named after its target repo:
- `seeds/llama-builds.yaml` → issues for `Heretek-AI/llama-builds`
- `seeds/heretek-manager.yaml` → issues for `Heretek-AI/heretek-manager`

The `seed-id` prefix matches the repo slug: `lb-` for llama-builds,
`hm-` for heretek-manager.

## Idempotency

The script embeds an HTML comment at the top of each issue body:

```html
<!-- seed-id: lb-0001 -->
```

On re-run, it checks for existing issues with this seed-id and skips creation.
This makes the script safe to run multiple times.

## Recovery from partial failure

If the script fails mid-run (network error, rate limit, etc.):

1. Check which issues were created: `gh issue list --repo Heretek-AI/llama-builds`
2. Re-run the same command — idempotency will skip already-created issues
3. For rate limits, wait and retry: `gh api rate_limit`

## Adding a new repo slug

1. Create `seeds/<repo-slug>.yaml` following the format above
2. Use the correct prefix for `seed-id` values
3. Run: `./scripts/seed-issues.sh seeds/<repo-slug>.yaml`

## Regenerating labels.yaml

If you modify labels in the seed file, regenerate the labels config:

```bash
# Extract unique labels from seed file
yq '.[].labels[]' seeds/llama-builds.yaml | sort -u
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `gh: not authenticated` | No GitHub auth | Run `gh auth login` |
| Issues created with duplicate content | Seed-id mismatch | Check HTML comment in issue body |
| Rate limit errors | Too many API calls | Wait 60s, re-run (idempotent) |
