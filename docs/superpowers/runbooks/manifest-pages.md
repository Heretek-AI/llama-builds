# Manifest Pages Publish Runbook

How `manifest.json` gets published to GitHub Pages and consumed by heretek-manager.

## Flow

1. A tag matching `v*` is pushed (e.g., `v1.0.0`)
2. `manifest-pages.yml` runs:
   - Generates `manifest.json` via `generate_manifest.py`
   - Validates against schema via `audit_matrix.py`
   - Redacts sensitive fields (only name/repo/ref/backend/arch/capabilities survive)
   - Uploads as a Pages artifact
3. Deploys to `https://heretek-ai.github.io/llama-builds/manifest.json`

## Consumption

`heretek-manager`'s `/api/registry` endpoint fetches the manifest from the Pages URL:

```
GET https://heretek-ai.github.io/llama-builds/manifest.json
```

## Manual trigger

To publish without a tag push:

```bash
gh workflow run manifest-pages.yml --ref main
```

## Troubleshooting

| Symptom                 | Cause                                  | Fix                                          |
| ----------------------- | -------------------------------------- | -------------------------------------------- |
| Pages deploy fails      | GitHub Pages not enabled               | Enable in repo Settings → Pages              |
| Manifest is stale       | No tag pushed since last target change | Push a new `v*` tag                          |
| Schema validation fails | Manifest doesn't match schema          | Run `python -m scripts.audit_matrix` locally |

## Security

The workflow redacts all fields except: `name`, `repo`, `ref`, `backend`, `arch`, `capabilities`. No secrets, tokens, or internal paths are included in the published manifest.
