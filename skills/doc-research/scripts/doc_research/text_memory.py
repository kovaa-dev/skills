"""Mechanical provenance for ordinary text research.

One answer note owns findings. Neither source freshness nor a quote match certifies
an analyst's conclusion.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
from pathlib import Path

from .text_reader import (
    _check_memory_path, _decode, _json, _open_memory_directory,
    _open_memory_file, _parse_ranges, read_bytes, source_snapshot, NEWLINE_CHARS,
)

MAX_NOTE_BYTES = 1_048_576
NOTE_KIND = "doc-research-answer"
POINT_STATUSES = {"confirmed", "interpretation", "unresolved", "conflicted"}
POINT_FIELDS = {"text", "status", "basis", "coverage", "limits", "cite", "quote", "exact", "depends_on"}


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate memory/point field: {key}")
        result[key] = value
    return result


def _read_owned(path: Path, kind: str) -> dict | None:
    try:
        directory = _open_memory_directory(path.parent.resolve())
    except FileNotFoundError:
        return None
    try:
        try:
            descriptor = _open_memory_file(directory, path.name)
        except FileNotFoundError:
            return None
        with os.fdopen(descriptor, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError("Memory/state must be a regular, unaliased file")
            data = stream.read(MAX_NOTE_BYTES + 1)
        if len(data) > MAX_NOTE_BYTES:
            raise ValueError("Memory/state exceeds 1 MiB; use the existing owner directly")
        value = json.loads(_decode(data), object_pairs_hook=_unique_object)
        if not isinstance(value, dict) or value.get("kind") != kind:
            raise ValueError("Existing file belongs to another format; use its owner, not save-answer")
        return value
    finally:
        if isinstance(directory, int):
            os.close(directory)


def _write_owned(path: Path, payload: dict, source: Path, inputs: list[Path | None]) -> bool:
    from .evidence_pack import _write_json
    from .index import validate_output_paths

    # Reuse the package's collision and atomic-write rules. One writer owns each
    # artifact; this is not a concurrent database or an adversarial directory sandbox.
    # System ancestors such as macOS /tmp are trusted aliases. The artifact
    # itself must still be an unaliased regular file.
    path = path.parent.resolve() / path.name
    _check_memory_path(path.parent)
    if path.exists() or path.is_symlink():
        info = _check_memory_path(path.absolute())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("Refusing to overwrite an aliased or non-regular artifact")
    validate_output_paths(source, [path], inputs)
    if len((_json(payload) + "\n").encode("utf-8")) > MAX_NOTE_BYTES:
        raise ValueError("Memory/state exceeds 1 MiB; narrow the scope")
    previous = _read_owned(path, payload["kind"])
    if previous == payload:
        return False
    _write_json(path, payload, max_bytes=MAX_NOTE_BYTES)
    return True


def _text(value: str, name: str, maximum: int = 4000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{name} must contain 1:{maximum} characters")
    return value


def _point(value: dict, stored: bool = False) -> dict:
    allowed = POINT_FIELDS | ({"source_hash", "review_required"} if stored else set())
    if not isinstance(value, dict) or value.keys() - allowed:
        raise ValueError("Invalid point fields; use text/status/basis/coverage/limits/cite/quote/exact/depends_on")
    if stored and (POINT_FIELDS | {"source_hash"}) - value.keys():
        raise ValueError("Incomplete stored point; assess provenance through its owner")
    result = {key: _text(value.get(key), key, MAX_NOTE_BYTES if key == "text" else 4000)
              for key in ("text", "basis", "coverage")}
    if not isinstance(value.get("status"), str) or value["status"] not in POINT_STATUSES:
        raise ValueError("Each point needs an explicit confirmed/interpretation/unresolved/conflicted status")
    result["status"] = value["status"]
    result["limits"] = value.get("limits", "")
    if not isinstance(result["limits"], str) or len(result["limits"]) > 4000:
        raise ValueError("Point limits must be text within 4000 characters")
    if result["status"] != "confirmed" and not result["limits"].strip():
        raise ValueError("Unconfirmed points need their own limits/uncertainty")
    for key in ("cite", "quote", "exact", "depends_on"):
        values = value.get(key, [])
        if not isinstance(values, list):
            raise ValueError(f"{key} must be a list")
        result[key] = [_text(item, key) for item in values]
    if result["status"] in {"confirmed", "interpretation"} and not any(
        result[key] for key in ("cite", "quote", "depends_on")
    ):
        raise ValueError("Confirmed/interpretation points need locators or explicit dependencies")
    if stored:
        result["source_hash"] = _text(value.get("source_hash"), "source_hash")
        if "review_required" in value:
            result["review_required"] = _text(value["review_required"], "review_required")
            if result["status"] != "unresolved":
                raise ValueError("A point requiring review cannot remain confirmed")
    return result


def _dependency_order(points: dict) -> list[str]:
    # Iterative traversal: a large user-supplied chain must not exhaust recursion.
    remaining = {key: set(point["depends_on"]) for key, point in points.items()}
    if any(deps - points.keys() for deps in remaining.values()):
        raise ValueError("Point dependency does not exist in this scope")
    order = []
    while remaining:
        ready = {key for key, deps in remaining.items() if not deps}
        if not ready:
            raise ValueError("Point dependencies contain a cycle")
        order.extend(sorted(ready))
        remaining = {key: deps - ready for key, deps in remaining.items() if key not in ready}
    return order


def _entries(note: dict) -> dict:
    entries = note.get("entries")
    if not isinstance(entries, dict):
        raise ValueError("Invalid answer-note entries")
    for scope, entry in entries.items():
        _text(scope, "scope")
        if not isinstance(entry, dict) or set(entry) != {"points"} or not isinstance(entry["points"], dict):
            raise ValueError("Expected point-scoped answer memory; no implicit conversion of whole-answer assessments")
        for key, point in entry["points"].items():
            _text(key, "point ID")
            _point(point, stored=True)
        _dependency_order(entry["points"])
    return entries


def _view(entry: dict, source_hash: str) -> dict:
    points = {key: {**point, "source_current": point["source_hash"] == source_hash}
              for key, point in entry["points"].items()}
    for key in _dependency_order(points):
        point = points[key]
        point["reusable"] = (point["source_current"] and point["status"] == "confirmed"
                             and not point.get("review_required")
                             and all(points[dep]["reusable"] for dep in point["depends_on"]))
    return {"points": points}


def answer_page(args: object, source_hash: str, envelope: dict) -> dict:
    scope = _text(args.scope, "--scope") if args.scope is not None else None
    offset = args.memory_offset
    if offset < 0 or (offset and not args.memory_hash):
        raise ValueError("Memory continuation needs a nonnegative offset and --memory-hash")
    note = _read_owned(Path(args.memory), NOTE_KIND)
    status = "miss"
    entry = None
    if note is not None:
        if note.get("source") != str(Path(args.source).resolve()):
            status = "different-source"
        else:
            entries = {key: _view(value, source_hash) for key, value in _entries(note).items()}
            entry = entries.get(scope)
            if entry is not None:
                current = [point["source_current"] for point in entry["points"].values()]
                status = "current" if current and all(current) else "partial" if any(current) else "stale"
            elif entries:
                # A paraphrase is not an empty store or proof of equivalence. Return
                # candidates and their limits for assessment before any new search.
                status = "candidates"
                entry = {"entries": entries}
            else:
                status = "stale" if entries else "miss"
    if status not in {"current", "partial", "candidates", "stale"} or entry is None:
        if offset or args.memory_hash:
            raise ValueError("Memory/source changed during continuation; restart memory lookup")
        return {"status": status}
    # Page the complete entry, not just the answer: no qualifiers or provenance
    # disappear when a note exceeds one response. Concatenate text before parsing.
    content = _json(entry)
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if args.memory_hash and args.memory_hash != digest:
        raise ValueError("Memory changed during continuation; restart memory lookup")
    if offset >= len(content):
        raise ValueError("Memory offset is outside the entry")
    result = {"status": status, "memory_hash": digest, "text": "",
              "next_offset": max(1000, len(content)),
              "assessment": "assess scope; reusable retains analyst review, not semantic certification"}
    low, high = 0, len(content) - offset
    while low < high:
        middle = (low + high + 1) // 2
        result["text"] = content[offset:offset + middle]
        candidate = {**envelope, "memory": result}
        if len(_json(candidate)) + NEWLINE_CHARS <= args.max_chars:
            low = middle
        else:
            high = middle - 1
    if not low:
        raise ValueError("Memory envelope cannot fit; increase --max-chars")
    result["text"] = content[offset:offset + low]
    result["next_offset"] = offset + low if offset + low < len(content) else None
    return result


def command_save_answer(args: object) -> int:
    source, memory = Path(args.source), Path(args.memory)
    scope = _text(args.scope, "--scope")
    source_hash, lines = source_snapshot(source)
    if source_hash != args.source_hash:
        raise ValueError("Source generation changed; do not save this answer against new bytes")
    if args.points_file is not None:
        body = _decode(read_bytes(Path(args.points_file), MAX_NOTE_BYTES))
    elif args.points == "-":
        body = _decode(sys.stdin.buffer.read(MAX_NOTE_BYTES + 1))
    else:
        body = args.points
    body = _text(body, "points JSON", MAX_NOTE_BYTES)
    if len(body.encode("utf-8")) > MAX_NOTE_BYTES:
        raise ValueError("Points input exceeds 1 MiB")
    updates = json.loads(body, object_pairs_hook=_unique_object)
    if not isinstance(updates, dict) or not updates:
        raise ValueError("--points must be a nonempty object keyed by stable point IDs")
    reviewed = set(args.reviewed)
    if reviewed - updates.keys():
        raise ValueError("--reviewed IDs must belong to the supplied updates")
    note = _read_owned(memory, NOTE_KIND) or {
        "kind": NOTE_KIND, "source": str(source.resolve()), "entries": {},
    }
    if note.get("source") != str(source.resolve()):
        raise ValueError("Answer note belongs to another source")
    previous = _entries(note).get(scope, {"points": {}})["points"]
    points = dict(previous)
    changed_ids = set()
    for key, value in updates.items():
        _text(key, "point ID")
        point = _point(value)
        if point["cite"]:
            _parse_ranges(point["cite"], len(lines))
        excerpts = []
        for value in point["quote"]:
            locator, separator, quote = value.partition("=")
            if not separator or not quote:
                raise ValueError("quote requires START:END=exact text")
            start, end = _parse_ranges([locator], len(lines))[0]
            if quote not in "\n".join(lines[start - 1:end]):
                raise ValueError(f"Quote does not match source lines {start}:{end}")
            excerpts.append(quote)
        if point["status"] == "confirmed" and any(
            literal not in point["text"] or not any(literal in excerpt for excerpt in excerpts)
            for literal in point["exact"]
        ):
            raise ValueError("Confirmed exact literals must occur verbatim in the point and a checked quote")
        point["source_hash"] = source_hash
        if point != previous.get(key):
            changed_ids.add(key)
            if point["status"] == "confirmed" and key not in reviewed:
                raise ValueError(f"New/changed confirmation needs actual analyst review: --reviewed {key}")
        points[key] = point
    invalidated = []
    for key in _dependency_order(points):
        point = points[key]
        if set(point["depends_on"]) & changed_ids and not (key in updates and key in reviewed):
            point = points[key] = {**point, "status": "unresolved",
                                   "review_required": "Upstream point changed; review affected conclusion",
                                   "limits": point["limits"] or "Dependent conclusion requires review"}
            changed_ids.add(key)
            invalidated.append(key)
        if key in updates and point["status"] == "confirmed" and any(
            points[dep]["status"] != "confirmed" or points[dep]["source_hash"] != source_hash
            or points[dep].get("review_required") for dep in point["depends_on"]
        ):
            raise ValueError(f"Confirmed point {key} depends on unconfirmed or stale evidence")
    note["entries"][scope] = {"points": points}
    changed = _write_owned(memory, note, source, [args.points_file])
    print(_json({"memory": str(memory), "changed": changed, "source_hash": source_hash,
                 "invalidated": invalidated}))
    return 0
