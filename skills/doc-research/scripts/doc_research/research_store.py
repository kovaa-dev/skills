from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from .catalog_store import (
    catalog_snapshot,
    project_scope_corpus_ids,
    require_catalog_database,
    require_catalog_schema,
)
from .common import (
    HANDLED_ERRORS,
    MAX_CATALOG_CORPORA,
    MAX_RESEARCH_JSON,
    RECORD_ID,
    RESEARCH_APPLICATION_ID,
    RESEARCH_SCHEMA_VERSION,
    RESEARCH_STATUSES,
    application_id,
    clip_text,
    connect,
    database,
    database_objects,
    emit_json,
    harden_database_permissions,
    optional_research_text,
    required_research_text,
    schema_version,
    sqlite3,
    table_columns,
    table_exists,
    utc_now,
    validate_record_id,
)
from .index import resolve_index_binding
from .receipts import require_receipt_database, require_receipt_schema

RESEARCH_COLUMNS = {
    "research_state": (
        "singleton",
        "scope",
        "status",
        "binding_kind",
        "corpus_root",
        "index_path",
        "index_fingerprint",
        "catalog_path",
        "catalog_fingerprint",
        "catalog_scope_json",
        "next_action",
        "created_at",
        "updated_at",
    ),
    "facets": ("facet_id", "question", "status", "next_action", "updated_at"),
    "evidence": (
        "evidence_id",
        "facet_id",
        "corpus_id",
        "finding",
        "source",
        "source_version",
        "source_hash",
        "page",
        "section",
        "passage_id",
        "excerpt",
        "interpretation",
        "confidence",
        "verified",
        "updated_at",
    ),
    "gaps": (
        "gap_id",
        "facet_id",
        "description",
        "status",
        "reason",
        "next_query",
        "updated_at",
    ),
    "conflicts": (
        "conflict_id",
        "facet_id",
        "evidence_ids_json",
        "description",
        "status",
        "resolution",
        "updated_at",
    ),
    "receipt_links": (
        "facet_id",
        "store_kind",
        "store_path",
        "receipt_id",
        "linked_at",
    ),
}

def require_research_owner(connection: sqlite3.Connection) -> None:
    identifier = application_id(connection)
    if identifier == RESEARCH_APPLICATION_ID:
        return
    if identifier != 0:
        raise ValueError("Database belongs to another application; refusing to use it")
    if database_objects(connection):
        raise ValueError(
            "Existing database is not a research state with this tool's application "
            "identifier; refusing to use it"
        )

def research_schema_is_current(connection: sqlite3.Connection) -> bool:
    return (
        application_id(connection) == RESEARCH_APPLICATION_ID
        and schema_version(connection) == RESEARCH_SCHEMA_VERSION
        and all(
            table_exists(connection, table)
            and table_columns(connection, table) == columns
            for table, columns in RESEARCH_COLUMNS.items()
        )
    )

def require_research_schema(connection: sqlite3.Connection) -> None:
    require_research_owner(connection)
    if not research_schema_is_current(connection):
        raise ValueError("Research database schema is unsupported or incomplete")

