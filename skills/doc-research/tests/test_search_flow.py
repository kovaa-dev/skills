from __future__ import annotations

from test_support import *


class SearchFlowTest(CorpusCliTestCase):
    def command(self, *args: object) -> dict[str, object]:
        result = run_corpus_raw(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_registered_evidence_can_accumulate_across_bounded_searches(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("# Base\n\nBaseline evidence.\n\n" + "\n\n".join(
                f"# Section {number}\n\nNovel evidence {number}." for number in range(51)
            ), encoding="utf-8")
            questions = root / "questions.json"
            questions.write_text(json.dumps({"questions": [{
                "id": "facet", "question": "What is baseline?", "verification": "exact",
                "queries": [{"query": "baseline", "role": "support"}]
            }]}), encoding="utf-8")
            index, receipt = root / "index.sqlite", root / "task.json"
            self.command("evidence-pack", source, questions, "--db", index,
                         "--task-receipt", receipt, "--execution-route", "coordinator-direct")
            args = ("search", index, "novel", "--limit", 50, "--task-receipt", receipt, "--gap-facet", "facet")
            first = self.command(*args)
            second = self.command(*args, "--offset", first["next_offset"])
            self.assertEqual(first["result_count"], 50)
            self.assertEqual(second["result_count"], 1)
            saved = json.loads(receipt.read_text())
            self.assertEqual(len(saved["facets"][0]["passage_ids"]), 52)
            self.command("get", index, second["results"][0]["passage_id"], "--task-receipt", receipt)

    def test_independent_receipt_write_cannot_modify_a_corpus_alias(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "source.md").write_text("Needle evidence.", encoding="utf-8")
            index, receipts = root / "index.sqlite", root / "receipts.sqlite"
            self.command("index", corpus, "--db", index)
            self.command("receipts-init", receipts, "--corpus", corpus, "--index", index)
            alias = corpus / "alias.md"
            os.link(receipts, alias)
            protected = alias.read_bytes()
            refused = run_corpus_raw("search", index, "needle", "--receipts-db", receipts)
            self.assertEqual(refused.returncode, 2, refused.stderr)
            self.assertIn("collides", refused.stderr)
            self.assertEqual(alias.read_bytes(), protected)
            self.assertEqual(receipts.read_bytes(), protected)

    def test_named_gap_registers_new_evidence_then_get_and_findings_save(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text(
                "# Alpha\n\nBaseline alpha.\n\n# Beta\n\nBaseline beta.\n\n"
                "# Exception\n\nSpecialcase changes alpha under a condition.", encoding="utf-8"
            )
            index = root / "index.sqlite"
            receipt_path = root / "task.json"
            questions = root / "questions.json"
            questions.write_text(json.dumps({"questions": [
                {"id": name, "question": f"What is baseline {name}?", "verification": "exact",
                 "queries": [{"query": f"baseline {name}", "role": "support"}]}
                for name in ("alpha", "beta")
            ]}), encoding="utf-8")
            self.command("evidence-pack", source, questions, "--db", index,
                         "--task-receipt", receipt_path, "--execution-route", "coordinator-direct")
            receipt = json.loads(receipt_path.read_text())
            findings = root / "findings.json"
            findings.write_text(json.dumps({"findings": [
                {"facet_id": facet["id"], "claims": [
                    {"text": f"Baseline {facet['id']} holds.", "passage_ids": facet["passage_ids"],
                     "status": "confirmed", "basis": "Read baseline", "scope": "Baseline"}
                ]} for facet in receipt["facets"]
            ]}), encoding="utf-8")
            self.command("findings-save", receipt_path, findings)
            before = json.loads(receipt_path.read_text())
            self.assertEqual(before["gaps"], [])
            found = self.command("search", index, "specialcase", "--purpose", "named-gap",
                                 "--task-receipt", receipt_path, "--gap-facet", "alpha")
            new_id = found["results"][0]["passage_id"]
            after = json.loads(receipt_path.read_text())
            self.assertIn(new_id, after["facets"][0]["passage_ids"])
            self.assertEqual(after["facets"][0]["finding"]["status"], "confirmed")
            self.assertIn({"facet_id": "alpha", "reason": "new-evidence-needs-review"}, after["gaps"])
            self.assertEqual(after["facets"][1], before["facets"][1])
            self.assertEqual(after["conflicts"], before["conflicts"])
            self.assertEqual(after["facets"][0]["support_passage_ids"], before["facets"][0]["support_passage_ids"])
            reopened = self.command("get", index, new_id, "--task-receipt", receipt_path)
            self.assertIn("under a condition", reopened["results"][0]["text"])
            findings.write_text(json.dumps({"findings": [{
                "facet_id": "alpha", "claims": [{
                    "text": "The special case changes alpha conditionally.", "passage_ids": [new_id],
                    "status": "confirmed", "basis": "Checked special case", "scope": "Special case conditions"
                }]
            }]}), encoding="utf-8")
            self.command("findings-save", receipt_path, findings)
            verified = receipt_path.read_bytes()
            self.command("search", index, "specialcase", "--task-receipt", receipt_path,
                         "--gap-facet", "alpha")
            self.assertEqual(receipt_path.read_bytes(), verified)

            source.write_text(source.read_text() + "\n\nChanged index.", encoding="utf-8")
            self.command("index", source, "--db", index)
            for command in (("search", index, "specialcase"), ("get", index, new_id)):
                stale = run_corpus_raw(*command, "--task-receipt", receipt_path, "--gap-facet", "alpha")
                self.assertEqual(stale.returncode, 2, stale.stderr)
                self.assertIn("stale", stale.stderr)
                self.assertEqual(receipt_path.read_bytes(), verified)

    def test_cached_snippets_keep_aliases_and_bounded_pagination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            for name in ("one", "alias", "other"):
                text = "Needle repeated evidence " + "word " * 100
                if name == "other":
                    text += "distinct"
                (corpus / f"{name}.md").write_text(text, encoding="utf-8")
            index = root / "index.sqlite"
            receipts = root / "receipts.sqlite"
            self.command("index", corpus, "--db", index)
            self.command("receipts-init", receipts, "--corpus", corpus, "--index", index)
            args = ("search", index, "needle", "--receipts-db", receipts, "--dedupe-exact",
                    "--max-chars", 100, "--max-total-chars", 4000, "--limit", 1, "--snippet-tokens", 64)
            first = self.command(*args)
            repeated = self.command(*args)
            self.assertTrue(repeated.pop("receipt_hit"))
            self.assertFalse(first.pop("receipt_hit"))
            self.assertEqual(repeated, first)
            self.assertTrue(first["has_more"])
            self.assertTrue(first["results"][0]["also_in"])
            self.assertLessEqual(first["characters"], 100)
            continued = self.command(*args, "--offset", first["next_offset"])
            self.assertNotEqual(continued["results"][0]["passage_id"], first["results"][0]["passage_id"])

    def test_batch_and_direct_get_register_only_requested_facet_with_aliases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "base.md").write_text("Baseline evidence.", encoding="utf-8")
            for name in ("new", "alias"):
                (corpus / f"{name}.md").write_text("Novel exception.", encoding="utf-8")
            index = root / "index.sqlite"
            receipt = root / "task.json"
            questions = root / "questions.json"
            questions.write_text(json.dumps({"questions": [
                {"id": name, "question": "What is baseline?", "verification": "exact",
                 "queries": [{"query": "baseline", "role": "support"}]}
                for name in ("first", "second")
            ]}), encoding="utf-8")
            self.command("evidence-pack", corpus, questions, "--db", index,
                         "--task-receipt", receipt, "--execution-route", "coordinator-direct")
            before = json.loads(receipt.read_text())
            batch = root / "batch.json"
            batch.write_text(json.dumps([{"query": "novel", "gap_facet": "first"}]), encoding="utf-8")
            result = self.command("search-many", index, batch, "--task-receipt", receipt, "--dedupe-exact")
            hit = result["results"][0]["results"][0]
            new_ids = {hit["passage_id"], hit["also_in"][0]["passage_id"]}
            after = json.loads(receipt.read_text())
            self.assertTrue(new_ids.issubset(after["facets"][0]["passage_ids"]))
            self.assertTrue(new_ids.issubset({item["passage_id"] for item in after["facets"][0]["locators"]}))
            self.assertEqual(after["facets"][1], before["facets"][1])
            self.command("get", index, hit["passage_id"], "--task-receipt", receipt, "--gap-facet", "second")
            direct = json.loads(receipt.read_text())
            self.assertIn(hit["passage_id"], direct["facets"][1]["passage_ids"])
            self.assertEqual(direct["facets"][0], after["facets"][0])
            direct["queries"] = [{"query": "novel", "gap_facet": "second"}]
            receipt.write_text(json.dumps(direct), encoding="utf-8")
            protected = receipt.read_bytes()
            collision = run_corpus_raw("search-many", index, receipt, "--task-receipt", receipt)
            self.assertEqual(collision.returncode, 2, collision.stderr)
            self.assertIn("collides", collision.stderr)
            self.assertEqual(receipt.read_bytes(), protected)
