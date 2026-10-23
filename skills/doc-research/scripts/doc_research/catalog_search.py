from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Iterator
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
    clip_text,
    database,
    emit_json,
    harden_database_permissions,
    optional_research_text,
    required_record_id,
    required_research_text,
    sqlite3,
    utc_now,
    validate_record_id,
)
from .index import get_payload, literal_query, prefix_query, require_current_schema, result_item, source_hash
from .research_links import link_catalog_receipt_to_research
from .search import resolved_query_mode, search_payload


def hydrate_federated_references(
    references: list[dict[str, object]],
    entries: list[dict[str, object]],
    args: argparse.Namespace,
    raw_query: str,
) -> list[dict[str, object]]:
    """Reconstruct snippets from current indexes without repeating candidate selection."""
    mode = resolved_query_mode(raw_query, args.mode)
    query = literal_query(raw_query) if mode == "literal" else (
        prefix_query(raw_query) if mode == "prefix" else raw_query
    )
    by_corpus = {str(entry["corpus_id"]): entry for entry in entries}
    found: dict[tuple[str, int], dict[str, object]] = {}
    requested: dict[str, list[int]] = {}
    for reference in references:
        corpus_id, passage_id = reference.get("corpus_id"), reference.get("passage_id")
        if corpus_id not in by_corpus or not isinstance(passage_id, int):
            raise ValueError("Cached federated reference is outside the selected catalog scope")
        requested.setdefault(str(corpus_id), []).append(passage_id)
    for corpus_id, passage_ids in requested.items():
        with database(Path(str(by_corpus[corpus_id]["index_path"])), readonly=True) as connection:
            require_current_schema(connection)
            rows = connection.execute(
                f"""SELECT rowid AS passage_id,
                       bm25(chunks, 0.0, 3.0, 0.0, 0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 2.0, 1.0) AS score,
                       source_path, source, source_hash, page, section, version, date,
                       line_start, line_end,
                       snippet(chunks, 10, '', '', ' … ', {args.snippet_tokens}) AS text
                FROM chunks WHERE chunks MATCH ? AND rowid IN (
                    {','.join('?' for _ in passage_ids)})""",
                [query, *passage_ids],
            ).fetchall()
            for row in rows:
                text = str(row["text"] or "")
                visible, truncated = clip_text(text, args.max_chars)
                found[(corpus_id, row["passage_id"])] = {
                    "corpus_id": corpus_id,
                    **result_item(row, visible, text_truncated=truncated),
                }
    results = []
    for reference in references:
        key = (str(reference["corpus_id"]), int(reference["passage_id"]))
        result = found.get(key)
        if result is None or result.get("source_hash") != reference.get("source_hash"):
            raise ValueError("Cached federated reference is stale for its index")
        if isinstance(reference.get("also_in"), list):
            result["also_in"] = reference["also_in"]
        results.append(result)
    return results


