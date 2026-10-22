from __future__ import annotations

import argparse
import difflib
import json
import os
import platform
import re
import shutil
import stat
import sys
import tempfile
import unicodedata
import zipfile
from contextlib import closing
from pathlib import Path, PurePosixPath

from .common import MIN_PYTHON, SUPPORTED_SUFFIXES, check_write_access, emit_json, file_signature, join_bounded, normalize_text, python_install_guidance, sha256_file, utc_now
from .index import optional_scalar, paragraphs_from_text, scalar_text, source_hash
from .common import SQLITE_IMPORT_ERROR, sqlite3

WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}

def docling_source(item: dict[str, object], input_path: Path, override: str | None) -> str:
    if override:
        return override.strip()
    direct = item.get("source") or item.get("filename")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    metadata = item.get("metadata")
    if isinstance(metadata, dict):
        origin = metadata.get("origin")
        if isinstance(origin, dict):
            filename = origin.get("filename")
            if isinstance(filename, str) and filename.strip():
                return filename.strip()
    suffix = ".chunks.jsonl"
    return input_path.name[: -len(suffix)] if input_path.name.endswith(suffix) else input_path.stem

def docling_page(item: dict[str, object], location: str) -> str | None:
    if item.get("page") is not None:
        return scalar_text(item["page"], location, "page")
    pages = item.get("page_numbers")
    if pages is None:
        return None
    if not isinstance(pages, list):
        raise ValueError(f"{location}: page_numbers must be an array")
    normalized = list(
        dict.fromkeys(
            scalar_text(page, location, "page_numbers item")
            for page in pages
            if page is not None
        )
    )
    return ",".join(normalized) or None

def docling_section(item: dict[str, object], location: str) -> str | None:
    if item.get("section") is not None:
        return scalar_text(item["section"], location, "section")
    headings = item.get("headings")
    if headings is None:
        return None
    if not isinstance(headings, list):
        raise ValueError(f"{location}: headings must be an array")
    normalized = [scalar_text(heading, location, "headings item") for heading in headings]
    return " > ".join(normalized) or None

def docling_context(item: dict[str, object], location: str) -> str | None:
    captions = item.get("captions")
    if captions is None:
        return optional_scalar(item, "context", location)
    if not isinstance(captions, list):
        raise ValueError(f"{location}: captions must be an array")
    normalized = [scalar_text(caption, location, "captions item") for caption in captions]
    return " | ".join(normalized) or None

def command_import_docling(args: argparse.Namespace) -> int:
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    if not input_path.is_file():
        raise ValueError(f"Docling chunks file does not exist: {input_path}")
    if input_path == output_path:
        raise ValueError("Input and output paths must be different")
    if output_path.exists() and not args.force:
        raise ValueError(f"Output already exists: {output_path}; pass --force to replace it")
    if args.source is not None and not args.source.strip():
        raise ValueError("--source must not be empty")
    if args.version is not None:
        args.version = scalar_text(args.version, "--version", "version")
    if args.date is not None:
        args.date = scalar_text(args.date, "--date", "date")
    canonical_hash = (
        source_hash(args.source_sha256, "", "--source-sha256")
        if args.source_sha256 is not None
        else None
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    records_written = 0
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            dir=output_path.parent,
            delete=False,
        ) as output_handle:
            temporary_path = Path(output_handle.name)
            with input_path.open("r", encoding="utf-8") as input_handle:
                for line_number, line in enumerate(input_handle, start=1):
                    if not line.strip():
                        continue
                    location = f"{input_path}:{line_number}"
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"{location}: invalid JSON: {exc}") from exc
                    if not isinstance(item, dict) or not isinstance(item.get("text"), str):
                        raise ValueError(f"{location}: expected an object with string field 'text'")
                    contextualized_text = item["text"].strip()
                    raw_text = item.get("raw_text")
                    if raw_text is not None and not isinstance(raw_text, str):
                        raise ValueError(f"{location}: raw_text must be a string")
                    raw_candidate = raw_text.strip() if isinstance(raw_text, str) else ""
                    text = raw_candidate or contextualized_text
                    if not text:
                        raise ValueError(f"{location}: text must not be empty")

                    record: dict[str, object] = {
                        "text": text,
                        "source": docling_source(item, input_path, args.source),
                    }
                    page = docling_page(item, location)
                    section = docling_section(item, location)
                    context = docling_context(item, location)
                    version = (
                        args.version
                        if args.version is not None
                        else optional_scalar(item, "version", location)
                    )
                    date = (
                        args.date
                        if args.date is not None
                        else optional_scalar(item, "date", location)
                    )
                    for key, value in {
                        "page": page,
                        "section": section,
                        "context": context,
                        "version": version,
                        "date": date,
                        "source_hash": canonical_hash,
                    }.items():
                        if value is not None:
                            record[key] = value
                    output_handle.write(
                        json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
                    )
                    records_written += 1
        if records_written == 0:
            raise ValueError(f"Docling chunks file contains no records: {input_path}")
        temporary_path.replace(output_path)
    except BaseException:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise

    emit_json(
        {
            "input": str(input_path),
            "output": str(output_path),
            "records_written": records_written,
        },
        args.pretty,
    )
    return 0

