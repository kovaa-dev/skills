from __future__ import annotations

from test_support import *


class IngestionCliTest(CorpusCliTestCase):
    def test_import_docling_normalizes_metadata_and_protects_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "contract.chunks.jsonl"
            output = root / "normalized" / "contract.jsonl"
            records = [
                {
                    "filename": "contract.pdf",
                    "text": "Terms\nTermination\nTermination requires notice.",
                    "raw_text": "Termination requires notice.\nDays | Notice\n30 | Written",
                    "headings": ["Terms", "Termination"],
                    "captions": ["Table 2"],
                    "page_numbers": [12, 13],
                    "metadata": {"origin": {"filename": "contract.pdf"}},
                },
                {
                    "filename": "contract.pdf",
                    "text": "The notice period is thirty days.",
                    "headings": ["Terms"],
                    "page_numbers": [14],
                },
            ]
            source.write_text(
                "".join(json.dumps(record) + "\n" for record in records),
                encoding="utf-8",
            )

            converted = run_corpus(
                "import-docling",
                source,
                "--output",
                output,
                "--source",
                "canonical/contract.pdf",
                "--version",
                "v3",
                "--date",
                "2026-09-30",
                "--source-sha256",
                "a" * 64,
            )
            self.assertEqual(converted.returncode, 0, converted.stderr)
            summary = json.loads(converted.stdout)
            self.assertEqual(summary["records_written"], 2)

            normalized = [
                json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(normalized[0]["source"], "canonical/contract.pdf")
            self.assertEqual(normalized[0]["page"], "12,13")
            self.assertEqual(normalized[0]["section"], "Terms > Termination")
            self.assertEqual(normalized[0]["context"], "Table 2")
            self.assertEqual(
                normalized[0]["text"],
                "Termination requires notice.\nDays | Notice\n30 | Written",
            )
            self.assertEqual(normalized[0]["version"], "v3")
            self.assertEqual(normalized[0]["date"], "2026-09-30")
            self.assertEqual(normalized[0]["source_hash"], "a" * 64)

            database = root / "index.sqlite"
            indexed = run_corpus("index", output.parent, "--db", database)
            self.assertEqual(indexed.returncode, 0, indexed.stderr)
            searched = json.loads(
                run_corpus("search", database, "table", "--page", 12).stdout
            )
            self.assertEqual(searched["result_count"], 1)
            retrieved = json.loads(
                run_corpus("get", database, searched["results"][0]["passage_id"]).stdout
            )
            self.assertEqual(
                retrieved["results"][0]["text"],
                "Termination requires notice.\nDays | Notice\n30 | Written",
            )
            self.assertEqual(retrieved["results"][0]["source_hash"], "a" * 64)

            protected = run_corpus("import-docling", source, "--output", output)
            self.assertEqual(protected.returncode, 2)
            self.assertIn("already exists", protected.stderr)

    def test_index_and_compare_enforce_resource_limits(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            source = corpus / "source.txt"
            source.write_text("0123456789", encoding="utf-8")
            database = root / "index.sqlite"

            oversized = run_corpus(
                "index", corpus, "--db", database, "--max-source-bytes", 5
            )
            self.assertEqual(oversized.returncode, 2)
            self.assertIn("exceeds --max-source-bytes", oversized.stderr)
            self.assertFalse(database.exists())

            (corpus / "second.txt").write_text("abcde", encoding="utf-8")
            oversized_corpus = run_corpus(
                "index",
                corpus,
                "--db",
                database,
                "--max-source-bytes",
                20,
                "--max-corpus-bytes",
                14,
            )
            self.assertEqual(oversized_corpus.returncode, 2)
            self.assertIn("exceeds --max-corpus-bytes", oversized_corpus.stderr)
            self.assertFalse(database.exists())

            left = root / "left.txt"
            right = root / "right.txt"
            left.write_text("one\n\ntwo", encoding="utf-8")
            right.write_text("one\n\nthree", encoding="utf-8")
            too_many = run_corpus("compare", left, right, "--max-units", 1)
            self.assertEqual(too_many.returncode, 2)
            self.assertIn("exceeds --max-units", too_many.stderr)

    def test_compare_bounds_the_diff_while_generating_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            left = root / "left.txt"
            right = root / "right.txt"
            left.write_text(
                "\n\n".join(f"Before {number}" for number in range(30)), encoding="utf-8"
            )
            right.write_text(
                "\n\n".join(f"After {number}" for number in range(30)), encoding="utf-8"
            )

            compared = run_corpus(
                "compare", left, right, "--context-lines", 0, "--max-total-chars", 100
            )
            self.assertEqual(compared.returncode, 0, compared.stderr)
            payload = json.loads(compared.stdout)
            self.assertTrue(payload["diff_truncated"])
            self.assertLessEqual(len(payload["diff"]), 100)

    def test_extract_zip_rejects_traversal_and_writes_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            safe_archive = root / "safe.zip"
            with zipfile.ZipFile(safe_archive, "w") as archive:
                archive.writestr("docs/source.txt", "Needle evidence.")
            output = root / "safe-output"
            extracted = run_corpus("extract-zip", safe_archive, "--output", output)
            self.assertEqual(extracted.returncode, 0, extracted.stderr)
            self.assertEqual(
                (output / "docs" / "source.txt").read_text(encoding="utf-8"),
                "Needle evidence.",
            )
            manifest = json.loads(
                (output / ".doc-research-archive.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["file_count"], 1)

            unsafe_archive = root / "unsafe.zip"
            with zipfile.ZipFile(unsafe_archive, "w") as archive:
                archive.writestr("../escape.txt", "not allowed")
            unsafe_output = root / "unsafe-output"
            rejected = run_corpus("extract-zip", unsafe_archive, "--output", unsafe_output)
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("Unsafe archive member path", rejected.stderr)
            self.assertFalse(unsafe_output.exists())

            for name, members in (
                ("windows-alias", [("docs/report.txt:secret", "not allowed")]),
                (
                    "unicode-alias",
                    [("docs/caf\N{LATIN SMALL LETTER E WITH ACUTE}.txt", "one"),
                     ("docs/cafe\N{COMBINING ACUTE ACCENT}.txt", "two")],
                ),
            ):
                archive_path = root / f"{name}.zip"
                with zipfile.ZipFile(archive_path, "w") as archive:
                    for member, content in members:
                        archive.writestr(member, content)
                rejected_output = root / f"{name}-output"
                rejected = run_corpus(
                    "extract-zip", archive_path, "--output", rejected_output
                )
                self.assertEqual(rejected.returncode, 2)
                self.assertFalse(rejected_output.exists())

    @unittest.skipIf(os.name == "nt", "POSIX launcher test")
    def test_posix_launcher_skips_incompatible_python_and_honors_override(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first"
            second = root / "second"
            first.mkdir()
            second.mkdir()
            incompatible = first / "python3"
            incompatible.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            incompatible.chmod(0o700)
            # The compatible interpreter may exist only under a versioned name;
            # an earlier incompatible `python3` must not hide it.
            (second / "python3.10").symlink_to(Path(sys.executable))
            launcher = SCRIPT.with_name("corpus")
            environment = os.environ.copy()
            environment["PATH"] = f"{first}:{second}:/usr/bin:/bin"
            selected = subprocess.run(
                [str(launcher), "doctor", "--write-dir", root],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(selected.returncode, 0, selected.stderr)
            self.assertTrue(json.loads(selected.stdout)["python_ok"])

            environment["DOC_RESEARCH_PYTHON"] = sys.executable
            overridden = subprocess.run(
                [str(launcher), "doctor", "--write-dir", root],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(overridden.returncode, 0, overridden.stderr)
