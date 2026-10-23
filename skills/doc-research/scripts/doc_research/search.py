from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Callable

from .common import MAX_BATCH_QUERIES, MAX_FILTER_TEXT, MAX_QUERY_TEXT, database, emit_json, load_bounded_json, lower_level_purpose_record, lower_level_task_receipt, optional_research_text, required_record_id, required_research_text
from .index import bounded_rows, index_fingerprint, iter_source_files, like_contains, literal_query, prefix_query, require_current_schema, require_database, search_row_locator, select_search_rows, validate_output_paths
from .receipts import lookup_cached_receipt, receipt_cache_id, save_cached_receipt
from .research_links import link_receipt_to_research, validate_research_receipt_link
from .common import SQLITE_OPERATIONAL_ERROR, sqlite3


FTS_BOOLEAN_OPERATORS = (" AND ", " OR ", " NOT ", " NEAR ")


def register_task_results(args: argparse.Namespace, payload: dict[str, object]) -> None:
    if getattr(args, "task_receipt", None) is None or getattr(args, "gap_facet", None) is None:
        return
    from .evidence_pack import _compact_locators, _write_task_receipt

    receipt = lower_level_task_receipt(args)
    facet_id = required_record_id(args.gap_facet, "--gap-facet")
    facet = next((item for item in receipt["facets"] if item["id"] == facet_id), None)
    if facet is None:
        raise ValueError(f"Task receipt has no facet {facet_id}")
    raw_results = payload.get("results", [])
    flattened = []
    for result in raw_results:
        flattened.append(result)
        flattened.extend(result.get("also_in", []))
    locators = _compact_locators(flattened)
    if not locators:
        return
    with database(require_database(args.db), readonly=True) as connection:
        for passage_id, locator in locators.items():
            row = connection.execute(
                "SELECT rowid AS passage_id, source_path, source, source_hash, page, "
                "section, version, date, line_start, line_end FROM chunks WHERE rowid = ?",
                (passage_id,),
            ).fetchone()
            if row is None or row["source_hash"] != locator.get("source_hash"):
                raise ValueError("Search result is stale for this index")
            # Use authoritative index metadata, including aliases' line locators.
            locators[passage_id] = _compact_locators([dict(row)])[passage_id]
    new_ids = set(locators) - set(facet["passage_ids"])
    all_ids = {value for item in receipt["facets"] for value in item["passage_ids"]}
    if len(all_ids | new_ids) > 10_000:
        raise ValueError("Task receipt exceeds 10000 locators; use a separate investigation scope")
    if not new_ids:
        return
    facet["passage_ids"].extend(passage_id for passage_id in locators if passage_id in new_ids)
    facet["locators"].extend(locator for passage_id, locator in locators.items() if passage_id in new_ids)
    gaps = receipt.setdefault("gaps", [])
    if not any(gap.get("facet_id") == facet_id for gap in gaps):
        gaps.append({"facet_id": facet_id, "reason": "new-evidence-needs-review"})
    receipt["next_mode"] = "named-gap"
    _write_task_receipt(Path(args.task_receipt), receipt)


def resolved_query_mode(query: str, requested_mode: str) -> str:
    if requested_mode != "auto":
        return requested_mode
    # FTS operators are uppercase; ordinary title words such as "and" are not
    # a request to interpret surrounding punctuation as an FTS expression.
    padded = f" {query} "
    if any(operator in padded for operator in FTS_BOOLEAN_OPERATORS):
        return "fts"
    # Parentheses alone commonly belong to titles and section identifiers.
    if '"' in query or re.search(r"\bNEAR\s*\(", query):
        return "fts"
    if "*" in query:
        return "prefix"
    return "literal"


