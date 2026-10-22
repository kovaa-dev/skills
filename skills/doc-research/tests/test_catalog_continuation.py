from __future__ import annotations

from test_support import *


class CatalogContinuationCliTest(CorpusCliTestCase):
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
                                    "--offset", offset, "--max-total-chars", 100000)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                repeated = run_corpus("catalog-search", catalog, "needle", "--limit", 10,
                                      "--offset", offset, "--max-total-chars", 100000)
                self.assertEqual(repeated.returncode, 0, repeated.stderr)
                warm = json.loads(repeated.stdout)
                self.assertTrue(warm["receipt_hit"])
                self.assertEqual(warm["results"], payload["results"])
                self.assertEqual(warm["characters"], payload["characters"])
                self.assertEqual(warm["has_more"], payload["has_more"])
                found.extend(item["passage_id"] for item in payload["results"])
                if not payload["has_more"]:
                    break
                self.assertGreater(payload["next_offset"], offset)
                offset = payload["next_offset"]
                self.assertLessEqual(offset, 63)
            self.assertEqual(len(found), 63)
            self.assertEqual(len(set(found)), 63)

    def test_cached_catalog_results_respect_smaller_output_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            catalog = self.make_catalog(Path(directory), [f"Needle record {i}." for i in range(3)])
            first = run_corpus("catalog-search", catalog, "needle", "--max-total-chars", 100000)
            self.assertEqual(first.returncode, 0, first.stderr)
            original = json.loads(first.stdout)
            repeated = run_corpus("catalog-search", catalog, "needle", "--max-total-chars", 400)
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            warm = json.loads(repeated.stdout)
            self.assertTrue(warm["receipt_hit"])
            self.assertTrue(warm["has_more"])
            self.assertTrue(warm["text_truncated"])
            self.assertEqual(warm["results"], original["results"][:1])
            self.assertEqual(warm["next_offset"], 1)
            self.assertLessEqual(warm["characters"], 400)

    def test_catalog_get_continuation_recovers_text_and_unvisited_passages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            texts = ["Needle first " + "long " * 90 + "end", "Needle second complete."]
            catalog = self.make_catalog(Path(directory), texts)
            offset = start = 0
            restored = {1: "", 2: ""}
            while True:
                result = run_corpus("catalog-get", catalog, "C=1", "C=2", "C=999",
                                    "--offset", offset, "--start-char", start,
                                    "--max-chars", 100, "--max-total-chars", 100000)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertNotIn("C=2", payload["not_found"])
                for item in payload["results"]:
                    text = item["text"]
                    restored[item["passage_id"]] += text[:-1] if item.get("text_truncated") else text
                if not payload["has_more"]:
                    self.assertIn("C=999", payload["not_found"])
                    break
                cursor = (payload["next_offset"], payload["next_start_char"])
                self.assertGreater(cursor, (offset, start))
                offset, start = cursor
            self.assertEqual(restored, dict(enumerate(texts, 1)))

    def test_catalog_get_total_budget_returns_reachable_next_locator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            catalog = self.make_catalog(Path(directory), ["Needle " + "a" * 150, "Needle " + "b" * 150])
            first = run_corpus("catalog-get", catalog, "C=1", "C=2", "--max-total-chars", 600)
            self.assertEqual(first.returncode, 0, first.stderr)
            payload = json.loads(first.stdout)
            self.assertTrue(payload["has_more"])
            self.assertEqual(payload["not_found"], [])
            second = run_corpus("catalog-get", catalog, "C=1", "C=2", "--max-total-chars", 600,
                                "--offset", payload["next_offset"], "--start-char", payload["next_start_char"])
            self.assertEqual(second.returncode, 0, second.stderr)
            continuation = json.loads(second.stdout)
            self.assertFalse(continuation["has_more"])
            self.assertEqual([item["passage_id"] for item in payload["results"] + continuation["results"]], [1, 2])

    def test_get_final_unicode_slice_and_prefix_only_context_are_lossless(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            text = "background " * 100 + "needle " + "Ж🙂…"
            catalog = self.make_catalog(root, [text])
            final = run_corpus("catalog-get", catalog, "C=1", "--start-char", len(text) - 3)
            self.assertEqual(final.returncode, 0, final.stderr)
            final_payload = json.loads(final.stdout)
            final_item = final_payload["results"][0]
            self.assertEqual(final_item["text"], "Ж🙂…")
            self.assertEqual(final_item["text_start_char"], len(text) - 3)
            self.assertFalse(final_item.get("text_truncated", False))
            self.assertFalse(final_payload["has_more"])

            around = run_corpus("get", root / "index.sqlite", 1,
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