def command_doctor(args: argparse.Namespace) -> int:
    python_ok = sys.version_info >= MIN_PYTHON
    sqlite_ok = sqlite3 is not None
    status: dict[str, object] = {
        "platform": platform.system() or sys.platform,
        "python": platform.python_version(),
        "python_minimum": ".".join(map(str, MIN_PYTHON)),
        "python_ok": python_ok,
        "sqlite3": sqlite_ok,
        "sqlite": sqlite3.sqlite_version if sqlite3 is not None else None,
        "fts5": False,
    }

    if SQLITE_IMPORT_ERROR:
        status["sqlite3_error"] = SQLITE_IMPORT_ERROR

    if sqlite3 is not None:
        try:
            with closing(sqlite3.connect(":memory:")) as connection:
                connection.execute("CREATE VIRTUAL TABLE fts5_probe USING fts5(text)")
                connection.execute("INSERT INTO fts5_probe(text) VALUES ('probe')")
                probe = connection.execute(
                    "SELECT rowid FROM fts5_probe WHERE fts5_probe MATCH 'probe'"
                ).fetchone()
                if probe is None:
                    raise RuntimeError("FTS5 probe query returned no result")
            status["fts5"] = True
        except (sqlite3.Error, RuntimeError) as exc:
            status["fts5_error"] = str(exc)

    write_ok, write_error, write_dir = check_write_access(args.write_dir)
    status.update({"write": write_ok, "write_directory": str(write_dir)})
    if write_error:
        status["write_error"] = write_error
        status["write_remediation"] = (
            "Choose an existing writable directory with --write-dir or change its permissions."
        )

    runtime_ok = python_ok and sqlite_ok and status["fts5"] is True
    if not runtime_ok:
        status["python_install"] = python_install_guidance()

    status["ok"] = runtime_ok and write_ok
    emit_json(status, args.pretty)
    return 0 if status["ok"] else 1

