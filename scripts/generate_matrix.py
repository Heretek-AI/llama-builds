#!/usr/bin/env python3
"""Generate GitHub Actions build matrix from target METADATA."""

import json
import sys
from pathlib import Path

# Allow running from repo root: python scripts/generate_matrix.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.metadata_parser import generate_matrix

targets_dir = Path("targets")
matrix = generate_matrix(targets_dir)

# Write to file for workflow to consume
Path("matrix.json").write_text(json.dumps(matrix))
print(json.dumps(matrix, indent=2))
