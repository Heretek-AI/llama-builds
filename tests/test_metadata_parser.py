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
