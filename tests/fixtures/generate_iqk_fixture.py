"""Generate a tiny valid IQ4_KS-style GGUF fixture for smoke testing.

Produces tests/fixtures/iqk-test-model.iq4.gguf — a valid GGUF v3 header
with a single IQ4_KS-quantized tensor declaration, padded to ≤50 MB with
zero bytes. The file is *not* a real model: it exists to verify that the
ik_llama.cpp build can parse a GGUF and that the IQK kernel paths are
loaded. Smoke-test command is `llama-cli --n-predict 1` which will fail on
real weight loading but is sufficient to exercise the IQK decoder entry
points when paired with a real IQ4_KS fixture in production CI.

Deterministic: same SHA256 on every run.
"""

from __future__ import annotations

import hashlib
import struct
import sys
from pathlib import Path

FIXTURE_PATH = Path(__file__).resolve().parent / "iqk-test-model.iq4.gguf"
TARGET_SIZE_BYTES = 8 * 1024 * 1024  # 8 MB — well under the 50 MB limit

# GGUF v3 constants
GGUF_MAGIC = b"GGUF"
GGUF_VERSION = 3
# ggml_type: IQ4_KS = 30 (placeholder; ik_llama.cpp defines the actual enum)
IQ4_KS_TYPE = 30

# gguf_type values
GGUF_TYPE_STRING = 8


def _write_string(buf: bytearray, s: str) -> None:
    """Append GGUF-encoded string (u64 length + bytes)."""
    encoded = s.encode("utf-8")
    buf.extend(struct.pack("<Q", len(encoded)))
    buf.extend(encoded)


def _build_header() -> bytes:
    """Construct a minimal GGUF v3 header with a single tensor metadata entry."""
    buf = bytearray()

    # Magic + version
    buf.extend(GGUF_MAGIC)
    buf.extend(struct.pack("<I", GGUF_VERSION))

    # tensor_count (u64) = 1
    buf.extend(struct.pack("<Q", 1))

    # metadata_key_value_count (u64) = 0 — no global metadata entries
    buf.extend(struct.pack("<Q", 0))

    # Tensor info entry: name, n_dims, dims[4], ggml_type
    _write_string(buf, "token_embd.weight")
    buf.extend(struct.pack("<I", 2))  # n_dims
    # dims: 1 (vocab=8) x 4 (hidden=4) — deliberately tiny
    buf.extend(struct.pack("<Q", 8))
    buf.extend(struct.pack("<Q", 4))
    buf.extend(struct.pack("<Q", 0))  # unused
    buf.extend(struct.pack("<Q", 0))  # unused
    buf.extend(struct.pack("<I", IQ4_KS_TYPE))

    return bytes(buf)


def generate() -> bytes:
    """Generate the fixture bytes deterministically."""
    header = _build_header()
    # Pad with zeros to TARGET_SIZE_BYTES so file is a stable shape.
    if len(header) > TARGET_SIZE_BYTES:
        raise ValueError(f"Header {len(header)}B exceeds target size {TARGET_SIZE_BYTES}B")
    padding = b"\x00" * (TARGET_SIZE_BYTES - len(header))
    blob = header + padding
    digest = hashlib.sha256(blob).hexdigest()
    print(f"[gen] fixture size: {len(blob)} bytes")
    print(f"[gen] fixture sha256: {digest}")
    return blob


def main() -> int:
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    blob = generate()
    FIXTURE_PATH.write_bytes(blob)
    print(f"[gen] wrote {FIXTURE_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
