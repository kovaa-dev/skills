from __future__ import annotations

from test_support import *

from doc_research.research_records import research_put_namespace, write_research_record
from doc_research.research_store import create_research_schema


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
