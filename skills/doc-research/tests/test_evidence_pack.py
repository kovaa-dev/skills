from __future__ import annotations

from test_support import *


class EvidencePackCliTest(CorpusCliTestCase):
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
            self.assertNotIn("Which exchange files", json.dumps(saved))
            self.assertNotIn("Who signs", json.dumps(saved))
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
            self.assertEqual(redundant_worker.returncode, 2)
            self.assertIn(
                "do not launch a cold worker", redundant_worker.stderr
            )
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

    def test_explicit_queries_require_support_and_check_roles(self) -> None:
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
            self.assertEqual(result.returncode, 2)
            self.assertIn("must include support and check roles", result.stderr)

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
                                "status": "verified",
                                "claims": [
                                    {"text": "Invalid locator.", "passage_ids": [999]}
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
                                "status": "verified",
                                "claims": [
                                    {
                                        "text": "Cargo mass is required in kilograms.",
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
                                "status": "verified",
                                "claims": [
                                    {
                                        "text": "Alpha is covered.",
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
                                "question": "Tell me about alpha using new wording.",
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
                        "worker_startup_tokens": 0,
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
