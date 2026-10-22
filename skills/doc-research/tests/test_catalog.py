from __future__ import annotations

from test_support import *


class CatalogCliTest(CorpusCliTestCase):
    def test_catalog_federates_local_corpora_and_resumes_catalog_research(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "catalog.sqlite"
            self.assertEqual(run_corpus("catalog-init", catalog).returncode, 0)

            for corpus_id, text in (
                ("project-a", "Needle evidence from alpha."),
                ("project-b", "Needle evidence from beta."),
            ):
                corpus = root / corpus_id
                corpus.mkdir()
                (corpus / "source.txt").write_text(text, encoding="utf-8")
                index = root / f"{corpus_id}-index.sqlite"
                receipts = root / f"{corpus_id}-receipts.sqlite"
                self.assertEqual(
                    run_corpus("index", corpus, "--db", index).returncode, 0
                )
                self.assertEqual(
                    run_corpus(
                        "receipts-init",
                        receipts,
                        "--corpus",
                        corpus,
                        "--index",
                        index,
                    ).returncode,
                    0,
                )
                registered = run_corpus(
                    "catalog-put",
                    catalog,
                    corpus_id,
                    "--adapter",
                    "local-index",
                    "--access-boundary",
                    "workspace",
                    "--index",
                    index,
                    "--receipts-db",
                    receipts,
                )
                self.assertEqual(registered.returncode, 0, registered.stderr)

            first = run_corpus("catalog-search", catalog, "needle", "--limit", 4)
            self.assertEqual(first.returncode, 0, first.stderr)
            payload = json.loads(first.stdout)
            self.assertFalse(payload["receipt_hit"])
            self.assertEqual(
                {result["corpus_id"] for result in payload["results"]},
                {"project-a", "project-b"},
            )
            locators = [
                f"{result['corpus_id']}={result['passage_id']}"
                for result in payload["results"]
            ]
            fetched = run_corpus("catalog-get", catalog, *locators)
            self.assertEqual(fetched.returncode, 0, fetched.stderr)
            self.assertEqual(json.loads(fetched.stdout)["result_count"], 2)

            repeated = json.loads(
                run_corpus("catalog-search", catalog, "needle", "--limit", 4).stdout
            )
            self.assertTrue(repeated["receipt_hit"])
            self.assertTrue(all("text" not in item for item in repeated["results"]))

            research = root / "research.sqlite"
            self.assertEqual(
                run_corpus(
                    "research-init",
                    research,
                    "--scope",
                    "Cross-project review",
                    "--catalog",
                    catalog,
                ).returncode,
                0,
            )
            self.assertEqual(
                run_corpus(
                    "research-put", research, "facet", "F1", "--question", "Evidence?"
                ).returncode,
                0,
            )
            ambiguous_evidence = run_corpus(
                "research-put",
                research,
                "evidence",
                "E1",
                "--facet",
                "F1",
                "--finding",
                "Needle found.",
                "--source",
                "source.txt",
            )
            self.assertEqual(ambiguous_evidence.returncode, 2)
            self.assertIn("--corpus-id is required", ambiguous_evidence.stderr)
            saved_evidence = run_corpus(
                "research-put",
                research,
                "evidence",
                "E1",
                "--facet",
                "F1",
                "--corpus-id",
                "project-a",
                "--finding",
                "Needle found.",
                "--source",
                "source.txt",
                "--passage-id",
                "1",
            )
            self.assertEqual(saved_evidence.returncode, 0, saved_evidence.stderr)
            listed_evidence = json.loads(
                run_corpus("research-list", research, "evidence").stdout
            )
            self.assertEqual(listed_evidence["records"][0]["corpus_id"], "project-a")
            linked = run_corpus(
                "catalog-search",
                catalog,
                "needle",
                "--limit",
                4,
                "--research-db",
                research,
                "--facet-id",
                "F1",
            )
            self.assertEqual(linked.returncode, 0, linked.stderr)
            resume = json.loads(
                run_corpus("research-info", research, "--resume").stdout
            )
            self.assertEqual(resume["binding_kind"], "catalog")
            self.assertEqual(resume["recent_receipts"][0]["store_kind"], "catalog")
            self.assertTrue(resume["recent_receipts"][0]["current"])

    def test_catalog_requires_explicit_scope_and_partial_external_search(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "catalog.sqlite"
            self.assertEqual(run_corpus("catalog-init", catalog).returncode, 0)
            for corpus_id, boundary in (("wiki-a", "team-a"), ("wiki-b", "team-b")):
                registered = run_corpus(
                    "catalog-put",
                    catalog,
                    corpus_id,
                    "--adapter",
                    "external",
                    "--access-boundary",
                    boundary,
                    "--locator",
                    f"wiki://{corpus_id}",
                    "--generation",
                    "v1",
                )
                self.assertEqual(registered.returncode, 0, registered.stderr)

            project = run_corpus(
                "catalog-project-put",
                catalog,
                "team-a-project",
                "--access-boundary",
                "team-a",
                "--anchor-kind",
                "manual",
                "--anchor",
                "team-a-project",
                "--corpus-id",
                "wiki-a",
            )
            self.assertEqual(project.returncode, 0, project.stderr)
            cross_boundary = run_corpus(
                "catalog-project-put",
                catalog,
                "invalid-project",
                "--access-boundary",
                "team-a",
                "--anchor-kind",
                "manual",
                "--anchor",
                "invalid-project",
                "--corpus-id",
                "wiki-b",
            )
            self.assertEqual(cross_boundary.returncode, 2)
            self.assertIn("access boundaries differ", cross_boundary.stderr)
            moved_boundary = run_corpus(
                "catalog-put",
                catalog,
                "wiki-a",
                "--adapter",
                "external",
                "--access-boundary",
                "team-b",
                "--locator",
                "wiki://wiki-a",
                "--generation",
                "v1",
            )
            self.assertEqual(moved_boundary.returncode, 2)
            self.assertIn("cannot be changed in place", moved_boundary.stderr)

            broad = run_corpus("catalog-search", catalog, "needle")
            self.assertEqual(broad.returncode, 2)
            self.assertIn("multiple access boundaries", broad.stderr)
            unavailable = run_corpus(
                "catalog-search", catalog, "needle", "--access-boundary", "team-a"
            )
            self.assertEqual(unavailable.returncode, 2)
            self.assertIn("external or unavailable adapter", unavailable.stderr)
            before_readonly = catalog.read_bytes()
            readonly_partial = run_corpus(
                "catalog-search",
                catalog,
                "needle",
                "--access-boundary",
                "team-a",
                "--allow-partial",
                "--read-only",
            )
            self.assertEqual(readonly_partial.returncode, 0, readonly_partial.stderr)
            readonly_payload = json.loads(readonly_partial.stdout)
            self.assertFalse(readonly_payload["coverage_complete"])
            self.assertFalse(readonly_payload["receipt_persisted"])
            self.assertEqual(catalog.read_bytes(), before_readonly)
            partial = run_corpus(
                "catalog-search",
                catalog,
                "needle",
                "--access-boundary",
                "team-a",
                "--allow-partial",
            )
            self.assertEqual(partial.returncode, 0, partial.stderr)
            payload = json.loads(partial.stdout)
            self.assertEqual(payload["results"], [])
            self.assertEqual(payload["unsearched_corpora"][0]["corpus_id"], "wiki-a")
            self.assertFalse(payload["has_more"])
            self.assertFalse(payload["coverage_complete"])
            self.assertNotIn("next_offset", payload)

            research = root / "research.sqlite"
            self.assertEqual(
                run_corpus(
                    "research-init",
                    research,
                    "--scope",
                    "Selected remote scope",
                    "--catalog",
                    catalog,
                    "--access-boundary",
                    "team-a",
                ).returncode,
                0,
            )
            self.assertEqual(
                run_corpus(
                    "research-put", research, "facet", "F1", "--question", "Evidence?"
                ).returncode,
                0,
            )
            outside_scope = run_corpus(
                "catalog-search",
                catalog,
                "needle",
                "--access-boundary",
                "team-b",
                "--allow-partial",
                "--research-db",
                research,
                "--facet-id",
                "F1",
            )
            self.assertEqual(outside_scope.returncode, 2)
            self.assertIn("outside the research catalog scope", outside_scope.stderr)
            linked_partial = run_corpus(
                "catalog-search",
                catalog,
                "needle",
                "--access-boundary",
                "team-a",
                "--allow-partial",
                "--research-db",
                research,
                "--facet-id",
                "F1",
            )
            self.assertEqual(linked_partial.returncode, 0, linked_partial.stderr)
            resume = json.loads(
                run_corpus("research-info", research, "--resume").stdout
            )
            self.assertEqual(resume["recent_receipts"][0]["store_kind"], "catalog")

    def test_catalog_projects_overlap_resolve_and_freeze_research_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / "workspace"
            nested = workspace / "nested"
            nested.mkdir(parents=True)
            catalog = root / "catalog.sqlite"
            self.assertEqual(run_corpus("catalog-init", catalog).returncode, 0)

            for corpus_id, text in (
                ("shared", "Needle shared evidence."),
                ("alpha", "Needle alpha evidence."),
                ("beta", "Needle beta evidence."),
            ):
                corpus = root / corpus_id
                corpus.mkdir()
                (corpus / "source.txt").write_text(text, encoding="utf-8")
                index = root / f"{corpus_id}.index.sqlite"
                receipts = root / f"{corpus_id}.receipts.sqlite"
                self.assertEqual(
                    run_corpus("index", corpus, "--db", index).returncode, 0
                )
                self.assertEqual(
                    run_corpus(
                        "receipts-init",
                        receipts,
                        "--corpus",
                        corpus,
                        "--index",
                        index,
                    ).returncode,
                    0,
                )
                self.assertEqual(
                    run_corpus(
                        "catalog-put",
                        catalog,
                        corpus_id,
                        "--adapter",
                        "local-index",
                        "--access-boundary",
                        "workspace",
                        "--index",
                        index,
                        "--receipts-db",
                        receipts,
                    ).returncode,
                    0,
                )

            parent = run_corpus(
                "catalog-project-put",
                catalog,
                "parent",
                "--access-boundary",
                "workspace",
                "--anchor-kind",
                "filesystem",
                "--anchor",
                workspace,
                "--corpus-id",
                "shared",
                "--corpus-id",
                "alpha",
            )
            self.assertEqual(parent.returncode, 0, parent.stderr)
            child = run_corpus(
                "catalog-project-put",
                catalog,
                "child",
                "--access-boundary",
                "workspace",
                "--anchor-kind",
                "filesystem",
                "--anchor",
                nested,
                "--corpus-id",
                "shared",
                "--corpus-id",
                "beta",
            )
            self.assertEqual(child.returncode, 0, child.stderr)

            resolved = json.loads(
                run_corpus(
                    "catalog-project-resolve",
                    catalog,
                    "--anchor-kind",
                    "filesystem",
                    "--anchor",
                    nested / "document.md",
                ).stdout
            )
            self.assertTrue(resolved["resolved"])
            self.assertEqual(resolved["project_id"], "child")
            self.assertEqual(resolved["related_projects"][0]["project_id"], "parent")

            searched = run_corpus(
                "catalog-search",
                catalog,
                "needle",
                "--project-id",
                "parent",
                "--project-id",
                "child",
                "--limit",
                6,
            )
            self.assertEqual(searched.returncode, 0, searched.stderr)
            payload = json.loads(searched.stdout)
            self.assertEqual(payload["project_ids"], ["parent", "child"])
            self.assertEqual(
                set(payload["corpus_ids"]), {"shared", "alpha", "beta"}
            )

            research = root / "research.sqlite"
            initialized = run_corpus(
                "research-init",
                research,
                "--scope",
                "Parent-only review",
                "--catalog",
                catalog,
                "--project-id",
                "parent",
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            before = json.loads(run_corpus("research-info", research).stdout)
            self.assertEqual(before["catalog_scope"]["project_ids"], ["parent"])
            self.assertEqual(
                set(before["catalog_scope"]["corpus_ids"]), {"shared", "alpha"}
            )

            expanded = run_corpus(
                "catalog-project-put",
                catalog,
                "parent",
                "--access-boundary",
                "workspace",
                "--anchor-kind",
                "filesystem",
                "--anchor",
                workspace,
                "--corpus-id",
                "beta",
            )
            self.assertEqual(expanded.returncode, 0, expanded.stderr)
            after = json.loads(run_corpus("research-info", research).stdout)
            self.assertEqual(
                set(after["catalog_scope"]["corpus_ids"]), {"shared", "alpha"}
            )
            self.assertFalse(after["catalog_stale"])

            auto_anchor = root / "unassigned"
            auto_anchor.mkdir()
            created = run_corpus(
                "catalog-project-resolve",
                catalog,
                "--anchor-kind",
                "filesystem",
                "--anchor",
                auto_anchor,
                "--access-boundary",
                "workspace",
                "--create",
                "--corpus-id",
                "beta",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            created_payload = json.loads(created.stdout)
            self.assertTrue(created_payload["resolved"])
            self.assertTrue(created_payload["project_id"].startswith("auto-"))
            repeated = json.loads(
                run_corpus(
                    "catalog-project-resolve",
                    catalog,
                    "--anchor-kind",
                    "filesystem",
                    "--anchor",
                    auto_anchor,
                    "--access-boundary",
                    "workspace",
                    "--create",
                    "--corpus-id",
                    "beta",
                ).stdout
            )
            self.assertEqual(repeated["project_id"], created_payload["project_id"])
            overview = json.loads(run_corpus("catalog-info", catalog).stdout)
            self.assertEqual(overview["project_count"], 3)
