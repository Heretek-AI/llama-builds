"""Weekly health check for tracked fork repos via GitHub API.

Checks each fork's last commit date, archival status, and health.
Writes health_report.json and optionally opens a health PR.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

TARGETS_DIR = Path("targets")
HEALTH_REPORT = Path("health_report.json")

STALE_DAYS = 90
ARCHIVED_DAYS = 180


def _github_api(path: str, token: str | None = None) -> dict | None:
    """Fetch a GitHub API endpoint. Returns dict or None on error."""
    url = f"https://api.github.com/{path}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "llama-builds-audit"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None


def check_repo_health(owner: str, repo: str, token: str | None = None) -> dict:
    """Check GitHub API for fork health metrics.

    Returns dict with last_commit_date, days_since_commit, is_archived,
    is_404, health_status.
    """
    result = {
        "repo": f"{owner}/{repo}",
        "last_commit_date": None,
        "days_since_commit": None,
        "is_archived": False,
        "is_404": False,
        "health_status": "unknown",
    }

    data = _github_api(f"repos/{owner}/{repo}", token)
    if data is None:
        result["is_404"] = True
        result["health_status"] = "not_found"
        return result

    if data.get("archived", False):
        result["is_archived"] = True
        result["health_status"] = "archived"
        return result

    pushed_at = data.get("pushed_at") or data.get("updated_at")
    if pushed_at:
        last = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
        result["last_commit_date"] = last.isoformat()
        days = (datetime.now(UTC) - last).days
        result["days_since_commit"] = days

        if days > ARCHIVED_DAYS:
            result["health_status"] = "stale"
        elif days > STALE_DAYS:
            result["health_status"] = "stale"
        else:
            result["health_status"] = "healthy"
    else:
        result["health_status"] = "unknown"

    return result


def audit_all_forks(
    targets_dir: Path = TARGETS_DIR,
    token: str | None = None,
) -> dict:
    """Audit all targets/*/build.sh repos. Returns health_report dict."""
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "targets": {},
        "summary": {"healthy": 0, "stale": 0, "archived": 0, "not_found": 0, "unknown": 0},
    }

    for target_dir in sorted(targets_dir.iterdir()):
        if not target_dir.is_dir() or target_dir.name.startswith("_"):
            continue

        build_sh = target_dir / "build.sh"
        if not build_sh.exists():
            continue

        from scripts.metadata_common import MetadataParseError, parse_metadata_raw
        try:
            raw = parse_metadata_raw(build_sh)
        except MetadataParseError:
            continue

        repo_str = raw.get("repo", "")
        if "/" not in repo_str:
            continue

        owner, repo = repo_str.split("/", 1)
        health = check_repo_health(owner, repo, token)
        report["targets"][target_dir.name] = health
        status = health["health_status"]
        if status in report["summary"]:
            report["summary"][status] += 1

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit fork health via GitHub API")
    parser.add_argument("--targets-dir", type=Path, default=TARGETS_DIR)
    parser.add_argument("--output", type=Path, default=HEALTH_REPORT)
    parser.add_argument("--dry-run", action="store_true", help="Print report, don't write file")
    parser.add_argument("--token", type=str, default=None, help="GitHub token (or GITHUB_TOKEN env)")
    args = parser.parse_args(argv)

    token = args.token or os.environ.get("GITHUB_TOKEN")
    report = audit_all_forks(args.targets_dir, token)

    if args.dry_run:
        print(json.dumps(report, indent=2))
    else:
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(f"Health report written to {args.output}")

    unhealthy = sum(1 for t in report["targets"].values() if t["health_status"] != "healthy")
    if unhealthy:
        print(f"WARNING: {unhealthy} targets unhealthy", file=sys.stderr)
        for name, info in report["targets"].items():
            if info["health_status"] != "healthy":
                print(f"  {name}: {info['health_status']}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