def deduplicate_batch_snippets(
    payload: dict[str, object], seen_passages: set[tuple[object, object, object]]
) -> int:
    raw_results = payload.get("results")
    if not isinstance(raw_results, list):
        return 0
    compact_results: list[object] = []
    duplicate_count = 0
    removed_characters = 0
    for raw_result in raw_results:
        if not isinstance(raw_result, dict):
            compact_results.append(raw_result)
            continue
        result = dict(raw_result)
        passage_id = result.get("passage_id")
        source_hash = result.get("source_hash")
        text = result.get("text")
        # The same passage can expose different evidence for different queries.
        key = (source_hash, passage_id, text)
        if passage_id is not None and isinstance(text, str):
            if key in seen_passages:
                removed_characters += len(text)
                result.pop("text", None)
                result.pop("text_truncated", None)
                result["batch_duplicate"] = True
                duplicate_count += 1
            else:
                seen_passages.add(key)
        compact_results.append(result)
    if duplicate_count:
        payload["results"] = compact_results
        payload["batch_duplicate_count"] = duplicate_count
        characters = payload.get("characters")
        if isinstance(characters, int):
            payload["characters"] = max(0, characters - removed_characters)
    return duplicate_count


def _attach_content_hashes(results: list[dict[str, object]], rows: list[sqlite3.Row]) -> None:
    by_id = {row["passage_id"]: row for row in rows}
    for result in results:
        text = str(by_id[result["passage_id"]]["full_text"] or "")
        result["_content_hash"] = hashlib.sha256(text.encode("utf-8")).hexdigest()


def _response_size(payload: dict[str, object], pretty: bool = False) -> int:
    options = {"indent": 2} if pretty else {"separators": (",", ":")}
    return len(json.dumps(payload, ensure_ascii=False, **options)) + 1


def _bound_search_response(
    payload: dict[str, object], args: argparse.Namespace, positions: Callable[[], list[int]]
) -> dict[str, object]:
    """Bound the complete wire response, preserving locator identities and raw offsets."""
    results = payload["results"]
    original_count = len(results)
    raw_positions = None

    def fits() -> bool:
        if _response_size(payload, args.pretty) > args.max_total_chars:
            return False
        envelope = getattr(args, "_response_envelope", None)
        return envelope is None or _response_size(envelope(payload), args.pretty) <= args._response_limit

    def update() -> None:
        nonlocal raw_positions
        payload["result_count"] = len(results)
        payload["characters"] = sum(len(item.get("text", "")) for item in results)
        if len(results) < original_count:
            if raw_positions is None:
                raw_positions = positions()
            payload["has_more"] = True
            payload["next_offset"] = args.offset + raw_positions[len(results)]
        if any(item.get("text_truncated") for item in results):
            payload["text_truncated"] = True

    update()
    while not fits():
        if not results:
            raise ValueError("--max-total-chars is too small for search response metadata")
        last = results[-1]
        original_text = last.get("text", "")
        last["text_truncated"] = True
        last["text"] = original_text[:1]
        update()
        if fits():
            low, high = 1, len(original_text)
            while low < high:
                middle = (low + high + 1) // 2
                last["text"] = original_text[:middle]
                update()
                if fits():
                    low = middle
                else:
                    high = middle - 1
            last["text"] = original_text[:low]
            update()
            return payload
        if len(results) == 1:
            raise ValueError("--max-total-chars is too small for one search result and its metadata")
        results.pop()
        update()
    return payload


