from __future__ import annotations

from test_support import *


class ResearchResumeCliTest(CorpusCliTestCase):
    def test_non_current_database_schemas_are_rejected_without_migration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "source.txt").write_text("Evidence.", encoding="utf-8")
            index = root / "index.sqlite"
            receipts = root / "receipts.sqlite"
            research = root / "research.sqlite"
            catalog = root / "catalog.sqlite"

            self.assertEqual(run_corpus("index", corpus, "--db", index).returncode, 0)
            self.assertEqual(
                run_corpus(
                    "receipts-init", receipts, "--corpus", corpus, "--index", index
                ).returncode,
                0,
            )
            self.assertEqual(
                run_corpus(
                    "research-init", research, "--scope", "Review", "--corpus", corpus
                ).returncode,
                0,
            )
            self.assertEqual(run_corpus("catalog-init", catalog).returncode, 0)

            for database_path in (index, receipts, research, catalog):
                with closing(sqlite3.connect(database_path)) as connection, connection:
                    connection.execute("PRAGMA user_version = 0")

            commands = (
                ("index", corpus, "--db", index),
                ("receipts-info", receipts),
                ("research-info", research),
                ("catalog-info", catalog),
            )
            for command in commands:
                refused = run_corpus(*command)
                self.assertEqual(refused.returncode, 2)
                self.assertIn("unsupported or incomplete", refused.stderr)

            for database_path in (index, receipts, research, catalog):
                with closing(sqlite3.connect(database_path)) as connection:
                    self.assertEqual(
                        connection.execute("PRAGMA user_version").fetchone()[0], 0
                    )

    def test_research_apply_is_atomic_and_resume_is_compact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "source.txt").write_text("Needle evidence.", encoding="utf-8")
            index = root / "index.sqlite"
            state = root / "research.sqlite"
            receipts = root / "receipts.sqlite"
            delta = root / "delta.json"
            self.assertEqual(run_corpus("index", corpus, "--db", index).returncode, 0)
            self.assertEqual(
                run_corpus(
                    "research-init",
                    state,
                    "--scope",
                    "Review",
                    "--corpus",
                    corpus,
                    "--index",
                    index,
                ).returncode,
                0,
            )
            self.assertEqual(
                run_corpus(
                    "receipts-init", receipts, "--corpus", corpus, "--index", index
                ).returncode,
                0,
            )
            delta.write_text(
                json.dumps(
                    {
                        "state": {"next_action": "Verify the open gap"},
                        "records": [
                            {
                                "kind": "facet",
                                "id": "F1",
                                "question": "Where is the needle?",
                                "status": "open",
                            },
                            {
                                "kind": "evidence",
                                "id": "E1",
                                "facet": "F1",
                                "finding": "The source contains needle evidence.",
                                "source": "source.txt",
                                "excerpt": "x" * 2000,
                                "verified": True,
                            },
                            {
                                "kind": "gap",
                                "id": "G1",
                                "facet": "F1",
                                "description": "Need a second source.",
                                "status": "open",
                                "next_query": "needle corroboration",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            applied = run_corpus("research-apply", state, delta)
            self.assertEqual(applied.returncode, 0, applied.stderr)
            self.assertEqual(json.loads(applied.stdout)["records_applied"], 3)
            linked = run_corpus(
                "search",
                index,
                "needle",
                "--receipts-db",
                receipts,
                "--research-db",
                state,
                "--facet-id",
                "F1",
            )
            self.assertEqual(linked.returncode, 0, linked.stderr)
            resume = json.loads(run_corpus("research-info", state, "--resume").stdout)
            self.assertEqual(resume["active_facets"][0]["facet_id"], "F1")
            self.assertEqual(resume["open_gaps"][0]["gap_id"], "G1")
            self.assertEqual(len(resume["recent_receipts"]), 1)
            summary = json.loads(
                run_corpus(
                    "research-list", state, "evidence", "--id", "E1", "--summary"
                ).stdout
            )
            self.assertNotIn("excerpt", summary["records"][0])

            invalid = root / "invalid.json"
            invalid.write_text(
                json.dumps(
                    {
                        "records": [
                            {
                                "kind": "facet",
                                "id": "F2",
                                "question": "Temporary facet",
                            },
                            {
                                "kind": "evidence",
                                "id": "E2",
                                "facet": "missing",
                                "finding": "Invalid",
                                "source": "source.txt",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            refused = run_corpus("research-apply", state, invalid)
            self.assertEqual(refused.returncode, 2)
            absent = json.loads(
                run_corpus("research-list", state, "facets", "--id", "F2").stdout
            )
            self.assertEqual(absent["result_count"], 0)

    def test_metadata_summary_and_research_schema_excludes_search_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            source = corpus / "record.jsonl"
            source.write_text(
                json.dumps(
                    {
                        "text": "Needle evidence.",
                        "source": "contract.pdf",
                        "page": "2",
                        "section": "Terms",
                        "version": "v2",
                        "date": "2026-10-01",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            index = root / "index.sqlite"
            state = root / "research.sqlite"
            receipts = root / "receipts.sqlite"
            self.assertEqual(run_corpus("index", corpus, "--db", index).returncode, 0)
            overview = json.loads(
                run_corpus("info", index, "--metadata-summary").stdout
            )["metadata_summary"]
            self.assertEqual(overview["versions"][0]["value"], "v2")
            self.assertEqual(overview["sections"][0]["value"], "Terms")
            self.assertEqual(overview["chunk_coverage"]["page_chunks"], 1)
            self.assertEqual(
                run_corpus(
                    "research-init",
                    state,
                    "--scope",
                    "Review",
                    "--corpus",
                    corpus,
                    "--index",
                    index,
                ).returncode,
                0,
            )
            self.assertEqual(
                run_corpus(
                    "receipts-init", receipts, "--corpus", corpus, "--index", index
                ).returncode,
                0,
            )
            self.assertEqual(
                run_corpus(
                    "research-put", state, "facet", "F1", "--question", "Question"
                ).returncode,
                0,
            )
            self.assertEqual(
                run_corpus(
                    "search",
                    index,
                    "needle",
                    "--receipts-db",
                    receipts,
                    "--research-db",
                    state,
                    "--facet-id",
                    "F1",
                ).returncode,
                0,
            )
            with closing(sqlite3.connect(state)) as connection:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }
                self.assertNotIn("search_receipts", tables)
                self.assertIn("receipt_links", tables)
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM receipt_links").fetchone()[0],
                    1,
                )
            with closing(sqlite3.connect(receipts)) as connection:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }
                self.assertIn("search_receipts", tables)
