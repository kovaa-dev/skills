# Evidence ledger

This reference owns helper storage contracts, not a prerequisite for keeping ordinary notes. Apply the always-on memory contract in `SKILL.md` on every route. Use a research ledger when its structured updates materially help a long or multi-source investigation. Choosing Research does not itself require or authorize `research.sqlite`. Direct and Retrieval preserve findings in a simple note when sufficient; they need no facets or database rows.

## Lightweight memory and existing work

A small Markdown/JSON note or compatible project store is a complete analytical owner when it meets the task's needs. Keep the question and scope, source identity/generation, selected supported findings with stable locators, necessary conditions, unresolved ambiguities/conflicts, and next action if any. No fixed field names, receipt conversion, index, or extra reference load is required. Edit it normally and update affected entries rather than appending a transcript. Do not create a second note when an existing store already owns these findings.

Non-helper searches retain compact query/scope, generation, outcome, selected locators and any coverage/continuation limits in the same owner. A scoped no-hit result is reusable search state, not proof of absence. For indexed search, pass the authorized `--receipts-db` so the helper checks and saves query receipts; do not copy those rows into an analytical note. Batch pending non-helper updates and save before completion/handoff, without a separate write turn after every query. A direct read with no search needs findings and locators, not a fabricated query receipt.

For a repeat, check the known note's question/scope, verification provenance and source generation. Reuse current supported findings without automatic rereading; retain known limits. Leave unchanged notes untouched: no session stamp, duplicate summary, or ceremonial save. Unverified notes are leads, and changed/disputed facts or missing qualifiers require targeted verification. A hash match does not certify a conclusion. A current unresolved result can avoid repeating an exhausted query but cannot become a positive or negative answer merely because it was saved.

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

These are semantic requirements for relevant evidence, not mandatory columns for a simple note. Use a note, helper task receipt, or separate `research.sqlite`/compatible analytical store according to the task; do not store durable findings inside the rebuildable FTS index. In-session-only state is a fallback when persistence is prohibited or unavailable, not an exception for apparently one-off questions.

## Memory levels and resume

Use only the memory roles that the task needs. Retrieval memory and analytical ownership are separate:

| Level | Scope and contents | Lifetime and storage |
| --- | --- | --- |
| Reusable index | One authorized corpus: derived chunks, metadata, hashes, retrieval IDs, and complete normalized XSD node graphs when present | Rebuildable `index.sqlite` or compatible corpus adapter; reusable by investigations with the same boundary. Schema IR is keyed by source/block hash and normalizer version; model retrieval sees only bounded fact chunks |
| Search receipt | One query: executed terms, filters, outcome, index fingerprint, stable result locators, and continuation | Compact row in corpus-bound `receipts.sqlite` or a compatible receipt store; reusable by Direct, Retrieval, and Research and stale when its index fingerprint no longer matches |
| Task receipt | One active task/request family: corpus/index fingerprint, question/scope-aware facet hashes, search-receipt IDs, decisive locators, checks, and optionally bounded findings, conflicts, and gaps | Optional task/session KV or `evidence-pack --task-receipt` JSON; upsert affected facets atomically, retaining unrelated findings and conflicts |
| Research state | One investigation: facets, selected evidence, conflicts, gaps, status, and next action | Durable records in `research.sqlite` or one compatible project store; retained only while the investigation or its audit value requires it |

Choose one analytical owner: a note, task receipt, Research state, or compatible existing store. A pack receipt may hold retrieval metadata alongside Research without duplicating its conclusions/progress. A direct or scoped answer needs no task receipt. Helpers maintain their own locators and continuation; use their commands rather than hand-repairing helper JSON. This does not restrict editing ordinary notes. Example helper task-receipt shape:

