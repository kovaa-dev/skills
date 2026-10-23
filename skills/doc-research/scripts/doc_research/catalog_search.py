from __future__ import annotations

import argparse
import base64
import copy
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
from .index import get_payload, index_fingerprint, literal_query, prefix_query, require_current_schema, result_item
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
            if index_fingerprint(connection) != by_corpus[corpus_id]["current_generation"]:
                raise ValueError("Cached federated index generation changed; restart the search")
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
        for field in ("index_fingerprint", "locator"):
            if field in reference:
                result[field] = reference[field]
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
            "index_fingerprint",
            "locator",
        )
        if result.get(key) is not None
    }
    aliases = result.get("also_in")
    if isinstance(aliases, list):
        reference["also_in"] = aliases[:5]
    return reference


def continuation_identity(query: str, mode: str, filters: dict[str, object], ids: list[str]) -> str:
    stable = {key: value for key, value in filters.items() if key not in {"_offset", "_limit"}}
    return hashlib.sha256(json.dumps([query, mode, stable, ids], sort_keys=True).encode()).hexdigest()


def encode_continuation(state: dict[str, object]) -> str:
    raw = json.dumps(state, separators=(",", ":"), sort_keys=True).encode()
    if len(raw) > 750_000:
        raise ValueError("Catalog continuation exceeds its bounded state; narrow the search scope")
    return base64.urlsafe_b64encode(raw).decode()


def decode_continuation(token: str, identity: str, fingerprint: str, offset: int | None) -> dict[str, object]:
    try:
        if len(token) > 1_000_000:
            raise ValueError("oversized token")
        state = json.loads(base64.b64decode(token, altchars=b"-_", validate=True))
        if state["identity"] != identity or state["fingerprint"] != fingerprint:
            raise ValueError("search parameters or catalog generation changed")
        if type(state["offset"]) is not int or not 0 <= state["offset"] < 2**63:
            raise ValueError("invalid output position")
        if offset is not None and state["offset"] != offset:
            raise ValueError("offset does not match continuation")
        if not isinstance(state["members"], dict) or not isinstance(state["seen"], list):
            raise ValueError("invalid member state")
        for member in state["members"].values():
            if (type(member["offset"]) is not int or not 0 <= member["offset"] < 2**63
                    or not isinstance(member["done"], bool)):
                raise ValueError("invalid member position")
        if not all(isinstance(value, str) for value in state["seen"]):
            raise ValueError("invalid dedupe state")
        if not isinstance(state["turn"], int) or state["turn"] < 0:
            raise ValueError("invalid member turn")
        if not isinstance(state["sources"], dict) or not all(
            isinstance(value, int) and value >= 0 for value in state["sources"].values()
        ):
            raise ValueError("invalid source counts")
        return state
    except (ValueError, TypeError, KeyError) as exc:
        raise ValueError(f"Invalid catalog continuation: {exc}; restart the search") from exc


def position_checkpoint(state: dict[str, object]) -> dict[str, object]:
    return {"members": copy.deepcopy(state["members"]), "turn": state["turn"]}


def receipt_revision(metadata: dict[str, object], references: list[dict[str, object]]) -> str:
    value = [metadata["base"], metadata["final"], references]
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]