def create_research_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE research_state (
            singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
            scope TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('active', 'complete')),
            binding_kind TEXT NOT NULL CHECK (binding_kind IN ('corpus', 'catalog')),
            corpus_root TEXT,
            index_path TEXT,
            index_fingerprint TEXT,
            catalog_path TEXT,
            catalog_fingerprint TEXT,
            catalog_scope_json TEXT,
            next_action TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            CHECK (
                (binding_kind = 'corpus' AND corpus_root IS NOT NULL
                    AND catalog_path IS NULL AND catalog_fingerprint IS NULL
                    AND catalog_scope_json IS NULL)
                OR (binding_kind = 'catalog' AND corpus_root IS NULL
                    AND index_path IS NULL AND index_fingerprint IS NULL
                    AND catalog_path IS NOT NULL AND catalog_fingerprint IS NOT NULL
                    AND catalog_scope_json IS NOT NULL)
            )
        );
        CREATE TABLE facets (
            facet_id TEXT PRIMARY KEY,
            question TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN (
                'open', 'supported', 'refuted', 'conflicted', 'unresolved', 'out-of-scope'
            )),
            next_action TEXT,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE evidence (
            evidence_id TEXT PRIMARY KEY,
            facet_id TEXT NOT NULL REFERENCES facets(facet_id) ON DELETE CASCADE,
            corpus_id TEXT,
            finding TEXT NOT NULL,
            source TEXT NOT NULL,
            source_version TEXT,
            source_hash TEXT,
            page TEXT,
            section TEXT,
            passage_id INTEGER,
            excerpt TEXT,
            interpretation TEXT,
            confidence TEXT CHECK (
                confidence IS NULL OR confidence IN ('confirmed', 'probable', 'uncertain')
            ),
            verified INTEGER NOT NULL CHECK (verified IN (0, 1)),
            updated_at TEXT NOT NULL
        );
        CREATE TABLE gaps (
            gap_id TEXT PRIMARY KEY,
            facet_id TEXT NOT NULL REFERENCES facets(facet_id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('open', 'resolved', 'out-of-scope')),
            reason TEXT,
            next_query TEXT,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE conflicts (
            conflict_id TEXT PRIMARY KEY,
            facet_id TEXT NOT NULL REFERENCES facets(facet_id) ON DELETE CASCADE,
            evidence_ids_json TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('open', 'resolved')),
            resolution TEXT,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE receipt_links (
            facet_id TEXT NOT NULL REFERENCES facets(facet_id) ON DELETE CASCADE,
            store_kind TEXT NOT NULL CHECK (store_kind IN ('receipts', 'catalog')),
            store_path TEXT NOT NULL,
            receipt_id TEXT NOT NULL,
            linked_at TEXT NOT NULL,
            PRIMARY KEY(facet_id, store_kind, store_path, receipt_id)
        );
        CREATE INDEX evidence_facet ON evidence(facet_id);
        CREATE INDEX gaps_facet ON gaps(facet_id);
        CREATE INDEX conflicts_facet ON conflicts(facet_id);
        CREATE INDEX receipt_links_receipt
            ON receipt_links(store_kind, store_path, receipt_id);
        """
    )
    connection.execute(f"PRAGMA application_id = {RESEARCH_APPLICATION_ID}")
    connection.execute(f"PRAGMA user_version = {RESEARCH_SCHEMA_VERSION}")

def normalized_json(
    value: str, field: str, expected: type[dict] | type[list]
) -> str:
    if len(value) > MAX_RESEARCH_JSON:
        raise ValueError(f"{field} exceeds {MAX_RESEARCH_JSON} characters")
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field} is invalid JSON: {exc}") from exc
    if not isinstance(parsed, expected):
        label = "object" if expected is dict else "array"
        raise ValueError(f"{field} must be a JSON {label}")
    return json.dumps(parsed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def normalized_id_array(value: str, field: str) -> str:
    normalized = normalized_json(value, field, list)
    parsed = json.loads(normalized)
    if not all(isinstance(item, str) and RECORD_ID.fullmatch(item) for item in parsed):
        raise ValueError(f"{field} must contain only valid record IDs")
    if len(parsed) != len(set(parsed)):
        raise ValueError(f"{field} must not contain duplicate IDs")
    return normalized

def require_research_database(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_file():
        raise ValueError(f"Research database does not exist: {resolved}")
    return resolved

def encode_catalog_scope(
    corpus_ids: list[str], access_boundaries: list[str], project_ids: list[str]
) -> str:
    return json.dumps(
        {
            "corpus_ids": list(dict.fromkeys(corpus_ids)),
            "access_boundaries": list(dict.fromkeys(access_boundaries)),
            "project_ids": list(dict.fromkeys(project_ids)),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

def decode_catalog_scope(value: object) -> tuple[list[str], list[str], list[str]]:
    try:
        scope = json.loads(str(value))
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Research catalog scope is invalid") from exc
    if not isinstance(scope, dict):
        raise ValueError("Research catalog scope is invalid")
    corpus_ids = scope.get("corpus_ids", [])
    access_boundaries = scope.get("access_boundaries", [])
    project_ids = scope.get("project_ids", [])
    if not isinstance(corpus_ids, list) or not all(
        isinstance(item, str) for item in corpus_ids
    ):
        raise ValueError("Research catalog corpus scope is invalid")
    if not isinstance(access_boundaries, list) or not all(
        isinstance(item, str) for item in access_boundaries
    ):
        raise ValueError("Research catalog access scope is invalid")
    if not isinstance(project_ids, list) or not all(
        isinstance(item, str) for item in project_ids
    ):
        raise ValueError("Research catalog project scope is invalid")
    return corpus_ids, access_boundaries, project_ids

def catalog_scope_payload(state: dict[str, object]) -> dict[str, list[str]] | None:
    if state["binding_kind"] != "catalog":
        return None
    corpus_ids, access_boundaries, project_ids = decode_catalog_scope(
        state["catalog_scope_json"]
    )
    return {
        "corpus_ids": corpus_ids,
        "access_boundaries": access_boundaries,
        "project_ids": project_ids,
    }

def current_binding_status(state: dict[str, object]) -> dict[str, object]:
    if state["binding_kind"] == "catalog":
        catalog_path = Path(str(state["catalog_path"]))
        try:
            resolved = require_catalog_database(catalog_path)
            corpus_ids, access_boundaries, _ = decode_catalog_scope(
                state["catalog_scope_json"]
            )
            with database(resolved, readonly=True) as connection:
                _, fingerprint, all_current = catalog_snapshot(
                    connection, corpus_ids or None, access_boundaries or None
                )
        except HANDLED_ERRORS as exc:
            return {
                "catalog_available": False,
                "catalog_stale": True,
                "current_catalog_fingerprint": None,
                "catalog_error": str(exc),
            }
        return {
            "catalog_available": True,
            "catalog_stale": (
                fingerprint != state["catalog_fingerprint"] or not all_current
            ),
            "current_catalog_fingerprint": fingerprint,
            "catalog_path": str(resolved),
        }

    stored_path = state["index_path"]
    if not stored_path:
        return {
            "index_available": False,
            "index_stale": None,
            "current_index_fingerprint": None,
        }
    try:
        path, fingerprint = resolve_index_binding(
            Path(str(stored_path)), Path(str(state["corpus_root"]))
        )
    except HANDLED_ERRORS as exc:
        return {
            "index_available": False,
            "index_stale": True,
            "current_index_fingerprint": None,
            "index_error": str(exc),
        }
    return {
        "index_available": True,
        "index_stale": fingerprint != state["index_fingerprint"],
        "current_index_fingerprint": fingerprint,
        "index_path": str(path),
    }

def research_summary_payload(
    db_path: Path, facet_limit: int = 10, offset: int = 0
) -> dict[str, object]:
    with database(db_path, readonly=True) as connection:
        require_research_schema(connection)
        state = connection.execute("SELECT * FROM research_state WHERE singleton = 1").fetchone()
        if state is None:
            raise ValueError("Research database has no state row")
        counts = {
            "facets": int(connection.execute("SELECT COUNT(*) FROM facets").fetchone()[0]),
            "receipt_links": int(
                connection.execute("SELECT COUNT(*) FROM receipt_links").fetchone()[0]
            ),
            "evidence": int(connection.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]),
            "gaps": int(connection.execute("SELECT COUNT(*) FROM gaps").fetchone()[0]),
            "conflicts": int(
                connection.execute("SELECT COUNT(*) FROM conflicts").fetchone()[0]
            ),
        }
        facets = connection.execute(
            """
            SELECT facet_id, question, status, next_action, updated_at
            FROM facets ORDER BY facet_id LIMIT ? OFFSET ?
            """,
            (facet_limit + 1, offset),
        ).fetchall()
        schema_version_value = schema_version(connection)
        state_values = dict(state)

    selected = facets[:facet_limit]
    has_more = len(facets) > len(selected)
    payload: dict[str, object] = {
        "database": str(db_path),
        "schema_version": schema_version_value,
        "scope": state_values["scope"],
        "status": state_values["status"],
        "binding_kind": state_values["binding_kind"],
        "corpus": state_values["corpus_root"],
        "index_path": state_values["index_path"],
        "index_fingerprint": state_values["index_fingerprint"],
        "catalog_path": state_values["catalog_path"],
        "catalog_fingerprint": state_values["catalog_fingerprint"],
        "catalog_scope": catalog_scope_payload(state_values),
        "next_action": state_values["next_action"],
        "created_at": state_values["created_at"],
        "updated_at": state_values["updated_at"],
        "counts": counts,
        "facet_offset": offset,
        "facet_result_count": len(selected),
        "facet_has_more": has_more,
        "facets": [clip_research_record(dict(row), 800) for row in selected],
    }
    if has_more:
        payload["next_facet_offset"] = offset + len(selected)
    payload.update(current_binding_status(state_values))
    return payload

def fit_payload_lists(
    payload: dict[str, object], list_keys: tuple[str, ...], max_total_chars: int
) -> dict[str, object]:
    """Shrink bounded list fields until the serialized payload fits."""
    while len(json.dumps(payload, ensure_ascii=False, separators=(",", ":"))) > max_total_chars:
        selected_key = next(
            (
                key
                for key in list_keys
                if isinstance(payload.get(key), list) and payload[key]
            ),
            None,
        )
        if selected_key is None:
            raise ValueError("--max-total-chars is too small for the resume summary")
        values = payload[selected_key]
        assert isinstance(values, list)
        values.pop()
        payload["output_truncated"] = True
    return payload

def research_resume_payload(
    db_path: Path,
    limit: int,
    max_total_chars: int,
) -> dict[str, object]:
    with database(db_path, readonly=True) as connection:
        require_research_schema(connection)
        state = connection.execute(
            "SELECT * FROM research_state WHERE singleton = 1"
        ).fetchone()
        if state is None:
            raise ValueError("Research database has no state row")
        receipt_links = [
            dict(row)
            for row in connection.execute(
                """
                SELECT facet_id, store_kind, store_path, receipt_id, linked_at
                FROM receipt_links
                ORDER BY linked_at DESC, receipt_id
                LIMIT ?
                """,
                (limit + 1,),
            )
        ]
        facets = [
            clip_research_record(dict(row), 600)
            for row in connection.execute(
                """
                SELECT f.facet_id, f.question, f.status, f.next_action,
                       COUNT(DISTINCT e.evidence_id) AS evidence_count,
                       COALESCE(SUM(CASE WHEN e.verified = 1 THEN 1 ELSE 0 END), 0)
                           AS verified_count
                FROM facets AS f
                LEFT JOIN evidence AS e ON e.facet_id = f.facet_id
                WHERE f.status IN ('open', 'conflicted', 'unresolved')
                GROUP BY f.facet_id
                ORDER BY f.facet_id
                LIMIT ?
                """,
                (limit + 1,),
            )
        ]
        gaps = [
            clip_research_record(dict(row), 600)
            for row in connection.execute(
                """
                SELECT gap_id, facet_id, description, reason, next_query
                FROM gaps WHERE status = 'open'
                ORDER BY gap_id LIMIT ?
                """,
                (limit + 1,),
            )
        ]
        conflicts = [
            clip_research_record(research_record(row), 600)
            for row in connection.execute(
                """
                SELECT conflict_id, facet_id, evidence_ids_json, description, resolution
                FROM conflicts WHERE status = 'open'
                ORDER BY conflict_id LIMIT ?
                """,
                (limit + 1,),
            )
        ]
        values = dict(state)

    output_truncated = any(
        len(items) > limit for items in (receipt_links, facets, gaps, conflicts)
    ) or any(
        item.get("truncated_fields") for items in (facets, gaps, conflicts) for item in items
    )
    receipt_links = receipt_links[:limit]
    facets, gaps, conflicts = facets[:limit], gaps[:limit], conflicts[:limit]
    recent_receipts: list[dict[str, object]] = []
    local_fingerprint_cache: dict[str, str | None] = {}
    catalog_fingerprint_cache: dict[tuple[str, tuple[str, ...]], tuple[str, bool]] = {}
    for link in receipt_links:
        store_path_value = link.get("store_path")
        if not store_path_value:
            continue
        store_path = Path(str(store_path_value)).resolve()
        try:
            if link["store_kind"] == "receipts":
                receipt_path = require_receipt_database(store_path)
                with database(receipt_path, readonly=True) as connection:
                    require_receipt_schema(connection)
                    receipt_state = connection.execute(
                        "SELECT * FROM receipt_state WHERE singleton = 1"
                    ).fetchone()
                    if receipt_state is None:
                        raise ValueError("Receipt database has no state row")
                    cache_key = str(receipt_path)
                    if cache_key not in local_fingerprint_cache:
                        try:
                            _, cached_fingerprint = resolve_index_binding(
                                Path(receipt_state["index_path"]),
                                Path(receipt_state["corpus_root"]),
                            )
                        except HANDLED_ERRORS:
                            cached_fingerprint = None
                        local_fingerprint_cache[cache_key] = cached_fingerprint
                    live_fingerprint = local_fingerprint_cache[cache_key]
                    row = connection.execute(
                        """
                        SELECT receipt_id, query, mode, outcome, next_offset,
                               next_start_char, index_fingerprint, last_used_at
                        FROM search_receipts WHERE receipt_id = ?
                        """,
                        (link["receipt_id"],),
                    ).fetchone()
                    if row is None:
                        continue
                    item = {**dict(row), **link}
                    item["current"] = (
                        live_fingerprint is not None
                        and row["index_fingerprint"] == live_fingerprint
                    )
            else:
                catalog_path = require_catalog_database(store_path)
                with database(catalog_path, readonly=True) as connection:
                    row = connection.execute(
                        """
                        SELECT receipt_id, query, mode, outcome, next_offset,
                               corpus_ids_json, catalog_fingerprint, last_used_at
                        FROM federated_receipts WHERE receipt_id = ?
                        """,
                        (link["receipt_id"],),
                    ).fetchone()
                    if row is None:
                        continue
                    item = {**dict(row), **link}
                    receipt_scope = json.loads(str(item.pop("corpus_ids_json")))
                    if not isinstance(receipt_scope, list) or not all(
                        isinstance(corpus_id, str) for corpus_id in receipt_scope
                    ):
                        raise ValueError("Federated receipt corpus scope is invalid")
                    item["corpus_ids"] = receipt_scope
                    cache_key = (str(catalog_path), tuple(receipt_scope))
                    if cache_key not in catalog_fingerprint_cache:
                        _, cached_fingerprint, cached_current = catalog_snapshot(
                            connection, receipt_scope
                        )
                        catalog_fingerprint_cache[cache_key] = (
                            cached_fingerprint,
                            cached_current,
                        )
                    live_fingerprint, all_current = catalog_fingerprint_cache[cache_key]
                    item["current"] = (
                        all_current
                        and row["catalog_fingerprint"] == live_fingerprint
                    )
            recent_receipts.append(item)
        except HANDLED_ERRORS as exc:
            recent_receipts.append(
                {
                    **link,
                    "current": False,
                    "store_error": str(exc),
                }
            )

    payload: dict[str, object] = {
        "database": str(db_path),
        "scope": values["scope"],
        "status": values["status"],
        "next_action": values["next_action"],
        "binding_kind": values["binding_kind"],
        "index_fingerprint": values["index_fingerprint"],
        "catalog_fingerprint": values["catalog_fingerprint"],
        "catalog_scope": catalog_scope_payload(values),
        "active_facets": facets,
        "open_gaps": gaps,
        "open_conflicts": conflicts,
        "recent_receipts": recent_receipts,
        "output_truncated": output_truncated,
    }
    payload.update(current_binding_status(values))
    return fit_payload_lists(
        payload,
        ("recent_receipts", "open_conflicts", "open_gaps", "active_facets"),
        max_total_chars,
    )

def command_research_init(args: argparse.Namespace) -> int:
    db_path = args.db.resolve()
    scope = required_research_text(args.scope, "--scope")
    next_action = optional_research_text(args.next_action, "--next-action")
    if db_path.exists():
        with database(db_path, readonly=True) as connection:
            require_research_owner(connection)
        raise ValueError(f"Research database already exists: {db_path}")

    binding_kind: str
    corpus_root: Path | None = None
    index_path: Path | None = None
    index_fingerprint_value: str | None = None
    catalog_path: Path | None = None
    catalog_fingerprint_value: str | None = None
    catalog_scope_json: str | None = None
    selected_corpus_ids = [
        validate_record_id(value, "--corpus-id") for value in args.corpus_id
    ]
    selected_project_ids = [
        validate_record_id(value, "--project-id") for value in args.project_id
    ]
    selected_boundaries = [
        required_research_text(value, "--access-boundary")
        for value in args.access_boundary
    ]
    if args.catalog is not None:
        if args.index is not None:
            raise ValueError("--index cannot be used with --catalog")
        binding_kind = "catalog"
        catalog_path = require_catalog_database(args.catalog)
        with database(catalog_path, readonly=True) as connection:
            require_catalog_schema(connection)
            project_corpora = project_scope_corpus_ids(
                connection, selected_project_ids
            )
            requested_corpus_ids = list(
                dict.fromkeys([*selected_corpus_ids, *project_corpora])
            )
            entries, catalog_fingerprint_value, _ = catalog_snapshot(
                connection,
                requested_corpus_ids or None,
                selected_boundaries or None,
                MAX_CATALOG_CORPORA,
            )
        if (
            not selected_corpus_ids
            and not selected_project_ids
            and not selected_boundaries
        ):
            boundaries = {str(item["access_boundary"]) for item in entries}
            if len(boundaries) > 1:
                raise ValueError(
                    "Catalog spans multiple access boundaries; select --access-boundary "
                    "or explicit --corpus-id values"
                )
        concrete_corpus_ids = [str(item["corpus_id"]) for item in entries]
        catalog_scope_json = encode_catalog_scope(
            concrete_corpus_ids, selected_boundaries, selected_project_ids
        )
        if catalog_path == db_path:
            raise ValueError("Research database and catalog database must be separate files")
    else:
        binding_kind = "corpus"
        if selected_corpus_ids or selected_project_ids or selected_boundaries:
            raise ValueError(
                "--corpus-id, --project-id, and --access-boundary require --catalog"
            )
        if args.corpus is None:
            raise ValueError("Provide --corpus or --catalog")
        corpus_root = args.corpus.resolve()
        if not corpus_root.is_dir() and not corpus_root.is_file():
            raise ValueError(f"Corpus path does not exist: {corpus_root}")
        if args.index is not None:
            index_path, index_fingerprint_value = resolve_index_binding(
                args.index, corpus_root
            )
            if index_path == db_path:
                raise ValueError("Research database and index database must be separate files")

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
                create_research_schema(connection)
                now = utc_now()
                connection.execute(
                    """
                    INSERT INTO research_state(
                        singleton, scope, status, binding_kind, corpus_root, index_path,
                        index_fingerprint, catalog_path, catalog_fingerprint,
                        catalog_scope_json, next_action, created_at, updated_at
                    ) VALUES (1, ?, 'active', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        scope,
                        binding_kind,
                        str(corpus_root) if corpus_root else None,
                        str(index_path) if index_path else None,
                        index_fingerprint_value,
                        str(catalog_path) if catalog_path else None,
                        catalog_fingerprint_value,
                        catalog_scope_json,
                        next_action,
                        now,
                        now,
                    ),
                )
        finally:
            connection.close()
        harden_database_permissions(temporary_path)
        try:
            os.link(temporary_path, db_path)
        except FileExistsError as exc:
            raise ValueError(f"Research database already exists: {db_path}") from exc
        temporary_path.unlink()
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    emit_json(research_summary_payload(db_path), args.pretty)
    return 0

