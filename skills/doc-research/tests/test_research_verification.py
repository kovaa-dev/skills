from __future__ import annotations

from test_support import *

from doc_research.research_records import research_put_namespace, write_research_record
from doc_research.research_store import create_research_schema
from doc_research import research_store as RESEARCH_STORE
from doc_research.research_records import command_research_list
from doc_research.cli import parser


class ResearchVerificationTest(unittest.TestCase):
    def test_changed_evidence_does_not_inherit_verification(self) -> None:
        with closing(sqlite3.connect(":memory:")) as connection:
            connection.row_factory = sqlite3.Row
            create_research_schema(connection)

            def put(record: dict[str, object]) -> None:
                write_research_record(
                    connection, research_put_namespace(Path("unused"), record), "2026-10-23"
                )

            put({"kind": "facet", "id": "rule", "question": "Which rule applies?"})
            put({"kind": "evidence", "id": "proof", "facet": "rule",
                 "finding": "A is required", "source": "rules.md", "source_version": "v1",
                 "verified": True})
            put({"kind": "evidence", "id": "proof", "source_version": "v1"})
            self.assertEqual(connection.execute("SELECT verified FROM evidence").fetchone()[0], 1)

            put({"kind": "evidence", "id": "proof", "finding": "B is required",
                 "source_version": "v2"})
            changed = connection.execute("SELECT finding, source_version, verified FROM evidence").fetchone()
            self.assertEqual(tuple(changed), ("B is required", "v2", 0))

            put({"kind": "evidence", "id": "proof", "finding": "C is required",
                 "verified": True})
            self.assertEqual(connection.execute("SELECT verified FROM evidence").fetchone()[0], 1)

            put({"kind": "facet", "id": "rule", "question": "Which exception applies?"})
            self.assertEqual(connection.execute("SELECT verified FROM evidence").fetchone()[0], 0)


class ResearchFreshnessCliTest(CorpusCliTestCase):
    def test_jsonl_input_freshness_hashes_once_without_confusing_original_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            source = corpus / "source.jsonl"
            source.write_text("\n".join(json.dumps({"source": name, "source_hash": "a" * 64,
                                                    "text": name + " evidence"})
                                          for name in ("A", "B")), encoding="utf-8")
            index, research = root / "index.sqlite", root / "research.sqlite"
            for args in (("index", corpus, "--db", index),
                         ("research-init", research, "--scope", "review", "--corpus", corpus, "--index", index),
                         ("research-put", research, "facet", "F", "--question", "Question")):
                result = run_corpus(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
            with closing(sqlite3.connect(index)) as connection:
                rows = connection.execute("SELECT rowid, source FROM chunks").fetchall()
            for passage, name in rows:
                result = run_corpus("research-put", research, "evidence", name, "--facet", "F",
                                    "--finding", name + " finding", "--source", name,
                                    "--source-hash", "a" * 64, "--passage-id", passage,
                                    "--verified", "true", "--status", "confirmed")
                self.assertEqual(result.returncode, 0, result.stderr)
            args = parser().parse_args(["research-list", str(research), "evidence"])
            with mock.patch.object(RESEARCH_STORE, "sha256_file", wraps=RESEARCH_STORE.sha256_file) as hashed, redirect_stdout(io.StringIO()) as stdout:
                command_research_list(args)
            self.assertEqual(hashed.call_count, 1)
            self.assertTrue(all(item["reusable"] for item in json.loads(stdout.getvalue())["records"]))
            source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            changed = json.loads(run_corpus("research-list", research, "evidence").stdout)
            self.assertTrue(all(not item["source_current"] for item in changed["records"]))

    def test_sync_cannot_reconfirm_changed_dependencies_and_preserves_unchanged_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            for name in ("stable", "changed"):
                (corpus / f"{name}.txt").write_text(f"{name} rule applies.", encoding="utf-8")
            index, research = root / "index.sqlite", root / "research.sqlite"

            def run(*args: object) -> dict[str, object]:
                result = run_corpus(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)

            run("index", corpus, "--db", index)
            run("research-init", research, "--scope", "rules", "--corpus", corpus, "--index", index)
            run("research-put", research, "facet", "F", "--question", "Which rule applies?")
            with closing(sqlite3.connect(index)) as connection:
                sources = connection.execute("SELECT rowid, source, source_hash FROM chunks").fetchall()
            for passage_id, source, digest in sources:
                run("research-put", research, "evidence", source.split(".")[0], "--facet", "F",
                    "--finding", "The rule applies", "--source", source, "--source-hash", digest,
                    "--passage-id", passage_id, "--status", "confirmed", "--verified", "true")
            initial = run("research-list", research, "evidence")
            self.assertTrue(all(item["reusable"] for item in initial["records"]))
            (corpus / "changed.txt").write_text("Changed exception supersedes the rule.", encoding="utf-8")
            unindexed = {item["evidence_id"]: item for item in run("research-list", research, "evidence")["records"]}
            self.assertFalse(unindexed["changed"]["source_current"])
            self.assertTrue(unindexed["stable"]["reusable"])
            run("index", corpus, "--db", index)
            before = {item["evidence_id"]: item for item in run("research-list", research, "evidence")["records"]}
            self.assertFalse(before["changed"]["reusable"])
            self.assertTrue(before["stable"]["reusable"])
            synced = run("research-sync", research)
            self.assertEqual(synced["invalidated_evidence"], 1)
            after = {item["evidence_id"]: item for item in run("research-list", research, "evidence")["records"]}
            self.assertFalse(after["changed"]["verified"])
            self.assertEqual(after["changed"]["status"], "unresolved")
            self.assertTrue(after["stable"]["reusable"])
            self.assertEqual(run("research-sync", research)["invalidated_evidence"], 0)
            resume = run("research-info", research, "--resume")
            self.assertFalse(next(item for item in resume["evidence"] if item["evidence_id"] == "changed")["reusable"])
            run("research-put", research, "facet", "F", "--question", "Which exception applies?")
            final = run("research-list", research, "evidence")
            self.assertTrue(all(not item["verified"] and not item["reusable"] for item in final["records"]))

    def test_verification_marker_alone_does_not_imply_confirmed_semantics(self) -> None:
        with closing(sqlite3.connect(":memory:")) as connection:
            connection.row_factory = sqlite3.Row
            create_research_schema(connection)
            for record in (
                {"kind": "facet", "id": "F", "question": "Question"},
                {"kind": "evidence", "id": "E", "facet": "F", "finding": "A lead",
                 "source": "source.txt", "verified": True},
            ):
                write_research_record(connection, research_put_namespace(Path("unused"), record), "now")
            self.assertEqual(connection.execute("SELECT status FROM evidence").fetchone()[0], "unresolved")
