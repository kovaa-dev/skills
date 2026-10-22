from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile
from contextlib import closing, redirect_stdout
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "corpus.py"
SPEC = importlib.util.spec_from_file_location("doc_research_corpus", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load {SCRIPT}")
CORPUS_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CORPUS_MODULE
SPEC.loader.exec_module(CORPUS_MODULE)

from doc_research import common as COMMON_MODULE
from doc_research import index as INDEX_MODULE


def run_corpus(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *(str(arg) for arg in args)],
        check=False,
        capture_output=True,
        text=True,
    )


class CorpusCliTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        doctor = run_corpus("doctor")
        status = json.loads(doctor.stdout)
        if not status["fts5"]:
            raise unittest.SkipTest("SQLite FTS5 is unavailable")
