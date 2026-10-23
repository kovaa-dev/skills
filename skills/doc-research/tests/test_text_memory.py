from __future__ import annotations

from test_support import *
from doc_research import text_memory, text_reader


class TextMemoryTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "source.txt"
        self.source.write_text('first fact\nsecond "fact"\nthird fact\nfourth fact\n', encoding="utf-8")
        self.memory = self.root / "answer.json"
        self.hash = text_reader.source_snapshot(self.source)[0]

    def read(self, **options):
        args = dict(source=self.source, lines=[], find=[], context=0, max_chars=24000,
                    after_line=0, source_hash=None, memory_dir=None, memory=None,
                    scope=None, memory_offset=0, memory_hash=None)
        args.update(options)
        output = io.StringIO()
        with redirect_stdout(output):
            text_reader.command_read_text(argparse.Namespace(**args))
        raw = output.getvalue()
        self.assertLessEqual(len(raw), args["max_chars"])
        return json.loads(raw)

    def save(self, **options):
        args = dict(source=self.source, memory=self.memory, source_hash=self.hash,
                    scope="question A", points_file=None, reviewed=["fact"])
        point = dict(text=options.pop("answer", 'Answer: second "fact" (source line 2).'),
                     status="confirmed", basis="Checked original table", coverage="Line 2; no pending search",
                     limits="Does not establish other cases", cite=["2"], quote=['2=second "fact"'])
        for key in tuple(point) + ("depends_on", "exact"):
            if key in options:
                point[key] = options.pop(key)
        args["points"] = json.dumps(options.pop("points", {"fact": point}))
        args.update(options)
        output = io.StringIO()
        with redirect_stdout(output):
            text_memory.command_save_answer(argparse.Namespace(**args))
        return json.loads(output.getvalue())

    def test_cold_search_save_warm_without_search_or_unchanged_write(self):
        cold = self.read(memory=self.memory, scope="question A", find=["second"])
        self.assertEqual(cold["memory"]["status"], "miss")
        self.assertEqual([item["number"] for item in cold["lines"]], [2])
        self.assertTrue(self.save()["changed"])
        before = self.memory.read_bytes(), self.memory.stat().st_mtime_ns
        with mock.patch.object(text_reader, "_select_ranges", side_effect=AssertionError("searched")):
            warm = self.read(memory=self.memory, scope="question A", find=["second"])
        self.assertEqual(warm["memory"]["status"], "current")
        self.assertFalse(warm["lines"])
        self.assertIn('second "fact"', json.loads(warm["memory"]["text"])["points"]["fact"]["text"])
        self.assertEqual(before, (self.memory.read_bytes(), self.memory.stat().st_mtime_ns))
        self.assertFalse(self.save()["changed"])
        self.assertEqual(before, (self.memory.read_bytes(), self.memory.stat().st_mtime_ns))

    def test_scope_upsert_preserves_other_answers_and_stale_points_for_recheck(self):
        self.save()
        self.save(scope="question B", answer="Another answer")
        self.assertEqual(set(json.loads(self.memory.read_text())["entries"]), {"question A", "question B"})
        miss = self.read(memory=self.memory, scope="question C", find=["third"])
        self.assertEqual(miss["memory"]["status"], "candidates")
        self.assertFalse(miss["lines"])
        self.assertEqual(set(json.loads(miss["memory"]["text"])["entries"]), {"question A", "question B"})
        self.source.write_text("new fact", encoding="utf-8")
        result = self.read(memory=self.memory, scope="question A", find=["new"])
        self.assertEqual(result["memory"]["status"], "stale")
        self.assertFalse(result["lines"])
        point = json.loads(result["memory"]["text"])["points"]["fact"]
        self.assertIn('second "fact"', point["text"])
        self.assertFalse(point["source_current"])
        self.assertFalse(point["reusable"])
        candidates = self.read(memory=self.memory, scope="paraphrased")
        self.assertEqual(candidates["memory"]["status"], "candidates")
        self.assertFalse(candidates["lines"])
        self.assertEqual(set(json.loads(candidates["memory"]["text"])["entries"]), {"question A", "question B"})
        before = self.memory.read_bytes()
        with self.assertRaisesRegex(ValueError, "generation changed"):
            self.save()
        self.assertEqual(before, self.memory.read_bytes())

    def test_no_hit_state_is_preserved_as_unresolved_not_certified_absence(self):
        self.save(scope="missing item", status="unresolved", answer="No matches in selected scope",
                  coverage="Literal missing item; lines 1:4", limits="Not corpus-wide absence",
                  cite=[], quote=[])
        with mock.patch.object(text_reader, "_select_ranges", side_effect=AssertionError("searched")):
            result = self.read(memory=self.memory, scope="missing item", find=["missing item"])
        entry = json.loads(result["memory"]["text"])["points"]["fact"]
        self.assertEqual(entry["status"], "unresolved")
        self.assertEqual(entry["limits"], "Not corpus-wide absence")

    def test_complete_memory_continuation_and_changed_note_rejection(self):
        answer = 'text "quoted" \\ русский\n' * 100
        self.save(answer=answer)
        pages, offset, digest = [], 0, None
        for _ in range(100):
            result = self.read(memory=self.memory, scope="question A", memory_offset=offset,
                               memory_hash=digest, max_chars=700)
            memory = result["memory"]
            self.assertFalse(result["lines"])
            pages.append(memory["text"])
            digest, offset = memory["memory_hash"], memory["next_offset"]
            if offset is None:
                break
        else:
            self.fail("Memory continuation did not terminate")
        self.assertGreater(len(pages), 1)
        assembled = json.loads("".join(pages))["points"]["fact"]
        self.assertEqual(assembled["text"], answer)
        self.assertEqual(assembled["limits"], "Does not establish other cases")
        self.save(answer="changed answer")
        with self.assertRaisesRegex(ValueError, "Memory changed"):
            self.read(memory=self.memory, scope="question A", memory_offset=1, memory_hash=digest)
        with self.assertRaisesRegex(ValueError, "continuation"):
            self.read(memory=self.memory, scope="question A", memory_offset=1)

    def test_lost_output_does_not_suppress_evidence_or_write_state(self):
        before = sorted(self.root.iterdir())
        self.read(lines=["1:3"])  # Caller lost or truncated this response.
        retried = self.read(lines=["1:3"])
        self.assertEqual([v["number"] for v in retried["lines"]], [1, 2, 3])
        continued = self.read(lines=["1:4"], after_line=2, source_hash=self.hash)
        self.assertEqual([v["number"] for v in continued["lines"]], [3, 4])
        self.assertEqual(before, sorted(self.root.iterdir()))

    def test_budgeted_ranges_continue_with_explicit_cursor(self):
        self.source.write_text("\n".join(f'{n} "quote" \\ ' + "ю" * 20 for n in range(1, 31)), encoding="utf-8")
        options = dict(max_chars=450)
        numbers = []
        for _ in range(30):
            result = self.read(**options)
            numbers.extend(v["number"] for v in result["lines"])
            if result["next_after_line"] is None:
                break
            options.update(after_line=result["next_after_line"], source_hash=result["source_hash"])
        self.assertEqual(numbers, list(range(1, 31)))

    def test_memory_without_exact_scope_returns_candidates_without_source_decode(self):
        self.save()
        with mock.patch.object(text_reader, "_source_lines", side_effect=AssertionError("decoded source")):
            for scope in (None, "Paraphrased question"):
                result = self.read(memory=self.memory, scope=scope, find=["first"])
                self.assertEqual(result["memory"]["status"], "candidates")
                self.assertFalse(result["lines"])
                entry = json.loads(result["memory"]["text"])["entries"]["question A"]["points"]["fact"]
                self.assertTrue(entry["source_current"])
                self.assertEqual(entry["limits"], "Does not establish other cases")

    def test_candidate_continuation_retains_stale_labels_and_unresolved_limits(self):
        self.save(answer="Older answer " * 60)
        self.source.write_text("new evidence", encoding="utf-8")
        self.hash = text_reader.source_snapshot(self.source)[0]
        self.save(scope="question B", answer="Unresolved " * 60, status="unresolved",
                  cite=[], quote=[], limits="Not proof of absence")
        pages, offset, digest = [], 0, None
        for _ in range(100):
            result = self.read(memory=self.memory, memory_offset=offset, memory_hash=digest,
                               max_chars=700)
            self.assertFalse(result["lines"])
            page = result["memory"]
            self.assertEqual(page["status"], "candidates")
            pages.append(page["text"])
            offset, digest = page["next_offset"], page["memory_hash"]
            if offset is None:
                break
        else:
            self.fail("Candidate continuation did not terminate")
        entries = json.loads("".join(pages))["entries"]
        older, newer = (entries[key]["points"]["fact"] for key in ("question A", "question B"))
        self.assertFalse(older["source_current"])
        self.assertTrue(newer["source_current"])
        self.assertEqual(newer["status"], "unresolved")
        self.assertEqual(newer["limits"], "Not proof of absence")

    def test_quote_locator_collisions_and_foreign_files_fail_without_changes(self):
        for options in ({"quote": ["2=wrong quote"]}, {"cite": ["100"]},
                        {"cite": [], "quote": []}, {"memory": self.source},
                        {"memory": self.root / "missing" / "note.json"}):
            before = self.source.read_bytes()
            with self.assertRaises((ValueError, OSError)):
                self.save(**options)
            self.assertEqual(before, self.source.read_bytes())
        self.memory.write_text("existing unrelated note", encoding="utf-8")
        before = self.memory.read_bytes()
        with self.assertRaises(ValueError):
            self.save()
        with self.assertRaises(ValueError):
            self.read(memory=self.memory, scope="question A")
        self.assertEqual(before, self.memory.read_bytes())

    def test_cli_save_and_read_and_alias_safety(self):
        points = {"fact": {"text": "first fact", "status": "confirmed", "basis": "original",
                           "coverage": "line 1", "cite": ["1"]}}
        saved = run_corpus_raw("save-answer", self.source, "--memory", self.root / "cli.json",
                               "--scope", "question", "--source-hash", self.hash,
                               "--points", json.dumps(points), "--reviewed", "fact")
        self.assertEqual(saved.returncode, 0, saved.stderr)
        warm = run_corpus_raw("read-text", self.source, "--memory", self.root / "cli.json", "--scope", "question")
        self.assertEqual(warm.returncode, 0, warm.stderr)
        self.assertEqual(json.loads(warm.stdout)["memory"]["status"], "current")
        original = self.source.read_bytes()
        for kind in ("symlink", "hardlink"):
            alias = self.root / (kind + ".json")
            if kind == "symlink":
                alias.symlink_to(self.source)
            else:
                os.link(self.source, alias)
            with self.assertRaises((ValueError, OSError)):
                self.save(memory=alias)
            with self.assertRaises((ValueError, OSError)):
                self.read(memory=alias, scope="question A")
            self.assertEqual(self.source.read_bytes(), original)

    def test_trusted_parent_alias_and_tmp_work_without_allowing_linked_notes(self):
        alias = self.root / "trusted-parent"
        alias.symlink_to(self.root, target_is_directory=True)
        target = alias / "through-parent.json"
        self.assertTrue(self.save(memory=target)["changed"])
        warm = self.read(memory=target, scope="question A")
        self.assertEqual(warm["memory"]["status"], "current")
        linked = alias / "linked-note.json"
        linked.symlink_to(target.resolve())
        with self.assertRaises((OSError, ValueError)):
            self.read(memory=linked, scope="question A")
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            memory = Path(directory) / "answer.json"
            self.assertTrue(self.save(memory=memory)["changed"])
            self.assertEqual(self.read(memory=memory, scope="question A")["memory"]["status"], "current")

    def test_ambiguous_literal_never_promoted_by_save_or_warm_read(self):
        self.source.write_text("Components: A, B, date, UUID\nPrinted: TX_A_ _B_date_UUID.xml\n", encoding="utf-8")
        self.hash = text_reader.source_snapshot(self.source)[0]
        points = {
            "components": {"text": "Components are A, B, date, UUID", "status": "confirmed",
                           "basis": "Read the component definition", "coverage": "line 1", "cite": ["1"]},
            "template": {"text": "Possibly TX_A_B_date_UUID.xml", "status": "interpretation",
                         "basis": "Whitespace normalization would produce this spelling", "coverage": "line 2",
                         "limits": "Exact delimiters unresolved; do not use as a validated template", "cite": ["2"],
                         "quote": ["2=TX_A_ _B_date_UUID.xml"], "exact": ["TX_A_B_date_UUID.xml"]},
        }
        self.save(points=points, reviewed=["components"])
        before = self.memory.read_bytes()
        with mock.patch.object(text_reader, "_source_lines", side_effect=AssertionError("reverified source")):
            warm = self.read(memory=self.memory, scope="question A")
        returned = json.loads(warm["memory"]["text"])["points"]
        self.assertTrue(returned["components"]["reusable"])
        self.assertFalse(returned["template"]["reusable"])
        self.assertEqual(returned["template"]["status"], "interpretation")
        self.assertFalse(self.save(points=points, reviewed=[])["changed"])
        promoted = {**points["template"], "status": "confirmed"}
        with self.assertRaisesRegex(ValueError, "exact literals"):
            self.save(points={"template": promoted}, reviewed=["template"])
        self.assertEqual(self.memory.read_bytes(), before)
        # Verbatim spelling can be retained; the helper still does not certify its applicability.
        literal = "TX_A_ _B_date_UUID.xml"
        self.save(points={"template": {**promoted, "text": "Printed spelling: " + literal,
                                      "exact": [literal]}}, reviewed=["template"])

    def test_correction_invalidates_only_dependents_and_requires_explicit_review(self):
        base = dict(text="first fact", status="confirmed", basis="Read source", coverage="line 1", cite=["1"])
        points = {"base": base, "derived": {**base, "depends_on": ["base"]},
                  "downstream": {**base, "depends_on": ["derived"]}, "independent": base}
        self.save(points=points, reviewed=list(points))
        before = self.memory.read_bytes()
        correction = {**base, "text": "Corrected first fact"}
        with self.assertRaisesRegex(ValueError, "actual analyst review"):
            self.save(points={"base": correction}, reviewed=[])
        self.assertEqual(before, self.memory.read_bytes())
        result = self.save(points={"base": correction}, reviewed=["base"])
        self.assertEqual(set(result["invalidated"]), {"derived", "downstream"})
        saved = json.loads(self.memory.read_text())["entries"]["question A"]["points"]
        self.assertEqual(saved["independent"]["status"], "confirmed")
        self.assertEqual(saved["derived"]["status"], "unresolved")
        self.assertEqual(len(saved), 4)  # Correction replaces the point, not an appended conflicting copy.
        self.assertIn("review_required", saved["downstream"])
        with self.assertRaisesRegex(ValueError, "actual analyst review"):
            self.save(points={"derived": points["derived"]}, reviewed=[])
        self.save(points={key: points[key] for key in ("derived", "downstream")}, reviewed=["derived", "downstream"])
        self.assertFalse(self.save(points={"base": correction}, reviewed=[])["changed"])

    def test_invalid_dependencies_and_unsupported_confirmation_leave_memory_untouched(self):
        self.save()
        before = self.memory.read_bytes()
        base = dict(text="fact", status="confirmed", basis="Read source", coverage="line 1", cite=["1"])
        for points in (
            {"a": {**base, "depends_on": ["missing"]}},
            {"a": {**base, "depends_on": ["b"]}, "b": {**base, "depends_on": ["a"]}},
            {"a": {**base, "status": "interpretation", "limits": "Uncertain"}, "b": {**base, "depends_on": ["a"]}},
            {"a": {**base, "status": "unresolved"}},
            {"a": {**base, "status": []}},
            {"a": {key: value for key, value in base.items() if key != "status"}},
        ):
            with self.assertRaises(ValueError):
                self.save(points=points, reviewed=list(points))
            self.assertEqual(self.memory.read_bytes(), before)

    def test_duplicate_input_and_whole_answer_memory_fail_closed(self):
        self.save()
        before = self.memory.read_bytes()
        result = run_corpus_raw("save-answer", self.source, "--memory", self.memory,
                                "--scope", "question A", "--source-hash", self.hash,
                                "--points", '{"fact": {}, "fact": {}}')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Duplicate", result.stderr)
        self.assertEqual(before, self.memory.read_bytes())
        self.memory.write_text(json.dumps({"kind": text_memory.NOTE_KIND, "source": str(self.source),
                                           "entries": {"old": {"answer": "Whole answer", "status": "supported"}}}))
        old = self.memory.read_bytes()
        with self.assertRaisesRegex(ValueError, "point-scoped"):
            self.read(memory=self.memory)
        with self.assertRaisesRegex(ValueError, "point-scoped"):
            self.save()
        self.assertEqual(old, self.memory.read_bytes())

    def test_partial_refresh_does_not_relabel_untouched_points_current(self):
        self.save()
        self.source.write_text(self.source.read_text() + "new evidence\n", encoding="utf-8")
        self.hash = text_reader.source_snapshot(self.source)[0]
        new = dict(text="new evidence", status="confirmed", basis="Read appended line", coverage="line 5", cite=["5"])
        self.save(points={"new": new}, reviewed=["new"])
        result = self.read(memory=self.memory, scope="question A", find=["first"])
        self.assertEqual(result["memory"]["status"], "partial")
        self.assertFalse(result["lines"])
        points = json.loads(result["memory"]["text"])["points"]
        self.assertFalse(points["fact"]["source_current"])
        self.assertFalse(points["fact"]["reusable"])
        self.assertTrue(points["new"]["reusable"])


if __name__ == "__main__":
    unittest.main()
