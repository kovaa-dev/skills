from __future__ import annotations

from test_support import *


class SearchCliTest(CorpusCliTestCase):
    def test_scoped_search_and_get_need_no_purpose_or_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("Needle.", encoding="utf-8")
            index = root / "index.sqlite"
            indexed = run_corpus("index", source, "--db", index)
            self.assertEqual(indexed.returncode, 0, indexed.stderr)

            queries = root / "queries.json"
            queries.write_text(
                json.dumps([{"query": "needle"}]), encoding="utf-8"
            )
            commands = (
                ("search", index, "needle"),
                ("search-many", index, queries),
                ("get", index, 1),
            )
            for command in commands:
                with self.subTest(command=command[0]):
                    result = run_corpus_raw(*command)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(json.loads(result.stdout)["purpose"]["kind"], "scoped-search")
                    declared = run_corpus(*command)
                    self.assertEqual(declared.returncode, 0, declared.stderr)
                    self.assertEqual(
                        json.loads(declared.stdout)["purpose"],
                        {"kind": "adapter-debugging", "reason": "test-suite"},
                    )

    def test_named_gap_can_be_declared_without_a_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("Needle.", encoding="utf-8")
            index = root / "index.sqlite"
            indexed = run_corpus("index", source, "--db", index)
            self.assertEqual(indexed.returncode, 0, indexed.stderr)
            named_gap = run_corpus_raw(
                "search", index, "needle", "--purpose", "named-gap", "--gap-facet", "F1"
            )
            self.assertEqual(named_gap.returncode, 0, named_gap.stderr)
            self.assertEqual(
                json.loads(named_gap.stdout)["purpose"],
                {"kind": "named-gap", "facet_id": "F1"},
            )

            verified_locator = run_corpus_raw(
                "get",
                index,
                1,
                "--purpose",
                "locator-verification",
            )
            self.assertEqual(verified_locator.returncode, 0, verified_locator.stderr)
            self.assertEqual(
                json.loads(verified_locator.stdout)["purpose"],
                {"kind": "locator-verification", "passage_ids": [1]},
            )

            missing_reason = run_corpus_raw(
                "search", index, "needle", "--purpose", "adapter-debugging"
            )
            self.assertEqual(missing_reason.returncode, 2)
            self.assertIn("--purpose-reason", missing_reason.stderr)

    def test_retrieval_commands_enforce_hard_output_cap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("Needle evidence.", encoding="utf-8")
            index = root / "index.sqlite"
            self.assertEqual(run_corpus("index", source, "--db", index).returncode, 0)

            search = run_corpus(
                "search", index, "needle", "--max-total-chars", 40001
            )
            self.assertEqual(search.returncode, 2)
            self.assertIn("between 100 and 40000", search.stderr)

            get = run_corpus("get", index, 1, "--max-total-chars", 200001)
            self.assertEqual(get.returncode, 2)
            self.assertIn("between 100 and 200000", get.stderr)

    def test_search_many_fits_multi_facet_and_exception_probes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("Needle evidence.", encoding="utf-8")
            index = root / "index.sqlite"
            queries = root / "queries.json"
            queries.write_text(
                json.dumps({"queries": [{"query": "needle"}] * 24}),
                encoding="utf-8",
            )

            self.assertEqual(run_corpus("index", source, "--db", index).returncode, 0)
            bounded = run_corpus(
                "search-many", index, queries, "--max-total-chars", 40000
            )
            self.assertEqual(bounded.returncode, 0, bounded.stderr)
            self.assertEqual(json.loads(bounded.stdout)["query_count"], 24)

            queries.write_text(
                json.dumps({"queries": [{"query": "needle"}] * 25}),
                encoding="utf-8",
            )
            rejected = run_corpus("search-many", index, queries)
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("At most 24 batch queries", rejected.stderr)

            queries.write_text(
                json.dumps({"queries": [{"query": "needle"}] * 24}),
                encoding="utf-8",
            )
            oversized = run_corpus(
                "search-many", index, queries, "--max-total-chars", 40001
            )
            self.assertEqual(oversized.returncode, 2)
            self.assertIn("between 1000 and 40000", oversized.stderr)

    def test_auto_mode_handles_prefix_and_fts_queries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text(
                "Accepted cargo volume.\n\nPlanned shipment volume.",
                encoding="utf-8",
            )
            index = root / "index.sqlite"
            self.assertEqual(run_corpus("index", source, "--db", index).returncode, 0)

            prefix = json.loads(
                run_corpus("search", index, "accept* cargo*").stdout
            )
            self.assertEqual(prefix["mode"], "prefix")
            self.assertEqual(prefix["requested_mode"], "auto")
            self.assertEqual(prefix["result_count"], 1)

            fts = json.loads(
                run_corpus(
                    "search",
                    index,
                    '"missing phrase" OR "planned shipment"',
                ).stdout
            )
            self.assertEqual(fts["mode"], "fts")
            self.assertEqual(fts["requested_mode"], "auto")
            self.assertEqual(fts["result_count"], 1)

    def test_search_many_emits_one_snippet_per_passage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("Needle supporting evidence.", encoding="utf-8")
            index = root / "index.sqlite"
            queries = root / "queries.json"
            queries.write_text(
                json.dumps(
                    {"queries": [{"query": "needle"}, {"query": "supporting"}]}
                ),
                encoding="utf-8",
            )
            self.assertEqual(run_corpus("index", source, "--db", index).returncode, 0)

            payload = json.loads(run_corpus("search-many", index, queries).stdout)
            first = payload["results"][0]["results"][0]
            second = payload["results"][1]["results"][0]
            self.assertIn("text", first)
            self.assertNotIn("text", second)
            self.assertTrue(second["batch_duplicate"])
            self.assertEqual(payload["duplicate_snippets_removed"], 1)

    def test_single_file_receipts_are_reused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text(
                "# Variants\n\nGeneral pattern R_T_A_E_O_W.\n\n"
                "Exception pattern R_T_A_W for files 07 and 08.",
                encoding="utf-8",
            )
            index = root / "index.sqlite"
            receipts = root / "receipts.sqlite"
            queries = root / "queries.json"
            queries.write_text(
                json.dumps(
                    {
                        "queries": [
                            {"query": "R_T_A_E_O_W"},
                            {"query": "R_T_A_W"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(run_corpus("index", source, "--db", index).returncode, 0)
            initialized = run_corpus(
                "receipts-init", receipts, "--corpus", source, "--index", index
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            first = json.loads(
                run_corpus(
                    "search-many", index, queries, "--receipts-db", receipts
                ).stdout
            )
            self.assertTrue(all(not item["receipt_hit"] for item in first["results"]))
            repeated = json.loads(
                run_corpus(
                    "search-many", index, queries, "--receipts-db", receipts
                ).stdout
            )
            self.assertTrue(all(item["receipt_hit"] for item in repeated["results"]))

    def test_auto_mode_reuses_legacy_literal_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("Needle evidence.", encoding="utf-8")
            index = root / "index.sqlite"
            receipts = root / "receipts.sqlite"

            self.assertEqual(run_corpus("index", source, "--db", index).returncode, 0)
            initialized = run_corpus(
                "receipts-init", receipts, "--corpus", source, "--index", index
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)

            legacy = json.loads(
                run_corpus(
                    "search",
                    index,
                    "needle",
                    "--mode",
                    "literal",
                    "--receipts-db",
                    receipts,
                ).stdout
            )
            automatic = json.loads(
                run_corpus(
                    "search", index, "needle", "--receipts-db", receipts
                ).stdout
            )

            self.assertFalse(legacy["receipt_hit"])
            self.assertTrue(automatic["receipt_hit"])
            self.assertEqual(automatic["mode"], "literal")
            self.assertEqual(automatic["requested_mode"], "auto")
            self.assertEqual(automatic["receipt_id"], legacy["receipt_id"])

    def test_search_and_get_continue_without_repeats(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            for number in range(3):
                (corpus / f"source-{number}.txt").write_text(
                    f"Needle passage {number}. " + "x" * 240,
                    encoding="utf-8",
                )
            database = root / "index.sqlite"
            self.assertEqual(run_corpus("index", corpus, "--db", database).returncode, 0)

            first_search = json.loads(
                run_corpus("search", database, "needle", "--limit", 1).stdout
            )
            second_search = json.loads(
                run_corpus(
                    "search",
                    database,
                    "needle",
                    "--limit",
                    1,
                    "--offset",
                    first_search["next_offset"],
                ).stdout
            )
            first_id = first_search["results"][0]["passage_id"]
            second_id = second_search["results"][0]["passage_id"]
            self.assertNotEqual(first_id, second_id)

            search_results = first_search["results"] + second_search["results"]
            expected = {
                item["passage_id"]: (corpus / item["source"]).read_text(encoding="utf-8")
                for item in search_results
            }
            reconstructed = {first_id: "", second_id: ""}
            offset = 0
            start_char = 0
            for _ in range(10):
                page = json.loads(
                    run_corpus(
                        "get",
                        database,
                        first_id,
                        second_id,
                        "--max-chars",
                        100,
                        "--max-total-chars",
                        100,
                        "--offset",
                        offset,
                        "--start-char",
                        start_char,
                    ).stdout
                )
                for item in page["results"]:
                    passage_id = item["passage_id"]
                    self.assertEqual(
                        item.get("text_start_char", 0), len(reconstructed[passage_id])
                    )
                    text = item["text"]
                    if item.get("text_truncated"):
                        text = text.removesuffix("…")
                    reconstructed[passage_id] += text
                if not page["has_more"]:
                    break
                offset = page["next_offset"]
                start_char = page["next_start_char"]
            else:
                self.fail("get continuation did not terminate")

            self.assertEqual(reconstructed, expected)

    def test_search_combines_prefix_and_metadata_filters(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "record.jsonl").write_text(
                json.dumps(
                    {
                        "text": "Termination requires notice.",
                        "source": "contract.pdf",
                        "page": 12,
                        "section": "Terms",
                        "version": "v2",
                        "date": "2026-09-30",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            database = root / "index.sqlite"
            self.assertEqual(run_corpus("index", corpus, "--db", database).returncode, 0)

            matched = run_corpus(
                "search",
                database,
                "termin",
                "--mode",
                "prefix",
                "--page",
                12,
                "--version",
                "v2",
            )
            self.assertEqual(matched.returncode, 0, matched.stderr)
            self.assertEqual(json.loads(matched.stdout)["result_count"], 1)
            excluded = run_corpus("search", database, "termination", "--version", "v1")
            self.assertEqual(json.loads(excluded.stdout)["result_count"], 0)

    def test_search_rejects_unbounded_query_and_filter_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "source.txt").write_text("Needle evidence.", encoding="utf-8")
            database = root / "index.sqlite"
            self.assertEqual(run_corpus("index", corpus, "--db", database).returncode, 0)

            query = run_corpus("search", database, "q" * 2_001)
            self.assertEqual(query.returncode, 2)
            self.assertIn("--query exceeds 2000 characters", query.stderr)

            source_filter = run_corpus(
                "search", database, "needle", "--source", "s" * 1_001
            )
            self.assertEqual(source_filter.returncode, 2)
            self.assertIn("--source exceeds 1000 characters", source_filter.stderr)

    def test_search_can_save_a_deduplicated_research_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            source = corpus / "alpha.txt"
            source.write_text("Needle in the first source.", encoding="utf-8")
            (corpus / "beta.txt").write_text(
                "Needle in the second source.", encoding="utf-8"
            )
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
                    "Where is the needle?",
                    "--status",
                    "open",
                ).returncode,
                0,
            )

            search_args = (
                "search",
                index,
                "needle",
                "--limit",
                "1",
                "--receipts-db",
                receipts_db,
                "--research-db",
                state,
                "--facet-id",
                "F1",
            )
            first = run_corpus(*search_args)
            self.assertEqual(first.returncode, 0, first.stderr)
            receipt_id = json.loads(first.stdout)["receipt_id"]

            sentinel = "2000-01-01T00:00:00+00:00"
            with closing(sqlite3.connect(receipts_db)) as connection, connection:
                connection.execute(
                    "UPDATE search_receipts SET last_used_at = ? WHERE receipt_id = ?",
                    (sentinel, receipt_id),
                )
            with closing(sqlite3.connect(state)) as connection, connection:
                connection.execute(
                    "UPDATE receipt_links SET linked_at = ? WHERE receipt_id = ?",
                    (sentinel, receipt_id),
                )
                connection.execute(
                    "UPDATE research_state SET updated_at = ? WHERE singleton = 1",
                    (sentinel,),
                )

            repeated = run_corpus(*search_args)
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            self.assertTrue(json.loads(repeated.stdout)["receipt_hit"])
            self.assertEqual(json.loads(repeated.stdout)["receipt_id"], receipt_id)
            with closing(sqlite3.connect(receipts_db)) as connection:
                self.assertEqual(
                    connection.execute(
                        "SELECT last_used_at FROM search_receipts WHERE receipt_id = ?",
                        (receipt_id,),
                    ).fetchone()[0],
                    sentinel,
                )
            with closing(sqlite3.connect(state)) as connection:
                self.assertEqual(
                    connection.execute(
                        "SELECT linked_at FROM receipt_links WHERE receipt_id = ?",
                        (receipt_id,),
                    ).fetchone()[0],
                    sentinel,
                )
                self.assertEqual(
                    connection.execute(
                        "SELECT updated_at FROM research_state WHERE singleton = 1"
                    ).fetchone()[0],
                    sentinel,
                )

            receipts = json.loads(
                run_corpus(
                    "receipts-list", receipts_db, "--receipt-id", receipt_id, "--details"
                ).stdout
            )
            self.assertEqual(receipts["result_count"], 1)
            self.assertEqual(receipts["records"][0]["query"], "needle")
            self.assertEqual(receipts["records"][0]["outcome"], "incomplete")
            self.assertEqual(receipts["records"][0]["next_offset"], 1)
            self.assertEqual(len(receipts["records"][0]["result_refs"]), 1)
            self.assertNotIn("text", receipts["records"][0]["result_refs"][0])
            summary = json.loads(run_corpus("research-info", state).stdout)
            self.assertEqual(summary["counts"]["receipt_links"], 1)

            source.write_text("Needle after an index change.", encoding="utf-8")
            self.assertEqual(run_corpus("index", corpus, "--db", index).returncode, 0)
            stale = run_corpus(*search_args)
            self.assertEqual(stale.returncode, 2)
            self.assertIn("research-sync", stale.stderr)

    def test_independent_receipts_reuse_searches_and_detect_live_staleness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            source = corpus / "source.txt"
            source.write_text("Needle and clause evidence.", encoding="utf-8")
            index = root / "index.sqlite"
            receipts = root / "receipts.sqlite"
            self.assertEqual(run_corpus("index", corpus, "--db", index).returncode, 0)
            foreign = root / "foreign.sqlite"
            with closing(sqlite3.connect(foreign)) as connection, connection:
                connection.execute("CREATE TABLE keep(value TEXT)")
                connection.execute("INSERT INTO keep VALUES ('safe')")
            refused = run_corpus(
                "receipts-init", foreign, "--corpus", corpus, "--index", index
            )
            self.assertEqual(refused.returncode, 2)
            with closing(sqlite3.connect(foreign)) as connection:
                self.assertEqual(
                    connection.execute("SELECT value FROM keep").fetchone()[0], "safe"
                )
            initialized = run_corpus(
                "receipts-init", receipts, "--corpus", corpus, "--index", index
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)

            first = json.loads(
                run_corpus(
                    "search", index, "needle", "--receipts-db", receipts, "--limit", 1
                ).stdout
            )
            self.assertFalse(first["receipt_hit"])
            self.assertIn("text", first["results"][0])
            repeated = json.loads(
                run_corpus(
                    "search", index, "needle", "--receipts-db", receipts, "--limit", 1
                ).stdout
            )
            self.assertTrue(repeated["receipt_hit"])
            self.assertEqual(repeated["receipt_id"], first["receipt_id"])
            self.assertEqual(repeated["results"], first["results"])
            self.assertEqual(repeated["characters"], first["characters"])
            self.assertEqual(
                run_corpus("search", index, "clause", "--receipts-db", receipts).returncode,
                0,
            )
            self.assertEqual(
                run_corpus(
                    "search",
                    index,
                    "needle",
                    "--receipts-db",
                    receipts,
                    "--receipt-id",
                    "fixed",
                ).returncode,
                0,
            )
            collision = run_corpus(
                "search",
                index,
                "clause",
                "--receipts-db",
                receipts,
                "--receipt-id",
                "fixed",
            )
            self.assertEqual(collision.returncode, 2)
            self.assertIn("different search parameters", collision.stderr)
            refreshed_collision = run_corpus(
                "search",
                index,
                "clause",
                "--receipts-db",
                receipts,
                "--receipt-id",
                "fixed",
                "--refresh",
            )
            self.assertEqual(refreshed_collision.returncode, 2)

            source.write_text("Needle and clause changed.", encoding="utf-8")
            self.assertEqual(run_corpus("index", corpus, "--db", index).returncode, 0)
            status = json.loads(run_corpus("receipts-info", receipts).stdout)
            self.assertTrue(status["index_stale"])
            self.assertEqual(status["current_receipts"], 0)
            self.assertEqual(status["stale_receipts"], 3)
            visible = json.loads(run_corpus("receipts-list", receipts).stdout)
            self.assertEqual(visible["result_count"], 0)
            stale = json.loads(
                run_corpus("receipts-list", receipts, "--include-stale").stdout
            )
            self.assertEqual(stale["result_count"], 3)
            self.assertTrue(all(not record["current"] for record in stale["records"]))

    def test_readonly_receipt_search_never_mutates_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "source.txt").write_text("Needle evidence.", encoding="utf-8")
            index = root / "index.sqlite"
            receipts = root / "receipts.sqlite"
            self.assertEqual(run_corpus("index", corpus, "--db", index).returncode, 0)
            self.assertEqual(
                run_corpus(
                    "receipts-init", receipts, "--corpus", corpus, "--index", index
                ).returncode,
                0,
            )

            before = receipts.read_bytes()
            first = run_corpus(
                "search",
                index,
                "needle",
                "--receipts-db",
                receipts,
                "--read-only-receipts",
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            payload = json.loads(first.stdout)
            self.assertFalse(payload["receipt_hit"])
            self.assertFalse(payload["receipt_persisted"])
            self.assertEqual(receipts.read_bytes(), before)

            stored = run_corpus("search", index, "needle", "--receipts-db", receipts)
            self.assertEqual(stored.returncode, 0, stored.stderr)
            before_hit = receipts.read_bytes()
            hit = json.loads(
                run_corpus(
                    "search",
                    index,
                    "needle",
                    "--receipts-db",
                    receipts,
                    "--read-only-receipts",
                ).stdout
            )
            self.assertTrue(hit["receipt_hit"])
            self.assertEqual(receipts.read_bytes(), before_hit)

    def test_search_many_deduplicates_and_reuses_receipts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            identical = "Needle exact duplicate paragraph."
            (corpus / "first.txt").write_text(identical, encoding="utf-8")
            (corpus / "second.txt").write_text(identical, encoding="utf-8")
            (corpus / "third.txt").write_text(
                "Needle different supporting paragraph.", encoding="utf-8"
            )
            index = root / "index.sqlite"
            receipts = root / "receipts.sqlite"
            queries = root / "queries.json"
            queries.write_text(
                json.dumps({"queries": [{"query": "needle"}, {"query": "supporting"}]}),
                encoding="utf-8",
            )
            self.assertEqual(run_corpus("index", corpus, "--db", index).returncode, 0)
            self.assertEqual(
                run_corpus(
                    "receipts-init", receipts, "--corpus", corpus, "--index", index
                ).returncode,
                0,
            )
            deduplicated = json.loads(
                run_corpus(
                    "search", index, "needle", "--dedupe-exact", "--limit", 3
                ).stdout
            )
            self.assertEqual(deduplicated["result_count"], 2)
            self.assertEqual(len(deduplicated["results"][0]["also_in"]), 1)

            first = run_corpus(
                "search-many", index, queries, "--receipts-db", receipts
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            payload = json.loads(first.stdout)
            self.assertEqual(payload["query_count"], 2)
            self.assertTrue(all(not item["receipt_hit"] for item in payload["results"]))
            repeated = json.loads(
                run_corpus(
                    "search-many", index, queries, "--receipts-db", receipts
                ).stdout
            )
            self.assertTrue(all(item["receipt_hit"] for item in repeated["results"]))
            invalid_queries = root / "invalid-queries.json"
            invalid_queries.write_text(
                json.dumps({"queries": [{"query": "needle", "source": 7}]}),
                encoding="utf-8",
            )
            invalid = run_corpus("search-many", index, invalid_queries)
            self.assertEqual(invalid.returncode, 2)
            self.assertNotIn("Traceback", invalid.stderr)

    def test_readonly_database_connection_rejects_writes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "state.sqlite"
            with sqlite3.connect(database) as connection:
                connection.execute("CREATE TABLE records(value TEXT)")
            with COMMON_MODULE.database(database, readonly=True) as connection:
                self.assertEqual(connection.execute("PRAGMA query_only").fetchone()[0], 1)
                with self.assertRaises(sqlite3.OperationalError):
                    connection.execute("INSERT INTO records(value) VALUES ('blocked')")
