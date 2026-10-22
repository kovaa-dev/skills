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

## Memory levels and resume

Use three independent durable logical memory levels plus one mandatory transient level:

| Level | Scope and contents | Lifetime and storage |
| --- | --- | --- |
| Reusable index | One authorized corpus: derived chunks, metadata, hashes, retrieval IDs, and complete normalized XSD node graphs when present | Rebuildable `index.sqlite` or compatible corpus adapter; reusable by investigations with the same boundary. Schema IR is keyed by source/block hash and normalizer version; model retrieval sees only bounded fact chunks |
| Search receipt | One query: executed terms, filters, outcome, index fingerprint, stable result locators, and continuation | Compact row in corpus-bound `receipts.sqlite` or a compatible receipt store; reusable by Direct, Retrieval, and Research and stale when its index fingerprint no longer matches |
| Task receipt | One active task/request family: cold/latest executor route, optimization trace, corpus/index fingerprint, facet hashes, relevant search-receipt IDs, decisive locators, completed checks, bounded atomic findings, conflicts, gaps, and next mode | Task/session KV for an equivalent connector, otherwise the required task-scoped `evidence-pack --task-receipt` JSON file; create after the first Retrieval and replace/update rather than append |
| Research state | One investigation: facets, selected evidence, conflicts, gaps, status, and next action | Durable records in `research.sqlite` or one compatible project store; retained only while the investigation or its audit value requires it |

Use this minimal task-receipt shape or a semantically equivalent native object:

```json
{
  "version": 2,
  "route": "retrieval",
  "adapter": "local-index/evidence-pack-v2",
  "index_fingerprint": "current corpus/index generation",
  "question_set_hash": "full request hash for audit",
  "execution": {
    "cold": {"route": "coordinator-direct", "reason": "bounded-inline-evidence"},
    "last": {"route": "coordinator-warm", "reason": "verified-finding-receipt"}
  },
  "optimization": {
    "index": "reused",
    "retrieval": "finding-receipt",
    "query_batch": "skipped",
    "search_receipts": "not-needed",
    "task_receipt": "hit",
    "selection": "coverage-aware",
    "deduplication": "exact",
    "finding_receipt": "hit",
    "reopen": "skipped",
    "evidence_char_limit": 20000
  },
  "facets": [{
    "id": "F1",
    "facet_hash": "hash of stable facet id plus normalized query plan",
    "passage_ids": [12],
    "support_passage_ids": [12],
    "check_passage_ids": [12],
    "receipt_ids": ["Q-..."],
    "locators": [{"passage_id": 12, "source": "standard.md", "source_hash": "...", "section": "4.2"}],
    "checks": ["support", "control"],
    "finding": {
      "status": "verified",
      "claims": [{"text": "Atomic supported proposition", "passage_ids": [12], "scope": "conditions or applicability"}]
    }
  }],
  "conflicts": [],
  "gaps": [],
  "next_mode": "direct"
}
```

For several corpora, optional `catalog.sqlite` is a routing layer within the first two levels: it points to isolated corpus indexes/receipt stores, maps overlapping logical projects to those corpora, and keeps composite locator-only receipts. It is not another evidence ledger. `research.sqlite` may bind to one corpus or a frozen concrete subset of one catalog and records each receipt link's store kind/path. Project IDs remain explanatory metadata; membership changes do not silently alter an existing investigation. Neither receipt level requires research state, and research promotes only selected verified findings rather than duplicating receipt contents.

A task receipt may contain only bounded atomic findings produced from its selected passages plus compact source/hash/page/section/version/date locators; locator entries never contain passage text. It must not contain copied snippets, full passages, tool logs, reasoning traces, or final-answer prose. `findings-save` accepts at most eight facets and eight claims per facet; each claim text is at most 1,000 characters, optional scope at most 500 characters, and every referenced passage must already belong to that facet. `verified` also requires both support and control coverage. `conflicted` and `unresolved` keep useful bounded state without being treated as reusable verified answers. An exact warm response attaches only the locators referenced by its returned claims, so it remains citable without reopening source text.

