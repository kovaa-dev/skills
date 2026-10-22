from __future__ import annotations

from test_support import *


class CatalogCliTest(CorpusCliTestCase):
    def test_catalog_derives_stable_ids_and_separate_labels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "catalog.sqlite"
            self.assertEqual(run_corpus("catalog-init", catalog).returncode, 0)

            registrations: list[dict[str, object]] = []
            for parent in ("first", "second"):
                corpus = root / parent / "Shared Docs"
                corpus.mkdir(parents=True)
                (corpus / "source.txt").write_text(parent, encoding="utf-8")
                index = root / f"{parent}.index.sqlite"
                receipts = root / f"{parent}.receipts.sqlite"
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
                registrations.append(json.loads(registered.stdout))

            first, second = registrations
            self.assertTrue(str(first["corpus_id"]).startswith("corpus-"))
            self.assertNotEqual(first["corpus_id"], second["corpus_id"])
            self.assertEqual(first["label"], "Shared Docs")
            self.assertEqual(second["label"], "Shared Docs")

            relabeled = run_corpus(
                "catalog-put",
                catalog,
                "--adapter",
                "local-index",
                "--access-boundary",
                "workspace",
                "--index",
                root / "first.index.sqlite",
                "--receipts-db",
                root / "first.receipts.sqlite",
                "--label",
                "Primary shared documents",
            )
            self.assertEqual(relabeled.returncode, 0, relabeled.stderr)
            relabeled_payload = json.loads(relabeled.stdout)
            self.assertEqual(relabeled_payload["corpus_id"], first["corpus_id"])
            self.assertEqual(relabeled_payload["label"], "Primary shared documents")

            repeated = run_corpus(
                "catalog-put",
                catalog,
                "--adapter",
                "local-index",
                "--access-boundary",
                "workspace",
                "--index",
                root / "first.index.sqlite",
                "--receipts-db",
                root / "first.receipts.sqlite",
            )
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            repeated_payload = json.loads(repeated.stdout)
            self.assertEqual(repeated_payload["corpus_id"], first["corpus_id"])
            self.assertEqual(repeated_payload["label"], "Primary shared documents")

            external = run_corpus(
                "catalog-put",
                catalog,
                "--adapter",
                "external",
                "--access-boundary",
                "workspace",
                "--locator",
                "wiki://knowledge/policies/security",
                "--generation",
                "v1",
            )
            self.assertEqual(external.returncode, 0, external.stderr)
            external_payload = json.loads(external.stdout)
            self.assertTrue(str(external_payload["corpus_id"]).startswith("corpus-"))
            self.assertEqual(external_payload["label"], "security")
            external_update = run_corpus(
                "catalog-put",
                catalog,
                "--adapter",
                "external",
                "--access-boundary",
                "workspace",
                "--locator",
                "wiki://knowledge/policies/security",
                "--generation",
                "v2",
            )
            self.assertEqual(external_update.returncode, 0, external_update.stderr)
            self.assertEqual(
                json.loads(external_update.stdout)["corpus_id"],
                external_payload["corpus_id"],
            )

            project_anchor = root / "Acme Workspace"
            project_anchor.mkdir()
            project = run_corpus(
                "catalog-project-put",
                catalog,
                "--access-boundary",
                "workspace",
                "--anchor-kind",
                "filesystem",
                "--anchor",
                project_anchor,
                "--corpus-id",
                first["corpus_id"],
            )
            self.assertEqual(project.returncode, 0, project.stderr)
            project_payload = json.loads(project.stdout)
            self.assertTrue(str(project_payload["project_id"]).startswith("project-"))
            self.assertEqual(project_payload["label"], "Acme Workspace")

            repeated_project = run_corpus(
                "catalog-project-put",
                catalog,
                "--access-boundary",
                "workspace",
                "--anchor-kind",
                "filesystem",
                "--anchor",
                project_anchor,
                "--label",
                "Shared workspace",
                "--corpus-id",
                second["corpus_id"],
            )
            self.assertEqual(repeated_project.returncode, 0, repeated_project.stderr)
            repeated_project_payload = json.loads(repeated_project.stdout)
            self.assertEqual(
                repeated_project_payload["project_id"], project_payload["project_id"]
            )
            self.assertEqual(repeated_project_payload["label"], "Shared workspace")
            preserved_project = run_corpus(
                "catalog-project-put",
                catalog,
                "--access-boundary",
                "workspace",
                "--anchor-kind",
                "filesystem",
                "--anchor",
                project_anchor,
                "--corpus-id",
                first["corpus_id"],
            )
            self.assertEqual(preserved_project.returncode, 0, preserved_project.stderr)
            self.assertEqual(
                json.loads(preserved_project.stdout)["label"], "Shared workspace"
            )

    def test_catalog_federates_local_corpora_and_resumes_catalog_research(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog = root / "catalog.sqlite"
            self.assertEqual(run_corpus("catalog-init", catalog).returncode, 0)

            for corpus_id, text in (
                ("corpus-a", "Needle evidence from alpha."),
                ("corpus-b", "Needle evidence from beta."),
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
                {"corpus-a", "corpus-b"},
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
                "corpus-a",
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
            self.assertEqual(listed_evidence["records"][0]["corpus_id"], "corpus-a")
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
            self.assertTrue(created_payload["project_id"].startswith("project-"))
            self.assertEqual(created_payload["project"]["label"], "unassigned")
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
