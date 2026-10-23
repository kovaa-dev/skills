from __future__ import annotations

from test_support import *


class PackContinuityCliTest(CorpusCliTestCase):
    def test_verified_schema_finding_survives_repeated_warm_reads(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.xsd"
            source.write_text(
                '<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                '<xs:element name="CargoMass" type="xs:decimal"/>'
                '</xs:schema>',
                encoding="utf-8",
            )
            questions = root / "questions.json"
            questions.write_text(json.dumps([{
                "id": "mass", "question": "CargoMass type?", "kind": "schema",
                "queries": ["CargoMass"],
            }]), encoding="utf-8")
            receipt = root / "receipt.json"
            command = (
                "evidence-pack", source, questions, "--db", root / "index.sqlite",
                "--task-receipt", receipt,
            )
            cold = run_corpus(*command)
            self.assertEqual(cold.returncode, 0, cold.stderr)
            fact = next(item for item in json.loads(cold.stdout)["schema_facts"]
                        if item["name"] == "CargoMass")
            findings = root / "findings.json"
            findings.write_text(json.dumps([{
                "facet_id": "mass", "status": "verified",
                "claims": [{"text": "CargoMass has decimal type.",
                            "evidence_ids": [fact["evidence_id"]]}],
            }]), encoding="utf-8")
            saved = run_corpus("findings-save", receipt, findings)
            self.assertEqual(saved.returncode, 0, saved.stderr)

            for budget_args in ((), ("--max-passage-chars", "500", "--max-total-chars", "2000",
                                     "--limit-per-query", "1", "--max-passages", "1"), ()):
                warm = run_corpus(*command, *budget_args)
                self.assertEqual(warm.returncode, 0, warm.stderr)
                payload = json.loads(warm.stdout)
                self.assertEqual(payload["finding_hits"], 1)
                self.assertEqual(payload["search_count"], 0)
                self.assertEqual(payload["passages"], [])
                self.assertEqual(payload["findings"][0]["schema_locators"][0]["evidence_id"],
                                 fact["evidence_id"])

            saved_receipt = json.loads(receipt.read_text(encoding="utf-8"))
            saved_receipt["conflicts"] = [{"description": "A separate policy contradicts this type."}]
            saved_receipt["gaps"] = [{"facet_id": "mass", "reason": "Policy precedence remains unknown."}]
            receipt.write_text(json.dumps(saved_receipt), encoding="utf-8")
            blocked = run_corpus(*command, "--execution-route", "auto")
            self.assertEqual(blocked.returncode, 0, blocked.stderr)
            payload = json.loads(blocked.stdout)
            self.assertEqual(payload["conflicts"], saved_receipt["conflicts"])
            self.assertEqual(payload["gaps"], saved_receipt["gaps"])
            self.assertFalse(payload["requested_findings_current"])
            self.assertEqual(payload["next_mode"], "retrieval")
            self.assertEqual(payload["next_action"]["kind"], "review-saved-findings-and-gaps")

    def test_uncertain_findings_survive_repeat_subset_and_new_query(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.md"
            source.write_text(
                '# Rules\n\nCargoMass policy needs confirmation.\n\n'
                '```xsd\n<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">'
                '<xs:element name="CargoMass" type="xs:decimal"/>'
                '</xs:schema>\n```\n',
                encoding="utf-8",
            )
            questions = root / "questions.json"
            initial_questions = [
                {"id": "mass", "question": "CargoMass type?", "kind": "schema",
                 "queries": ["CargoMass"]},
                {"id": "policy", "question": "CargoMass policy?", "queries": ["policy"]},
            ]
            questions.write_text(json.dumps(initial_questions), encoding="utf-8")
            receipt = root / "receipt.json"
            command = ("evidence-pack", source, questions, "--db", root / "index.sqlite",
                       "--task-receipt", receipt, "--execution-route", "auto")
            cold = run_corpus(*command)
            self.assertEqual(cold.returncode, 0, cold.stderr)
            fact = next(item for item in json.loads(cold.stdout)["schema_facts"]
                        if item["name"] == "CargoMass")
            findings = root / "findings.json"
            findings.write_text(json.dumps([
                {"facet_id": "mass", "status": "conflicted", "reason": "Policy contradicts XSD.",
                 "claims": [{"text": "XSD declares decimal.", "evidence_ids": [fact["evidence_id"]],
                             "scope": "Type declaration only; policy applicability is unknown."}]},
                {"facet_id": "policy", "status": "unresolved", "claims": [],
                 "reason": "No authoritative policy version identified."},
            ]), encoding="utf-8")
            saved = run_corpus("findings-save", receipt, findings)
            self.assertEqual(saved.returncode, 0, saved.stderr)

            for selected in (initial_questions, initial_questions[:1]):
                questions.write_text(json.dumps(selected), encoding="utf-8")
                warm = run_corpus(*command)
                self.assertEqual(warm.returncode, 0, warm.stderr)
                payload = json.loads(warm.stdout)
                self.assertEqual(payload["search_count"], 0)
                self.assertEqual(payload["schema_query_count"], 0)
                self.assertEqual(payload["passages"], [])
                self.assertEqual(payload["finding_hits"], 0)
                self.assertFalse(payload["requested_findings_current"])
                self.assertEqual(payload["next_mode"], "retrieval")
                self.assertEqual(payload["findings"][0]["status"], "conflicted")
                self.assertEqual(payload["findings"][0]["reason"], "Policy contradicts XSD.")
                self.assertEqual(payload["findings"][0]["claims"][0]["scope"],
                                 "Type declaration only; policy applicability is unknown.")
                self.assertEqual(payload["findings"][0]["schema_locators"][0]["evidence_id"],
                                 fact["evidence_id"])
                self.assertTrue(any(gap["facet_id"] == "policy" for gap in payload["gaps"]))
                if len(selected) == 2:
                    self.assertEqual(payload["findings"][1]["reason"],
                                     "No authoritative policy version identified.")

            refined = {**initial_questions[0], "queries": ["CargoMass", "policy"]}
            questions.write_text(json.dumps([refined]), encoding="utf-8")
            delta = run_corpus(*command)
            self.assertEqual(delta.returncode, 0, delta.stderr)
            payload = json.loads(delta.stdout)
            self.assertGreater(payload["search_count"], 0)
            self.assertEqual(payload["searched_facets"], ["mass"])
            self.assertEqual(payload["facets"][0]["previous_finding"]["finding"]["reason"],
                             "Policy contradicts XSD.")
            self.assertEqual(payload["findings"], [])

            questions.write_text(json.dumps(initial_questions[1:]), encoding="utf-8")
            deeper = run_corpus(*command, "--max-passage-chars", 5000)
            self.assertEqual(deeper.returncode, 0, deeper.stderr)
            payload = json.loads(deeper.stdout)
            self.assertEqual(payload["search_count"], 0)
            self.assertTrue(payload["passages"])
            self.assertEqual(payload["findings"], [])
            self.assertEqual(payload["facets"][0]["previous_finding"]["finding"]["reason"],
                             "No authoritative policy version identified.")

    def test_auto_route_requires_worker_startup_measurement(self) -> None:
        from doc_research.evidence_pack import _route_evidence

        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory) / "routing.json"
            profile.write_text(json.dumps({
                "worker_input_cost_ratio": 0.01, "worker_output_cost_ratio": 0.01,
            }), encoding="utf-8")
            result = _route_evidence(argparse.Namespace(
                routing_profile=profile, parent_context_tokens=165000,
                expected_direct_turns=2, expected_delegated_parent_turns=1,
            ), 10000, 1)
            self.assertEqual(result["recommendation"], "coordinator-direct")
            self.assertEqual(result["missing_cost_inputs"], ["worker_startup_tokens"])
            self.assertIsNone(result["estimated_delegated_cost_units"])
