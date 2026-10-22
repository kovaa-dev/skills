from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .catalog_store import (
    catalog_entry_status,
    catalog_snapshot,
    project_scope_corpus_ids,
    require_catalog_database,
    require_catalog_schema,
)
from .common import (
    MAX_CATALOG_CORPORA,
    MAX_FILTER_TEXT,
    MAX_QUERY_TEXT,
    database,
    emit_json,
    harden_database_permissions,
    normalize_text,
    optional_research_text,
    required_record_id,
    required_research_text,
    sqlite3,
    utc_now,
    validate_record_id,
)
from .index import get_payload, source_hash
from .research_links import link_catalog_receipt_to_research
from .search import search_payload

def federated_receipt_id(
    query: str,
    mode: str,
    filters: dict[str, object],
    corpus_ids: list[str],
    offset: int,
) -> str:
    identity = json.dumps(
        [query, mode, filters, corpus_ids, offset],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"F-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:20]}"

def federated_reference(result: dict[str, object]) -> dict[str, object]:
    reference = {
        key: result[key]
        for key in (
            "corpus_id",
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
    return reference

def federated_dedupe_key(result: dict[str, object]) -> str:
    text = result.get("text")
    source_hash = result.get("source_hash")
    if isinstance(source_hash, str) and isinstance(text, str) and text.strip():
        return "source-text:" + source_hash + ":" + hashlib.sha256(
            normalize_text(text).encode("utf-8")
        ).hexdigest()
    return "locator:" + json.dumps(
        [
            result.get("corpus_id"),
            result.get("passage_id"),
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )

def lookup_federated_receipt(
    connection: sqlite3.Connection,
    receipt_id: str,
    query: str,
    mode: str,
    filters: dict[str, object],
    corpus_ids: list[str],
    fingerprint: str,
) -> dict[str, object] | None:
    row = connection.execute(
        "SELECT * FROM federated_receipts WHERE receipt_id = ?", (receipt_id,)
    ).fetchone()
    if row is None or row["catalog_fingerprint"] != fingerprint:
        return None
    if (
        row["query"] != query
        or row["mode"] != mode
        or json.loads(row["filters_json"]) != filters
        or json.loads(row["corpus_ids_json"]) != corpus_ids
    ):
        raise ValueError(
            "Federated receipt ID belongs to different search parameters; choose another ID"
        )
    item = dict(row)
    item["result_refs"] = json.loads(item.pop("result_refs_json"))
    item["member_receipts"] = json.loads(item.pop("member_receipts_json"))
    return item

def save_federated_receipt(
    connection: sqlite3.Connection,
    receipt_id: str,
    query: str,
    mode: str,
    filters: dict[str, object],
    corpus_ids: list[str],
    member_receipts: list[dict[str, object]],
    outcome: str,
    references: list[dict[str, object]],
    next_offset: int | None,
    fingerprint: str,
) -> None:
    now = utc_now()
    encoded_filters = json.dumps(
        filters, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    encoded_corpora = json.dumps(corpus_ids, ensure_ascii=False, separators=(",", ":"))
    encoded_members = json.dumps(
        member_receipts, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    encoded_references = json.dumps(
        references, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    existing = connection.execute(
        "SELECT query, mode, filters_json, corpus_ids_json "
        "FROM federated_receipts WHERE receipt_id = ?",
        (receipt_id,),
    ).fetchone()
    expected = (query, mode, encoded_filters, encoded_corpora)
    if existing is not None and tuple(existing) != expected:
        raise ValueError(
            "Federated receipt ID belongs to different search parameters; choose another ID"
        )
    connection.execute(
        """
        INSERT INTO federated_receipts(
            receipt_id, query, mode, filters_json, corpus_ids_json,
            member_receipts_json, outcome, result_refs_json, next_offset,
            catalog_fingerprint, created_at, updated_at, last_used_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(receipt_id) DO UPDATE SET
            member_receipts_json = excluded.member_receipts_json,
            outcome = excluded.outcome,
            result_refs_json = excluded.result_refs_json,
            next_offset = excluded.next_offset,
            catalog_fingerprint = excluded.catalog_fingerprint,
            updated_at = excluded.updated_at,
            last_used_at = excluded.last_used_at
        """,
        (
            receipt_id,
            query,
            mode,
            encoded_filters,
            encoded_corpora,
            encoded_members,
            outcome,
            encoded_references,
            next_offset,
            fingerprint,
            now,
            now,
            now,
        ),
    )

def command_catalog_search(args: argparse.Namespace) -> int:
    db_path = require_catalog_database(args.db)
    if (args.research_db is None) != (args.facet_id is None):
        raise ValueError("--research-db and --facet-id must be provided together")
    if args.read_only and args.research_db is not None:
        raise ValueError("--read-only cannot link a receipt to writable research state")
    if not 1 <= args.limit <= 12:
        raise ValueError("--limit must be between 1 and 12")
    if args.offset < 0 or args.offset + args.limit > 50:
        raise ValueError("--offset plus --limit must be between 1 and 50")
    if not 100 <= args.max_chars <= 8000:
        raise ValueError("--max-chars must be between 100 and 8000")
    if not 100 <= args.max_total_chars <= 100_000:
        raise ValueError("--max-total-chars must be between 100 and 100000")
    if not 4 <= args.snippet_tokens <= 64:
        raise ValueError("--snippet-tokens must be between 4 and 64")
    if not 0 <= args.max_per_source <= 50:
        raise ValueError("--max-per-source must be between 0 and 50")

    raw_query = required_research_text(args.query, "--query", MAX_QUERY_TEXT)
    normalized_filters = {
        key: optional_research_text(value, f"--{key}", MAX_FILTER_TEXT)
        for key, value in {
            "source": args.source,
            "page": args.page,
            "section": args.section,
            "version": args.version,
            "date": args.date,
        }.items()
    }

    corpus_ids = [validate_record_id(value, "--corpus-id") for value in args.corpus_id]
    project_ids = [
        validate_record_id(value, "--project-id") for value in args.project_id
    ]
    access_boundaries = [
        required_research_text(value, "--access-boundary")
        for value in args.access_boundary
    ]
    filters = {
        key: value
        for key, value in {
            **normalized_filters,
            "_limit": args.limit,
            "_dedupe_exact": args.dedupe_exact,
            "_max_per_source": args.max_per_source,
            "_offset": args.offset,
            "_allow_partial": args.allow_partial,
        }.items()
        if value is not None
    }
    with database(db_path, readonly=True) as connection:
        require_catalog_schema(connection)
        project_corpora = project_scope_corpus_ids(connection, project_ids)
        selected_corpus_ids = list(dict.fromkeys([*corpus_ids, *project_corpora]))
        entries, fingerprint, all_current = catalog_snapshot(
            connection,
            selected_corpus_ids or None,
            access_boundaries or None,
            MAX_CATALOG_CORPORA,
        )
        if not selected_corpus_ids and not access_boundaries:
            boundaries = {str(item["access_boundary"]) for item in entries}
            if len(boundaries) > 1:
                raise ValueError(
                    "Catalog spans multiple access boundaries; select --access-boundary "
                    "or explicit --corpus-id values"
                )
        unavailable = [
            {
                "corpus_id": str(item["corpus_id"]),
                "adapter": str(item["adapter"]),
                "reason": (
                    str(item.get("error"))
                    if not item.get("available")
                    else "External adapter must be searched by the authorized connector"
                ),
                "locator": str(item["locator"]),
            }
            for item in entries
            if item["adapter"] != "local-index" or not item.get("available")
        ]
        if unavailable and not args.allow_partial:
            names = ", ".join(item["corpus_id"] for item in unavailable)
            raise ValueError(
                f"Selected corpora require an external or unavailable adapter: {names}; "
                "search them through the authorized connector or pass --allow-partial"
            )
        selected_ids = [str(item["corpus_id"]) for item in entries]
        receipt_id = args.receipt_id or federated_receipt_id(
            raw_query, args.mode, filters, selected_ids, args.offset
        )
        receipt_id = validate_record_id(receipt_id, "--receipt-id")
        if not args.refresh and all_current:
            cached = lookup_federated_receipt(
                connection,
                receipt_id,
                raw_query,
                args.mode,
                filters,
                selected_ids,
                fingerprint,
            )
            if cached is not None:
                references = cached["result_refs"]
                if not isinstance(references, list):
                    raise ValueError("Cached federated references are not a list")
                payload: dict[str, object] = {
                    "query": raw_query,
                    "mode": args.mode,
                    "project_ids": list(dict.fromkeys(project_ids)),
                    "corpus_ids": selected_ids,
                    "offset": args.offset,
                    "result_count": len(references),
                    "characters": 0,
                    "has_more": cached["next_offset"] is not None,
                    "coverage_complete": not unavailable,
                    "results": references,
                    "unsearched_corpora": unavailable,
                    "receipt_hit": True,
                    "receipt_id": receipt_id,
                }
                if cached["next_offset"] is not None:
                    payload["next_offset"] = cached["next_offset"]
                if args.research_db is not None:
                    link_catalog_receipt_to_research(
                        args.research_db,
                        db_path,
                        receipt_id,
                        required_record_id(args.facet_id, "--facet-id"),
                    )
                emit_json(payload, args.pretty)
                return 0

    local_entries = [
        item
        for item in entries
        if item["adapter"] == "local-index" and item.get("available")
    ]
    candidate_limit = min(50, args.offset + args.limit)
    member_payloads: list[tuple[str, dict[str, object]]] = []
    member_receipts: list[dict[str, object]] = []
    for item in local_entries:
        namespace = argparse.Namespace(
            db=Path(str(item["index_path"])),
            query=raw_query,
            mode=args.mode,
            source=normalized_filters["source"],
            page=normalized_filters["page"],
            section=normalized_filters["section"],
            version=normalized_filters["version"],
            date=normalized_filters["date"],
            limit=candidate_limit,
            offset=0,
            max_chars=args.max_chars,
            max_total_chars=args.max_total_chars,
            snippet_tokens=args.snippet_tokens,
            receipts_db=Path(str(item["receipts_path"])),
            research_db=None,
            facet_id=None,
            receipt_id=None,
            refresh=args.refresh,
            read_only_receipts=args.read_only,
            dedupe_exact=args.dedupe_exact,
            max_per_source=args.max_per_source,
            pretty=False,
        )
        payload = search_payload(namespace)
        if not isinstance(payload, dict):
            raise RuntimeError("Internal search returned an invalid payload")
        member_payloads.append((str(item["corpus_id"]), payload))
        member_receipts.append(
            {
                "corpus_id": item["corpus_id"],
                "receipt_id": payload.get("receipt_id"),
                "generation": item.get("current_generation"),
                "has_more": bool(payload.get("has_more")),
                "next_offset": payload.get("next_offset"),
            }
        )

    interleaved: list[dict[str, object]] = []
    max_members = max(
        (len(payload.get("results", [])) for _, payload in member_payloads), default=0
    )
    seen: dict[str, int] = {}
    for rank in range(max_members):
        for corpus_id, payload in member_payloads:
            results = payload.get("results", [])
            if not isinstance(results, list) or rank >= len(results):
                continue
            raw = results[rank]
            if not isinstance(raw, dict):
                continue
            result = {"corpus_id": corpus_id, **raw}
            key = federated_dedupe_key(result)
            if args.dedupe_exact and key in seen:
                existing = interleaved[seen[key]]
                aliases = existing.setdefault("also_in", [])
                if isinstance(aliases, list) and len(aliases) < 5:
                    aliases.append(federated_reference(result))
                continue
            seen[key] = len(interleaved)
            interleaved.append(result)

    page = interleaved[args.offset : args.offset + args.limit]
    bounded: list[dict[str, object]] = []
    characters = 0
    output_truncated = False
    for result in page:
        encoded = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        if bounded and characters + len(encoded) > args.max_total_chars:
            output_truncated = True
            break
        if not bounded and len(encoded) > args.max_total_chars:
            raise ValueError("--max-total-chars is too small for one federated result")
        bounded.append(result)
        characters += len(encoded)
    any_member_more = any(bool(payload.get("has_more")) for _, payload in member_payloads)
    has_more = (
        args.offset + len(bounded) < len(interleaved)
        or any_member_more
        or output_truncated
    )
    coverage_complete = not unavailable
    references = [federated_reference(result) for result in bounded]
    outcome = (
        "incomplete"
        if has_more or not coverage_complete
        else ("results" if references else "no-material-result")
    )
    next_offset = args.offset + len(bounded) if has_more and bounded else None
    if not args.read_only:
        with database(db_path) as connection:
            require_catalog_schema(connection)
            save_federated_receipt(
                connection,
                receipt_id,
                raw_query,
                args.mode,
                filters,
                selected_ids,
                member_receipts,
                outcome,
                references,
                next_offset,
                fingerprint,
            )
        harden_database_permissions(db_path)
    if args.research_db is not None and not args.read_only:
        link_catalog_receipt_to_research(
            args.research_db,
            db_path,
            receipt_id,
            required_record_id(args.facet_id, "--facet-id"),
        )
    payload = {
        "query": raw_query,
        "mode": args.mode,
        "project_ids": list(dict.fromkeys(project_ids)),
        "corpus_ids": selected_ids,
        "offset": args.offset,
        "result_count": len(bounded),
        "characters": characters,
        "has_more": has_more,
        "coverage_complete": coverage_complete,
        "results": bounded,
        "unsearched_corpora": unavailable,
        "receipt_hit": False,
    }
    if args.read_only:
        payload["receipt_persisted"] = False
    else:
        payload["receipt_id"] = receipt_id
    if next_offset is not None:
        payload["next_offset"] = next_offset
    if output_truncated:
        payload["text_truncated"] = True
    emit_json(payload, args.pretty)
    return 0
def command_catalog_get(args: argparse.Namespace) -> int:
    db_path = require_catalog_database(args.db)
    if len(args.locators) > 50:
        raise ValueError("At most 50 federated locators may be requested")
    parsed: list[tuple[str, int]] = []
    for locator in args.locators:
        if "=" not in locator:
            raise ValueError("Federated locator must use CORPUS_ID=PASSAGE_ID")
        corpus_id, raw_passage = locator.rsplit("=", 1)
        corpus_id = validate_record_id(corpus_id, "corpus ID")
        try:
            passage_id = int(raw_passage)
        except ValueError as exc:
            raise ValueError(f"Invalid passage ID in locator: {locator}") from exc
        if passage_id < 1:
            raise ValueError(f"Invalid passage ID in locator: {locator}")
        parsed.append((corpus_id, passage_id))
    with database(db_path, readonly=True) as connection:
        require_catalog_schema(connection)
        requested = list(dict.fromkeys(corpus_id for corpus_id, _ in parsed))
        if len(requested) > MAX_CATALOG_CORPORA:
            raise ValueError(
                f"At most {MAX_CATALOG_CORPORA} corpora may be fetched at once"
            )
        placeholders = ",".join("?" for _ in requested)
        rows = connection.execute(
            f"SELECT * FROM corpora WHERE enabled = 1 AND corpus_id IN ({placeholders})",
            requested,
        ).fetchall()
    entries = {str(row["corpus_id"]): catalog_entry_status(row) for row in rows}
    missing = [corpus_id for corpus_id in requested if corpus_id not in entries]
    if missing:
        raise ValueError(f"Unknown or disabled corpus IDs: {', '.join(missing)}")
    by_corpus: dict[str, list[int]] = {}
    for corpus_id, passage_id in parsed:
        item = entries[corpus_id]
        if item["adapter"] != "local-index" or not item.get("available"):
            raise ValueError(
                f"Corpus {corpus_id} requires its external adapter; catalog-get is local only"
            )
        by_corpus.setdefault(corpus_id, []).append(passage_id)
    found: dict[tuple[str, int], dict[str, object]] = {}
    for corpus_id, passage_ids in by_corpus.items():
        namespace = argparse.Namespace(
            db=Path(str(entries[corpus_id]["index_path"])),
            passage_ids=passage_ids,
            limit=len(passage_ids),
            offset=0,
            start_char=0,
            max_chars=args.max_chars,
            max_total_chars=args.max_total_chars,
            pretty=False,
        )
        payload = get_payload(namespace)
        for result in payload.get("results", []):
            if isinstance(result, dict) and isinstance(result.get("passage_id"), int):
                found[(corpus_id, result["passage_id"])] = {
                    "corpus_id": corpus_id,
                    **result,
                }
    results: list[dict[str, object]] = []
    characters = 0
    output_truncated = False
    for key in parsed:
        result = found.get(key)
        if result is None:
            continue
        encoded = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        if results and characters + len(encoded) > args.max_total_chars:
            output_truncated = True
            break
        if not results and len(encoded) > args.max_total_chars:
            raise ValueError("--max-total-chars is too small for one federated passage")
        results.append(result)
        characters += len(encoded)
    emit_json(
        {
            "requested_count": len(parsed),
            "result_count": len(results),
            "characters": characters,
            "has_more": output_truncated,
            "not_found": [
                f"{corpus_id}={passage_id}"
                for corpus_id, passage_id in parsed
                if (corpus_id, passage_id) not in found
            ],
            "results": results,
        },
        args.pretty,
    )
    return 0
