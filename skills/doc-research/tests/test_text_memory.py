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
                    scope="question A", answer='Answer: second "fact" (source line 2).',
                    answer_file=None, basis="Checked original table", coverage="Line 2; no pending search",
                    limits="Does not establish other cases", cite=["2"], quote=['2=second "fact"'])
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
        self.assertIn('second "fact"', json.loads(warm["memory"]["text"])["answer"])
        self.assertEqual(before, (self.memory.read_bytes(), self.memory.stat().st_mtime_ns))
        self.assertFalse(self.save()["changed"])
        self.assertEqual(before, (self.memory.read_bytes(), self.memory.stat().st_mtime_ns))

    def test_scope_upsert_preserves_other_answers_and_stale_version_falls_through(self):
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
        self.assertEqual(result["lines"][0]["text"], "new fact")
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
        entry = json.loads(result["memory"]["text"])
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
        assembled = json.loads("".join(pages))
        self.assertEqual(assembled["answer"], answer)
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
                entry = json.loads(result["memory"]["text"])["entries"]["question A"]
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
        self.assertFalse(entries["question A"]["source_current"])
        self.assertTrue(entries["question B"]["source_current"])
        self.assertEqual(entries["question B"]["status"], "unresolved")
        self.assertEqual(entries["question B"]["limits"], "Not proof of absence")

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
        saved = run_corpus_raw("save-answer", self.source, "--memory", self.root / "cli.json",
                               "--scope", "question", "--source-hash", self.hash,
                               "--answer", "first fact", "--basis", "original", "--coverage", "line 1", "--cite", "1")
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


if __name__ == "__main__":
    unittest.main()
