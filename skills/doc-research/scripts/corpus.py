#!/usr/bin/env python3
"""Stable command-line entrypoint for the doc-research corpus helper."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIRECTORY = Path(__file__).resolve().parent
if str(SCRIPT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIRECTORY))

from doc_research.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
