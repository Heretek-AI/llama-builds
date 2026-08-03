"""Tests for the IQK smoke test wiring on ik_llama.cpp targets.

Validates the lb-0094 acceptance criteria:
  - tests/fixtures/iqk-test-model.iq4.gguf exists and is <=50MB
  - ik-llama-cpp METADATA smoke_test references the fixture and --n-predict 1
  - ik-llama-cpp-cuda METADATA smoke_test references the fixture and --n-predict 1
  - .github/workflows/iqk-smoke-test.yml exists, triggers on PR + push to main,
    and runs llama-cli with --n-predict 1
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "iqk-test-model.iq4.gguf"
GGUF_MAGIC = b"GGUF"
MAX_FIXTURE_BYTES = 50 * 1024 * 1024  # 50 MB


def _read_metadata_block(build_sh: Path) -> dict[str, str]:
    """Minimal METADATA extractor (matches scripts/generate_manifest.py shape)."""
    metadata: dict[str, str] = {}
    in_metadata = False
    for line in build_sh.read_text().splitlines():
        stripped = line.strip()
        if stripped == "# METADATA":
            in_metadata = True
            continue
        if in_metadata:
            match = re.match(r"^#\s+(\w+)=(.+)$", stripped)
            if match:
                key, value = match.groups()
                metadata[key] = value.strip()
            elif stripped and not stripped.startswith("#"):
                break
    return metadata


class TestIqkFixture:
    """Acceptance criterion: tests/fixtures/iqk-test-model.iq4.gguf <=50MB."""

    def test_fixture_exists(self):
        assert FIXTURE_PATH.exists(), (
            f"IQK fixture missing at {FIXTURE_PATH}. "
            "Run `python tests/fixtures/generate_iqk_fixture.py` to create it."
        )

    def test_fixture_under_size_limit(self):
        assert FIXTURE_PATH.exists(), "Fixture must exist before size check"
        size = FIXTURE_PATH.stat().st_size
        assert size <= MAX_FIXTURE_BYTES, (
            f"Fixture is {size} bytes, max allowed is {MAX_FIXTURE_BYTES} (50MB)"
        )

    def test_fixture_has_gguf_magic(self):
        assert FIXTURE_PATH.exists(), "Fixture must exist before magic check"
        with FIXTURE_PATH.open("rb") as f:
            header = f.read(4)
        assert header == GGUF_MAGIC, f"IQK fixture must start with GGUF magic bytes, got {header!r}"


class TestIqkSmokeTestMetadata:
    """Acceptance: METADATA smoke_test references the fixture and --n-predict 1."""

    def test_cpu_target_smoke_test_references_fixture(self):
        build_sh = REPO_ROOT / "targets" / "ik-llama-cpp" / "build.sh"
        assert build_sh.exists(), f"Missing {build_sh}"
        meta = _read_metadata_block(build_sh)
        smoke = meta.get("smoke_test", "")
        assert "iqk-test-model.iq4.gguf" in smoke, (
            f"ik-llama-cpu smoke_test must reference the IQK fixture, got: {smoke!r}"
        )
        assert "--n-predict 1" in smoke, f"smoke_test must include --n-predict 1, got: {smoke!r}"

    def test_cuda_target_smoke_test_references_fixture(self):
        build_sh = REPO_ROOT / "targets" / "ik-llama-cpp-cuda" / "build.sh"
        assert build_sh.exists(), f"Missing {build_sh}"
        meta = _read_metadata_block(build_sh)
        smoke = meta.get("smoke_test", "")
        assert "iqk-test-model.iq4.gguf" in smoke, (
            f"ik-llama-cuda smoke_test must reference the IQK fixture, got: {smoke!r}"
        )
        assert "--n-predict 1" in smoke, f"smoke_test must include --n-predict 1, got: {smoke!r}"


class TestIqkSmokeTestWorkflow:
    """Acceptance: .github/workflows/iqk-smoke-test.yml triggers on PR + push, runs llama-cli."""

    WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "iqk-smoke-test.yml"

    def test_workflow_exists(self):
        assert self.WORKFLOW_PATH.exists(), (
            f"Missing IQK smoke test workflow at {self.WORKFLOW_PATH}"
        )

    def test_workflow_triggers_on_pull_request(self):
        text = self.WORKFLOW_PATH.read_text()
        assert re.search(r"^\s*pull_request:", text, re.MULTILINE), (
            "Workflow must trigger on pull_request"
        )

    def test_workflow_triggers_on_push_main(self):
        text = self.WORKFLOW_PATH.read_text()
        # Accept either top-level push, or nested under `on:`
        assert re.search(r"^\s*push:", text, re.MULTILINE), "Workflow must trigger on push"
        assert re.search(r"branches:\s*\[\s*main\s*\]", text), (
            "Workflow push trigger must target main branch"
        )

    def test_workflow_runs_llama_cli_n_predict_one(self):
        text = self.WORKFLOW_PATH.read_text()
        assert "llama-cli" in text or "llama-server" in text, (
            "Workflow must invoke llama-cli or llama-server"
        )
        assert "--n-predict 1" in text or "--n-predict=1" in text, (
            "Workflow must pass --n-predict 1 to exercise the IQK decode path"
        )
