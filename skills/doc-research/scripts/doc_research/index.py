from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

from .common import APPLICATION_ID, CHUNK_COLUMNS, HEADING, INDEX_FINGERPRINT_KEY, METADATA_COLUMNS, MIN_INDEX_HEADROOM_BYTES, PAGE_MARKER, SCHEMA_VERSION, SHA256, SOURCE_COLUMNS, SUPPORTED_SUFFIXES, TOKEN, application_id, clip_text, connect, database, database_objects, emit_json, file_signature, harden_database_permissions, normalize_text, schema_version, sha256_file, table_exists
from .common import sqlite3

@dataclass(frozen=True)
class Chunk:
    source: str
    source_hash: str
    page: str | None
    section: str | None
    version: str | None
    date: str | None
    context: str | None
    text: str

@dataclass(frozen=True)
class SourceFile:
    path: Path
    relative_path: str
    size: int
    signature: tuple[int, int, int, int]
    sha256: str

def split_long(text: str, max_chars: int, overlap: int = 200) -> Iterator[str]:
    text = normalize_text(text)
    if not text:
        return
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            split_at = text.rfind(" ", start + max_chars // 2, end)
            if split_at > start:
                end = split_at
        piece = text[start:end].strip()
        if piece:
            yield piece
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)

def paragraphs_from_text(raw: str) -> Iterator[tuple[str | None, str | None, str]]:
    pages = raw.split("\f")
    has_page_breaks = len(pages) > 1
    current_section: str | None = None

    for page_index, page_text in enumerate(pages, start=1):
        current_page: str | None = str(page_index) if has_page_breaks else None
        buffer: list[str] = []

        def flush() -> tuple[str | None, str | None, str] | None:
            if not buffer:
                return None
            value = "\n".join(part.rstrip() for part in buffer if part.strip()).strip()
            buffer.clear()
            if not value:
                return None
            return current_page, current_section, value

        for line in page_text.splitlines():
            page_match = PAGE_MARKER.match(line)
            if page_match:
                item = flush()
                if item:
                    yield item
                current_page = page_match.group(1).strip()
                continue

            heading_match = HEADING.match(line)
            if heading_match:
                item = flush()
                if item:
                    yield item
                current_section = heading_match.group(1).strip()
                continue

            if not line.strip():
                item = flush()
                if item:
                    yield item
                continue

            buffer.append(line)

        item = flush()
        if item:
            yield item

def chunks_from_text(
    path: Path, relative_path: str, source_hash: str, max_chars: int
) -> Iterator[Chunk]:
    raw = path.read_text(encoding="utf-8")
    pending: list[str] = []
    pending_length = 0
    pending_page: str | None = None
    pending_section: str | None = None

    def flush_pending() -> Chunk | None:
        nonlocal pending_length
        if not pending:
            return None
        value = "\n\n".join(pending).strip()
        pending.clear()
        pending_length = 0
        if not value:
            return None
        return Chunk(
            relative_path,
            source_hash,
            pending_page,
            pending_section,
            None,
            None,
            None,
            value,
        )

    for page, section, paragraph in paragraphs_from_text(raw):
        if (page, section) != (pending_page, pending_section):
            item = flush_pending()
            if item:
                yield item
            pending_page, pending_section = page, section

        if len(paragraph) > max_chars:
            item = flush_pending()
            if item:
                yield item
            for piece in split_long(paragraph, max_chars):
                yield Chunk(relative_path, source_hash, page, section, None, None, None, piece)
            continue

        projected = pending_length + len(paragraph) + (2 if pending else 0)
        if pending and projected > max_chars:
            item = flush_pending()
            if item:
                yield item
        pending.append(paragraph)
        pending_length += len(paragraph) + (2 if len(pending) > 1 else 0)

    item = flush_pending()
    if item:
        yield item