def search_payload(
    args: argparse.Namespace, *, include_content_hash: bool = False,
    expected_fingerprint: str | None = None,
) -> dict[str, object]:
    db_path = require_database(args.db)
    if (args.research_db is None) != (args.facet_id is None):
        raise ValueError(
            "--research-db and --facet-id must be provided together when linking a receipt"
        )
    if args.receipts_db is None and any(
        value is not None
        for value in (args.research_db, args.facet_id, args.receipt_id)
    ):
        raise ValueError(
            "--research-db, --facet-id, and --receipt-id require the independent "
            "--receipts-db store"
        )
    if args.refresh and args.receipts_db is None:
        raise ValueError("--refresh requires --receipts-db")
    if args.read_only_receipts and args.receipts_db is None:
        raise ValueError("--read-only-receipts requires --receipts-db")
    if args.read_only_receipts and args.research_db is not None:
        raise ValueError(
            "--read-only-receipts cannot link a receipt to writable research state"
        )

    facet_id = (
        required_record_id(args.facet_id, "--facet-id")
        if args.facet_id is not None
        else None
    )
    receipt_id = (
        required_record_id(args.receipt_id, "--receipt-id")
        if args.receipt_id is not None
        else None
    )
    if not 1 <= args.limit <= 50:
        raise ValueError("--limit must be between 1 and 50")
    if args.offset < 0:
        raise ValueError("--offset must be zero or greater")
    if not 100 <= args.max_chars <= 8000:
        raise ValueError("--max-chars must be between 100 and 8000")
    if not 100 <= args.max_total_chars <= 40_000:
        raise ValueError("--max-total-chars must be between 100 and 40000")
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

    mode = resolved_query_mode(raw_query, args.mode)
    if mode == "literal":
        query = literal_query(raw_query)
    elif mode == "prefix":
        query = prefix_query(raw_query)
    else:
        query = raw_query
    conditions = ["chunks MATCH ?"]
    parameters: list[object] = [query]
    if normalized_filters["source"]:
        source_pattern = like_contains(normalized_filters["source"])
        conditions.append(
            "(source_path LIKE ? ESCAPE '\\' OR source LIKE ? ESCAPE '\\')"
        )
        parameters.extend((source_pattern, source_pattern))
    if normalized_filters["page"]:
        conditions.append("(page = ? OR (',' || page || ',') LIKE ? ESCAPE '\\')")
        parameters.extend((normalized_filters["page"], like_contains(f",{normalized_filters['page']},")))
    if normalized_filters["section"]:
        conditions.append("section LIKE ? ESCAPE '\\'")
        parameters.append(like_contains(normalized_filters["section"]))
    if normalized_filters["version"]:
        conditions.append("version = ?")
        parameters.append(normalized_filters["version"])
    if normalized_filters["date"]:
        conditions.append("date = ?")
        parameters.append(normalized_filters["date"])
    filters = {
        key: value for key, value in normalized_filters.items()
        if value is not None
    }
    candidate_limit = args.limit
    if args.dedupe_exact or args.max_per_source:
        candidate_limit = min(250, max(args.limit * 5, args.limit))
    parameters.extend((candidate_limit + 1, args.offset))

    sql = f"""
        SELECT rowid AS passage_id,
               bm25(chunks, 0.0, 3.0, 0.0, 0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 2.0, 1.0) AS score,
               source_path, source, source_hash, page, section, version, date,
               line_start, line_end,
               text AS full_text,
               snippet(chunks, 10, '', '', ' … ', {args.snippet_tokens}) AS text
        FROM chunks
        WHERE {' AND '.join(conditions)}
        ORDER BY score, rowid
        LIMIT ? OFFSET ?
    """

    fingerprint: str | None = None
    corpus_root: Path | None = None
    cached_receipt_id: str | None = None
    try:
        with database(db_path, readonly=True) as connection:
            require_current_schema(connection)
            fingerprint = index_fingerprint(connection)
            expected = expected_fingerprint or getattr(args, "expected_fingerprint", None)
            if expected is not None and expected != fingerprint:
                raise ValueError("Index fingerprint changed; restart search with the current index")
            corpus_row = connection.execute(
                "SELECT value FROM metadata WHERE key = 'corpus_root'"
            ).fetchone()
            if corpus_row is None:
                raise ValueError("Index database has no corpus binding")
            corpus_root = Path(corpus_row["value"])
            if args.receipts_db is not None:
                if not args.read_only_receipts:
                    validate_output_paths(
                        corpus_root, [args.receipts_db, args.research_db],
                        [db_path, getattr(args, "input", None), getattr(args, "task_receipt", None)],
                        source_paths=getattr(args, "_source_paths", None),
                    )
                receipt_identity = dict(filters)
                receipt_identity.update(
                    {
                        "_limit": args.limit,
                        "_dedupe_exact": args.dedupe_exact,
                        "_max_per_source": args.max_per_source,
                        "_offset": args.offset,
                    }
                )
                cached_receipt_id = receipt_id or receipt_cache_id(
                    raw_query, mode, receipt_identity, args.offset
                )
                if not args.refresh:
                    cached = lookup_cached_receipt(
                        args.receipts_db,
                        db_path,
                        corpus_root,
                        fingerprint,
                        cached_receipt_id,
                        raw_query,
                        mode,
                        receipt_identity,
                    )
                    if cached is not None:
                        if args.research_db is not None and facet_id is not None:
                            link_receipt_to_research(
                                args.research_db,
                                args.receipts_db,
                                corpus_root,
                                db_path,
                                fingerprint,
                                cached_receipt_id,
                                facet_id,
                            )
                        references = cached["result_refs"]
                        if not isinstance(references, list) or len(references) > 50 or any(
                            not isinstance(reference, dict)
                            or not isinstance(reference.get("passage_id"), int)
                            or isinstance(reference.get("passage_id"), bool)
                            for reference in references
                        ):
                            raise ValueError("Cached receipt references are invalid")
                        ids = [reference["passage_id"] for reference in references]
                        # Receipts retain locators only; reconstruct snippets under the
                        # caller's current bounds without repeating candidate selection.
                        cached_rows = connection.execute(
                            sql.split("WHERE", 1)[0]
                            + "WHERE chunks MATCH ? AND rowid IN ("
                            + ",".join("?" for _ in ids)
                            + ") ORDER BY score, rowid",
                            [query, *ids],
                        ).fetchall() if ids else []
                        results, characters, truncated = bounded_rows(
                            cached_rows, args.max_chars, args.max_chars * 50
                        )
                        if include_content_hash:
                            _attach_content_hashes(results, cached_rows)
                        aliases_by_id = {
                            reference["passage_id"]: reference.get("also_in")
                            for reference in references
                        }
                        for result in results:
                            if aliases_by_id.get(result["passage_id"]):
                                result["also_in"] = aliases_by_id[result["passage_id"]]
                        next_offset = cached["next_offset"]
                        cache_payload: dict[str, object] = {
                            "index_fingerprint": fingerprint,
                            "purpose": lower_level_purpose_record(args),
                            "query": raw_query,
                            "mode": mode,
                            "filters": filters,
                            "offset": args.offset,
                            "result_count": len(results),
                            "characters": characters,
                            "has_more": next_offset is not None,
                            "results": results,
                            "receipt_hit": True,
                            "receipt_id": cached_receipt_id,
                        }
                        if next_offset is not None:
                            cache_payload["next_offset"] = next_offset
                        if truncated:
                            cache_payload["text_truncated"] = True
                        if args.mode == "auto":
                            cache_payload["requested_mode"] = "auto"
                        def cached_positions():
                            # Cached locator pages omit raw filtered/duplicate positions.
                            # Recover them only if the current wire budget drops hits.
                            raw_rows = connection.execute(sql, parameters).fetchall()
                            return select_search_rows(
                                raw_rows, args.limit, args.dedupe_exact,
                                args.max_per_source, candidate_limit,
                            )[1]
                        return _bound_search_response(cache_payload, args, cached_positions)
            rows = connection.execute(sql, parameters).fetchall()
    except SQLITE_OPERATIONAL_ERROR as exc:
        raise ValueError(f"Invalid FTS query or index: {exc}") from exc

    (
        selected_rows,
        selected_positions,
        duplicate_locators,
        filtered_has_more,
        next_advance,
    ) = select_search_rows(
        rows,
        args.limit,
        args.dedupe_exact,
        args.max_per_source,
        candidate_limit,
    )
    receipt_next_advance = next_advance
    results, characters, output_truncated = bounded_rows(
        selected_rows, args.max_chars, args.max_chars * 50
    )
    if include_content_hash:
        _attach_content_hashes(results, selected_rows)
    for index, result in enumerate(results):
        aliases = duplicate_locators.get(index)
        if aliases:
            result["also_in"] = aliases
    has_more = filtered_has_more or len(selected_rows) > len(results)
    payload: dict[str, object] = {
        "index_fingerprint": fingerprint,
        "purpose": lower_level_purpose_record(args),
        "query": raw_query,
        "mode": mode,
        "filters": filters,
        "offset": args.offset,
        "result_count": len(results),
        "characters": characters,
        "has_more": has_more,
        "results": results,
    }
    if args.mode == "auto":
        payload["requested_mode"] = "auto"
    if output_truncated:
        payload["text_truncated"] = True
    if has_more:
        if results and len(results) < len(selected_positions):
            next_advance = selected_positions[len(results) - 1] + 1
        payload["next_offset"] = args.offset + next_advance
    if (
        args.receipts_db is not None
        and not args.read_only_receipts
        and fingerprint is not None
        and corpus_root is not None
        and cached_receipt_id is not None
    ):
        receipt_results: list[dict[str, object]] = []
        for index, row in enumerate(selected_rows):
            locator = search_row_locator(row)
            aliases = duplicate_locators.get(index)
            if aliases:
                locator["also_in"] = aliases
            receipt_results.append(locator)
        receipt_payload = {
            **payload,
            "filters": receipt_identity,
            "results": receipt_results,
            "result_count": len(receipt_results),
            "characters": 0,
            "has_more": filtered_has_more,
        }
        if filtered_has_more:
            receipt_payload["next_offset"] = args.offset + receipt_next_advance
        else:
            receipt_payload.pop("next_offset", None)
        if args.research_db is not None and facet_id is not None:
            validate_research_receipt_link(
                args.research_db,
                corpus_root,
                facet_id,
                db_path,
                fingerprint,
            )
        save_cached_receipt(
            args.receipts_db,
            db_path,
            corpus_root,
            fingerprint,
            cached_receipt_id,
            receipt_payload,
        )
        if args.research_db is not None and facet_id is not None:
            link_receipt_to_research(
                args.research_db,
                args.receipts_db,
                corpus_root,
                db_path,
                fingerprint,
                cached_receipt_id,
                facet_id,
            )
        payload["receipt_hit"] = False
        payload["receipt_id"] = cached_receipt_id
    elif args.receipts_db is not None:
        payload["receipt_hit"] = False
        payload["receipt_persisted"] = False
    return _bound_search_response(payload, args, lambda: selected_positions)