def validated_archive_members(
    archive: zipfile.ZipFile,
    max_entries: int,
    max_total_bytes: int,
    max_member_bytes: int,
    max_ratio: int,
) -> list[tuple[zipfile.ZipInfo, Path]]:
    members = archive.infolist()
    if len(members) > max_entries:
        raise ValueError(
            f"Archive exceeds --max-entries ({len(members)} > {max_entries})"
        )
    validated: list[tuple[zipfile.ZipInfo, Path]] = []
    paths: dict[str, bool] = {}
    total_bytes = 0
    for info in members:
        raw_name = info.filename
        if "\x00" in raw_name:
            raise ValueError("Archive contains a NUL byte in a member name")
        normalized_name = raw_name.replace("\\", "/")
        if (
            not normalized_name
            or normalized_name.startswith("/")
            or re.match(r"^[A-Za-z]:", normalized_name)
        ):
            raise ValueError(f"Unsafe archive member path: {raw_name!r}")
        pure_path = PurePosixPath(normalized_name)
        if any(part in ("", ".", "..") for part in pure_path.parts):
            raise ValueError(f"Unsafe archive member path: {raw_name!r}")
        for part in pure_path.parts:
            stem = part.split(".", 1)[0].upper()
            if (
                ":" in part
                or part.rstrip(" .") != part
                or stem in WINDOWS_RESERVED_NAMES
                or any(ord(character) < 32 for character in part)
            ):
                raise ValueError(f"Non-portable archive member path: {raw_name!r}")
        relative_path = Path(*pure_path.parts)
        normalized_key = unicodedata.normalize(
            "NFC", relative_path.as_posix()
        ).casefold()
        if normalized_key == ".doc-research-archive.json":
            raise ValueError("Archive uses the reserved extraction-manifest path")
        if normalized_key in paths:
            raise ValueError(f"Archive contains a duplicate path: {raw_name!r}")

        mode = (info.external_attr >> 16) & 0xFFFF
        if stat.S_ISLNK(mode):
            raise ValueError(f"Archive contains a symbolic link: {raw_name!r}")
        file_type = stat.S_IFMT(mode)
        if file_type and not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise ValueError(f"Archive contains an unsupported file type: {raw_name!r}")
        if info.flag_bits & 0x1:
            raise ValueError(f"Encrypted archive members are not supported: {raw_name!r}")
        if info.file_size < 0 or info.compress_size < 0:
            raise ValueError(f"Archive member has an invalid size: {raw_name!r}")
        is_directory = info.is_dir()
        if not is_directory:
            if info.file_size > max_member_bytes:
                raise ValueError(
                    f"Archive member exceeds --max-member-bytes: {raw_name!r}"
                )
            ratio = info.file_size / max(1, info.compress_size)
            if ratio > max_ratio:
                raise ValueError(
                    f"Archive member exceeds --max-ratio ({ratio:.1f} > {max_ratio}): "
                    f"{raw_name!r}"
                )
            total_bytes += info.file_size
            if total_bytes > max_total_bytes:
                raise ValueError(
                    f"Archive exceeds --max-total-bytes "
                    f"({total_bytes} > {max_total_bytes})"
                )
        paths[normalized_key] = is_directory
        validated.append((info, relative_path))

    for _, relative_path in validated:
        for parent in relative_path.parents:
            if parent == Path("."):
                break
            parent_key = unicodedata.normalize("NFC", parent.as_posix()).casefold()
            parent_type = paths.get(parent_key)
            if parent_type is False:
                raise ValueError(
                    f"Archive path is nested below a file: {relative_path.as_posix()!r}"
                )
    return validated