```json
{
  "version": 3,
  "route": "retrieval",
  "adapter": "local-index/evidence-pack-v3",
  "index_fingerprint": "current corpus/index generation",
  "question_set_hash": "full request hash for audit",
  "execution": {
    "cold": {"route": "coordinator-direct", "reason": "bounded-inline-evidence"},
    "last": {"route": "coordinator-warm", "reason": "saved-finding-receipt"}
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
    "facet_hash": "hash of exact question, facet id, query plan, scope, and relevant options",
    "passage_ids": [12],
    "support_passage_ids": [12],
    "check_passage_ids": [12],
    "receipt_ids": ["Q-..."],
    "locators": [{"passage_id": 12, "source": "standard.md", "source_hash": "...", "section": "4.2", "line_start": 90, "line_end": 102}],
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

For several corpora, optional `catalog.sqlite` is a routing layer within the first two levels: it points to isolated corpus indexes/receipt stores, maps overlapping logical projects to those corpora, and keeps composite locator-only receipts. It is not another evidence ledger. `research.sqlite` may bind to one corpus or a frozen concrete subset of one catalog and records each receipt link's store kind/path. Project IDs remain explanatory metadata; membership changes do not silently alter an existing investigation. Research evidence writes must validate that `corpus_id` belongs to the frozen investigation scope. Neither receipt level requires research state, and research promotes only selected verified findings rather than duplicating receipt contents.

A task receipt may contain bounded atomic findings from selected passages or structural facts plus compact source/hash/page/section/line/version/date locators; schema locators include the block hash and exact XSD/Markdown lines. Locator entries never contain passage or fact text. Do not store full passages, tool logs, reasoning traces, or final-answer prose. `findings-save` accepts at most 50 facets and 50 claims per facet; each claim text is at most 1,000 characters and optional scope at most 500 characters. Referenced evidence must belong to the facet; normal scoped retrieval registers newly selected locators through the helper. The analyst establishes support for exact claims and checks contrary evidence/exceptions for control claims. Lexical support/check roles are not a mechanical save gate or proof of truth/completeness. `conflicted` and `unresolved` retain useful state without becoming reusable verified answers; an unresolved facet may have `claims: []` and a reason. Exact warm responses retain claim locators without reopening source text.

Reuse is question- and scope-aware. `facet_hash` includes the question text, stable ID, normalized query plan, requested versions/filters, and relevant kind/verification/group/selection options; query similarity alone cannot establish unchanged meaning. The corpus fingerprint must also match. A changed question with identical terms must not receive an old answer. A version mismatch, malformed finding, missing citation provenance, outside evidence ID, or changed corpus fails closed for verified reuse. A source-local fact may remain true after a corpus change, but earlier corpus-wide completeness does not. Recheck affected evidence and coverage before reusing that conclusion.

Upsert affected facets atomically rather than replacing the entire request family. Return requested findings while keeping retained gaps and conflicts visible. An unchanged repeat reuses unresolved/conflicted findings too, without certifying them or automatically retrying an exhausted search. Refine the question/query or increase retrieval depth/breadth to investigate further. Retrieval hits cannot clear an analyst's unresolved gap or conflict. Larger budgets must actually widen candidate/context selection; smaller display budgets do not invalidate a current finding. Prune only under explicit lifecycle/cleanup authority, not as a side effect of a subset follow-up.

After a source-generation change, retained unrequested facets are stale and their findings unresolved, not silently deleted or reused. Re-retrieving an unchanged question may retain one bounded `previous_finding` snapshot with its old provenance for review; it is not current evidence or an accumulating history. Saving the replacement finding removes that snapshot.

Prefer compatible project stores as adapters. With durable-write authority, keep `index.sqlite` and `receipts.sqlite` in a persistent derived-data location for the authorized corpus, and each `research.sqlite` in its investigation location. Without it, use task-local temporary state and disclose its lifetime. Report paths needed for handoff. Keep all generated outputs distinct from originals, databases, and other inputs; never overwrite an input through an output-path alias. Several investigations may share a corpus index and receipt store but not one analytical database across unrelated scopes.

For one investigation, at most one process, agent, or session may mutate its research store at a time. This includes record updates and searches that link receipts into that store. Read-only inspection and searches that do not write research state may run in parallel; the coordinator serializes mutations.

```bash
scripts/corpus receipts-init receipts.sqlite --corpus CORPUS_PATH --index index.sqlite
scripts/corpus receipts-info receipts.sqlite
scripts/corpus research-init research.sqlite --scope "question" --corpus CORPUS_PATH --index index.sqlite
scripts/corpus research-info research.sqlite --resume
```

For ordinary `search --receipts-db`, a missing explicitly writable receipt store is created on save; `--read-only-receipts` treats a missing store as a cache miss without creating it. Existing foreign, corrupt, or mismatched stores still fail closed instead of being overwritten.

For independent facet batches, optional `evidence-pack --execution-route auto --pack-output ...` combines receipt reuse, searches, enumeration continuation, indexed schema lookup, unique passage retrieval, and interpretation cost estimation. It accepts up to 50 facets and 20 planned queries per facet. Without explicit worker costs it returns inline evidence; an unchanged saved finding returns with its status and locators, without search or passage reopen. `search --receipts-db`, `search-many`, `schema-query`, and `get` are also normal routes and may refine a pack's results. With a task receipt and facet selected, helpers register retrieved locators automatically. Use `findings-save` only when that receipt is the analytical owner. A connector can provide verifiable evidence without implementing reusable memory; caching requires the stronger receipt-equivalence contract in source routing.

A pack question plan is needed only for that helper, not for ordinary research:

```json
{"questions":[{"id":"types","question":"Which message types and signers exist?","kind":"enumeration","group_by":"section","max_items":12,"verification":"control","queries":[{"query":"message signer","role":"support"},{"query":"optional required","role":"check"}]}]}
```

```bash
scripts/corpus evidence-pack CORPUS questions.json --db index.sqlite --task-receipt task-receipt.json
```

`kind: lookup` selects bounded facts; `enumeration` broadens grouped candidates; `schema` adds structural facts. `verification: exact` requires authoritative support; `control` additionally checks contrary evidence and exceptions. Neither a tag nor a query count proves completeness. Cost routing and worker output are separate opt-ins, not required for batching.

To extend an existing task receipt with scoped passage evidence, select its facet on search/get. The retained flag name `--gap-facet` selects the owner; it does not require proving a gap:

```bash
scripts/corpus search index.sqlite "termination amendment" --task-receipt task-receipt.json --gap-facet F1
scripts/corpus get index.sqlite PASSAGE_ID --around "termination amendment" --task-receipt task-receipt.json --gap-facet F1
scripts/corpus findings-save task-receipt.json findings.json
```

Use an ID actually returned by search, inspect the context, and write supported findings before saving. Structural queries can guide analysis directly; save only evidence registered to the target facet, or record verified original locators in the analytical owner.

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

Reuse current receipts when they answer the same question and scope. A partial request retrieves only missing or changed evidence; later refinement may use new terms, versions, filters, or context without a named-gap gate. Query receipts remember retrieval outcomes and never promote lexical hits or misses to semantic proof. Add research evidence only when selected and relevant to a material facet, recording verification honestly; keep unresolved questions and conflicts in their own records. Reference stable locators instead of copying receipt data. Keep findings atomic. Omit `excerpt` and `interpretation` unless they prevent material re-analysis; each is limited to 2,000 characters and hidden from ordinary evidence reads. Do not store raw session/tool logs, full documents, final answers, or repeated passages. Re-indexing can invalidate passage IDs and offsets; use current receipts and relocate durable evidence by stable source metadata.

## Claim discipline

- One row supports one coherent proposition and maps to one facet.
- Before adding a row, compare proposition, source identity, version, location, scope, conditions, and exceptions. Semantic similarity proposes a duplicate; it does not prove one.
- Update provenance or verification on an existing row only when its meaning and applicability are unchanged. Keep separate rows for materially different findings or genuinely independent originals. A copied summary or repeated citation to the same passage is not independent support.
- Preserve enough surrounding text to avoid reversing conditions, exceptions, or negation.
- Do not present interpretation as a quotation.
- Link conflicting rows rather than silently selecting the convenient one.
- Prefer primary/controlling sources; label secondary material.
- A missing result is not evidence of absence until the search scope, terms, versions, and unreadable sources have been checked.
- Verify decisive claims against originals when first establishing them or when freshness, scope, provenance, dispute, or needed detail changes. Do not repeat already completed verification solely because a new session started. Retrieval ranking alone is not verification.
- A generated or approved report may support a claim about its own issuance or decision status, but cannot independently validate the evidence it summarizes.

Create rows only for evidence used in the analysis. Pass the verified evidence forward; reopen the original when a quotation, context, table relationship, or dispute is not already verified in the retained material.

## Synthesis

Draft from verified evidence already in context or in the selected analytical owner, not unsupported recollection. No persisted ledger is required to use evidence just checked in this session. Map material conclusions to source locators. Preserve applicability, conditions, exceptions, versions, and disagreements when shortening findings or combining a worker's results. If several rows depend on one ambiguous passage, report one shared uncertainty rather than multiplying confidence. A required child field within a conditional parent must retain that condition in the final answer.

## Internal and delivered state

Keep inventory, receipts, passage IDs, ledger, and coverage out of the prose answer, but persist the compact subset above only when authorized. For Direct/Retrieval handoff, report the receipt store only when useful; for durable Research, report `research.sqlite`, `receipts.sqlite`, and the next action. If durable writes are not authorized, return a compact resume block instead of implying that another session can discover internal state. Unless requested, deliver only the answer, claim-level citations, material conflicts, corpus/version limits, and unresolved questions.
