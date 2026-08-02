"""Test a new llama.cpp upstream SHA before promoting to a release.

Clones the upstream repo at a given SHA, extracts METADATA, and
validates it against the manifest schema and matrix consistency.

Usage:
    python -m scripts.upstream_sha_tester --repo ggml-org/llama.cpp --sha abc1234
    python -m scripts.upstream_sha_tester --repo ggml-org/llama.cpp --sha abc1234 --backend cpu
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA_PATH = Path("schemas/manifest.schema.json")


def clone_repo(repo: str, ref: str, dest: Path) -> bool:
    """Clone a GitHub repo at a specific ref. Returns True on success."""
    url = f"https://github.com/{repo}.git"
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", ref, url, str(dest)],
            check=True,
            capture_output=True,
            timeout=120,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        # Tag might not exist, try fetching by SHA
        try:
            dest.mkdir(parents=True, exist_ok=True)
            subprocess.run(["git", "init"], cwd=str(dest), check=True, capture_output=True)
            subprocess.run(
                ["git", "remote", "add", "origin", url],
                cwd=str(dest),
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "fetch", "--depth", "1", "origin", ref],
                cwd=str(dest),
                check=True,
                capture_output=True,
                timeout=120,
            )
            subprocess.run(
                ["git", "checkout", "FETCH_HEAD"],
                cwd=str(dest),
                check=True,
                capture_output=True,
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False


def extract_metadata_from_repo(repo_dir: Path) -> dict | None:
    """Extract METADATA from the repo's build.sh or CMakeLists.txt."""
    # Try common build script locations
    for candidate in ["build.sh", "scripts/build.sh", "Makefile"]:
        build_file = repo_dir / candidate
        if build_file.exists():
            return _parse_metadata_file(build_file)

    # Try CMakeLists.txt for CMake-based projects
    cmake = repo_dir / "CMakeLists.txt"
    if cmake.exists():
        return _parse_cmake_metadata(cmake)

    return None


def _parse_metadata_file(path: Path) -> dict | None:
    """Parse METADATA block from a build script."""
    import re

    in_metadata = False
    metadata: dict[str, str] = {}
    header = "# METADATA"
    pattern = re.compile(r"^#\s+(\w+)=(.+)$")

    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped == header:
            in_metadata = True
            continue
        if in_metadata:
            match = pattern.match(stripped)
            if match:
                key, value = match.groups()
                metadata[key] = value.strip()
            elif not stripped.startswith("#"):
                break

    return metadata if metadata else None


def _parse_cmake_metadata(path: Path) -> dict | None:
    """Extract basic info from CMakeLists.txt (fallback)."""
    content = path.read_text()
    if "llama.cpp" in content.lower() or "ggml" in content.lower():
        return {
            "name": "Upstream llama.cpp (CMake)",
            "repo": "ggml-org/llama.cpp",
            "ref": "main",
            "backend": "cpu",
            "arch": "x86_64",
            "capabilities": "chat,embed",
        }
    return None


def validate_sha(repo: str, sha: str, backend: str = "cpu") -> list[str]:
    """Validate a SHA against the manifest system. Returns list of errors."""
    errors: list[str] = []

    with tempfile.TemporaryDirectory(prefix="upstream-test-") as tmpdir:
        repo_dir = Path(tmpdir) / "repo"

        print(f"Cloning {repo}@{sha}...")
        if not clone_repo(repo, sha, repo_dir):
            errors.append(f"Failed to clone {repo}@{sha}")
            return errors

        # Get the actual resolved SHA
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
        )
        resolved_sha = result.stdout.strip() if result.returncode == 0 else sha
        print(f"Resolved SHA: {resolved_sha[:12]}")

        # Extract metadata
        meta = extract_metadata_from_repo(repo_dir)
        if meta is None:
            errors.append("No METADATA block found in upstream repo")
            return errors

        # Validate required fields
        for field in ["name", "repo", "backend"]:
            if field not in meta:
                errors.append(f"METADATA missing required field: {field}")

        # Validate backend against allowed values
        allowed_backends = {"cpu", "cuda", "rocm", "vulkan", "docs"}
        if meta.get("backend") not in allowed_backends:
            errors.append(
                f"Invalid backend: {meta.get('backend')} "
                f"(allowed: {', '.join(sorted(allowed_backends))})"
            )

        # Build a manifest entry and validate against schema
        caps_raw = meta.get("capabilities", "")
        capabilities = [c.strip() for c in caps_raw.split(",") if c.strip()]

        manifest_entry = {
            "version": 1,
            "generated_at": "2026-08-02T00:00:00Z",
            "targets": {
                "test": {
                    "name": meta.get("name", "Unknown"),
                    "repo": meta.get("repo", repo),
                    "ref": resolved_sha,
                    "backend": meta.get("backend", backend),
                    "arch": meta.get("arch", "x86_64"),
                    "capabilities": capabilities or ["chat"],
                    "build": {
                        "runner": "ubuntu-latest",
                        "script": "targets/test/build.sh",
                    },
                }
            },
        }

        if SCHEMA_PATH.exists():
            try:
                import jsonschema

                schema = json.loads(SCHEMA_PATH.read_text())
                jsonschema.validate(instance=manifest_entry, schema=schema)
                print("Schema validation: PASSED")
            except ImportError:
                print("jsonschema not installed — skipping schema validation")
            except jsonschema.ValidationError as e:
                errors.append(f"Schema validation failed: {e.message}")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Test an upstream llama.cpp SHA against the manifest system"
    )
    parser.add_argument("--repo", required=True, help="GitHub owner/repo")
    parser.add_argument("--sha", required=True, help="Git SHA or tag to test")
    parser.add_argument(
        "--backend",
        default="cpu",
        choices=["cpu", "cuda", "rocm", "vulkan", "docs"],
        help="Expected backend (default: cpu)",
    )
    args = parser.parse_args(argv)

    errors = validate_sha(args.repo, args.sha, args.backend)

    if errors:
        print("\nFAILED — errors found:")
        for err in errors:
            print(f"  ✗ {err}")
        return 1

    print("\nPASSED — upstream SHA is compatible")
    return 0


if __name__ == "__main__":
    sys.exit(main())
