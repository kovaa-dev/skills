from __future__ import annotations

from test_support import *


class RetrievalInteractionsTest(CorpusCliTestCase):
    def invoke(self, *args):
        result = run_corpus_raw(*args)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def pack(self, root, source, questions, *extra):
        (root / "questions.json").write_text(json.dumps({"questions": questions}), encoding="utf-8")
        return self.invoke("evidence-pack", source, root / "questions.json",
                           "--db", root / "index.sqlite", "--task-receipt", root / "task.json", *extra)

    def question(self, key, word):
        return {"id": key, "question": f"What does {word} require?",
                "queries": [{"query": word, "role": "support"}]}

    def save(self, root, payload):
        (root / "findings.json").write_text(json.dumps({"findings": [
            {"facet_id": facet["id"], "claims": [
                {"text": "A supported fixture finding, conditional on the cited rule.",
                 "status": "confirmed", "basis": "Checked cited rule", "scope": "Rule conditions",
                 "passage_ids": facet["passage_ids"][:1]}]}
            for facet in payload["facets"]]}), encoding="utf-8")
        return self.invoke("findings-save", root / "task.json", root / "findings.json")

    def test_match_context_and_reachable_prefix_and_suffix(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("# Conditions\n\n" + "background " * 600
                              + "\n\nCriticalToken is required only when the parent exists. ExceptionToken excludes cancelled cases.\n",
                              encoding="utf-8")
            payload = self.pack(root, source, [self.question("A", "CriticalToken")],
                                "--chunk-chars", 12000, "--max-passage-chars", 800)
            text = payload["passages"][0]["text"]
            self.assertIn("CriticalToken", text)
            self.assertIn("ExceptionToken", text)
            self.assertTrue(payload["has_more"])
            self.assertTrue(payload["gaps"])
            self.assertEqual(payload["facets"][0]["evidence_status"], "unverified-candidates")
            self.assertTrue(payload["continuations"])
            pid = payload["passages"][0]["passage_id"]
            window = self.invoke("get", root / "index.sqlite", pid, "--around", "CriticalToken", "--max-chars", 800)
            self.assertIn("CriticalToken", window["results"][0]["text"])
            self.assertTrue(window["has_more"])
            self.assertTrue(window["prefix_continuations"])
            continued = self.invoke("get", root / "index.sqlite", pid, "--offset", window["next_offset"],
                                    "--start-char", window["next_start_char"])
            self.assertIn("background", continued["results"][0]["text"])

    def test_memory_meaning_subset_expansion_and_source_change_together(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "sources"
            corpus.mkdir()
            (corpus / "source.md").write_text("\n\n".join(f"# Part {i}\n\nAlpha rule {i}. Beta rule {i}." for i in range(6)), encoding="utf-8")
            questions = [self.question("A", "Alpha"), self.question("B", "Beta")]
            first = self.pack(root, corpus, questions)
            self.save(root, first)
            warm = self.pack(root, corpus, questions)
            self.assertEqual((warm["search_count"], warm["passages"], warm["finding_hits"]), (0, [], 2))
            self.pack(root, corpus, questions[1:])
            again = self.pack(root, corpus, questions)
            self.assertEqual(again["finding_hits"], 2)
            changed = self.pack(root, corpus, [dict(questions[0], question="Does Alpha forbid the action?"), questions[1]])
            self.assertEqual(changed["finding_hits"], 1)
            self.assertEqual(changed["searched_facets"], ["A"])
            # A larger retrieval budget alone does not invalidate a current answer.
            small = self.pack(root, corpus, questions)
            self.save(root, small)
            expanded = self.pack(root, corpus, questions, "--limit-per-query", 6, "--max-passages-per-question", 6)
            self.assertEqual(expanded["finding_hits"], 2)
            self.assertEqual(expanded["search_count"], 0)
            self.assertEqual(expanded["passages"], [])
            self.assertEqual(expanded["findings"], warm["findings"])
            self.save(root, expanded)
            receipt_path = root / "task.json"
            saved = json.loads(receipt_path.read_text())
            saved["conflicts"] = [{"facet_id": "A", "reason": "Human review remains open"}]
            saved["gaps"].append({"facet_id": "A", "reason": "Check applicability in amendment"})
            receipt_path.write_text(json.dumps(saved), encoding="utf-8")
            (corpus / "new.md").write_text("A newly authorized amendment.", encoding="utf-8")
            self.pack(root, corpus, questions[1:])
            saved = json.loads(receipt_path.read_text())
            by_id = {facet["id"]: facet for facet in saved["facets"]}
            self.assertEqual(set(by_id), {"A", "B"})
            self.assertTrue(by_id["A"]["stale"])
            self.assertEqual(by_id["A"]["finding"]["status"], "confirmed")
            self.assertTrue(by_id["A"]["finding"]["claims"])
            self.assertIn("previous_finding", by_id["B"])
            self.assertTrue(saved["conflicts"])
            self.assertEqual(saved["next_mode"], "retrieval")
            self.assertTrue(any(gap["reason"] == "Check applicability in amendment" for gap in saved["gaps"]))
            for generation in range(2):
                (corpus / "new.md").write_text(f"Amendment generation {generation}.", encoding="utf-8")
                self.pack(root, corpus, questions[1:])
                saved = json.loads(receipt_path.read_text())
                self.assertEqual(sum(gap == {"facet_id": "A", "reason": "source-changed"}
                                     for gap in saved["gaps"]), 1)

    def test_aliases_filters_and_unresolved_without_fabricated_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.jsonl"
            source.write_text("\n".join(json.dumps({"source": f"v{i}.md", "version": str(i),
                "text": "SharedTerm applies to this version."}) for i in range(2)), encoding="utf-8")
            question = self.question("A", "SharedTerm")
            payload = self.pack(root, source, [question])
            self.assertIn("also_in", payload["passages"][0])
            filtered = self.pack(root, source, [dict(question, version="1")])
            self.assertTrue(all(item["version"] == "1" for item in filtered["passages"]))
            self.assertFalse(any(item.get("also_in") for item in filtered["passages"]))
            findings = root / "findings.json"
            findings.write_text(json.dumps({"findings": [{"facet_id": "A", "claims": [],
                "reason": "No evidence for the requested interpretation"}]}), encoding="utf-8")
            self.invoke("findings-save", root / "task.json", findings)
            repeated = self.pack(root, source, [dict(question, version="1")])
            self.assertEqual(repeated["finding_hits"], 0)

    def test_mixed_findings_retain_each_assessment_and_reject_blanket_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("Alpha is specified; the applicability is unclear.", encoding="utf-8")
            question = self.question("A", "Alpha")
            packed = self.pack(root, source, [question])
            locator = packed["facets"][0]["passage_ids"]
            confirmed = {"text": "Alpha is specified.", "status": "confirmed", "basis": "Read explicit statement",
                         "scope": "Alpha statement", "passage_ids": locator}
            interpretation = {"text": "Alpha might apply to every case.", "status": "interpretation",
                              "basis": "Applicability is inferred", "scope": "All cases", "limits": "Unconfirmed applicability",
                              "passage_ids": locator}
            findings = root / "findings.json"
            document = [{"facet_id": "A", "claims": [confirmed, interpretation]}]
            findings.write_text(json.dumps(document), encoding="utf-8")
            self.invoke("findings-save", root / "task.json", findings)
            warm = self.pack(root, source, [question])
            self.assertEqual(warm["findings"][0]["status"], "interpretation")
            self.assertEqual([point["status"] for point in warm["findings"][0]["claims"]],
                             ["confirmed", "interpretation"])
            self.assertEqual(warm["search_count"], 0)
            self.assertEqual(warm["next_mode"], "retrieval")
            before = (root / "task.json").read_bytes()
            for invalid in (
                {**document[0], "status": "confirmed"},
                {"facet_id": "A", "claims": [{key: value for key, value in interpretation.items() if key != "limits"}]},
                {"facet_id": "A", "claims": [{key: value for key, value in confirmed.items() if key != "status"}]},
            ):
                findings.write_text(json.dumps([invalid]), encoding="utf-8")
                result = run_corpus_raw("findings-save", root / "task.json", findings)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual((root / "task.json").read_bytes(), before)
            expanded = self.pack(root, source, [question], "--max-passage-chars", 5000)
            prior = expanded["facets"][0]["previous_finding"]
            self.assertTrue(prior["source_current"])
            self.assertEqual(prior["finding"]["claims"][0]["status"], "confirmed")

    def test_oversized_final_receipt_refuses_save_and_preserves_readable_owner(self):
        from doc_research.common import MAX_BATCH_INPUT_BYTES, load_bounded_json
        from doc_research.evidence_pack import _write_task_receipt

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("Alpha is specified.", encoding="utf-8")
            packed = self.pack(root, source, [self.question("A", "Alpha")])
            receipt = root / "task.json"
            payload = json.loads(receipt.read_text())
            payload["conflicts"] = [{"description": ""}]
            serialized = lambda: (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
            # Fill the real receipt to exactly the reader cap, including UTF-8 bytes.
            remaining = MAX_BATCH_INPUT_BYTES - len(serialized())
            payload["conflicts"][0]["description"] = "я" * (remaining // 2) + "x" * (remaining % 2)
            _write_task_receipt(receipt, payload)
            self.assertEqual(receipt.stat().st_size, MAX_BATCH_INPUT_BYTES)
            self.assertEqual(load_bounded_json(receipt, "Task receipt"), payload)
            before = receipt.read_bytes()
            claim = {"text": "Alpha is specified.", "status": "confirmed", "basis": "Checked explicit wording",
                     "scope": "Alpha", "passage_ids": packed["facets"][0]["passage_ids"]}
            findings = root / "findings.json"
            findings.write_text(json.dumps([{"facet_id": "A", "claims": [claim]}]), encoding="utf-8")
            result = run_corpus_raw("findings-save", receipt, findings)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn("exceeds", result.stderr)
            self.assertEqual(receipt.read_bytes(), before)
            self.assertFalse(list(root.glob(".task.json.*.tmp")))

    def test_output_collisions_fail_before_any_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("Original Term source", encoding="utf-8")
            questions = root / "questions.json"
            questions.write_text(json.dumps({"questions": [self.question("A", "Term")]}), encoding="utf-8")
            alias = root / "source-alias.json"
            os.link(source, alias)
            for option, target in (("--pack-output", source), ("--task-receipt", source),
                                   ("--db", source), ("--receipts-db", alias), ("--pack-output", questions)):
                with self.subTest(option=option, target=target.name):
                    before = {p: p.read_bytes() for p in (source, alias, questions)}
                    result = run_corpus_raw("evidence-pack", source, questions, "--db", root / "index.sqlite",
                                            "--task-receipt", root / "task.json", option, target)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(before, {p: p.read_bytes() for p in before})
                    self.assertFalse((root / "index.sqlite").exists())
            payload = self.pack(root, source, [self.question("A", "Term")])
            self.save(root, payload)
            task = root / "task.json"
            saved = json.loads(task.read_text())
            saved["findings"] = [{"facet_id": "A", "status": "unresolved", "claims": []}]
            task.write_text(json.dumps(saved), encoding="utf-8")
            before = task.read_bytes()
            result = run_corpus_raw("findings-save", task, task)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(task.read_bytes(), before)

    def test_broken_schema_keeps_narrative_and_reports_incomplete_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text('# Narrative\n\nDeadline is Monday.\n\n```xsd\n<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><broken></xs:schema>\n```\n', encoding="utf-8")
            payload = self.pack(root, source, [self.question("A", "Deadline")])
            self.assertIn("Monday", payload["passages"][0]["text"])
            self.assertTrue(payload["schema_warnings"])
            warm = self.pack(root, source, [self.question("A", "Deadline")])
            self.assertEqual(warm["schema_warnings"], payload["schema_warnings"])
            structural = self.invoke("schema-query", root / "index.sqlite", "absent")
            self.assertTrue(structural["schema_warnings"])

    def test_schema_scope_filters_and_large_budget_do_not_broaden_or_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text('# Schema\n```xsd\n<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:element name="Root"><xs:complexType><xs:sequence><xs:element name="Optional" minOccurs="0"><xs:complexType><xs:attribute name="Key" use="required"/></xs:complexType></xs:element></xs:sequence></xs:complexType></xs:element></xs:schema>\n```', encoding="utf-8")
            question = dict(self.question("A", "Key"), kind="schema", verification="exact")
            payload = self.pack(root, source, [question], "--max-total-chars", 100000)
            self.assertTrue(payload["schema_facts"])
            facts = self.invoke("schema-query", root / "index.sqlite", "Key")
            self.assertIn("presence=conditional", json.dumps(facts))
            filtered = self.pack(root, source, [dict(question, section="Nonexistent")])
            self.assertEqual(filtered["schema_facts"], [])
            self.assertEqual(filtered["passages"], [])