def scalar_text(value: object, location: str, field: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError(f"{location}: {field} must be a string or number")
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{location}: {field} must not be empty")
    return normalized

def optional_scalar(item: dict[str, object], field: str, location: str) -> str | None:
    value = item.get(field)
    return None if value is None else scalar_text(value, location, field)

def source_hash(value: object, fallback: str, location: str) -> str:
    if value is None:
        return fallback
    normalized = scalar_text(value, location, "source_hash").lower()
    if not SHA256.fullmatch(normalized):
        raise ValueError(f"{location}: source_hash must be 64 hexadecimal characters")
    return normalized

def chunks_from_jsonl(
    path: Path, relative_path: str, input_hash: str, max_chars: int
) -> Iterator[Chunk]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{relative_path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(item, dict) or not isinstance(item.get("text"), str):
                raise ValueError(
                    f"{relative_path}:{line_number}: expected an object with string field 'text'"
                )

            text = item["text"].strip()
            if not text:
                raise ValueError(f"{relative_path}:{line_number}: text must not be empty")
            location = f"{relative_path}:{line_number}"
            source = optional_scalar(item, "source", location) or relative_path
            page = optional_scalar(item, "page", location)
            section = optional_scalar(item, "section", location)
            version = optional_scalar(item, "version", location)
            date = optional_scalar(item, "date", location)
            context = optional_scalar(item, "context", location)
            canonical_hash = source_hash(item.get("source_hash"), input_hash, location)
            for piece in split_long(text, max_chars):
                yield Chunk(
                    source,
                    canonical_hash,
                    page,
                    section,
                    version,
                    date,
                    context,
                    piece,
                )

def iter_source_files(corpus: Path) -> Iterator[Path]:
    for path in sorted(corpus.rglob("*")):
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if any(part.startswith(".") for part in path.relative_to(corpus).parts):
            continue
        yield path

def chunk_columns(connection: sqlite3.Connection) -> tuple[str, ...]:
    return tuple(row["name"] for row in connection.execute("PRAGMA table_info(chunks)"))

def source_columns(connection: sqlite3.Connection) -> tuple[str, ...]:
    return tuple(row["name"] for row in connection.execute("PRAGMA table_info(sources)"))

def metadata_columns(connection: sqlite3.Connection) -> tuple[str, ...]:
    return tuple(row["name"] for row in connection.execute("PRAGMA table_info(metadata)"))

def require_index_owner(connection: sqlite3.Connection) -> None:
    identifier = application_id(connection)
    if identifier == APPLICATION_ID:
        return
    if identifier != 0:
        raise ValueError("Database belongs to another application; refusing to use it")
    objects = database_objects(connection)
    if objects:
        raise ValueError(
            "Existing database is not a corpus index with this tool's application "
            "identifier; refusing to use it"
        )

def create_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE sources (
            path TEXT PRIMARY KEY,
            sha256 TEXT NOT NULL,
            indexed_at TEXT NOT NULL,
            chunk_count INTEGER NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE VIRTUAL TABLE chunks USING fts5(
            source_path UNINDEXED,
            source,
            source_hash UNINDEXED,
            page UNINDEXED,
            section,
            version UNINDEXED,
            date UNINDEXED,
            context,
            text,
            tokenize = 'unicode61'
        )
        """
    )
    connection.execute(f"PRAGMA application_id = {APPLICATION_ID}")
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

def schema_is_current(connection: sqlite3.Connection) -> bool:
    structure_is_current = (
        application_id(connection) == APPLICATION_ID
        and table_exists(connection, "chunks")
        and table_exists(connection, "sources")
        and table_exists(connection, "metadata")
        and metadata_columns(connection) == METADATA_COLUMNS
        and source_columns(connection) == SOURCE_COLUMNS
        and chunk_columns(connection) == CHUNK_COLUMNS
        and schema_version(connection) == SCHEMA_VERSION
        and connection.execute(
            "SELECT 1 FROM metadata WHERE key = 'corpus_root'"
        ).fetchone()
        is not None
    )
    if not structure_is_current:
        return False
    fingerprint = connection.execute(
        "SELECT value FROM metadata WHERE key = ?", (INDEX_FINGERPRINT_KEY,)
    ).fetchone()
    return fingerprint is not None and bool(SHA256.fullmatch(str(fingerprint["value"])))

def validate_corpus_binding(connection: sqlite3.Connection, corpus: Path) -> None:
    stored = connection.execute(
        "SELECT value FROM metadata WHERE key = 'corpus_root'"
    ).fetchone()
    if stored is None:
        raise ValueError("Index database has no corpus binding")
    if Path(stored["value"]).resolve() != corpus:
        raise ValueError(
            f"Index belongs to another corpus: {stored['value']}; choose a different database"
        )

def inventory_sources(
    corpus: Path,
    db_path: Path,
    max_source_bytes: int,
    max_corpus_bytes: int,
) -> tuple[list[SourceFile], int]:
    if max_source_bytes <= 0:
        raise ValueError("--max-source-bytes must be greater than zero")
    if max_corpus_bytes <= 0:
        raise ValueError("--max-corpus-bytes must be greater than zero")

    sources: list[SourceFile] = []
    total_bytes = 0
    for path in iter_source_files(corpus):
        if path.resolve() == db_path:
            continue
        relative_path = path.relative_to(corpus).as_posix()
        before = file_signature(path)
        size = before[2]
        if size > max_source_bytes:
            raise ValueError(
                f"Source exceeds --max-source-bytes ({size} > {max_source_bytes}): "
                f"{relative_path}"
            )
        total_bytes += size
        if total_bytes > max_corpus_bytes:
            raise ValueError(
                f"Corpus exceeds --max-corpus-bytes "
                f"({total_bytes} > {max_corpus_bytes})"
            )
        digest = sha256_file(path)
        after = file_signature(path)
        if after != before:
            raise ValueError(f"Source changed while it was hashed: {relative_path}; retry")
        sources.append(SourceFile(path, relative_path, size, after, digest))
    return sources, total_bytes

def verify_source_inventory(sources: Iterable[SourceFile]) -> None:
    for source in sources:
        if file_signature(source.path) != source.signature:
            raise ValueError(
                f"Source changed during indexing: {source.relative_path}; retry"
            )

def ensure_rebuild_space(db_path: Path, corpus_bytes: int) -> None:
    required = corpus_bytes + MIN_INDEX_HEADROOM_BYTES
    available = shutil.disk_usage(db_path.parent).free
    if available < required:
        raise ValueError(
            f"Insufficient free space for atomic index rebuild "
            f"({available} available, {required} required)"
        )

def require_current_schema(connection: sqlite3.Connection) -> None:
    require_index_owner(connection)
    if not schema_is_current(connection):
        raise ValueError(
            "Index database schema is unsupported or incomplete; use a new database "
            "path or remove this derived index before rebuilding"
        )

def calculate_index_fingerprint(connection: sqlite3.Connection) -> str:
    digest = hashlib.sha256()
    corpus = connection.execute(
        "SELECT value FROM metadata WHERE key = 'corpus_root'"
    ).fetchone()
    digest.update(f"schema:{SCHEMA_VERSION}\n".encode())
    digest.update(f"corpus:{corpus['value'] if corpus else ''}\n".encode())
    for row in connection.execute(
        "SELECT path, sha256, chunk_count FROM sources ORDER BY path"
    ):
        digest.update(
            json.dumps(
                [row["path"], row["sha256"], row["chunk_count"]],
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()

def store_index_fingerprint(connection: sqlite3.Connection) -> str:
    fingerprint = calculate_index_fingerprint(connection)
    connection.execute(
        """
        INSERT INTO metadata(key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """,
        (INDEX_FINGERPRINT_KEY, fingerprint),
    )
    return fingerprint

def index_fingerprint(connection: sqlite3.Connection) -> str:
    stored = connection.execute(
        "SELECT value FROM metadata WHERE key = ?", (INDEX_FINGERPRINT_KEY,)
    ).fetchone()
    if stored is None or not SHA256.fullmatch(str(stored["value"])):
        raise ValueError("Index fingerprint is missing or invalid")
    return str(stored["value"]).lower()

def resolve_index_binding(index_path: Path, corpus_root: Path) -> tuple[Path, str]:
    resolved = require_database(index_path)
    with database(resolved, readonly=True) as connection:
        require_current_schema(connection)
        stored = connection.execute(
            "SELECT value FROM metadata WHERE key = 'corpus_root'"
        ).fetchone()
        if stored is None or Path(stored["value"]).resolve() != corpus_root.resolve():
            raise ValueError("Index corpus does not match the research corpus")
        fingerprint = index_fingerprint(connection)
    return resolved, fingerprint

def command_index(args: argparse.Namespace) -> int:
    corpus = args.corpus.resolve()
    db_path = args.db.resolve()
    if not corpus.is_dir():
        raise ValueError(f"Corpus directory does not exist: {corpus}")
    if args.max_chars < 500:
        raise ValueError("--max-chars must be at least 500")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    sources, corpus_bytes = inventory_sources(
        corpus,
        db_path,
        args.max_source_bytes,
        args.max_corpus_bytes,
    )
    current_paths = {source.relative_path for source in sources}
    indexed = 0
    unchanged = 0
    removed = 0
    total_chunks = 0
    existing: dict[str, sqlite3.Row] = {}
    existing_connection: sqlite3.Connection | None = None
    database_existed = db_path.exists()
    temporary_path: Path | None = None
    update_strategy = "full-build"

    try:
        if database_existed:
            existing_connection = connect(db_path)
            require_current_schema(existing_connection)
            validate_corpus_binding(existing_connection, corpus)
            existing = {
                row["path"]: row
                for row in existing_connection.execute("SELECT * FROM sources")
            }

        if not sources and existing:
            raise ValueError(
                "Corpus contains no supported files; refusing to clear a non-empty index"
            )

        changed_paths = {
            source.relative_path
            for source in sources
            if not database_existed
            or source.relative_path not in existing
            or existing[source.relative_path]["sha256"] != source.sha256
        }
        stale_paths = set(existing) - current_paths if database_existed else set()
        removed = len(stale_paths)

        if database_existed and not changed_paths and not stale_paths:
            verify_source_inventory(sources)
            total_chunks = sum(int(row["chunk_count"]) for row in existing.values())
            unchanged = len(sources)
            if existing_connection is not None:
                existing_connection.close()
                existing_connection = None
            permissions_hardened = harden_database_permissions(db_path)
            emit_json(
                {
                    "corpus": str(corpus),
                    "database": str(db_path),
                    "files_seen": len(sources),
                    "files_indexed": 0,
                    "files_unchanged": unchanged,
                    "files_removed": 0,
                    "corpus_bytes": corpus_bytes,
                    "chunks": total_chunks,
                    "database_rebuilt": False,
                    "update_strategy": "none",
                    "permissions_hardened": permissions_hardened,
                }
            )
            return 0

        changed_sources = [
            source for source in sources if source.relative_path in changed_paths
        ]
        if database_existed:
            update_strategy = "delta-copy"
            # The temporary database starts as a page-level snapshot of the old
            # index. Budget for that copy plus new input; deleted/changed pages can
            # then be reused by SQLite while the delta is applied.
            working_bytes = db_path.stat().st_size + sum(
                source.size for source in changed_sources
            )
        else:
            working_bytes = corpus_bytes
        ensure_rebuild_space(db_path, working_bytes)
        with tempfile.NamedTemporaryFile(
            prefix=f".{db_path.name}.",
            suffix=".tmp",
            dir=db_path.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)

        new_connection = connect(temporary_path)
        try:
            if database_existed:
                if existing_connection is None:
                    raise RuntimeError("Current index connection is unavailable")
                existing_connection.backup(new_connection)
                require_current_schema(new_connection)

            # This database is a disposable working copy until os.replace below.
            # Avoid a second on-disk rollback copy; any failed update discards the
            # temporary database and leaves the published index untouched.
            journal_mode = str(
                new_connection.execute("PRAGMA journal_mode = OFF").fetchone()[0]
            ).lower()
            if journal_mode != "off":
                raise RuntimeError("Could not configure temporary index journal mode")

            with new_connection:
                if database_existed:
                    affected_paths = sorted(changed_paths | stale_paths)
                    new_connection.execute("PRAGMA secure_delete = ON")
                    # FTS5 cannot index an UNINDEXED source_path column. Resolve
                    # affected rowids with one scan instead of rescanning the whole
                    # virtual table once per changed source.
                    new_connection.execute(
                        "CREATE TEMP TABLE affected_sources(path TEXT PRIMARY KEY) WITHOUT ROWID"
                    )
                    new_connection.executemany(
                        "INSERT INTO affected_sources(path) VALUES (?)",
                        ((path,) for path in affected_paths),
                    )
                    new_connection.execute(
                        """
                        CREATE TEMP TABLE affected_chunk_rows(rowid INTEGER PRIMARY KEY)
                        """
                    )
                    new_connection.execute(
                        """
                        INSERT INTO affected_chunk_rows(rowid)
                        SELECT chunks.rowid
                        FROM chunks
                        JOIN affected_sources
                          ON affected_sources.path = chunks.source_path
                        """
                    )
                    new_connection.execute(
                        "DELETE FROM chunks WHERE rowid IN "
                        "(SELECT rowid FROM affected_chunk_rows)"
                    )
                    new_connection.execute(
                        "DELETE FROM sources WHERE path IN "
                        "(SELECT path FROM affected_sources)"
                    )
                    unchanged = len(sources) - len(changed_sources)
                else:
                    create_schema(new_connection)
                    new_connection.execute(
                        "INSERT INTO metadata(key, value) VALUES ('corpus_root', ?)",
                        (str(corpus),),
                    )

                for source in changed_sources:
                    if source.path.suffix.lower() == ".jsonl":
                        chunks = chunks_from_jsonl(
                            source.path,
                            source.relative_path,
                            source.sha256,
                            args.max_chars,
                        )
                    else:
                        chunks = chunks_from_text(
                            source.path,
                            source.relative_path,
                            source.sha256,
                            args.max_chars,
                        )
                    chunk_count = 0

                    def parsed_rows() -> Iterator[tuple[object, ...]]:
                        nonlocal chunk_count
                        for chunk in chunks:
                            chunk_count += 1
                            yield (
                                source.relative_path,
                                chunk.source,
                                chunk.source_hash,
                                chunk.page,
                                chunk.section,
                                chunk.version,
                                chunk.date,
                                chunk.context,
                                chunk.text,
                            )

                    new_connection.executemany(
                        """
                        INSERT INTO chunks(
                            source_path, source, source_hash, page, section,
                            version, date, context, text
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        parsed_rows(),
                    )
                    new_connection.execute(
                        """
                        INSERT INTO sources(path, sha256, indexed_at, chunk_count)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            source.relative_path,
                            source.sha256,
                            dt.datetime.now(dt.timezone.utc).isoformat(),
                            chunk_count,
                        ),
                    )
                    indexed += 1

                verify_source_inventory(sources)
                total_chunks = int(
                    new_connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
                )
                store_index_fingerprint(new_connection)

            restored_journal_mode = str(
                new_connection.execute("PRAGMA journal_mode = DELETE").fetchone()[0]
            ).lower()
            if restored_journal_mode != "delete":
                raise RuntimeError("Could not finalize temporary index journal mode")
        finally:
            new_connection.close()

        if existing_connection is not None:
            existing_connection.close()
            existing_connection = None
        temporary_path.replace(db_path)
        temporary_path = None
        permissions_hardened = harden_database_permissions(db_path)
    finally:
        if existing_connection is not None:
            existing_connection.close()
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    emit_json(
        {
            "corpus": str(corpus),
            "database": str(db_path),
            "files_seen": len(sources),
            "files_indexed": indexed,
            "files_unchanged": unchanged,
            "files_removed": removed,
            "corpus_bytes": corpus_bytes,
            "chunks": total_chunks,
            "database_rebuilt": True,
            "update_strategy": update_strategy,
            "permissions_hardened": permissions_hardened,
        }
    )
    return 0

def command_info(args: argparse.Namespace) -> int:
    db_path = require_database(args.db)
    if not 1 <= args.source_limit <= 100:
        raise ValueError("--source-limit must be between 1 and 100")
    if args.offset < 0:
        raise ValueError("--offset must be zero or greater")
    if not 1 <= args.metadata_limit <= 50:
        raise ValueError("--metadata-limit must be between 1 and 50")

    with database(db_path, readonly=True) as connection:
        require_current_schema(connection)
        corpus_row = connection.execute(
            "SELECT value FROM metadata WHERE key = 'corpus_root'"
        ).fetchone()
        source_count = int(connection.execute("SELECT COUNT(*) FROM sources").fetchone()[0])
        chunk_count = int(connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])
        indexed_range = connection.execute(
            "SELECT MIN(indexed_at) AS earliest, MAX(indexed_at) AS latest FROM sources"
        ).fetchone()
        metadata_counts = connection.execute(
            """
            SELECT COUNT(DISTINCT version) AS versions,
                   COUNT(DISTINCT date) AS dates
            FROM chunks
            """
        ).fetchone()
        source_columns_sql = "path, chunk_count"
        if args.hashes:
            source_columns_sql += ", sha256"
        rows = connection.execute(
            f"""
            SELECT {source_columns_sql}
            FROM sources
            ORDER BY path
            LIMIT ? OFFSET ?
            """,
            (args.source_limit + 1, args.offset),
        ).fetchall()
        metadata_summary: dict[str, object] | None = None
        if args.metadata_summary:
            grouped: dict[str, list[dict[str, object]]] = {}
            for column in ("version", "date", "section"):
                grouped[column + "s"] = [
                    dict(row)
                    for row in connection.execute(
                        f"""
                        SELECT {column} AS value, COUNT(*) AS chunks,
                               COUNT(DISTINCT source_path) AS sources
                        FROM chunks
                        WHERE {column} IS NOT NULL AND TRIM({column}) != ''
                        GROUP BY {column}
                        ORDER BY chunks DESC, value
                        LIMIT ?
                        """,
                        (args.metadata_limit,),
                    )
                ]
            coverage = connection.execute(
                """
                SELECT
                    SUM(CASE WHEN version IS NOT NULL AND TRIM(version) != '' THEN 1 ELSE 0 END)
                        AS version_chunks,
                    SUM(CASE WHEN date IS NOT NULL AND TRIM(date) != '' THEN 1 ELSE 0 END)
                        AS date_chunks,
                    SUM(CASE WHEN section IS NOT NULL AND TRIM(section) != '' THEN 1 ELSE 0 END)
                        AS section_chunks,
                    SUM(CASE WHEN page IS NOT NULL AND TRIM(page) != '' THEN 1 ELSE 0 END)
                        AS page_chunks
                FROM chunks
                """
            ).fetchone()
            metadata_summary = {
                **grouped,
                "chunk_coverage": {
                    key: int(coverage[key] or 0)
                    for key in (
                        "version_chunks",
                        "date_chunks",
                        "section_chunks",
                        "page_chunks",
                    )
                },
                "limit_per_field": args.metadata_limit,
            }

    selected = rows[: args.source_limit]
    has_more = len(rows) > len(selected)
    payload: dict[str, object] = {
        "database": str(db_path),
        "corpus": corpus_row["value"] if corpus_row is not None else None,
        "schema_version": SCHEMA_VERSION,
        "source_count": source_count,
        "chunk_count": chunk_count,
        "indexed_at": {
            "earliest": indexed_range["earliest"],
            "latest": indexed_range["latest"],
        },
        "metadata_values": {
            "versions": int(metadata_counts["versions"]),
            "dates": int(metadata_counts["dates"]),
        },
        "offset": args.offset,
        "result_count": len(selected),
        "has_more": has_more,
        "sources": [dict(row) for row in selected],
    }
    if has_more:
        payload["next_offset"] = args.offset + len(selected)
    if metadata_summary is not None:
        payload["metadata_summary"] = metadata_summary
    emit_json(payload, args.pretty)
    return 0

def literal_query(query: str) -> str:
    tokens = TOKEN.findall(query)
    if not tokens:
        raise ValueError("Literal query contains no searchable words")
    return " AND ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens)

def prefix_query(query: str) -> str:
    tokens = TOKEN.findall(query)
    if not tokens:
        raise ValueError("Prefix query contains no searchable words")
    return " AND ".join(f'"{token.replace(chr(34), chr(34) * 2)}"*' for token in tokens)

def like_contains(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"

def result_item(
    row: sqlite3.Row,
    text: str,
    *,
    text_truncated: bool = False,
    text_start_char: int = 0,
) -> dict[str, object]:
    score = row["score"] if "score" in row.keys() else None
    if isinstance(score, float):
        score = round(score, 6)
    item: dict[str, object] = {
        "passage_id": row["passage_id"],
        "source": row["source"],
        "source_hash": row["source_hash"],
        "text": text,
    }
    if row["source_path"] != row["source"]:
        item["source_path"] = row["source_path"]
    if score is not None:
        item["score"] = score
    for key in ("page", "section", "version", "date"):
        if row[key] is not None:
            item[key] = row[key]
    if text_start_char:
        item["text_start_char"] = text_start_char
    if text_truncated:
        item["text_truncated"] = True
    return item

def bounded_rows(
    rows: Iterable[sqlite3.Row], per_result: int, total_limit: int
) -> tuple[list[dict[str, object]], int, bool]:
    output: list[dict[str, object]] = []
    used = 0
    truncated = False
    for row in rows:
        remaining = total_limit - used
        if remaining < 2:
            truncated = True
            break
        text = str(row["text"] or "")
        allowed = min(per_result, remaining)
        clipped, text_truncated = clip_text(text, allowed)
        truncated = truncated or text_truncated
        used += len(clipped)
        output.append(result_item(row, clipped, text_truncated=text_truncated))
    return output, used, truncated

def search_row_locator(row: sqlite3.Row) -> dict[str, object]:
    return {
        key: row[key]
        for key in (
            "passage_id",
            "source",
            "source_path",
            "source_hash",
            "page",
            "section",
            "version",
            "date",
        )
        if row[key] is not None
    }

def select_search_rows(
    rows: list[sqlite3.Row],
    limit: int,
    dedupe_exact: bool,
    max_per_source: int,
    candidate_limit: int,
) -> tuple[
    list[sqlite3.Row],
    list[int],
    dict[int, list[dict[str, object]]],
    bool,
    int,
]:
    selected: list[sqlite3.Row] = []
    positions: list[int] = []
    duplicates: dict[int, list[dict[str, object]]] = {}
    seen_text: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    extra_selected = False

    for position, row in enumerate(rows[:candidate_limit]):
        if dedupe_exact:
            text_key = hashlib.sha256(
                normalize_text(str(row["full_text"] or "")).encode("utf-8")
            ).hexdigest()
            existing_index = seen_text.get(text_key)
            if existing_index is not None:
                aliases = duplicates.setdefault(existing_index, [])
                if len(aliases) < 5:
                    aliases.append(search_row_locator(row))
                continue
        else:
            text_key = ""

        source_key = str(row["source"] or row["source_path"])
        if max_per_source and source_counts.get(source_key, 0) >= max_per_source:
            continue
        source_counts[source_key] = source_counts.get(source_key, 0) + 1
        if dedupe_exact:
            seen_text[text_key] = len(selected)
        selected.append(row)
        positions.append(position)
        if len(selected) > limit:
            extra_selected = True
            break

    more_raw = len(rows) > candidate_limit
    has_more = extra_selected or more_raw
    if extra_selected and positions:
        next_advance = positions[min(limit, len(positions)) - 1] + 1
    elif more_raw:
        next_advance = candidate_limit
    elif positions:
        next_advance = positions[-1] + 1
    else:
        next_advance = candidate_limit if more_raw else 0
    return selected[:limit], positions[:limit], duplicates, has_more, next_advance

def require_database(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_file():
        raise ValueError(f"Index database does not exist: {resolved}")
    return resolved

def get_payload(args: argparse.Namespace) -> dict[str, object]:
    db_path = require_database(args.db)
    unique_ids = list(dict.fromkeys(args.passage_ids))
    if len(unique_ids) > 50:
        raise ValueError("At most 50 passage IDs may be requested")
    if not 1 <= args.limit <= 50:
        raise ValueError("--limit must be between 1 and 50")
    if args.offset < 0:
        raise ValueError("--offset must be zero or greater")
    if args.start_char < 0:
        raise ValueError("--start-char must be zero or greater")
    if not 100 <= args.max_chars <= 8000:
        raise ValueError("--max-chars must be between 100 and 8000")
    if not 100 <= args.max_total_chars <= 100000:
        raise ValueError("--max-total-chars must be between 100 and 100000")

    placeholders = ",".join("?" for _ in unique_ids)
    sql = f"""
        SELECT rowid AS passage_id, source_path, source, source_hash,
               page, section, version, date, text
        FROM chunks
        WHERE rowid IN ({placeholders})
    """
    with database(db_path, readonly=True) as connection:
        require_current_schema(connection)
        rows = connection.execute(sql, unique_ids).fetchall()
    by_id = {row["passage_id"]: row for row in rows}
    ordered = [by_id[passage_id] for passage_id in unique_ids if passage_id in by_id]
    if args.offset < len(ordered) and args.start_char > len(ordered[args.offset]["text"]):
        raise ValueError("--start-char exceeds the selected passage length")

    results: list[dict[str, object]] = []
    characters = 0
    current_offset = args.offset
    current_start = args.start_char
    next_offset: int | None = None
    next_start_char = 0

    while current_offset < len(ordered) and len(results) < args.limit:
        remaining_budget = args.max_total_chars - characters
        if remaining_budget < 2:
            next_offset = current_offset
            next_start_char = current_start
            break

        row = ordered[current_offset]
        full_text = str(row["text"] or "")
        remaining_text = full_text[current_start:]
        allowed = min(args.max_chars, remaining_budget)
        text_truncated = len(remaining_text) > allowed
        visible_chars = allowed - 1 if text_truncated else len(remaining_text)
        clipped = (
            remaining_text[:visible_chars] + "…"
            if text_truncated
            else remaining_text
        )
        results.append(
            result_item(
                row,
                clipped,
                text_truncated=text_truncated,
                text_start_char=current_start,
            )
        )
        characters += len(clipped)

        if text_truncated:
            next_offset = current_offset
            next_start_char = current_start + visible_chars
            break

        current_offset += 1
        current_start = 0

    if next_offset is None and current_offset < len(ordered):
        next_offset = current_offset
    has_more = next_offset is not None
    payload: dict[str, object] = {
        "offset": args.offset,
        "start_char": args.start_char,
        "result_count": len(results),
        "characters": characters,
        "has_more": has_more,
        "not_found": [passage_id for passage_id in unique_ids if passage_id not in by_id],
        "results": results,
    }
    if has_more:
        payload["next_offset"] = next_offset
        payload["next_start_char"] = next_start_char
    return payload

def command_get(args: argparse.Namespace) -> int:
    emit_json(get_payload(args), args.pretty)
    return 0
