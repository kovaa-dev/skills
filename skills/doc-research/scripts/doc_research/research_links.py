from __future__ import annotations

import argparse
import json
from pathlib import Path

from .catalog_store import catalog_snapshot, require_catalog_database
from .common import database, emit_json, harden_database_permissions, utc_now
from .index import resolve_index_binding

from .research_store import (
    decode_catalog_scope,
    evidence_freshness,
    require_facet,
    require_research_database,
    require_research_schema,
)

def validate_research_receipt_link(
    research_db: Path,
    corpus_root: Path,
    facet_id: str,
    index_db: Path,
    fingerprint: str,
) -> Path:
    state_path = require_research_database(research_db)
    with database(state_path, readonly=True) as connection:
        require_research_schema(connection)
        state = connection.execute(
            "SELECT * FROM research_state WHERE singleton = 1"
        ).fetchone()
        if state is not None and state["binding_kind"] != "corpus":
            raise ValueError(
                "Catalog-bound research must link searches through catalog-search"
            )
        if state is None or Path(state["corpus_root"]).resolve() != corpus_root.resolve():
            raise ValueError("Research state corpus does not match the receipt corpus")
        if not state["index_path"]:
            raise ValueError("Research state has no bound index; run research-sync --index")
        if (
            Path(state["index_path"]).resolve() != index_db.resolve()
            or state["index_fingerprint"] != fingerprint
        ):
            raise ValueError("Research state index is stale; run research-sync before searching")
        require_facet(connection, facet_id)
    return state_path

def command_research_sync(args: argparse.Namespace) -> int:
    db_path = require_research_database(args.db)
    with database(db_path) as connection:
        require_research_schema(connection)
        state = connection.execute(
            "SELECT * FROM research_state WHERE singleton = 1"
        ).fetchone()
        if state is None:
            raise ValueError("Research database has no state row")
        values = dict(state)
        if values["binding_kind"] == "catalog":
            if args.index is not None:
                raise ValueError("--index cannot be used with catalog-bound research")
            selected_catalog = args.catalog or (
                Path(str(values["catalog_path"])) if values["catalog_path"] else None
            )
            if selected_catalog is None:
                raise ValueError("No catalog is bound; provide --catalog")
            catalog_path = require_catalog_database(selected_catalog)
            corpus_ids, access_boundaries, _ = decode_catalog_scope(
                values["catalog_scope_json"]
            )
            with database(catalog_path, readonly=True) as catalog:
                _, fingerprint, _ = catalog_snapshot(
                    catalog, corpus_ids or None, access_boundaries or None
                )
            changed = (
                str(catalog_path) != values["catalog_path"]
                or fingerprint != values["catalog_fingerprint"]
            )
            connection.execute(
                """
                UPDATE research_state
                SET catalog_path = ?, catalog_fingerprint = ?, updated_at = ?
                WHERE singleton = 1
                """,
                (str(catalog_path), fingerprint, utc_now()),
            )
            payload = {
                "database": str(db_path),
                "binding_kind": "catalog",
                "catalog": str(catalog_path),
                "catalog_fingerprint": fingerprint,
                "changed": changed,
            }
        else:
            if args.catalog is not None:
                raise ValueError("--catalog cannot be used with corpus-bound research")
            selected_index = args.index or (
                Path(str(values["index_path"])) if values["index_path"] else None
            )
            if selected_index is None:
                raise ValueError("No index is bound; provide --index")
            index_path, fingerprint = resolve_index_binding(
                selected_index, Path(str(values["corpus_root"]))
            )
            changed = (
                str(index_path) != values["index_path"]
                or fingerprint != values["index_fingerprint"]
            )
            connection.execute(
                """
                UPDATE research_state
                SET index_path = ?, index_fingerprint = ?, updated_at = ?
                WHERE singleton = 1
                """,
                (str(index_path), fingerprint, utc_now()),
            )
            payload = {
                "database": str(db_path),
                "binding_kind": "corpus",
                "index": str(index_path),
                "index_fingerprint": fingerprint,
                "changed": changed,
            }
        refreshed = dict(connection.execute(
            "SELECT * FROM research_state WHERE singleton = 1"
        ).fetchone())
        invalidated = 0
        freshness_cache: dict[str, tuple[object, str]] = {}
        for evidence in connection.execute("SELECT * FROM evidence WHERE verified = 1").fetchall():
            if not evidence_freshness(refreshed, dict(evidence), freshness_cache)["source_current"]:
                connection.execute(
                    "UPDATE evidence SET verified = 0, status = CASE WHEN status = 'confirmed' "
                    "THEN 'unresolved' ELSE status END, updated_at = ? WHERE evidence_id = ?",
                    (utc_now(), evidence["evidence_id"]),
                )
                invalidated += 1
        payload["invalidated_evidence"] = invalidated
    harden_database_permissions(db_path)
    emit_json(payload, args.pretty)
    return 0

