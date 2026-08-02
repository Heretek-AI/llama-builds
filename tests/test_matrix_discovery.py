"""Tests for matrix discovery logic used in the CI workflow.

Validates that the Python-based METADATA parser produces a correct GitHub
Actions matrix JSON structure from the targets/ directory.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

TARGETS_DIR = Path(__file__).resolve().parent.parent / "targets"


def _discover_matrix(targets_dir: Path) -> dict:
    """Replicate the discover logic from the workflow (Python version).

    Walks targets/*/build.sh, parses METADATA headers, and returns
    a GitHub Actions matrix dict.
    """
    targets = []
    for d in sorted(os.listdir(targets_dir)):
        if d.startswith("_") or not (targets_dir / d).is_dir():
            continue
        build_sh = targets_dir / d / "build.sh"
        if not build_sh.exists():
            continue
        meta: dict[str, str] = {}
        in_metadata = False
        with open(build_sh) as f:
            for line in f:
                if line.startswith("# METADATA"):
                    in_metadata = True
                    continue
                if in_metadata:
                    match = re.match(r"^#\s+(\w+)=(.*)", line.strip())
                    if match:
                        meta[match.group(1)] = match.group(2)
                    elif not line.startswith("# "):
                        break
        if "repo" in meta and "ref" in meta and "backend" in meta:
            targets.append(
                {
                    "target": d,
                    "repo": meta["repo"],
                    "ref": meta["ref"],
                    "backend": meta["backend"],
                    "arch": meta.get("arch", "x86_64"),
                    "gpu_target": meta.get("gpu_target", ""),
                    "name": meta.get("name", d),
                    "smoke_test": meta.get("smoke_test", "llama-cli --version"),
                }
            )
    return {"include": targets}


def test_matrix_includes_all_backends() -> None:
    """Matrix should contain cpu, cuda, and vulkan backend entries."""
    matrix = _discover_matrix(TARGETS_DIR)
    backends = {entry["backend"] for entry in matrix["include"]}
    assert "cpu" in backends, f"cpu backend missing; found {backends}"
    assert "cuda" in backends, f"cuda backend missing; found {backends}"
    assert "vulkan" in backends, f"vulkan backend missing; found {backends}"


def test_template_directory_excluded() -> None:
    """Directories starting with _ must not appear in the matrix."""
    matrix = _discover_matrix(TARGETS_DIR)
    targets = {entry["target"] for entry in matrix["include"]}
    for t in targets:
        assert not t.startswith("_"), f"_template target leaked into matrix: {t}"


def test_matrix_output_valid_json() -> None:
    """The discover output must be serialisable to valid JSON."""
    matrix = _discover_matrix(TARGETS_DIR)
    serialised = json.dumps(matrix)
    parsed = json.loads(serialised)
    assert "include" in parsed
    assert isinstance(parsed["include"], list)
