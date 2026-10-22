# Evidence ledger

Use a research ledger only when several documents support consequential conclusions, conflicts/completeness must be explicit, or investigation state must resume later. Choosing the Research route does not itself require or authorize `research.sqlite`: without durable-write authority, keep the same facet/evidence/conflict/gap model task-local and return a compact resume block. Direct and Retrieval need only citations plus compact receipts for indexed queries; they do not need facets or evidence rows.

## Fields

| Field | Meaning |
| --- | --- |
| `claim_id` | Stable local identifier for the question or candidate conclusion |
| `facet` | The part of the research question being answered |
| `corpus_id` | Required for catalog-bound evidence; selects the physical corpus needed to reopen a passage |
| `finding` | Concise factual proposition supported by the source |
| `source` | Stable identifier, path, title, or connector ID for the original evidence record |
| `source_version` | Published version, effective date, amendment, or other applicable version; label an unverified metadata claim |
| `source_hash` | Verified hash of the authorized original when available; do not substitute a normalized or OCR file hash |
| `derived_from` | Upstream source identifier when the selected passage comes from extraction, OCR, computation, or synthesis |
| `transformation` | Transformation and, only when reproducibility matters, tool/version or method and derived-artifact hash |
| `date` | Document date stated by the source, when available |
| `page` | Printed or PDF page when available |
| `section` | Heading, clause, sheet/table, or other structural location |
| `passage_id` | Ephemeral retrieval identifier used to reopen selected text; never the only durable locator and, for a catalog, meaningful only with `corpus_id` |
| `excerpt` | Optional short source text only when exact wording, a number, condition, or negation must survive handoff |
| `interpretation` | Optional compact analysis kept separate from the excerpt |
| `confidence` | `confirmed`, `probable`, or `uncertain`, with a reason when not confirmed |
| `conflict` | Competing source or interpretation that affects the conclusion |
| `verified` | Whether the decisive passage was checked in immediate context or against the rendered original |

Use only fields that affect the current task. A compact in-session table is enough for one-off work. For reusable or resumable work, use the helper's separate `research.sqlite`; do not store durable findings inside the rebuildable FTS index.

## Three memory levels and resume

Use three independent logical memory levels:

| Level | Scope and contents | Lifetime and storage |
| --- | --- | --- |
| Reusable index | One authorized corpus: derived chunks, metadata, hashes, and retrieval IDs | Rebuildable `index.sqlite` or compatible corpus adapter; reusable by investigations with the same boundary |
| Search receipt | One query: executed terms, filters, outcome, index fingerprint, stable result locators, and continuation | Compact row in corpus-bound `receipts.sqlite` or a compatible receipt store; reusable by Direct, Retrieval, and Research and stale when its index fingerprint no longer matches |
| Research state | One investigation: facets, selected evidence, conflicts, gaps, status, and next action | Durable records in `research.sqlite` or one compatible project store; retained only while the investigation or its audit value requires it |

For several corpora, optional `catalog.sqlite` is a routing layer within the first two levels: it points to isolated corpus indexes/receipt stores, maps overlapping logical projects to those corpora, and keeps composite locator-only receipts. It is not another evidence ledger. `research.sqlite` may bind to one corpus or a frozen concrete subset of one catalog and records each receipt link's store kind/path. Project IDs remain explanatory metadata; membership changes do not silently alter an existing investigation. The receipt level does not require research state, and research promotes only selected verified findings rather than duplicating receipt contents.

Prefer compatible project stores as adapters. Otherwise keep `index.sqlite` and `receipts.sqlite` in a persistent derived-data location for the authorized corpus, and keep each `research.sqlite` in its investigation location. Report the paths that matter to handoff; do not place them in the installed skill, a temporary directory, or among original sources. Several investigations may share one corpus index and receipt store, but never share one research database across unrelated scopes.

For one investigation, at most one process, agent, or session may mutate its research store at a time. This includes record updates and searches that link receipts into that store. Read-only inspection and searches that do not write research state may run in parallel; the coordinator serializes mutations.

```bash
scripts/corpus receipts-init receipts.sqlite --corpus CORPUS_DIR --index index.sqlite
scripts/corpus receipts-info receipts.sqlite
scripts/corpus research-init research.sqlite --scope "question" --corpus CORPUS_DIR --index index.sqlite
scripts/corpus research-info research.sqlite --resume
```

Before an indexed query, let `search --receipts-db` check the deterministic current receipt when receipt writes are authorized. Without that authority, add `--read-only-receipts`: a hit is reused, while a miss executes without persistence. A hit returns stable locators without passage text; fetch only needed IDs. Use `search-many` for up to eight independent queries. Add `--research-db` and `--facet-id` only when a receipt materially explains coverage, a gap, or the next resumable action; they are intentionally incompatible with read-only receipt mode. Leave exploratory wording variants in the receipt store alone. The receipt store remains usable without a research database; an external retrieval adapter must map to the receipt-store interface rather than writing query data into research state.

