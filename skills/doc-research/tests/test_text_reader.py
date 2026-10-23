from __future__ import annotations

from test_support import *

from doc_research import text_reader


class TextReaderTest(unittest.TestCase):
    def read(self, source: Path, **options: object) -> tuple[dict, str]:
        values = dict(source=source, lines=[], find=[], context=3, max_chars=24000,
                      after_line=0, source_hash=None, memory_dir=None)
        values.update(options)
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(text_reader.command_read_text(argparse.Namespace(**values)), 0)
        return json.loads(output.getvalue()), output.getvalue()

    def test_physical_lines_preserve_unicode_and_formfeed_separators(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.txt"
            source.write_bytes("first\u2028still first\falso first\r\nsecond\nthird\r".encode("utf-8"))
            result, _ = self.read(source)
            self.assertEqual(result["lines"], [
                {"number": 1, "text": "first\u2028still first\falso first"},
                {"number": 2, "text": "second"}, {"number": 3, "text": "third\r"},
            ])

    def test_portable_memory_fallback_reads_notes_and_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source, memory = root / "source.txt", root / "memory"
            source.write_text("source evidence", encoding="utf-8")
            memory.mkdir()
            (memory / "note.md").write_text("saved note", encoding="utf-8")
            with mock.patch.dict(text_reader.os.__dict__):
                text_reader.os.__dict__.pop("O_NOFOLLOW", None)
                text_reader.os.__dict__.pop("O_NONBLOCK", None)
                result, _ = self.read(source, memory_dir=memory)
                self.assertEqual(result["memory"]["status"], "hit")
                self.assertEqual(result["memory"]["entries"][0]["text"], "saved note")
                (memory / "linked.txt").symlink_to(source)
                result, _ = self.read(source, memory_dir=memory)
                self.assertEqual(result["memory"]["status"], "incomplete")
                self.assertEqual(next(entry["status"] for entry in result["memory"]["entries"]
                                      if entry["name"] == "linked.txt"), "symlink")
                (root / "linked-dir").symlink_to(memory, target_is_directory=True)
                result, _ = self.read(source, memory_dir=root / "linked-dir")
                self.assertEqual(result["memory"]["status"], "incomplete")
                self.assertFalse(result["lines"])

    def test_ranges_and_literal_context_paginate_without_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.txt"
            source.write_text("\n".join(
                f"{number} " + ("A.*[B]" if number in (3, 5, 12) else "ordinary")
                for number in range(1, 15)
            ), encoding="utf-8")
            merged, _ = self.read(source, lines=["2:5", "4:7", "2"])
            self.assertEqual([line["number"] for line in merged["lines"]], list(range(2, 8)))
            context, _ = self.read(source, lines=["3"], find=["a.*[b]"], context=1)
            self.assertEqual([line["number"] for line in context["lines"]], [2, 3, 4])
            numbers, after_line, source_hash = [], 0, None
            while True:
                result, raw = self.read(source, lines=["2:6", "11:13"], find=["a.*[b]"],
                                        context=1, max_chars=320, after_line=after_line,
                                        source_hash=source_hash)
                self.assertLessEqual(len(raw), 320)
                self.assertEqual(result["total_selected_lines"], 8)
                numbers.extend(line["number"] for line in result["lines"])
                source_hash = result["source_hash"]
                after_line = result["next_after_line"]
                if after_line is None:
                    break
            self.assertEqual(numbers, [2, 3, 4, 5, 6, 11, 12, 13])
            source.write_text("changed", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "changed"):
                self.read(source, source_hash=source_hash)

    def test_memory_hit_precedes_selection_and_miss_searches_same_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source, memory = root / "source.txt", root / "memory"
            source.write_text("target\nother", encoding="utf-8")
            for state in ("absent", "empty"):
                if state == "empty":
                    memory.mkdir()
                result, _ = self.read(source, memory_dir=memory, find=["target"], context=0)
                self.assertEqual(result["memory"]["status"], "miss")
                self.assertEqual(result["lines"], [{"number": 1, "text": "target"}])
            cli = run_corpus_raw("read-text", source, "--memory-dir", memory,
                                 "--find", "target", "--context", "0")
            self.assertEqual(cli.returncode, 0, cli.stderr)
            cli_result = json.loads(cli.stdout)
            self.assertEqual(cli_result["memory"]["status"], "miss")
            self.assertEqual(cli_result["lines"], [{"number": 1, "text": "target"}])
            (memory / "note.md").write_text("Past assessment; check freshness.", encoding="utf-8")
            with mock.patch.object(text_reader, "_select_ranges", side_effect=AssertionError("searched")):
                result, _ = self.read(source, memory_dir=memory, find=["target"])
            self.assertEqual(result["memory"]["status"], "hit")
            self.assertEqual(result["memory"]["entries"][0]["text"], "Past assessment; check freshness.")
            self.assertFalse(result["lines"])
            self.assertTrue(result["source_hash"])
            self.assertEqual(sorted(p.name for p in root.iterdir()), ["memory", "source.txt"])

    def test_memory_unknown_symlinks_and_unreadable_are_never_misses(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source, memory = root / "source.txt", root / "memory"
            source.write_text("source evidence", encoding="utf-8")
            memory.mkdir()
            (memory / "unknown.bin").write_bytes(b"opaque")
            (memory / "subdir").mkdir()
            (memory / "link.md").symlink_to(source)
            os.link(source, memory / "hardlink.md")
            result, _ = self.read(source, memory_dir=memory)
            self.assertEqual(result["memory"]["status"], "incomplete")
            self.assertEqual({entry["status"] for entry in result["memory"]["entries"]},
                             {"unsupported", "directory", "symlink", "hardlink"})
            self.assertFalse(result["lines"])
            (root / "linked").symlink_to(memory, target_is_directory=True)
            result, _ = self.read(source, memory_dir=root / "linked")
            self.assertEqual(result["memory"]["status"], "incomplete")
            with mock.patch.object(text_reader.os, "scandir", side_effect=PermissionError("denied")):
                result, _ = self.read(source, memory_dir=memory)
            self.assertEqual(result["memory"]["status"], "incomplete")
            self.assertFalse(result["lines"])
            (memory / "private.md").write_text("private note", encoding="utf-8")
            real_open = os.open

            def deny_note(path, *args, **kwargs):
                if path == "private.md":
                    raise PermissionError("denied")
                return real_open(path, *args, **kwargs)

            with mock.patch.object(text_reader.os, "open", side_effect=deny_note):
                result, _ = self.read(source, memory_dir=memory)
            self.assertEqual(next(entry["status"] for entry in result["memory"]["entries"]
                                  if entry["name"] == "private.md"), "unreadable")
            self.assertFalse(result["lines"])

    def test_large_memory_returns_bounded_inventory_without_source_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source, memory = root / "source.txt", root / "memory"
            source.write_text("source evidence", encoding="utf-8")
            memory.mkdir()
            (memory / "large.md").write_text("x" * 10000, encoding="utf-8")
            result, raw = self.read(source, memory_dir=memory, max_chars=1000)
            self.assertLessEqual(len(raw), 1000)
            self.assertEqual(result["memory"]["status"], "incomplete")
            self.assertEqual(result["memory"]["entries"][0]["name"], "large.md")
            self.assertNotIn("text", result["memory"]["entries"][0])
            self.assertFalse(result["lines"])
            for number in range(30):
                (memory / f"note-{number}.txt").write_text("\\\"" * 20, encoding="utf-8")
            result, raw = self.read(source, memory_dir=memory, max_chars=1000)
            self.assertLessEqual(len(raw), 1000)
            self.assertEqual(result["memory"]["status"], "incomplete")
            self.assertGreater(result["memory"]["omitted_entries"], 0)
            self.assertFalse(result["lines"])

    def test_invalid_ranges_limits_encoding_and_overlong_lines_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.txt"
            source.write_text("first\nsecond", encoding="utf-8")
            for options in ({"lines": ["0"]}, {"lines": ["3"]}, {"lines": ["2:1"]},
                            {"lines": ["1:3"]}, {"lines": ["a"]}, {"context": -1},
                            {"max_chars": 0}, {"after_line": -1}, {"after_line": 3}):
                with self.subTest(options=options), self.assertRaises(ValueError):
                    self.read(source, **options)
            source.write_text("x" * 500, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "max-chars"):
                self.read(source, max_chars=100)
            for content in (b"binary\x00data", b"\xff"):
                source.write_bytes(content)
                with self.assertRaises(ValueError):
                    self.read(source)
            source.write_text("longer than cap", encoding="utf-8")
            with mock.patch.object(text_reader, "DEFAULT_MAX_SOURCE_BYTES", 4):
                with self.assertRaisesRegex(ValueError, "bytes"):
                    self.read(source)
            if hasattr(os, "mkfifo"):
                pipe = Path(directory) / "pipe"
                os.mkfifo(pipe)
                with self.assertRaisesRegex(ValueError, "regular"):
                    self.read(pipe)


if __name__ == "__main__":
    unittest.main()