def load_continuation(
    connection: sqlite3.Connection, token: str, identity: str, fingerprint: str,
    offset: int | None,
) -> dict[str, object]:
    if not token.startswith("c:"):
        decoded = decode_continuation(token, identity, fingerprint, offset)
        decoded.pop("parent", None)
        return decoded
    original_token = token
    selected_state = None
    history: list[list[dict[str, object]]] = []
    visited: set[str] = set()
    try:
        while token:
            if token in visited or len(visited) >= 10_000:
                raise ValueError("invalid or oversized receipt chain")
            visited.add(token)
            prefix, receipt_id, count_value, revision = token.split(":")
            if prefix != "c":
                raise ValueError("invalid receipt reference")
            validate_record_id(receipt_id, "continuation receipt")
            row = connection.execute(
                "SELECT member_receipts_json, result_refs_json, catalog_fingerprint "
                "FROM federated_receipts WHERE receipt_id = ?", (receipt_id,),
            ).fetchone()
            if row is None or row["catalog_fingerprint"] != fingerprint:
                raise ValueError("receipt missing or catalog generation changed")
            metadata = json.loads(row["member_receipts_json"])[0]
            references = json.loads(row["result_refs_json"])
            if receipt_revision(metadata, references) != revision:
                raise ValueError("receipt changed; restart the search")
            base = metadata["base"]
            if base["identity"] != identity or base["fingerprint"] != fingerprint:
                raise ValueError("search parameters or catalog generation changed")
            count = len(references) if count_value == "end" else int(count_value)
            if not 0 <= count <= len(references):
                raise ValueError("invalid receipt result position")
            checkpoint = (metadata["final"] if count_value == "end" else
                          references[count - 1]["_checkpoint"] if count else base)
            current_offset = base["offset"] + count
            if selected_state is None:
                selected_state = {**base, **checkpoint, "offset": current_offset}
            elif child_offset != current_offset:
                raise ValueError("receipt chain position changed")
            history.append(references[:count])
            child_offset = base["offset"]
            token = base.get("parent")
        assert selected_state is not None
        seen = set(base.get("seen", []))
        sources = dict(base.get("sources", {}))
        for references in reversed(history):
            for reference in references:
                if reference.get("_dedupe_key"):
                    seen.add(reference["_dedupe_key"])
                if reference.get("_source_key"):
                    key = reference["_source_key"]
                    sources[key] = sources.get(key, 0) + 1
        selected_state.update(seen=[], sources={})
        selected_state.pop("parent", None)
        # Apply the same bounded/type validation to state restored from receipts.
        validated = decode_continuation(encode_continuation(selected_state), identity, fingerprint, offset)
        validated.update(seen=sorted(seen), sources=sources)
        validated["parent"] = original_token
        return validated
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        raise ValueError(f"Invalid catalog continuation: {exc}; restart the search") from exc


