from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path

from .common import (
    MAX_QUERY_TEXT,
    MAX_BATCH_INPUT_BYTES,
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
from .index import (
    index_payload,
    iter_source_files,
    resolve_index_binding,
    schema_query_payload,
    validate_output_paths,
    context_start,
    result_item,
    search_row_locator,
)
from .receipts import (
    initialize_receipt_store,
    require_receipt_database,
    validate_receipt_store_connection,
)
from .search import search_payload


MAX_EVIDENCE_QUESTIONS = 50
MAX_QUERIES_PER_QUESTION = 20
MAX_FINDING_CLAIMS = 50
MAX_FINDING_TEXT = 1_000
MAX_FINDING_SCOPE = 500
QUERY_ROLES = {"support", "check"}
QUERY_MODES = {"auto", "literal", "prefix", "fts"}
QUESTION_KINDS = {"lookup", "enumeration", "schema"}
VERIFICATION_MODES = {"exact", "control"}
GROUP_BY_FIELDS = {"source", "section", "schema"}
MAX_ENUMERATION_ITEMS = 50
FINDING_STATUSES = {"confirmed", "interpretation", "conflicted", "unresolved"}
LOCATOR_FIELDS = (
    "passage_id",
    "source",
    "source_path",
    "source_hash",
    "page",
    "section",
    "version",
    "date",
    "line_start",
    "line_end",
)
SCHEMA_LOCATOR_FIELDS = {
    "evidence_id",
    "source",
    "schema_name",
    "block_hash",
    "block_index",
    "record_order",
    "kind",
    "name",
    "path",
    "xsd_line",
    "markdown_line",
    "roles",
}
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
CONTROL_QUESTION_TERMS = {
    "all",
    "any",
    "can",
    "every",
    "must",
    "none",
    "required",
    "все",
    "каждый",
    "можно",
    "несколько",
    "обязателен",
    "обязательно",
    "порядок",
}


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


def _needs_control(question: str, kind: str) -> bool:
    if kind == "enumeration":
        return True
    return any(token.casefold() in CONTROL_QUESTION_TERMS for token in TOKEN.findall(question))


def _automatic_queries(
    question: str, *, requires_check: bool
) -> list[dict[str, str]]:
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
    if requires_check:
        control = f"{anchors[0]}* AND ({' OR '.join(STRUCTURAL_TERMS)})"
        queries.append({"query": control, "mode": "fts", "role": "check"})
    return queries[:MAX_QUERIES_PER_QUESTION]


def _zero_hit_fallbacks(
    question: str,
    planned_queries: list[dict[str, str]],
    *,
    requires_check: bool,
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
    output = {
        "support": {"query": expression, "mode": "fts", "role": "support"},
    }
    if requires_check:
        output["check"] = {
            "query": f"({expression}) AND ({structural})",
            "mode": "fts",
            "role": "check",
        }
    return output


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
    for index, item in enumerate(items, start=1):
        location = f"questions[{index - 1}]"
        if isinstance(item, str):
            question = required_research_text(item, location, MAX_QUERY_TEXT)
            question_id = f"q{index}"
            raw_queries: object = None
        elif isinstance(item, dict):
            unknown = set(item) - {
                "id",
                "question",
                "queries",
                "kind",
                "verification",
                "group_by",
                "max_items",
                "source", "page", "section", "version", "date",
            }
            if unknown:
                raise ValueError(
                    f"{location} has unsupported fields: {', '.join(sorted(unknown))}"
                )
            question = required_research_text(
                item.get("question"), f"{location}.question", MAX_QUERY_TEXT
            )
            question_id = required_record_id(item.get("id", f"q{index}"), f"{location}.id")
            raw_queries = item.get("queries")
            kind = item.get("kind", "lookup")
            verification = item.get("verification")
            group_by = item.get("group_by")
            max_items = item.get("max_items")
        else:
            raise ValueError(f"{location} must be text or an object")
        if isinstance(item, str):
            kind = "lookup"
            verification = None
            group_by = None
            max_items = None
        if kind not in QUESTION_KINDS:
            raise ValueError(f"{location}.kind must be lookup, enumeration, or schema")
        if verification is not None and verification not in VERIFICATION_MODES:
            raise ValueError(f"{location}.verification must be exact or control")
        if group_by is not None and group_by not in GROUP_BY_FIELDS:
            raise ValueError(f"{location}.group_by must be source, section, or schema")
        if group_by is None and kind in {"enumeration", "schema"}:
            group_by = "schema" if kind == "schema" else "section"
        if max_items is None:
            max_items = 12 if kind in {"enumeration", "schema"} else 3
        if (
            not isinstance(max_items, int)
            or isinstance(max_items, bool)
            or not 1 <= max_items <= MAX_ENUMERATION_ITEMS
        ):
            raise ValueError(
                f"{location}.max_items must be between 1 and {MAX_ENUMERATION_ITEMS}"
            )
        if question_id in seen_ids:
            raise ValueError(f"Duplicate question id: {question_id}")
        seen_ids.add(question_id)
        if raw_queries is None:
            requires_check = (
                verification == "control"
                if verification is not None
                else _needs_control(question, str(kind))
            )
            queries = _automatic_queries(question, requires_check=requires_check)
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
            has_explicit_check = any(query["role"] == "check" for query in queries)
            requires_check = (
                verification == "control"
                if verification is not None
                else has_explicit_check
            )
        roles = {str(query["role"]) for query in queries}
        required_roles = {"support"}
        if not required_roles.issubset(roles):
            missing = ", ".join(sorted(required_roles - roles))
            raise ValueError(
                f"{location}.queries are missing required roles: {missing}"
            )
        normalized.append(
            {
                "id": question_id,
                "question": question,
                "queries": queries,
                "kind": kind,
                "verification": "control" if requires_check else "exact",
                "requires_check": requires_check,
                "group_by": group_by,
                "max_items": max_items,
                "filters": {
                    key: required_research_text(item[key], f"{location}.{key}", 1000)
                    for key in ("source", "page", "section", "version", "date")
                    if isinstance(item, dict) and item.get(key) is not None
                },
            }
        )
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
        {
            "id": question["id"],
            "question": question["question"],
            "filters": question.get("filters", {}),
            "queries": question["queries"],
            "kind": question["kind"],
            "verification": question["verification"],
            "group_by": question["group_by"],
            "max_items": question["max_items"],
        },
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
            for field in ("line_start", "line_end"):
                value = locator.get(field)
                if value is not None and (
                    not isinstance(value, int) or isinstance(value, bool) or value < 1
                ):
                    raise ValueError(f"{location}.{field} is invalid")
            locator_passage_ids.append(passage_id)
        if len(locator_passage_ids) != len(set(locator_passage_ids)) or set(
            locator_passage_ids
        ) != passage_ids:
            raise ValueError(
                f"Task receipt facet {index}.locators must cover passage_ids exactly"
            )
        schema_locators = facet.get("schema_locators", [])
        if not isinstance(schema_locators, list):
            raise ValueError(f"Task receipt facet {index}.schema_locators is invalid")
        allowed_evidence_ids: set[str] = set()
        for schema_index, locator in enumerate(schema_locators):
            location = f"Task receipt facet {index}.schema_locators[{schema_index}]"
            if not isinstance(locator, dict) or set(locator) - SCHEMA_LOCATOR_FIELDS:
                raise ValueError(f"{location} is invalid")
            evidence_id = locator.get("evidence_id")
            if (
                not isinstance(evidence_id, str)
                or not evidence_id
                or len(evidence_id) > 1_000
            ):
                raise ValueError(f"{location}.evidence_id is invalid")
            required_research_text(locator.get("source"), f"{location}.source")
            for field in ("schema_name", "kind", "name", "path"):
                if locator.get(field) is not None:
                    required_research_text(locator[field], f"{location}.{field}")
            block_hash = locator.get("block_hash")
            if (
                not isinstance(block_hash, str)
                or len(block_hash) != 64
                or any(character not in "0123456789abcdef" for character in block_hash)
            ):
                raise ValueError(f"{location}.block_hash is invalid")
            for field in (
                "block_index",
                "record_order",
                "xsd_line",
                "markdown_line",
            ):
                value = locator.get(field)
                if (
                    not isinstance(value, int)
                    or isinstance(value, bool)
                    or value < 1
                ):
                    raise ValueError(f"{location}.{field} is invalid")
            roles = locator.get("roles", [])
            if not isinstance(roles, list) or not roles or any(
                role not in QUERY_ROLES for role in roles
            ):
                raise ValueError(f"{location}.roles is invalid")
            allowed_evidence_ids.add(evidence_id)
        finding = facet.get("finding")
        if finding is not None:
            if (
                not isinstance(finding, dict)
                or set(finding) - {"status", "claims", "reason"}
                or not isinstance(finding.get("status"), str)
                or finding.get("status") not in FINDING_STATUSES
            ):
                raise ValueError(f"Task receipt facet {index}.finding is invalid")
            normalized = _normalize_findings([{
                "facet_id": facet_id, **{key: value for key, value in finding.items() if key != "status"},
            }])[0]
            if normalized["status"] != finding["status"]:
                raise ValueError("Task receipt finding status disagrees with its individual claims")
            claims = finding.get("claims")
            if finding.get("reason") is not None:
                required_research_text(finding["reason"], "finding.reason", MAX_FINDING_TEXT)
            if not isinstance(claims, list) or (not claims and finding.get("status") != "unresolved") or len(claims) > MAX_FINDING_CLAIMS:
                raise ValueError(f"Task receipt facet {index}.finding.claims is invalid")
            for claim_index, claim in enumerate(claims):
                if not isinstance(claim, dict):
                    raise ValueError(
                        f"Task receipt facet {index}.finding.claims[{claim_index}] is invalid"
                    )
                if set(claim) - {"text", "passage_ids", "evidence_ids", "scope", "status", "basis", "limits"}:
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
                evidence_ids = claim.get("evidence_ids", [])
                if not isinstance(evidence_ids, list) or any(
                    not isinstance(value, str) or not value
                    for value in evidence_ids
                ):
                    raise ValueError(
                        f"Task receipt facet {index}.finding.claims[{claim_index}]"
                        ".evidence_ids is invalid"
                    )
                if not set(evidence_ids).issubset(allowed_evidence_ids):
                    raise ValueError(
                        f"Task receipt facet {index}.finding references outside schema evidence"
                    )
                if claim.get("status") == "confirmed" and not (
                    claim_ids or evidence_ids
                ):
                    raise ValueError(
                        f"Task receipt facet {index}.confirmed claim requires evidence locators"
                    )
                if claim.get("scope") is not None:
                    required_research_text(
                        claim["scope"],
                        f"Task receipt facet {index}.finding.claims[{claim_index}].scope",
                        MAX_FINDING_SCOPE,
                    )
    if len(set(all_passage_ids)) > 10_000:
        raise ValueError("Task receipt exceeds 10000 locators; use a separate investigation scope")
    return raw


def _write_json(path: Path, payload: object, *, max_bytes: int | None = None) -> None:
    serialized = (json.dumps(payload, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")) + "\n").encode("utf-8")
    if max_bytes is not None and len(serialized) > max_bytes:
        raise ValueError(f"Serialized artifact exceeds {max_bytes} bytes; narrow the scope")
    resolved = path.resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{resolved.name}.",
            suffix=".tmp",
            dir=resolved.parent,
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(serialized)
        if os.name != "nt":
            temporary_path.chmod(0o600)
        temporary_path.replace(resolved)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _write_task_receipt(path: Path, payload: dict[str, object]) -> None:
    _write_json(path, payload, max_bytes=MAX_BATCH_INPUT_BYTES)


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
    db: Path,
    passage_ids: list[int],
    max_chars: int,
    max_total_chars: int,
    passage_queries: dict[int, str] | None = None,
) -> dict[str, object]:
    if not passage_ids:
        return {
            "result_count": 0,
            "characters": 0,
            "has_more": False,
            "not_found": [],
            "results": [],
        }
    # Selection already interleaves facets. Prefer whole chunks instead of forcing
    # every candidate into an equally tiny prefix; explicit continuations cover the rest.
    with database(db, readonly=True) as connection:
        rows = connection.execute(
            "SELECT rowid AS passage_id, * FROM chunks WHERE rowid IN ("
            + ",".join("?" for _ in passage_ids) + ")", passage_ids
        ).fetchall()
    by_id = {row["passage_id"]: row for row in rows}
    results: list[dict[str, object]] = []
    not_found: list[int] = []
    truncated: list[int] = []
    characters = 0
    continuations: list[dict[str, object]] = []
    for passage_id in passage_ids:
        row = by_id.get(passage_id)
        if row is None:
            not_found.append(passage_id)
            continue
        allowed = min(max_chars, max_total_chars - characters)
        if allowed < 100:
            continuations.append({"passage_id": passage_id, "start_char": 0, "reason": "not-returned"})
            continue
        full_text = str(row["text"] or "")
        start = context_start(full_text, (passage_queries or {}).get(passage_id, ""), allowed)
        text = full_text[start:start + allowed]
        incomplete = start > 0 or start + len(text) < len(full_text)
        results.append(result_item(row, text, text_truncated=incomplete, text_start_char=start))
        characters += len(text)
        if incomplete:
            truncated.append(passage_id)
            if start:
                continuations.append({"passage_id": passage_id, "start_char": 0, "end_char": start, "reason": "prefix-not-returned"})
            if start + len(text) < len(full_text):
                continuations.append({"passage_id": passage_id, "start_char": start + len(text), "reason": "suffix-not-returned"})
    payload: dict[str, object] = {
        "result_count": len(results),
        "characters": characters,
        "has_more": bool(continuations),
        "continuations": continuations,
        "locators": [search_row_locator(row) for row in rows],
        "not_found": not_found,
        "results": results,
    }
    if truncated:
        payload["truncated_passage_ids"] = truncated
    return payload


def _search_namespace(
    args: argparse.Namespace,
    query: dict[str, str],
    receipts_db: Path | None,
    *,
    limit: int | None = None,
    offset: int = 0,
    filters: dict[str, str] | None = None,
) -> argparse.Namespace:
    return argparse.Namespace(
        db=args.db,
        query=query["query"],
        mode=query["mode"],
        **{key: (filters or {}).get(key) for key in ("source", "page", "section", "version", "date")},
        limit=limit or args.limit_per_query,
        offset=offset,
        max_chars=240,
        # This in-process batch carries complete locator/alias metadata as well
        # as snippets; the selected evidence has a separate user output budget.
        max_total_chars=max(24000, (limit or args.limit_per_query) * 1600),
        snippet_tokens=16,
        receipts_db=receipts_db,
        research_db=None,
        facet_id=None,
        receipt_id=None,
        refresh=False,
        read_only_receipts=False,
        dedupe_exact=True,
        max_per_source=0,
        _source_paths=getattr(args, "_source_paths", None),
        pretty=False,
    )


def _candidate_group(item: dict[str, object], group_by: object) -> str | None:
    if group_by == "source":
        value = item.get("source")
    elif group_by in {"section", "schema"}:
        value = item.get("section")
    else:
        return None
    return str(value) if value is not None else None


def _schema_fact_id(item: dict[str, object]) -> str:
    return "schema:" + ":".join(
        str(item.get(key, ""))
        for key in ("source", "block_index", "record_order")
    )


def _schema_facts_for_question(
    args: argparse.Namespace,
    question: dict[str, object],
    character_budget: int,
) -> tuple[list[dict[str, object]], int, list[dict[str, object]]]:
    if question.get("kind") != "schema" or character_budget < 100:
        return [], 0, []
    if any(key != "source" for key in question.get("filters", {})):
        # Schema records have source/block identity, not passage metadata. Do not
        # silently broaden a version/page/section-filtered search with unfiltered facts.
        return [], 0, []
    terms: list[tuple[str, str]] = []
    seen_terms: set[str] = set()
    for raw_query in question["queries"]:
        if not isinstance(raw_query, dict):
            continue
        role = str(raw_query["role"])
        ranked = sorted(
            _question_tokens(str(raw_query["query"])),
            key=lambda token: (
                -int(
                    "_" in token
                    or any(character.isdigit() for character in token)
                    or (
                        any(character.isupper() for character in token)
                        and not token.isupper()
                    )
                ),
                -len(token),
            ),
        )
        for term in ranked[:2]:
            key = term.casefold()
            if key not in seen_terms:
                seen_terms.add(key)
                terms.append((term, role))
    facts: dict[str, dict[str, object]] = {}
    continuations: list[dict[str, object]] = []
    query_count = 0
    used = 0
    for term, role in terms[:3]:
        remaining_items = int(question["max_items"]) - len(facts)
        remaining_chars = character_budget - used
        if remaining_items <= 0 or remaining_chars < 100:
            break
        query_args = argparse.Namespace(
                db=args.db,
                query=term,
                kind=None,
                source=question.get("filters", {}).get("source"),
                schema=None,
                limit=min(50, remaining_items),
                offset=0,
                max_total_chars=remaining_chars,
                purpose="custom-adapter",
                purpose_reason="evidence-pack structural facet",
                task_receipt=None,
                gap_facet=None,
            )
        marker = {"tool": "schema-query", "query": term, "role": role,
                  "source": query_args.source, "offset": 0, "start_char": 0,
                  "index_fingerprint": getattr(args, "_index_fingerprint", None)}
        try:
            result = schema_query_payload(query_args)
        except ValueError as exc:
            if "too small for the schema response envelope" not in str(exc):
                raise
            continuations.append({**marker, "reason": "schema-budget-insufficient"})
            query_count += 1
            continue
        query_count += 1
        marker["index_fingerprint"] = result["index_fingerprint"]
        incomplete_record = False
        for position, raw in enumerate(result.get("results", [])):
            if not isinstance(raw, dict):
                continue
            if "record_fragment" in raw:
                # The prefix was not delivered as evidence. Resume this exact
                # record from its beginning, never promote partial JSON to a fact.
                continuations.append({**marker, "offset": position,
                                      "reason": "schema-record-exceeds-budget",
                                      "record_total_chars": raw["record_total_chars"]})
                incomplete_record = True
                break
            evidence_id = _schema_fact_id(raw)
            current = facts.get(evidence_id)
            if current is None:
                candidate = {**raw, "evidence_id": evidence_id, "roles": [role]}
                candidate_characters = len(
                    json.dumps(candidate, ensure_ascii=False, separators=(",", ":"))
                )
                if used + candidate_characters > character_budget:
                    continuations.append({**marker, "offset": position,
                                          "reason": "schema-record-exceeds-budget"})
                    incomplete_record = True
                    break
                facts[evidence_id] = candidate
                used += candidate_characters
                continue
            roles = current["roles"]
            if isinstance(roles, list) and role not in roles:
                roles.append(role)
        if result.get("has_more") and not incomplete_record:
            continuations.append({**marker, "offset": result["next_offset"],
                                  "start_char": result.get("next_start_char", 0),
                                  "reason": "schema-results-remaining"})
    return list(facts.values()), query_count, continuations


def _facet_candidates(
    args: argparse.Namespace,
    questions: list[dict[str, object]],
    receipts_db: Path | None,
) -> tuple[list[dict[str, object]], int, int, int, int]:
    facets: list[dict[str, object]] = []
    search_count = 0
    receipt_hits = 0
    fallback_search_count = 0
    schema_query_count = 0
    schema_facet_count = sum(
        question.get("kind") == "schema" for question in questions
    )
    schema_character_budget = (
        max(100, (args.max_total_chars // 2) // max(1, schema_facet_count))
        if schema_facet_count
        else 0
    )
    for question in questions:
        candidates: list[dict[str, object]] = []
        receipt_ids: list[str] = []
        continuations: list[dict[str, object]] = []
        planned_queries = [
            {key: str(value) for key, value in raw_query.items()}
            for raw_query in question["queries"]
            if isinstance(raw_query, dict)
        ]
        executed = {
            (query["query"], query["mode"], query["role"])
            for query in planned_queries
        }
        required_roles = ["support"]
        if question.get("requires_check"):
            required_roles.append("check")
        role_hits = {role: False for role in required_roles}
        query_limit = (
            int(question["max_items"])
            if question.get("kind") in {"enumeration", "schema"}
            else args.limit_per_query
        )

        def execute_query(query: dict[str, str], *, fallback: bool = False) -> None:
            nonlocal search_count, receipt_hits, fallback_search_count
            offset = 0
            role = query["role"]
            for page_index in range(3):
                result = search_payload(
                    _search_namespace(
                        args,
                        query,
                        receipts_db,
                        limit=query_limit,
                        offset=offset,
                        filters=question.get("filters", {}),
                    )
                )
                search_count += 1
                if fallback:
                    fallback_search_count += 1
                if result.get("receipt_hit") is True:
                    receipt_hits += 1
                receipt_id = result.get("receipt_id")
                if isinstance(receipt_id, str) and receipt_id not in receipt_ids:
                    receipt_ids.append(receipt_id)
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
                            {
                                "passage_id": passage_id,
                                "role": role,
                                "rank": page_index * query_limit + rank,
                                "group": _candidate_group(
                                    item, question.get("group_by")
                                ),
                                "also_in": item.get("also_in", []),
                            }
                        )
                if result.get("has_more"):
                    continuations[:] = [entry for entry in continuations if entry["query"] != query]
                    continuations.append({"query": query, "offset": result.get("next_offset"), "filters": question.get("filters", {})})
                else:
                    continuations[:] = [entry for entry in continuations if entry["query"] != query]
                if question.get("kind") not in {"enumeration", "schema"}:
                    break
                if question.get("group_by") is None:
                    covered = len(
                        {
                            candidate["passage_id"]
                            for candidate in candidates
                            if candidate["role"] == role
                        }
                    )
                else:
                    covered = len(
                        {
                            candidate["group"]
                            for candidate in candidates
                            if candidate["role"] == role
                            and candidate.get("group") is not None
                        }
                    )
                if covered >= int(question["max_items"]):
                    break
                next_offset = result.get("next_offset")
                if not result.get("has_more") or not isinstance(next_offset, int):
                    break
                offset = next_offset

        for query in planned_queries:
            execute_query(query)

        fallbacks = _zero_hit_fallbacks(
            str(question["question"]),
            planned_queries,
            requires_check=bool(question.get("requires_check")),
        )
        for role in required_roles:
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
                    "group": candidate.get("group"),
                    "also_in": candidate.get("also_in", []),
                },
            )
            roles = current["roles"]
            if isinstance(roles, list) and candidate["role"] not in roles:
                roles.append(candidate["role"])

        ordered: list[dict[str, object]] = []
        seen: set[int] = set()
        for role in required_roles:
            for candidate in merged.values():
                passage_id = int(candidate["passage_id"])
                roles = candidate["roles"]
                if isinstance(roles, list) and role in roles and passage_id not in seen:
                    seen.add(passage_id)
                    ordered.append(candidate)
                    break
        grouped_candidates: list[dict[str, object]] = []
        if question.get("group_by") is not None:
            seen_groups: set[str] = set()
            for candidate in merged.values():
                group = candidate.get("group")
                if isinstance(group, str) and group not in seen_groups:
                    seen_groups.add(group)
                    grouped_candidates.append(candidate)
        for candidate in [*grouped_candidates, *merged.values()]:
            passage_id = int(candidate["passage_id"])
            if passage_id not in seen:
                seen.add(passage_id)
                ordered.append(candidate)
        schema_facts, schema_queries, schema_continuations = _schema_facts_for_question(
            args, question, schema_character_budget
        )
        schema_query_count += schema_queries
        facets.append(
            {
                "id": question["id"],
                "facet_hash": facet_hash(question),
                "question": question["question"],
                "queries": planned_queries,
                "query_continuations": [*continuations, *schema_continuations],
                "aliases": {str(item["passage_id"]): item["also_in"] for item in merged.values() if item.get("also_in")},
                "candidates": ordered,
                "receipt_ids": receipt_ids,
                "kind": question["kind"],
                "requires_check": question["requires_check"],
                "group_by": question["group_by"],
                "selection_limit": (
                    int(question["max_items"])
                    if question.get("kind") == "enumeration"
                    else min(int(question["max_items"]), 2)
                    if question.get("kind") == "schema"
                    else args.max_passages_per_question
                ),
                "schema_facts": schema_facts,
            }
        )
    return (
        facets,
        search_count,
        receipt_hits,
        fallback_search_count,
        schema_query_count,
    )


def _select_passages(
    facets: list[dict[str, object]], max_per_question: int, max_passages: int
) -> list[int]:
    selected: list[int] = []
    selected_set: set[int] = set()
    highest_limit = max(
        (
            int(facet.get("selection_limit", max_per_question))
            for facet in facets
        ),
        default=max_per_question,
    )
    for position in range(highest_limit):
        for facet in facets:
            facet_limit = int(facet.get("selection_limit", max_per_question))
            if position >= facet_limit:
                continue
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
        facet_limit = int(facet.get("selection_limit", max_per_question))
        chosen = [
            candidate
            for candidate in candidates
            if int(candidate["passage_id"]) in selected_set
        ][:facet_limit]
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
            "question": facet.get("question"),
            "queries": facet.get("queries", []),
            "retrieval_budget": facet.get("retrieval_budget", {}),
            "query_continuations": facet.get("query_continuations", []),
            "aliases": facet.get("aliases", {}),
            **({"previous_finding": facet["previous_finding"]} if facet.get("previous_finding") else {}),
            "passage_ids": facet["passage_ids"],
            "support_passage_ids": facet.get("support_passage_ids", []),
            "check_passage_ids": facet.get("check_passage_ids", []),
            "receipt_ids": facet.get("receipt_ids", []),
            "locators": facet.get("locators", []),
            "kind": facet.get("kind", "lookup"),
            "requires_check": bool(facet.get("requires_check", True)),
            "group_by": facet.get("group_by"),
            "selection_limit": facet.get("selection_limit", 3),
            "schema_locators": [
                {
                    key: fact.get(key)
                    for key in (
                        "evidence_id",
                        "source",
                        "schema_name",
                        "block_hash",
                        "block_index",
                        "record_order",
                        "kind",
                        "name",
                        "path",
                        "xsd_line",
                        "markdown_line",
                        "roles",
                    )
                    if fact.get(key) is not None
                }
                for fact in (facet.get("schema_facts") or facet.get("schema_locators", []))
                if isinstance(fact, dict)
            ],
            "checks": [
                role
                for role, key in (
                    ("support", "support_passage_ids"),
                    ("control", "check_passage_ids"),
                )
                if facet.get(key) or _schema_role_covered(facet, "check" if role == "control" else role)
            ],
            **(
                {"finding": facet["finding"]}
                if isinstance(facet.get("finding"), dict)
                else {}
            ),
        }
        for facet in facets
    ]


