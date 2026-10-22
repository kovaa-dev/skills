from __future__ import annotations

from test_support import *


class ResearchCliTest(CorpusCliTestCase):
    def test_research_state_is_separate_persistent_and_private(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            source = corpus / "source.txt"
            source.write_text("Initial evidence.", encoding="utf-8")
            index = root / "index.sqlite"
            state = root / "research.sqlite"
            self.assertEqual(run_corpus("index", corpus, "--db", index).returncode, 0)

            initialized = run_corpus(
                "research-init",
                state,
                "--scope",
                "Contract review",
                "--corpus",
                corpus,
                "--index",
                index,
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            summary = json.loads(initialized.stdout)
            self.assertEqual(summary["database"], str(state.resolve()))
            self.assertFalse(summary["index_stale"])
            if os.name != "nt":
                self.assertEqual(state.stat().st_mode & 0o777, 0o600)

            source.write_text("Changed evidence.", encoding="utf-8")
            self.assertEqual(run_corpus("index", corpus, "--db", index).returncode, 0)
            stale = json.loads(run_corpus("research-info", state).stdout)
            self.assertTrue(stale["index_stale"])
            self.assertEqual(stale["scope"], "Contract review")

            synced = run_corpus("research-sync", state)
            self.assertEqual(synced.returncode, 0, synced.stderr)
            self.assertTrue(json.loads(synced.stdout)["changed"])
            self.assertFalse(json.loads(run_corpus("research-info", state).stdout)["index_stale"])

    def test_research_records_upsert_and_list(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "source.txt").write_text("Evidence.", encoding="utf-8")
            state = root / "research.sqlite"
            initialized = run_corpus(
                "research-init", state, "--scope", "Review", "--corpus", corpus
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)

            commands = [
                (
                    "facet",
                    "F1",
                    "--question",
                    "What are the termination conditions?",
                    "--status",
                    "open",
                    "--next-action",
                    "Search amendments",
                ),
                (
                    "evidence",
                    "E1",
                    "--facet",
                    "F1",
                    "--finding",
                    "Written notice is required.",
                    "--source",
                    "contract.pdf",
                    "--source-version",
                    "v2",
                    "--page",
                    "12",
                    "--section",
                    "4.2",
                    "--verified",
                    "true",
                ),
                (
                    "gap",
                    "G1",
                    "--facet",
                    "F1",
                    "--description",
                    "Amendment date is unknown.",
                    "--status",
                    "open",
                    "--next-query",
                    "effective date amendment",
                ),
                (
                    "conflict",
                    "C1",
                    "--facet",
                    "F1",
                    "--description",
                    "Summary and contract disagree.",
                    "--status",
                    "open",
                    "--evidence-ids-json",
                    '["E1"]',
                ),
            ]
            for command in commands:
                result = run_corpus("research-put", state, *command)
                self.assertEqual(result.returncode, 0, result.stderr)

            updated = run_corpus(
                "research-put", state, "facet", "F1", "--status", "supported"
            )
            self.assertEqual(updated.returncode, 0, updated.stderr)
            self.assertEqual(json.loads(updated.stdout)["action"], "updated")

            summary = json.loads(run_corpus("research-info", state).stdout)
            self.assertEqual(
                summary["counts"],
                {
                    "facets": 1,
                    "receipt_links": 0,
                    "evidence": 1,
                    "gaps": 1,
                    "conflicts": 1,
                },
            )
            facets = json.loads(
                run_corpus("research-list", state, "facets", "--status", "supported").stdout
            )
            self.assertEqual(facets["records"][0]["facet_id"], "F1")
            evidence = json.loads(
                run_corpus("research-list", state, "evidence", "--facet", "F1").stdout
            )
            self.assertTrue(evidence["records"][0]["verified"])

            too_large = run_corpus(
                "research-put", state, "evidence", "E1", "--excerpt", "x" * 2_001
            )
            self.assertEqual(too_large.returncode, 2)
            self.assertIn("exceeds 2000 characters", too_large.stderr)
            self.assertEqual(
                run_corpus(
                    "research-put",
                    state,
                    "evidence",
                    "E1",
                    "--excerpt",
                    "x" * 1_800,
                    "--interpretation",
                    "Precise wording matters.",
                ).returncode,
                0,
            )
            compact = json.loads(
                run_corpus("research-list", state, "evidence", "--facet", "F1").stdout
            )
            self.assertTrue(compact["summary"])
            self.assertNotIn("excerpt", compact["records"][0])
            self.assertNotIn("interpretation", compact["records"][0])
            bounded_result = run_corpus(
                "research-list",
                state,
                "evidence",
                "--facet",
                "F1",
                "--details",
                "--max-chars",
                "100",
                "--max-total-chars",
                "1000",
            )
            self.assertEqual(bounded_result.returncode, 0, bounded_result.stderr)
            bounded = json.loads(bounded_result.stdout)
            self.assertFalse(bounded["summary"])
            self.assertTrue(bounded["output_truncated"])
            self.assertIn("excerpt", bounded["records"][0]["truncated_fields"])

    def test_research_state_rejects_foreign_files_and_invalid_references(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            foreign = root / "foreign.sqlite"
            with closing(sqlite3.connect(foreign)) as connection, connection:
                connection.execute("CREATE TABLE keep(value TEXT)")
                connection.execute("INSERT INTO keep VALUES ('safe')")

            refused = run_corpus(
                "research-init", foreign, "--scope", "Review", "--corpus", corpus
            )
            self.assertEqual(refused.returncode, 2)
            with closing(sqlite3.connect(foreign)) as connection:
                self.assertEqual(connection.execute("SELECT value FROM keep").fetchone()[0], "safe")

            state = root / "research.sqlite"
            self.assertEqual(
                run_corpus(
                    "research-init", state, "--scope", "Review", "--corpus", corpus
                ).returncode,
                0,
            )
            missing_facet = run_corpus(
                "research-put",
                state,
                "evidence",
                "E1",
                "--facet",
                "missing",
                "--finding",
                "Finding",
                "--source",
                "source.txt",
            )
            self.assertEqual(missing_facet.returncode, 2)
            self.assertIn("facet", missing_facet.stderr.lower())

            self.assertEqual(
                run_corpus(
                    "research-put",
                    state,
                    "facet",
                    "F1",
                    "--question",
                    "Question",
                    "--status",
                    "open",
                ).returncode,
                0,
            )
            invalid_json = run_corpus(
                "research-put",
                state,
                "conflict",
                "C1",
                "--facet",
                "F1",
                "--description",
                "Conflicting sources",
                "--evidence-ids-json",
                "{}",
            )
            self.assertEqual(invalid_json.returncode, 2)
            self.assertIn("JSON array", invalid_json.stderr)

    def test_research_sync_preserves_independent_receipt_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            source = corpus / "source.txt"
            source.write_text("First version.", encoding="utf-8")
            (corpus / "second.txt").write_text("Another version.", encoding="utf-8")
            index = root / "index.sqlite"
            state = root / "research.sqlite"
            receipts_db = root / "receipts.sqlite"
            self.assertEqual(run_corpus("index", corpus, "--db", index).returncode, 0)
            self.assertEqual(
                run_corpus(
                    "receipts-init", receipts_db, "--corpus", corpus, "--index", index
                ).returncode,
                0,
            )
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
                    "research-put",
                    state,
                    "facet",
                    "F1",
                    "--question",
                    "Question",
                    "--status",
                    "open",
                ).returncode,
                0,
            )
            searched = json.loads(
                run_corpus(
                    "search",
                    index,
                    "version",
                    "--limit",
                    "1",
                    "--receipts-db",
                    receipts_db,
                    "--research-db",
                    state,
                    "--facet-id",
                    "F1",
                ).stdout
            )
            self.assertEqual(searched["next_offset"], 1)

            source.write_text("Second version.", encoding="utf-8")
            self.assertEqual(run_corpus("index", corpus, "--db", index).returncode, 0)
            self.assertEqual(run_corpus("research-sync", state).returncode, 0)
            receipts = json.loads(
                run_corpus(
                    "receipts-list", receipts_db, "--include-stale", "--details"
                ).stdout
            )
            self.assertEqual(receipts["records"][0]["next_offset"], 1)
            self.assertEqual(
                json.loads(run_corpus("research-info", state).stdout)["counts"][
                    "receipt_links"
                ],
                1,
            )