def command_research_info(args: argparse.Namespace) -> int:
    db_path = require_research_database(args.db)
    if not 1 <= args.facet_limit <= 100:
        raise ValueError("--facet-limit must be between 1 and 100")
    if args.offset < 0:
        raise ValueError("--offset must be zero or greater")
    if args.resume:
        if not 1 <= args.resume_limit <= 50:
            raise ValueError("--resume-limit must be between 1 and 50")
        if not 1_000 <= args.max_total_chars <= 100_000:
            raise ValueError("--max-total-chars must be between 1000 and 100000")
        payload = research_resume_payload(db_path, args.resume_limit, args.max_total_chars)
    else:
        payload = research_summary_payload(db_path, args.facet_limit, args.offset)
    emit_json(payload, args.pretty)
    return 0

def command_research_update(args: argparse.Namespace) -> int:
    db_path = require_research_database(args.db)
    if args.scope is None and args.status is None and args.next_action is None:
        raise ValueError("Provide --scope, --status, or --next-action")
    updates: list[str] = []
    values: list[object] = []
    if args.scope is not None:
        updates.append("scope = ?")
        values.append(required_research_text(args.scope, "--scope"))
    if args.status is not None:
        if args.status not in RESEARCH_STATUSES:
            raise ValueError(f"Unsupported research status: {args.status}")
        updates.append("status = ?")
        values.append(args.status)
    if args.next_action is not None:
        updates.append("next_action = ?")
        values.append(optional_research_text(args.next_action, "--next-action"))
    updates.append("updated_at = ?")
    values.append(utc_now())
    with database(db_path) as connection:
        require_research_schema(connection)
        connection.execute(
            f"UPDATE research_state SET {', '.join(updates)} WHERE singleton = 1",
            values,
        )
    harden_database_permissions(db_path)
    emit_json(research_summary_payload(db_path), args.pretty)
    return 0

