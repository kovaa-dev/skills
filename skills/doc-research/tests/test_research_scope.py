from __future__ import annotations

from test_support import *


class ResearchScopeCliTest(CorpusCliTestCase):
    def test_evidence_writes_enforce_frozen_scope_and_batch_atomicity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog, state = root / "catalog.sqlite", root / "research.sqlite"
            self.assertEqual(run_corpus("catalog-init", catalog).returncode, 0)
            for corpus_id, boundary in (("C", "team-a"), ("SAME", "team-a"), ("OTHER", "team-b")):
                result = run_corpus("catalog-put", catalog, corpus_id, "--adapter", "external",
                                    "--access-boundary", boundary, "--locator", f"wiki://{corpus_id}",
                                    "--generation", "1")
                self.assertEqual(result.returncode, 0, result.stderr)
            result = run_corpus("research-init", state, "--scope", "Frozen investigation",
                                "--catalog", catalog, "--corpus-id", "C", "--access-boundary", "team-a")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(run_corpus("research-put", state, "facet", "F", "--question", "Evidence?").returncode, 0)
            accepted = run_corpus("research-put", state, "evidence", "E", "--facet", "F",
                                  "--finding", "Allowed", "--source", "source", "--corpus-id", "C")
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            for corpus_id in ("SAME", "OTHER"):
                with self.subTest(corpus_id=corpus_id):
                    refused = run_corpus("research-put", state, "evidence", "E", "--corpus-id", corpus_id)
                    self.assertEqual(refused.returncode, 2)
                    self.assertIn("outside the research catalog scope", refused.stderr)
                    delta = root / "delta.json"
                    delta.write_text(json.dumps({"records": [
                        {"kind": "facet", "id": "ROLLBACK", "question": "Must roll back"},
                        {"kind": "evidence", "id": "BAD", "facet": "F", "finding": "Outside",
                         "source": "source", "corpus_id": corpus_id},
                    ]}), encoding="utf-8")
                    refused_batch = run_corpus("research-apply", state, delta)
                    self.assertEqual(refused_batch.returncode, 2)
                    self.assertIn("outside the research catalog scope", refused_batch.stderr)
            with closing(sqlite3.connect(state)) as connection:
                self.assertEqual(connection.execute("SELECT evidence_id, corpus_id, finding FROM evidence").fetchall(), [("E", "C", "Allowed")])
                self.assertEqual(connection.execute("SELECT facet_id FROM facets").fetchall(), [("F",)])

    def test_resume_marks_limited_open_work_as_truncated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            state = root / "research.sqlite"
            self.assertEqual(run_corpus("research-init", state, "--scope", "Review", "--corpus", corpus).returncode, 0)
            delta = root / "delta.json"
            delta.write_text(json.dumps({"records": [
                {"kind": "facet", "id": f"F{i:02d}", "question": f"Question {i}"} for i in range(12)
            ]}), encoding="utf-8")
            result = run_corpus("research-apply", state, delta)
            self.assertEqual(result.returncode, 0, result.stderr)
            limited = json.loads(run_corpus("research-info", state, "--resume").stdout)
            self.assertEqual(len(limited["active_facets"]), 8)
            self.assertTrue(limited["output_truncated"])
            complete = json.loads(run_corpus("research-info", state, "--resume", "--resume-limit", 12).stdout)
            self.assertEqual(len(complete["active_facets"]), 12)
            self.assertFalse(complete["output_truncated"])
