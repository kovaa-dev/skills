from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "cost_audit.py"
SPEC = importlib.util.spec_from_file_location("cost_audit", SCRIPT)
assert SPEC and SPEC.loader
COST_AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = COST_AUDIT
SPEC.loader.exec_module(COST_AUDIT)


def write_jsonl(path: Path, events: list[dict]) -> None:
    path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")


class CostAuditTests(unittest.TestCase):
    def test_claude_usage_is_deduplicated_and_payloads_are_hidden(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "claude-session.jsonl"
            assistant = {
                "type": "assistant",
                "timestamp": "2026-10-20T10:00:00Z",
                "message": {
                    "id": "message-1",
                    "role": "assistant",
                    "usage": {
                        "input_tokens": 100,
                        "cache_read_input_tokens": 900,
                        "cache_creation_input_tokens": 50,
                        "output_tokens": 20,
                    },
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "call-1",
                            "name": "Bash",
                            "input": {"command": "cd secret-project"},
                        }
                    ],
                },
            }
            write_jsonl(
                path,
                [
                    {"type": "user", "uuid": "u1", "message": {"role": "user", "content": "private"}},
                    assistant,
                    assistant,
                    {
                        "type": "user",
                        "message": {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": "call-1",
                                    "is_error": True,
                                    "content": "failure text",
                                }
                            ],
                        },
                    },
                ],
            )
            metrics = COST_AUDIT.parse_session(path, "claude", include_locator=False)
            public = metrics.public()
            self.assertEqual(metrics.model_calls, 1)
            self.assertEqual(metrics.cache_read_tokens, 900)
            self.assertEqual(metrics.tool_calls, 1)
            self.assertEqual(metrics.tool_errors, 1)
            self.assertEqual(metrics.standalone_cd_calls, 1)
            self.assertNotIn("locator", public)
            self.assertNotIn("private", json.dumps(public))
            self.assertNotIn("secret-project", json.dumps(public))

    def test_codex_cumulative_usage_uses_maximum_not_sum(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "codex-session.jsonl"
            write_jsonl(
                path,
                [
                    {
                        "type": "response_item",
                        "payload": {"type": "message", "id": "u1", "role": "user", "content": "hidden"},
                    },
                    {
                        "type": "event_msg",
                        "payload": {
                            "info": {
                                "total_token_usage": {
                                    "input_tokens": 100,
                                    "cached_input_tokens": 80,
                                    "output_tokens": 20,
                                    "total_tokens": 120,
                                },
                                "last_token_usage": {"input_tokens": 100},
                            }
                        },
                    },
                    {
                        "type": "event_msg",
                        "payload": {
                            "info": {
                                "total_token_usage": {
                                    "input_tokens": 250,
                                    "cached_input_tokens": 200,
                                    "output_tokens": 50,
                                    "total_tokens": 300,
                                },
                                "last_token_usage": {"input_tokens": 150},
                            }
                        },
                    },
                ],
            )
            metrics = COST_AUDIT.parse_session(path, "codex", include_locator=False)
            self.assertEqual(metrics.reported_total_tokens, 300)
            self.assertEqual(metrics.input_tokens, 250)
            self.assertEqual(metrics.cache_read_tokens, 200)
            self.assertEqual(metrics.peak_input_tokens, 150)
            self.assertEqual(metrics.user_turns, 1)

    def test_codex_window_subtracts_pre_window_cumulative_usage(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "codex-window.jsonl"
            write_jsonl(
                path,
                [
                    {
                        "type": "session_meta",
                        "timestamp": "2026-10-20T09:00:00Z",
                        "payload": {"cwd": directory},
                    },
                    {
                        "type": "event_msg",
                        "timestamp": "2026-10-20T10:00:00Z",
                        "payload": {
                            "info": {
                                "total_token_usage": {
                                    "input_tokens": 100,
                                    "cached_input_tokens": 80,
                                    "output_tokens": 20,
                                    "total_tokens": 120,
                                }
                            }
                        },
                    },
                    {
                        "type": "event_msg",
                        "timestamp": "2026-10-20T11:00:00Z",
                        "payload": {
                            "info": {
                                "total_token_usage": {
                                    "input_tokens": 350,
                                    "cached_input_tokens": 280,
                                    "output_tokens": 70,
                                    "total_tokens": 420,
                                },
                                "last_token_usage": {"input_tokens": 250},
                            }
                        },
                    },
                ],
            )
            cutoff = datetime(2026, 10, 20, 10, 30, tzinfo=timezone.utc)
            metrics = COST_AUDIT.parse_session(
                path, "codex", include_locator=False, cutoff=cutoff
            )
            self.assertEqual(metrics.reported_total_tokens, 300)
            self.assertEqual(metrics.input_tokens, 250)
            self.assertEqual(metrics.cache_read_tokens, 200)
            self.assertEqual(metrics.output_tokens, 50)
            self.assertEqual(metrics.usage_window_coverage, "complete")
            self.assertEqual(metrics.window_first_event_at, "2026-10-20T11:00:00Z")
            self.assertTrue(metrics.window_starts_after_session_start)

    def test_selection_covers_heavy_sessions_and_anomalies(self) -> None:
        def metric(key: str, tokens: int, errors: int = 0) -> object:
            value = COST_AUDIT.Metrics("codex", key, 1, "2026-10-20T00:00:00Z")
            value.reported_total_tokens = tokens
            value.observed_tool_errors = errors
            value.tool_calls = max(errors, 1)
            return value

        items = [metric("heavy", 700), metric("middle", 200), metric("small", 100, errors=5)]
        selected, coverage = COST_AUDIT.select_sessions(items, 0.70, 0, 3)
        keys = {item.session_key for item, _ in selected}
        self.assertIn("heavy", keys)
        self.assertIn("small", keys)
        self.assertGreaterEqual(coverage["token_coverage"], 0.70)
        self.assertIsNone(coverage["proxy_byte_coverage"])

    def test_selection_never_combines_tokens_and_bytes(self) -> None:
        measured = COST_AUDIT.Metrics("codex", "measured", 10_000_000, "now")
        measured.reported_total_tokens = 100
        proxy = COST_AUDIT.Metrics("unknown", "proxy", 500, "now")
        selected, coverage = COST_AUDIT.select_sessions([measured, proxy], 0.70, 0, 2)
        self.assertEqual({item.session_key for item, _ in selected}, {"measured", "proxy"})
        self.assertEqual(coverage["token_coverage"], 1.0)
        self.assertEqual(coverage["proxy_byte_coverage"], 1.0)

    def test_document_inventory_is_bounded_and_does_not_emit_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "AGENTS.md").write_text("secret instruction", encoding="utf-8")
            (root / "notes.md").write_text("ordinary note", encoding="utf-8")
            excluded = root / "node_modules"
            excluded.mkdir()
            (excluded / "SKILL.md").write_text("ignored secret", encoding="utf-8")
            nested = root / "nested"
            nested.mkdir()
            (nested / "AGENTS.md").write_text("secret instruction", encoding="utf-8")
            items, unreadable = COST_AUDIT.inventory_docs(root, nested)
            self.assertEqual(
                [item["path"] for item in items], ["AGENTS.md", "nested/AGENTS.md"]
            )
            rendered = json.dumps(items)
            self.assertNotIn("secret instruction", rendered)
            self.assertNotIn("ignored secret", rendered)
            self.assertEqual(items[0]["load_status"], "unknown")
            self.assertTrue(all(item["scope_relation"] == "ancestor_of_cwd" for item in items))
            self.assertEqual(unreadable, 0)

    def test_sessions_filter_to_requested_project(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wanted = root / "wanted"
            other = root / "other"
            logs = root / "logs"
            wanted.mkdir()
            other.mkdir()
            logs.mkdir()
            for name, cwd, tokens in (("wanted", wanted, 100), ("other", other, 900)):
                write_jsonl(
                    logs / f"{name}.jsonl",
                    [
                        {
                            "type": "session_meta",
                            "timestamp": "2026-10-20T10:00:00Z",
                            "payload": {"cwd": str(cwd)},
                        },
                        {
                            "type": "event_msg",
                            "timestamp": "2026-10-20T10:01:00Z",
                            "payload": {
                                "info": {
                                    "total_token_usage": {
                                        "input_tokens": tokens,
                                        "output_tokens": 0,
                                        "total_tokens": tokens,
                                    }
                                }
                            },
                        },
                    ],
                )
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "sessions",
                    "--input",
                    str(logs),
                    "--project-root",
                    str(wanted),
                    "--since",
                    "all",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            report = json.loads(result.stdout)
            self.assertEqual(report["totals"]["sessions"], 1)
            self.assertEqual(report["totals"]["reported_total_tokens"], 100)
            self.assertEqual(report["coverage"]["excluded_other_projects"], 1)

    def test_inspect_is_bounded_and_never_emits_content_or_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inspect.jsonl"
            write_jsonl(
                path,
                [
                    {
                        "type": "session_meta",
                        "timestamp": "2026-10-20T10:00:00Z",
                        "payload": {"cwd": directory},
                    },
                    {
                        "type": "response_item",
                        "timestamp": "2026-10-20T10:01:00Z",
                        "payload": {
                            "type": "message",
                            "id": "u1",
                            "role": "user",
                            "content": "private prompt",
                        },
                    },
                    {
                        "type": "response_item",
                        "timestamp": "2026-10-20T10:02:00Z",
                        "payload": {
                            "type": "custom_tool_call",
                            "id": "c1",
                            "call_id": "c1",
                            "name": "exec",
                            "input": "secret arguments",
                        },
                    },
                    {
                        "type": "response_item",
                        "timestamp": "2026-10-20T10:03:00Z",
                        "payload": {
                            "type": "custom_tool_call_output",
                            "id": "r1",
                            "call_id": "c1",
                            "output": "secret output",
                        },
                    },
                ],
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "inspect", str(path), "--max-buckets", "1"],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertNotIn("private prompt", result.stdout)
            self.assertNotIn("secret arguments", result.stdout)
            self.assertNotIn("secret output", result.stdout)
            report = json.loads(result.stdout)
            self.assertEqual(report["session"]["tool_errors"], None)
            self.assertEqual(report["session"]["opaque_wrapper_calls"], 1)
            self.assertLessEqual(report["activity"]["selected_activity_buckets"], 1)

    def test_cli_rejects_invalid_sampling_limits(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "sessions",
                "--min-sessions",
                "5",
                "--max-sessions",
                "2",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot exceed", result.stderr)


if __name__ == "__main__":
    unittest.main()
