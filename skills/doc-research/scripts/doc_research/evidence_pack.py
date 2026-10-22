from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

from .common import (
    MAX_BATCH_QUERIES,
    MAX_QUERY_TEXT,
    EVIDENCE_EXECUTION_ROUTES,
    EVIDENCE_WORKER_CONTEXTS,
    TASK_RECEIPT_VERSION,
    TOKEN,
    database,
    emit_json,
    load_bounded_json,
    required_record_id,
    required_research_text,
)
from .index import get_payload, index_payload, resolve_index_binding
from .receipts import (
    initialize_receipt_store,
    require_receipt_database,
    validate_receipt_store_connection,
)
from .search import search_payload


MAX_EVIDENCE_QUESTIONS = 8
MAX_QUERIES_PER_QUESTION = 3
MAX_FINDING_CLAIMS = 8
MAX_FINDING_TEXT = 1_000
MAX_FINDING_SCOPE = 500
QUERY_ROLES = {"support", "check"}
QUERY_MODES = {"auto", "literal", "prefix", "fts"}
FINDING_STATUSES = {"verified", "conflicted", "unresolved"}
LOCATOR_FIELDS = (
    "passage_id",
    "source",
    "source_path",
    "source_hash",
    "page",
    "section",
    "version",
    "date",
)
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "where",
    "which",
    "who",
    "а",
    "без",
    "в",
    "во",
    "где",
    "для",
    "до",
    "есть",
    "и",
    "из",
    "или",
    "как",
    "какие",
    "какой",
    "кто",
    "ли",
    "на",
    "нет",
    "один",
    "одной",
    "от",
    "по",
    "при",
    "с",
    "со",
    "у",
    "что",
    "это",
}
STRUCTURAL_TERMS = (
    "maxOccurs",
    "minOccurs",
    "choice",
    "обязательн*",
    "исключ*",
    "вариант*",
)


def _query_token(token: str) -> str:
    if len(token) <= 4 or any(character.isdigit() for character in token):
        return token
    if "_" in token or (any(character.isupper() for character in token) and not token.isupper()):
        return token
    prefix_length = min(8, max(4, len(token) - 2))
    return token[:prefix_length]


def _question_tokens(question: str) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for token in TOKEN.findall(question):
        lowered = token.casefold()
        if lowered in STOP_WORDS or len(token) < 3 or lowered in seen:
            continue
        seen.add(lowered)
        output.append(token)
    return output


def _automatic_queries(question: str) -> list[dict[str, str]]:
    tokens = _question_tokens(question)
    if not tokens:
        raise ValueError("Question contains no searchable terms; provide explicit queries")
    ranked = sorted(
        enumerate(tokens),
        key=lambda item: (
            -int(any(character.isdigit() for character in item[1]) or "_" in item[1]),
            -len(item[1]),
            item[0],
        ),
    )
    anchors = [_query_token(token) for _, token in ranked[:3]]
    queries: list[dict[str, str]] = []
    if len(anchors) > 1:
        queries.append(
            {"query": " ".join(anchors[:2]), "mode": "prefix", "role": "support"}
        )
    queries.append({"query": anchors[0], "mode": "prefix", "role": "support"})
    control = f"{anchors[0]}* AND ({' OR '.join(STRUCTURAL_TERMS)})"
    queries.append({"query": control, "mode": "fts", "role": "check"})
    return queries[:MAX_QUERIES_PER_QUESTION]


def _zero_hit_fallbacks(
    question: str, planned_queries: list[dict[str, str]]
) -> dict[str, dict[str, str]]:
    combined = " ".join(
        [question, *(query["query"] for query in planned_queries)]
    )
    tokens = _question_tokens(combined)
    ranked = sorted(
        enumerate(tokens),
        key=lambda item: (
            -int(
                any(character.isdigit() for character in item[1])
                or "_" in item[1]
                or (
                    any(character.isupper() for character in item[1])
                    and not item[1].isupper()
                )
            ),
            -len(item[1]),
            item[0],
        ),
    )
    anchors = list(dict.fromkeys(_query_token(token) for _, token in ranked[:8]))
    if not anchors:
        return {}
    expression = " OR ".join(
        f'"{anchor.replace(chr(34), chr(34) * 2)}"*' for anchor in anchors
    )
    structural = " OR ".join(STRUCTURAL_TERMS)
    return {
        "support": {"query": expression, "mode": "fts", "role": "support"},
        "check": {
            "query": f"({expression}) AND ({structural})",
            "mode": "fts",
            "role": "check",
        },
    }


def _normalize_query(value: object, location: str) -> dict[str, str]:
    if isinstance(value, str):
        query = required_research_text(value, f"{location}.query", MAX_QUERY_TEXT)
        return {"query": query, "mode": "auto", "role": "support"}
    if not isinstance(value, dict):
        raise ValueError(f"{location} must be text or an object")
    unknown = set(value) - {"query", "mode", "role"}
    if unknown:
        raise ValueError(f"{location} has unsupported fields: {', '.join(sorted(unknown))}")
    query = required_research_text(value.get("query"), f"{location}.query", MAX_QUERY_TEXT)
    mode = value.get("mode", "auto")
    role = value.get("role", "support")
    if mode not in QUERY_MODES:
        raise ValueError(f"{location}.mode must be auto, literal, prefix, or fts")
    if role not in QUERY_ROLES:
        raise ValueError(f"{location}.role must be support or check")
    return {"query": query, "mode": str(mode), "role": str(role)}


