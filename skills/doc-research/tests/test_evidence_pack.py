from __future__ import annotations

from test_support import *


class EvidencePackCliTest(CorpusCliTestCase):
    def test_schema_fragment_is_a_gap_with_replayable_generation_bound_query(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.xsd"
            source.write_text('<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                              '<xs:element name="LargeElement"><xs:annotation><xs:documentation>'
                              + "Long applicability detail. " * 500
                              + '</xs:documentation></xs:annotation></xs:element></xs:schema>', encoding="utf-8")
            questions = root / "questions.json"
            questions.write_text(json.dumps([{"id": "large", "question": "LargeElement?",
                                               "kind": "schema", "queries": ["LargeElement"]}]), encoding="utf-8")
            index, receipt = root / "index.sqlite", root / "task.json"
            result = run_corpus("evidence-pack", source, questions, "--db", index,
                                "--task-receipt", receipt, "--max-total-chars", 2000)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["schema_facts"])
            self.assertIn({"facet_id": "large", "reason": "schema-evidence-incomplete"}, payload["gaps"])
            marker = next(item for item in payload["facets"][0]["query_continuations"]
                          if item.get("tool") == "schema-query")
            self.assertEqual(marker["start_char"], 0)
            self.assertEqual(marker["index_fingerprint"], payload["index"]["fingerprint"])
            resumed = run_corpus("schema-query", index, marker["query"], "--offset", marker["offset"],
                                 "--start-char", marker["start_char"], "--expected-fingerprint", marker["index_fingerprint"],
                                 "--limit", 1, "--max-total-chars", 100000)
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            record = json.loads(resumed.stdout)["results"][0]
            self.assertEqual(record["name"], "LargeElement")
            self.assertIn("Long applicability detail.", record["documentation"])
            self.assertFalse(json.loads(receipt.read_text())["facets"][0]["schema_locators"])

    def test_multi_query_pack_walks_source_directory_once(self) -> None:
        from doc_research.cli import parser
        from doc_research.evidence_pack import evidence_pack_payload

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "rules.md").write_text("Alpha rule. Beta rule. Gamma rule.", encoding="utf-8")
            questions = root / "questions.json"
            questions.write_text(json.dumps([{"id": term, "question": term,
                                               "queries": [term]} for term in ("Alpha", "Beta", "Gamma")]), encoding="utf-8")
            args = parser().parse_args(["evidence-pack", str(corpus), str(questions), "--db", str(root / "index.sqlite"),
                                        "--task-receipt", str(root / "task.json")])
            original, walks = Path.rglob, []

            def tracked(path, pattern, *values, **options):
                if path == corpus.resolve():
                    walks.append(path)
                return original(path, pattern, *values, **options)

            with mock.patch.object(Path, "rglob", tracked):
                payload = evidence_pack_payload(args)
            self.assertEqual(payload["search_count"], 3)
            self.assertTrue(payload["passages"])
            self.assertEqual(len(walks), 1)

    def test_zero_hit_explicit_queries_get_one_deterministic_role_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text(
                "DestinationReceiver has minOccurs 1 and maxOccurs 1.",
                encoding="utf-8",
            )
            questions = root / "questions.json"
            questions.write_text(
                json.dumps(
                    {
                        "questions": [
                            {
                                "id": "receiver",
                                "question": "What constraints does DestinationReceiver use?",
                                "queries": [
                                    {
                                        "query": "unrelated long literal query",
                                        "mode": "literal",
                                        "role": "support",
                                    },
                                    {
                                        "query": "absent control wording",
                                        "mode": "literal",
                                        "role": "check",
                                    },
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = run_corpus(
                "evidence-pack",
                source,
                questions,
                "--db",
                root / "index.sqlite",
                "--task-receipt",
                root / "task-receipt.json",
                "--execution-route",
                "auto",
                "--pack-output",
                root / "pack.json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["search_count"], 4)
            self.assertEqual(payload["fallback_search_count"], 2)
            self.assertEqual(payload["optimization"]["query_fallback"], "used")
            self.assertEqual(payload["facets"][0]["coverage"], "support-and-check")

    def test_pack_distributes_budget_across_selected_passages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text(
                "# Alpha\n\nAlpha evidence " + "a" * 1800 + "\n\n"
                "# Beta\n\nBeta evidence " + "b" * 1800,
                encoding="utf-8",
            )
            questions = root / "questions.json"
            questions.write_text(
                json.dumps(
                    {
                        "questions": [
                            {
                                "id": "alpha",
                                "question": "Alpha evidence?",
                                "queries": [
                                    {"query": "alpha evidence", "role": "support"},
                                    {"query": "alpha exception", "role": "check"},
                                ],
                            },
                            {
                                "id": "beta",
                                "question": "Beta evidence?",
                                "queries": [
                                    {"query": "beta evidence", "role": "support"},
                                    {"query": "beta exception", "role": "check"},
                                ],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = run_corpus(
                "evidence-pack",
                source,
                questions,
                "--db",
                root / "index.sqlite",
                "--task-receipt",
                root / "task-receipt.json",
                "--execution-route",
                "low-overhead-worker",
                "--executor",
                "test-worker",
                "--worker-context",
                "capsule-no-parent-history-v1",
                "--max-total-chars",
                1000,
                "--max-passage-chars",
                800,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(len(payload["passages"]), 2)
            self.assertLessEqual(payload["characters"], 1000)
            self.assertEqual(len(payload["truncated_passage_ids"]), 2)

    def test_cold_pack_indexes_searches_checks_and_saves_compact_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text(
                "# General\n\nFile exchange 01 is signed by the sender.\n\n"
                "# Exception\n\nException pattern 07 omits the carrier signature.",
                encoding="utf-8",
            )
            questions = root / "questions.json"
            questions.write_text(
                json.dumps(
                    {
                        "questions": [
                            {
                                "id": "files",
                                "question": "Which exchange files and exceptions exist?",
                                "queries": [
                                    {"query": "file exchange", "role": "support"},
                                    {"query": "exception pattern", "role": "check"},
                                ],
                            },
                            {
                                "id": "signatures",
                                "question": "Who signs the exchange?",
                                "queries": [
                                    {"query": "signed sender", "role": "support"},
                                    {"query": "carrier signature", "role": "check"},
                                ],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            index = root / "index.sqlite"
            task_receipt = root / "task-receipt.json"

            result = run_corpus(
                "evidence-pack",
                source,
                questions,
                "--db",
                index,
                "--task-receipt",
                task_receipt,
                "--execution-route",
                "low-overhead-worker",
                "--executor",
                "test-worker",
                "--worker-context",
                "capsule-no-parent-history-v1",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)

            self.assertEqual(payload["retrieval"], "search")
            self.assertEqual(payload["search_count"], 4)
            self.assertTrue(payload["index"]["updated"])
            self.assertEqual(
                [facet["coverage"] for facet in payload["facets"]],
                ["support-and-check", "support-and-check"],
            )
            passage_ids = [item["passage_id"] for item in payload["passages"]]
            self.assertEqual(len(passage_ids), len(set(passage_ids)))
            self.assertEqual(len(payload["sources"]), 1)
            self.assertTrue(task_receipt.is_file())
            self.assertTrue((root / "index.receipts.sqlite").is_file())
            saved = json.loads(task_receipt.read_text(encoding="utf-8"))
            self.assertNotIn("task_receipt", payload)
            self.assertEqual(payload["gaps"], saved["gaps"])
            self.assertEqual(payload["next_mode"], saved["next_mode"])
            self.assertEqual(
                payload["execution"]["cold"]["route"], "low-overhead-worker"
            )
            self.assertEqual(
                payload["execution"]["cold"]["worker_context"],
                "capsule-no-parent-history-v1",
            )
            self.assertEqual(payload["optimization"]["context_transfer"], "capsule-only")
            self.assertEqual(payload["optimization"]["query_batch"], "bounded")
            self.assertEqual(payload["optimization"]["search_receipts"], "created")
            self.assertEqual(saved["optimization"], payload["optimization"])
            self.assertEqual(saved["facets"][0]["question"], "Which exchange files and exceptions exist?")
            self.assertEqual(saved["facets"][1]["question"], "Who signs the exchange?")
            self.assertNotIn("File exchange", json.dumps(saved))

    def test_warm_pack_reopens_task_receipt_without_searching(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text(
                "# Rule\n\nCargo mass is required in kilograms.\n\n"
                "# Variant\n\nOptional volume is measured in cubic metres.",
                encoding="utf-8",
            )
            questions = root / "questions.json"
            questions.write_text(
                json.dumps(
                    {
                        "questions": [
                            {
                                "id": "mass",
                                "question": "What mass is required?",
                                "queries": [
                                    {"query": "cargo mass", "role": "support"},
                                    {"query": "optional volume", "role": "check"},
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            index = root / "index.sqlite"
            task_receipt = root / "task-receipt.json"
            cold_command = (
                "evidence-pack",
                source,
                questions,
                "--db",
                index,
                "--task-receipt",
                task_receipt,
                "--execution-route",
                "low-overhead-worker",
                "--executor",
                "test-worker",
                "--worker-context",
                "capsule-no-parent-history-v1",
            )
            warm_command = (
                "evidence-pack",
                source,
                questions,
                "--db",
                index,
                "--task-receipt",
                task_receipt,
                "--execution-route",
                "coordinator-warm",
            )

            first = run_corpus(*cold_command)
            self.assertEqual(first.returncode, 0, first.stderr)
            first_payload = json.loads(first.stdout)
            redundant_worker = run_corpus(*cold_command)
            self.assertEqual(redundant_worker.returncode, 0, redundant_worker.stderr)
            self.assertEqual(json.loads(redundant_worker.stdout)["search_count"], 0)
            repeated = run_corpus(*warm_command)
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            payload = json.loads(repeated.stdout)

            self.assertEqual(payload["retrieval"], "task-receipt")
            self.assertEqual(payload["search_count"], 0)
            self.assertEqual(payload["receipt_hits"], 0)
            self.assertFalse(payload["index"]["updated"])
            self.assertEqual(payload["passages"], first_payload["passages"])
            self.assertEqual(payload["facets"], first_payload["facets"])
            self.assertEqual(payload["optimization"]["task_receipt"], "hit")
            self.assertEqual(payload["optimization"]["query_batch"], "skipped")
            self.assertEqual(
                payload["execution"]["cold"]["route"], "low-overhead-worker"
            )
            self.assertEqual(
                payload["execution"]["last"]["route"], "coordinator-warm"
            )

            source.write_text(
                source.read_text(encoding="utf-8") + "\n\nChanged source generation.",
                encoding="utf-8",
            )
            refused = run_corpus(*warm_command)
            self.assertEqual(refused.returncode, 2)
            self.assertIn("Task receipt is missing, stale", refused.stderr)

            changed = run_corpus(*cold_command)
            self.assertEqual(changed.returncode, 0, changed.stderr)
            changed_payload = json.loads(changed.stdout)
            self.assertEqual(changed_payload["retrieval"], "search")
            self.assertEqual(changed_payload["search_count"], 2)
            self.assertFalse(changed_payload["index"]["updated"])
            self.assertNotEqual(
                changed_payload["index"]["fingerprint"],
                payload["index"]["fingerprint"],
            )

    def test_automatic_plan_returns_support_and_structural_check(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text(
                "Foreign participant identifier is required; maxOccurs is 1.",
                encoding="utf-8",
            )
            questions = root / "questions.json"
            questions.write_text(
                json.dumps(
                    {
                        "questions": [
                            {
                                "id": "participant",
                                "question": "What foreign participant identifier is required?",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = run_corpus(
                "evidence-pack",
                source,
                questions,
                "--db",
                root / "index.sqlite",
                "--task-receipt",
                root / "task-receipt.json",
                "--execution-route",
                "low-overhead-worker",
                "--executor",
                "test-worker",
                "--worker-context",
                "capsule-no-parent-history-v1",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["search_count"], 3)
            self.assertEqual(payload["facets"][0]["coverage"], "support-and-check")
            self.assertEqual(len(payload["passages"]), 1)
            self.assertIn("receipt_store", payload)

    def test_pack_records_missing_control_as_a_named_gap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("Primary rule only.", encoding="utf-8")
            questions = root / "questions.json"
            questions.write_text(
                json.dumps(
                    {
                        "questions": [
                            {
                                "id": "rule",
                                "question": "What is the rule and its exception?",
                                "queries": [
                                    {"query": "primary rule", "role": "support"},
                                    {"query": "missing exception", "role": "check"},
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = run_corpus(
                "evidence-pack",
                source,
                questions,
                "--db",
                root / "index.sqlite",
                "--task-receipt",
                root / "task-receipt.json",
                "--execution-route",
                "low-overhead-worker",
                "--executor",
                "test-worker",
                "--worker-context",
                "capsule-no-parent-history-v1",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["facets"][0]["coverage"], "support-only")
            saved = json.loads(
                (root / "task-receipt.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                saved["gaps"],
                [{"facet_id": "rule", "reason": "control-not-found"}],
            )
            self.assertEqual(saved["next_mode"], "retrieval")

    def test_exact_lookup_does_not_require_a_control_query(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("Only the primary rule.", encoding="utf-8")
            questions = root / "questions.json"
            questions.write_text(
                json.dumps(
                    {
                        "questions": [
                            {
                                "id": "rule",
                                "question": "What is the primary rule?",
                                "queries": [
                                    {"query": "primary rule", "role": "support"}
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            result = run_corpus(
                "evidence-pack",
                source,
                questions,
                "--db",
                root / "index.sqlite",
                "--task-receipt",
                root / "task-receipt.json",
                "--execution-route",
                "low-overhead-worker",
                "--executor",
                "test-worker",
                "--worker-context",
                "capsule-no-parent-history-v1",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["search_count"], 1)
            self.assertEqual(payload["facets"][0]["verification"], "exact")
            self.assertEqual(payload["facets"][0]["coverage"], "support-only")
            findings = root / "findings.json"
            findings.write_text(
                json.dumps(
                    {
                        "findings": [
                            {
                                "facet_id": "rule",
                                "claims": [
                                    {
                                        "text": "The primary rule is present.",
                                        "status": "confirmed", "basis": "Checked the rule", "scope": "Primary rule",
                                        "passage_ids": payload["facets"][0][
                                            "support_passage_ids"
                                        ],
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            saved = run_corpus(
                "findings-save",
                root / "task-receipt.json",
                findings,
            )
            self.assertEqual(saved.returncode, 0, saved.stderr)
            self.assertEqual(
                json.loads(saved.stdout)["execution"]["last"]["route"],
                "coordinator-direct",
            )

    def test_control_verification_allows_followup_instead_of_forcing_a_plan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("Only the primary rule.", encoding="utf-8")
            questions = root / "questions.json"
            questions.write_text(
                json.dumps(
                    {
                        "questions": [
                            {
                                "id": "rule",
                                "question": "Does every case use the primary rule?",
                                "verification": "control",
                                "queries": [
                                    {"query": "primary rule", "role": "support"}
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = run_corpus(
                "evidence-pack",
                source,
                questions,
                "--db",
                root / "index.sqlite",
                "--task-receipt",
                root / "task-receipt.json",
                "--execution-route",
                "auto",
                "--pack-output",
                root / "pack.json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["facets"][0]["evidence_status"], "unverified-candidates")
            self.assertTrue(json.loads(result.stdout)["gaps"])

    def test_cold_coordinator_fallback_requires_a_reason(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("Rule and exception.", encoding="utf-8")
            questions = root / "questions.json"
            questions.write_text(json.dumps(["Rule and exception?"]), encoding="utf-8")

            result = run_corpus(
                "evidence-pack",
                source,
                questions,
                "--db",
                root / "index.sqlite",
                "--task-receipt",
                root / "task-receipt.json",
                "--execution-route",
                "coordinator-fallback",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("--fallback-reason is required", result.stderr)

            fallback = run_corpus(
                "evidence-pack",
                source,
                questions,
                "--db",
                root / "index.sqlite",
                "--task-receipt",
                root / "task-receipt.json",
                "--execution-route",
                "coordinator-fallback",
                "--fallback-reason",
                "model-routing-unavailable",
            )
            self.assertEqual(fallback.returncode, 0, fallback.stderr)
            payload = json.loads(fallback.stdout)
            self.assertEqual(
                payload["execution"]["cold"],
                {
                    "route": "coordinator-fallback",
                    "reason": "model-routing-unavailable",
                },
            )

    def test_cold_worker_requires_compact_no_history_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("Rule and exception.", encoding="utf-8")
            questions = root / "questions.json"
            questions.write_text(json.dumps(["Rule and exception?"]), encoding="utf-8")

            result = run_corpus(
                "evidence-pack",
                source,
                questions,
                "--db",
                root / "index.sqlite",
                "--task-receipt",
                root / "task-receipt.json",
                "--execution-route",
                "low-overhead-worker",
                "--executor",
                "test-worker",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn(
                "--worker-context capsule-no-parent-history-v1 is required",
                result.stderr,
            )

    def test_verified_findings_make_warm_hit_return_no_passages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text(
                "Cargo mass is required in kilograms. The exception also uses kilograms.",
                encoding="utf-8",
            )
            questions = root / "questions.json"
            questions.write_text(
                json.dumps(
                    {
                        "questions": [
                            {
                                "id": "mass",
                                "question": "What mass is required?",
                                "queries": [
                                    {"query": "cargo mass", "role": "support"},
                                    {"query": "exception kilograms", "role": "check"},
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            index = root / "index.sqlite"
            receipt = root / "task-receipt.json"
            cold = run_corpus(
                "evidence-pack",
                source,
                questions,
                "--db",
                index,
                "--task-receipt",
                receipt,
                "--execution-route",
                "low-overhead-worker",
                "--executor",
                "test-worker",
                "--worker-context",
                "capsule-no-parent-history-v1",
            )
            self.assertEqual(cold.returncode, 0, cold.stderr)
            cold_payload = json.loads(cold.stdout)
            facet = cold_payload["facets"][0]
            findings = root / "findings.json"
            findings.write_text(
                json.dumps(
                    {
                        "findings": [
                            {
                                "facet_id": "mass",
                                "claims": [
                                    {"text": "Invalid locator.", "passage_ids": [999],
                                     "status": "confirmed", "basis": "Checked source", "scope": "Mass"}
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            rejected = run_corpus(
                "findings-save",
                receipt,
                findings,
                "--execution-route",
                "low-overhead-worker",
                "--executor",
                "test-worker",
                "--worker-context",
                "capsule-no-parent-history-v1",
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("outside its facet", rejected.stderr)
            findings.write_text(
                json.dumps(
                    {
                        "findings": [
                            {
                                "facet_id": "mass",
                                "claims": [
                                    {
                                        "text": "Cargo mass is required in kilograms.",
                                        "status": "confirmed", "basis": "Read mass definition", "scope": "Cargo mass",
                                        "passage_ids": facet["passage_ids"],
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            saved = run_corpus(
                "findings-save",
                receipt,
                findings,
                "--execution-route",
                "low-overhead-worker",
                "--executor",
                "test-worker",
                "--worker-context",
                "capsule-no-parent-history-v1",
            )
            self.assertEqual(saved.returncode, 0, saved.stderr)
            saved_receipt = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(
                saved_receipt["facets"][0]["locators"][0]["source"], "source.md"
            )
            self.assertNotIn("text", saved_receipt["facets"][0]["locators"][0])

            warm = run_corpus(
                "evidence-pack",
                source,
                questions,
                "--db",
                index,
                "--task-receipt",
                receipt,
                "--execution-route",
                "coordinator-warm",
            )
            self.assertEqual(warm.returncode, 0, warm.stderr)
            payload = json.loads(warm.stdout)
            self.assertEqual(payload["retrieval"], "finding-receipt")
            self.assertEqual(payload["finding_hits"], 1)
            self.assertEqual(payload["search_count"], 0)
            self.assertEqual(payload["characters"], 0)
            self.assertEqual(payload["passages"], [])
            self.assertEqual(payload["sources"], [])
            self.assertEqual(payload["optimization"]["reopen"], "skipped")
            self.assertEqual(payload["findings"][0]["facet_id"], "mass")
            self.assertEqual(
                payload["findings"][0]["locators"][0]["source"], "source.md"
            )
            self.assertNotIn("text", payload["findings"][0]["locators"][0])

    def test_changed_question_set_reuses_matching_facet_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text(
                "Alpha rule and alpha exception. Gamma rule and gamma exception.",
                encoding="utf-8",
            )
            first_questions = root / "first.json"
            first_questions.write_text(
                json.dumps(
                    {
                        "questions": [
                            {
                                "id": "alpha",
                                "question": "Alpha?",
                                "queries": [
                                    {"query": "alpha rule", "role": "support"},
                                    {"query": "alpha exception", "role": "check"},
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            index = root / "index.sqlite"
            receipt = root / "task-receipt.json"
            cold = run_corpus(
                "evidence-pack",
                source,
                first_questions,
                "--db",
                index,
                "--task-receipt",
                receipt,
                "--execution-route",
                "coordinator-direct",
            )
            self.assertEqual(cold.returncode, 0, cold.stderr)
            first_payload = json.loads(cold.stdout)
            findings = root / "findings.json"
            findings.write_text(
                json.dumps(
                    {
                        "findings": [
                            {
                                "facet_id": "alpha",
                                "claims": [
                                    {
                                        "text": "Alpha is covered.",
                                        "status": "confirmed", "basis": "Checked source", "scope": "Alpha",
                                        "passage_ids": first_payload["facets"][0]["passage_ids"],
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            saved = run_corpus(
                "findings-save",
                receipt,
                findings,
                "--execution-route",
                "coordinator-direct",
            )
            self.assertEqual(saved.returncode, 0, saved.stderr)

            second_questions = root / "second.json"
            second_questions.write_text(
                json.dumps(
                    {
                        "questions": [
                            {
                                "id": "alpha",
                                "question": "Alpha?",
                                "queries": [
                                    {"query": "alpha rule", "role": "support"},
                                    {"query": "alpha exception", "role": "check"},
                                ],
                            },
                            {
                                "id": "gamma",
                                "question": "Gamma?",
                                "queries": [
                                    {"query": "gamma rule", "role": "support"},
                                    {"query": "gamma exception", "role": "check"},
                                ],
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            delta = run_corpus(
                "evidence-pack",
                source,
                second_questions,
                "--db",
                index,
                "--task-receipt",
                receipt,
                "--execution-route",
                "auto",
                "--pack-output",
                root / "pack.json",
            )
            self.assertEqual(delta.returncode, 0, delta.stderr)
            payload = json.loads(delta.stdout)
            self.assertEqual(payload["retrieval"], "delta")
            self.assertEqual(payload["finding_hits"], 1)
            self.assertEqual(payload["searched_facets"], ["gamma"])
            self.assertEqual(payload["search_count"], 2)
            self.assertEqual(payload["routing"]["recommendation"], "coordinator-direct")
            self.assertEqual([item["facet_id"] for item in payload["findings"]], ["alpha"])
            self.assertTrue(payload["passages"])
            saved_receipt = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(
                [facet["id"] for facet in saved_receipt["facets"]],
                ["alpha", "gamma"],
            )

    def test_auto_route_omits_passages_when_measured_worker_is_cheaper(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text(
                "Rule evidence " + "x" * 3000 + " exception evidence.",
                encoding="utf-8",
            )
            questions = root / "questions.json"
            questions.write_text(
                json.dumps(
                    {
                        "questions": [
                            {
                                "id": "rule",
                                "question": "Rule?",
                                "queries": [
                                    {"query": "rule evidence", "role": "support"},
                                    {"query": "exception evidence", "role": "check"},
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            profile = root / "routing.json"
            profile.write_text(
                json.dumps(
                    {
                        "worker_input_cost_ratio": 0.01,
                        "worker_output_cost_ratio": 0.01,
                        "worker_startup_tokens": 800,
                        "expected_parent_turns": 1,
                        "finding_tokens_per_facet": 1,
                        "minimum_savings_fraction": 0,
                    }
                ),
                encoding="utf-8",
            )
            pack = root / "pack.json"
            result = run_corpus(
                "evidence-pack",
                source,
                questions,
                "--db",
                root / "index.sqlite",
                "--task-receipt",
                root / "task-receipt.json",
                "--execution-route",
                "auto",
                "--pack-output",
                pack,
                "--routing-profile",
                profile,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = json.loads(result.stdout)
            self.assertEqual(
                manifest["routing"]["recommendation"], "low-overhead-worker"
            )
            self.assertTrue(manifest["passages_omitted"])
            self.assertNotIn("passages", manifest)
            self.assertTrue(pack.is_file())
            stored_pack = json.loads(pack.read_text(encoding="utf-8"))
            self.assertTrue(stored_pack["passages"])
            self.assertEqual(stored_pack["facets"][0]["question"], "Rule?")

    def test_enumeration_selects_more_than_lookup_passage_cap(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text(
                "\n\n".join(
                    f"# Variant {index}\n\nVariant signer {index}."
                    for index in range(1, 7)
                ),
                encoding="utf-8",
            )
            questions = root / "questions.json"
            questions.write_text(
                json.dumps(
                    {
                        "questions": [
                            {
                                "id": "variants",
                                "question": "List every variant signer.",
                                "kind": "enumeration",
                                "group_by": "section",
                                "max_items": 6,
                                "queries": [
                                    {"query": "variant signer", "role": "support"},
                                    {"query": "variant signer", "role": "check"},
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            result = run_corpus(
                "evidence-pack",
                source,
                questions,
                "--db",
                root / "index.sqlite",
                "--task-receipt",
                root / "task-receipt.json",
                "--execution-route",
                "auto",
                "--pack-output",
                root / "pack.json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(len(payload["facets"][0]["passage_ids"]), 6)
            self.assertEqual(
                {passage["section"] for passage in payload["passages"]},
                {f"Variant {index}" for index in range(1, 7)},
            )

    def test_schema_facet_returns_exact_schema_locators_in_same_pack(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "schema.md"
            source.write_text(
                "# `cargo.xsd`\n\n"
                "```xsd\n"
                '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">\n'
                '  <xs:element name="CargoMass" type="xs:decimal">\n'
                "    <xs:annotation><xs:documentation>Gross mass in kilograms"
                "</xs:documentation></xs:annotation>\n"
                "  </xs:element>\n"
                "</xs:schema>\n"
                "```\n",
                encoding="utf-8",
            )
            questions = root / "questions.json"
            questions.write_text(
                json.dumps(
                    {
                        "questions": [
                            {
                                "id": "mass",
                                "question": "What is CargoMass?",
                                "kind": "schema",
                                "verification": "exact",
                                "queries": [
                                    {
                                        "query": "CargoMass",
                                        "mode": "literal",
                                        "role": "support",
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            receipt = root / "task-receipt.json"
            result = run_corpus(
                "evidence-pack",
                source,
                questions,
                "--db",
                root / "index.sqlite",
                "--task-receipt",
                receipt,
                "--execution-route",
                "auto",
                "--pack-output",
                root / "pack.json",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertGreaterEqual(payload["schema_query_count"], 1)
            fact = next(
                item for item in payload["schema_facts"] if item["name"] == "CargoMass"
            )
            self.assertEqual(fact["markdown_line"], 5)
            self.assertEqual(fact["roles"], ["support"])
            self.assertEqual(len(fact["block_hash"]), 64)
            self.assertLessEqual(payload["characters"], 20_000)
            saved = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(
                saved["facets"][0]["schema_locators"][0]["markdown_line"], 5
            )
            self.assertEqual(
                saved["facets"][0]["schema_locators"][0]["block_hash"],
                fact["block_hash"],
            )
            findings = root / "findings.json"
            findings.write_text(
                json.dumps(
                    {
                        "findings": [
                            {
                                "facet_id": "mass",
                                "claims": [
                                    {
                                        "text": "CargoMass is a decimal schema element.",
                                        "status": "confirmed", "basis": "Read schema element", "scope": "CargoMass element",
                                        "evidence_ids": [fact["evidence_id"]],
                                    }
                                ],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            saved_findings = run_corpus("findings-save", receipt, findings)
            self.assertEqual(saved_findings.returncode, 0, saved_findings.stderr)

    def test_parent_context_alone_does_not_imply_worker_savings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text("Rule evidence.", encoding="utf-8")
            questions = root / "questions.json"
            questions.write_text(json.dumps(["Rule evidence?"]), encoding="utf-8")
            pack = root / "pack.json"
            result = run_corpus(
                "evidence-pack",
                source,
                questions,
                "--db",
                root / "index.sqlite",
                "--task-receipt",
                root / "task-receipt.json",
                "--execution-route",
                "auto",
                "--pack-output",
                pack,
                "--parent-context-tokens",
                "165000",
                "--expected-direct-turns",
                "2",
                "--expected-delegated-parent-turns",
                "1",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(
                payload["routing"]["recommendation"], "coordinator-direct"
            )
            self.assertEqual(payload["routing"]["parent_context_tokens"], 165000)
            self.assertEqual(payload["routing"]["reason"], "incomplete-worker-costs")
            self.assertIsNone(payload["routing"]["estimated_delegated_cost_units"])
            self.assertFalse(pack.exists())
