from __future__ import annotations

import argparse
import json
import os
import tempfile
from contextlib import closing
from pathlib import Path

from .catalog_store import require_catalog_database
from .common import (
    CONFIDENCE_VALUES,
    CONFLICT_STATUSES,
    FACET_STATUSES,
    GAP_STATUSES,
    MAX_BATCH_RECORDS,
    MAX_RESEARCH_EXCERPT,
    RESEARCH_STATUSES,
    SHA256,
    connect,
    database,
    emit_json,
    file_signature,
    harden_database_permissions,
    load_bounded_json,
    optional_research_text,
    required_record_id,
    required_research_text,
    sqlite3,
    utc_now,
    validate_record_id,
)

from .research_store import (
    clip_research_record,
    decode_catalog_scope,
    normalized_id_array,
    require_facet,
    require_research_database,
    require_research_schema,
    research_record,
    summarize_research_record,
)

def record_value(
    args: argparse.Namespace,
    existing: sqlite3.Row | None,
    argument: str,
    column: str | None = None,
    default: object = None,
) -> object:
    supplied = getattr(args, argument)
    if supplied is not None:
        return supplied
    key = column or argument
    if existing is not None:
        return existing[key]
    return default

def write_research_record(
    connection: sqlite3.Connection, args: argparse.Namespace, now: str
) -> dict[str, str]:
    record_id = validate_record_id(args.record_id, "record_id")
    table_by_kind = {
        "facet": ("facets", "facet_id"),
        "evidence": ("evidence", "evidence_id"),
        "gap": ("gaps", "gap_id"),
        "conflict": ("conflicts", "conflict_id"),
    }
    table, id_column = table_by_kind[args.kind]
    existing = connection.execute(
        f"SELECT * FROM {table} WHERE {id_column} = ?", (record_id,)
    ).fetchone()
    action = "updated" if existing is not None else "created"

    if args.kind == "facet":
        question = required_research_text(
            record_value(args, existing, "question"), "--question"
        )
        status = str(record_value(args, existing, "status", default="open"))
        if status not in FACET_STATUSES:
            raise ValueError(f"Unsupported facet status: {status}")
        next_action = optional_research_text(
            record_value(args, existing, "next_action"), "--next-action"
        )
        connection.execute(
            """
            INSERT INTO facets(facet_id, question, status, next_action, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(facet_id) DO UPDATE SET
                question = excluded.question,
                status = excluded.status,
                next_action = excluded.next_action,
                updated_at = excluded.updated_at
            """,
            (record_id, question, status, next_action, now),
        )
    elif args.kind == "evidence":
        facet_id = required_record_id(
            record_value(args, existing, "facet", "facet_id"), "--facet"
        )
        require_facet(connection, facet_id)
        state = connection.execute(
            "SELECT * FROM research_state WHERE singleton = 1"
        ).fetchone()
        state_values = dict(state) if state is not None else None
        corpus_id_value = record_value(args, existing, "corpus_id")
        corpus_id = (
            validate_record_id(str(corpus_id_value), "--corpus-id")
            if corpus_id_value is not None
            else None
        )
        if state_values is not None:
            if state_values["binding_kind"] == "catalog":
                if corpus_id is None:
                    raise ValueError("--corpus-id is required for catalog-bound evidence")
                scoped_ids, scoped_boundaries, _ = decode_catalog_scope(
                    state_values["catalog_scope_json"]
                )
                if corpus_id not in scoped_ids:
                    raise ValueError("Evidence corpus is outside the research catalog scope")
                catalog_path = require_catalog_database(
                    Path(str(state_values["catalog_path"]))
                )
                with database(catalog_path, readonly=True) as catalog:
                    corpus = catalog.execute(
                        "SELECT access_boundary FROM corpora WHERE corpus_id = ? AND enabled = 1",
                        (corpus_id,),
                    ).fetchone()
                    if corpus is None:
                        raise ValueError(
                            f"Catalog has no enabled corpus with ID: {corpus_id}"
                        )
                    if scoped_boundaries and corpus["access_boundary"] not in scoped_boundaries:
                        raise ValueError("Evidence corpus is outside the research catalog scope")
            elif corpus_id is not None:
                raise ValueError("--corpus-id is only valid for catalog-bound evidence")
        finding = required_research_text(
            record_value(args, existing, "finding"), "--finding"
        )
        source = required_research_text(
            record_value(args, existing, "source"), "--source"
        )
        source_version = optional_research_text(
            record_value(args, existing, "source_version"), "--source-version"
        )
        source_hash = optional_research_text(
            record_value(args, existing, "source_hash"), "--source-hash", 64
        )
        if source_hash is not None and not SHA256.fullmatch(source_hash):
            raise ValueError("--source-hash must be 64 hexadecimal characters")
        page = optional_research_text(
            record_value(args, existing, "page"), "--page", 500
        )
        section = optional_research_text(
            record_value(args, existing, "section"), "--section", 1_000
        )
        passage_id = record_value(args, existing, "passage_id")
        if passage_id is not None and int(passage_id) < 0:
            raise ValueError("--passage-id must be zero or greater")
        excerpt = optional_research_text(
            record_value(args, existing, "excerpt"),
            "--excerpt",
            MAX_RESEARCH_EXCERPT,
        )
        interpretation = optional_research_text(
            record_value(args, existing, "interpretation"),
            "--interpretation",
            MAX_RESEARCH_EXCERPT,
        )
        confidence = record_value(args, existing, "confidence")
        if confidence is not None and confidence not in CONFIDENCE_VALUES:
            raise ValueError(f"Unsupported confidence: {confidence}")
        verified_raw = record_value(args, existing, "verified", default=0)
        if isinstance(verified_raw, str):
            if verified_raw not in {"true", "false"}:
                raise ValueError("--verified must be true or false")
            verified = 1 if verified_raw == "true" else 0
        else:
            verified = int(verified_raw)
            if verified not in {0, 1}:
                raise ValueError("--verified must be true or false")
        connection.execute(
            """
            INSERT INTO evidence(
                evidence_id, facet_id, corpus_id, finding, source, source_version,
                source_hash, page, section, passage_id, excerpt,
                interpretation, confidence, verified, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(evidence_id) DO UPDATE SET
                facet_id = excluded.facet_id,
                corpus_id = excluded.corpus_id,
                finding = excluded.finding,
                source = excluded.source,
                source_version = excluded.source_version,
                source_hash = excluded.source_hash,
                page = excluded.page,
                section = excluded.section,
                passage_id = excluded.passage_id,
                excerpt = excluded.excerpt,
                interpretation = excluded.interpretation,
                confidence = excluded.confidence,
                verified = excluded.verified,
                updated_at = excluded.updated_at
            """,
            (
                record_id,
                facet_id,
                corpus_id,
                finding,
                source,
                source_version,
                source_hash,
                page,
                section,
                passage_id,
                excerpt,
                interpretation,
                confidence,
                verified,
                now,
            ),
        )
    elif args.kind == "gap":
        facet_id = required_record_id(
            record_value(args, existing, "facet", "facet_id"), "--facet"
        )
        require_facet(connection, facet_id)
        description = required_research_text(
            record_value(args, existing, "description"), "--description"
        )
        status = str(record_value(args, existing, "status", default="open"))
        if status not in GAP_STATUSES:
            raise ValueError(f"Unsupported gap status: {status}")
        reason = optional_research_text(
            record_value(args, existing, "reason"), "--reason"
        )
        next_query = optional_research_text(
            record_value(args, existing, "next_query"), "--next-query", 2_000
        )
        connection.execute(
            """
            INSERT INTO gaps(
                gap_id, facet_id, description, status, reason, next_query, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(gap_id) DO UPDATE SET
                facet_id = excluded.facet_id,
                description = excluded.description,
                status = excluded.status,
                reason = excluded.reason,
                next_query = excluded.next_query,
                updated_at = excluded.updated_at
            """,
            (record_id, facet_id, description, status, reason, next_query, now),
        )
    else:
        facet_id = required_record_id(
            record_value(args, existing, "facet", "facet_id"), "--facet"
        )
        require_facet(connection, facet_id)
        description = required_research_text(
            record_value(args, existing, "description"), "--description"
        )
        status = str(record_value(args, existing, "status", default="open"))
        if status not in CONFLICT_STATUSES:
            raise ValueError(f"Unsupported conflict status: {status}")
        ids_raw = str(record_value(args, existing, "evidence_ids_json", default="[]"))
        evidence_ids_json = normalized_id_array(ids_raw, "--evidence-ids-json")
        for evidence_id in json.loads(evidence_ids_json):
            if connection.execute(
                "SELECT 1 FROM evidence WHERE evidence_id = ?", (evidence_id,)
            ).fetchone() is None:
                raise ValueError(f"Evidence does not exist: {evidence_id}")
        resolution = optional_research_text(
            record_value(args, existing, "resolution"), "--resolution"
        )
        connection.execute(
            """
            INSERT INTO conflicts(
                conflict_id, facet_id, evidence_ids_json, description,
                status, resolution, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(conflict_id) DO UPDATE SET
                facet_id = excluded.facet_id,
                evidence_ids_json = excluded.evidence_ids_json,
                description = excluded.description,
                status = excluded.status,
                resolution = excluded.resolution,
                updated_at = excluded.updated_at
            """,
            (
                record_id,
                facet_id,
                evidence_ids_json,
                description,
                status,
                resolution,
                now,
            ),
        )

    return {"kind": args.kind, "id": record_id, "action": action}