def link_receipt_to_research(
    research_db: Path,
    receipt_db: Path,
    corpus_root: Path,
    index_db: Path,
    fingerprint: str,
    receipt_id: str,
    facet_id: str,
) -> bool:
    state_path = require_research_database(research_db)
    now = utc_now()
    linked = False
    with database(state_path) as connection:
        require_research_schema(connection)
        state = connection.execute("SELECT * FROM research_state WHERE singleton = 1").fetchone()
        values = dict(state) if state is not None else None
        if (
            values is None
            or values["binding_kind"] != "corpus"
            or Path(str(values["corpus_root"])).resolve() != corpus_root.resolve()
            or not values["index_path"]
            or Path(str(values["index_path"])).resolve() != index_db.resolve()
            or values["index_fingerprint"] != fingerprint
        ):
            raise ValueError("Research state changed during search; retry after research-sync")
        require_facet(connection, facet_id)
        cursor = connection.execute(
            """
            INSERT INTO receipt_links(
                facet_id, store_kind, store_path, receipt_id, linked_at
            ) VALUES (?, 'receipts', ?, ?, ?)
            ON CONFLICT(facet_id, store_kind, store_path, receipt_id) DO NOTHING
            """,
            (facet_id, str(receipt_db.resolve()), receipt_id, now),
        )
        linked = cursor.rowcount > 0
        if linked:
            connection.execute(
                "UPDATE research_state SET updated_at = ? WHERE singleton = 1", (now,)
            )
    if linked:
        harden_database_permissions(state_path)
    return linked
def link_catalog_receipt_to_research(
    research_db: Path,
    catalog_db: Path,
    receipt_id: str,
    facet_id: str,
) -> bool:
    state_path = require_research_database(research_db)
    now = utc_now()
    with database(state_path) as connection:
        require_research_schema(connection)
        state = connection.execute(
            "SELECT * FROM research_state WHERE singleton = 1"
        ).fetchone()
        if (
            state is None
            or state["binding_kind"] != "catalog"
            or Path(state["catalog_path"]).resolve() != catalog_db.resolve()
        ):
            raise ValueError(
                "Research catalog binding changed; run research-sync --catalog before searching"
            )
        scoped_corpus_ids, scoped_boundaries, _ = decode_catalog_scope(
            state["catalog_scope_json"]
        )
        with database(catalog_db, readonly=True) as catalog:
            entries, catalog_fingerprint_value, _ = catalog_snapshot(
                catalog,
                scoped_corpus_ids or None,
                scoped_boundaries or None,
            )
            receipt = catalog.execute(
                "SELECT corpus_ids_json FROM federated_receipts WHERE receipt_id = ?",
                (receipt_id,),
            ).fetchone()
        if state["catalog_fingerprint"] != catalog_fingerprint_value:
            raise ValueError(
                "Research catalog binding changed; run research-sync --catalog before searching"
            )
        if receipt is None:
            raise ValueError(f"Federated receipt does not exist: {receipt_id}")
        receipt_corpus_ids = json.loads(str(receipt["corpus_ids_json"]))
        allowed_corpus_ids = {str(item["corpus_id"]) for item in entries}
        if (
            not isinstance(receipt_corpus_ids, list)
            or not all(isinstance(item, str) for item in receipt_corpus_ids)
            or not set(receipt_corpus_ids).issubset(allowed_corpus_ids)
        ):
            raise ValueError("Federated receipt falls outside the research catalog scope")
        require_facet(connection, facet_id)
        cursor = connection.execute(
            """
            INSERT INTO receipt_links(
                facet_id, store_kind, store_path, receipt_id, linked_at
            ) VALUES (?, 'catalog', ?, ?, ?)
            ON CONFLICT(facet_id, store_kind, store_path, receipt_id) DO NOTHING
            """,
            (facet_id, str(catalog_db), receipt_id, now),
        )
        linked = cursor.rowcount > 0
        if linked:
            connection.execute(
                "UPDATE research_state SET updated_at = ? WHERE singleton = 1", (now,)
            )
    if linked:
        harden_database_permissions(state_path)
    return linked
