# Evidence ledger

This reference owns helper storage contracts, not a prerequisite for keeping ordinary notes. Apply the always-on memory contract in `SKILL.md` on every route. Use a research ledger when its structured updates materially help a long or multi-source investigation. Choosing Research does not itself require or authorize `research.sqlite`. Direct and Retrieval preserve findings in a simple note when sufficient; they need no facets or database rows.

## Lightweight memory and existing work

For a local UTF-8 source and an authorized answer-note location, use the existing launcher (`scripts/corpus` on POSIX, `scripts\corpus.cmd` on Windows):

```bash
scripts/corpus read-text source.md --memory answers.json --scope "question" --find "term" --find "synonym"
scripts/corpus read-text source.md --lines 20:60 90:130 --source-hash HASH
scripts/corpus save-answer source.md --memory answers.json --scope "question" --source-hash HASH --points '{"mass":{"text":"Mass unit is kg","status":"confirmed","basis":"Checked the unit in its applicable table","coverage":"line 20","quote":["20=kg"],"exact":["kg"]}}' --reviewed mass
```

`--memory` reads one answer-note owner and checks current source path/hash before source-content selection. A missing owner falls through to the requested search; malformed/unreadable owners fail closed. A wholly stale scope returns its old points as noncurrent leads for targeted rechecking, not an automatic broad search. `--scope` is optional: an exact match selects that scope; absent or unrecognized keys return bounded `candidates`. Mixed generations return `partial`. Every point includes `source_current` and `reusable`: the latter means a current analyst-confirmed point with current confirmed dependencies, not independently certified truth. Assess applicability yourself: candidates are not equivalent answers. Retrieve missing evidence without memory flags. Updating one point never retags untouched points with a new source hash. No database or index is created.

Memory status `current` means matching source bytes, not certified correctness. Hashing occurs in this invocation; a saved hash alone is insufficient. Assess basis, applicability and limits before reuse. Large entries or candidate collections return `text` pages and `next_offset`; continue with the same scope, `--memory-offset` and `--memory-hash`, concatenating pages before parsing the JSON or drawing conclusions. Changed memory invalidates continuation. Memory hits hash the source bytes without decoding/splitting its full text.

`--memory-dir KNOWN_NOTES` remains an inspection path for existing ordinary notes, not an invitation to migrate them. It returns bounded contents/inventory for analyst assessment, without automatic freshness claims. Unknown, oversized, linked or unreadable entries remain incomplete, not a miss. Inspect selected files with their existing tools; do not create a competing answer note. After assessing memory, obtain missing evidence with ordinary tools or `read-text` without memory flags.

`read-text` merges requested ranges and literal OR matches with adjacent context. `--max-chars` bounds the **whole serialized response including escaping, metadata and newline**; choose it to fit the calling tool's output budget, which this CLI cannot change. Whole source lines are never silently cut: use `next_after_line` as `--after-line` with identical selectors and `--source-hash`. An oversized single line or envelope produces a required-budget error. End of selected results is not evidence of corpus-wide absence.

Reading is always read-only. There is no emitted-range store: a CLI cannot know whether its stdout reached the model intact. Continue only after actually received lines; if the outer tool loses/truncates output, retry or resume after the last complete visible line with the same hash and selectors. Never advance solely because the producer generated output. Range merging removes overlap within a response; the caller controls cross-call continuation without a second state file.

`save-answer` takes a JSON object keyed by stable point IDs through `--points`, UTF-8 stdin (`--points -`), or an **existing** `--points-file`. Batch the affected points in one save; do not create an intermediate file or call once per sentence. Each point requires:

- `text`: answer-ready finding, table/mapping or scoped open result;
- `status`: explicit `confirmed`, `interpretation`, `unresolved` or `conflicted` (no default);
- `basis`: what establishes the finding, or why its meaning remains uncertain;
- `coverage`: applicability and checked scope, including pending continuation;
- `limits`: required for every unconfirmed point, optional otherwise;
- `cite`: optional physical line/range strings, e.g. `["20:60"]`;
- `quote`: optional exact substrings with physical ranges, e.g. `["20:21=original text"]`;
- `exact`: exact technical literals asserted in `text`; declare filenames, XML paths, units and other decisive exact values here. A confirmed literal must appear verbatim in a checked quote. Derived exact results needing a reproducible computation/structural check belong in the existing suitable owner; this helper does not execute arbitrary checks;
- `depends_on`: optional point IDs **within this scope**, only for real dependent conclusions, not shared citations. Missing/cyclic dependencies are rejected.