def command_search(args: argparse.Namespace) -> int:
    purpose = lower_level_purpose_record(args)
    payload = search_payload(args)
    register_task_results(args, payload)
    payload["purpose"] = purpose
    emit_json(payload, args.pretty)
    return 0

def command_search_many(args: argparse.Namespace) -> int:
    purpose = lower_level_purpose_record(args)
    if args.read_only_receipts and args.receipts_db is None:
        raise ValueError("--read-only-receipts requires --receipts-db")
    if args.read_only_receipts and args.research_db is not None:
        raise ValueError(
            "--read-only-receipts cannot link receipts to writable research state"
        )
    raw = load_bounded_json(args.input, "Batch query file")
    items = raw.get("queries") if isinstance(raw, dict) else raw
    if not isinstance(items, list):
        raise ValueError("Batch query file must be an array or an object with a queries array")
    if len(items) > MAX_BATCH_QUERIES:
        raise ValueError(f"At most {MAX_BATCH_QUERIES} batch queries are allowed")
    if args.query_offset < 0:
        raise ValueError("--query-offset must be zero or greater")
    if not 1 <= args.limit_per_query <= 20:
        raise ValueError("--limit-per-query must be between 1 and 20")
    if not 100 <= args.max_per_query_chars <= 20_000:
        raise ValueError("--max-per-query-chars must be between 100 and 20000")
    if not 1_000 <= args.max_total_chars <= 40_000:
        raise ValueError("--max-total-chars must be between 1000 and 40000")

    allowed = {
        "query",
        "mode",
        "source",
        "page",
        "section",
        "version",
        "date",
        "offset",
        "facet_id",
        "receipt_id",
        "refresh",
        "gap_facet",
    }
    normalized: list[dict[str, object]] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"Batch query {index} must be an object")
        unknown = set(item) - allowed
        if unknown:
            raise ValueError(
                f"Batch query {index} has unsupported fields: {', '.join(sorted(unknown))}"
            )
        query = item.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ValueError(f"Batch query {index} requires non-empty query text")
        mode = item.get("mode", "auto")
        if mode not in {"auto", "literal", "prefix", "fts"}:
            raise ValueError(f"Batch query {index} has unsupported mode: {mode}")
        for field in (
            "source",
            "page",
            "section",
            "version",
            "date",
            "facet_id",
            "receipt_id",
            "gap_facet",
        ):
            if field in item and item[field] is not None and not isinstance(item[field], str):
                raise ValueError(f"Batch query {index} field {field} must be a string")
        offset = item.get("offset", 0)
        if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
            raise ValueError(f"Batch query {index} offset must be zero or greater")
        refresh = item.get("refresh", False)
        if not isinstance(refresh, bool):
            raise ValueError(f"Batch query {index} refresh must be a boolean")
        normalized.append(item)

    selected = normalized[args.query_offset :]
    outputs: list[dict[str, object]] = []
    seen_passages: set[tuple[object, object, object]] = set()
    duplicate_snippets_removed = 0
    source_paths = getattr(args, "_source_paths", None)
    if source_paths is None and args.receipts_db is not None and not args.read_only_receipts:
        with database(require_database(args.db), readonly=True) as connection:
            corpus_row = connection.execute(
                "SELECT value FROM metadata WHERE key = 'corpus_root'"
            ).fetchone()
            if corpus_row is None:
                raise ValueError("Index database has no corpus binding")
            source_paths = list(iter_source_files(Path(corpus_row["value"])))

    def batch_response(values, duplicate_count):
        more = args.query_offset + len(values) < len(normalized)
        result = {
            "purpose": purpose,
            "query_offset": args.query_offset,
            "query_count": len(values),
            "characters": sum(_response_size(value) - 1 for value in values),
            "has_more": more,
            "results": values,
        }
        if duplicate_count:
            result["duplicate_snippets_removed"] = duplicate_count
        if more:
            result["next_query_offset"] = args.query_offset + len(values)
        return result

    for item in selected:
        namespace = argparse.Namespace(
            db=args.db,
            query=item["query"],
            mode=item.get("mode", "auto"),
            source=item.get("source"),
            page=item.get("page"),
            section=item.get("section"),
            version=item.get("version"),
            date=item.get("date"),
            limit=args.limit_per_query,
            offset=item.get("offset", 0),
            max_chars=args.max_chars,
            max_total_chars=args.max_per_query_chars,
            snippet_tokens=args.snippet_tokens,
            receipts_db=args.receipts_db,
            research_db=args.research_db,
            facet_id=item.get("facet_id"),
            receipt_id=item.get("receipt_id"),
            refresh=bool(item.get("refresh", False)),
            read_only_receipts=args.read_only_receipts,
            dedupe_exact=args.dedupe_exact,
            max_per_source=args.max_per_source,
            pretty=args.pretty,
            task_receipt=getattr(args, "task_receipt", None),
            gap_facet=item.get("gap_facet", getattr(args, "gap_facet", None)),
            input=args.input,
            _source_paths=source_paths,
            _response_envelope=lambda value: batch_response([*outputs, value], duplicate_snippets_removed),
            _response_limit=args.max_total_chars,
        )
        lower_level_purpose_record(namespace)
        try:
            payload = search_payload(namespace)
        except ValueError as exc:
            if outputs and "--max-total-chars is too small" in str(exc):
                break
            raise
        trial_seen = set(seen_passages)
        removed = deduplicate_batch_snippets(payload, trial_seen)
        trial = batch_response([*outputs, payload], duplicate_snippets_removed + removed)
        if _response_size(trial, args.pretty) > args.max_total_chars:
            if outputs:
                break
            raise ValueError("--max-total-chars is too small for one query result and its envelope")
        register_task_results(namespace, payload)
        outputs.append(payload)
        seen_passages = trial_seen
        duplicate_snippets_removed += removed
    result = batch_response(outputs, duplicate_snippets_removed)
    if _response_size(result, args.pretty) > args.max_total_chars:
        raise ValueError("--max-total-chars is too small for batch response metadata")
    emit_json(result, args.pretty)
    return 0