def normalize_questions(raw: object) -> list[dict[str, object]]:
    items = raw.get("questions") if isinstance(raw, dict) else raw
    if not isinstance(items, list) or not items:
        raise ValueError("Evidence input must contain a non-empty questions array")
    if len(items) > MAX_EVIDENCE_QUESTIONS:
        raise ValueError(f"At most {MAX_EVIDENCE_QUESTIONS} evidence questions are allowed")
    normalized: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    query_count = 0
    for index, item in enumerate(items, start=1):
        location = f"questions[{index - 1}]"
        if isinstance(item, str):
            question = required_research_text(item, location, MAX_QUERY_TEXT)
            question_id = f"q{index}"
            raw_queries: object = None
        elif isinstance(item, dict):
            unknown = set(item) - {"id", "question", "queries"}
            if unknown:
                raise ValueError(
                    f"{location} has unsupported fields: {', '.join(sorted(unknown))}"
                )
            question = required_research_text(
                item.get("question"), f"{location}.question", MAX_QUERY_TEXT
            )
            question_id = required_record_id(item.get("id", f"q{index}"), f"{location}.id")
            raw_queries = item.get("queries")
        else:
            raise ValueError(f"{location} must be text or an object")
        if question_id in seen_ids:
            raise ValueError(f"Duplicate question id: {question_id}")
        seen_ids.add(question_id)
        if raw_queries is None:
            queries = _automatic_queries(question)
        else:
            if not isinstance(raw_queries, list) or not raw_queries:
                raise ValueError(f"{location}.queries must be a non-empty array")
            if len(raw_queries) > MAX_QUERIES_PER_QUESTION:
                raise ValueError(
                    f"{location}.queries allows at most {MAX_QUERIES_PER_QUESTION} entries"
                )
            queries = [
                _normalize_query(value, f"{location}.queries[{query_index}]")
                for query_index, value in enumerate(raw_queries)
            ]
        roles = {str(query["role"]) for query in queries}
        if roles != QUERY_ROLES:
            missing = ", ".join(sorted(QUERY_ROLES - roles))
            raise ValueError(
                f"{location}.queries must include support and check roles; missing: {missing}"
            )
        query_count += len(queries)
        normalized.append({"id": question_id, "question": question, "queries": queries})
    if query_count > MAX_BATCH_QUERIES:
        raise ValueError(f"At most {MAX_BATCH_QUERIES} planned queries are allowed")
    return normalized


