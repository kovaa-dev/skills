from __future__ import annotations

from test_support import *


class IndexCliTest(CorpusCliTestCase):
    def test_single_file_can_be_indexed_and_incrementally_refreshed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "large-source.md"
            source.write_text(
                "# File 01\n\nPattern R_T_A_E_O_W.\n\n"
                "# File 07\n\nException pattern R_T_A_W.",
                encoding="utf-8",
            )
            database = root / "index.sqlite"

            first = run_corpus("index", source, "--db", database)
            self.assertEqual(first.returncode, 0, first.stderr)
            first_payload = json.loads(first.stdout)
            self.assertEqual(first_payload["corpus"], str(source.resolve()))
            self.assertEqual(first_payload["files_seen"], 1)

            info = json.loads(run_corpus("info", database, "--hashes").stdout)
            self.assertEqual(info["source_count"], 1)
            self.assertEqual(info["sources"][0]["path"], source.name)

            source.write_text(
                source.read_text(encoding="utf-8") + "\n\nChanged marker.",
                encoding="utf-8",
            )
            refreshed = run_corpus("index", source, "--db", database)
            self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
            refresh_payload = json.loads(refreshed.stdout)
            self.assertEqual(refresh_payload["update_strategy"], "delta-copy")
            self.assertEqual(refresh_payload["files_indexed"], 1)
            found = json.loads(run_corpus("search", database, "changed marker").stdout)
            self.assertEqual(found["result_count"], 1)
            self.assertEqual(found["results"][0]["line_start"], 7)
            self.assertEqual(found["results"][0]["line_end"], 9)

    def test_info_reports_bounded_index_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "alpha.md").write_text("# Alpha\n\nFirst passage.", encoding="utf-8")
            (corpus / "beta.txt").write_text("Second passage.", encoding="utf-8")
            database = root / "index.sqlite"

            indexed = run_corpus("index", corpus, "--db", database)
            self.assertEqual(indexed.returncode, 0, indexed.stderr)
            self.assertEqual(json.loads(indexed.stdout)["update_strategy"], "full-build")

            first = run_corpus("info", database, "--source-limit", 1)
            self.assertEqual(first.returncode, 0, first.stderr)
            payload = json.loads(first.stdout)
            self.assertEqual(payload["schema_version"], 3)
            self.assertEqual(payload["corpus"], str(corpus.resolve()))
            self.assertEqual(payload["source_count"], 2)
            self.assertEqual(payload["chunk_count"], 2)
            self.assertEqual(payload["result_count"], 1)
            self.assertTrue(payload["has_more"])
            self.assertEqual(payload["next_offset"], 1)
            self.assertNotIn("sha256", payload["sources"][0])

            with_hash = run_corpus("info", database, "--source-limit", 1, "--hashes")
            self.assertEqual(with_hash.returncode, 0, with_hash.stderr)
            self.assertEqual(len(json.loads(with_hash.stdout)["sources"][0]["sha256"]), 64)

            second = run_corpus("info", database, "--source-limit", 1, "--offset", 1)
            self.assertEqual(second.returncode, 0, second.stderr)
            continued = json.loads(second.stdout)
            self.assertEqual(continued["result_count"], 1)
            self.assertFalse(continued["has_more"])

    def test_index_refuses_missing_fingerprint_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "source.txt").write_text("Needle evidence.", encoding="utf-8")
            index = root / "index.sqlite"

            self.assertEqual(run_corpus("index", corpus, "--db", index).returncode, 0)
            with closing(sqlite3.connect(index)) as connection, connection:
                fingerprint = connection.execute(
                    "SELECT value FROM metadata WHERE key = 'index_fingerprint'"
                ).fetchone()[0]
                self.assertRegex(fingerprint, r"^[0-9a-f]{64}$")
                connection.execute(
                    "DELETE FROM metadata WHERE key = 'index_fingerprint'"
                )

            searched = run_corpus("search", index, "needle")
            self.assertEqual(searched.returncode, 2)
            self.assertIn("unsupported or incomplete", searched.stderr)

            indexed = run_corpus("index", corpus, "--db", index)
            self.assertEqual(indexed.returncode, 2)
            self.assertIn("unsupported or incomplete", indexed.stderr)
            with closing(sqlite3.connect(index)) as connection:
                restored = connection.execute(
                    "SELECT value FROM metadata WHERE key = 'index_fingerprint'"
                ).fetchone()
            self.assertIsNone(restored)
            self.assertRegex(fingerprint, r"^[0-9a-f]{64}$")

    def test_index_refuses_foreign_database_without_changing_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "source.txt").write_text("Evidence.", encoding="utf-8")
            database = root / "foreign.sqlite"
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.execute("CREATE TABLE chunks(value TEXT)")
                connection.execute("INSERT INTO chunks VALUES ('keep me')")

            result = run_corpus("index", corpus, "--db", database)
            self.assertEqual(result.returncode, 2)
            self.assertIn("not a corpus index", result.stderr)
            with closing(sqlite3.connect(database)) as connection:
                self.assertEqual(
                    connection.execute("SELECT value FROM chunks").fetchone()[0],
                    "keep me",
                )

    def test_index_refuses_unidentified_schema_shaped_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "source.txt").write_text("Evidence.", encoding="utf-8")
            database = root / "foreign.sqlite"
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.execute(
                    """
                    CREATE TABLE sources (
                        path TEXT PRIMARY KEY,
                        sha256 TEXT NOT NULL,
                        indexed_at TEXT NOT NULL,
                        chunk_count INTEGER NOT NULL
                    )
                    """
                )
                connection.execute(
                    "CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
                )
                connection.execute(
                    """
                    CREATE VIRTUAL TABLE chunks USING fts5(
                        source_path UNINDEXED, source, source_hash UNINDEXED,
                        page UNINDEXED, section, version UNINDEXED, date UNINDEXED,
                        context, text, tokenize = 'unicode61'
                    )
                    """
                )
                connection.execute(
                    "INSERT INTO chunks(source_path, source, source_hash, text) "
                    "VALUES ('foreign', 'foreign', 'hash', 'keep me')"
                )

            result = run_corpus("index", corpus, "--db", database)
            self.assertEqual(result.returncode, 2)
            self.assertIn("application identifier", result.stderr)
            with closing(sqlite3.connect(database)) as connection:
                self.assertEqual(
                    connection.execute("SELECT text FROM chunks").fetchone()[0],
                    "keep me",
                )

    @unittest.skipIf(os.name == "nt", "POSIX permission bits are unavailable on Windows")
    def test_new_index_is_private_on_posix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "source.txt").write_text("Private evidence.", encoding="utf-8")
            database = root / "index.sqlite"

            indexed = run_corpus("index", corpus, "--db", database)
            self.assertEqual(indexed.returncode, 0, indexed.stderr)
            self.assertEqual(database.stat().st_mode & 0o777, 0o600)

    def test_rebuild_removes_deleted_text_from_database_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            secret = b"UNIQUE_REMOVED_SECRET_7319"
            removable = corpus / "remove.txt"
            removable.write_bytes(secret)
            (corpus / "keep.txt").write_text("Retained evidence.", encoding="utf-8")
            database = root / "index.sqlite"
            self.assertEqual(run_corpus("index", corpus, "--db", database).returncode, 0)
            self.assertIn(secret, database.read_bytes())

            removable.unlink()
            rebuilt = run_corpus("index", corpus, "--db", database)
            self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)
            self.assertNotIn(secret, database.read_bytes())
            self.assertEqual(
                json.loads(run_corpus("search", database, "UNIQUE_REMOVED_SECRET_7319").stdout)[
                    "result_count"
                ],
                0,
            )

    def test_source_change_during_index_keeps_previous_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            source = corpus / "source.txt"
            source.write_text("Stable evidence.", encoding="utf-8")
            database = root / "index.sqlite"
            self.assertEqual(run_corpus("index", corpus, "--db", database).returncode, 0)
            source.write_text("Candidate evidence.", encoding="utf-8")

            original = INDEX_MODULE.chunks_from_text

            def mutating_chunks(*args: object, **kwargs: object):
                yield from original(*args, **kwargs)
                source.write_text("Concurrent mutation.", encoding="utf-8")

            args = argparse.Namespace(
                corpus=corpus,
                db=database,
                max_chars=3500,
                max_source_bytes=COMMON_MODULE.DEFAULT_MAX_SOURCE_BYTES,
                max_corpus_bytes=COMMON_MODULE.DEFAULT_MAX_CORPUS_BYTES,
            )
            with mock.patch.object(INDEX_MODULE, "chunks_from_text", mutating_chunks):
                with self.assertRaisesRegex(ValueError, "changed during indexing"):
                    with redirect_stdout(io.StringIO()):
                        INDEX_MODULE.command_index(args)

            retained = json.loads(run_corpus("search", database, "stable").stdout)
            self.assertEqual(retained["result_count"], 1)
            self.assertEqual(
                json.loads(run_corpus("search", database, "concurrent").stdout)[
                    "result_count"
                ],
                0,
            )

    def test_index_refuses_partial_owned_schema_without_repairing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "source.txt").write_text("Recoverable evidence.", encoding="utf-8")
            database = root / "index.sqlite"
            self.assertEqual(run_corpus("index", corpus, "--db", database).returncode, 0)
            with closing(sqlite3.connect(database)) as connection, connection:
                connection.execute("DROP TABLE chunks")

            refused = run_corpus("index", corpus, "--db", database)
            self.assertEqual(refused.returncode, 2)
            self.assertIn("unsupported or incomplete", refused.stderr)
            with closing(sqlite3.connect(database)) as connection:
                self.assertIsNone(
                    connection.execute(
                        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'chunks'"
                    ).fetchone()
                )

    def test_index_skips_symlinked_files_outside_the_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            outside = root / "outside.txt"
            outside.write_text("Private material.", encoding="utf-8")
            link = corpus / "linked.txt"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("File symlinks are unavailable")
            database = root / "index.sqlite"

            indexed = run_corpus("index", corpus, "--db", database)
            self.assertEqual(indexed.returncode, 0, indexed.stderr)
            self.assertEqual(json.loads(indexed.stdout)["files_seen"], 0)

    def test_index_refuses_to_rebind_a_database_to_another_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first"
            second = root / "second"
            first.mkdir()
            second.mkdir()
            (first / "one.txt").write_text("First corpus.", encoding="utf-8")
            (second / "two.txt").write_text("Second corpus.", encoding="utf-8")
            database = root / "index.sqlite"
            self.assertEqual(run_corpus("index", first, "--db", database).returncode, 0)

            rebound = run_corpus("index", second, "--db", database)
            self.assertEqual(rebound.returncode, 2)
            self.assertIn("another corpus", rebound.stderr)
            found = json.loads(run_corpus("search", database, "first").stdout)
            self.assertEqual(found["result_count"], 1)

    def test_index_does_not_ingest_its_own_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            corpus = Path(directory)
            (corpus / "source.txt").write_text("Stable evidence.", encoding="utf-8")
            database = corpus / "index.jsonl"

            first = run_corpus("index", corpus, "--db", database)
            self.assertEqual(first.returncode, 0, first.stderr)
            second = run_corpus("index", corpus, "--db", database)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(second.stdout)["files_seen"], 1)

    def test_invalid_utf8_is_rejected_instead_of_silently_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            corpus = Path(directory)
            (corpus / "invalid.txt").write_bytes(b"valid\xffinvalid")

            indexed = run_corpus("index", corpus, "--db", corpus / "index.sqlite")
            self.assertEqual(indexed.returncode, 2)
            self.assertIn("can't decode byte", indexed.stderr)

    def test_failed_update_keeps_the_last_valid_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            source = corpus / "source.txt"
            source.write_text("Stable evidence.", encoding="utf-8")
            database = root / "index.sqlite"
            self.assertEqual(run_corpus("index", corpus, "--db", database).returncode, 0)

            source.write_bytes(b"broken\xffsource")
            failed = run_corpus("index", corpus, "--db", database)
            self.assertEqual(failed.returncode, 2)
            retained = json.loads(run_corpus("search", database, "stable").stdout)
            self.assertEqual(retained["result_count"], 1)
    def test_incremental_index_updates_and_removes_sources(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            changed = corpus / "changed.txt"
            removed = corpus / "removed.txt"
            unchanged = corpus / "unchanged.txt"
            changed.write_text("Old wording.", encoding="utf-8")
            removed.write_text("Delete this.", encoding="utf-8")
            unchanged.write_text("Keep this passage.", encoding="utf-8")
            database = root / "index.sqlite"
            self.assertEqual(run_corpus("index", corpus, "--db", database).returncode, 0)
            with closing(sqlite3.connect(database)) as connection:
                unchanged_rowid = connection.execute(
                    "SELECT rowid FROM chunks WHERE source_path = 'unchanged.txt'"
                ).fetchone()[0]

            changed.write_text("New wording.", encoding="utf-8")
            removed.unlink()
            updated = run_corpus("index", corpus, "--db", database)
            self.assertEqual(updated.returncode, 0, updated.stderr)
            summary = json.loads(updated.stdout)
            self.assertEqual(summary["files_indexed"], 1)
            self.assertEqual(summary["files_unchanged"], 1)
            self.assertEqual(summary["files_removed"], 1)
            self.assertEqual(summary["update_strategy"], "delta-copy")
            with closing(sqlite3.connect(database)) as connection:
                retained_rowid = connection.execute(
                    "SELECT rowid FROM chunks WHERE source_path = 'unchanged.txt'"
                ).fetchone()[0]
                self.assertEqual(
                    connection.execute("PRAGMA quick_check").fetchone()[0], "ok"
                )
                self.assertEqual(
                    connection.execute("PRAGMA journal_mode").fetchone()[0], "delete"
                )
            self.assertEqual(retained_rowid, unchanged_rowid)
            self.assertEqual(
                json.loads(run_corpus("search", database, "new").stdout)["result_count"],
                1,
            )
            self.assertEqual(
                json.loads(run_corpus("search", database, "delete").stdout)["result_count"],
                0,
            )

    def test_index_does_not_trust_size_and_mtime_as_content_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            source = corpus / "source.txt"
            source.write_text("alpha", encoding="utf-8")
            database = root / "index.sqlite"
            self.assertEqual(run_corpus("index", corpus, "--db", database).returncode, 0)

            original = source.stat()
            source.write_text("bravo", encoding="utf-8")
            os.utime(source, ns=(original.st_atime_ns, original.st_mtime_ns))
            restored = source.stat()
            if restored.st_mtime_ns != original.st_mtime_ns:
                self.skipTest("Filesystem cannot restore nanosecond mtime")

            updated = run_corpus("index", corpus, "--db", database)
            self.assertEqual(updated.returncode, 0, updated.stderr)
            summary = json.loads(updated.stdout)
            self.assertEqual(summary["files_indexed"], 1)
            self.assertEqual(summary["update_strategy"], "delta-copy")
            self.assertEqual(
                json.loads(run_corpus("search", database, "bravo").stdout)["result_count"],
                1,
            )
            self.assertEqual(
                json.loads(run_corpus("search", database, "alpha").stdout)["result_count"],
                0,
            )

    def test_empty_corpus_does_not_clear_an_existing_index(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            source = corpus / "source.txt"
            source.write_text("Retained evidence.", encoding="utf-8")
            database = root / "index.sqlite"
            self.assertEqual(run_corpus("index", corpus, "--db", database).returncode, 0)

            source.unlink()
            refused = run_corpus("index", corpus, "--db", database)
            self.assertEqual(refused.returncode, 2)
            self.assertIn("refusing to clear", refused.stderr)
            retained = json.loads(run_corpus("search", database, "retained").stdout)
            self.assertEqual(retained["result_count"], 1)
