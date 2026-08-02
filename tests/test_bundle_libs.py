from pathlib import Path

from scripts.bundle_libs import BUNDLE_STRATEGIES, bundle_libs


def test_cpu_static_noop(tmp_path: Path) -> None:
    """CPU static strategy copies nothing."""
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "llama-server").write_text("binary")
    bundle_libs(artifact_dir, "cpu-static")
    assert list(artifact_dir.iterdir()) == [artifact_dir / "llama-server"]


def test_strategy_has_required_keys() -> None:
    for name, strategy in BUNDLE_STRATEGIES.items():
        assert "patterns" in strategy, f"{name} missing patterns"
        assert "rpath" in strategy, f"{name} missing rpath"


def test_rocm_strategy_patterns_nonempty() -> None:
    assert len(BUNDLE_STRATEGIES["rocm-therock"]["patterns"]) > 0


def test_bundle_copies_matching_files(tmp_path: Path) -> None:
    """Strategy with patterns copies matching files."""
    lib_dir = tmp_path / "libs"
    lib_dir.mkdir()
    (lib_dir / "libfoo.so.1").write_text("lib")
    (lib_dir / "libfoo.so.1.2").write_text("lib")
    (lib_dir / "libbar.so").write_text("lib")
    (lib_dir / "unrelated.txt").write_text("txt")

    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "llama-server").write_text("binary")

    # Use a custom strategy with one pattern
    from scripts.bundle_libs import bundle_libs_custom

    bundle_libs_custom(artifact_dir, lib_dir, ["libfoo.so*"])
    copied = [f.name for f in artifact_dir.iterdir()]
    assert "libfoo.so.1" in copied
    assert "libfoo.so.1.2" in copied
    assert "libbar.so" not in copied
    assert "unrelated.txt" not in copied