def bound_catalog_response(payload: dict[str, object], args: argparse.Namespace, cursor) -> None:
    """Account for the complete wire envelope, including continuation state."""
    results = payload["results"]
    original_count = len(results)
    while True:
        payload["result_count"] = len(results)
        payload["characters"] = sum(len(json.dumps(item, ensure_ascii=False, separators=(",", ":"))) for item in results)
        if len(results) < original_count:
            payload["has_more"] = True
            payload["text_truncated"] = True
        if payload["has_more"]:
            payload["next_offset"] = args.offset + len(results)
            payload["next_continuation"] = cursor(len(results), len(results) == original_count)
        options = {"indent": 2} if args.pretty else {"separators": (",", ":")}
        if len(json.dumps(payload, ensure_ascii=False, **options)) + 1 <= args.max_total_chars:
            return
        if len(results) <= 1:
            raise ValueError("--max-total-chars is too small for a catalog result/continuation envelope; increase it or narrow the search")
        results.pop()

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
        identity = continuation_identity(raw_query, args.mode, filters, selected_ids)
        token = getattr(args, "continuation", None)
        continuation = load_continuation(connection, token, identity, fingerprint, args.offset or None) if token else None
        if continuation is not None:
            args.offset = continuation["offset"]
            filters["_offset"] = args.offset
        if args.offset and continuation is None:
            # Existing receipts own continuation; an absent checkpoint must not trigger
            # an unbounded replay of all preceding corpus candidates.
            for previous in connection.execute(
                "SELECT filters_json, member_receipts_json FROM federated_receipts "
                "WHERE query = ? AND mode = ? AND corpus_ids_json = ? AND catalog_fingerprint = ? "
                "AND next_offset = ? ORDER BY updated_at DESC",
                (raw_query, args.mode, json.dumps(selected_ids, separators=(",", ":")),
                 fingerprint, args.offset),
            ):
                if continuation_identity(raw_query, args.mode, json.loads(previous["filters_json"]), selected_ids) != identity:
                    continue
                members = json.loads(previous["member_receipts_json"])
                saved_token = members[0].get("next_continuation") if members else None
                if saved_token:
                    continuation = load_continuation(connection, saved_token, identity, fingerprint, args.offset)
                    break
        if continuation is not None and args.receipt_id is not None:
            raise ValueError("Omit --receipt-id when continuing; each page owns a separate receipt")
        cursor_identity = token or (continuation.get("parent") if continuation else None)
        receipt_id = args.receipt_id or federated_receipt_id(
            raw_query, args.mode, {**filters, **({"_cursor": cursor_identity} if cursor_identity else {})}, selected_ids, args.offset
        )
        receipt_id = validate_record_id(receipt_id, "--receipt-id")
        if not args.refresh and all_current and token is None:
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
                results = hydrate_federated_references(references, entries, args, raw_query)
                next_offset = cached["next_offset"]
                payload: dict[str, object] = {
                    "query": raw_query,
                    "mode": args.mode,
                    "project_ids": list(dict.fromkeys(project_ids)),
                    "corpus_ids": selected_ids,
                    "offset": args.offset,
                    "result_count": len(results),
                    "has_more": next_offset is not None,
                    "coverage_complete": not unavailable,
                    "results": results,
                    "unsearched_corpora": unavailable,
                    "receipt_hit": True,
                    "receipt_id": receipt_id,
                }
                bound_catalog_response(
                    payload, args,
                    lambda count, full: f"c:{receipt_id}:{'end' if full else count}:" + receipt_revision(cached["member_receipts"][0], references),
                )
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
    if args.offset and continuation is None:
        raise ValueError("No current catalog continuation for --offset; use --continuation or restart at offset 0")
    state = continuation or {
        "identity": identity, "fingerprint": fingerprint, "offset": args.offset,
        "turn": 0, "seen": [], "sources": {},
        "members": {str(item["corpus_id"]): {"offset": 0, "done": False} for item in local_entries},
    }
    if set(state["members"]) != {str(item["corpus_id"]) for item in local_entries}:
        raise ValueError("Catalog continuation members changed; restart the search")
    initial_state = copy.deepcopy(state)
    page_base = copy.deepcopy(state)
    if page_base.get("parent"):
        page_base.pop("seen", None)
        page_base.pop("sources", None)
    seen = set(state["seen"])
    buffers: dict[str, list[dict[str, object]]] = {}
    buffer_more: dict[str, bool] = {}
    member_receipts: list[dict[str, object]] = [{}]
    candidate_limit = min(50, args.limit + 1)

    def member_result(item: dict[str, object]) -> dict[str, object] | None:
        corpus_id = str(item["corpus_id"])
        position = state["members"][corpus_id]
        if position["done"]:
            return None
        if buffers.get(corpus_id):
            result = buffers[corpus_id].pop(0)
            position["offset"] += 1
            if not buffers[corpus_id] and not buffer_more[corpus_id]:
                position["done"] = True
            return result
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
            offset=position["offset"],
            max_chars=args.max_chars,
            max_total_chars=40_000,
            snippet_tokens=args.snippet_tokens,
            receipts_db=Path(str(item["receipts_path"])),
            research_db=None,
            facet_id=None,
            receipt_id=None,
            refresh=args.refresh,
            read_only_receipts=args.read_only,
            dedupe_exact=False,
            max_per_source=0,
            expected_fingerprint=item.get("current_generation"),
            pretty=False,
        )
        payload = search_payload(namespace, include_content_hash=args.dedupe_exact)
        member_receipts.append({"corpus_id": corpus_id, "receipt_id": payload.get("receipt_id"),
                                "generation": item.get("current_generation")})
        generation = str(item["current_generation"])
        buffers[corpus_id] = [
            {"corpus_id": corpus_id, **result, "index_fingerprint": generation,
             "locator": f"{corpus_id}@{generation}={result['passage_id']}"}
            for result in payload.get("results", [])
        ]
        buffer_more[corpus_id] = bool(payload.get("has_more"))
        if not buffers[corpus_id]:
            if buffer_more[corpus_id]:
                raise ValueError("Member search returned a non-advancing continuation")
            position["done"] = True
            return None
        return member_result(item)

    page: list[dict[str, object]] = []
    checkpoints: list[dict[str, object]] = []
    page_keys: list[str | None] = []
    source_keys: list[str | None] = []
    page_by_key: dict[str, dict[str, object]] = {}
    candidates = 0
    while local_entries and len(page) < args.limit and candidates < 50 * len(local_entries):
        if all(member["done"] for member in state["members"].values()):
            break
        item = local_entries[state["turn"] % len(local_entries)]
        state["turn"] = (state["turn"] + 1) % len(local_entries)
        result = member_result(item)
        if result is None:
            continue
        candidates += 1
        key = federated_dedupe_key(result)
        if args.dedupe_exact and key in seen:
            existing = page_by_key.get(key)
            if existing is not None:
                aliases = existing.setdefault("also_in", [])
                if len(aliases) < 5:
                    aliases.append(federated_reference(result))
            continue
        source_key = json.dumps([result["corpus_id"], result.get("source")])
        source_count = state["sources"].get(source_key, 0)
        if args.max_per_source and source_count >= args.max_per_source:
            continue
        if args.max_per_source:
            state["sources"][source_key] = source_count + 1
        if args.dedupe_exact:
            seen.add(key)
            state["seen"] = sorted(seen)
            page_by_key[key] = result
        state["offset"] += 1
        page.append(result)
        checkpoints.append(position_checkpoint(state))
        page_keys.append(key if args.dedupe_exact else None)
        source_keys.append(source_key if args.max_per_source else None)

    more_results = any(not member["done"] for member in state["members"].values())
    coverage_complete = not unavailable
    all_references = [federated_reference(result) for result in page]
    for reference, checkpoint, key, source_key in zip(all_references, checkpoints, page_keys, source_keys):
        reference.update(_checkpoint=checkpoint, _dedupe_key=key, _source_key=source_key)

    def page_metadata(count: int) -> dict[str, object]:
        final = position_checkpoint(state) if count == len(page) else checkpoints[count - 1]
        return {"base": page_base, "final": final}

    def output_cursor(count: int, full: bool) -> str:
        if not args.read_only:
            return f"c:{receipt_id}:end:" + receipt_revision(page_metadata(count), all_references[:count])
        selected = copy.deepcopy(state if full else initial_state)
        selected.pop("parent", None)
        if not full:
            selected.update(checkpoints[count - 1])
            selected["offset"] = args.offset + count
            selected["seen"] = sorted(set(selected.get("seen", [])) | {key for key in page_keys[:count] if key})
            sources = selected.setdefault("sources", {})
            for key in source_keys[:count]:
                if key:
                    sources[key] = sources.get(key, 0) + 1
        return encode_continuation(selected)

    payload = {
        "query": raw_query, "mode": args.mode,
        "project_ids": list(dict.fromkeys(project_ids)), "corpus_ids": selected_ids,
        "offset": args.offset, "has_more": more_results,
        "coverage_complete": coverage_complete, "results": list(page),
        "unsearched_corpora": unavailable, "receipt_hit": False,
        **({"receipt_persisted": False} if args.read_only else {"receipt_id": receipt_id}),
    }
    bound_catalog_response(payload, args, output_cursor)
    bounded = payload["results"]
    references = all_references[:len(bounded)]
    member_receipts[0] = {**page_metadata(len(bounded)), "next_continuation": payload.get("next_continuation")}
    next_offset = payload.get("next_offset")
    outcome = "incomplete" if payload["has_more"] or not coverage_complete else ("results" if references else "no-material-result")
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
    expected_generations: dict[str, str] = {}
    for locator in args.locators:
        if "=" not in locator:
            raise ValueError("Federated locator must use CORPUS_ID=PASSAGE_ID")
        corpus_id, raw_passage = locator.rsplit("=", 1)
        if "@" in corpus_id:
            corpus_id, generation = corpus_id.rsplit("@", 1)
            if not generation or (corpus_id in expected_generations and expected_generations[corpus_id] != generation):
                raise ValueError("Conflicting or empty generation in federated locators")
            expected_generations[corpus_id] = generation
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
        if getattr(args, "expected_fingerprint", None) is not None and len(requested) != 1:
            raise ValueError("--expected-fingerprint requires one corpus; use generation-qualified locators for multiple corpora")
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
        expected = expected_generations.get(corpus_id) or getattr(args, "expected_fingerprint", None)
        if expected is not None and expected != item["current_generation"]:
            raise ValueError(f"Corpus {corpus_id} locator generation changed; search again")

    results: list[dict[str, object]] = []
    result_positions: list[tuple[int, int]] = []
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
            expected_fingerprint=expected_generations.get(corpus_id) or getattr(args, "expected_fingerprint", None),
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
        result_positions.append((position, namespace.start_char))
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
    options = {"indent": 2} if args.pretty else {"separators": (",", ":")}
    while len(json.dumps(response, ensure_ascii=False, **options)) + 1 > args.max_total_chars:
        if len(results) <= 1:
            raise ValueError("--max-total-chars is too small for a catalog passage response envelope")
        removed = results.pop()
        response["next_offset"], response["next_start_char"] = result_positions.pop()
        response["has_more"] = True
        response["result_count"] = len(results)
        response["characters"] -= len(json.dumps(removed, ensure_ascii=False, separators=(",", ":")))
    emit_json(response, args.pretty)
    return 0
