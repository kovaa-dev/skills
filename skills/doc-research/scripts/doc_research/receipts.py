from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

from .common import RECEIPT_APPLICATION_ID, RECEIPT_SCHEMA_VERSION, application_id, connect, database, database_objects, emit_json, harden_database_permissions, schema_version, table_columns, table_exists, utc_now, validate_record_id
from .index import resolve_index_binding
from .common import HANDLED_ERRORS, sqlite3

RECEIPT_COLUMNS = {
    "receipt_state": (
        "singleton",
        "corpus_root",
        "index_path",
        "index_fingerprint",
        "created_at",
        "updated_at",
    ),
    "search_receipts": (
        "receipt_id",
        "query",
        "mode",
        "filters_json",
        "outcome",
        "result_refs_json",
        "next_offset",
        "next_start_char",
        "index_fingerprint",
        "created_at",
        "updated_at",
        "last_used_at",
    ),
}

def require_receipt_owner(connection: sqlite3.Connection) -> None:
    identifier = application_id(connection)
    if identifier == RECEIPT_APPLICATION_ID:
        return
    if identifier != 0:
        raise ValueError("Database belongs to another application; refusing to use it")
    if database_objects(connection):
        raise ValueError(
            "Existing database is not a receipt store with this tool's application "
            "identifier; refusing to use it"
        )

def receipt_schema_is_current(connection: sqlite3.Connection) -> bool:
    return (
        application_id(connection) == RECEIPT_APPLICATION_ID
        and schema_version(connection) == RECEIPT_SCHEMA_VERSION
        and all(
            table_exists(connection, table)
            and table_columns(connection, table) == columns
            for table, columns in RECEIPT_COLUMNS.items()
        )
    )

def require_receipt_schema(connection: sqlite3.Connection) -> None:
    require_receipt_owner(connection)
    if not receipt_schema_is_current(connection):
        raise ValueError("Receipt database schema is unsupported or incomplete")

