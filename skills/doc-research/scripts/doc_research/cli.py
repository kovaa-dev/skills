from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

from .common import CATALOG_ADAPTERS, CONFIDENCE_VALUES, DEFAULT_MAX_ARCHIVE_BYTES, DEFAULT_MAX_ARCHIVE_ENTRIES, DEFAULT_MAX_ARCHIVE_MEMBER_BYTES, DEFAULT_MAX_ARCHIVE_RATIO, DEFAULT_MAX_COMPARE_UNITS, DEFAULT_MAX_CORPUS_BYTES, DEFAULT_MAX_SOURCE_BYTES, EVIDENCE_EXECUTION_ROUTES, EVIDENCE_FALLBACK_REASONS, EVIDENCE_WORKER_CONTEXTS, PROJECT_ANCHOR_KINDS, RESEARCH_STATUSES
from .common import HANDLED_ERRORS

def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)

    read_text = subparsers.add_parser(
        "read-text", help="Read/search numbered text without an index; optionally read memory first"
    )
    read_text.add_argument("source", type=Path)
    read_text.add_argument("--lines", nargs="+", default=[], help="Inclusive START:END ranges or line numbers")
    read_text.add_argument("--find", action="append", default=[], help="Case-insensitive literal; repeat for OR; --lines limits search scope")
    read_text.add_argument("--context", type=int, help="Extra lines around matches (default 3; prose mode 0)")
    read_text.add_argument("--prose", action="store_true", help="Query-diversified Markdown paragraphs/tables without fenced code; code remains accessible without this flag")
    read_text.add_argument("--max-chars", type=int, default=24000, help="Entire serialized response, including metadata and newline")
    read_text.add_argument("--after-line", type=int, default=0, help="Continue after this received source line in the same selection order")
    read_text.add_argument("--source-hash", help="Reject continuation when source bytes changed")
    memory = read_text.add_mutually_exclusive_group()
    memory.add_argument("--memory-dir", type=Path, help="Inspect existing ordinary notes; unknown provenance needs assessment")
    memory.add_argument("--memory", type=Path, help="Answer note written by save-answer; checks current source bytes")
    read_text.add_argument("--scope", help="Select an exact key when known; otherwise return candidates for assessment")
    read_text.add_argument("--memory-offset", type=int, default=0)
    read_text.add_argument("--memory-hash", help="Required on subsequent answer pages")
    read_text.set_defaults(handler=("text_reader", "command_read_text"))

    save_answer = subparsers.add_parser("save-answer", help="Upsert answer points with explicit assessments; checks evidence mechanics, not meaning")
    save_answer.add_argument("source", type=Path)
    save_answer.add_argument("--memory", type=Path, required=True)
    save_answer.add_argument("--scope", required=True)
    save_answer.add_argument("--source-hash", required=True, help="Hash of the snapshot actually researched")
    body = save_answer.add_mutually_exclusive_group(required=True)
    body.add_argument("--points", help="JSON object keyed by stable point IDs, or - for UTF-8 stdin; see evidence-schema.md")
    body.add_argument("--points-file", type=Path, help="Existing prepared JSON; do not create an intermediate file just for this command")
    save_answer.add_argument("--reviewed", nargs="+", default=[], metavar="ID", help="Updated points actually reviewed in this invocation; required for new/changed confirmations")
    save_answer.set_defaults(handler=("text_memory", "command_save_answer"))

    doctor = subparsers.add_parser(
        "doctor", help="Check Python, SQLite FTS5, and directory write access"
    )
    doctor.add_argument(
        "--write-dir",
        type=Path,
        default=Path.cwd(),
        help="Existing directory to test for write access (default: current directory)",
    )
    doctor.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    doctor.set_defaults(handler=("ingestion", "command_doctor"))

    index = subparsers.add_parser("index", help="Create or incrementally update an index")
    index.add_argument(
        "corpus",
        type=Path,
        help="A .md, .txt, .jsonl, or .xsd file, or a directory containing them",
    )
    index.add_argument("--db", type=Path, required=True, help="SQLite index path")
    index.add_argument(
        "--max-chars", type=int, default=3500, help="Maximum characters per stored chunk"
    )
    index.add_argument(
        "--max-source-bytes",
        type=int,
        default=DEFAULT_MAX_SOURCE_BYTES,
        help=f"Maximum bytes per source (default: {DEFAULT_MAX_SOURCE_BYTES})",
    )
    index.add_argument(
        "--max-corpus-bytes",
        type=int,
        default=DEFAULT_MAX_CORPUS_BYTES,
        help=f"Maximum total source bytes (default: {DEFAULT_MAX_CORPUS_BYTES})",
    )
    index.set_defaults(handler=("index", "command_index"))

    info = subparsers.add_parser("info", help="Inspect an existing index without searching it")
    info.add_argument("db", type=Path, help="SQLite index path")
    info.add_argument("--source-limit", type=int, default=10, help="Maximum sources returned")
    info.add_argument("--offset", type=int, default=0, help="Continue at this source offset")
    info.add_argument("--hashes", action="store_true", help="Include normalized-input hashes")
    info.add_argument(
        "--metadata-summary",
        action="store_true",
        help="Include bounded version, date, section, and coverage distributions",
    )
    info.add_argument(
        "--metadata-limit", type=int, default=10, help="Maximum values per metadata field"
    )
    info.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    info.set_defaults(handler=("index", "command_info"))

    normalize_xml_schema = subparsers.add_parser(
        "normalize-xml-schema",
        help="Inspect the built-in semantic normalization of XSD or embedded XSD",
    )
    normalize_xml_schema.add_argument(
        "source", type=Path, help="A .xsd file or Markdown file with fenced XSD blocks"
    )
    normalize_xml_schema.add_argument(
        "--include-records",
        action="store_true",
        help="Include a bounded page of normalized semantic records",
    )
    normalize_xml_schema.add_argument("--limit", type=int, default=20)
    normalize_xml_schema.add_argument("--offset", type=int, default=0)
    normalize_xml_schema.add_argument("--start-char", type=int, default=0, help="Continue a serialized record fragment")
    normalize_xml_schema.add_argument("--source-hash", help="Reject continuation after source bytes change")
    normalize_xml_schema.add_argument("--max-total-chars", type=int, default=12000)
    normalize_xml_schema.add_argument("--pretty", action="store_true")
    normalize_xml_schema.set_defaults(
        handler=("index", "command_normalize_xml_schema")
    )

    schema_query = subparsers.add_parser(
        "schema-query",
        help="Search persisted schema records with bounded output and continuation",
    )
    schema_query.add_argument("db", type=Path, help="SQLite index path")
    schema_query.add_argument("query", help="Name, path, documentation, or fact substring")
    schema_query.add_argument("--kind", help="Restrict to an exact normalized node kind")
    schema_query.add_argument("--source", help="Restrict to a source path substring")
    schema_query.add_argument("--schema", help="Restrict to a schema name substring")
    schema_query.add_argument("--limit", type=int, default=10)
    schema_query.add_argument("--offset", type=int, default=0)
    schema_query.add_argument("--start-char", type=int, default=0, help="Continue a serialized record fragment")
    schema_query.add_argument("--expected-fingerprint", help="Index generation returned by the previous page")
    schema_query.add_argument("--max-total-chars", type=int, default=12000)
    schema_query.add_argument(
        "--purpose",
        choices=("scoped-search", "adapter-debugging", "custom-adapter"),
        default="scoped-search",
    )
    schema_query.add_argument("--purpose-reason")
    schema_query.add_argument("--pretty", action="store_true")
    schema_query.set_defaults(handler=("index", "command_schema_query"))

    catalog_init = subparsers.add_parser(
        "catalog-init", help="Create a logical catalog of isolated corpora"
    )
    catalog_init.add_argument("db", type=Path, help="Catalog SQLite database path")
    catalog_init.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    catalog_init.set_defaults(handler=("catalog", "command_catalog_init"))

    catalog_put = subparsers.add_parser(
        "catalog-put", help="Register or update one corpus in a logical catalog"
    )
    catalog_put.add_argument("db", type=Path, help="Catalog SQLite database path")
    catalog_put.add_argument(
        "corpus_id",
        nargs="?",
        help="Stable corpus identifier; derived from the source identity when omitted",
    )
    catalog_put.add_argument("--adapter", choices=sorted(CATALOG_ADAPTERS), required=True)
    catalog_put.add_argument(
        "--access-boundary",
        required=True,
        help="Stable tenant or permission boundary identifier",
    )
    catalog_put.add_argument("--label", help="Human-readable corpus label")
    catalog_put.add_argument(
        "--locator", help="Corpus root for local-index or stable external source locator"
    )
    catalog_put.add_argument("--generation", help="Verified external source generation")
    catalog_put.add_argument("--index", type=Path, help="Local corpus index")
    catalog_put.add_argument("--receipts-db", type=Path, help="Local receipt store")
    catalog_put.add_argument(
        "--project-id",
        action="append",
        default=[],
        help="Repeat to attach the corpus to existing logical projects",
    )
    catalog_put.add_argument("--disabled", action="store_true", help="Disable this corpus")
    catalog_put.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    catalog_put.set_defaults(handler=("catalog", "command_catalog_put"))

    catalog_project_put = subparsers.add_parser(
        "catalog-project-put",
        help="Create or update one logical project view over registered corpora",
    )
    catalog_project_put.add_argument("db", type=Path, help="Catalog SQLite database path")
    catalog_project_put.add_argument(
        "project_id",
        nargs="?",
        help="Stable logical project identifier; derived from the anchor when omitted",
    )
    catalog_project_put.add_argument("--label", help="Human-readable project label")
    catalog_project_put.add_argument(
        "--access-boundary", required=True, help="Permission boundary identifier"
    )
    catalog_project_put.add_argument(
        "--anchor-kind", choices=sorted(PROJECT_ANCHOR_KINDS), required=True
    )
    catalog_project_put.add_argument(
        "--anchor", required=True, help="Stable filesystem or source-system anchor"
    )
    catalog_project_put.add_argument(
        "--corpus-id", action="append", default=[], help="Repeat to attach corpora"
    )
    catalog_project_put.add_argument(
        "--replace-corpora",
        action="store_true",
        help="Make the provided corpus IDs the complete current membership",
    )
    catalog_project_put.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output"
    )
    catalog_project_put.set_defaults(handler=("catalog", "command_catalog_project_put"))

    catalog_project_resolve = subparsers.add_parser(
        "catalog-project-resolve",
        help="Resolve a stable context anchor to the most specific project",
    )
    catalog_project_resolve.add_argument(
        "db", type=Path, help="Catalog SQLite database path"
    )
    catalog_project_resolve.add_argument(
        "--anchor-kind", choices=sorted(PROJECT_ANCHOR_KINDS), required=True
    )
    catalog_project_resolve.add_argument("--anchor", required=True)
    catalog_project_resolve.add_argument("--access-boundary")
    catalog_project_resolve.add_argument(
        "--create",
        action="store_true",
        help="Create or attach to an anchored project when durable setup is authorized",
    )
    catalog_project_resolve.add_argument("--label")
    catalog_project_resolve.add_argument(
        "--corpus-id", action="append", default=[], help="Corpus to attach with --create"
    )
    catalog_project_resolve.add_argument(
        "--pretty", action="store_true", help="Pretty-print JSON output"
    )
    catalog_project_resolve.set_defaults(handler=("catalog", "command_catalog_project_resolve"))

    catalog_info = subparsers.add_parser(
        "catalog-info", help="Inspect bounded corpus registrations and health"
    )
    catalog_info.add_argument("db", type=Path, help="Catalog SQLite database path")
    catalog_info.add_argument(
        "--live", action="store_true", help="Validate local indexes and receipt stores"
    )
    catalog_info.add_argument("--limit", type=int, default=10)
    catalog_info.add_argument("--offset", type=int, default=0)
    catalog_info.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    catalog_info.set_defaults(handler=("catalog", "command_catalog_info"))

    catalog_sync = subparsers.add_parser(
        "catalog-sync", help="Record current generations for registered local corpora"
    )
    catalog_sync.add_argument("db", type=Path, help="Catalog SQLite database path")
    catalog_sync.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    catalog_sync.set_defaults(handler=("catalog", "command_catalog_sync"))

    catalog_search = subparsers.add_parser(
        "catalog-search", help="Search selected local corpora through one bounded query"
    )
    catalog_search.add_argument("db", type=Path, help="Catalog SQLite database path")
    catalog_search.add_argument("query", help="Search text or FTS5 expression")
    catalog_search.add_argument(
        "--corpus-id", action="append", default=[], help="Repeat to restrict the search scope"
    )
    catalog_search.add_argument(
        "--project-id",
        action="append",
        default=[],
        help="Repeat to search the deduplicated union of logical project members",
    )
    catalog_search.add_argument(
        "--access-boundary",
        action="append",
        default=[],
        help="Repeat to search only explicitly selected permission boundaries",
    )
    catalog_search.add_argument(
        "--mode", choices=("literal", "prefix", "fts"), default="literal"
    )
    catalog_search.add_argument("--source")
    catalog_search.add_argument("--page")
    catalog_search.add_argument("--section")
    catalog_search.add_argument("--version")
    catalog_search.add_argument("--date")
    catalog_search.add_argument("--limit", type=int, default=8)
    catalog_search.add_argument("--offset", type=int, default=0)
    catalog_search.add_argument("--continuation", help="Opaque cursor returned by the previous page")
    catalog_search.add_argument("--max-chars", type=int, default=1600)
    catalog_search.add_argument("--max-total-chars", type=int, default=20000)
    catalog_search.add_argument("--snippet-tokens", type=int, default=48)
    catalog_dedupe = catalog_search.add_mutually_exclusive_group()
    catalog_dedupe.add_argument(
        "--dedupe-exact",
        dest="dedupe_exact",
        action="store_true",
        help="Collapse exact duplicate passages and retain alternate locators (default)",
    )
    catalog_dedupe.add_argument(
        "--keep-duplicates",
        dest="dedupe_exact",
        action="store_false",
        help="Return exact duplicate passages separately",
    )
    catalog_search.add_argument("--max-per-source", type=int, default=0)
    catalog_search.add_argument("--receipt-id")
    catalog_search.add_argument("--refresh", action="store_true")
    catalog_search.add_argument(
        "--read-only",
        action="store_true",
        help="Reuse receipts when present but never write catalog, receipt, or research state",
    )
    catalog_search.add_argument(
        "--allow-partial",
        action="store_true",
        help="Search available local corpora and report every unsearched corpus",
    )
    catalog_search.add_argument("--research-db", type=Path)
    catalog_search.add_argument("--facet-id")
    catalog_search.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    catalog_search.set_defaults(handler=("catalog", "command_catalog_search"), dedupe_exact=True)

    catalog_get = subparsers.add_parser(
        "catalog-get", help="Retrieve local passages by CORPUS_ID=PASSAGE_ID"
    )
    catalog_get.add_argument("db", type=Path, help="Catalog SQLite database path")
    catalog_get.add_argument("locators", nargs="+")
    catalog_get.add_argument("--offset", type=int, default=0)
    catalog_get.add_argument("--start-char", type=int, default=0)
    catalog_get.add_argument("--expected-fingerprint", help="Expected generation for a single-corpus raw locator")
    catalog_get.add_argument("--max-chars", type=int, default=6000)
    catalog_get.add_argument("--max-total-chars", type=int, default=20000)
    catalog_get.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    catalog_get.set_defaults(handler=("catalog", "command_catalog_get"))

    receipts_init = subparsers.add_parser(
        "receipts-init", help="Create an independent cross-session search-receipt store"
    )
    receipts_init.add_argument("db", type=Path, help="Receipt SQLite database path")
    receipts_init.add_argument(
        "--corpus",
        type=Path,
        required=True,
        help="Authorized corpus file or directory",
    )
    receipts_init.add_argument("--index", type=Path, required=True, help="Bound corpus index")
    receipts_init.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    receipts_init.set_defaults(handler=("receipts", "command_receipts_init"))

    receipts_info = subparsers.add_parser(
        "receipts-info", help="Show compact receipt-store health and freshness"
    )
    receipts_info.add_argument("db", type=Path, help="Receipt SQLite database path")
    receipts_info.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    receipts_info.set_defaults(handler=("receipts", "command_receipts_info"))

    receipts_list = subparsers.add_parser(
        "receipts-list", help="Read bounded current search receipts"
    )
    receipts_list.add_argument("db", type=Path, help="Receipt SQLite database path")
    receipts_list.add_argument("--receipt-id", help="Return one receipt by stable ID")
    receipts_list.add_argument(
        "--include-stale", action="store_true", help="Include non-current index generations"
    )
    receipts_list.add_argument(
        "--details", action="store_true", help="Include stable result references"
    )
    receipts_list.add_argument("--limit", type=int, default=10)
    receipts_list.add_argument("--offset", type=int, default=0)
    receipts_list.add_argument("--max-total-chars", type=int, default=12000)
    receipts_list.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    receipts_list.set_defaults(handler=("receipts", "command_receipts_list"))

    receipts_sync = subparsers.add_parser(
        "receipts-sync", help="Bind receipts to the current index generation"
    )
    receipts_sync.add_argument("db", type=Path, help="Receipt SQLite database path")
    receipts_sync.add_argument("--index", type=Path, help="Replacement corpus index path")
    receipts_sync.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    receipts_sync.set_defaults(handler=("receipts", "command_receipts_sync"))

    research_init = subparsers.add_parser(
        "research-init", help="Create a separate durable research-state database"
    )
    research_init.add_argument("db", type=Path, help="Research SQLite database path")
    research_init.add_argument("--scope", required=True, help="Investigation scope")
    research_binding = research_init.add_mutually_exclusive_group(required=True)
    research_binding.add_argument(
        "--corpus", type=Path, help="Authorized corpus file or directory"
    )
    research_binding.add_argument("--catalog", type=Path, help="Bound corpus catalog")
    research_init.add_argument(
        "--corpus-id", action="append", default=[], help="Repeat to scope catalog research"
    )
    research_init.add_argument(
        "--project-id",
        action="append",
        default=[],
        help="Repeat to scope catalog research through logical projects",
    )
    research_init.add_argument(
        "--access-boundary",
        action="append",
        default=[],
        help="Repeat to scope catalog research by permission boundary",
    )
    research_init.add_argument("--index", type=Path, help="Optional corpus index to bind")
    research_init.add_argument("--next-action", help="Next useful investigation action")
    research_init.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    research_init.set_defaults(handler=("research", "command_research_init"))

    research_info = subparsers.add_parser(
        "research-info", help="Show bounded resumable research state"
    )
    research_info.add_argument("db", type=Path, help="Research SQLite database path")
    research_info.add_argument(
        "--facet-limit", type=int, default=10, help="Maximum facets returned"
    )
    research_info.add_argument("--offset", type=int, default=0, help="Continue at facet offset")
    research_info.add_argument(
        "--resume",
        action="store_true",
        help="Return one compact bundle of active work for the next session",
    )
    research_info.add_argument("--resume-limit", type=int, default=8)
    research_info.add_argument("--max-total-chars", type=int, default=12000)
    research_info.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    research_info.set_defaults(handler=("research", "command_research_info"))

    research_update = subparsers.add_parser(
        "research-update", help="Update investigation-level status or next action"
    )
    research_update.add_argument("db", type=Path, help="Research SQLite database path")
    research_update.add_argument("--scope", help="Updated investigation scope")
    research_update.add_argument("--status", choices=sorted(RESEARCH_STATUSES))
    research_update.add_argument(
        "--next-action", help="Next action; pass an empty value to clear it"
    )
    research_update.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    research_update.set_defaults(handler=("research", "command_research_update"))

    research_put = subparsers.add_parser(
        "research-put", help="Create or update one compact research-state record"
    )
    research_put.add_argument("db", type=Path, help="Research SQLite database path")
    research_put.add_argument(
        "kind", choices=("facet", "evidence", "gap", "conflict")
    )
    research_put.add_argument("record_id", help="Stable record identifier")
    research_put.add_argument("--facet", help="Owning facet ID")
    research_put.add_argument("--corpus-id", help="Owning catalog corpus ID")
    research_put.add_argument("--question")
    research_put.add_argument("--status")
    research_put.add_argument("--next-action")
    research_put.add_argument("--finding")
    research_put.add_argument("--source")
    research_put.add_argument("--source-version")
    research_put.add_argument("--source-hash")
    research_put.add_argument("--page")
    research_put.add_argument("--section")
    research_put.add_argument("--passage-id", type=int)
    research_put.add_argument("--excerpt")
    research_put.add_argument("--interpretation")
    research_put.add_argument("--confidence", choices=sorted(CONFIDENCE_VALUES))
    research_put.add_argument("--verified", choices=("true", "false"))
    research_put.add_argument("--description")
    research_put.add_argument("--reason")
    research_put.add_argument("--next-query")
    research_put.add_argument("--evidence-ids-json")
    research_put.add_argument("--resolution")
    research_put.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    research_put.set_defaults(handler=("research", "command_research_put"))

    research_apply = subparsers.add_parser(
        "research-apply", help="Atomically apply a bounded JSON research-state delta"
    )
    research_apply.add_argument("db", type=Path, help="Research SQLite database path")
    research_apply.add_argument("input", type=Path, help="JSON object with state and records")
    research_apply.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    research_apply.set_defaults(handler=("research", "command_research_apply"))

    research_list = subparsers.add_parser(
        "research-list", help="Read bounded records from a research database"
    )
    research_list.add_argument("db", type=Path, help="Research SQLite database path")
    research_list.add_argument(
        "kind", choices=("facets", "evidence", "gaps", "conflicts")
    )
    research_list.add_argument("--id", dest="record_id", help="Return one record by stable ID")
    research_list.add_argument("--facet", help="Restrict records to one facet")
    research_list.add_argument(
        "--status", help="Restrict by status or evidence confidence"
    )
    research_list.add_argument("--limit", type=int, default=10)
    research_list.add_argument("--offset", type=int, default=0)
    research_view = research_list.add_mutually_exclusive_group()
    research_view.add_argument(
        "--summary",
        dest="summary",
        action="store_true",
        help="Omit large detail fields; this is the default for evidence",
    )
    research_view.add_argument(
        "--details",
        dest="summary",
        action="store_false",
        help="Include excerpt, interpretation, and other detail fields",
    )
    research_list.add_argument("--max-chars", type=int, default=1600)
    research_list.add_argument("--max-total-chars", type=int, default=20000)
    research_list.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    research_list.set_defaults(handler=("research", "command_research_list"), summary=None)

    research_sync = subparsers.add_parser(
        "research-sync", help="Rebind state to the current index generation"
    )
    research_sync.add_argument("db", type=Path, help="Research SQLite database path")
    research_sync.add_argument("--index", type=Path, help="Replacement corpus index path")
    research_sync.add_argument("--catalog", type=Path, help="Replacement corpus catalog path")
    research_sync.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    research_sync.set_defaults(handler=("research", "command_research_sync"))

    import_docling = subparsers.add_parser(
        "import-docling", help="Normalize Docling chunks JSONL for indexing"
    )
    import_docling.add_argument("input", type=Path, help="Docling .chunks.jsonl file")
    import_docling.add_argument("--output", type=Path, required=True, help="Normalized JSONL path")
    import_docling.add_argument("--source", help="Canonical source path or identifier")
    import_docling.add_argument("--source-sha256", help="SHA-256 of the authorized original source")
    import_docling.add_argument("--version", help="Authoritative source version")
    import_docling.add_argument("--date", help="Source-native document date")
    import_docling.add_argument(
        "--force", action="store_true", help="Replace an existing output file"
    )
    import_docling.add_argument("--pretty", action="store_true", help="Pretty-print JSON summary")
    import_docling.set_defaults(handler=("ingestion", "command_import_docling"))

    extract_zip = subparsers.add_parser(
        "extract-zip", help="Safely extract one ZIP archive into a new directory"
    )
    extract_zip.add_argument("archive", type=Path, help="Source ZIP archive")
    extract_zip.add_argument("--output", type=Path, required=True, help="New output directory")
    extract_zip.add_argument("--max-entries", type=int, default=DEFAULT_MAX_ARCHIVE_ENTRIES)
    extract_zip.add_argument(
        "--max-total-bytes", type=int, default=DEFAULT_MAX_ARCHIVE_BYTES
    )
    extract_zip.add_argument(
        "--max-member-bytes", type=int, default=DEFAULT_MAX_ARCHIVE_MEMBER_BYTES
    )
    extract_zip.add_argument("--max-ratio", type=int, default=DEFAULT_MAX_ARCHIVE_RATIO)
    extract_zip.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    extract_zip.set_defaults(handler=("ingestion", "command_extract_zip"))

    search = subparsers.add_parser("search", help="Search an existing index")
    search.add_argument("db", type=Path, help="SQLite index path")
    search.add_argument("query", help="Search text or FTS5 expression")
    search.add_argument(
        "--purpose",
        choices=("scoped-search", "named-gap", "adapter-debugging", "custom-adapter"),
        default="scoped-search",
        help="Optional retrieval purpose; a task receipt is not required for normal search",
    )
    search.add_argument("--task-receipt", type=Path)
    search.add_argument("--gap-facet")
    search.add_argument("--purpose-reason")
    search.add_argument(
        "--mode",
        choices=("auto", "literal", "prefix", "fts"),
        default="auto",
        help="auto selects FTS syntax, prefix matching, or literal terms",
    )
    search.add_argument("--source", help="Restrict to source names or paths containing this string")
    search.add_argument("--page", help="Restrict to a page value or page-list member")
    search.add_argument("--section", help="Restrict to sections containing this string")
    search.add_argument("--version", help="Restrict to an exact version value")
    search.add_argument("--date", help="Restrict to an exact document date value")
    search.add_argument("--limit", type=int, default=4)
    search.add_argument("--offset", type=int, default=0, help="Continue at this result offset")
    search.add_argument("--expected-fingerprint", help="Reject continuation after index generation changes")
    search.add_argument(
        "--max-chars", type=int, default=1600, help="Maximum characters returned per result"
    )
    search.add_argument("--max-total-chars", type=int, default=20000)
    search.add_argument(
        "--snippet-tokens", type=int, default=48, help="FTS5 snippet size in tokens"
    )
    search.add_argument(
        "--dedupe-exact",
        action="store_true",
        help="Collapse byte-equivalent normalized result text and retain alternate locators",
    )
    search.add_argument(
        "--max-per-source",
        type=int,
        default=0,
        help="Maximum selected results per source; zero disables diversity filtering",
    )
    search.add_argument(
        "--receipts-db",
        type=Path,
        help="Reuse or save a compact receipt without requiring research state",
    )
    search.add_argument(
        "--research-db",
        type=Path,
        help="Optional research state to link to a receipt; requires --receipts-db",
    )
    search.add_argument(
        "--facet-id", help="Facet that owns the saved receipt; requires --research-db"
    )
    search.add_argument(
        "--receipt-id",
        help="Stable receipt ID; generated deterministically when omitted",
    )
    search.add_argument(
        "--refresh",
        action="store_true",
        help="Ignore a current receipt and execute the search again",
    )
    search.add_argument(
        "--read-only-receipts",
        action="store_true",
        help="Reuse an existing receipt on a hit but do not save one on a miss",
    )
    search.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    search.set_defaults(handler=("search", "command_search"))

    search_many = subparsers.add_parser(
        "search-many",
        help="Run up to 24 bounded searches and deduplicate repeated snippets",
    )
    search_many.add_argument("db", type=Path, help="SQLite index path")
    search_many.add_argument("input", type=Path, help="JSON array or object with queries")
    search_many.add_argument(
        "--purpose",
        choices=("scoped-search", "named-gap", "adapter-debugging", "custom-adapter"),
        default="scoped-search",
    )
    search_many.add_argument("--task-receipt", type=Path)
    search_many.add_argument("--gap-facet")
    search_many.add_argument("--purpose-reason")
    search_many.add_argument("--receipts-db", type=Path, help="Independent receipt store")
    search_many.add_argument(
        "--read-only-receipts",
        action="store_true",
        help="Reuse existing receipts but do not save misses",
    )
    search_many.add_argument(
        "--research-db", type=Path, help="Optional research state for facet links"
    )
    search_many.add_argument("--query-offset", type=int, default=0)
    search_many.add_argument("--limit-per-query", type=int, default=2)
    search_many.add_argument("--max-chars", type=int, default=800)
    search_many.add_argument("--max-per-query-chars", type=int, default=4000)
    search_many.add_argument("--max-total-chars", type=int, default=12000)
    search_many.add_argument("--snippet-tokens", type=int, default=32)
    search_many.add_argument("--dedupe-exact", action="store_true")
    search_many.add_argument("--max-per-source", type=int, default=0)
    search_many.add_argument("--pretty", action="store_true")
    search_many.set_defaults(handler=("search", "command_search_many"))

    evidence_pack = subparsers.add_parser(
        "evidence-pack",
        help="Index, search, verify, and reopen evidence in one bounded command",
    )
    evidence_pack.add_argument(
        "corpus",
        type=Path,
        help="A .md, .txt, .jsonl, or .xsd file, or a directory containing them",
    )
    evidence_pack.add_argument(
        "input", type=Path, help="JSON array or object with evidence questions"
    )
    evidence_pack.add_argument("--db", type=Path, required=True, help="SQLite index path")
    evidence_pack.add_argument(
        "--receipts-db",
        type=Path,
        help="Receipt store path (default: INDEX_STEM.receipts.sqlite)",
    )
    evidence_pack.add_argument(
        "--task-receipt",
        type=Path,
        required=True,
        help="Required compact task receipt for replay and optimization audit",
    )
    evidence_pack.add_argument(
        "--execution-route",
        choices=EVIDENCE_EXECUTION_ROUTES,
        default="coordinator-direct",
        help="Executor route; defaults to inline interpretation",
    )
    evidence_pack.add_argument(
        "--executor",
        help="Actual worker/model/agent label for --execution-route low-overhead-worker",
    )
    evidence_pack.add_argument(
        "--worker-context",
        choices=EVIDENCE_WORKER_CONTEXTS,
        help="Required compact context contract for a low-overhead worker",
    )
    evidence_pack.add_argument(
        "--fallback-reason",
        choices=EVIDENCE_FALLBACK_REASONS,
        help="Why a cold request could not use a low-overhead worker",
    )
    evidence_pack.add_argument(
        "--pack-output",
        type=Path,
        help="Write a worker-selected evidence pack here when delegation is selected",
    )
    evidence_pack.add_argument(
        "--routing-profile",
        type=Path,
        help="Optional measured cost profile for deterministic auto routing",
    )
    evidence_pack.add_argument(
        "--parent-context-tokens",
        type=int,
        help="Measured parent-context tokens used by deterministic route costing",
    )
    evidence_pack.add_argument(
        "--expected-direct-turns",
        type=float,
        help="Expected remaining parent model turns without isolation",
    )
    evidence_pack.add_argument(
        "--expected-delegated-parent-turns",
        type=float,
        help="Expected remaining parent turns when a no-history worker is used",
    )
    evidence_pack.add_argument("--chunk-chars", type=int, default=3500)
    evidence_pack.add_argument(
        "--max-source-bytes",
        type=int,
        default=DEFAULT_MAX_SOURCE_BYTES,
        help=f"Maximum bytes per source (default: {DEFAULT_MAX_SOURCE_BYTES})",
    )
    evidence_pack.add_argument(
        "--max-corpus-bytes",
        type=int,
        default=DEFAULT_MAX_CORPUS_BYTES,
        help=f"Maximum total source bytes (default: {DEFAULT_MAX_CORPUS_BYTES})",
    )
    evidence_pack.add_argument("--limit-per-query", type=int, default=2)
    evidence_pack.add_argument("--max-passages-per-question", type=int, default=3)
    evidence_pack.add_argument("--max-passages", type=int, default=16)
    evidence_pack.add_argument("--max-passage-chars", type=int, default=3500)
    evidence_pack.add_argument("--max-total-chars", type=int, default=20000)
    evidence_pack.add_argument("--pretty", action="store_true")
    evidence_pack.set_defaults(handler=("evidence_pack", "command_evidence_pack"))

    findings_save = subparsers.add_parser(
        "findings-save",
        help="Attach bounded verified facet findings to a current task receipt",
    )
    findings_save.add_argument("task_receipt", type=Path)
    findings_save.add_argument("input", type=Path, help="JSON findings array or object")
    findings_save.add_argument(
        "--execution-route",
        choices=("coordinator-direct", "low-overhead-worker", "coordinator-fallback"),
        default="coordinator-direct",
        help="Actual model route that produced the findings",
    )
    findings_save.add_argument("--executor")
    findings_save.add_argument("--worker-context", choices=EVIDENCE_WORKER_CONTEXTS)
    findings_save.add_argument(
        "--fallback-reason", choices=EVIDENCE_FALLBACK_REASONS
    )
    findings_save.add_argument("--pretty", action="store_true")
    findings_save.set_defaults(handler=("evidence_pack", "command_findings_save"))

    get = subparsers.add_parser("get", help="Retrieve passages by ID")
    get.add_argument("db", type=Path, help="SQLite index path")
    get.add_argument("passage_ids", type=int, nargs="+", help="Passage IDs from search results")
    get.add_argument(
        "--purpose",
        choices=("scoped-search", "named-gap", "adapter-debugging", "custom-adapter", "locator-verification"),
        default="scoped-search",
    )
    get.add_argument("--task-receipt", type=Path)
    get.add_argument("--gap-facet")
    get.add_argument("--purpose-reason")
    get.add_argument("--around", help="Open matching context initially; explicit --start-char resumes without re-anchoring")
    get.add_argument("--expected-fingerprint", help="Reject retrieval after index generation changes")
    get.add_argument("--limit", type=int, default=12)
    get.add_argument("--offset", type=int, default=0, help="Continue at this passage offset")
    get.add_argument(
        "--start-char", type=int, default=None, help="Continue within the passage at --offset (including 0 for its prefix)"
    )
    get.add_argument("--max-chars", type=int, default=6000, help="Maximum characters per passage")
    get.add_argument("--max-total-chars", type=int, default=20000)
    get.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    get.set_defaults(handler=("index", "command_get"))

    compare = subparsers.add_parser("compare", help="Compare two normalized source files")
    compare.add_argument("left", type=Path, help="First .md, .txt, .jsonl, or .xsd source")
    compare.add_argument("right", type=Path, help="Second .md, .txt, .jsonl, or .xsd source")
    compare.add_argument("--context-lines", type=int, default=2)
    compare.add_argument("--max-total-chars", type=int, default=20000)
    compare.add_argument(
        "--max-source-bytes",
        type=int,
        default=DEFAULT_MAX_SOURCE_BYTES,
        help=f"Maximum bytes per source (default: {DEFAULT_MAX_SOURCE_BYTES})",
    )
    compare.add_argument(
        "--max-units",
        type=int,
        default=DEFAULT_MAX_COMPARE_UNITS,
        help=f"Maximum normalized units per source (default: {DEFAULT_MAX_COMPARE_UNITS})",
    )
    compare.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    compare.set_defaults(handler=("ingestion", "command_compare"))

    return root

def main() -> int:
    args = parser().parse_args()
    try:
        module_name, handler_name = args.handler
        module = importlib.import_module(f".{module_name}", __package__)
        handler = getattr(module, handler_name)
        return handler(args)
    except HANDLED_ERRORS as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