def _schema_role_covered(facet: dict[str, object], role: str) -> bool:
    records = facet.get("schema_facts") or facet.get("schema_locators") or []
    return any(
        isinstance(record, dict)
        and role in record.get("roles", [])
        for record in records
    )


def _receipt_gaps(facets: list[dict[str, object]]) -> list[dict[str, object]]:
    gaps: list[dict[str, object]] = []
    for facet in facets:
        if _verified_finding(facet) is not None:
            continue
        if any(item.get("tool") == "schema-query" for item in facet.get("query_continuations", [])):
            gaps.append({"facet_id": facet["id"], "reason": "schema-evidence-incomplete"})
        finding = facet.get("finding")
        if isinstance(finding, dict):
            gaps.append({
                "facet_id": facet["id"],
                "reason": f"finding-{finding['status']}",
                **({"finding_reason": finding["reason"]} if finding.get("reason") else {}),
            })
            continue
        support = bool(facet.get("support_passage_ids")) or _schema_role_covered(
            facet, "support"
        )
        control = bool(facet.get("check_passage_ids")) or _schema_role_covered(
            facet, "check"
        )
        if not support and not control:
            reason = "no-material-result"
        elif not support:
            reason = "support-not-found"
        elif facet.get("requires_check") and not control:
            reason = "control-not-found"
        else:
            reason = "candidates-require-verification"
        gaps.append({"facet_id": facet["id"], "reason": reason})
    return gaps