def require_facet(connection: sqlite3.Connection, facet_id: str) -> None:
    if connection.execute(
        "SELECT 1 FROM facets WHERE facet_id = ?", (facet_id,)
    ).fetchone() is None:
        raise ValueError(f"Facet does not exist: {facet_id}")

def research_record(row: sqlite3.Row) -> dict[str, object]:
    item: dict[str, object] = dict(row)
    for key in ("evidence_ids_json",):
        if key in item:
            item[key.removesuffix("_json")] = json.loads(str(item.pop(key)))
    if "verified" in item:
        item["verified"] = bool(item["verified"])
    return item

def clip_research_record(item: dict[str, object], limit: int) -> dict[str, object]:
    clipped = dict(item)
    truncated_fields: list[str] = []
    for key in (
        "question",
        "next_action",
        "finding",
        "source",
        "section",
        "excerpt",
        "interpretation",
        "description",
        "reason",
        "next_query",
        "resolution",
    ):
        value = clipped.get(key)
        if isinstance(value, str):
            clipped_value, truncated = clip_text(value, limit)
            clipped[key] = clipped_value
            if truncated:
                truncated_fields.append(key)
    if truncated_fields:
        clipped["truncated_fields"] = truncated_fields
    return clipped

def summarize_research_record(kind: str, item: dict[str, object]) -> dict[str, object]:
    summary = dict(item)
    if kind == "evidence":
        summary.pop("excerpt", None)
        summary.pop("interpretation", None)
    elif kind == "conflicts":
        summary.pop("resolution", None)
    return summary
