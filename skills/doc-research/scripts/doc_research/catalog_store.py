from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from contextlib import closing
from pathlib import Path

from .common import (
    CATALOG_APPLICATION_ID,
    CATALOG_SCHEMA_VERSION,
    HANDLED_ERRORS,
    MAX_CATALOG_CORPORA,
    MAX_CATALOG_PROJECTS,
    PROJECT_ANCHOR_KINDS,
    application_id,
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
from .index import (
    index_fingerprint,
    require_current_schema,
    require_database,
    resolve_index_binding,
)
from .receipts import require_receipt_database, validate_receipt_store_connection

CATALOG_COLUMNS = {
    "catalog_state": ("singleton", "created_at", "updated_at"),
    "projects": (
        "project_id",
        "label",
        "access_boundary",
        "created_at",
        "updated_at",
    ),
    "project_anchors": ("project_id", "anchor_kind", "anchor"),
    "corpora": (
        "corpus_id",
        "label",
        "access_boundary",
        "adapter",
        "locator",
        "index_path",
        "receipts_path",
        "generation",
        "enabled",
        "created_at",
        "updated_at",
    ),
    "project_corpora": ("project_id", "corpus_id"),
    "federated_receipts": (
        "receipt_id",
        "query",
        "mode",
        "filters_json",
        "corpus_ids_json",
        "member_receipts_json",
        "outcome",
        "result_refs_json",
        "next_offset",
        "catalog_fingerprint",
        "created_at",
        "updated_at",
        "last_used_at",
    ),
}

def require_catalog_owner(connection: sqlite3.Connection) -> None:
    identifier = application_id(connection)
    if identifier == CATALOG_APPLICATION_ID:
        return
    if identifier != 0:
        raise ValueError("Database belongs to another application; refusing to use it")
    if database_objects(connection):
        raise ValueError(
            "Existing database is not a corpus catalog with this tool's application "
            "identifier; refusing to use it"
        )

def catalog_schema_is_current(connection: sqlite3.Connection) -> bool:
    return (
        application_id(connection) == CATALOG_APPLICATION_ID
        and schema_version(connection) == CATALOG_SCHEMA_VERSION
        and all(
            table_exists(connection, table)
            and table_columns(connection, table) == columns
            for table, columns in CATALOG_COLUMNS.items()
        )
    )

def require_catalog_schema(connection: sqlite3.Connection) -> None:
    require_catalog_owner(connection)
    if not catalog_schema_is_current(connection):
        raise ValueError("Corpus catalog schema is unsupported or incomplete")

def create_catalog_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE catalog_state (
            singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE projects (
            project_id TEXT PRIMARY KEY,
            label TEXT,
            access_boundary TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE project_anchors (
            project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
            anchor_kind TEXT NOT NULL CHECK (
                anchor_kind IN ('connector', 'filesystem', 'manual')
            ),
            anchor TEXT NOT NULL,
            PRIMARY KEY(project_id, anchor_kind, anchor)
        );
        CREATE TABLE corpora (
            corpus_id TEXT PRIMARY KEY,
            label TEXT,
            access_boundary TEXT NOT NULL,
            adapter TEXT NOT NULL CHECK (adapter IN ('local-index', 'external')),
            locator TEXT NOT NULL,
            index_path TEXT,
            receipts_path TEXT,
            generation TEXT,
            enabled INTEGER NOT NULL CHECK (enabled IN (0, 1)),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            CHECK (
                (adapter = 'local-index' AND index_path IS NOT NULL AND receipts_path IS NOT NULL)
                OR (adapter = 'external' AND index_path IS NULL AND receipts_path IS NULL)
            )
        );
        CREATE TABLE project_corpora (
            project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
            corpus_id TEXT NOT NULL REFERENCES corpora(corpus_id) ON DELETE CASCADE,
            PRIMARY KEY(project_id, corpus_id)
        );
        CREATE TABLE federated_receipts (
            receipt_id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            mode TEXT NOT NULL CHECK (mode IN ('literal', 'prefix', 'fts')),
            filters_json TEXT NOT NULL,
            corpus_ids_json TEXT NOT NULL,
            member_receipts_json TEXT NOT NULL,
            outcome TEXT NOT NULL CHECK (
                outcome IN ('results', 'no-material-result', 'incomplete')
            ),
            result_refs_json TEXT NOT NULL,
            next_offset INTEGER,
            catalog_fingerprint TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_used_at TEXT NOT NULL,
            CHECK (next_offset IS NULL OR next_offset >= 0)
        );
        CREATE INDEX project_anchors_lookup
            ON project_anchors(anchor_kind, anchor, project_id);
        CREATE INDEX project_corpora_corpus
            ON project_corpora(corpus_id, project_id);
        CREATE INDEX corpora_enabled ON corpora(enabled, corpus_id);
        CREATE INDEX federated_receipts_fingerprint
            ON federated_receipts(catalog_fingerprint);
        """
    )
    connection.execute(f"PRAGMA application_id = {CATALOG_APPLICATION_ID}")
    connection.execute(f"PRAGMA user_version = {CATALOG_SCHEMA_VERSION}")

def require_catalog_database(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_file():
        raise ValueError(f"Corpus catalog does not exist: {resolved}")
    return resolved

def catalog_entry_status(row: sqlite3.Row) -> dict[str, object]:
    item = dict(row)
    item["enabled"] = bool(item["enabled"])
    item["available"] = True
    item["current_generation"] = item["generation"]
    if item["adapter"] == "local-index":
        try:
            index_path, fingerprint = resolve_index_binding(
                Path(item["index_path"]), Path(item["locator"])
            )
            receipt_path = require_receipt_database(Path(item["receipts_path"]))
            with database(receipt_path, readonly=True) as receipts:
                validate_receipt_store_connection(
                    receipts, index_path, Path(item["locator"])
                )
            item["index_path"] = str(index_path)
            item["receipts_path"] = str(receipt_path)
            item["current_generation"] = fingerprint
            item["stale"] = fingerprint != item["generation"]
        except HANDLED_ERRORS as exc:
            item["available"] = False
            item["stale"] = True
            item["error"] = str(exc)
    else:
        item["stale"] = None if not item["generation"] else False
        if not item["generation"]:
            item["available"] = False
            item["error"] = "External adapter has no verified generation"
    return item

def normalize_project_anchor(anchor_kind: str, value: str) -> str:
    if anchor_kind not in PROJECT_ANCHOR_KINDS:
        raise ValueError(f"Unsupported project anchor kind: {anchor_kind}")
    normalized = required_research_text(value, "--anchor")
    if anchor_kind == "filesystem":
        return os.path.normcase(str(Path(normalized).resolve()))
    return normalized

def project_candidates(
    connection: sqlite3.Connection,
    anchor_kind: str,
    anchor: str,
    access_boundaries: list[str] | None = None,
) -> list[dict[str, object]]:
    parameters: list[object] = [anchor_kind]
    where = "WHERE a.anchor_kind = ?"
    if access_boundaries:
        normalized_boundaries = list(dict.fromkeys(access_boundaries))
        placeholders = ",".join("?" for _ in normalized_boundaries)
        where += f" AND p.access_boundary IN ({placeholders})"
        parameters.extend(normalized_boundaries)
    rows = connection.execute(
        f"""
        SELECT p.project_id, p.label, p.access_boundary, a.anchor_kind, a.anchor
        FROM projects AS p
        JOIN project_anchors AS a ON a.project_id = p.project_id
        {where}
        ORDER BY p.project_id, a.anchor
        """,
        parameters,
    ).fetchall()
    matched: dict[str, dict[str, object]] = {}
    target_path = Path(anchor) if anchor_kind == "filesystem" else None
    for row in rows:
        candidate_anchor = str(row["anchor"])
        if anchor_kind == "filesystem":
            assert target_path is not None
            try:
                relative = target_path.relative_to(Path(candidate_anchor))
            except ValueError:
                continue
            specificity = len(Path(candidate_anchor).parts)
            distance = len(relative.parts)
        else:
            if candidate_anchor != anchor:
                continue
            specificity = len(candidate_anchor)
            distance = 0
        item = {
            "project_id": str(row["project_id"]),
            "label": row["label"],
            "access_boundary": str(row["access_boundary"]),
            "anchor_kind": anchor_kind,
            "anchor": candidate_anchor,
            "specificity": specificity,
            "distance": distance,
        }
        current = matched.get(item["project_id"])
        if current is None or int(item["specificity"]) > int(current["specificity"]):
            matched[str(item["project_id"])] = item
    return sorted(
        matched.values(),
        key=lambda item: (-int(item["specificity"]), str(item["project_id"])),
    )

def resolve_project_anchor(
    connection: sqlite3.Connection,
    anchor_kind: str,
    anchor: str,
    access_boundaries: list[str] | None = None,
) -> dict[str, object]:
    candidates = project_candidates(
        connection, anchor_kind, anchor, access_boundaries
    )
    if not candidates:
        return {
            "resolved": False,
            "ambiguous": False,
            "project_id": None,
            "candidates": [],
        }
    top_specificity = int(candidates[0]["specificity"])
    top = [
        item for item in candidates if int(item["specificity"]) == top_specificity
    ]
    if len(top) != 1:
        return {
            "resolved": False,
            "ambiguous": True,
            "project_id": None,
            "candidates": candidates[:MAX_CATALOG_PROJECTS],
        }
    return {
        "resolved": True,
        "ambiguous": False,
        "project_id": top[0]["project_id"],
        "project": top[0],
        "related_projects": candidates[1:MAX_CATALOG_PROJECTS],
    }

def validate_project_corpora(
    connection: sqlite3.Connection,
    corpus_ids: list[str],
    access_boundary: str,
) -> list[str]:
    normalized = list(dict.fromkeys(corpus_ids))
    if not normalized:
        return []
    if len(normalized) > MAX_CATALOG_CORPORA:
        raise ValueError(f"At most {MAX_CATALOG_CORPORA} corpora may be selected")
    placeholders = ",".join("?" for _ in normalized)
    rows = connection.execute(
        f"SELECT corpus_id, access_boundary, enabled FROM corpora "
        f"WHERE corpus_id IN ({placeholders})",
        normalized,
    ).fetchall()
    found = {
        str(row["corpus_id"]): (str(row["access_boundary"]), bool(row["enabled"]))
        for row in rows
    }
    missing = [corpus_id for corpus_id in normalized if corpus_id not in found]
    if missing:
        raise ValueError(f"Unknown corpus IDs: {', '.join(missing)}")
    mismatched = [
        corpus_id
        for corpus_id in normalized
        if found[corpus_id][0] != access_boundary
    ]
    if mismatched:
        raise ValueError(
            "Project and corpus access boundaries differ: "
            + ", ".join(mismatched)
        )
    disabled = [corpus_id for corpus_id in normalized if not found[corpus_id][1]]
    if disabled:
        raise ValueError(
            "Disabled corpora cannot be newly attached to a project: "
            + ", ".join(disabled)
        )
    return normalized

def upsert_catalog_project(
    connection: sqlite3.Connection,
    project_id: str,
    label: str | None,
    access_boundary: str,
    anchor_kind: str,
    anchor: str,
    corpus_ids: list[str],
    replace_corpora: bool,
    add_anchor: bool = True,
) -> tuple[str, list[str]]:
    existing = connection.execute(
        "SELECT label, access_boundary, created_at FROM projects WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    if existing is not None and existing["access_boundary"] != access_boundary:
        raise ValueError("A project's access boundary cannot be changed in place")
    normalized_corpora = validate_project_corpora(
        connection, corpus_ids, access_boundary
    )
    if existing is None and not normalized_corpora:
        raise ValueError("A new project must be attached to at least one corpus")
    now = utc_now()
    created_at = str(existing["created_at"]) if existing else now
    stored_label = label if label is not None else (existing["label"] if existing else None)
    connection.execute(
        """
        INSERT INTO projects(project_id, label, access_boundary, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(project_id) DO UPDATE SET
            label = excluded.label,
            updated_at = excluded.updated_at
        """,
        (project_id, stored_label, access_boundary, created_at, now),
    )
    if add_anchor:
        connection.execute(
            """
            INSERT INTO project_anchors(project_id, anchor_kind, anchor)
            VALUES (?, ?, ?)
            ON CONFLICT(project_id, anchor_kind, anchor) DO NOTHING
            """,
            (project_id, anchor_kind, anchor),
        )
    if replace_corpora:
        if not normalized_corpora:
            raise ValueError("--replace-corpora requires at least one --corpus-id")
        placeholders = ",".join("?" for _ in normalized_corpora)
        connection.execute(
            f"DELETE FROM project_corpora WHERE project_id = ? "
            f"AND corpus_id NOT IN ({placeholders})",
            [project_id, *normalized_corpora],
        )
    connection.executemany(
        """
        INSERT INTO project_corpora(project_id, corpus_id) VALUES (?, ?)
        ON CONFLICT(project_id, corpus_id) DO NOTHING
        """,
        ((project_id, corpus_id) for corpus_id in normalized_corpora),
    )
    connection.execute(
        "UPDATE catalog_state SET updated_at = ? WHERE singleton = 1", (now,)
    )
    members = [
        str(row["corpus_id"])
        for row in connection.execute(
            "SELECT corpus_id FROM project_corpora WHERE project_id = ? "
            "ORDER BY corpus_id",
            (project_id,),
        )
    ]
    return ("updated" if existing else "created"), members

def project_scope_corpus_ids(
    connection: sqlite3.Connection, project_ids: list[str]
) -> list[str]:
    normalized = list(dict.fromkeys(project_ids))
    if not normalized:
        return []
    if len(normalized) > MAX_CATALOG_PROJECTS:
        raise ValueError(f"At most {MAX_CATALOG_PROJECTS} projects may be selected")
    placeholders = ",".join("?" for _ in normalized)
    found_projects = {
        str(row["project_id"])
        for row in connection.execute(
            f"SELECT project_id FROM projects WHERE project_id IN ({placeholders})",
            normalized,
        )
    }
    missing = [project_id for project_id in normalized if project_id not in found_projects]
    if missing:
        raise ValueError(f"Unknown project IDs: {', '.join(missing)}")
    rows = connection.execute(
        f"""
        SELECT DISTINCT pc.corpus_id
        FROM project_corpora AS pc
        JOIN corpora AS c ON c.corpus_id = pc.corpus_id
        WHERE pc.project_id IN ({placeholders}) AND c.enabled = 1
        ORDER BY pc.corpus_id
        """,
        normalized,
    ).fetchall()
    corpus_ids = [str(row["corpus_id"]) for row in rows]
    if not corpus_ids:
        raise ValueError("Selected projects have no enabled corpora")
    if len(corpus_ids) > MAX_CATALOG_CORPORA:
        raise ValueError(
            f"Selected projects contain {len(corpus_ids)} corpora; narrow the scope "
            f"to at most {MAX_CATALOG_CORPORA}"
        )
    return corpus_ids

def catalog_snapshot(
    connection: sqlite3.Connection,
    corpus_ids: list[str] | None = None,
    access_boundaries: list[str] | None = None,
    max_corpora: int | None = None,
) -> tuple[list[dict[str, object]], str, bool]:
    require_catalog_schema(connection)
    parameters: list[object] = []
    where = "WHERE enabled = 1"
    if corpus_ids:
        normalized = list(dict.fromkeys(corpus_ids))
        if len(normalized) > MAX_CATALOG_CORPORA:
            raise ValueError(f"At most {MAX_CATALOG_CORPORA} corpora may be selected")
        placeholders = ",".join("?" for _ in normalized)
        where += f" AND corpus_id IN ({placeholders})"
        parameters.extend(normalized)
    if access_boundaries:
        normalized_boundaries = list(dict.fromkeys(access_boundaries))
        placeholders = ",".join("?" for _ in normalized_boundaries)
        where += f" AND access_boundary IN ({placeholders})"
        parameters.extend(normalized_boundaries)
    rows = connection.execute(
        f"SELECT * FROM corpora {where} ORDER BY corpus_id", parameters
    ).fetchall()
    if corpus_ids:
        found = {str(row["corpus_id"]) for row in rows}
        missing = [corpus_id for corpus_id in dict.fromkeys(corpus_ids) if corpus_id not in found]
        if missing:
            raise ValueError(f"Unknown or disabled corpus IDs: {', '.join(missing)}")
    if access_boundaries:
        found_boundaries = {str(row["access_boundary"]) for row in rows}
        missing_boundaries = [
            boundary
            for boundary in dict.fromkeys(access_boundaries)
            if boundary not in found_boundaries
        ]
        if missing_boundaries:
            raise ValueError(
                "Unknown or disabled access boundaries: "
                + ", ".join(missing_boundaries)
            )
    if not rows:
        raise ValueError("Corpus catalog has no enabled corpus in the selected scope")
    if max_corpora is not None and len(rows) > max_corpora:
        raise ValueError(
            f"Selected scope contains {len(rows)} corpora; narrow it to at most "
            f"{max_corpora} with --project-id, --access-boundary, or --corpus-id"
        )
    entries = [catalog_entry_status(row) for row in rows]
    digest = hashlib.sha256()
    all_current = True
    for item in entries:
        current_generation = item.get("current_generation")
        available = bool(item.get("available"))
        all_current = all_current and available and bool(current_generation)
        digest.update(
            json.dumps(
                [
                    item["corpus_id"],
                    item["adapter"],
                    item["locator"],
                    current_generation,
                    item["access_boundary"],
                    available,
                ],
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return entries, digest.hexdigest(), all_current

def catalog_status(db_path: Path, live: bool = False) -> dict[str, object]:
    with database(db_path, readonly=True) as connection:
        require_catalog_schema(connection)
        state = connection.execute(
            "SELECT * FROM catalog_state WHERE singleton = 1"
        ).fetchone()
        if state is None:
            raise ValueError("Corpus catalog has no state row")
        rows = connection.execute("SELECT * FROM corpora ORDER BY corpus_id").fetchall()
        receipt_count = int(
            connection.execute("SELECT COUNT(*) FROM federated_receipts").fetchone()[0]
        )
        project_count = int(
            connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        )
        project_membership_count = int(
            connection.execute("SELECT COUNT(*) FROM project_corpora").fetchone()[0]
        )
    entries = [catalog_entry_status(row) if live else dict(row) for row in rows]
    for item in entries:
        item["enabled"] = bool(item["enabled"])
    return {
        "database": str(db_path),
        "schema_version": CATALOG_SCHEMA_VERSION,
        "corpus_count": len(entries),
        "enabled_corpus_count": sum(bool(item["enabled"]) for item in entries),
        "project_count": project_count,
        "project_membership_count": project_membership_count,
        "federated_receipt_count": receipt_count,
        "created_at": state["created_at"],
        "updated_at": state["updated_at"],
        "corpora": entries,
    }

def command_catalog_init(args: argparse.Namespace) -> int:
    db_path = args.db.resolve()
    if db_path.exists():
        with database(db_path, readonly=True) as connection:
            require_catalog_owner(connection)
        raise ValueError(f"Corpus catalog already exists: {db_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{db_path.name}.", suffix=".tmp", dir=db_path.parent, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
        with closing(connect(temporary_path)) as connection, connection:
            create_catalog_schema(connection)
            now = utc_now()
            connection.execute(
                "INSERT INTO catalog_state(singleton, created_at, updated_at) "
                "VALUES (1, ?, ?)",
                (now, now),
            )
        harden_database_permissions(temporary_path)
        try:
            os.link(temporary_path, db_path)
        except FileExistsError as exc:
            raise ValueError(f"Corpus catalog already exists: {db_path}") from exc
        temporary_path.unlink()
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    emit_json(catalog_status(db_path), args.pretty)
    return 0
def command_catalog_put(args: argparse.Namespace) -> int:
    db_path = require_catalog_database(args.db)
    corpus_id = validate_record_id(args.corpus_id, "corpus_id")
    label = optional_research_text(args.label, "--label")
    access_boundary = required_research_text(
        args.access_boundary, "--access-boundary"
    )
    project_ids = [
        validate_record_id(value, "--project-id") for value in args.project_id
    ]
    if args.disabled and project_ids:
        raise ValueError("A disabled corpus cannot be newly attached to a project")
    adapter = args.adapter
    locator: str
    index_path: str | None = None
    receipts_path: str | None = None
    generation: str | None = args.generation
    if adapter == "local-index":
        if args.locator is not None or args.generation is not None:
            raise ValueError(
                "local-index derives --locator and --generation from its index"
            )
        if args.index is None or args.receipts_db is None:
            raise ValueError("local-index requires --index and --receipts-db")
        index = require_database(args.index)
        with database(index, readonly=True) as connection:
            require_current_schema(connection)
            corpus_row = connection.execute(
                "SELECT value FROM metadata WHERE key = 'corpus_root'"
            ).fetchone()
            if corpus_row is None:
                raise ValueError("Index database has no corpus binding")
            corpus_root = Path(corpus_row["value"])
            generation = index_fingerprint(connection)
        receipts = require_receipt_database(args.receipts_db)
        with database(receipts, readonly=True) as connection:
            validate_receipt_store_connection(connection, index, corpus_root)
        locator = str(corpus_root.resolve())
        index_path = str(index)
        receipts_path = str(receipts)
    else:
        if args.index is not None or args.receipts_db is not None:
            raise ValueError("external adapter does not accept --index or --receipts-db")
        locator = required_research_text(args.locator, "--locator")
        generation = optional_research_text(args.generation, "--generation")

    now = utc_now()
    with database(db_path) as connection:
        require_catalog_schema(connection)
        existing = connection.execute(
            "SELECT access_boundary, created_at FROM corpora WHERE corpus_id = ?",
            (corpus_id,),
        ).fetchone()
        if existing is not None and existing["access_boundary"] != access_boundary:
            raise ValueError("A corpus access boundary cannot be changed in place")
        created_at = str(existing["created_at"]) if existing else now
        connection.execute(
            """
            INSERT INTO corpora(
                corpus_id, label, access_boundary, adapter, locator,
                index_path, receipts_path, generation, enabled, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(corpus_id) DO UPDATE SET
                label = excluded.label,
                access_boundary = excluded.access_boundary,
                adapter = excluded.adapter,
                locator = excluded.locator,
                index_path = excluded.index_path,
                receipts_path = excluded.receipts_path,
                generation = excluded.generation,
                enabled = excluded.enabled,
                updated_at = excluded.updated_at
            """,
            (
                corpus_id,
                label,
                access_boundary,
                adapter,
                locator,
                index_path,
                receipts_path,
                generation,
                0 if args.disabled else 1,
                created_at,
                now,
            ),
        )
        if project_ids:
            normalized_projects = list(dict.fromkeys(project_ids))
            placeholders = ",".join("?" for _ in normalized_projects)
            projects = connection.execute(
                f"SELECT project_id, access_boundary FROM projects "
                f"WHERE project_id IN ({placeholders})",
                normalized_projects,
            ).fetchall()
            project_boundaries = {
                str(row["project_id"]): str(row["access_boundary"])
                for row in projects
            }
            missing = [
                project_id
                for project_id in normalized_projects
                if project_id not in project_boundaries
            ]
            if missing:
                raise ValueError(f"Unknown project IDs: {', '.join(missing)}")
            mismatched = [
                project_id
                for project_id in normalized_projects
                if project_boundaries[project_id] != access_boundary
            ]
            if mismatched:
                raise ValueError(
                    "Project and corpus access boundaries differ: "
                    + ", ".join(mismatched)
                )
            connection.executemany(
                """
                INSERT INTO project_corpora(project_id, corpus_id) VALUES (?, ?)
                ON CONFLICT(project_id, corpus_id) DO NOTHING
                """,
                ((project_id, corpus_id) for project_id in normalized_projects),
            )
            connection.executemany(
                "UPDATE projects SET updated_at = ? WHERE project_id = ?",
                ((now, project_id) for project_id in normalized_projects),
            )
        connection.execute(
            "UPDATE catalog_state SET updated_at = ? WHERE singleton = 1", (now,)
        )
    harden_database_permissions(db_path)
    emit_json(
        {
            "database": str(db_path),
            "corpus_id": corpus_id,
            "adapter": adapter,
            "locator": locator,
            "generation": generation,
            "enabled": not args.disabled,
            "project_ids": list(dict.fromkeys(project_ids)),
            "action": "updated" if existing else "created",
        },
        args.pretty,
    )
    return 0
def command_catalog_project_put(args: argparse.Namespace) -> int:
    db_path = require_catalog_database(args.db)
    project_id = validate_record_id(args.project_id, "project_id")
    label = optional_research_text(args.label, "--label")
    access_boundary = required_research_text(
        args.access_boundary, "--access-boundary"
    )
    anchor_kind = args.anchor_kind
    anchor = normalize_project_anchor(anchor_kind, args.anchor)
    if anchor_kind == "filesystem" and not Path(anchor).is_dir():
        raise ValueError("A filesystem project anchor must be an existing directory")
    corpus_ids = [
        validate_record_id(value, "--corpus-id") for value in args.corpus_id
    ]
    with database(db_path) as connection:
        require_catalog_schema(connection)
        action, members = upsert_catalog_project(
            connection,
            project_id,
            label,
            access_boundary,
            anchor_kind,
            anchor,
            corpus_ids,
            args.replace_corpora,
        )
    harden_database_permissions(db_path)
    emit_json(
        {
            "database": str(db_path),
            "project_id": project_id,
            "access_boundary": access_boundary,
            "anchor_kind": anchor_kind,
            "anchor": anchor,
            "corpus_ids": members,
            "action": action,
        },
        args.pretty,
    )
    return 0

def command_catalog_project_resolve(args: argparse.Namespace) -> int:
    db_path = require_catalog_database(args.db)
    anchor_kind = args.anchor_kind
    anchor = normalize_project_anchor(anchor_kind, args.anchor)
    access_boundary = (
        required_research_text(args.access_boundary, "--access-boundary")
        if args.access_boundary
        else None
    )
    access_boundaries = [access_boundary] if access_boundary else []
    corpus_ids = [
        validate_record_id(value, "--corpus-id") for value in args.corpus_id
    ]
    if (args.label is not None or corpus_ids) and not args.create:
        raise ValueError("--label and --corpus-id require --create")
    with database(db_path) as connection:
        require_catalog_schema(connection)
        resolution = resolve_project_anchor(
            connection, anchor_kind, anchor, access_boundaries or None
        )
        if args.create:
            if access_boundary is None:
                raise ValueError("--create requires --access-boundary")
            if not corpus_ids:
                raise ValueError("--create requires at least one --corpus-id")
            if anchor_kind == "filesystem" and not Path(anchor).is_dir():
                raise ValueError(
                    "A filesystem project anchor must be an existing directory"
                )
            if resolution["ambiguous"]:
                raise ValueError(
                    "Project anchor is ambiguous; select an explicit project ID"
                )
            project_id_value = resolution.get("project_id")
            project_existed = project_id_value is not None
            if project_id_value is None:
                identity = json.dumps(
                    [access_boundary, anchor_kind, anchor],
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                project_id_value = (
                    "auto-"
                    + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
                )
            project_id = validate_record_id(str(project_id_value), "project_id")
            action, members = upsert_catalog_project(
                connection,
                project_id,
                optional_research_text(args.label, "--label"),
                access_boundary,
                anchor_kind,
                anchor,
                corpus_ids,
                False,
                not project_existed,
            )
            resolution = resolve_project_anchor(
                connection, anchor_kind, anchor, access_boundaries
            )
            resolution["action"] = action
            resolution["corpus_ids"] = members
    payload = {
        "database": str(db_path),
        "anchor_kind": anchor_kind,
        "anchor": anchor,
        **resolution,
    }
    if args.create:
        harden_database_permissions(db_path)
    emit_json(payload, args.pretty)
    return 0

def command_catalog_info(args: argparse.Namespace) -> int:
    db_path = require_catalog_database(args.db)
    if not 1 <= args.limit <= 100:
        raise ValueError("--limit must be between 1 and 100")
    if args.offset < 0:
        raise ValueError("--offset must be zero or greater")
    payload = catalog_status(db_path, live=args.live)
    corpora = payload["corpora"]
    if not isinstance(corpora, list):
        raise ValueError("Corpus catalog returned invalid entries")
    selected = corpora[args.offset : args.offset + args.limit]
    payload["corpora"] = selected
    payload["offset"] = args.offset
    payload["result_count"] = len(selected)
    payload["has_more"] = args.offset + len(selected) < len(corpora)
    if payload["has_more"]:
        payload["next_offset"] = args.offset + len(selected)
    emit_json(payload, args.pretty)
    return 0

def command_catalog_sync(args: argparse.Namespace) -> int:
    db_path = require_catalog_database(args.db)
    changed: list[str] = []
    unavailable: list[dict[str, str]] = []
    now = utc_now()
    with database(db_path) as connection:
        require_catalog_schema(connection)
        rows = connection.execute(
            "SELECT * FROM corpora WHERE enabled = 1 ORDER BY corpus_id"
        ).fetchall()
        for row in rows:
            item = catalog_entry_status(row)
            if item["adapter"] != "local-index":
                continue
            if not item["available"]:
                unavailable.append(
                    {"corpus_id": str(item["corpus_id"]), "error": str(item["error"])}
                )
                continue
            generation = str(item["current_generation"])
            if generation != row["generation"]:
                connection.execute(
                    "UPDATE corpora SET generation = ?, updated_at = ? WHERE corpus_id = ?",
                    (generation, now, row["corpus_id"]),
                )
                changed.append(str(row["corpus_id"]))
        if changed:
            connection.execute(
                "UPDATE catalog_state SET updated_at = ? WHERE singleton = 1", (now,)
            )
    if changed:
        harden_database_permissions(db_path)
    emit_json(
        {
            "database": str(db_path),
            "changed_corpora": changed,
            "unavailable": unavailable,
        },
        args.pretty,
    )
    return 0
