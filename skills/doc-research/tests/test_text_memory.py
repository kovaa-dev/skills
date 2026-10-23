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
        self.state = self.root / "reads.json"
        self.hash = text_reader.source_snapshot(self.source)[0]

    def read(self, **options):
        args = dict(source=self.source, lines=[], find=[], context=0, max_chars=24000,
                    after_line=0, source_hash=None, memory_dir=None, memory=None,
                    scope=None, memory_offset=0, memory_hash=None, read_state=None,
                    session=None, reread=False)
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
        self.assertEqual(miss["memory"]["status"], "scope-miss")
        self.assertEqual(miss["lines"][0]["number"], 3)
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

    def test_read_state_suppresses_only_current_context_and_version_with_escape_hatch(self):
        options = dict(read_state=self.state, session="context-1")
        first = self.read(lines=["1:3"], **options)
        second = self.read(lines=["2:4"], **options)
        self.assertEqual([v["number"] for v in second["lines"]], [4])
        self.assertEqual(second["suppressed_lines"], 2)
        self.assertIsNone(second["next_after_line"])
        reread = self.read(lines=["2:4"], reread=True, **options)
        self.assertEqual([v["number"] for v in reread["lines"]], [2, 3, 4])
        new = self.read(lines=["1:4"], read_state=self.state, session="context-2")
        self.assertEqual(len(new["lines"]), 4)
        self.source.write_text("changed", encoding="utf-8")
        self.assertEqual(self.read(**options)["lines"][0]["text"], "changed")
        self.assertNotIn("answer", json.loads(self.state.read_text()))
        with self.assertRaisesRegex(ValueError, "together"):
            self.read(read_state=self.state)

    def test_budgeted_ranges_continue_and_failure_does_not_mark_emitted(self):
        self.source.write_text("\n".join(f'{n} "quote" \\ ' + "ю" * 20 for n in range(1, 31)), encoding="utf-8")
        options = dict(read_state=self.state, session="one", max_chars=450)
        numbers = []
        for _ in range(30):
            result = self.read(**options)
            numbers.extend(v["number"] for v in result["lines"])
            if result["next_after_line"] is None:
                break
        self.assertEqual(numbers, list(range(1, 31)))
        before = self.state.read_bytes()
        with self.assertRaisesRegex(ValueError, "max-chars"):
            self.read(**{**options, "max_chars": 10, "reread": True})
        self.assertEqual(before, self.state.read_bytes())

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
        with self.assertRaises(ValueError):
            self.read(read_state=self.source, session="one")
        with self.assertRaises(ValueError):
            self.read(memory=self.memory, scope="question A", read_state=self.memory, session="one")

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
                self.read(read_state=alias, session="one")
            self.assertEqual(self.source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
