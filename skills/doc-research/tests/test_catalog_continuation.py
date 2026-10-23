from __future__ import annotations

from test_support import *
from doc_research.cli import parser
from doc_research import catalog_search as CATALOG_SEARCH


class CatalogContinuationCliTest(CorpusCliTestCase):
    def test_read_only_cursor_obeys_whole_response_budget_or_fails_explicitly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            catalog = self.make_catalog(Path(directory), [f"Needle unique record {i}." for i in range(40)])
            token = None
            for _ in range(40):
                args = ["catalog-search", catalog, "needle", "--limit", 3, "--read-only",
                        "--dedupe-exact", "--max-total-chars", 2000]
                if token:
                    args.extend(["--continuation", token])
                result = run_corpus(*args)
                if result.returncode:
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("envelope", result.stderr)
                    break
                self.assertLessEqual(len(result.stdout), 2000)
                payload = json.loads(result.stdout)
                self.assertTrue(payload["has_more"])
                token = payload["next_continuation"]
            else:
                self.fail("Growing read-only state did not enforce the response budget")

    def test_refresh_cannot_silently_retarget_a_saved_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            catalog = self.make_catalog(Path(directory), [f"Needle record {i}." for i in range(5)])
            first = run_corpus("catalog-search", catalog, "needle", "--limit", 2)
            self.assertEqual(first.returncode, 0, first.stderr)
            payload = json.loads(first.stdout)
            budget = len(json.dumps(payload["results"][0], ensure_ascii=False, separators=(",", ":"))) + 500
            refreshed = run_corpus("catalog-search", catalog, "needle", "--limit", 2,
                                   "--refresh", "--max-total-chars", budget)
            self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
            self.assertEqual(json.loads(refreshed.stdout)["result_count"], 1)
            stale = run_corpus("catalog-search", catalog, "needle", "--limit", 2,
                              "--continuation", payload["next_continuation"])
            self.assertEqual(stale.returncode, 2)
            self.assertIn("receipt changed", stale.stderr)

    def test_continuation_rejects_unrepresentable_member_offsets(self) -> None:
        state = {"identity": "search", "fingerprint": "generation", "offset": 0,
                 "members": {"C": {"offset": 2**63, "done": False}},
                 "turn": 0, "seen": [], "sources": {}}
        with self.assertRaisesRegex(ValueError, "Invalid catalog continuation"):
            CATALOG_SEARCH.decode_continuation(
                CATALOG_SEARCH.encode_continuation(state), "search", "generation", 0
            )

    def passage_ids(self, catalog: Path) -> list[int]:
        with closing(sqlite3.connect(catalog.parent / "index.sqlite")) as connection:
            return [row[0] for row in connection.execute("SELECT rowid FROM chunks ORDER BY source")]

    def test_continuation_resumes_member_position_without_replaying_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            catalog = self.make_catalog(Path(directory), [f"Needle record {i}." for i in range(20)])
            first = run_corpus("catalog-search", catalog, "needle", "--limit", 3)
            self.assertEqual(first.returncode, 0, first.stderr)
            page = json.loads(first.stdout)
            offsets = []
            original = CATALOG_SEARCH.search_payload

            def search(args: argparse.Namespace, **kwargs: object) -> dict[str, object]:
                offsets.append(args.offset)
                return original(args, **kwargs)

            args = parser().parse_args(["catalog-search", str(catalog), "needle", "--limit", "3", "--offset", "3"])
            with mock.patch.object(CATALOG_SEARCH, "search_payload", side_effect=search), redirect_stdout(io.StringIO()) as stdout:
                CATALOG_SEARCH.command_catalog_search(args)
            self.assertEqual(offsets, [3])
            continued = json.loads(stdout.getvalue())
            self.assertFalse(set(item["passage_id"] for item in page["results"]) &
                             set(item["passage_id"] for item in continued["results"]))

    def test_read_only_dedupe_continuation_is_bounded_and_generation_guarded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = self.make_catalog(root, ["Needle"] * 120 + ["Needle unique detail"])
            offset, token = 0, None
            found, empty_pages = [], 0
            first_locator = None
            for _ in range(8):
                arguments = ["catalog-search", catalog, "needle", "--limit", 3,
                             "--read-only", "--dedupe-exact", "--offset", offset]
                if token:
                    arguments.extend(["--continuation", token])
                result = run_corpus(*arguments)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                found.extend(item["text"] for item in payload["results"])
                if not payload["results"]:
                    empty_pages += 1
                if first_locator is None and payload["results"]:
                    first_locator = payload["results"][0]["locator"]
                if not payload["has_more"]:
                    break
                offset, token = payload["next_offset"], payload["next_continuation"]
            else:
                self.fail("Continuation did not terminate")
            self.assertEqual(len(found), 2)
            self.assertEqual(len(set(found)), 2)
            self.assertGreater(empty_pages, 0)
            with closing(sqlite3.connect(catalog)) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM federated_receipts").fetchone()[0], 0)
            (root / "corpus" / "source.jsonl").write_text('{"text":"Needle replacement"}', encoding="utf-8")
            rebuilt = run_corpus("index", root / "corpus", "--db", root / "index.sqlite")
            self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr)
            stale = run_corpus("catalog-search", catalog, "needle", "--limit", 3, "--read-only",
                               "--dedupe-exact", "--offset", offset, "--continuation", token)
            self.assertEqual(stale.returncode, 2)
            self.assertIn("generation changed", stale.stderr)
            old_get = run_corpus("catalog-get", catalog, first_locator)
            self.assertEqual(old_get.returncode, 2)
            self.assertIn("generation changed", old_get.stderr)

    def make_catalog(self, root: Path, texts: list[str]) -> Path:
        corpus = root / "corpus"
        corpus.mkdir()
        (corpus / "source.jsonl").write_text(
            "\n".join(json.dumps({"text": text, "source": f"source-{i}"})
                      for i, text in enumerate(texts)), encoding="utf-8"
        )
        index, receipts, catalog = (root / name for name in
                                    ("index.sqlite", "receipts.sqlite", "catalog.sqlite"))
        for command in (
            ("index", corpus, "--db", index),
            ("receipts-init", receipts, "--corpus", corpus, "--index", index),
            ("catalog-init", catalog),
            ("catalog-put", catalog, "C", "--adapter", "local-index",
             "--access-boundary", "team", "--index", index, "--receipts-db", receipts),
        ):
            result = run_corpus(*command)
            self.assertEqual(result.returncode, 0, result.stderr)
        return catalog

    def test_catalog_search_continues_past_fifty_with_large_outer_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            catalog = self.make_catalog(Path(directory), [f"Needle record {i}." for i in range(63)])
            offset = 0
            found = []
            while True:
                result = run_corpus("catalog-search", catalog, "needle", "--limit", 10,
                                    "--offset", offset, "--max-total-chars", 100000, "--dedupe-exact")
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                repeated = run_corpus("catalog-search", catalog, "needle", "--limit", 10,
                                      "--offset", offset, "--max-total-chars", 100000, "--dedupe-exact")
                self.assertEqual(repeated.returncode, 0, repeated.stderr)
                warm = json.loads(repeated.stdout)
                self.assertTrue(warm["receipt_hit"])
                self.assertEqual(warm["results"], payload["results"])
                self.assertEqual(warm["characters"], payload["characters"])
                self.assertEqual(warm["has_more"], payload["has_more"])
                found.extend(item["passage_id"] for item in payload["results"])
                if not payload["has_more"]:
                    break
                self.assertLess(len(payload["next_continuation"]), 80)
                self.assertGreater(payload["next_offset"], offset)
                offset = payload["next_offset"]
                self.assertLessEqual(offset, 63)
            self.assertEqual(len(found), 63)
            self.assertEqual(len(set(found)), 63)
            with closing(sqlite3.connect(catalog)) as connection:
                stored = connection.execute("SELECT result_refs_json, member_receipts_json FROM federated_receipts").fetchall()
            self.assertEqual(sum(len(json.loads(row[0])) for row in stored), 63)
            for references, members in stored:
                metadata = json.loads(members)[0]
                self.assertFalse(metadata["base"].get("seen"))
                self.assertTrue(all("_next_continuation" not in item for item in json.loads(references)))

    def test_cached_catalog_results_respect_smaller_output_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            catalog = self.make_catalog(Path(directory), [f"Needle record {i}." for i in range(3)])
            first = run_corpus("catalog-search", catalog, "needle", "--max-total-chars", 100000)
            self.assertEqual(first.returncode, 0, first.stderr)
            original = json.loads(first.stdout)
            budget = len(json.dumps(original["results"][0], ensure_ascii=False, separators=(",", ":"))) + 450
            repeated = run_corpus("catalog-search", catalog, "needle", "--max-total-chars", budget)
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            warm = json.loads(repeated.stdout)
            self.assertTrue(warm["receipt_hit"])
            self.assertTrue(warm["has_more"])
            self.assertTrue(warm["text_truncated"])
            self.assertEqual(warm["results"], original["results"][:1])
            self.assertEqual(warm["next_offset"], 1)
            self.assertLessEqual(warm["characters"], budget)
            self.assertLessEqual(len(repeated.stdout), budget)
            continued = run_corpus("catalog-search", catalog, "needle",
                                   "--continuation", warm["next_continuation"])
            self.assertEqual(continued.returncode, 0, continued.stderr)
            self.assertEqual(json.loads(continued.stdout)["results"], original["results"][1:])

    def test_catalog_get_continuation_recovers_text_and_unvisited_passages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            texts = ["Needle first " + "long " * 90 + "end", "Needle second complete."]
            catalog = self.make_catalog(Path(directory), texts)
            ids = self.passage_ids(catalog)
            offset = start = 0
            restored = dict.fromkeys(ids, "")
            while True:
                result = run_corpus("catalog-get", catalog, *(f"C={item}" for item in ids), "C=999",
                                    "--offset", offset, "--start-char", start,
                                    "--max-chars", 100, "--max-total-chars", 100000)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertNotIn(f"C={ids[1]}", payload["not_found"])
                for item in payload["results"]:
                    text = item["text"]
                    restored[item["passage_id"]] += text[:-1] if item.get("text_truncated") else text
                if not payload["has_more"]:
                    self.assertIn("C=999", payload["not_found"])
                    break
                cursor = (payload["next_offset"], payload["next_start_char"])
                self.assertGreater(cursor, (offset, start))
                offset, start = cursor
            self.assertEqual(restored, dict(zip(ids, texts)))

    def test_catalog_get_total_budget_returns_reachable_next_locator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            catalog = self.make_catalog(Path(directory), ["Needle " + "a" * 150, "Needle " + "b" * 150])
            ids = self.passage_ids(catalog)
            locators = [f"C={item}" for item in ids]
            first = run_corpus("catalog-get", catalog, *locators, "--max-total-chars", 800)
            self.assertEqual(first.returncode, 0, first.stderr)
            payload = json.loads(first.stdout)
            self.assertTrue(payload["has_more"])
            self.assertEqual(payload["not_found"], [])
            self.assertLessEqual(len(first.stdout), 800)
            second = run_corpus("catalog-get", catalog, *locators, "--max-total-chars", 800,
                                "--offset", payload["next_offset"], "--start-char", payload["next_start_char"])
            self.assertEqual(second.returncode, 0, second.stderr)
            continuation = json.loads(second.stdout)
            self.assertFalse(continuation["has_more"])
            self.assertEqual([item["passage_id"] for item in payload["results"] + continuation["results"]], ids)

    def test_get_final_unicode_slice_and_prefix_only_context_are_lossless(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            text = "background " * 100 + "needle " + "Ж🙂…"
            catalog = self.make_catalog(root, [text])
            passage_id = self.passage_ids(catalog)[0]
            final = run_corpus("catalog-get", catalog, f"C={passage_id}", "--start-char", len(text) - 3)
            self.assertEqual(final.returncode, 0, final.stderr)
            final_payload = json.loads(final.stdout)
            final_item = final_payload["results"][0]
            self.assertEqual(final_item["text"], "Ж🙂…")
            self.assertEqual(final_item["text_start_char"], len(text) - 3)
            self.assertFalse(final_item.get("text_truncated", False))
            self.assertFalse(final_payload["has_more"])

            around = run_corpus("get", root / "index.sqlite", passage_id,
                                "--around", "needle", "--max-chars", 600)
            self.assertEqual(around.returncode, 0, around.stderr)
            window = json.loads(around.stdout)
            item = window["results"][0]
            self.assertGreater(item["text_start_char"], 0)
            self.assertEqual(item["text"], text[item["text_start_char"]:])
            self.assertFalse(item.get("text_truncated", False))
            self.assertTrue(window["has_more"])
            self.assertEqual(window["prefix_continuations"], [
                {"offset": 0, "start_char": 0, "end_char": item["text_start_char"]}
            ])
            self.assertEqual((window["next_offset"], window["next_start_char"]), (0, 0))
