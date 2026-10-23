"""Numbered text selection with an exact serialized-output budget."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path

from .common import DEFAULT_MAX_SOURCE_BYTES


NEWLINE_CHARS = len(os.linesep)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _decode(data: bytes) -> str:
    text = data.decode("utf-8", errors="strict")
    if any(ord(character) < 32 and character not in "\t\n\r\f" for character in text):
        raise ValueError("Binary/control-character input is not supported; supply UTF-8 text")
    return text


def _merge(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return merged


def _parse_ranges(values: list[str], line_count: int) -> list[tuple[int, int]]:
    ranges = []
    for value in values:
        parts = value.split(":")
        if len(parts) not in (1, 2) or not all(part.isascii() and part.isdigit() for part in parts):
            raise ValueError(f"Invalid line range {value!r}; use START:END or a line number")
        start, end = int(parts[0]), int(parts[-1])
        if not 1 <= start <= end <= line_count:
            raise ValueError(f"Line range {value!r} is outside source lines 1:{line_count}")
        ranges.append((start, end))
    return _merge(ranges) if values else ([(1, line_count)] if line_count else [])


def _select_ranges(lines: list[str], requested: list[str], find: list[str],
                   context: int) -> list[tuple[int, int]]:
    ranges = _parse_ranges(requested, len(lines))
    if not find:
        return ranges
    needles = [term.casefold() for term in find]
    selected = []
    for start, end in ranges:
        for number in range(start, end + 1):
            if any(term in lines[number - 1].casefold() for term in needles):
                selected.append((max(1, number - context), min(len(lines), number + context)))
    return _merge(selected)


def _prose_ranges(lines: list[str], requested: list[str], find: list[str],
                  context: int) -> tuple[list[tuple[int, int]], int]:
    """Select original prose, not a generated summary or a schema substitute.

    Markdown table rows retain their header and preceding title; paragraphs are
    kept whole. Explicitly scoped code is still excluded in this opt-in view.
    The ordinary reader remains the way to inspect code/use-site constraints.
    """
    allowed = _parse_ranges(requested, len(lines))
    needles = [term.casefold() for term in find]
    code: set[int] = set()
    fence: tuple[str, int] | None = None
    for number, line in enumerate(lines, 1):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            code.add(number)
            if match and match[1][0] == fence[0] and len(match[1]) >= fence[1] and not match[2].strip():
                fence = None
        elif match and (match[1][0] != "`" or "`" not in match[2]):
            code.add(number)
            fence = (match[1][0], len(match[1]))

    selected: set[int] = set()
    omitted_matches = 0
    headings: list[int] = []
    heading_at: dict[int, tuple[int, ...]] = {}
    for number, line in enumerate(lines, 1):
        if number not in code:
            heading = re.match(r"^ {0,3}(#{1,6})\s+", line)
            if heading:
                level = len(heading[1])
                headings = [n for n in headings if len(re.match(r"^ {0,3}(#+)", lines[n - 1])[1]) < level]
                headings.append(number)
        heading_at[number] = tuple(headings)

    for start, end in allowed:
        for number in range(start, end + 1):
            if needles and not any(term in lines[number - 1].casefold() for term in needles):
                continue
            if number in code:
                omitted_matches += 1
                continue
            if not lines[number - 1].strip():
                continue
            selected.update(heading_at[number])
            low = high = number
            if lines[number - 1].lstrip().startswith("|"):
                # Keep each matching row verbatim and the column names. Do not
                # copy every row of a large table for a single matching field.
                table_start = number
                while table_start > 1 and lines[table_start - 2].lstrip().startswith("|") and table_start - 1 not in code:
                    table_start -= 1
                selected.update(range(table_start, min(table_start + 2, len(lines) + 1)))
                # Markdown table labels/titles often aren't ATX headings.
                selected.update(n for n in range(max(1, table_start - 6), table_start)
                                if n not in code and lines[n - 1].strip())
            else:
                while low > 1 and lines[low - 2].strip() and low - 1 not in code and not lines[low - 2].lstrip().startswith(("|", "#")):
                    low -= 1
                while high < len(lines) and lines[high].strip() and high + 1 not in code and not lines[high].lstrip().startswith(("|", "#")):
                    high += 1
            selected.update(n for n in range(max(1, low - context), min(len(lines), high + context) + 1)
                            if n not in code)
    return _merge([(n, n) for n in selected]), omitted_matches


def _is_link(info: os.stat_result) -> bool:
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    )


def _check_memory_path(path: Path) -> os.stat_result:
    for component in reversed((path, *path.parents)):
        info = component.lstat()
        if _is_link(info):
            raise ValueError(f"Refusing memory symlink/reparse traversal: {component}")
    return info


def _open_memory_directory(path: Path) -> int | Path:
    """Resolve trusted ancestors while rejecting a linked memory directory itself."""
    absolute = path.parent.resolve() / path.name
    if not hasattr(os, "O_NOFOLLOW") or os.name == "nt":
        info = _check_memory_path(absolute)
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError("Memory path must be a directory")
        return absolute
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open(absolute.anchor, flags)
    try:
        for part in absolute.parts[1:]:
            next_descriptor = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = next_descriptor
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _open_memory_file(directory: int | Path, name: str) -> int:
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0)
    if isinstance(directory, int):
        return os.open(name, flags | os.O_NOFOLLOW, dir_fd=directory)
    path = directory / name
    before = _check_memory_path(path)
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("Memory entry is not a regular file")
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        after = _check_memory_path(path)
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino) or (
            after.st_dev, after.st_ino
        ) != (opened.st_dev, opened.st_ino):
            raise ValueError("Memory entry changed during inspection")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def _memory(path: Path, budget: int) -> dict[str, object]:
    result: dict[str, object] = {
        "directory": str(path), "status": "incomplete", "entries": [],
        "omitted_entries": 0, "validity": "not-assessed",
    }
    try:
        descriptor = _open_memory_directory(path)
    except FileNotFoundError:
        result["status"] = "miss"
        return result
    except (OSError, ValueError) as exc:
        result["inspection_error"] = str(exc)[:240]
        return result
    entries: list[dict[str, object]] = []
    used = 2
    total = 0
    incomplete = False
    try:
        with os.scandir(descriptor) as scan:
            for entry in scan:
                total += 1
                item: dict[str, object] = {"name": entry.name}
                try:
                    info = entry.stat(follow_symlinks=False)
                    mode = info.st_mode
                    if _is_link(info):
                        item["status"] = "symlink"
                    elif stat.S_ISDIR(mode):
                        item["status"] = "directory"
                    elif info.st_nlink != 1:
                        item["status"] = "hardlink"
                    elif not stat.S_ISREG(mode) or Path(entry.name).suffix.lower() not in {".md", ".txt", ".json"}:
                        item["status"] = "unsupported"
                    else:
                        item["status"] = "budget-exceeded"
                        remaining = max(0, budget - used - len(_json(item)) - 32)
                        file_descriptor = _open_memory_file(descriptor, entry.name)
                        with os.fdopen(file_descriptor, "rb") as stream:
                            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                                raise ValueError("Memory entry changed to a non-regular file")
                            # UTF-8 needs at most four bytes per character. Never load
                            # a large note just to discover it exceeds the output cap.
                            data = stream.read(min(DEFAULT_MAX_SOURCE_BYTES, remaining * 4) + 1)
                        if len(data) <= min(DEFAULT_MAX_SOURCE_BYTES, remaining * 4):
                            candidate = {"name": entry.name, "status": "read", "text": _decode(data)}
                            if used + len(_json(candidate)) + 1 <= budget:
                                item = candidate
                except (OSError, ValueError) as exc:
                    item["status"] = "unreadable"
                    item["error"] = str(exc)[:160]
                incomplete |= item["status"] != "read"
                size = len(_json(item)) + 1
                if used + size <= budget:
                    entries.append(item)
                    used += size
                else:
                    result["omitted_entries"] += 1
                    incomplete = True
    except OSError as exc:
        result["inspection_error"] = str(exc)[:240]
        incomplete = True
    finally:
        if isinstance(descriptor, int):
            os.close(descriptor)
    result["entries"] = entries
    result["total_entries"] = total
    if not incomplete:
        result["status"] = "hit" if total else "miss"
    return result


def read_bytes(source: Path, maximum: int) -> bytes:
    if not stat.S_ISREG(source.stat().st_mode):
        raise ValueError("Source must be a regular UTF-8 text file")
    descriptor = os.open(source, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0))
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("Source must be a regular UTF-8 text file")
        data = stream.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError(f"Source exceeds {maximum} bytes")
    return data


def source_snapshot(source: Path) -> tuple[str, list[str]]:
    data = read_bytes(source, DEFAULT_MAX_SOURCE_BYTES)
    return hashlib.sha256(data).hexdigest(), _source_lines(data)


def _source_lines(data: bytes) -> list[str]:
    text = _decode(data)
    lines = text.split("\n") if text else []
    if text.endswith("\n"):
        lines.pop()
    lines = [line[:-1] if line.endswith("\r") and (number < len(lines) - 1 or text.endswith("\n"))
             else line for number, line in enumerate(lines)]
    return lines


def command_read_text(args: object) -> int:
    """Return memory first or complete source lines, bounded after JSON escaping."""
    from .text_memory import answer_page

    source, budget = Path(args.source), args.max_chars
    prose = getattr(args, "prose", False)
    context = args.context if args.context is not None else (0 if prose else 3)
    if budget <= 0 or context < 0 or args.after_line < 0:
        raise ValueError("--max-chars must be positive; --context and --after-line must be nonnegative")
    if any(not term for term in args.find):
        raise ValueError("--find must not be empty")
    memory_path = getattr(args, "memory", None)
    if not memory_path and (getattr(args, "memory_offset", 0) or getattr(args, "memory_hash", None)):
        raise ValueError("Memory continuation requires --memory")
    data = read_bytes(source, DEFAULT_MAX_SOURCE_BYTES)
    source_hash = hashlib.sha256(data).hexdigest()
    if args.source_hash is not None and args.source_hash != source_hash:
        raise ValueError("Source generation changed; restart selection with its current source hash")
    result: dict[str, object] = {
        "source": str(source), "source_hash": source_hash, "lines": [],
        "next_after_line": None, "total_selected_lines": None,
    }
    if memory_path:
        memory = answer_page(args, source_hash, result)
    else:
        # Leave room for the outer envelope; the exact final response is checked below.
        allowance = max(0, budget - len(_json(result)) - 512)
        memory = _memory(Path(args.memory_dir), allowance) if args.memory_dir is not None else None
    if memory is not None:
        result["memory"] = memory
    if memory is None or memory["status"] in {"miss", "different-source"}:
        lines = _source_lines(data)
        if args.after_line > len(lines):
            raise ValueError("--after-line is outside the source")
        if prose:
            ranges, omitted = _prose_ranges(lines, args.lines, args.find, context)
            result["view"] = "prose; fenced code excluded, use ordinary view for schema/code evidence"
            result["excluded_code_matches"] = omitted
        else:
            ranges = _select_ranges(lines, args.lines, args.find, context)
        result["total_selected_lines"] = sum(end - start + 1 for start, end in ranges)
        selected: list[dict[str, object]] = []
        result["lines"] = selected
        # Reserve the largest possible cursor/count before adding any content.
        result["next_after_line"] = max(1000, len(lines))
        used = len(_json(result)) + NEWLINE_CHARS
        finished = False
        for start, end in ranges:
            for number in range(max(start, args.after_line + 1), end + 1):
                item = {"number": number, "text": lines[number - 1]}
                size = len(_json(item)) + (1 if selected else 0)
                if used + size > budget:
                    if not selected:
                        raise ValueError(f"Line {number} cannot fit; use --max-chars at least {used + size}")
                    result["next_after_line"] = selected[-1]["number"]
                    finished = True
                    break
                selected.append(item)
                used += size
            if finished:
                break
        if not finished:
            result["next_after_line"] = None
    output = _json(result)
    if len(output) + NEWLINE_CHARS > budget:
        raise ValueError(f"Response metadata cannot fit; use --max-chars at least {len(output) + NEWLINE_CHARS}")
    print(output)
    return 0
