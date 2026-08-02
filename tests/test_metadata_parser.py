from pathlib import Path
from scripts.metadata_parser import parse_metadata


def test_parse_cpu_target(tmp_path: Path) -> None:
    build_sh = tmp_path / "build.sh"
    build_sh.write_text(
        '#!/usr/bin/env bash\n'
        '# METADATA\n'
        '# name=llama.cpp upstream CPU baseline\n'
        '# repo=ggml-org/llama.cpp\n'
        '# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48\n'
        '# backend=cpu\n'
        '# arch=x86_64\n'
        '# capabilities=chat,embed\n'
        'set -euo pipefail\n'
        'echo "build"\n'
    )
    meta = parse_metadata(build_sh)
    assert meta["name"] == "llama.cpp upstream CPU baseline"
    assert meta["backend"] == "cpu"
    assert meta["arch"] == "x86_64"
    assert meta["capabilities"] == ["chat", "embed"]
    assert meta["gpu_targets"] == []
    assert meta["bundle_strategy"] == "cpu-static"


def test_parse_rocm_target(tmp_path: Path) -> None:
    build_sh = tmp_path / "build.sh"
    build_sh.write_text(
        '#!/usr/bin/env bash\n'
        '# METADATA\n'
        '# name=llama.cpp upstream ROCm baseline\n'
        '# repo=ggml-org/llama.cpp\n'
        '# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48\n'
        '# backend=rocm\n'
        '# arch=x86_64\n'
        '# gpu_targets=gfx1100,gfx1101,gfx1102,gfx1103\n'
        '# capabilities=chat,embed\n'
        '# runtime_deps=librocblas,libhipblas,libamdhip64\n'
        '# bundle_strategy=rocm-therock\n'
        'set -euo pipefail\n'
    )
    meta = parse_metadata(build_sh)
    assert meta["backend"] == "rocm"
    assert meta["gpu_targets"] == ["gfx1100", "gfx1101", "gfx1102", "gfx1103"]
    assert meta["runtime_deps"] == ["librocblas", "libhipblas", "libamdhip64"]
    assert meta["bundle_strategy"] == "rocm-therock"


def test_parse_missing_metadata_raises(tmp_path: Path) -> None:
    build_sh = tmp_path / "build.sh"
    build_sh.write_text('#!/usr/bin/env bash\necho "no metadata"\n')
    from scripts.metadata_parser import MetadataParseError
    try:
        parse_metadata(build_sh)
        assert False, "Should have raised MetadataParseError"
    except MetadataParseError:
        pass


from scripts.metadata_parser import expand_gpu_family, generate_matrix


def test_expand_gpu_family_gfx110x() -> None:
    assert expand_gpu_family("gfx110X") == ["gfx1100", "gfx1101", "gfx1102", "gfx1103"]


def test_expand_gpu_family_gfx103x() -> None:
    assert expand_gpu_family("gfx103X") == ["gfx1030", "gfx1031", "gfx1032", "gfx1034"]


def test_expand_gpu_family_gfx120x() -> None:
    assert expand_gpu_family("gfx120X") == ["gfx1200", "gfx1201"]


def test_expand_gpu_family_single() -> None:
    assert expand_gpu_family("gfx1151") == ["gfx1151"]


def test_generate_matrix_cpu_only(tmp_path: Path) -> None:
    target_dir = tmp_path / "upstream-cpu"
    target_dir.mkdir()
    (target_dir / "build.sh").write_text(
        '#!/usr/bin/env bash\n'
        '# METADATA\n'
        '# name=llama.cpp upstream CPU baseline\n'
        '# repo=ggml-org/llama.cpp\n'
        '# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48\n'
        '# backend=cpu\n'
        '# arch=x86_64\n'
        '# capabilities=chat,embed\n'
    )
    matrix = generate_matrix(tmp_path)
    assert len(matrix["include"]) == 1
    assert matrix["include"][0]["backend"] == "cpu"
    assert matrix["include"][0]["gfx_target"] is None


def test_generate_matrix_rocm_expands(tmp_path: Path) -> None:
    target_dir = tmp_path / "upstream-rocm"
    target_dir.mkdir()
    (target_dir / "build.sh").write_text(
        '#!/usr/bin/env bash\n'
        '# METADATA\n'
        '# name=llama.cpp upstream ROCm\n'
        '# repo=ggml-org/llama.cpp\n'
        '# ref=0ab9d6fed73dbc5dc8026c868cb10a6728c4ed48\n'
        '# backend=rocm\n'
        '# arch=x86_64\n'
        '# gpu_targets=gfx110X,gfx1151\n'
        '# capabilities=chat,embed\n'
        '# bundle_strategy=rocm-therock\n'
    )
    matrix = generate_matrix(tmp_path)
    # gfx110X expands to 4 + gfx1151 = 5 entries
    assert len(matrix["include"]) == 5
    gfx_targets = [e["gfx_target"] for e in matrix["include"]]
    assert "gfx1100" in gfx_targets
    assert "gfx1103" in gfx_targets
    assert "gfx1151" in gfx_targets