def create_receipt_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE receipt_state (
            singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
            corpus_root TEXT NOT NULL,
            index_path TEXT NOT NULL,
            index_fingerprint TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE search_receipts (
            receipt_id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            mode TEXT NOT NULL CHECK (mode IN ('literal', 'prefix', 'fts', 'external')),
            filters_json TEXT NOT NULL,
            outcome TEXT NOT NULL CHECK (
                outcome IN ('results', 'no-material-result', 'incomplete')
            ),
            result_refs_json TEXT NOT NULL,
            next_offset INTEGER,
            next_start_char INTEGER,
            index_fingerprint TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_used_at TEXT NOT NULL,
            CHECK (next_offset IS NULL OR next_offset >= 0),
            CHECK (next_start_char IS NULL OR next_start_char >= 0)
        );
        CREATE INDEX search_receipts_fingerprint ON search_receipts(index_fingerprint);
        """
    )
    connection.execute(f"PRAGMA application_id = {RECEIPT_APPLICATION_ID}")
    connection.execute(f"PRAGMA user_version = {RECEIPT_SCHEMA_VERSION}")

def require_receipt_database(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_file():
        raise ValueError(f"Receipt database does not exist: {resolved}")
    return resolved

def receipt_store_status(db_path: Path) -> dict[str, object]:
    with database(db_path, readonly=True) as connection:
        require_receipt_schema(connection)
        stored_schema_version = schema_version(connection)
        state = connection.execute(
            "SELECT * FROM receipt_state WHERE singleton = 1"
        ).fetchone()
        if state is None:
            raise ValueError("Receipt database has no state row")
        values = dict(state)
    index_available = True
    index_stale = False
    index_error: str | None = None
    current_fingerprint: str | None = None
    try:
        _, current_fingerprint = resolve_index_binding(
            Path(values["index_path"]), Path(values["corpus_root"])
        )
        index_stale = current_fingerprint != values["index_fingerprint"]
    except HANDLED_ERRORS as exc:
        index_available = False
        index_stale = True
        index_error = str(exc)
    with database(db_path, readonly=True) as connection:
        require_receipt_schema(connection)
        total_count = int(connection.execute("SELECT COUNT(*) FROM search_receipts").fetchone()[0])
        if current_fingerprint is None:
            current_count = 0
            stale_count = total_count
        else:
            current_count = int(
                connection.execute(
                    "SELECT COUNT(*) FROM search_receipts WHERE index_fingerprint = ?",
                    (current_fingerprint,),
                ).fetchone()[0]
            )
            stale_count = total_count - current_count
    payload: dict[str, object] = {
        "database": str(db_path),
        "schema_version": stored_schema_version,
        "corpus": values["corpus_root"],
        "index_path": values["index_path"],
        "index_fingerprint": values["index_fingerprint"],
        "current_index_fingerprint": current_fingerprint,
        "index_available": index_available,
        "index_stale": index_stale,
        "current_receipts": current_count,
        "stale_receipts": stale_count,
        "created_at": values["created_at"],
        "updated_at": values["updated_at"],
        "database_bytes": db_path.stat().st_size,
    }
    if index_error:
        payload["index_error"] = index_error
    return payload

def initialize_receipt_store(
    db: Path, corpus: Path, index: Path
) -> dict[str, object]:
    db_path = db.resolve()
    corpus_root = corpus.resolve()
    if not corpus_root.is_dir() and not corpus_root.is_file():
        raise ValueError(f"Corpus path does not exist: {corpus_root}")
    if db_path.exists():
        with database(db_path, readonly=True) as connection:
            require_receipt_owner(connection)
        raise ValueError(f"Receipt database already exists: {db_path}")
    index_path, fingerprint = resolve_index_binding(index, corpus_root)
    if index_path == db_path:
        raise ValueError("Receipt database and index database must be separate files")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{db_path.name}.", suffix=".tmp", dir=db_path.parent, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
        connection = connect(temporary_path)
        try:
            with connection:
                create_receipt_schema(connection)
                now = utc_now()
                connection.execute(
                    """
                    INSERT INTO receipt_state(
                        singleton, corpus_root, index_path, index_fingerprint,
                        created_at, updated_at
                    ) VALUES (1, ?, ?, ?, ?, ?)
                    """,
                    (str(corpus_root), str(index_path), fingerprint, now, now),
                )
        finally:
            connection.close()
        harden_database_permissions(temporary_path)
        try:
            os.link(temporary_path, db_path)
        except FileExistsError as exc:
            raise ValueError(f"Receipt database already exists: {db_path}") from exc
        temporary_path.unlink()
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    return receipt_store_status(db_path)


def command_receipts_init(args: argparse.Namespace) -> int:
    emit_json(
        initialize_receipt_store(args.db, args.corpus, args.index),
        args.pretty,
    )
    return 0

def command_receipts_info(args: argparse.Namespace) -> int:
    db_path = require_receipt_database(args.db)
    emit_json(receipt_store_status(db_path), args.pretty)
    return 0

def command_receipts_sync(args: argparse.Namespace) -> int:
    db_path = require_receipt_database(args.db)
    with database(db_path) as connection:
        require_receipt_schema(connection)
        state = connection.execute(
            "SELECT * FROM receipt_state WHERE singleton = 1"
        ).fetchone()
        if state is None:
            raise ValueError("Receipt database has no state row")
        selected_index = args.index or Path(state["index_path"])
        index_path, fingerprint = resolve_index_binding(
            selected_index, Path(state["corpus_root"])
        )
        changed = (
            str(index_path) != state["index_path"]
            or fingerprint != state["index_fingerprint"]
        )
        now = utc_now()
        connection.execute(
            """
            UPDATE receipt_state
            SET index_path = ?, index_fingerprint = ?, updated_at = ?
            WHERE singleton = 1
            """,
            (str(index_path), fingerprint, now),
        )
        stale_count = int(
            connection.execute(
                "SELECT COUNT(*) FROM search_receipts WHERE index_fingerprint != ?",
                (fingerprint,),
            ).fetchone()[0]
        )
    harden_database_permissions(db_path)
    emit_json(
        {
            "database": str(db_path),
            "index": str(index_path),
            "index_fingerprint": fingerprint,
            "changed": changed,
            "stale_receipts": stale_count,
        },
        args.pretty,
    )
    return 0

def receipt_cache_id(
    query: str, mode: str, filters: dict[str, object], offset: int
) -> str:
    identity = json.dumps(
        [query, mode, filters, offset],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"Q-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:20]}"

def receipt_references(results: object) -> list[dict[str, object]]:
    if not isinstance(results, list):
        raise ValueError("Search results are not a list")
    references: list[dict[str, object]] = []
    for result in results:
        if not isinstance(result, dict):
            continue
        reference = {
            key: result[key]
            for key in (
                "source",
                "source_path",
                "source_hash",
                "page",
                "section",
                "version",
                "date",
                "passage_id",
            )
            if result.get(key) is not None
        }
        aliases = result.get("also_in")
        if isinstance(aliases, list):
            reference["also_in"] = aliases[:5]
        if reference.get("source") is not None:
            references.append(reference)
    return references

def search_outcome(payload: dict[str, object]) -> str:
    if payload["has_more"]:
        return "incomplete"
    if payload["result_count"]:
        return "results"
    return "no-material-result"

def validate_receipt_store_connection(
    connection: sqlite3.Connection, index_db: Path, corpus_root: Path
) -> sqlite3.Row:
    require_receipt_schema(connection)
    state = connection.execute(
        "SELECT * FROM receipt_state WHERE singleton = 1"
    ).fetchone()
    if state is None:
        raise ValueError("Receipt database has no state row")
    if Path(state["corpus_root"]).resolve() != corpus_root.resolve():
        raise ValueError("Receipt database corpus does not match the search index")
    if Path(state["index_path"]).resolve() != index_db.resolve():
        raise ValueError("Receipt database uses another index; run receipts-sync --index")
    return state

def lookup_cached_receipt(
    receipt_db: Path,
    index_db: Path,
    corpus_root: Path,
    fingerprint: str,
    receipt_id: str,
    expected_query: str,
    expected_mode: str,
    expected_filters: dict[str, object],
) -> dict[str, object] | None:
    store_path = require_receipt_database(receipt_db)
    with database(store_path, readonly=True) as connection:
        validate_receipt_store_connection(connection, index_db, corpus_root)
        row = connection.execute(
            "SELECT * FROM search_receipts WHERE receipt_id = ?",
            (receipt_id,),
        ).fetchone()
        if row is None or row["index_fingerprint"] != fingerprint:
            return None
        stored_filters = json.loads(str(row["filters_json"]))
        if (
            row["query"] != expected_query
            or row["mode"] != expected_mode
            or stored_filters != expected_filters
        ):
            raise ValueError(
                "Receipt ID belongs to different search parameters; "
                "choose another ID"
            )
        item = dict(row)
    item["filters"] = json.loads(str(item.pop("filters_json")))
    item["result_refs"] = json.loads(str(item.pop("result_refs_json")))
    item["current"] = True
    return item

def save_cached_receipt(
    receipt_db: Path,
    index_db: Path,
    corpus_root: Path,
    fingerprint: str,
    receipt_id: str,
    payload: dict[str, object],
) -> str:
    store_path = require_receipt_database(receipt_db)
    references = receipt_references(payload["results"])
    now = utc_now()
    with database(store_path) as connection:
        validate_receipt_store_connection(connection, index_db, corpus_root)
        encoded_filters = json.dumps(
            payload["filters"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        existing = connection.execute(
            "SELECT query, mode, filters_json FROM search_receipts WHERE receipt_id = ?",
            (receipt_id,),
        ).fetchone()
        if existing is not None and (
            existing["query"] != payload["query"]
            or existing["mode"] != payload["mode"]
            or existing["filters_json"] != encoded_filters
        ):
            raise ValueError("Receipt ID belongs to different search parameters; choose another ID")
        connection.execute(
            """
            INSERT INTO search_receipts(
                receipt_id, query, mode, filters_json, outcome,
                result_refs_json, next_offset, next_start_char,
                index_fingerprint, created_at, updated_at, last_used_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?)
            ON CONFLICT(receipt_id) DO UPDATE SET
                query = excluded.query,
                mode = excluded.mode,
                filters_json = excluded.filters_json,
                outcome = excluded.outcome,
                result_refs_json = excluded.result_refs_json,
                next_offset = excluded.next_offset,
                next_start_char = NULL,
                index_fingerprint = excluded.index_fingerprint,
                updated_at = excluded.updated_at,
                last_used_at = excluded.last_used_at
            """,
            (
                receipt_id,
                payload["query"],
                payload["mode"],
                encoded_filters,
                search_outcome(payload),
                json.dumps(
                    references,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                payload.get("next_offset"),
                fingerprint,
                now,
                now,
                now,
            ),
        )
        connection.execute(
            """
            UPDATE receipt_state
            SET index_fingerprint = ?, updated_at = ?
            WHERE singleton = 1
            """,
            (fingerprint, now),
        )
    harden_database_permissions(store_path)
    return receipt_id

def receipt_list_item(
    row: sqlite3.Row, current_fingerprint: str | None, details: bool
) -> dict[str, object]:
    stored_filters = json.loads(row["filters_json"])
    filters = {
        key: value for key, value in stored_filters.items() if not key.startswith("_")
    }
    search_options = {
        key.removeprefix("_"): value
        for key, value in stored_filters.items()
        if key.startswith("_")
    }
    item: dict[str, object] = {
        "receipt_id": row["receipt_id"],
        "query": row["query"],
        "mode": row["mode"],
        "filters": filters,
        "outcome": row["outcome"],
        "next_offset": row["next_offset"],
        "next_start_char": row["next_start_char"],
        "index_fingerprint": row["index_fingerprint"],
        "current": (
            current_fingerprint is not None
            and row["index_fingerprint"] == current_fingerprint
        ),
        "updated_at": row["updated_at"],
        "last_used_at": row["last_used_at"],
    }
    if search_options:
        item["search_options"] = search_options
    references = json.loads(row["result_refs_json"])
    item["result_count"] = len(references)
    if details:
        item["result_refs"] = references
    return item

def command_receipts_list(args: argparse.Namespace) -> int:
    db_path = require_receipt_database(args.db)
    if not 1 <= args.limit <= 100:
        raise ValueError("--limit must be between 1 and 100")
    if args.offset < 0:
        raise ValueError("--offset must be zero or greater")
    if not 1_000 <= args.max_total_chars <= 100_000:
        raise ValueError("--max-total-chars must be between 1000 and 100000")
    with database(db_path, readonly=True) as connection:
        require_receipt_schema(connection)
        state = connection.execute(
            "SELECT corpus_root, index_path, index_fingerprint "
            "FROM receipt_state WHERE singleton = 1"
        ).fetchone()
        if state is None:
            raise ValueError("Receipt database has no state row")
        try:
            _, live_fingerprint = resolve_index_binding(
                Path(state["index_path"]), Path(state["corpus_root"])
            )
        except HANDLED_ERRORS:
            live_fingerprint = None
        conditions: list[str] = []
        parameters: list[object] = []
        if not args.include_stale:
            if live_fingerprint is None:
                conditions.append("0 = 1")
            else:
                conditions.append("index_fingerprint = ?")
                parameters.append(live_fingerprint)
        if args.receipt_id:
            conditions.append("receipt_id = ?")
            parameters.append(validate_record_id(args.receipt_id, "--receipt-id"))
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        parameters.extend((args.limit + 1, args.offset))
        rows = connection.execute(
            f"""
            SELECT * FROM search_receipts {where}
            ORDER BY last_used_at DESC, receipt_id
            LIMIT ? OFFSET ?
            """,
            parameters,
        ).fetchall()
        current_fingerprint = live_fingerprint

    records: list[dict[str, object]] = []
    characters = 0
    for row in rows[: args.limit]:
        item = receipt_list_item(row, current_fingerprint, args.details)
        encoded = json.dumps(item, ensure_ascii=False, separators=(",", ":"))
        if records and characters + len(encoded) > args.max_total_chars:
            break
        if not records and len(encoded) > args.max_total_chars:
            raise ValueError("--max-total-chars is too small for one receipt")
        records.append(item)
        characters += len(encoded)
    has_more = len(rows) > len(records)
    payload: dict[str, object] = {
        "database": str(db_path),
        "offset": args.offset,
        "result_count": len(records),
        "characters": characters,
        "has_more": has_more,
        "records": records,
    }
    if has_more:
        payload["next_offset"] = args.offset + len(records)
    emit_json(payload, args.pretty)
    return 0