def command_extract_zip(args: argparse.Namespace) -> int:
    if min(
        args.max_entries,
        args.max_total_bytes,
        args.max_member_bytes,
        args.max_ratio,
    ) <= 0:
        raise ValueError("Archive safety limits must be greater than zero")
    archive_path = args.archive.resolve()
    if not archive_path.is_file():
        raise ValueError(f"ZIP archive does not exist: {archive_path}")
    archive_signature = file_signature(archive_path)
    output_path = args.output.resolve()
    if output_path.exists():
        raise ValueError(f"Extraction output already exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = Path(
        tempfile.mkdtemp(prefix=f".{output_path.name}.", dir=output_path.parent)
    )
    extracted_files = 0
    extracted_bytes = 0
    manifest_members: list[dict[str, object]] = []
    try:
        try:
            with zipfile.ZipFile(archive_path) as archive:
                members = validated_archive_members(
                    archive,
                    args.max_entries,
                    args.max_total_bytes,
                    args.max_member_bytes,
                    args.max_ratio,
                )
                for info, relative_path in members:
                    destination = temporary_path / relative_path
                    if info.is_dir():
                        destination.mkdir(mode=0o700, parents=True, exist_ok=True)
                        if os.name != "nt":
                            destination.chmod(0o700)
                        continue
                    destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                    written = 0
                    with archive.open(info, "r") as source, destination.open("xb") as target:
                        while True:
                            block = source.read(1024 * 1024)
                            if not block:
                                break
                            written += len(block)
                            extracted_bytes += len(block)
                            if (
                                written > args.max_member_bytes
                                or extracted_bytes > args.max_total_bytes
                            ):
                                raise ValueError(
                                    "Archive expanded beyond the configured safety limits"
                                )
                            target.write(block)
                    if written != info.file_size:
                        raise ValueError(
                            f"Archive member size changed while extracting: {info.filename!r}"
                        )
                    if os.name != "nt":
                        destination.chmod(0o600)
                    extracted_files += 1
                    manifest_members.append(
                        {
                            "path": relative_path.as_posix(),
                            "bytes": written,
                            "crc32": f"{info.CRC:08x}",
                        }
                    )
        except (zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
            raise ValueError(f"Invalid ZIP archive: {archive_path}") from exc

        archive_hash = sha256_file(archive_path)
        if file_signature(archive_path) != archive_signature:
            raise ValueError(f"ZIP archive changed during extraction: {archive_path}")
        manifest = {
            "archive": str(archive_path),
            "archive_sha256": archive_hash,
            "extracted_at": utc_now(),
            "file_count": extracted_files,
            "total_bytes": extracted_bytes,
            "members": manifest_members,
        }
        manifest_path = temporary_path / ".doc-research-archive.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if os.name != "nt":
            manifest_path.chmod(0o600)
        if output_path.exists():
            raise ValueError(f"Extraction output appeared during extraction: {output_path}")
        os.rename(temporary_path, output_path)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            shutil.rmtree(temporary_path)

    emit_json(
        {
            "archive": str(archive_path),
            "output": str(output_path),
            "archive_sha256": manifest["archive_sha256"],
            "file_count": extracted_files,
            "total_bytes": extracted_bytes,
            "manifest": str(output_path / ".doc-research-archive.json"),
        },
        args.pretty,
    )
    return 0

def normalized_comparison_units(
    path: Path, max_source_bytes: int, max_units: int
) -> list[str]:
    if not path.is_file():
        raise ValueError(f"Source file does not exist: {path}")
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(
            f"Unsupported source type {path.suffix or '<none>'}; expected .md, .txt, or .jsonl"
        )
    size = path.stat().st_size
    if size > max_source_bytes:
        raise ValueError(
            f"Source exceeds --max-source-bytes ({size} > {max_source_bytes}): {path}"
        )

    units: list[str] = []

    def append_unit(value: str) -> None:
        if len(units) >= max_units:
            raise ValueError(
                f"Comparison exceeds --max-units ({max_units}) while reading {path}"
            )
        units.append(value)

    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
                if not isinstance(item, dict) or not isinstance(item.get("text"), str):
                    raise ValueError(
                        f"{path}:{line_number}: expected an object with string field 'text'"
                    )
                metadata = {
                    key: str(item[key])
                    for key in (
                        "source",
                        "source_hash",
                        "page",
                        "section",
                        "context",
                        "version",
                        "date",
                    )
                    if item.get(key) is not None
                }
                text = normalize_text(item["text"])
                prefix = json.dumps(
                    metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                )
                append_unit(f"{prefix}\t{text}" if prefix else text)
        return units

    raw = path.read_text(encoding="utf-8")
    for page, section, text in paragraphs_from_text(raw):
        metadata = {
            key: value
            for key, value in {"page": page, "section": section}.items()
            if value is not None
        }
        normalized = normalize_text(text)
        prefix = json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        append_unit(f"{prefix}\t{normalized}" if prefix else normalized)
    return units

def comparison_snapshot(
    path: Path, max_source_bytes: int, max_units: int
) -> tuple[list[str], str]:
    if not path.is_file():
        raise ValueError(f"Source file does not exist: {path}")
    before = file_signature(path)
    units = normalized_comparison_units(path, max_source_bytes, max_units)
    digest = sha256_file(path)
    after = file_signature(path)
    if after != before:
        raise ValueError(f"Source changed during comparison: {path}; retry")
    return units, digest

def command_compare(args: argparse.Namespace) -> int:
    if not 0 <= args.context_lines <= 20:
        raise ValueError("--context-lines must be between 0 and 20")
    if not 100 <= args.max_total_chars <= 100000:
        raise ValueError("--max-total-chars must be between 100 and 100000")
    if args.max_source_bytes <= 0:
        raise ValueError("--max-source-bytes must be greater than zero")
    if args.max_units <= 0:
        raise ValueError("--max-units must be greater than zero")

    left = args.left.resolve()
    right = args.right.resolve()
    left_units, left_hash = comparison_snapshot(
        left, args.max_source_bytes, args.max_units
    )
    right_units, right_hash = comparison_snapshot(
        right, args.max_source_bytes, args.max_units
    )
    diff, diff_truncated = join_bounded(
        difflib.unified_diff(
            left_units,
            right_units,
            fromfile=str(left),
            tofile=str(right),
            n=args.context_lines,
            lineterm="",
        ),
        args.max_total_chars,
    )
    emit_json(
        {
            "left": {
                "path": str(left),
                "sha256": left_hash,
                "units": len(left_units),
            },
            "right": {
                "path": str(right),
                "sha256": right_hash,
                "units": len(right_units),
            },
            "identical": left_units == right_units,
            "diff_truncated": diff_truncated,
            "diff": diff,
        },
        args.pretty,
    )
    return 0
