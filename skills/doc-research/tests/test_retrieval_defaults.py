from __future__ import annotations

from test_support import *
from doc_research.cli import parser
from doc_research import search as SEARCH_MODULE


class RetrievalDefaultsTest(CorpusCliTestCase):
    def command(self, *args: object) -> dict[str, object]:
        result = run_corpus_raw(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_batch_preserves_different_snippets_from_the_same_passage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, index, batch = (root / name for name in ("source.jsonl", "index.sqlite", "batch.json"))
            source.write_text(json.dumps({"text": "Alpha approved. " + "background " * 110 + "Omega denied."}))
            batch.write_text(json.dumps([{"query": "alpha"}, {"query": "omega"}, {"query": "omega"}]))
            self.command("index", source, "--db", index)
            result = self.command("search-many", index, batch)
            first, second, repeated = [query["results"][0] for query in result["results"]]
            self.assertIn("Alpha approved", first["text"])
            self.assertIn("Omega denied", second["text"])
            self.assertNotEqual(first["text"], second["text"])
            self.assertNotIn("text", repeated)
            self.assertTrue(repeated["batch_duplicate"])

    def test_catalog_deduplicates_full_content_independently_of_snippet_bounds(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.jsonl"
            prefix = "Needle common material " + "same " * 90
            source.write_text("\n".join(json.dumps({"text": prefix + suffix}) for suffix in ("ALPHA", "BETA")))
            catalog = root / "catalog.sqlite"
            self.command("catalog-init", catalog)
            for corpus_id in ("first", "copy"):
                index, receipts = root / f"{corpus_id}.sqlite", root / f"{corpus_id}-receipts.sqlite"
                self.command("index", source, "--db", index)
                self.command("receipts-init", receipts, "--corpus", source, "--index", index)
                self.command("catalog-put", catalog, corpus_id, "--adapter", "local-index",
                             "--access-boundary", "team", "--index", index, "--receipts-db", receipts)
            args = ("catalog-search", catalog, "needle", "--max-chars", 100, "--receipt-id", "stable")
            for iteration, extra in enumerate(((), (), (), ("--refresh",), ("--max-chars", 800))):
                payload = self.command(*args, *extra)
                self.assertEqual(payload["result_count"], 2)
                self.assertFalse(payload["has_more"])
                self.assertEqual({item["passage_id"] for item in payload["results"]}, {1, 2})
                self.assertTrue(all(len(item["also_in"]) == 1 for item in payload["results"]))
                self.assertNotIn("_content_hash", json.dumps(payload))
                if iteration == 0:
                    with closing(sqlite3.connect(catalog)) as connection, connection:
                        filters_json, refs_json = connection.execute(
                            "SELECT filters_json, result_refs_json FROM federated_receipts WHERE receipt_id = 'stable'"
                        ).fetchone()
                        filters = json.loads(filters_json)
                        filters.pop("_dedupe_identity")
                        connection.execute(
                            "UPDATE federated_receipts SET filters_json = ?, result_refs_json = ? WHERE receipt_id = 'stable'",
                            (json.dumps(filters), json.dumps(json.loads(refs_json)[:1])),
                        )

    def test_auto_query_handles_section_punctuation_and_preserves_explicit_fts_errors(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, index, receipts = (root / name for name in ("source.md", "index.sqlite", "receipts.sqlite"))
            source.write_text("OAuth (RFC 6749). Section 4(a). C++ (API). Payments and refunds (FAQ).")
            self.command("index", source, "--db", index)
            for number, query in enumerate(("OAuth (RFC 6749)", "Section 4(a)", "C++ (API)",
                                            "Payments and refunds (FAQ)")):
                args = ("search", index, query, "--receipts-db", receipts, "--receipt-id", f"query-{number}")
                first, repeated = self.command(*args), self.command(*args)
                self.assertEqual(first["result_count"], 1)
                self.assertEqual(first["mode"], "literal")
                self.assertEqual(first["requested_mode"], "auto")
                self.assertTrue(repeated["receipt_hit"])
                explicit = run_corpus_raw("search", index, query, "--mode", "fts")
                self.assertEqual(explicit.returncode, 2)
                self.assertIn("syntax error", explicit.stderr)
            near = self.command("search", index, "NEAR(OAuth RFC)")
            self.assertEqual(near["mode"], "fts")
            self.assertEqual(near["result_count"], 1)
            args = parser().parse_args(["search", str(index), "Section 4(a)"])
            with mock.patch.object(SEARCH_MODULE, "require_current_schema", side_effect=sqlite3.OperationalError("database is locked")):
                with self.assertRaisesRegex(ValueError, "database is locked"):
                    SEARCH_MODULE.search_payload(args)

    def test_optional_missing_cache_is_readonly_or_created_and_reused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, index = root / "source.md", root / "index.sqlite"
            receipts = root / "new-cache" / "receipts.sqlite"
            source.write_text("Needle evidence.")
            self.command("index", source, "--db", index)
            args = ("search", index, "needle", "--receipts-db", receipts)
            readonly = self.command(*args, "--read-only-receipts")
            self.assertEqual(readonly["result_count"], 1)
            self.assertFalse(readonly["receipt_persisted"])
            self.assertFalse(receipts.parent.exists())
            first = self.command(*args)
            self.assertFalse(first["receipt_hit"])
            self.assertTrue(receipts.is_file())
            saved = receipts.read_bytes()
            second = self.command(*args, "--read-only-receipts")
            self.assertTrue(second["receipt_hit"])
            self.assertEqual(receipts.read_bytes(), saved)

    def test_automatic_cache_setup_preserves_foreign_files_and_source_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, index = root / "source.md", root / "index.sqlite"
            source.write_text("Needle evidence.")
            self.command("index", source, "--db", index)
            foreign = root / "foreign.sqlite"
            with closing(sqlite3.connect(foreign)) as connection, connection:
                connection.execute("CREATE TABLE unrelated(value TEXT)")
            corrupt = root / "corrupt.sqlite"
            corrupt.write_bytes(b"not a sqlite database")
            alias = root / "alias.sqlite"
            os.link(source, alias)
            for target in (foreign, corrupt, alias, index):
                saved = target.read_bytes()
                for extra in ((), ("--read-only-receipts",)):
                    result = run_corpus_raw("search", index, "needle", "--receipts-db", target, *extra)
                    self.assertEqual(result.returncode, 2, result.stdout)
                    self.assertEqual(target.read_bytes(), saved)