The helper checks the source snapshot, locator bounds and supplied quotes, not entailment, applicability or whether the analyst declared every exact assertion. `--reviewed ID ...` records the caller's actual review of new/changed confirmations; it is not an instruction to reread already adequate evidence. Unchanged confirmed points require neither review nor a write. An interpretation cannot become confirmed merely by re-save. Confirmed conclusions cannot depend on unconfirmed or stale points. Changing a premise marks unreviewed transitive dependents `unresolved` with `review_required`, preserving their text and limits as leads. To resolve them, supply updated points and their reviewed IDs in the same or a later batch. Unrelated points/scopes remain untouched. Cross-scope or external dependencies must be handled by their existing analyst/owner; the helper cannot discover undeclared relationships.

The helper atomically upserts affected points without a duplicate whole-answer body. It refuses foreign/incompatible formats (no implicit conversion of old answer-wide assessments), source/input collisions, linked artifacts and missing parent directories; reads/writes are capped at 1 MiB. Use the existing owner directly beyond that scope. Parent directories must be trusted and not concurrently replaced; this is a single-writer file helper, not a directory sandbox. Saved assessments are analyst assertions, not signed attestations; unknown or manually altered notes still need provenance assessment.

These commands automate mechanics, not the final chat response. Saving still precedes the agent's final message; eliminating that model roundtrip requires separately authorized runtime integration. No end-to-end token saving follows solely from these commands or their unit tests.

For a scoped no-hit result, save an `unresolved` point with the actual query/scope in coverage and the absence limitation in limits; no fabricated citation is required. Confirmed/interpretation points need a locator, quote or explicit dependency. A current open result can avoid repeating an exhausted query, but cannot become proof of absence.

A small Markdown/JSON note or compatible project store is a complete analytical owner when it meets the entrypoint's [answer-ready memory contract](../SKILL.md#freshness-memory-and-context-isolation). Facts/tables must retain all requested enumeration members, attributes and mappings with their qualifiers and citations, not substitute “see source” for established results. No fixed field names, receipt conversion, index, or extra reference load is required. Edit it normally and update affected entries rather than appending a transcript. Do not create a second note when an existing store already owns these findings.

For a simple note, retain the cited factual body without conversational text, with provenance and point-local assessments/limits. A compact labelled section or table suffices; do not reproduce the helper JSON schema or create an extra ledger. Old notes with only a global verification label are leads for uncertain points, not a reason to recheck clearly recorded applicable point-level evidence. This is one current analytical owner, not an archive of final messages. The structured task-receipt and Research schemas below still store selected findings; do not convert solely to persist an ordinary answer.

Non-helper searches retain compact query/scope, generation, outcome, selected locators and any coverage/continuation limits in the same owner. A scoped no-hit result is reusable search state, not proof of absence. For indexed search, pass the authorized `--receipts-db` so the helper checks and saves query receipts; do not copy those rows into an analytical note. Batch pending non-helper updates and save before completion/handoff, without a separate write turn after every query. A direct read with no search needs findings and locators, not a fabricated query receipt.