Use `research-apply` to commit several state changes from one bounded JSON file atomically. Use `research-put` for a single correction. Evidence lists are compact by default; add `--details` only to retrieve a stored excerpt or interpretation. The supported research kinds are `facet`, `evidence`, `gap`, and `conflict`; inspect command help instead of loading the script into context. Example:

```bash
scripts/corpus research-put research.sqlite facet F1 --question "Termination conditions" --status open
scripts/corpus search index.sqlite "termination notice" --receipts-db receipts.sqlite --research-db research.sqlite --facet-id F1
scripts/corpus research-list research.sqlite evidence --facet F1
```

For one cross-corpus investigation, initialize with `--catalog catalog.sqlite` and link searches through `catalog-search`; do not attach a catalog receipt to corpus-bound research or vice versa. A catalog receipt locator is stable only together with its `corpus_id` and source metadata.

Batch files are bounded JSON. `queries.json` is an array, or `{"queries":[...]}`, whose items accept `query`, optional search mode/filters/offset, and optional `facet_id`, `receipt_id`, or `refresh`. `delta.json` accepts one optional investigation `state` object and ordered `records`; records use `kind`, `id`, and the same named fields as `research-put`. Native `evidence_ids` arrays and boolean `verified` are accepted, so callers need not encode nested JSON strings. For example:

```json
{
  "state": {"next_action": "Verify the amendment"},
  "records": [
    {"kind": "facet", "id": "F1", "question": "Termination conditions", "status": "open"},
    {"kind": "gap", "id": "G1", "facet": "F1", "description": "Amendment not checked", "next_query": "termination amendment"}
  ]
}
```

On resume, call `research-info --resume`; each linked receipt carries its own store path, so the command returns active facets, evidence counts, open gaps/conflicts, recent linked receipts, next action, and live corpus/catalog status in one bounded payload. For Direct/Retrieval, inspect `receipts-list` or issue the exact search and accept a receipt hit before broadening. After a changed or replacement index, receipts from prior generations remain fingerprinted history and are excluded by default; rerunning an equivalent search refreshes its stable cache key. `receipts-sync` updates the receipt-store binding; `research-sync --index` or `research-sync --catalog` accepts a reviewed generation change without rewriting receipt history. Use `research-update` for a single investigation status change and do not create a second state file for the same investigation. The helper intentionally supports only its current database layouts; an incompatible database fails closed instead of invoking migration behavior.

## Compact research state

For resumable work, persist only:

- corpus or catalog boundary and applicable versions;
- facets with status `open`, `supported`, `refuted`, `conflicted`, `unresolved`, or `out-of-scope`;
- links from relevant facets to material receipts in the independent receipt store;
- selected passage and claim IDs;
- material conflicts and named coverage gaps;
- the investigation's next analytical action; search/get continuation remains in the receipt or caller state that owns it.

Before a query, check its current receipt so completed and meaningful negative searches are not repeated against an unchanged corpus. In writable receipt mode, search stores query memory but never promotes it to evidence; read-only mode reports that a miss was not persisted. Add a research row only after a finding is selected, verified, and relevant to a material facet; reference stable locators instead of copying receipt data. Keep `finding` atomic. Omit `excerpt` and `interpretation` unless they prevent material re-analysis; each is limited to 2,000 characters and remains hidden from ordinary evidence reads. Do not store every wording variant, raw session/tool logs, full documents, or repeated passage text. Re-indexing can invalidate passage IDs and offsets; use only receipts marked current and relocate durable evidence by stable source metadata.

## Claim discipline

- One row supports one coherent proposition and maps to one facet.
- Before adding a row, compare proposition, source identity, version, location, scope, conditions, and exceptions. Semantic similarity proposes a duplicate; it does not prove one.
- Update provenance or verification on an existing row only when its meaning and applicability are unchanged. Keep separate rows for materially different findings or genuinely independent originals. A copied summary or repeated citation to the same passage is not independent support.
- Preserve enough surrounding text to avoid reversing conditions, exceptions, or negation.
- Do not present interpretation as a quotation.
- Link conflicting rows rather than silently selecting the convenient one.
- Prefer primary/controlling sources; label secondary material.
- A missing result is not evidence of absence until the search scope, terms, versions, and unreadable sources have been checked.
- Reopen the original source for decisive claims. Retrieval ranking alone is not verification.
- A generated or approved report may support a claim about its own issuance or decision status, but cannot independently validate the evidence it summarizes.

Create rows only for evidence used in the analysis. Pass rows forward and reopen the original for quotations, context, tables, or disputes.

## Synthesis

Draft from the ledger, not session memory. Map each material conclusion to rows. If several rows depend on one ambiguous passage, report one shared uncertainty rather than multiplying confidence.

## Internal and delivered state

Keep inventory, receipts, passage IDs, ledger, and coverage out of the prose answer, but persist the compact subset above only when authorized. For Direct/Retrieval handoff, report the receipt store only when useful; for durable Research, report `research.sqlite`, `receipts.sqlite`, and the next action. If durable writes are not authorized, return a compact resume block instead of implying that another session can discover internal state. Unless requested, deliver only the answer, claim-level citations, material conflicts, corpus/version limits, and unresolved questions.
