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


def _read_owned(path: Path, kind: str) -> dict | None:
    try:
        directory = _open_memory_directory(path.parent)
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
        value = json.loads(_decode(data))
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
    _check_memory_path(path.parent.absolute())
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
    _write_json(path, payload)
    return True


def _text(value: str, name: str, maximum: int = 4000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{name} must contain 1:{maximum} characters")
    return value


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
        elif not isinstance(note.get("entries"), dict):
            raise ValueError("Invalid answer-note entries")
        else:
            entries = note["entries"]
            for candidate in entries.values():
                if not isinstance(candidate, dict) or not all(
                    isinstance(candidate.get(key), str)
                    for key in ("answer", "basis", "coverage", "limits", "source_hash")
                ) or candidate.get("status") not in {"supported", "unresolved", "conflicted"}:
                    raise ValueError("Invalid answer-note entry")
            entry = entries.get(scope)
            if entry is not None:
                status = "current" if entry["source_hash"] == source_hash else "stale"
            elif any(value["source_hash"] == source_hash for value in entries.values()):
                # A paraphrase is not an empty store or proof of equivalence. Return
                # candidates and their limits for assessment before any new search.
                status = "candidates"
                entry = {"entries": {
                    key: {**value, "source_current": value["source_hash"] == source_hash}
                    for key, value in entries.items()
                }}
            else:
                status = "stale" if entries else "miss"
    if status not in {"current", "candidates"}:
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
              "assessment": ("source-current; analyst provenance retained" if status == "current"
                             else "assess scope and source_current of each candidate; not equivalent answers")}
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
    if args.answer_file is not None:
        answer = _decode(read_bytes(Path(args.answer_file), MAX_NOTE_BYTES))
    elif args.answer == "-":
        answer = _decode(sys.stdin.buffer.read(MAX_NOTE_BYTES + 1))
    else:
        answer = args.answer
    answer = _text(answer, "answer", MAX_NOTE_BYTES)
    citations = _parse_ranges(args.cite, len(lines)) if args.cite else []
    quotes = []
    for value in args.quote:
        locator, separator, quote = value.partition("=")
        if not separator or not quote:
            raise ValueError("--quote requires START:END=exact text")
        start, end = _parse_ranges([locator], len(lines))[0]
        if quote not in "\n".join(lines[start - 1:end]):
            raise ValueError(f"Quote does not match source lines {start}:{end}")
        quotes.append({"lines": [start, end], "quote": quote})
    status = getattr(args, "status", "supported")
    if status not in {"supported", "unresolved", "conflicted"}:
        raise ValueError("Invalid analyst status")
    if status != "unresolved" and not citations and not quotes:
        raise ValueError("Supply at least one --cite or --quote supporting the answer")
    note = _read_owned(memory, NOTE_KIND) or {
        "kind": NOTE_KIND, "source": str(source.resolve()), "entries": {},
    }
    if note.get("source") != str(source.resolve()) or not isinstance(note.get("entries"), dict):
        raise ValueError("Answer note belongs to another source or has invalid entries")
    note["entries"][scope] = {
        "source_hash": source_hash, "answer": answer, "status": status,
        "basis": _text(args.basis, "--basis"), "coverage": _text(args.coverage, "--coverage"),
        "limits": args.limits, "citations": [list(pair) for pair in citations], "quotes": quotes,
        "checks": "locator bounds and supplied exact quotes only; not semantic verification",
    }
    changed = _write_owned(memory, note, source, [args.answer_file])
    print(_json({"memory": str(memory), "changed": changed, "source_hash": source_hash}))
    return 0