def command_research_put(args: argparse.Namespace) -> int:
    db_path = require_research_database(args.db)
    now = utc_now()
    with database(db_path) as connection:
        require_research_schema(connection)
        result = write_research_record(connection, args, now)
        connection.execute(
            "UPDATE research_state SET updated_at = ? WHERE singleton = 1", (now,)
        )
    harden_database_permissions(db_path)
    emit_json(
        {"database": str(db_path), **result},
        args.pretty,
    )
    return 0
RESEARCH_APPLY_FIELDS = {
    "facet",
    "corpus_id",
    "question",
    "status",
    "next_action",
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
    "description",
    "reason",
    "next_query",
    "evidence_ids",
    "evidence_ids_json",
    "resolution",
}

def research_put_namespace(db_path: Path, record: dict[str, object]) -> argparse.Namespace:
    unknown = set(record) - RESEARCH_APPLY_FIELDS - {"kind", "id"}
    if unknown:
        raise ValueError(
            "Research record has unsupported fields: " + ", ".join(sorted(unknown))
        )
    kind = record.get("kind")
    if kind not in {"facet", "evidence", "gap", "conflict"}:
        raise ValueError(f"Unsupported research record kind: {kind}")
    record_id = record.get("id")
    if not isinstance(record_id, str):
        raise ValueError("Research record requires a string id")
    if "evidence_ids" in record and "evidence_ids_json" in record:
        raise ValueError("Use evidence_ids or evidence_ids_json, not both")
    string_fields = RESEARCH_APPLY_FIELDS - {
        "evidence_ids",
        "passage_id",
        "verified",
    }
    for field in string_fields:
        if field in record and record[field] is not None and not isinstance(record[field], str):
            raise ValueError(f"Research record field {field} must be a string")
    for field in ("evidence_ids",):
        if field in record and not isinstance(record[field], list):
            raise ValueError(f"Research record {field} must be an array")
    for field in ("passage_id",):
        value = record.get(field)
        if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
            raise ValueError(f"Research record field {field} must be an integer")

    values = {field: None for field in RESEARCH_APPLY_FIELDS}
    values.update(record)
    for native, encoded in (("evidence_ids", "evidence_ids_json"),):
        if native in record:
            values[encoded] = json.dumps(
                record[native], ensure_ascii=False, separators=(",", ":")
            )
    verified = values.get("verified")
    if isinstance(verified, bool):
        values["verified"] = "true" if verified else "false"
    elif verified is not None and (
        not isinstance(verified, str) or verified not in {"true", "false"}
    ):
        raise ValueError("Research record verified must be true or false")
    return argparse.Namespace(
        db=db_path,
        kind=kind,
        record_id=record_id,
        pretty=False,
        **{field: values[field] for field in RESEARCH_APPLY_FIELDS},
    )