def question_set_hash(questions: list[dict[str, object]]) -> str:
    encoded = json.dumps(
        questions,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def facet_hash(question: dict[str, object]) -> str:
    encoded = json.dumps(
        {"id": question["id"], "queries": question["queries"]},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _execution_record(args: argparse.Namespace) -> dict[str, str]:
    route = args.execution_route
    if route not in EVIDENCE_EXECUTION_ROUTES:
        raise ValueError("--execution-route is invalid")
    if route == "auto":
        if not getattr(args, "pack_output", None):
            raise ValueError("--pack-output is required for --execution-route auto")
        if args.executor or args.fallback_reason or args.worker_context:
            raise ValueError(
                "--executor, --worker-context, and --fallback-reason are not valid for auto"
            )
        return {"route": route, "reason": "deterministic-cost-routing"}
    if route == "coordinator-direct":
        if args.executor or args.fallback_reason or args.worker_context:
            raise ValueError(
                "--executor, --worker-context, and --fallback-reason are not valid for "
                "coordinator-direct"
            )
        return {"route": route, "reason": "bounded-inline-evidence"}
    if route == "low-overhead-worker":
        if not args.executor:
            raise ValueError(
                "--executor is required for --execution-route low-overhead-worker"
            )
        if args.worker_context not in EVIDENCE_WORKER_CONTEXTS:
            raise ValueError(
                "--worker-context capsule-no-parent-history-v1 is required for "
                "--execution-route low-overhead-worker"
            )
        if args.fallback_reason:
            raise ValueError("--fallback-reason is only valid for coordinator-fallback")
        return {
            "route": route,
            "reason": "cold-bounded-retrieval",
            "executor": args.executor,
            "worker_context": args.worker_context,
        }
    if route == "coordinator-fallback":
        if not args.fallback_reason:
            raise ValueError(
                "--fallback-reason is required for --execution-route coordinator-fallback"
            )
        if args.executor:
            raise ValueError("--executor is only valid for low-overhead-worker")
        if args.worker_context:
            raise ValueError("--worker-context is only valid for low-overhead-worker")
        return {"route": route, "reason": args.fallback_reason}
    if args.executor or args.fallback_reason or args.worker_context:
        raise ValueError(
            "--executor, --worker-context, and --fallback-reason are not valid for "
            "coordinator-warm"
        )
    return {"route": route, "reason": "warm-task-receipt"}


def _load_task_receipt(
    path: Path | None, fingerprint: str
) -> dict[str, object] | None:
    if path is None or not path.exists():
        return None
    raw = load_bounded_json(path, "Task receipt")
    if not isinstance(raw, dict):
        raise ValueError("Task receipt must be a JSON object")
    if raw.get("version") != TASK_RECEIPT_VERSION:
        raise ValueError("Task receipt version is unsupported")
    facets = raw.get("facets")
    if not isinstance(facets, list):
        raise ValueError("Task receipt facets must be an array")
    stored_fingerprint = raw.get("index_fingerprint")
    if (
        not isinstance(stored_fingerprint, str)
        or len(stored_fingerprint) != 64
        or any(character not in "0123456789abcdef" for character in stored_fingerprint)
    ):
        raise ValueError("Task receipt index_fingerprint is invalid")
    if stored_fingerprint != fingerprint:
        return None
    all_passage_ids: list[int] = []
    seen_facet_ids: set[str] = set()
    for index, facet in enumerate(facets):
        if not isinstance(facet, dict):
            raise ValueError(f"Task receipt facet {index} must be an object")
        facet_id = required_record_id(
            facet.get("id"), f"Task receipt facet {index}.id"
        )
        if facet_id in seen_facet_ids:
            raise ValueError(f"Task receipt contains duplicate facet {facet_id}")
        seen_facet_ids.add(facet_id)
        raw_facet_hash = facet.get("facet_hash")
        if (
            not isinstance(raw_facet_hash, str)
            or len(raw_facet_hash) != 64
            or any(character not in "0123456789abcdef" for character in raw_facet_hash)
        ):
            raise ValueError(f"Task receipt facet {index}.facet_hash is invalid")
        validated: dict[str, list[int]] = {}
        for field in (
            "passage_ids",
            "support_passage_ids",
            "check_passage_ids",
        ):
            values = facet.get(field)
            if not isinstance(values, list) or any(
                not isinstance(value, int) or isinstance(value, bool) or value < 1
                for value in values
            ):
                raise ValueError(f"Task receipt facet {index}.{field} is invalid")
            validated[field] = values
        passage_ids = set(validated["passage_ids"])
        if not set(validated["support_passage_ids"]).issubset(passage_ids) or not set(
            validated["check_passage_ids"]
        ).issubset(passage_ids):
            raise ValueError(
                f"Task receipt facet {index} role passages are outside passage_ids"
            )
        all_passage_ids.extend(validated["passage_ids"])
        receipt_ids = facet.get("receipt_ids")
        if not isinstance(receipt_ids, list) or any(
            not isinstance(value, str) or not value for value in receipt_ids
        ):
            raise ValueError(f"Task receipt facet {index}.receipt_ids is invalid")
        locators = facet.get("locators")
        if not isinstance(locators, list):
            raise ValueError(f"Task receipt facet {index}.locators is invalid")
        locator_passage_ids: list[int] = []
        for locator_index, locator in enumerate(locators):
            location = f"Task receipt facet {index}.locators[{locator_index}]"
            if not isinstance(locator, dict) or set(locator) - set(LOCATOR_FIELDS):
                raise ValueError(f"{location} is invalid")
            passage_id = locator.get("passage_id")
            if (
                not isinstance(passage_id, int)
                or isinstance(passage_id, bool)
                or passage_id < 1
            ):
                raise ValueError(f"{location}.passage_id is invalid")
            required_research_text(locator.get("source"), f"{location}.source")
            source_hash = locator.get("source_hash")
            if (
                not isinstance(source_hash, str)
                or len(source_hash) != 64
                or any(character not in "0123456789abcdef" for character in source_hash)
            ):
                raise ValueError(f"{location}.source_hash is invalid")
            for field in ("source_path", "page", "section", "version", "date"):
                if locator.get(field) is not None:
                    required_research_text(locator[field], f"{location}.{field}")
            locator_passage_ids.append(passage_id)
        if len(locator_passage_ids) != len(set(locator_passage_ids)) or set(
            locator_passage_ids
        ) != passage_ids:
            raise ValueError(
                f"Task receipt facet {index}.locators must cover passage_ids exactly"
            )
        finding = facet.get("finding")
        if finding is not None:
            if (
                not isinstance(finding, dict)
                or set(finding) - {"status", "claims"}
                or finding.get("status") not in FINDING_STATUSES
            ):
                raise ValueError(f"Task receipt facet {index}.finding is invalid")
            claims = finding.get("claims")
            if not isinstance(claims, list) or not claims or len(claims) > MAX_FINDING_CLAIMS:
                raise ValueError(f"Task receipt facet {index}.finding.claims is invalid")
            for claim_index, claim in enumerate(claims):
                if not isinstance(claim, dict):
                    raise ValueError(
                        f"Task receipt facet {index}.finding.claims[{claim_index}] is invalid"
                    )
                if set(claim) - {"text", "passage_ids", "scope"}:
                    raise ValueError(
                        f"Task receipt facet {index}.finding.claims[{claim_index}] is invalid"
                    )
                required_research_text(
                    claim.get("text"),
                    f"Task receipt facet {index}.finding.claims[{claim_index}].text",
                    MAX_FINDING_TEXT,
                )
                claim_ids = claim.get("passage_ids")
                if not isinstance(claim_ids, list) or any(
                    not isinstance(value, int) or isinstance(value, bool) or value < 1
                    for value in claim_ids
                ):
                    raise ValueError(
                        f"Task receipt facet {index}.finding.claims[{claim_index}].passage_ids "
                        "is invalid"
                    )
                if not set(claim_ids).issubset(passage_ids):
                    raise ValueError(
                        f"Task receipt facet {index}.finding references outside passages"
                    )
                if finding.get("status") == "verified" and not claim_ids:
                    raise ValueError(
                        f"Task receipt facet {index}.verified finding requires passage_ids"
                    )
                if claim.get("scope") is not None:
                    required_research_text(
                        claim["scope"],
                        f"Task receipt facet {index}.finding.claims[{claim_index}].scope",
                        MAX_FINDING_SCOPE,
                    )
            if finding.get("status") == "verified" and not (
                validated["support_passage_ids"] and validated["check_passage_ids"]
            ):
                raise ValueError(
                    f"Task receipt facet {index}.verified finding lacks support/check coverage"
                )
    if len(set(all_passage_ids)) > 50:
        raise ValueError("Task receipt references more than 50 passages")
    return raw


def _write_json(path: Path, payload: object) -> None:
    resolved = path.resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=f".{resolved.name}.",
            suffix=".tmp",
            dir=resolved.parent,
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
        if os.name != "nt":
            temporary_path.chmod(0o600)
        temporary_path.replace(resolved)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _write_task_receipt(path: Path, payload: dict[str, object]) -> None:
    _write_json(path, payload)


def _receipt_store(args: argparse.Namespace, corpus: Path) -> tuple[Path, bool]:
    path = (
        args.receipts_db.resolve()
        if args.receipts_db is not None
        else args.db.resolve().with_name(f"{args.db.resolve().stem}.receipts.sqlite")
    )
    created = not path.exists()
    if created:
        initialize_receipt_store(path, corpus, args.db)
    else:
        require_receipt_database(path)
        with database(path, readonly=True) as connection:
            validate_receipt_store_connection(connection, args.db.resolve(), corpus)
    return path, created


def _get_payload(
    db: Path, passage_ids: list[int], max_chars: int, max_total_chars: int
) -> dict[str, object]:
    if not passage_ids:
        return {
            "result_count": 0,
            "characters": 0,
            "has_more": False,
            "not_found": [],
            "results": [],
        }
    if len(passage_ids) * 100 > max_total_chars:
        raise ValueError(
            "--max-total-chars must allow at least 100 characters per selected passage"
        )
    fair_share = max_total_chars // len(passage_ids)
    per_passage = min(max_chars, fair_share)
    results: list[dict[str, object]] = []
    not_found: list[int] = []
    truncated: list[int] = []
    characters = 0
    for passage_id in passage_ids:
        item = get_payload(
            argparse.Namespace(
                db=db,
                passage_ids=[passage_id],
                limit=1,
                offset=0,
                start_char=0,
                max_chars=per_passage,
                max_total_chars=per_passage,
            )
        )
        raw_results = item.get("results")
        if isinstance(raw_results, list):
            results.extend(raw_results)
        raw_not_found = item.get("not_found")
        if isinstance(raw_not_found, list):
            not_found.extend(
                value for value in raw_not_found if isinstance(value, int)
            )
        characters += int(item.get("characters", 0))
        if item.get("has_more"):
            truncated.append(passage_id)
    payload: dict[str, object] = {
        "result_count": len(results),
        "characters": characters,
        "has_more": bool(truncated),
        "not_found": not_found,
        "results": results,
    }
    if truncated:
        payload["truncated_passage_ids"] = truncated
    return payload


def _search_namespace(
    args: argparse.Namespace, query: dict[str, str], receipts_db: Path | None
) -> argparse.Namespace:
    return argparse.Namespace(
        db=args.db,
        query=query["query"],
        mode=query["mode"],
        source=None,
        page=None,
        section=None,
        version=None,
        date=None,
        limit=args.limit_per_query,
        offset=0,
        max_chars=240,
        max_total_chars=800,
        snippet_tokens=16,
        receipts_db=receipts_db,
        research_db=None,
        facet_id=None,
        receipt_id=None,
        refresh=False,
        read_only_receipts=False,
        dedupe_exact=True,
        max_per_source=0,
        pretty=False,
    )


def _facet_candidates(
    args: argparse.Namespace,
    questions: list[dict[str, object]],
    receipts_db: Path | None,
) -> tuple[list[dict[str, object]], int, int, int]:
    facets: list[dict[str, object]] = []
    search_count = 0
    receipt_hits = 0
    fallback_search_count = 0
    for question in questions:
        candidates: list[dict[str, object]] = []
        receipt_ids: list[str] = []
        planned_queries = [
            {key: str(value) for key, value in raw_query.items()}
            for raw_query in question["queries"]
            if isinstance(raw_query, dict)
        ]
        executed = {
            (query["query"], query["mode"], query["role"])
            for query in planned_queries
        }
        role_hits = {role: False for role in QUERY_ROLES}

        def execute_query(query: dict[str, str], *, fallback: bool = False) -> None:
            nonlocal search_count, receipt_hits, fallback_search_count
            result = search_payload(_search_namespace(args, query, receipts_db))
            search_count += 1
            if fallback:
                fallback_search_count += 1
            if result.get("receipt_hit") is True:
                receipt_hits += 1
            receipt_id = result.get("receipt_id")
            if isinstance(receipt_id, str) and receipt_id not in receipt_ids:
                receipt_ids.append(receipt_id)
            role = query["role"]
            raw_results = result.get("results")
            if not isinstance(raw_results, list):
                return
            if raw_results:
                role_hits[role] = True
            for rank, item in enumerate(raw_results):
                if not isinstance(item, dict):
                    continue
                passage_id = item.get("passage_id")
                if isinstance(passage_id, int) and not isinstance(passage_id, bool):
                    candidates.append(
                        {"passage_id": passage_id, "role": role, "rank": rank}
                    )

        for query in planned_queries:
            execute_query(query)

        fallbacks = _zero_hit_fallbacks(str(question["question"]), planned_queries)
        for role in ("support", "check"):
            if role_hits[role]:
                continue
            query = fallbacks.get(role)
            if query is None:
                continue
            key = (query["query"], query["mode"], query["role"])
            if key in executed:
                continue
            executed.add(key)
            execute_query(query, fallback=True)
        merged: dict[int, dict[str, object]] = {}
        for candidate in candidates:
            passage_id = int(candidate["passage_id"])
            current = merged.setdefault(
                passage_id,
                {
                    "passage_id": passage_id,
                    "roles": [],
                    "rank": candidate["rank"],
                },
            )
            roles = current["roles"]
            if isinstance(roles, list) and candidate["role"] not in roles:
                roles.append(candidate["role"])

        ordered: list[dict[str, object]] = []
        seen: set[int] = set()
        for role in ("support", "check"):
            for candidate in merged.values():
                passage_id = int(candidate["passage_id"])
                roles = candidate["roles"]
                if isinstance(roles, list) and role in roles and passage_id not in seen:
                    seen.add(passage_id)
                    ordered.append(candidate)
                    break
        for candidate in merged.values():
            passage_id = int(candidate["passage_id"])
            if passage_id not in seen:
                seen.add(passage_id)
                ordered.append(candidate)
        facets.append(
            {
                "id": question["id"],
                "facet_hash": facet_hash(question),
                "candidates": ordered,
                "receipt_ids": receipt_ids,
            }
        )
    return facets, search_count, receipt_hits, fallback_search_count


def _select_passages(
    facets: list[dict[str, object]], max_per_question: int, max_passages: int
) -> list[int]:
    selected: list[int] = []
    selected_set: set[int] = set()
    for position in range(max_per_question):
        for facet in facets:
            candidates = facet["candidates"]
            if not isinstance(candidates, list) or position >= len(candidates):
                continue
            candidate = candidates[position]
            if not isinstance(candidate, dict):
                continue
            passage_id = int(candidate["passage_id"])
            if passage_id not in selected_set and len(selected) >= max_passages:
                continue
            if passage_id not in selected_set:
                selected_set.add(passage_id)
                selected.append(passage_id)
    for facet in facets:
        candidates = facet.pop("candidates")
        chosen = [
            candidate
            for candidate in candidates
            if int(candidate["passage_id"]) in selected_set
        ][:max_per_question]
        facet["passage_ids"] = [int(item["passage_id"]) for item in chosen]
        facet["support_passage_ids"] = [
            int(item["passage_id"])
            for item in chosen
            if "support" in item["roles"]
        ]
        facet["check_passage_ids"] = [
            int(item["passage_id"])
            for item in chosen
            if "check" in item["roles"]
        ]
    return selected


def _receipt_facets(facets: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "id": facet["id"],
            "facet_hash": facet["facet_hash"],
            "passage_ids": facet["passage_ids"],
            "support_passage_ids": facet.get("support_passage_ids", []),
            "check_passage_ids": facet.get("check_passage_ids", []),
            "receipt_ids": facet.get("receipt_ids", []),
            "locators": facet.get("locators", []),
            "checks": [
                role
                for role, key in (
                    ("support", "support_passage_ids"),
                    ("control", "check_passage_ids"),
                )
                if facet.get(key)
            ],
            **(
                {"finding": facet["finding"]}
                if isinstance(facet.get("finding"), dict)
                else {}
            ),
        }
        for facet in facets
    ]


def _receipt_gaps(facets: list[dict[str, object]]) -> list[dict[str, object]]:
    gaps: list[dict[str, object]] = []
    for facet in facets:
        support = bool(facet.get("support_passage_ids"))
        control = bool(facet.get("check_passage_ids"))
        if not support and not control:
            reason = "no-material-result"
        elif not support:
            reason = "support-not-found"
        elif not control:
            reason = "control-not-found"
        else:
            continue
        gaps.append({"facet_id": facet["id"], "reason": reason})
    return gaps


def _warm_facets(receipt: dict[str, object]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for raw in receipt["facets"]:
        if not isinstance(raw, dict):
            continue
        output.append(
            {
                "id": raw["id"],
                "facet_hash": raw["facet_hash"],
                "passage_ids": list(raw.get("passage_ids", [])),
                "support_passage_ids": list(raw.get("support_passage_ids", [])),
                "check_passage_ids": list(raw.get("check_passage_ids", [])),
                "receipt_ids": list(raw.get("receipt_ids", [])),
                "locators": list(raw.get("locators", [])),
                **(
                    {"finding": raw["finding"]}
                    if isinstance(raw.get("finding"), dict)
                    else {}
                ),
            }
        )
    return output


def _compact_passages(raw_results: object) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    if not isinstance(raw_results, list):
        return [], []
    sources: list[dict[str, object]] = []
    passages: list[dict[str, object]] = []
    source_ids: dict[tuple[object, object, object], str] = {}
    for raw in raw_results:
        if not isinstance(raw, dict):
            continue
        key = (raw.get("source"), raw.get("source_path"), raw.get("source_hash"))
        source_id = source_ids.get(key)
        if source_id is None:
            source_id = f"s{len(source_ids) + 1}"
            source_ids[key] = source_id
            source: dict[str, object] = {
                "id": source_id,
                "source": raw.get("source"),
                "source_hash": raw.get("source_hash"),
            }
            if raw.get("source_path") is not None:
                source["source_path"] = raw["source_path"]
            sources.append(source)
        passage: dict[str, object] = {
            "passage_id": raw.get("passage_id"),
            "source_id": source_id,
            "text": raw.get("text", ""),
        }
        for field in (
            "page",
            "section",
            "version",
            "date",
            "text_start_char",
            "text_truncated",
        ):
            if raw.get(field) is not None:
                passage[field] = raw[field]
        passages.append(passage)
    return sources, passages


def _compact_locators(raw_results: object) -> dict[int, dict[str, object]]:
    if not isinstance(raw_results, list):
        return {}
    output: dict[int, dict[str, object]] = {}
    for raw in raw_results:
        if not isinstance(raw, dict):
            continue
        passage_id = raw.get("passage_id")
        if not isinstance(passage_id, int) or isinstance(passage_id, bool):
            continue
        output[passage_id] = {
            field: raw[field]
            for field in LOCATOR_FIELDS
            if raw.get(field) is not None
        }
    return output


def _verified_finding(facet: dict[str, object]) -> dict[str, object] | None:
    finding = facet.get("finding")
    if isinstance(finding, dict) and finding.get("status") == "verified":
        return finding
    return None


def _routing_profile(path: Path | None) -> dict[str, float]:
    defaults = {
        "parent_input_cost_ratio": 1.0,
        "worker_input_cost_ratio": 1.0,
        "worker_output_cost_ratio": 1.0,
        "worker_startup_tokens": 0.0,
        "expected_parent_turns": 1.0,
        "finding_tokens_per_facet": 120.0,
        "minimum_savings_fraction": 0.15,
    }
    if path is None:
        return defaults
    raw = load_bounded_json(path, "Routing profile")
    if not isinstance(raw, dict):
        raise ValueError("Routing profile must be a JSON object")
    unknown = set(raw) - set(defaults)
    if unknown:
        raise ValueError(
            f"Routing profile has unsupported fields: {', '.join(sorted(unknown))}"
        )
    profile = dict(defaults)
    for key, value in raw.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"Routing profile {key} must be numeric")
        profile[key] = float(value)
    for key in (
        "parent_input_cost_ratio",
        "worker_input_cost_ratio",
        "worker_output_cost_ratio",
        "expected_parent_turns",
        "finding_tokens_per_facet",
    ):
        if profile[key] <= 0:
            raise ValueError(f"Routing profile {key} must be positive")
    if profile["worker_startup_tokens"] < 0:
        raise ValueError("Routing profile worker_startup_tokens must not be negative")
    if not 0 <= profile["minimum_savings_fraction"] < 1:
        raise ValueError(
            "Routing profile minimum_savings_fraction must be between 0 and 1"
        )
    return profile


def _route_evidence(
    args: argparse.Namespace, evidence_characters: int, facets_needing_model: int
) -> dict[str, object]:
    if facets_needing_model == 0:
        return {
            "recommendation": "receipt-only",
            "reason": "verified-finding-hit",
            "estimated_evidence_tokens": 0,
            "estimated_finding_tokens": 0,
        }
    profile = _routing_profile(args.routing_profile)
    evidence_tokens = (max(0, evidence_characters) + 3) // 4
    finding_tokens = max(
        1, round(facets_needing_model * profile["finding_tokens_per_facet"])
    )
    turns = profile["expected_parent_turns"]
    direct_cost = evidence_tokens * profile["parent_input_cost_ratio"] * turns
    delegated_cost = (
        profile["worker_startup_tokens"] * profile["worker_input_cost_ratio"]
        + evidence_tokens * profile["worker_input_cost_ratio"]
        + finding_tokens * profile["worker_output_cost_ratio"]
        + finding_tokens * profile["parent_input_cost_ratio"] * turns
    )
    threshold = direct_cost * (1 - profile["minimum_savings_fraction"])
    if args.routing_profile is not None and delegated_cost <= threshold:
        recommendation = "low-overhead-worker"
        reason = "measured-worker-break-even"
    else:
        recommendation = "coordinator-direct"
        reason = (
            "no-routing-profile"
            if args.routing_profile is None
            else "worker-not-below-break-even"
        )
    return {
        "recommendation": recommendation,
        "reason": reason,
        "estimated_evidence_tokens": evidence_tokens,
        "estimated_finding_tokens": finding_tokens,
        "estimated_direct_cost_units": round(direct_cost, 3),
        "estimated_delegated_cost_units": round(delegated_cost, 3),
    }


def _finding_payload(facets: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for facet in facets:
        finding = _verified_finding(facet)
        if finding is not None:
            claim_passage_ids = {
                passage_id
                for claim in finding.get("claims", [])
                if isinstance(claim, dict)
                for passage_id in claim.get("passage_ids", [])
                if isinstance(passage_id, int) and not isinstance(passage_id, bool)
            }
            output.append(
                {
                    "facet_id": facet["id"],
                    **finding,
                    "locators": [
                        locator
                        for locator in facet.get("locators", [])
                        if isinstance(locator, dict)
                        and locator.get("passage_id") in claim_passage_ids
                    ],
                }
            )
    return output


def evidence_pack_payload(args: argparse.Namespace) -> dict[str, object]:
    if not 1 <= args.limit_per_query <= 5:
        raise ValueError("--limit-per-query must be between 1 and 5")
    if not 1 <= args.max_passages_per_question <= 5:
        raise ValueError("--max-passages-per-question must be between 1 and 5")
    if not 1 <= args.max_passages <= 50:
        raise ValueError("--max-passages must be between 1 and 50")
    if not 100 <= args.max_passage_chars <= 8000:
        raise ValueError("--max-passage-chars must be between 100 and 8000")
    if not 1000 <= args.max_total_chars <= 40_000:
        raise ValueError("--max-total-chars must be between 1000 and 40000")
    if args.task_receipt is None:
        raise ValueError("--task-receipt is required")

    execution = _execution_record(args)
    questions = normalize_questions(load_bounded_json(args.input, "Evidence question file"))
    questions_hash = question_set_hash(questions)
    corpus = args.corpus.resolve()
    index_result = index_payload(
        argparse.Namespace(
            corpus=corpus,
            db=args.db,
            max_chars=args.chunk_chars,
            max_source_bytes=args.max_source_bytes,
            max_corpus_bytes=args.max_corpus_bytes,
        )
    )
    index_path, fingerprint = resolve_index_binding(args.db, corpus)
    task_receipt_path = args.task_receipt.resolve()
    previous_receipt = _load_task_receipt(task_receipt_path, fingerprint)
    previous_facets = {
        (facet["id"], facet["facet_hash"]): facet
        for facet in _warm_facets(previous_receipt)
    } if previous_receipt is not None else {}

    reused_facets: list[dict[str, object]] = []
    missing_questions: list[dict[str, object]] = []
    for question in questions:
        key = (question["id"], facet_hash(question))
        previous = previous_facets.get(key)
        if previous is None:
            missing_questions.append(question)
        else:
            reused_facets.append(previous)

    if args.execution_route == "coordinator-warm" and missing_questions:
        raise ValueError(
            "Task receipt is missing, stale, or lacks current facets; use auto, "
            "coordinator-direct, a low-overhead worker, or an explicit fallback"
        )
    if (
        not missing_questions
        and previous_receipt is not None
        and args.execution_route
        in {"coordinator-direct", "low-overhead-worker", "coordinator-fallback"}
    ):
        raise ValueError(
            "Current facet receipt requires auto or coordinator-warm; do not launch a cold "
            "worker, direct route, or fallback for an unchanged repeat"
        )

    receipts_db: Path | None = None
    receipts_created = False
    search_count = 0
    receipt_hits = 0
    fallback_search_count = 0
    searched_facets: list[dict[str, object]] = []
    searched_passage_ids: list[int] = []
    if missing_questions:
        receipts_db, receipts_created = _receipt_store(args, corpus)
        searched_facets, search_count, receipt_hits, fallback_search_count = _facet_candidates(
            args, missing_questions, receipts_db
        )
        searched_passage_ids = _select_passages(
            searched_facets, args.max_passages_per_question, args.max_passages
        )

    facet_by_id = {
        str(facet["id"]): facet for facet in [*reused_facets, *searched_facets]
    }
    facets = [facet_by_id[str(question["id"])] for question in questions]
    locator_passage_ids = [
        int(passage_id)
        for facet in reused_facets
        if _verified_finding(facet) is None
        for passage_id in facet["passage_ids"]
    ]
    passage_ids = list(dict.fromkeys([*locator_passage_ids, *searched_passage_ids]))
    retrieved = _get_payload(
        index_path,
        passage_ids,
        args.max_passage_chars,
        args.max_total_chars,
    )
    if retrieved.get("not_found"):
        raise ValueError(
            "Task receipt references missing passages; rerun the affected facets through "
            "auto or a declared cold route"
        )

    retrieved_locators = _compact_locators(retrieved.get("results"))
    for facet in facets:
        existing_locators = {
            locator["passage_id"]: locator
            for locator in facet.get("locators", [])
            if isinstance(locator, dict) and isinstance(locator.get("passage_id"), int)
        }
        existing_locators.update(retrieved_locators)
        facet["locators"] = [
            existing_locators[passage_id]
            for passage_id in facet["passage_ids"]
            if passage_id in existing_locators
        ]
        if len(facet["locators"]) != len(facet["passage_ids"]):
            raise ValueError(
                f"Could not preserve all selected locators for facet {facet['id']}"
            )

    finding_hits = sum(_verified_finding(facet) is not None for facet in facets)
    if finding_hits == len(facets):
        retrieval = "finding-receipt"
    elif missing_questions and reused_facets:
        retrieval = "delta"
    elif missing_questions:
        retrieval = "search"
    else:
        retrieval = "task-receipt"

    routing = (
        _route_evidence(args, int(retrieved.get("characters", 0)), len(facets) - finding_hits)
        if args.execution_route == "auto"
        else {
            "recommendation": args.execution_route,
            "reason": execution["reason"],
            "estimated_evidence_tokens": (
                int(retrieved.get("characters", 0)) + 3
            ) // 4,
        }
    )
    if routing["recommendation"] == "receipt-only":
        last_execution: dict[str, object] = {
            "route": "coordinator-warm",
            "reason": "verified-finding-receipt",
        }
    elif args.execution_route == "auto":
        last_execution = {
            "route": "auto",
            "reason": routing["reason"],
            "recommendation": routing["recommendation"],
        }
    else:
        last_execution = execution

    previous_execution = (
        previous_receipt.get("execution")
        if isinstance(previous_receipt, dict)
        else None
    )
    cold_execution: object = None
    if isinstance(previous_execution, dict):
        candidate = previous_execution.get("cold")
        if isinstance(candidate, dict):
            cold_execution = candidate
    if cold_execution is None:
        cold_execution = last_execution

    receipt_gaps = _receipt_gaps(facets)
    optimization = {
        "index": "rebuilt" if index_result["database_rebuilt"] else "reused",
        "retrieval": retrieval,
        "query_batch": (
            "skipped"
            if not missing_questions
            else "partial" if reused_facets else "bounded"
        ),
        "query_fallback": "used" if fallback_search_count else "not-needed",
        "search_receipts": (
            "not-needed"
            if not missing_questions
            else "created" if receipts_created else "reused"
        ),
        "task_receipt": (
            "hit"
            if not missing_questions and previous_receipt is not None
            else "partial" if reused_facets else "miss"
        ),
        "finding_receipt": (
            "hit"
            if finding_hits == len(facets)
            else "partial" if finding_hits else "miss"
        ),
        "selection": "coverage-aware",
        "deduplication": "exact",
        "reopen": "skipped" if not passage_ids else "batched",
        "context_transfer": (
            "capsule-only"
            if routing["recommendation"] == "low-overhead-worker"
            else "not-delegated"
        ),
        "evidence_char_limit": args.max_total_chars,
    }
    task_receipt: dict[str, object] = {
        "version": TASK_RECEIPT_VERSION,
        "route": "retrieval",
        "adapter": "local-index/evidence-pack-v2",
        "index_fingerprint": fingerprint,
        "question_set_hash": questions_hash,
        "execution": {"cold": cold_execution, "last": last_execution},
        "optimization": optimization,
        "facets": _receipt_facets(facets),
        "conflicts": [],
        "gaps": receipt_gaps,
        "next_mode": (
            "direct"
            if finding_hits == len(facets) and not receipt_gaps
            else "retrieval"
        ),
    }
    if previous_receipt != task_receipt:
        _write_task_receipt(task_receipt_path, task_receipt)

    sources, passages = _compact_passages(retrieved.get("results"))
    visible_facets: list[dict[str, object]] = []
    for facet in facets:
        support = facet.get("support_passage_ids", [])
        checks = facet.get("check_passage_ids", [])
        if support and checks:
            coverage = "support-and-check"
        elif support:
            coverage = "support-only"
        elif checks:
            coverage = "check-only"
        else:
            coverage = "no-material-result"
        visible_facets.append(
            {
                "id": facet["id"],
                "coverage": coverage,
                "passage_ids": facet["passage_ids"],
                "support_passage_ids": support,
                "check_passage_ids": checks,
            }
        )

    payload: dict[str, object] = {
        "execution": task_receipt["execution"],
        "optimization": optimization,
        "retrieval": retrieval,
        "index": {
            "fingerprint": fingerprint,
            "updated": bool(index_result["database_rebuilt"]),
            "strategy": index_result["update_strategy"],
            "files": index_result["files_seen"],
            "chunks": index_result["chunks"],
        },
        "search_count": search_count,
        "fallback_search_count": fallback_search_count,
        "receipt_hits": receipt_hits,
        "finding_hits": finding_hits,
        "searched_facets": [str(question["id"]) for question in missing_questions],
        "characters": retrieved.get("characters", 0),
        "has_more": retrieved.get("has_more", False),
        "facets": visible_facets,
        "sources": sources,
        "passages": passages,
        "findings": _finding_payload(facets),
        "gaps": receipt_gaps,
        "next_mode": task_receipt["next_mode"],
        "routing": routing,
    }
    if receipts_db is not None:
        payload["receipt_store"] = {
            "path": str(receipts_db),
            "created": receipts_created,
        }
    payload["task_receipt_path"] = str(task_receipt_path)
    if retrieved.get("truncated_passage_ids"):
        payload["truncated_passage_ids"] = retrieved["truncated_passage_ids"]
    if (
        args.execution_route == "auto"
        and routing["recommendation"] == "low-overhead-worker"
    ):
        pack_path = args.pack_output.resolve()
        payload["pack_path"] = str(pack_path)
        _write_json(pack_path, payload)
        return {
            "execution": payload["execution"],
            "optimization": payload["optimization"],
            "retrieval": retrieval,
            "routing": routing,
            "index": payload["index"],
            "search_count": search_count,
            "receipt_hits": receipt_hits,
            "finding_hits": finding_hits,
            "searched_facets": payload["searched_facets"],
            "characters": payload["characters"],
            "facets": visible_facets,
            "findings": payload["findings"],
            "gaps": receipt_gaps,
            "next_mode": payload["next_mode"],
            "task_receipt_path": str(task_receipt_path),
            "pack_path": str(pack_path),
            "passages_omitted": True,
        }
    return payload


def command_evidence_pack(args: argparse.Namespace) -> int:
    emit_json(evidence_pack_payload(args), args.pretty)
    return 0


def _normalize_findings(raw: object) -> list[dict[str, object]]:
    items = raw.get("findings") if isinstance(raw, dict) else raw
    if not isinstance(items, list) or not items:
        raise ValueError("Findings input must contain a non-empty findings array")
    if len(items) > MAX_EVIDENCE_QUESTIONS:
        raise ValueError(f"At most {MAX_EVIDENCE_QUESTIONS} facet findings are allowed")
    normalized: list[dict[str, object]] = []
    seen: set[str] = set()
    total_claims = 0
    for index, item in enumerate(items):
        location = f"findings[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{location} must be an object")
        unknown = set(item) - {"facet_id", "status", "claims"}
        if unknown:
            raise ValueError(
                f"{location} has unsupported fields: {', '.join(sorted(unknown))}"
            )
        facet_id = required_record_id(item.get("facet_id"), f"{location}.facet_id")
        if facet_id in seen:
            raise ValueError(f"Duplicate finding facet: {facet_id}")
        seen.add(facet_id)
        status = item.get("status")
        if status not in FINDING_STATUSES:
            raise ValueError(
                f"{location}.status must be verified, conflicted, or unresolved"
            )
        raw_claims = item.get("claims")
        if not isinstance(raw_claims, list) or not raw_claims:
            raise ValueError(f"{location}.claims must be a non-empty array")
        if len(raw_claims) > MAX_FINDING_CLAIMS:
            raise ValueError(
                f"{location}.claims allows at most {MAX_FINDING_CLAIMS} entries"
            )
        claims: list[dict[str, object]] = []
        for claim_index, raw_claim in enumerate(raw_claims):
            claim_location = f"{location}.claims[{claim_index}]"
            if not isinstance(raw_claim, dict):
                raise ValueError(f"{claim_location} must be an object")
            claim_unknown = set(raw_claim) - {"text", "passage_ids", "scope"}
            if claim_unknown:
                raise ValueError(
                    f"{claim_location} has unsupported fields: "
                    f"{', '.join(sorted(claim_unknown))}"
                )
            text = required_research_text(
                raw_claim.get("text"), f"{claim_location}.text", MAX_FINDING_TEXT
            )
            passage_ids = raw_claim.get("passage_ids")
            if not isinstance(passage_ids, list) or any(
                not isinstance(value, int) or isinstance(value, bool) or value < 1
                for value in passage_ids
            ):
                raise ValueError(f"{claim_location}.passage_ids is invalid")
            claim: dict[str, object] = {
                "text": text,
                "passage_ids": list(dict.fromkeys(passage_ids)),
            }
            if raw_claim.get("scope") is not None:
                claim["scope"] = required_research_text(
                    raw_claim.get("scope"),
                    f"{claim_location}.scope",
                    MAX_FINDING_SCOPE,
                )
            claims.append(claim)
        total_claims += len(claims)
        normalized.append(
            {"facet_id": facet_id, "status": str(status), "claims": claims}
        )
    if total_claims > MAX_EVIDENCE_QUESTIONS * MAX_FINDING_CLAIMS:
        raise ValueError("Findings input contains too many claims")
    return normalized


def findings_save_payload(args: argparse.Namespace) -> dict[str, object]:
    receipt_path = args.task_receipt.resolve()
    raw_receipt = load_bounded_json(receipt_path, "Task receipt")
    if not isinstance(raw_receipt, dict):
        raise ValueError("Task receipt is invalid or unsupported")
    stored_fingerprint = raw_receipt.get("index_fingerprint")
    if not isinstance(stored_fingerprint, str):
        raise ValueError("Task receipt is invalid or unsupported")
    receipt = _load_task_receipt(receipt_path, stored_fingerprint)
    if receipt is None:
        raise ValueError("Task receipt is invalid or unsupported")
    raw_facets = receipt.get("facets")
    if not isinstance(raw_facets, list):
        raise ValueError("Task receipt facets must be an array")
    facets = {
        str(facet.get("id")): facet
        for facet in raw_facets
        if isinstance(facet, dict) and isinstance(facet.get("id"), str)
    }
    findings = _normalize_findings(
        load_bounded_json(args.input, "Findings input")
    )
    for finding in findings:
        facet_id = str(finding["facet_id"])
        facet = facets.get(facet_id)
        if facet is None:
            raise ValueError(f"Task receipt has no facet {facet_id}")
        allowed_ids = set(facet.get("passage_ids", []))
        status = finding["status"]
        if status == "verified" and not (
            facet.get("support_passage_ids") and facet.get("check_passage_ids")
        ):
            raise ValueError(
                f"Verified finding {facet_id} requires support and check coverage"
            )
        for claim in finding["claims"]:
            if not isinstance(claim, dict):
                continue
            claim_ids = set(claim.get("passage_ids", []))
            if status == "verified" and not claim_ids:
                raise ValueError(
                    f"Verified finding {facet_id} claims require passage_ids"
                )
            if not claim_ids.issubset(allowed_ids):
                raise ValueError(
                    f"Finding {facet_id} references passages outside its facet"
                )
        facet["finding"] = {
            "status": status,
            "claims": finding["claims"],
        }

    execution = _execution_record(args)
    previous_execution = receipt.get("execution")
    cold_execution: object = execution
    if isinstance(previous_execution, dict):
        candidate = previous_execution.get("cold")
        if isinstance(candidate, dict) and candidate.get("route") not in {"auto"}:
            cold_execution = candidate
    receipt["execution"] = {"cold": cold_execution, "last": execution}
    optimization = receipt.get("optimization")
    if not isinstance(optimization, dict):
        optimization = {}
        receipt["optimization"] = optimization
    optimization["finding_receipt"] = "saved"
    optimization["context_transfer"] = (
        "capsule-only"
        if args.execution_route == "low-overhead-worker"
        else "not-delegated"
    )
    gaps = receipt.get("gaps")
    every_verified = all(
        isinstance(facet.get("finding"), dict)
        and facet["finding"].get("status") == "verified"
        for facet in facets.values()
    )
    receipt["next_mode"] = (
        "direct" if every_verified and isinstance(gaps, list) and not gaps else "retrieval"
    )
    _write_task_receipt(receipt_path, receipt)
    return {
        "task_receipt_path": str(receipt_path),
        "saved_facets": [finding["facet_id"] for finding in findings],
        "saved_claims": sum(len(finding["claims"]) for finding in findings),
        "execution": receipt["execution"],
        "next_mode": receipt["next_mode"],
    }


def command_findings_save(args: argparse.Namespace) -> int:
    emit_json(findings_save_payload(args), args.pretty)
    return 0