Reuse is facet-scoped. `facet_hash` deliberately covers the stable facet ID and normalized query plan, not display wording, so a harmless rephrasing can reuse work. A semantic change must change the query plan or facet ID. The corpus fingerprint must also match. A version mismatch, malformed finding, missing support/control coverage, outside passage ID, or changed corpus fails closed. Receipts are replaced atomically rather than appended, so obsolete facets and findings do not accumulate indefinitely; unrequested facets are not returned to the model.

Prefer compatible project stores as adapters. Otherwise keep `index.sqlite` and `receipts.sqlite` in a persistent derived-data location for the authorized corpus, and keep each `research.sqlite` in its investigation location. Report the paths that matter to handoff; do not place them in the installed skill, a temporary directory, or among original sources. Several investigations may share one corpus index and receipt store, but never share one research database across unrelated scopes.

For one investigation, at most one process, agent, or session may mutate its research store at a time. This includes record updates and searches that link receipts into that store. Read-only inspection and searches that do not write research state may run in parallel; the coordinator serializes mutations.

```bash
scripts/corpus receipts-init receipts.sqlite --corpus CORPUS_PATH --index index.sqlite
scripts/corpus receipts-info receipts.sqlite
scripts/corpus research-init research.sqlite --scope "question" --corpus CORPUS_PATH --index index.sqlite
scripts/corpus research-info research.sqlite --resume
```

For ordinary local Retrieval, use `evidence-pack --execution-route auto --pack-output ...`: it checks deterministic facet/query receipts, searches only misses, selects and reopens unique passages, estimates the cheaper interpretation route, and saves a compact task receipt in one command. Its question input accepts up to eight facets and three planned queries per facet; every explicit plan includes both `support` and `check`. Without a measured routing profile, auto returns inline evidence for coordinator interpretation. When a profile proves a worker saving, stdout contains a compact manifest and the full passages stay at `pack_path`. After interpretation, `findings-save` validates and attaches the bounded findings using the actual route. On an exact verified hit, the helper returns findings only: no search, passage reopen, or worker. Use lower-level `search --receipts-db`, `search-many`, and `get` only for a named gap, custom adapter, or diagnostic. The receipt store remains usable without a research database; an external retrieval adapter must map to the receipt-store interface rather than writing query data into research state.

Use `research-apply` to commit several state changes from one bounded JSON file atomically. Use `research-put` for a single correction. Evidence lists are compact by default; add `--details` only to retrieve a stored excerpt or interpretation. The supported research kinds are `facet`, `evidence`, `gap`, and `conflict`; inspect command help instead of loading the script into context. Example:

```bash
scripts/corpus research-put research.sqlite facet F1 --question "Termination conditions" --status open
scripts/corpus search index.sqlite "termination notice" --purpose named-gap --task-receipt task-receipt.json --gap-facet F1 --receipts-db receipts.sqlite --research-db research.sqlite --facet-id F1
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

Before a query, let `evidence-pack` check the task receipt and then current query receipts so completed and meaningful negative searches are not repeated against an unchanged corpus. On an unchanged verified repeat it returns only the requested findings; on a partial repeat it searches only facet-hash misses and reopens only their needed passages. A new search needs a stale fingerprint, changed facet query plan/ID, missing locator, named gap, or explicit independent review. Query receipts store search memory but never promote it to evidence. Add a research row only after a finding is selected, verified, and relevant to a material facet; reference stable locators instead of copying receipt data. Keep `finding` atomic. Omit `excerpt` and `interpretation` unless they prevent material re-analysis; each is limited to 2,000 characters and remains hidden from ordinary evidence reads. Do not store every wording variant, raw session/tool logs, full documents, final answer prose, or repeated passage text. Re-indexing can invalidate passage IDs and offsets; use only receipts marked current and relocate durable evidence by stable source metadata.

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