Read relevant analytical memory before issuing source searches or reopening passages, following the entrypoint's dependency gate. For a repeat, check question/scope, verification provenance and source generation. Reuse current supported findings without automatic rereading; retain known limits. Leave unchanged notes untouched: no session stamp, duplicate summary, or confirmation log. Unverified notes are leads, and changed/disputed facts or missing qualifiers require targeted verification. A hash match does not certify a conclusion. A current unresolved result can avoid repeating an exhausted query but cannot become a positive or negative answer merely because it was saved.

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
| `status` | Claim-level assessment: `confirmed`, `interpretation`, `unresolved`, or `conflicted`; separate from freshness and the act of checking a locator |
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
      "status": "confirmed",
      "claims": [{"text": "Atomic supported proposition", "status": "confirmed", "basis": "Checked the applicable source provision", "passage_ids": [12], "scope": "conditions or applicability"}]
    }
  }],
  "conflicts": [],
  "gaps": [],
  "next_mode": "direct"
}
```

For several corpora, optional `catalog.sqlite` is a routing layer within the first two levels: it points to isolated corpus indexes/receipt stores, maps overlapping logical projects to those corpora, and keeps composite locator-only receipts. It is not another evidence ledger. `research.sqlite` may bind to one corpus or a frozen concrete subset of one catalog and records each receipt link's store kind/path. Project IDs remain explanatory metadata; membership changes do not silently alter an existing investigation. Research evidence writes must validate that `corpus_id` belongs to the frozen investigation scope. Neither receipt level requires research state, and research promotes only selected verified findings rather than duplicating receipt contents.

A task receipt stores selected findings and compact locators, not full passages, logs or answer transcripts. `findings-save` accepts up to 50 facets and 50 claims each. Each claim requires `text` (up to 1,000 characters), `status`, `basis`, and `scope` (up to 500); nonconfirmed claims also require `limits`. Evidence IDs must belong to that facet. A facet-wide input status is not accepted: the aggregate is derived from its claims. Empty `claims: []` requires a reason and remains unresolved. Confirmation is the analyst's assessment, never proof from lexical matches. The final serialized task receipt must fit its 256 KiB reader limit; an oversized update fails before replacing the previous file. Ordinary scoped retrieval registers new locators; new evidence creates a review gap without silently changing existing claim assessments.

Reuse is question- and scope-aware. `facet_hash` includes the question text, stable ID, normalized query plan, requested versions/filters, and relevant kind/verification/group/selection options; query similarity alone cannot establish unchanged meaning. The corpus fingerprint must also match. A changed question with identical terms must not receive an old answer. A version mismatch, malformed finding, missing citation provenance, outside evidence ID, or changed corpus fails closed for verified reuse. A source-local fact may remain true after a corpus change, but earlier corpus-wide completeness does not. Recheck affected evidence and coverage before reusing that conclusion.

Upsert affected facets atomically rather than replacing the request family. Keep retained gaps and conflicts visible. An unchanged repeat reuses open findings without certifying them or automatically retrying an exhausted search. Larger budgets widen incomplete retrieval but do not discard an applicable confirmed answer or invalidate existing claim assessments. Refine the question/query to investigate further. Retrieval hits cannot clear an analyst's gap or conflict. Prune only under explicit cleanup authority, not as a side effect of a subset follow-up.

After a source-generation change, retained facets are stale; their historical assessments remain labelled, not current confirmations. Re-retrieval may retain one bounded `previous_finding` with provenance and explicit current/reusable flags for targeted review, not an accumulating history. Saving the replacement removes that snapshot. Source-change gaps are upserted, not appended repeatedly.

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

Indexed `search`/`get` responses expose `index_fingerprint`; carry it as `--expected-fingerprint` when continuing across calls. Passage IDs are content-bound, not sequential row numbers. `get --around` anchors only the initial call; an explicit `--start-char`, including zero, resumes without re-anchoring. Keep selectors and returned offsets. Search/get budgets include the serialized envelope, metadata and aliases; a locator too large to fit fails explicitly rather than losing identity. Schema continuation is described in [ingestion](ingestion.md#xsd-semantic-normalization).

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

On resume, `research-info --resume` returns bounded facets, evidence freshness, gaps/conflicts, receipt links, next action and live bindings. Read analytical findings before searching; a query receipt is not analysis. Prior-generation receipts remain noncurrent history. `receipts-sync` updates its binding. `research-sync` rebinds the investigation but clears confirmations whose source/hash/locator dependencies no longer match; it never certifies old findings. Evidence defaults to `unresolved`; reuse requires explicit `status: confirmed`, `verified: true`, and current dependencies. Editing a facet's question invalidates its evidence confirmation. Use `research-update` for investigation status, not a second state file. Incompatible database layouts fail closed; no migration is performed.

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
