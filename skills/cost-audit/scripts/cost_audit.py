#!/usr/bin/env python3
"""Read-only, privacy-bounded cost inventory for local agent sessions and instructions."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

LARGE_OUTPUT_CHARS = 20_000
EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "build",
    "dist",
    "node_modules",
    "vendor",
    "__pycache__",
}
DOC_NAMES = {"AGENTS.md", "CLAUDE.md", "SKILL.md"}
CONFIG_NAMES = {
    ".mcp.json",
    "mcp.json",
    "settings.json",
    "config.json",
    "config.toml",
    "codex.toml",
}
USAGE_KEYS = (
    "input_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "output_tokens",
    "reasoning_tokens",
    "reported_total_tokens",
)


@dataclass
class Metrics:
    provider: str
    session_key: str
    bytes: int
    modified_at: str
    project_key: str | None = None
    session_first_event_at: str | None = None
    session_last_event_at: str | None = None
    window_first_event_at: str | None = None
    window_last_event_at: str | None = None
    window_starts_after_session_start: bool = False
    events_in_window: int = 0
    events_without_timestamp: int = 0
    user_turns: int = 0
    model_calls: int = 0
    tool_calls: int = 0
    tool_errors: int | None = None
    observed_tool_errors: int = 0
    tool_error_observability: str = "unavailable"
    opaque_wrapper_calls: int = 0
    tool_visibility: str = "unknown"
    exact_repeated_calls: int = 0
    standalone_cd_calls: int = 0
    compactions: int = 0
    large_tool_outputs: int = 0
    tool_output_chars: int = 0
    input_tokens: int | None = None
    cache_read_tokens: int | None = None
    cache_write_tokens: int | None = None
    output_tokens: int | None = None
    reasoning_tokens: int | None = None
    reported_total_tokens: int | None = None
    first_input_tokens: int | None = None
    median_input_tokens: int | None = None
    p95_input_tokens: int | None = None
    peak_input_tokens: int | None = None
    usage_window_coverage: str = "unavailable"
    usage_semantics: str = "provider_native"
    malformed_events: int = 0
    tool_names: Counter[str] = field(default_factory=Counter, repr=False)
    locator: str | None = None
    project_path: str | None = field(default=None, repr=False)
    input_samples: list[int] = field(default_factory=list, repr=False)

    @property
    def workload_tokens(self) -> int | None:
        if self.reported_total_tokens is not None:
            return self.reported_total_tokens
        values = (
            self.input_tokens,
            self.cache_read_tokens,
            self.cache_write_tokens,
            self.output_tokens,
            self.reasoning_tokens,
        )
        present = [value for value in values if value is not None]
        return sum(present) if present else None

    def public(self, include_locator: bool = False) -> dict[str, Any]:
        result = asdict(self)
        result["tool_names"] = dict(sorted(self.tool_names.items()))
        result["workload_tokens"] = self.workload_tokens
        result.pop("project_path", None)
        result.pop("input_samples", None)
        if not include_locator:
            result.pop("locator", None)
        return result


@dataclass(frozen=True)
class SessionProbe:
    path: Path
    provider: str
    project_path: str | None
    project_key: str


def safe_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()[:16]


def iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def timestamp(value: Any) -> datetime | None:
    if isinstance(value, (int, float)):
        seconds = float(value)
        if seconds > 10_000_000_000:
            seconds /= 1000
        try:
            return datetime.fromtimestamp(seconds, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def cutoff_for(value: str) -> datetime | None:
    if value.lower() == "all":
        return None
    match = re.fullmatch(r"(\d+)([dh])", value.lower())
    if match:
        count = int(match.group(1))
        delta = timedelta(days=count) if match.group(2) == "d" else timedelta(hours=count)
        return datetime.now(timezone.utc) - delta
    parsed = timestamp(value)
    if parsed is None:
        raise argparse.ArgumentTypeError("--since must be 'all', Nd, Nh, or an ISO timestamp")
    return parsed


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                yield {"__malformed__": True}
                continue
            if isinstance(value, dict):
                yield value


def event_time(event: dict[str, Any]) -> datetime | None:
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    for value in (
        event.get("timestamp"),
        event.get("created_at"),
        event.get("time"),
        payload.get("timestamp"),
        payload.get("created_at"),
    ):
        parsed = timestamp(value)
        if parsed is not None:
            return parsed
    return None


def provider_for(path: Path, requested: str, sample: list[dict[str, Any]]) -> str:
    if requested != "auto":
        return requested
    for event in sample:
        payload = event.get("payload")
        if event.get("type") in {"session_meta", "event_msg", "response_item"} and isinstance(
            payload, dict
        ):
            return "codex"
        message = event.get("message")
        if isinstance(message, dict) and ("usage" in message or "content" in message):
            return "claude"
    lower_parts = {part.lower() for part in path.parts}
    if ".claude" in lower_parts:
        return "claude"
    if ".codex" in lower_parts:
        return "codex"
    return "unknown"


def project_path_from_event(event: dict[str, Any]) -> str | None:
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    value = payload.get("cwd") or event.get("cwd")
    if isinstance(value, str) and value:
        return str(Path(value).expanduser().resolve())
    return None


def probe_session(path: Path, requested_provider: str) -> SessionProbe:
    sample: list[dict[str, Any]] = []
    project_path: str | None = None
    for event in iter_jsonl(path):
        if len(sample) < 50:
            sample.append(event)
        project_path = project_path or project_path_from_event(event)
        if len(sample) >= 50 and project_path is not None:
            break
    provider = provider_for(path, requested_provider, sample)
    identity = project_path or str(path.parent.resolve())
    return SessionProbe(path, provider, project_path, safe_key(identity))


def belongs_to_project(project_path: str | None, project_root: Path) -> bool:
    if project_path is None:
        return False
    candidate = Path(project_path)
    return candidate == project_root or project_root in candidate.parents


def in_window(value: datetime | None, cutoff: datetime | None) -> bool:
    return cutoff is None or (value is not None and value >= cutoff)


def percentile(values: list[int], fraction: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int((len(ordered) - 1) * fraction + 0.999999)))
    return ordered[index]


def finalize_metrics(metrics: Metrics) -> None:
    if metrics.input_samples:
        metrics.first_input_tokens = metrics.input_samples[0]
        metrics.median_input_tokens = percentile(metrics.input_samples, 0.50)
        metrics.p95_input_tokens = percentile(metrics.input_samples, 0.95)
        metrics.peak_input_tokens = max(metrics.input_samples)
    if metrics.opaque_wrapper_calls:
        metrics.tool_visibility = "wrapper_only" if metrics.opaque_wrapper_calls == metrics.tool_calls else "mixed"
    elif metrics.tool_calls:
        metrics.tool_visibility = "direct"
    else:
        metrics.tool_visibility = "none"


def int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and value >= 0:
        return int(value)
    return None


def usage_value(mapping: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = int_or_none(mapping.get(key))
        if value is not None:
            return value
    return None


def content_chars(value: Any) -> int:
    if isinstance(value, str):
        return len(value)
    if isinstance(value, list):
        return sum(content_chars(item) for item in value)
    if isinstance(value, dict):
        for key in ("content", "output", "text"):
            if key in value:
                return content_chars(value[key])
    return 0


def normalized_call_hash(name: str, arguments: Any) -> str:
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            arguments = arguments.strip()
    try:
        normalized = json.dumps(arguments, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError):
        normalized = repr(arguments)
    return safe_key(f"{name}\0{normalized}")


def command_from(arguments: Any) -> str | None:
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError:
            return arguments
        arguments = parsed
    if isinstance(arguments, dict):
        for key in ("cmd", "command", "script"):
            value = arguments.get(key)
            if isinstance(value, str):
                return value
    return None


def is_standalone_cd(name: str, arguments: Any) -> bool:
    if name.lower() not in {"bash", "shell", "exec_command", "run_command"}:
        return False
    command = command_from(arguments)
    return bool(command and re.fullmatch(r"\s*cd(?:\s+[^;&|\n]+)?\s*", command))


def add_tool_call(
    metrics: Metrics,
    seen: Counter[str],
    call_names: dict[str, str],
    name: Any,
    arguments: Any,
    call_id: Any,
) -> None:
    tool_name = str(name or "unknown")
    if isinstance(call_id, str) and call_id in call_names:
        return
    if isinstance(call_id, str):
        call_names[call_id] = tool_name
    metrics.tool_calls += 1
    metrics.tool_names[tool_name] += 1
    digest = normalized_call_hash(tool_name, arguments)
    if seen[digest]:
        metrics.exact_repeated_calls += 1
    seen[digest] += 1
    if is_standalone_cd(tool_name, arguments):
        metrics.standalone_cd_calls += 1


def add_tool_output(metrics: Metrics, value: Any, is_error: bool = False) -> None:
    chars = content_chars(value)
    metrics.tool_output_chars += chars
    if chars > LARGE_OUTPUT_CHARS:
        metrics.large_tool_outputs += 1
    if is_error:
        metrics.observed_tool_errors += 1
        if metrics.tool_errors is not None:
            metrics.tool_errors += 1


def sum_optional(values: Iterable[int | None]) -> int | None:
    present = [value for value in values if value is not None]
    return sum(present) if present else None


def parse_claude(
    path: Path,
    events: Iterable[dict[str, Any]],
    metrics: Metrics,
    cutoff: datetime | None,
) -> None:
    messages: dict[str, dict[str, int | None]] = {}
    anonymous_usage: list[dict[str, int | None]] = []
    seen_calls: Counter[str] = Counter()
    call_names: dict[str, str] = {}
    seen_results: set[str] = set()
    seen_user_ids: set[str] = set()
    metrics.tool_errors = 0
    metrics.tool_error_observability = "complete"
    metrics.usage_semantics = "component_sum_includes_cache_fields"

    for event in events:
        if event.get("__malformed__"):
            metrics.malformed_events += 1
            continue
        when = event_time(event)
        inside = in_window(when, cutoff)
        update_event_times(metrics, when, inside)
        if cutoff is not None and when is None:
            metrics.events_without_timestamp += 1
        event_type = str(event.get("type", ""))
        subtype = str(event.get("subtype", "")).lower()
        project_path = project_path_from_event(event)
        if metrics.project_path is None and project_path is not None:
            metrics.project_path = project_path
            metrics.project_key = safe_key(project_path)
        if not inside:
            continue
        metrics.events_in_window += 1
        if "compact" in event_type.lower() or "compact" in subtype:
            metrics.compactions += 1

        message = event.get("message")
        if not isinstance(message, dict):
            message = {}
        role = message.get("role") or event_type
        content = message.get("content", event.get("content"))
        if role == "user" or event_type == "user":
            blocks = content if isinstance(content, list) else []
            only_results = bool(blocks) and all(
                isinstance(block, dict) and block.get("type") == "tool_result" for block in blocks
            )
            event_id = str(event.get("uuid") or message.get("id") or "")
            if not only_results and (not event_id or event_id not in seen_user_ids):
                metrics.user_turns += 1
                if event_id:
                    seen_user_ids.add(event_id)
            for block in blocks:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    result_id = block.get("tool_use_id")
                    if isinstance(result_id, str) and result_id in seen_results:
                        continue
                    if isinstance(result_id, str):
                        seen_results.add(result_id)
                    add_tool_output(metrics, block, bool(block.get("is_error")))

        if role == "assistant" or event_type == "assistant":
            usage = message.get("usage")
            message_id = message.get("id") or event.get("uuid")
            if isinstance(usage, dict):
                normalized = {
                    "input_tokens": usage_value(usage, "input_tokens"),
                    "cache_read_tokens": usage_value(
                        usage, "cache_read_input_tokens", "cache_read_tokens"
                    ),
                    "cache_write_tokens": usage_value(
                        usage, "cache_creation_input_tokens", "cache_write_tokens"
                    ),
                    "output_tokens": usage_value(usage, "output_tokens"),
                    "reasoning_tokens": usage_value(usage, "reasoning_tokens"),
                }
                if message_id:
                    previous = messages.get(str(message_id), {})
                    messages[str(message_id)] = {
                        key: max(
                            value for value in (previous.get(key), normalized.get(key)) if value is not None
                        )
                        if previous.get(key) is not None or normalized.get(key) is not None
                        else None
                        for key in normalized
                    }
                else:
                    anonymous_usage.append(normalized)
            blocks = content if isinstance(content, list) else []
            for block in blocks:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    add_tool_call(
                        metrics,
                        seen_calls,
                        call_names,
                        block.get("name"),
                        block.get("input"),
                        block.get("id"),
                    )

    usage_rows = [*messages.values(), *anonymous_usage]
    metrics.model_calls = len(usage_rows)
    for key in (
        "input_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
        "output_tokens",
        "reasoning_tokens",
    ):
        setattr(metrics, key, sum_optional(row.get(key) for row in usage_rows))
    metrics.input_samples = [
        sum(
            value
            for value in (
                row.get("input_tokens"),
                row.get("cache_read_tokens"),
                row.get("cache_write_tokens"),
            )
            if value is not None
        )
        for row in usage_rows
    ]
    missing_results = set(call_names) - seen_results
    calls_without_ids = metrics.tool_calls > len(call_names)
    if missing_results or calls_without_ids:
        metrics.tool_errors = None
        metrics.tool_error_observability = "partial"
    metrics.usage_window_coverage = "complete" if usage_rows else "unavailable"
    finalize_metrics(metrics)


def nested_usage(event: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    payload = event.get("payload")
    if not isinstance(payload, dict):
        return None, None
    info = payload.get("info")
    if not isinstance(info, dict):
        info = payload
    total = info.get("total_token_usage") or info.get("total_usage")
    latest = info.get("last_token_usage") or info.get("last_usage")
    return total if isinstance(total, dict) else None, latest if isinstance(latest, dict) else None


def normalized_codex_usage(value: dict[str, Any]) -> dict[str, int | None]:
    return {
        "input_tokens": usage_value(value, "input_tokens"),
        "cache_read_tokens": usage_value(value, "cached_input_tokens", "cache_read_tokens"),
        "cache_write_tokens": usage_value(value, "cache_write_tokens"),
        "output_tokens": usage_value(value, "output_tokens"),
        "reasoning_tokens": usage_value(value, "reasoning_output_tokens", "reasoning_tokens"),
        "reported_total_tokens": usage_value(value, "total_tokens"),
    }


def merge_max(target: dict[str, int], values: dict[str, int | None]) -> None:
    for key, value in values.items():
        if value is not None:
            target[key] = max(target.get(key, 0), value)


def parse_codex(
    path: Path,
    events: Iterable[dict[str, Any]],
    metrics: Metrics,
    cutoff: datetime | None,
) -> None:
    seen_calls: Counter[str] = Counter()
    call_names: dict[str, str] = {}
    seen_results: set[str] = set()
    cumulative_before: dict[str, int] = {}
    cumulative_in_window: dict[str, int] = {}
    seen_assistant_items: set[str] = set()
    seen_user_items: set[str] = set()
    saw_event_before_window = False
    metrics.usage_semantics = "reported_total_and_input_include_cached_input"

    for event in events:
        if event.get("__malformed__"):
            metrics.malformed_events += 1
            continue
        when = event_time(event)
        inside = in_window(when, cutoff)
        update_event_times(metrics, when, inside)
        if cutoff is not None and when is None:
            metrics.events_without_timestamp += 1
        if cutoff is not None and when is not None and when < cutoff:
            saw_event_before_window = True
        event_type = str(event.get("type", ""))
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        payload_type = str(payload.get("type", ""))
        project_path = project_path_from_event(event)
        if metrics.project_path is None and project_path is not None:
            metrics.project_path = project_path
            metrics.project_key = safe_key(project_path)
        combined = f"{event_type} {payload_type} {payload.get('name', '')}".lower()
        if inside and "compact" in combined:
            metrics.compactions += 1

        total, latest = nested_usage(event)
        if total:
            target = cumulative_in_window if inside else cumulative_before
            merge_max(target, normalized_codex_usage(total))
        if inside and latest:
            latest_input = usage_value(latest, "input_tokens")
            if latest_input is not None:
                metrics.input_samples.append(latest_input)

        if not inside:
            continue
        metrics.events_in_window += 1

        if event_type == "response_item":
            item_id = str(payload.get("id") or payload.get("call_id") or "")
            if payload_type == "message":
                role = payload.get("role")
                if role == "user" and (not item_id or item_id not in seen_user_items):
                    metrics.user_turns += 1
                    if item_id:
                        seen_user_items.add(item_id)
                elif role == "assistant" and (not item_id or item_id not in seen_assistant_items):
                    metrics.model_calls += 1
                    if item_id:
                        seen_assistant_items.add(item_id)
            elif payload_type in {"function_call", "custom_tool_call", "local_shell_call"}:
                if payload_type == "custom_tool_call":
                    metrics.opaque_wrapper_calls += 1
                add_tool_call(
                    metrics,
                    seen_calls,
                    call_names,
                    payload.get("name") or payload_type,
                    payload.get("arguments") or payload.get("input") or payload.get("command"),
                    payload.get("call_id") or payload.get("id"),
                )
            elif payload_type in {
                "function_call_output",
                "custom_tool_call_output",
                "local_shell_call_output",
            }:
                result_id = payload.get("call_id") or payload.get("id")
                if isinstance(result_id, str) and result_id in seen_results:
                    continue
                if isinstance(result_id, str):
                    seen_results.add(result_id)
                value = payload.get("output") or payload.get("content")
                exit_code = int_or_none(payload.get("exit_code"))
                status = str(payload.get("status", "")).lower()
                error = bool(
                    payload.get("is_error")
                    or payload.get("error")
                    or (exit_code is not None and exit_code != 0)
                    or status in {"error", "failed", "failure"}
                )
                add_tool_output(metrics, value, error)

    if cumulative_in_window:
        if cutoff is not None and saw_event_before_window and not cumulative_before:
            metrics.usage_window_coverage = "unavailable"
        else:
            for key in USAGE_KEYS:
                if key not in cumulative_in_window:
                    continue
                baseline = cumulative_before.get(key, 0) if cutoff is not None else 0
                setattr(metrics, key, max(0, cumulative_in_window[key] - baseline))
            metrics.usage_window_coverage = "complete"
    metrics.tool_error_observability = "unavailable" if metrics.tool_calls else "complete"
    metrics.tool_errors = None if metrics.tool_calls else 0
    finalize_metrics(metrics)


def update_event_times(metrics: Metrics, value: datetime | None, inside: bool) -> None:
    if value is None:
        return
    rendered = iso_utc(value)
    if metrics.session_first_event_at is None or rendered < metrics.session_first_event_at:
        metrics.session_first_event_at = rendered
    if metrics.session_last_event_at is None or rendered > metrics.session_last_event_at:
        metrics.session_last_event_at = rendered
    if inside:
        if metrics.window_first_event_at is None or rendered < metrics.window_first_event_at:
            metrics.window_first_event_at = rendered
        if metrics.window_last_event_at is None or rendered > metrics.window_last_event_at:
            metrics.window_last_event_at = rendered


def parse_session(
    path: Path,
    provider: str,
    include_locator: bool,
    cutoff: datetime | None = None,
    probe: SessionProbe | None = None,
) -> Metrics:
    stat = path.stat()
    session_probe = probe or probe_session(path, provider)
    detected = session_probe.provider
    resolved = str(path.resolve())
    metrics = Metrics(
        provider=detected,
        session_key=safe_key(resolved),
        bytes=stat.st_size,
        modified_at=iso_utc(datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)),
        project_key=session_probe.project_key,
        project_path=session_probe.project_path,
        locator=resolved if include_locator else None,
    )
    if detected == "claude":
        parse_claude(path, iter_jsonl(path), metrics, cutoff)
    elif detected == "codex":
        parse_codex(path, iter_jsonl(path), metrics, cutoff)
    else:
        metrics.malformed_events += sum(1 for _ in iter_jsonl(path))
    first = timestamp(metrics.session_first_event_at)
    metrics.window_starts_after_session_start = bool(
        cutoff is not None and first is not None and first < cutoff
    )
    return metrics


def discover_sessions(inputs: list[str], include_archived: bool) -> list[Path]:
    roots: list[Path]
    if inputs:
        roots = [Path(value).expanduser() for value in inputs]
    else:
        home = Path.home()
        roots = [home / ".claude" / "projects", home / ".codex" / "sessions"]
        if include_archived:
            roots.append(home / ".codex" / "archived_sessions")
    paths: set[Path] = set()
    for root in roots:
        if root.is_file() and root.suffix.lower() == ".jsonl":
            paths.add(root)
        elif root.is_dir():
            for path in root.rglob("*.jsonl"):
                if not include_archived and "archived_sessions" in path.parts:
                    continue
                paths.add(path)
    return sorted(paths)


def select_sessions(
    metrics: list[Metrics], coverage_target: float, minimum: int, maximum: int
) -> tuple[list[tuple[Metrics, list[str]]], dict[str, Any]]:
    if not metrics:
        return [], {
            "token_coverage": None,
            "proxy_byte_coverage": None,
            "token_sessions": 0,
            "proxy_sessions": 0,
        }
    token_ranked = sorted(
        (item for item in metrics if item.workload_tokens is not None),
        key=lambda item: item.workload_tokens or 0,
        reverse=True,
    )
    proxy_ranked = sorted(
        (item for item in metrics if item.workload_tokens is None),
        key=lambda item: item.bytes,
        reverse=True,
    )
    selected: dict[str, tuple[Metrics, list[str]]] = {}

    def add(item: Metrics, reason: str) -> None:
        if item.session_key in selected:
            selected[item.session_key][1].append(reason)
        elif len(selected) < maximum:
            selected[item.session_key] = (item, [reason])

    coverage_ranked = token_ranked if token_ranked else proxy_ranked
    coverage_total = sum(
        (item.workload_tokens or 0) if token_ranked else item.bytes for item in coverage_ranked
    )
    running = 0
    for candidate in coverage_ranked:
        add(candidate, "token coverage" if token_ranked else "log-size proxy coverage")
        running += (candidate.workload_tokens or 0) if token_ranked else candidate.bytes
        if coverage_total and running / coverage_total >= coverage_target:
            break
        if len(selected) >= maximum:
            break

    if token_ranked and proxy_ranked and len(selected) < maximum:
        add(proxy_ranked[0], "missing-usage representative")

    ranked_all = token_ranked + proxy_ranked
    anomaly_rankings = (
        (
            "high calls per turn",
            lambda item: item.model_calls / max(item.user_turns, 1),
            lambda item: item.model_calls / max(item.user_turns, 1) > 2,
        ),
        (
            "observed tool errors",
            lambda item: item.observed_tool_errors / max(item.tool_calls, 1),
            lambda item: item.observed_tool_errors > 0,
        ),
        (
            "high exact-repeat rate",
            lambda item: item.exact_repeated_calls / max(item.tool_calls, 1),
            lambda item: item.exact_repeated_calls >= 2,
        ),
        (
            "high compaction rate",
            lambda item: item.compactions / max(item.model_calls, 1),
            lambda item: item.compactions > 0,
        ),
        (
            "high large-output rate",
            lambda item: item.large_tool_outputs / max(item.tool_calls, 1),
            lambda item: item.large_tool_outputs > 0,
        ),
        ("peak input", lambda item: item.peak_input_tokens or 0, lambda item: bool(item.peak_input_tokens)),
    )
    for reason, score, material in anomaly_rankings:
        candidates = [item for item in ranked_all if material(item)]
        if not candidates:
            continue
        candidate = max(candidates, key=score)
        add(candidate, reason)

    if minimum:
        fill_order = sorted(
            ranked_all,
            key=lambda item: (item.workload_tokens is not None, item.workload_tokens or item.bytes),
            reverse=True,
        )
        for candidate in fill_order:
            if len(selected) >= min(minimum, maximum):
                break
            add(candidate, "explicit minimum")

    ordered = sorted(
        selected.values(),
        key=lambda pair: (
            pair[0].workload_tokens is not None,
            pair[0].workload_tokens or pair[0].bytes,
        ),
        reverse=True,
    )
    token_total = sum(item.workload_tokens or 0 for item in token_ranked)
    token_selected = sum(
        item.workload_tokens or 0 for item, _ in ordered if item.workload_tokens is not None
    )
    proxy_total = sum(item.bytes for item in proxy_ranked)
    proxy_selected = sum(
        item.bytes for item, _ in ordered if item.workload_tokens is None
    )
    coverage = {
        "token_coverage": round(token_selected / token_total, 4) if token_total else None,
        "proxy_byte_coverage": round(proxy_selected / proxy_total, 4) if proxy_total else None,
        "token_sessions": len(token_ranked),
        "proxy_sessions": len(proxy_ranked),
    }
    return ordered, coverage


def aggregate(metrics: list[Metrics]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "sessions": len(metrics),
        "bytes": sum(item.bytes for item in metrics),
        "user_turns": sum(item.user_turns for item in metrics),
        "model_calls": sum(item.model_calls for item in metrics),
        "tool_calls": sum(item.tool_calls for item in metrics),
        "tool_errors": (
            sum(item.tool_errors or 0 for item in metrics)
            if all(item.tool_errors is not None for item in metrics)
            else None
        ),
        "tool_errors_coverage_sessions": sum(item.tool_errors is not None for item in metrics),
        "observed_tool_errors": sum(item.observed_tool_errors for item in metrics),
        "opaque_wrapper_calls": sum(item.opaque_wrapper_calls for item in metrics),
        "exact_repeated_calls": sum(item.exact_repeated_calls for item in metrics),
        "standalone_cd_calls": sum(item.standalone_cd_calls for item in metrics),
        "compactions": sum(item.compactions for item in metrics),
        "large_tool_outputs": sum(item.large_tool_outputs for item in metrics),
        "tool_output_chars": sum(item.tool_output_chars for item in metrics),
        "malformed_events": sum(item.malformed_events for item in metrics),
    }
    workload = [item.workload_tokens for item in metrics if item.workload_tokens is not None]
    result["workload_tokens"] = sum(workload) if workload else None
    result["workload_tokens_coverage_sessions"] = len(workload)
    for key in USAGE_KEYS:
        values = [getattr(item, key) for item in metrics if getattr(item, key) is not None]
        result[key] = sum(values) if values else None
        result[f"{key}_coverage_sessions"] = len(values)
    peaks = [item.peak_input_tokens for item in metrics if item.peak_input_tokens is not None]
    result["peak_input_tokens"] = max(peaks) if peaks else None
    tools: Counter[str] = Counter()
    for item in metrics:
        tools.update(item.tool_names)
    result["tool_names"] = dict(sorted(tools.items(), key=lambda pair: (-pair[1], pair[0])))
    result["sessions_by_provider"] = dict(sorted(Counter(item.provider for item in metrics).items()))
    result["sessions_by_project_key"] = dict(
        sorted(Counter(item.project_key or "unknown" for item in metrics).items())
    )
    result["tool_visibility"] = dict(
        sorted(Counter(item.tool_visibility for item in metrics).items())
    )
    by_provider: dict[str, dict[str, Any]] = {}
    for provider in sorted({item.provider for item in metrics}):
        group = [item for item in metrics if item.provider == provider]
        group_workload = [item.workload_tokens for item in group if item.workload_tokens is not None]
        by_provider[provider] = {
            "sessions": len(group),
            "workload_tokens": sum(group_workload) if group_workload else None,
            "workload_tokens_coverage_sessions": len(group_workload),
            "model_calls": sum(item.model_calls for item in group),
            "tool_calls": sum(item.tool_calls for item in group),
            "observed_tool_errors": sum(item.observed_tool_errors for item in group),
            "usage_semantics": sorted({item.usage_semantics for item in group}),
        }
    result["totals_by_provider"] = by_provider
    result["cross_provider_token_comparison"] = (
        "provider_native_semantics; compare provider groups before combining"
        if len(by_provider) > 1
        else "single_provider"
    )
    return result


def sessions_command(args: argparse.Namespace) -> dict[str, Any]:
    cutoff = cutoff_for(args.since)
    discovered = discover_sessions(args.input, args.include_archived)
    mtime_eligible = [
        path
        for path in discovered
        if cutoff is None
        or datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc) >= cutoff
    ]
    explicit_input_scope = bool(args.input) and not args.project_root and not args.all_projects
    project_root = None
    if not args.all_projects and not explicit_input_scope:
        project_root = Path(args.project_root or Path.cwd()).expanduser().resolve()
    probes: list[SessionProbe] = []
    probe_failures = 0
    excluded_projects = 0
    unknown_projects = 0
    unsupported_formats = 0
    for path in mtime_eligible:
        try:
            probe = probe_session(path, args.provider)
        except (OSError, TypeError, UnicodeError, ValueError):
            probe_failures += 1
            continue
        if probe.provider == "unknown":
            unsupported_formats += 1
            continue
        if project_root is not None and not belongs_to_project(probe.project_path, project_root):
            if probe.project_path is None:
                unknown_projects += 1
            else:
                excluded_projects += 1
            continue
        probes.append(probe)
    parsed: list[Metrics] = []
    parse_failures = 0
    no_events_in_window = 0
    for probe in probes:
        try:
            metrics = parse_session(
                probe.path,
                args.provider,
                args.include_locators,
                cutoff=cutoff,
                probe=probe,
            )
        except (OSError, TypeError, UnicodeError, ValueError):
            parse_failures += 1
            continue
        if cutoff is not None and metrics.events_in_window == 0:
            no_events_in_window += 1
            continue
        parsed.append(metrics)
    selected, selection_coverage = select_sessions(
        parsed, args.coverage_target, args.min_sessions, args.max_sessions
    )
    if args.all_projects:
        project_mode = "all_projects"
    elif explicit_input_scope:
        project_mode = "explicit_inputs"
    else:
        project_mode = "project_root"
    return {
        "schema_version": 1,
        "kind": "session_cost_inventory",
        "generated_at": iso_utc(datetime.now(timezone.utc)),
        "privacy": {
            "content_emitted": False,
            "tool_arguments_emitted": False,
            "locators_emitted": bool(args.include_locators),
        },
        "scope": {
            "since": args.since,
            "time_filter_basis": "event_timestamps_with_file_mtime_prefilter",
            "provider": args.provider,
            "include_archived": bool(args.include_archived),
            "project_mode": project_mode,
            "project_key": safe_key(str(project_root)) if project_root is not None else None,
        },
        "coverage": {
            "discovered_files": len(discovered),
            "mtime_eligible_files": len(mtime_eligible),
            "project_eligible_files": len(probes),
            "parsed_files": len(parsed),
            "probe_failures": probe_failures,
            "parse_failures": parse_failures,
            "unsupported_formats": unsupported_formats,
            "excluded_other_projects": excluded_projects,
            "excluded_unknown_projects": unknown_projects,
            "no_events_in_window": no_events_in_window,
            "sessions_with_token_usage": sum(item.workload_tokens is not None for item in parsed),
            "selected_sessions": len(selected),
            **selection_coverage,
        },
        "totals": aggregate(parsed),
        "selected": [
            {**item.public(args.include_locators), "selection_reasons": sorted(set(reasons))}
            for item, reasons in selected
        ],
    }


def is_excluded(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    return any(part in EXCLUDED_DIRS for part in relative.parts)


def document_category(path: Path, root: Path) -> str | None:
    if is_excluded(path, root):
        return None
    if path.name in DOC_NAMES:
        return "instruction_entrypoint"
    if path.name in CONFIG_NAMES and any(part in {".codex", ".claude", ".agents"} for part in path.parts):
        return "agent_configuration"
    if path.name == ".mcp.json":
        return "tool_configuration"
    return None


def scope_relation(path: Path, cwd: Path) -> str:
    parent = path.parent.resolve()
    if parent == cwd or parent in cwd.parents:
        return "ancestor_of_cwd"
    if cwd in parent.parents:
        return "descendant_of_cwd"
    return "other_project_path"


def worktree_root_for(directory: Path, root: Path) -> Path:
    root = root.resolve()
    current = directory.resolve()
    if current != root and root not in current.parents:
        return root
    while True:
        if (current / ".git").exists():
            return current
        if current == root:
            return root
        current = current.parent


def worktree_path(worktree_root: Path, root: Path) -> str:
    relative = worktree_root.relative_to(root)
    return "." if not relative.parts else relative.as_posix()


def inventory_docs(root: Path, cwd: Path | None = None) -> tuple[list[dict[str, Any]], int]:
    root = root.resolve()
    items: list[dict[str, Any]] = []
    unreadable = 0
    effective_cwd = (cwd or root).resolve()
    current_worktree = worktree_root_for(effective_cwd, root)
    paths: list[Path] = []
    for directory, names, filenames in os.walk(root, followlinks=False):
        names[:] = sorted(name for name in names if name not in EXCLUDED_DIRS)
        base = Path(directory)
        paths.extend(base / name for name in filenames)
    for path in sorted(paths):
        category = document_category(path, root)
        if category is None:
            continue
        try:
            raw = path.read_bytes()
        except OSError:
            unreadable += 1
            continue
        text = raw.decode("utf-8", errors="replace")
        document_worktree = worktree_root_for(path.parent, root)
        items.append(
            {
                "path": path.relative_to(root).as_posix(),
                "category": category,
                "bytes": len(raw),
                "characters": len(text),
                "lines": len(text.splitlines()),
                "words": len(re.findall(r"\S+", text)),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "scope_relation": scope_relation(path, effective_cwd),
                "worktree_key": safe_key(str(document_worktree)),
                "worktree_path": worktree_path(document_worktree, root),
                "worktree_relation": (
                    "current" if document_worktree == current_worktree else "other"
                ),
                "load_status": "unknown",
            }
        )
    return items, unreadable


def exact_duplicate_groups(documents: list[dict[str, Any]]) -> list[list[str]]:
    duplicates: dict[str, list[str]] = {}
    for item in documents:
        duplicates.setdefault(item["sha256"], []).append(item["path"])
    return sorted(sorted(paths) for paths in duplicates.values() if len(paths) > 1)


def document_totals(
    documents: list[dict[str, Any]], duplicate_group_count: int | None = None
) -> dict[str, int]:
    if duplicate_group_count is None:
        duplicate_group_count = len(exact_duplicate_groups(documents))
    return {
        "documents": len(documents),
        "bytes": sum(item["bytes"] for item in documents),
        "characters": sum(item["characters"] for item in documents),
        "words": sum(item["words"] for item in documents),
        "exact_duplicate_groups": duplicate_group_count,
    }


def docs_command(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"not a directory: {root}")
    cwd = Path(args.cwd).expanduser().resolve() if args.cwd else root
    if cwd != root and root not in cwd.parents:
        raise ValueError("--cwd must be inside --root")
    documents, unreadable = inventory_docs(root, cwd)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in documents:
        grouped.setdefault(item["worktree_path"], []).append(item)
    worktrees = []
    duplicate_groups: list[list[str]] = []
    for path, items in sorted(grouped.items()):
        groups = exact_duplicate_groups(items)
        duplicate_groups.extend(groups)
        worktrees.append(
            {
                "worktree_key": items[0]["worktree_key"],
                "worktree_path": path,
                "relation": items[0]["worktree_relation"],
                "totals": document_totals(items),
                "exact_duplicate_groups": groups,
            }
        )
    totals = document_totals(documents, len(duplicate_groups))
    totals["worktrees"] = len(worktrees)
    totals["unreadable_documents"] = unreadable
    return {
        "schema_version": 1,
        "kind": "instruction_inventory",
        "generated_at": iso_utc(datetime.now(timezone.utc)),
        "root_key": safe_key(str(root)),
        "cwd_key": safe_key(str(cwd)),
        "content_emitted": False,
        "worktree_accounting": "independent",
        "warning": (
            "Presence and size do not prove that a runtime loaded a file. "
            "Top-level totals cover the inventory; compare instruction sets by worktree."
        ),
        "totals": totals,
        "exact_duplicate_groups": duplicate_groups,
        "worktrees": worktrees,
        "documents": documents,
    }


def new_bucket(turn: int) -> dict[str, Any]:
    return {
        "turn": turn,
        "first_event_at": None,
        "last_event_at": None,
        "model_calls": 0,
        "tool_calls": 0,
        "opaque_wrapper_calls": 0,
        "observed_tool_errors": 0,
        "exact_repeated_calls": 0,
        "compactions": 0,
        "large_tool_outputs": 0,
        "tool_output_chars": 0,
        "input_tokens": None,
        "cache_read_tokens": None,
        "output_tokens": None,
        "reasoning_tokens": None,
    }


def touch_bucket(bucket: dict[str, Any], when: datetime | None) -> None:
    if when is None:
        return
    rendered = iso_utc(when)
    if bucket["first_event_at"] is None or rendered < bucket["first_event_at"]:
        bucket["first_event_at"] = rendered
    if bucket["last_event_at"] is None or rendered > bucket["last_event_at"]:
        bucket["last_event_at"] = rendered


def record_bucket_output(bucket: dict[str, Any], value: Any, is_error: bool) -> None:
    chars = content_chars(value)
    bucket["tool_output_chars"] += chars
    if chars > LARGE_OUTPUT_CHARS:
        bucket["large_tool_outputs"] += 1
    if is_error:
        bucket["observed_tool_errors"] += 1


def select_activity_buckets(
    buckets: list[dict[str, Any]], maximum: int
) -> list[dict[str, Any]]:
    if len(buckets) <= maximum:
        return [{**bucket, "selection_reasons": ["bounded complete sequence"]} for bucket in buckets]
    selected: dict[int, dict[str, Any]] = {}

    def add(bucket: dict[str, Any], reason: str) -> None:
        turn = int(bucket["turn"])
        if turn not in selected:
            if len(selected) >= maximum:
                return
            selected[turn] = {**bucket, "selection_reasons": []}
        selected[turn]["selection_reasons"].append(reason)

    add(buckets[0], "first")
    add(buckets[-1], "last")
    rankings = {
        "high input": sorted(buckets, key=lambda item: item["input_tokens"] or 0, reverse=True),
        "many tool calls": sorted(buckets, key=lambda item: item["tool_calls"], reverse=True),
        "large tool output": sorted(
            buckets, key=lambda item: item["tool_output_chars"], reverse=True
        ),
        "repeated calls": sorted(
            buckets, key=lambda item: item["exact_repeated_calls"], reverse=True
        ),
        "compaction": sorted(buckets, key=lambda item: item["compactions"], reverse=True),
    }
    positions = {reason: 0 for reason in rankings}
    while len(selected) < maximum:
        changed = False
        for reason, ranking in rankings.items():
            while positions[reason] < len(ranking):
                candidate = ranking[positions[reason]]
                positions[reason] += 1
                value_key = {
                    "high input": "input_tokens",
                    "many tool calls": "tool_calls",
                    "large tool output": "tool_output_chars",
                    "repeated calls": "exact_repeated_calls",
                    "compaction": "compactions",
                }[reason]
                if not candidate[value_key]:
                    break
                before = len(selected)
                add(candidate, reason)
                changed = changed or len(selected) > before
                break
            if len(selected) >= maximum:
                break
        if not changed:
            break
    return [selected[key] for key in sorted(selected)]


def inspect_activity(
    path: Path,
    provider: str,
    cutoff: datetime | None,
    maximum: int,
) -> dict[str, Any]:
    buckets: dict[int, dict[str, Any]] = {}
    signatures: Counter[tuple[str, str]] = Counter()
    seen_call_ids: set[str] = set()
    seen_result_ids: set[str] = set()
    seen_usage_ids: set[str] = set()
    turn = 0

    def current_bucket(when: datetime | None) -> dict[str, Any]:
        bucket = buckets.setdefault(turn, new_bucket(turn))
        touch_bucket(bucket, when)
        return bucket

    for event in iter_jsonl(path):
        if event.get("__malformed__"):
            continue
        when = event_time(event)
        if not in_window(when, cutoff):
            continue
        event_type = str(event.get("type", ""))
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        payload_type = str(payload.get("type", ""))
        message = event.get("message") if isinstance(event.get("message"), dict) else {}

        if provider == "codex" and event_type == "response_item" and payload_type == "message":
            if payload.get("role") == "user":
                turn += 1
            bucket = current_bucket(when)
            if payload.get("role") == "assistant":
                bucket["model_calls"] += 1
        elif provider == "claude" and (message.get("role") == "user" or event_type == "user"):
            content = message.get("content", event.get("content"))
            blocks = content if isinstance(content, list) else []
            only_results = bool(blocks) and all(
                isinstance(block, dict) and block.get("type") == "tool_result" for block in blocks
            )
            if not only_results:
                turn += 1

        bucket = current_bucket(when)
        combined = f"{event_type} {payload_type} {payload.get('name', '')}".lower()
        if "compact" in combined or "compact" in str(event.get("subtype", "")).lower():
            bucket["compactions"] += 1

        total, latest = nested_usage(event)
        if provider == "codex" and latest:
            for target, keys in (
                ("input_tokens", ("input_tokens",)),
                ("cache_read_tokens", ("cached_input_tokens", "cache_read_tokens")),
                ("output_tokens", ("output_tokens",)),
                ("reasoning_tokens", ("reasoning_output_tokens", "reasoning_tokens")),
            ):
                value = usage_value(latest, *keys)
                if value is not None:
                    bucket[target] = max(bucket[target] or 0, value)

        if provider == "codex" and event_type == "response_item":
            if payload_type in {"function_call", "custom_tool_call", "local_shell_call"}:
                call_id = str(payload.get("call_id") or payload.get("id") or "")
                if call_id and call_id in seen_call_ids:
                    continue
                if call_id:
                    seen_call_ids.add(call_id)
                name = str(payload.get("name") or payload_type)
                arguments = payload.get("arguments") or payload.get("input") or payload.get("command")
                signature = normalized_call_hash(name, arguments)
                if signatures[(name, signature)]:
                    bucket["exact_repeated_calls"] += 1
                signatures[(name, signature)] += 1
                bucket["tool_calls"] += 1
                if payload_type == "custom_tool_call":
                    bucket["opaque_wrapper_calls"] += 1
            elif payload_type in {
                "function_call_output",
                "custom_tool_call_output",
                "local_shell_call_output",
            }:
                result_id = str(payload.get("call_id") or payload.get("id") or "")
                if result_id and result_id in seen_result_ids:
                    continue
                if result_id:
                    seen_result_ids.add(result_id)
                exit_code = int_or_none(payload.get("exit_code"))
                status = str(payload.get("status", "")).lower()
                error = bool(
                    payload.get("is_error")
                    or payload.get("error")
                    or (exit_code is not None and exit_code != 0)
                    or status in {"error", "failed", "failure"}
                )
                record_bucket_output(bucket, payload.get("output") or payload.get("content"), error)

        if provider == "claude":
            content = message.get("content", event.get("content"))
            blocks = content if isinstance(content, list) else []
            if message.get("role") == "assistant" or event_type == "assistant":
                usage_id = str(message.get("id") or event.get("uuid") or "")
                usage = message.get("usage")
                if isinstance(usage, dict) and (not usage_id or usage_id not in seen_usage_ids):
                    if usage_id:
                        seen_usage_ids.add(usage_id)
                    bucket["model_calls"] += 1
                    context = sum(
                        value or 0
                        for value in (
                            usage_value(usage, "input_tokens"),
                            usage_value(usage, "cache_read_input_tokens", "cache_read_tokens"),
                            usage_value(usage, "cache_creation_input_tokens", "cache_write_tokens"),
                        )
                    )
                    bucket["input_tokens"] = max(bucket["input_tokens"] or 0, context)
                    bucket["output_tokens"] = (bucket["output_tokens"] or 0) + (
                        usage_value(usage, "output_tokens") or 0
                    )
                for block in blocks:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        call_id = str(block.get("id") or "")
                        if call_id and call_id in seen_call_ids:
                            continue
                        if call_id:
                            seen_call_ids.add(call_id)
                        name = str(block.get("name") or "unknown")
                        signature = normalized_call_hash(name, block.get("input"))
                        if signatures[(name, signature)]:
                            bucket["exact_repeated_calls"] += 1
                        signatures[(name, signature)] += 1
                        bucket["tool_calls"] += 1
            for block in blocks:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    result_id = str(block.get("tool_use_id") or "")
                    if result_id and result_id in seen_result_ids:
                        continue
                    if result_id:
                        seen_result_ids.add(result_id)
                    record_bucket_output(bucket, block, bool(block.get("is_error")))

    populated = [
        bucket
        for bucket in buckets.values()
        if any(
            bucket[key]
            for key in (
                "model_calls",
                "tool_calls",
                "tool_output_chars",
                "compactions",
                "input_tokens",
            )
        )
    ]
    populated.sort(key=lambda item: item["turn"])
    repeated = [
        {"tool": name, "signature": signature, "count": count}
        for (name, signature), count in signatures.most_common(20)
        if count > 1
    ]
    selected_buckets = select_activity_buckets(populated, maximum)
    return {
        "total_activity_buckets": len(populated),
        "selected_activity_buckets": len(selected_buckets),
        "selection": "complete" if len(populated) <= maximum else "first-last-and-anomalies",
        "buckets": selected_buckets,
        "repeated_call_signatures": repeated,
    }


def inspect_command(args: argparse.Namespace) -> dict[str, Any]:
    path = Path(args.session).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"not a file: {path}")
    cutoff = cutoff_for(args.since)
    probe = probe_session(path, args.provider)
    if probe.provider == "unknown":
        raise ValueError("unsupported session format")
    metrics = parse_session(path, args.provider, False, cutoff=cutoff, probe=probe)
    return {
        "schema_version": 1,
        "kind": "bounded_session_inspection",
        "generated_at": iso_utc(datetime.now(timezone.utc)),
        "privacy": {
            "content_emitted": False,
            "tool_arguments_emitted": False,
            "locator_emitted": False,
        },
        "scope": {"since": args.since, "provider": probe.provider},
        "session": metrics.public(False),
        "activity": inspect_activity(path, probe.provider, cutoff, args.max_buckets),
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)

    sessions = subparsers.add_parser("sessions", help="Aggregate supported local JSONL sessions")
    sessions.add_argument("--input", action="append", default=[], help="JSONL file or directory")
    sessions.add_argument("--provider", choices=("auto", "claude", "codex"), default="auto")
    sessions.add_argument("--since", default="7d", help="all, Nd, Nh, or ISO timestamp")
    project_scope = sessions.add_mutually_exclusive_group()
    project_scope.add_argument("--project-root", help="Include sessions whose cwd is under this root")
    project_scope.add_argument("--all-projects", action="store_true")
    sessions.add_argument("--include-archived", action="store_true")
    sessions.add_argument("--include-locators", action="store_true")
    sessions.add_argument("--coverage-target", type=float, default=0.70)
    sessions.add_argument("--min-sessions", type=int, default=0)
    sessions.add_argument("--max-sessions", type=int, default=20)
    sessions.add_argument("--pretty", action="store_true")

    docs = subparsers.add_parser("docs", help="Inventory likely instruction entrypoints")
    docs.add_argument("--root", required=True, help="Project root")
    docs.add_argument("--cwd", help="Working directory used to classify instruction scope")
    docs.add_argument("--pretty", action="store_true")

    inspect = subparsers.add_parser(
        "inspect", help="Inspect one selected session without emitting messages or tool payloads"
    )
    inspect.add_argument("session", help="Selected JSONL session file")
    inspect.add_argument("--provider", choices=("auto", "claude", "codex"), default="auto")
    inspect.add_argument("--since", default="all", help="all, Nd, Nh, or ISO timestamp")
    inspect.add_argument("--max-buckets", type=int, default=20)
    inspect.add_argument("--pretty", action="store_true")
    return root


def validate_args(args: argparse.Namespace) -> None:
    if args.command == "sessions":
        if not 0 < args.coverage_target <= 1:
            raise ValueError("--coverage-target must be greater than 0 and at most 1")
        if args.min_sessions < 0 or args.max_sessions < 1:
            raise ValueError("--min-sessions must be non-negative and --max-sessions positive")
        if args.min_sessions > args.max_sessions:
            raise ValueError("--min-sessions cannot exceed --max-sessions")
    if args.command == "inspect" and not 1 <= args.max_buckets <= 200:
        raise ValueError("--max-buckets must be between 1 and 200")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        validate_args(args)
        if args.command == "sessions":
            result = sessions_command(args)
        elif args.command == "docs":
            result = docs_command(args)
        else:
            result = inspect_command(args)
    except (ValueError, argparse.ArgumentTypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=indent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