def bound_federated_results(
    results: list[dict[str, object]], max_total_chars: int
) -> tuple[list[dict[str, object]], int, bool]:
    bounded = []
    characters = 0
    for result in results:
        size = len(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        if characters + size > max_total_chars:
            if not bounded:
                raise ValueError("--max-total-chars is too small for one federated result")
            return bounded, characters, True
        bounded.append(result)
        characters += size
    return bounded, characters, False

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
    content_hash = result.pop("_content_hash", None)
    source_hash = result.get("source_hash")
    if isinstance(source_hash, str) and isinstance(content_hash, str):
        return "source-content:" + source_hash + ":" + content_hash
    return "locator:" + json.dumps(
        [
            result.get("corpus_id"),
            result.get("passage_id"),
        ],
        ensure_ascii=False,
        separators=(",", ":"),
    )


def current_dedupe_filters(filters: dict[str, object]) -> dict[str, object]:
    if filters.get("_dedupe_exact") and "_dedupe_identity" not in filters:
        return {**filters, "_dedupe_identity": "full-content-v1"}
    return filters


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
    stored_filters = json.loads(row["filters_json"])
    if (
        row["query"] != query
        or row["mode"] != mode
        or current_dedupe_filters(stored_filters) != filters
        or json.loads(row["corpus_ids_json"]) != corpus_ids
    ):
        raise ValueError(
            "Federated receipt ID belongs to different search parameters; choose another ID"
        )
    if stored_filters != filters:
        # Snippet-based selections can omit distinct passages; recompute them.
        return None
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
    if existing is not None and (
        existing["query"] != query
        or existing["mode"] != mode
        or current_dedupe_filters(json.loads(existing["filters_json"])) != filters
        or existing["corpus_ids_json"] != encoded_corpora
    ):
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
            filters_json = excluded.filters_json,
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
    if args.offset < 0:
        raise ValueError("--offset must be zero or greater")
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
            "_dedupe_identity": "full-content-v1" if args.dedupe_exact else None,
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
                results, characters, output_truncated = bound_federated_results(
                    hydrate_federated_references(references, entries, args, raw_query),
                    args.max_total_chars,
                )
                next_offset = (
                    args.offset + len(results) if output_truncated else cached["next_offset"]
                )
                payload: dict[str, object] = {
                    "query": raw_query,
                    "mode": args.mode,
                    "project_ids": list(dict.fromkeys(project_ids)),
                    "corpus_ids": selected_ids,
                    "offset": args.offset,
                    "result_count": len(results),
                    "characters": characters,
                    "has_more": next_offset is not None,
                    "coverage_complete": not unavailable,
                    "results": results,
                    "unsearched_corpora": unavailable,
                    "receipt_hit": True,
                    "receipt_id": receipt_id,
                }
                if next_offset is not None:
                    payload["next_offset"] = next_offset
                if output_truncated:
                    payload["text_truncated"] = True
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
    candidate_limit = min(50, args.offset + args.limit + 1)
    member_receipts: list[dict[str, object]] = []

    def member_results(item: dict[str, object]) -> Iterator[dict[str, object]]:
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
            max_total_chars=min(args.max_total_chars, 40_000),
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
        member_receipt: dict[str, object] = {}
        member_receipts.append(member_receipt)
        while True:
            payload = search_payload(namespace, include_content_hash=args.dedupe_exact)
            member_receipt.update(
                {
                    "corpus_id": item["corpus_id"],
                    "receipt_id": payload.get("receipt_id"),
                    "generation": item.get("current_generation"),
                    "has_more": bool(payload.get("has_more")),
                    "next_offset": payload.get("next_offset"),
                }
            )
            for result in payload.get("results", []):
                if isinstance(result, dict):
                    yield {"corpus_id": str(item["corpus_id"]), **result}
            if not payload.get("has_more"):
                return
            next_offset = payload.get("next_offset")
            if not isinstance(next_offset, int) or next_offset <= namespace.offset:
                raise ValueError("Member search returned a non-advancing continuation")
            namespace.offset = next_offset

    page: list[dict[str, object]] = []
    seen: dict[str, dict[str, object] | None] = {}
    streams = [member_results(item) for item in local_entries]
    position = 0
    while streams and len(page) <= args.limit:
        active = []
        for stream in streams:
            result = next(stream, None)
            if result is None:
                continue
            active.append(stream)
            key = federated_dedupe_key(result)
            if args.dedupe_exact and key in seen:
                existing = seen[key]
                if existing is not None:
                    aliases = existing.setdefault("also_in", [])
                    if isinstance(aliases, list) and len(aliases) < 5:
                        aliases.append(federated_reference(result))
                continue
            if args.dedupe_exact:
                seen[key] = result if position >= args.offset else None
            if position >= args.offset:
                page.append(result)
            position += 1
        streams = active

    more_results = len(page) > args.limit
    page = page[:args.limit]
    bounded, characters, output_truncated = bound_federated_results(page, args.max_total_chars)
    has_more = more_results or output_truncated
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
    offset = getattr(args, "offset", 0)
    start_char = getattr(args, "start_char", 0)
    if offset < 0 or start_char < 0:
        raise ValueError("--offset and --start-char must be zero or greater")
    if not 100 <= args.max_chars <= 8000:
        raise ValueError("--max-chars must be between 100 and 8000")
    if not 100 <= args.max_total_chars <= 100_000:
        raise ValueError("--max-total-chars must be between 100 and 100000")
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
    for corpus_id, passage_id in parsed:
        item = entries[corpus_id]
        if item["adapter"] != "local-index" or not item.get("available"):
            raise ValueError(
                f"Corpus {corpus_id} requires its external adapter; catalog-get is local only"
            )

    results: list[dict[str, object]] = []
    not_found: list[str] = []
    characters = 0
    next_offset: int | None = None
    next_start_char = 0
    for position in range(offset, len(parsed)):
        corpus_id, passage_id = parsed[position]
        namespace = argparse.Namespace(
            db=Path(str(entries[corpus_id]["index_path"])),
            passage_ids=[passage_id],
            limit=1,
            offset=0,
            start_char=start_char if position == offset else 0,
            max_chars=args.max_chars,
            max_total_chars=min(args.max_total_chars, 40_000),
            pretty=False,
        )
        payload = get_payload(namespace)
        if passage_id in payload.get("not_found", []):
            not_found.append(f"{corpus_id}={passage_id}")
            continue
        result = {"corpus_id": corpus_id, **payload["results"][0]}
        encoded = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
        if results and characters + len(encoded) > args.max_total_chars:
            next_offset = position
            next_start_char = namespace.start_char
            break
        if not results and len(encoded) > args.max_total_chars:
            raise ValueError("--max-total-chars is too small for one federated passage")
        results.append(result)
        characters += len(encoded)
        if payload.get("has_more"):
            next_offset = position
            next_start_char = int(payload["next_start_char"])
            break
    response: dict[str, object] = {
        "requested_count": len(parsed),
        "offset": offset,
        "start_char": start_char,
        "result_count": len(results),
        "characters": characters,
        "has_more": next_offset is not None,
        "not_found": not_found,
        "results": results,
    }
    if next_offset is not None:
        response["next_offset"] = next_offset
        response["next_start_char"] = next_start_char
    emit_json(response, args.pretty)
    return 0