def _warm_facets(receipt: dict[str, object]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for raw in receipt["facets"]:
        if not isinstance(raw, dict):
            continue
        if raw.get("stale"):
            continue
        if raw.get("kind") == "schema" and not isinstance(raw.get("finding"), dict):
            continue
        output.append(
            {
                "id": raw["id"],
                "facet_hash": raw["facet_hash"],
                "question": raw.get("question"),
                "queries": raw.get("queries", []),
                "retrieval_budget": raw.get("retrieval_budget", {}),
                "query_continuations": raw.get("query_continuations", []),
                "aliases": raw.get("aliases", {}),
                **({"previous_finding": raw["previous_finding"]} if raw.get("previous_finding") else {}),
                "passage_ids": list(raw.get("passage_ids", [])),
                "support_passage_ids": list(raw.get("support_passage_ids", [])),
                "check_passage_ids": list(raw.get("check_passage_ids", [])),
                "receipt_ids": list(raw.get("receipt_ids", [])),
                "locators": list(raw.get("locators", [])),
                "kind": raw.get("kind", "lookup"),
                "requires_check": bool(raw.get("requires_check", True)),
                "group_by": raw.get("group_by"),
                "selection_limit": raw.get("selection_limit", 3),
                "schema_locators": list(raw.get("schema_locators", [])),
                "schema_facts": [],
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
            "line_start",
            "line_end",
            "text_start_char",
            "text_truncated",
            "also_in",
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
    if (not facet.get("stale") and isinstance(finding, dict)
            and finding.get("status") == "confirmed"):
        return finding
    return None


def _routing_profile(path: Path | None) -> dict[str, float | None]:
    defaults = {
        "parent_input_cost_ratio": 1.0,
        "worker_input_cost_ratio": None,
        "worker_output_cost_ratio": None,
        "worker_startup_tokens": None,
        "parent_context_tokens": 0.0,
        "expected_parent_turns": 1.0,
        "expected_delegated_parent_turns": 1.0,
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
        if not math.isfinite(value):
            raise ValueError(f"Routing profile {key} must be finite")
        profile[key] = float(value)
    for key in (
        "parent_input_cost_ratio",
        "worker_input_cost_ratio",
        "worker_output_cost_ratio",
        "expected_parent_turns",
        "expected_delegated_parent_turns",
        "finding_tokens_per_facet",
    ):
        if profile[key] is not None and profile[key] <= 0:
            raise ValueError(f"Routing profile {key} must be positive")
    if profile["worker_startup_tokens"] is not None and profile["worker_startup_tokens"] < 0:
        raise ValueError("Routing profile worker_startup_tokens must not be negative")
    if profile["parent_context_tokens"] < 0:
        raise ValueError("Routing profile parent_context_tokens must not be negative")
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
            "reason": "saved-finding-hit",
            "estimated_evidence_tokens": 0,
            "estimated_finding_tokens": 0,
        }
    profile = _routing_profile(args.routing_profile)
    evidence_tokens = (max(0, evidence_characters) + 3) // 4
    finding_tokens = max(
        1, round(facets_needing_model * profile["finding_tokens_per_facet"])
    )
    parent_context_tokens = float(
        args.parent_context_tokens
        if args.parent_context_tokens is not None
        else profile["parent_context_tokens"]
    )
    direct_turns = float(
        args.expected_direct_turns
        if args.expected_direct_turns is not None
        else profile["expected_parent_turns"]
    )
    delegated_parent_turns = float(
        args.expected_delegated_parent_turns
        if args.expected_delegated_parent_turns is not None
        else profile["expected_delegated_parent_turns"]
    )
    if parent_context_tokens < 0:
        raise ValueError("--parent-context-tokens must not be negative")
    if not math.isfinite(direct_turns) or not math.isfinite(delegated_parent_turns) or direct_turns <= 0 or delegated_parent_turns <= 0:
        raise ValueError("Expected routing turns must be positive")
    direct_cost = (
        (parent_context_tokens + evidence_tokens)
        * profile["parent_input_cost_ratio"]
        * direct_turns
    )
    has_cost_signal = (
        args.routing_profile is not None
        or args.parent_context_tokens is not None
        or args.expected_direct_turns is not None
        or args.expected_delegated_parent_turns is not None
    )
    missing_worker_costs = [key for key in (
        "worker_input_cost_ratio", "worker_output_cost_ratio", "worker_startup_tokens",
    ) if profile[key] is None]
    if missing_worker_costs:
        return {
            "recommendation": "coordinator-direct",
            "reason": "incomplete-worker-costs" if has_cost_signal else "no-routing-cost-signal",
            "estimated_evidence_tokens": evidence_tokens,
            "estimated_finding_tokens": finding_tokens,
            "parent_context_tokens": round(parent_context_tokens),
            "expected_direct_turns": direct_turns,
            "expected_delegated_parent_turns": delegated_parent_turns,
            "estimated_direct_cost_units": round(direct_cost, 3),
            "estimated_delegated_cost_units": None,
            "missing_cost_inputs": missing_worker_costs,
        }
    delegated_cost = (
        parent_context_tokens
        * profile["parent_input_cost_ratio"]
        * delegated_parent_turns
        + profile["worker_startup_tokens"] * profile["worker_input_cost_ratio"]
        + evidence_tokens * profile["worker_input_cost_ratio"]
        + finding_tokens * profile["worker_output_cost_ratio"]
        + finding_tokens
        * profile["parent_input_cost_ratio"]
        * delegated_parent_turns
    )
    threshold = direct_cost * (1 - profile["minimum_savings_fraction"])
    if has_cost_signal and delegated_cost <= threshold:
        recommendation = "low-overhead-worker"
        reason = "measured-worker-break-even"
    else:
        recommendation = "coordinator-direct"
        reason = (
            "no-routing-cost-signal"
            if not has_cost_signal
            else "worker-not-below-break-even"
        )
    return {
        "recommendation": recommendation,
        "reason": reason,
        "estimated_evidence_tokens": evidence_tokens,
        "estimated_finding_tokens": finding_tokens,
        "parent_context_tokens": round(parent_context_tokens),
        "expected_direct_turns": direct_turns,
        "expected_delegated_parent_turns": delegated_parent_turns,
        "estimated_direct_cost_units": round(direct_cost, 3),
        "estimated_delegated_cost_units": round(delegated_cost, 3),
    }


def _finding_payload(facets: list[dict[str, object]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for facet in facets:
        finding = facet.get("finding")
        if isinstance(finding, dict):
            claim_passage_ids = {
                passage_id
                for claim in finding.get("claims", [])
                if isinstance(claim, dict)
                for passage_id in claim.get("passage_ids", [])
                if isinstance(passage_id, int) and not isinstance(passage_id, bool)
            }
            claim_evidence_ids = {
                evidence_id
                for claim in finding.get("claims", [])
                if isinstance(claim, dict)
                for evidence_id in claim.get("evidence_ids", [])
                if isinstance(evidence_id, str)
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
                    "schema_locators": [
                        locator
                        for locator in facet.get("schema_locators", [])
                        if isinstance(locator, dict)
                        and locator.get("evidence_id") in claim_evidence_ids
                    ],
                }
            )
    return output


def evidence_pack_payload(args: argparse.Namespace) -> dict[str, object]:
    if not 1 <= args.limit_per_query <= 50:
        raise ValueError("--limit-per-query must be between 1 and 50")
    if not 1 <= args.max_passages_per_question <= 50:
        raise ValueError("--max-passages-per-question must be between 1 and 50")
    if not 1 <= args.max_passages <= 50:
        raise ValueError("--max-passages must be between 1 and 50")
    if not 100 <= args.max_passage_chars <= 100_000:
        raise ValueError("--max-passage-chars must be between 100 and 100000")
    if not 1000 <= args.max_total_chars <= 200_000:
        raise ValueError("--max-total-chars must be between 1000 and 200000")
    if args.task_receipt is None:
        raise ValueError("--task-receipt is required")

    execution = _execution_record(args)
    questions = normalize_questions(load_bounded_json(args.input, "Evidence question file"))
    questions_hash = question_set_hash(questions)
    corpus = args.corpus.resolve()
    args._source_paths = list(iter_source_files(corpus))
    receipt_db = args.receipts_db or args.db.with_name(f"{args.db.stem}.receipts.sqlite")
    validate_output_paths(
        corpus, [args.db, receipt_db, args.task_receipt, getattr(args, "pack_output", None)],
        [args.input, getattr(args, "routing_profile", None)],
        index_path=args.db,
        source_paths=args._source_paths,
    )
    index_result = index_payload(
        argparse.Namespace(
            corpus=corpus,
            db=args.db,
            max_chars=args.chunk_chars,
            max_source_bytes=args.max_source_bytes,
            max_corpus_bytes=args.max_corpus_bytes,
            _source_paths=args._source_paths,
        )
    )
    index_path, fingerprint = resolve_index_binding(args.db, corpus)
    args._index_fingerprint = fingerprint
    task_receipt_path = args.task_receipt.resolve()
    previous_receipt = _load_task_receipt(task_receipt_path, fingerprint)
    if previous_receipt is None and task_receipt_path.exists():
        raw_previous = load_bounded_json(task_receipt_path, "Task receipt")
        if isinstance(raw_previous, dict) and isinstance(raw_previous.get("index_fingerprint"), str):
            previous_receipt = _load_task_receipt(task_receipt_path, raw_previous["index_fingerprint"])
            if previous_receipt is not None:
                if previous_receipt.get("corpus_path") != str(corpus):
                    raise ValueError("Task receipt belongs to another corpus")
                for facet in previous_receipt["facets"]:
                    facet["stale"] = True
                    facet.setdefault("evidence_fingerprint", previous_receipt["index_fingerprint"])
                # Historical analytical state survives, but none of it is warm evidence.
                previous_receipt["gaps"] = [*(gap for gap in previous_receipt.get("gaps", [])
                                             if gap.get("reason") != "source-changed"),
                    *({"facet_id": facet["id"], "reason": "source-changed"} for facet in previous_receipt["facets"])]
    previous_facets = {
        (facet["id"], facet["facet_hash"]): facet
        for facet in _warm_facets(previous_receipt)
    } if previous_receipt is not None else {}

    reused_facets: list[dict[str, object]] = []
    missing_questions: list[dict[str, object]] = []
    reopened_for_depth: set[str] = set()
    retrieval_budget = {key: getattr(args, key) for key in (
        "limit_per_query", "max_passages_per_question", "max_passages",
        "max_passage_chars", "max_total_chars",
    )}
    for question in questions:
        key = (question["id"], facet_hash(question))
        previous = previous_facets.get(key)
        if previous is not None and _verified_finding(previous) is None and any(
            value > previous.get("retrieval_budget", {}).get(name, 0)
            for name, value in retrieval_budget.items()
        ):
            old_budget = previous.get("retrieval_budget", {})
            candidate_budget_increased = any(
                retrieval_budget[name] > old_budget.get(name, 0)
                for name in ("limit_per_query", "max_passages_per_question", "max_passages")
            )
            if candidate_budget_increased or question["kind"] == "schema":
                previous = None
            else:
                # More passage context needs reopening, not repeating the search.
                previous.pop("finding", None)
                reopened_for_depth.add(str(question["id"]))
        if previous is None:
            missing_questions.append(question)
        else:
            reused_facets.append(previous)

    if args.execution_route == "coordinator-warm" and missing_questions:
        raise ValueError(
            "Task receipt is missing, stale, or lacks current facets; use auto, "
            "coordinator-direct, a low-overhead worker, or an explicit fallback"
        )

    receipts_db: Path | None = None
    receipts_created = False
    search_count = 0
    receipt_hits = 0
    fallback_search_count = 0
    schema_query_count = 0
    searched_facets: list[dict[str, object]] = []
    searched_passage_ids: list[int] = []
    if missing_questions:
        receipts_db, receipts_created = _receipt_store(args, corpus)
        (
            searched_facets,
            search_count,
            receipt_hits,
            fallback_search_count,
            schema_query_count,
        ) = _facet_candidates(args, missing_questions, receipts_db)
        searched_passage_ids = _select_passages(
            searched_facets, args.max_passages_per_question, args.max_passages
        )

    facet_by_id = {
        str(facet["id"]): facet for facet in [*reused_facets, *searched_facets]
    }
    facets = [facet_by_id[str(question["id"])] for question in questions]
    for facet in facets:
        # A smaller later output budget does not erase previously covered depth.
        facet["retrieval_budget"] = {
            name: max(value, facet.get("retrieval_budget", {}).get(name, 0))
            for name, value in retrieval_budget.items()
        }
        prior = next((value for value in (previous_receipt or {}).get("facets", [])
                      if value["id"] == facet["id"]), None)
        if prior is not None and (facet in searched_facets or facet["id"] in reopened_for_depth):
            if prior.get("finding"):
                # One replaceable review input, not a second evidence authority or
                # growing history. Old IDs retain their original fingerprint.
                facet["previous_finding"] = {
                    "question": prior.get("question"),
                    "finding": prior["finding"],
                    "source_current": not prior.get("stale", False),
                    "reusable": False,
                    "locators": prior.get("locators", []),
                    "schema_locators": prior.get("schema_locators", []),
                    "evidence_fingerprint": prior.get("evidence_fingerprint", (previous_receipt or {}).get("index_fingerprint")),
                }
            elif prior.get("previous_finding"):
                facet["previous_finding"] = prior["previous_finding"]
    locator_passage_ids = [
        int(passage_id)
        for facet in reused_facets
        if not isinstance(facet.get("finding"), dict)
        for passage_id in facet["passage_ids"]
    ]
    passage_ids = list(dict.fromkeys([*locator_passage_ids, *searched_passage_ids]))
    schema_facts: list[dict[str, object]] = []
    seen_schema_facts: set[str] = set()
    for facet in facets:
        for fact in facet.get("schema_facts", []):
            if not isinstance(fact, dict):
                continue
            evidence_id = fact.get("evidence_id")
            if isinstance(evidence_id, str) and evidence_id not in seen_schema_facts:
                seen_schema_facts.add(evidence_id)
                schema_facts.append(fact)
    schema_characters = sum(
        len(json.dumps(fact, ensure_ascii=False, separators=(",", ":")))
        for fact in schema_facts
    )
    passage_character_budget = max(1000, args.max_total_chars - schema_characters)
    passage_queries: dict[int, str] = {}
    for facet in facets:
        for passage_id in facet.get("passage_ids", []):
            if isinstance(passage_id, int) and not isinstance(passage_id, bool):
                passage_queries[passage_id] = " ".join(str(query["query"]) for query in facet.get("queries", []))
    retrieved = _get_payload(
        index_path,
        passage_ids,
        args.max_passage_chars,
        passage_character_budget,
        passage_queries,
    )
    if retrieved.get("not_found"):
        raise ValueError(
            "Task receipt references missing passages; rerun the affected facets through "
            "auto or a declared cold route"
        )

    retrieved_locators = _compact_locators(retrieved.get("locators"))
    for item in retrieved.get("results", []):
        aliases = [alias for facet in facets for alias in facet.get("aliases", {}).get(str(item["passage_id"]), [])]
        if aliases:
            item["also_in"] = list({json.dumps(alias, sort_keys=True): alias for alias in aliases}.values())
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
        _route_evidence(
            args,
            int(retrieved.get("characters", 0)) + schema_characters,
            sum(not isinstance(facet.get("finding"), dict) for facet in facets),
        )
        if args.execution_route == "auto"
        else {
            "recommendation": args.execution_route,
            "reason": execution["reason"],
            "estimated_evidence_tokens": (
                int(retrieved.get("characters", 0)) + 3
            ) // 4,
        }
    )
    if routing["recommendation"] == "low-overhead-worker" and not getattr(args, "pack_output", None) and args.execution_route == "auto":
        routing = {**routing, "recommendation": "coordinator-direct", "reason": "no-worker-output-requested"}
    if routing["recommendation"] == "receipt-only":
        last_execution: dict[str, object] = {
            "route": "coordinator-warm",
            "reason": "saved-finding-receipt",
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
    requested_ids = {str(question["id"]) for question in questions}
    generated_reasons = {"no-material-result", "support-not-found", "control-not-found", "candidates-require-verification", "finding-unresolved", "finding-conflicted", "finding-interpretation", "schema-evidence-incomplete"}
    receipt_gaps.extend(gap for gap in (previous_receipt or {}).get("gaps", [])
                        if gap.get("facet_id") in requested_ids and gap.get("reason") not in generated_reasons)
    retained_facets = [facet for facet in (previous_receipt or {}).get("facets", []) if facet["id"] not in requested_ids]
    retained_gaps = [gap for gap in (previous_receipt or {}).get("gaps", []) if gap.get("facet_id") not in requested_ids]
    optimization = {
        "index": "rebuilt" if index_result["database_rebuilt"] else "reused",
        "retrieval": retrieval,
        "query_batch": (
            "skipped"
            if not missing_questions
            else "partial" if reused_facets else "bounded"
        ),
        "query_fallback": "used" if fallback_search_count else "not-needed",
        "schema_query": "used" if schema_query_count else "not-needed",
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
        "adapter": "local-index/evidence-pack-v3",
        "index_fingerprint": fingerprint,
        "index_path": str(index_path),
        "corpus_path": str(corpus),
        "question_set_hash": questions_hash,
        "execution": {"cold": cold_execution, "last": last_execution},
        "optimization": optimization,
        "facets": [*retained_facets, *_receipt_facets(facets)],
        "conflicts": (previous_receipt or {}).get("conflicts", []),
        "gaps": [*retained_gaps, *receipt_gaps],
        "next_mode": (
            "direct"
            if finding_hits == len(facets) and not receipt_gaps
            else "retrieval"
        ),
    }
    task_receipt["next_mode"] = (
        "direct" if all(_verified_finding(facet) for facet in task_receipt["facets"])
        and not task_receipt["gaps"] and not task_receipt["conflicts"] else "retrieval"
    )
    if previous_receipt != task_receipt:
        _write_task_receipt(task_receipt_path, task_receipt)

    sources, passages = _compact_passages(retrieved.get("results"))
    question_by_id = {str(question["id"]): question for question in questions}
    visible_facets: list[dict[str, object]] = []
    for facet in facets:
        support = facet.get("support_passage_ids", [])
        checks = facet.get("check_passage_ids", [])
        has_support = bool(support) or _schema_role_covered(facet, "support")
        has_check = bool(checks) or _schema_role_covered(facet, "check")
        if has_support and has_check:
            coverage = "support-and-check"
        elif has_support:
            coverage = "support-only"
        elif has_check:
            coverage = "check-only"
        else:
            coverage = "no-material-result"
        visible_facets.append(
            {
                "id": facet["id"],
                "question": question_by_id[str(facet["id"])]["question"],
                "kind": facet.get("kind", "lookup"),
                "verification": (
                    "control" if facet.get("requires_check") else "exact"
                ),
                "coverage": coverage,
                "evidence_status": facet["finding"]["status"] if isinstance(facet.get("finding"), dict) else "unverified-candidates",
                "query_continuations": facet.get("query_continuations", []),
                **({"previous_finding": facet["previous_finding"]} if facet.get("previous_finding") else {}),
                "passage_ids": facet["passage_ids"],
                "support_passage_ids": support,
                "check_passage_ids": checks,
                "schema_fact_ids": [
                    fact["evidence_id"]
                    for fact in facet.get("schema_facts", [])
                    if isinstance(fact, dict)
                    and isinstance(fact.get("evidence_id"), str)
                ],
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
        "schema_query_count": schema_query_count,
        "schema_warnings": index_result.get("schema_warnings", {}),
        "fallback_search_count": fallback_search_count,
        "receipt_hits": receipt_hits,
        "finding_hits": finding_hits,
        "requested_findings_current": finding_hits == len(facets) and not receipt_gaps and not task_receipt["conflicts"],
        "searched_facets": [str(question["id"]) for question in missing_questions],
        "characters": int(retrieved.get("characters", 0)) + schema_characters,
        "passage_characters": retrieved.get("characters", 0),
        "schema_characters": schema_characters,
        "has_more": retrieved.get("has_more", False),
        "continuations": retrieved.get("continuations", []),
        "facets": visible_facets,
        "sources": sources,
        "passages": passages,
        "schema_facts": schema_facts,
        "findings": _finding_payload(facets),
        "gaps": task_receipt["gaps"],
        "conflicts": task_receipt["conflicts"],
        "next_mode": task_receipt["next_mode"],
        "routing": routing,
        "next_action": (
            {"kind": "answer-from-findings" if task_receipt["next_mode"] == "direct" else "review-saved-findings-and-gaps", "save_findings": False}
            if all(isinstance(facet.get("finding"), dict) for facet in facets)
            else {
                "kind": "delegate-pack",
                "save_findings": True,
                "findings_execution_route": "low-overhead-worker",
            }
            if routing["recommendation"] == "low-overhead-worker"
            else {
                "kind": "interpret-inline-and-answer",
                "save_findings": True,
                "findings_execution_route": "coordinator-direct",
            }
        ),
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
        and args.pack_output is not None
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
            "gaps": payload["gaps"],
            "conflicts": payload["conflicts"],
            "next_mode": payload["next_mode"],
            "task_receipt_path": str(task_receipt_path),
            "pack_path": str(pack_path),
            "passages_omitted": True,
            "next_action": payload["next_action"],
        }
    return payload


def command_evidence_pack(args: argparse.Namespace) -> int:
    emit_json(evidence_pack_payload(args), args.pretty)
    return 0


def _finding_status(claims: list[dict[str, object]]) -> str:
    statuses = {claim["status"] for claim in claims}
    return next((status for status in ("conflicted", "unresolved", "interpretation")
                 if status in statuses), "confirmed" if claims else "unresolved")


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
        unknown = set(item) - {"facet_id", "claims", "reason"}
        if unknown:
            raise ValueError(
                f"{location} has unsupported fields: {', '.join(sorted(unknown))}"
            )
        facet_id = required_record_id(item.get("facet_id"), f"{location}.facet_id")
        if facet_id in seen:
            raise ValueError(f"Duplicate finding facet: {facet_id}")
        seen.add(facet_id)
        raw_claims = item.get("claims")
        if not isinstance(raw_claims, list):
            raise ValueError(f"{location}.claims must be an array")
        if not raw_claims and not item.get("reason"):
            raise ValueError(f"{location} needs a reason for an empty unresolved finding")
        if len(raw_claims) > MAX_FINDING_CLAIMS:
            raise ValueError(
                f"{location}.claims allows at most {MAX_FINDING_CLAIMS} entries"
            )
        claims: list[dict[str, object]] = []
        for claim_index, raw_claim in enumerate(raw_claims):
            claim_location = f"{location}.claims[{claim_index}]"
            if not isinstance(raw_claim, dict):
                raise ValueError(f"{claim_location} must be an object")
            claim_unknown = set(raw_claim) - {
                "text",
                "passage_ids",
                "evidence_ids",
                "scope",
                "status",
                "basis",
                "limits",
            }
            if claim_unknown:
                raise ValueError(
                    f"{claim_location} has unsupported fields: "
                    f"{', '.join(sorted(claim_unknown))}"
                )
            text = required_research_text(
                raw_claim.get("text"), f"{claim_location}.text", MAX_FINDING_TEXT
            )
            status = raw_claim.get("status")
            if not isinstance(status, str) or status not in FINDING_STATUSES:
                raise ValueError(f"{claim_location}.status must be confirmed, interpretation, unresolved, or conflicted")
            basis = required_research_text(raw_claim.get("basis"), f"{claim_location}.basis", MAX_FINDING_TEXT)
            scope = required_research_text(raw_claim.get("scope"), f"{claim_location}.scope", MAX_FINDING_SCOPE)
            limits = raw_claim.get("limits", "")
            if status != "confirmed" or limits:
                limits = required_research_text(limits, f"{claim_location}.limits", MAX_FINDING_TEXT)
            elif not isinstance(limits, str):
                raise ValueError(f"{claim_location}.limits must be text")
            passage_ids = raw_claim.get("passage_ids", [])
            if not isinstance(passage_ids, list) or any(
                not isinstance(value, int) or isinstance(value, bool) or value < 1
                for value in passage_ids
            ):
                raise ValueError(f"{claim_location}.passage_ids is invalid")
            evidence_ids = raw_claim.get("evidence_ids", [])
            if not isinstance(evidence_ids, list) or any(
                not isinstance(value, str) or not value or len(value) > 1_000
                for value in evidence_ids
            ):
                raise ValueError(f"{claim_location}.evidence_ids is invalid")
            claim: dict[str, object] = {
                "text": text,
                "status": status,
                "basis": basis,
                "scope": scope,
                "limits": limits,
                "passage_ids": list(dict.fromkeys(passage_ids)),
                "evidence_ids": list(dict.fromkeys(evidence_ids)),
            }
            claims.append(claim)
        total_claims += len(claims)
        normalized.append(
            {"facet_id": facet_id, "status": _finding_status(claims), "claims": claims,
             **({"reason": required_research_text(item["reason"], f"{location}.reason", MAX_FINDING_TEXT)} if item.get("reason") is not None else {})}
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
    if not isinstance(receipt.get("index_path"), str) or not isinstance(receipt.get("corpus_path"), str):
        raise ValueError("Task receipt lacks its index/corpus binding; create a fresh receipt")
    bound_index, current = resolve_index_binding(Path(receipt["index_path"]), Path(receipt["corpus_path"]))
    validate_output_paths(Path(receipt["corpus_path"]), [receipt_path], [bound_index, args.input])
    if current != stored_fingerprint:
        raise ValueError("Task receipt is stale; refresh the affected evidence before saving findings")
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
        if facet.get("stale"):
            raise ValueError(f"Facet {facet_id} has stale evidence; retrieve it again before saving")
        allowed_ids = set(facet.get("passage_ids", []))
        allowed_evidence_ids = {
            locator.get("evidence_id")
            for locator in facet.get("schema_locators", [])
            if isinstance(locator, dict)
            and isinstance(locator.get("evidence_id"), str)
        }
        status = finding["status"]
        for claim in finding["claims"]:
            if not isinstance(claim, dict):
                continue
            claim_ids = set(claim.get("passage_ids", []))
            claim_evidence_ids = set(claim.get("evidence_ids", []))
            if claim["status"] == "confirmed" and not (claim_ids or claim_evidence_ids):
                raise ValueError(
                    f"Confirmed finding {facet_id} claims require evidence locators"
                )
            if not claim_ids.issubset(allowed_ids):
                raise ValueError(
                    f"Finding {facet_id} references passages outside its facet"
                )
            if not claim_evidence_ids.issubset(allowed_evidence_ids):
                raise ValueError(
                    f"Finding {facet_id} references schema evidence outside its facet"
                )
        facet["finding"] = {
            "status": status,
            "claims": finding["claims"],
            **({"reason": finding["reason"]} if finding.get("reason") is not None else {}),
        }
        facet.pop("previous_finding", None)

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
    updated_ids = {finding["facet_id"] for finding in findings}
    gaps = [gap for gap in receipt.get("gaps", []) if gap.get("facet_id") not in updated_ids]
    gaps.extend(_receipt_gaps([facets[key] for key in updated_ids]))
    receipt["gaps"] = gaps
    every_verified = all(
        isinstance(facet.get("finding"), dict)
        and _verified_finding(facet) is not None
        for facet in facets.values()
    )
    receipt["next_mode"] = (
        "direct" if every_verified and isinstance(gaps, list) and not gaps and not receipt.get("conflicts") else "retrieval"
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