def command_research_apply(args: argparse.Namespace) -> int:
    db_path = require_research_database(args.db)
    raw = load_bounded_json(args.input, "Research delta file")
    if not isinstance(raw, dict):
        raise ValueError("Research delta must be a JSON object")
    unknown = set(raw) - {"state", "records"}
    if unknown:
        raise ValueError(
            "Research delta has unsupported fields: " + ", ".join(sorted(unknown))
        )
    state = raw.get("state")
    records = raw.get("records", [])
    if state is not None and not isinstance(state, dict):
        raise ValueError("Research delta state must be an object")
    if not isinstance(records, list):
        raise ValueError("Research delta records must be an array")
    if len(records) > MAX_BATCH_RECORDS:
        raise ValueError(f"At most {MAX_BATCH_RECORDS} records are allowed")
    if state is None and not records:
        raise ValueError("Research delta contains no changes")
    if isinstance(state, dict):
        unknown_state = set(state) - {"scope", "status", "next_action"}
        if unknown_state:
            raise ValueError(
                "Research state has unsupported fields: "
                + ", ".join(sorted(unknown_state))
            )
        if not state:
            raise ValueError("Research delta state contains no changes")
        for field, value in state.items():
            if value is not None and not isinstance(value, str):
                raise ValueError(f"Research state field {field} must be a string")
    normalized_records: list[argparse.Namespace] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Research record {index} must be an object")
        normalized_records.append(research_put_namespace(db_path, record))

    original_signature = file_signature(db_path)
    temporary_path: Path | None = None
    actions: list[dict[str, object]] = []
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{db_path.name}.", suffix=".tmp", dir=db_path.parent, delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
        with closing(connect(db_path)) as source, closing(connect(temporary_path)) as target:
            require_research_schema(source)
            source.backup(target)
        now = utc_now()
        with database(temporary_path) as connection:
            require_research_schema(connection)
            for namespace in normalized_records:
                actions.append(write_research_record(connection, namespace, now))
            if isinstance(state, dict):
                updates: list[str] = []
                values: list[object] = []
                if state.get("scope") is not None:
                    updates.append("scope = ?")
                    values.append(required_research_text(state["scope"], "scope"))
                if state.get("status") is not None:
                    if state["status"] not in RESEARCH_STATUSES:
                        raise ValueError(
                            f"Unsupported research status: {state['status']}"
                        )
                    updates.append("status = ?")
                    values.append(state["status"])
                if state.get("next_action") is not None:
                    updates.append("next_action = ?")
                    values.append(
                        optional_research_text(state["next_action"], "next_action")
                    )
                if not updates:
                    raise ValueError(
                        "Research state requires scope, status, or next_action"
                    )
                connection.execute(
                    f"UPDATE research_state SET {', '.join(updates)}, updated_at = ? "
                    "WHERE singleton = 1",
                    [*values, now],
                )
            elif normalized_records:
                connection.execute(
                    "UPDATE research_state SET updated_at = ? WHERE singleton = 1",
                    (now,),
                )
        if file_signature(db_path) != original_signature:
            raise ValueError("Research database changed during batch apply; retry the delta")
        harden_database_permissions(temporary_path)
        os.replace(temporary_path, db_path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    emit_json(
        {
            "database": str(db_path),
            "state_updated": state is not None,
            "records_applied": len(actions),
            "actions": actions,
        },
        args.pretty,
    )
    return 0
def command_research_list(args: argparse.Namespace) -> int:
    db_path = require_research_database(args.db)
    if not 1 <= args.limit <= 100:
        raise ValueError("--limit must be between 1 and 100")
    if args.offset < 0:
        raise ValueError("--offset must be zero or greater")
    if not 100 <= args.max_chars <= 8_000:
        raise ValueError("--max-chars must be between 100 and 8000")
    if not 1_000 <= args.max_total_chars <= 100_000:
        raise ValueError("--max-total-chars must be between 1000 and 100000")
    if args.record_id is not None and args.offset:
        raise ValueError("--offset cannot be combined with --id")
    summary = args.summary if args.summary is not None else args.kind == "evidence"
    definitions = {
        "facets": ("facets", "facet_id", "status"),
        "evidence": ("evidence", "evidence_id", "confidence"),
        "gaps": ("gaps", "gap_id", "status"),
        "conflicts": ("conflicts", "conflict_id", "status"),
    }
    table, order_column, status_column = definitions[args.kind]
    conditions: list[str] = []
    parameters: list[object] = []
    if args.facet:
        conditions.append("facet_id = ?")
        parameters.append(validate_record_id(args.facet, "--facet"))
    if args.status:
        conditions.append(f"{status_column} = ?")
        parameters.append(args.status)
    if args.record_id:
        conditions.append(f"{order_column} = ?")
        parameters.append(validate_record_id(args.record_id, "--id"))
    with database(db_path, readonly=True) as connection:
        require_research_schema(connection)
        state = connection.execute(
            "SELECT * FROM research_state WHERE singleton = 1"
        ).fetchone()
        if state is None:
            raise ValueError("Research database has no state row")
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        row_limit = 1 if args.record_id else args.limit
        parameters.extend((row_limit + 1, args.offset))
        rows = connection.execute(
            f"SELECT * FROM {table} {where} ORDER BY {order_column} LIMIT ? OFFSET ?",
            parameters,
        ).fetchall()

    candidates = rows[:row_limit]
    records: list[dict[str, object]] = []
    characters = 0
    output_truncated = False
    for row in candidates:
        item = clip_research_record(research_record(row), args.max_chars)
        if summary:
            item = summarize_research_record(args.kind, item)
        output_truncated = output_truncated or bool(item.get("truncated_fields"))
        encoded = json.dumps(item, ensure_ascii=False, separators=(",", ":"))
        if records and characters + len(encoded) > args.max_total_chars:
            output_truncated = True
            break
        if not records and len(encoded) > args.max_total_chars:
            item = clip_research_record(item, 128)
            encoded = json.dumps(item, ensure_ascii=False, separators=(",", ":"))
            if len(encoded) > args.max_total_chars:
                raise ValueError("--max-total-chars is too small for one record")
            output_truncated = True
        records.append(item)
        characters += len(encoded)

    has_more = len(rows) > len(records)
    payload: dict[str, object] = {
        "database": str(db_path),
        "kind": args.kind,
        "id": args.record_id,
        "facet": args.facet,
        "status": args.status,
        "summary": summary,
        "offset": args.offset,
        "result_count": len(records),
        "characters": characters,
        "output_truncated": output_truncated,
        "has_more": has_more,
        "records": records,
    }
    if has_more:
        payload["next_offset"] = args.offset + len(records)
    emit_json(payload, args.pretty)
    return 0
