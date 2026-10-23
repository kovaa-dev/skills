# Mixed-source routing

Use this reference only when the selected evidence spans several directories or projects, archives, chat attachments, URLs, wikis, connected services, or more than one authorization boundary.

## Logical union, physical isolation

Keep independently permissioned/versioned corpora identifiable and isolated. Several sources do not by themselves require indexes or a catalog: a few scoped reads may suffice. When reusable cross-corpus routing is selected, use separate indexes/receipt stores and one logical `catalog.sqlite`. It stores routing metadata, project membership, and composite locator-only receipts, not passages, findings, or credentials. One corpus may belong to several projects without duplicating its index. One `research.sqlite` may bind to a frozen concrete subset for an investigation that spans those corpora.

```text
local/normalized corpus A -> index A + receipts A --+
local/normalized corpus B -> index B + receipts B ----> catalog -> optional research
remote source descriptor ----------------------------+
```

This separation makes source changes, retention, access review, and removal local to one corpus. Generated federated locators use `CORPUS_ID@INDEX_FINGERPRINT=PASSAGE_ID`, preventing collisions and rejecting changed generations.

## Resolve projects without creating noise

A project is a retrieval view, not a source container, permission boundary, or second evidence store. Its only durable data is a stable ID, one or more stable anchors, and many-to-many links to registered corpora. Shared corpora are searched once after project unions are deduplicated. Reuse the catalog already bound by active research or configured by the current workspace. If none is known, do not scan the machine for databases: continue with an explicitly selected corpus, or create a catalog only in an authorized durable derived-data location and report that path.

Keep identity separate from presentation. When the positional ID is omitted, `catalog-put` derives `corpus-<hash>` from the access boundary, adapter, and canonical source locator; `catalog-project-put` and `catalog-project-resolve --create` derive `project-<hash>` from the access boundary, anchor kind, and normalized anchor. They independently infer a short label from the directory or final locator component. `--label` overrides that presentation without changing identity, and later calls without `--label` preserve the stored label. Equal labels never merge records. Source generations, query text, and generated summaries never enter an ID. Use an explicit ID when identity must survive a source move or locator change that the catalog cannot recognize as the same source.

Routing precedence is: an active research binding; an explicit project/corpus selection; one unambiguous stable context-anchor match; then a projectless explicitly bounded corpus search. Never select a project by recency alone. A term associated with another project may justify investigating its relevance, but does not authorize a broader source boundary.

Resolve an unnamed project from an authorized stable anchor:

```bash
scripts/corpus catalog-project-resolve catalog.sqlite --anchor-kind filesystem --anchor CURRENT_WORKSPACE
scripts/corpus catalog-search catalog.sqlite "search terms" --project-id RESOLVED_PROJECT
```

Filesystem resolution uses the most specific containing anchor and returns less-specific related projects. Connector and manual anchors match exactly. If equally specific projects match, keep the result ambiguous and select explicitly; do not merge them or search all of them by default. A named facet may intentionally search several `--project-id` values; their corpus union is deduplicated before retrieval.

When durable setup is authorized, create-or-attach by stable anchor and an existing corpus:

```bash
scripts/corpus catalog-project-resolve catalog.sqlite --anchor-kind filesystem --anchor CURRENT_WORKSPACE --access-boundary workspace-a --create --corpus-id CORPUS_ID
```

This operation is idempotent. It attaches to one unambiguous containing project or creates a deterministic `project-*` ID and a separate inferred label. It refuses empty projects and ambiguous matches. Never auto-create from a natural-language query, topic similarity, filename, transient chat ID, or generated summary. Without a stable anchor or durable-write authority, keep the task projectless and search explicitly selected corpus IDs or one access boundary; do not persist a synthetic “misc” or “inbox” project.

Use `catalog-project-put` for an explicit project or additional anchor. Repeated `--corpus-id` values add memberships; `--replace-corpora` deliberately makes that list authoritative without deleting corpus databases. `catalog-put --project-id` can attach a newly registered corpus to existing projects. Project and member corpora must share one access boundary; the project ID never grants access.

## Classify each source before routing

| Source | Default route | Durable reuse |
| --- | --- | --- |
| Existing local `.md`, `.txt`, or normalized `.jsonl` | Scoped search/reading; corpus index when reuse or complexity justifies it | Keep any reusable index and receipts beside authorized derived state |
| ZIP archive | Explicit safe extraction, then classify/index supported members | Keep the extraction manifest and archive hash; never recurse automatically |
| PDF, office file, scan, table | Use the conditional ingestion path, then index normalized output | Preserve the original locator and extraction lineage |
| Chat attachment | Use task-local access for one-off work | Copy to an authorized persistent corpus only when durable writes and retention are explicitly allowed |
| Wiki, drive, repository, or internal service | Prefer its authorized connector | For repeatable common search, export/materialize only the needed authorized records into a normalized corpus; otherwise keep it connector-local |
| Public URL | Fetch directly when allowed and current access is required | Persist a versioned export only when reuse justifies it and the user authorized storage |

A catalog entry with adapter `external` is a coverage descriptor, not an executable connector. The helper reports it as unsearched unless the caller explicitly accepts a partial local search. Never imply that a remote source was searched merely because it was registered. To make it participate in repeatable helper search, materialize an authorized, versioned export and register the resulting local index.

## First catalog-backed run

Only when catalog-backed retrieval is selected, reuse or create each required local/materialized index and receipt store and register it once. Simple persistent notes do not require this setup:

```bash
scripts/corpus index CORPUS_A --db corpus-a.index.sqlite
scripts/corpus receipts-init corpus-a.receipts.sqlite --corpus CORPUS_A --index corpus-a.index.sqlite
scripts/corpus catalog-init catalog.sqlite
scripts/corpus catalog-put catalog.sqlite --adapter local-index --access-boundary workspace-a --index corpus-a.index.sqlite --receipts-db corpus-a.receipts.sqlite
```

The registration response contains the stable `corpus_id` and inferred `label`; reuse the ID in project membership and locators. Pass a positional ID only to preserve an established external identity. Pass `--label` only when the inferred display name is unclear.

Register a remote source only to make coverage and freshness explicit:

```bash
scripts/corpus catalog-put catalog.sqlite --adapter external --access-boundary workspace-a --locator wiki://space/page --generation VERSION
```

`access-boundary` is a stable permission or tenant label, not a credential. If a catalog contains several boundaries, `catalog-search` requires explicit `--project-id`, `--access-boundary`, or `--corpus-id` selection. A single search is capped at 16 corpora; partition larger collections by a meaningful boundary or named facet rather than paying an unbounded fan-out cost.

Treat `access-boundary` as permission scope, not project identity. An explicit `--project-id` is also a valid bounded selection because every membership is checked against that project's boundary. A search may select up to eight projects and sixteen deduplicated corpora.

## Later search and continuation

```bash
scripts/corpus catalog-info catalog.sqlite --live
scripts/corpus catalog-search catalog.sqlite "search terms" --access-boundary workspace-a --limit 8
scripts/corpus catalog-get catalog.sqlite CORPUS_A_ID@FINGERPRINT_A=PASSAGE_A CORPUS_B_ID@FINGERPRINT_B=PASSAGE_B
```

Skip `catalog-info --live` on routine searches when no source changed. `catalog-search` validates bindings and rehydrates receipt locators from the current index. Without write authority, use `--read-only`; misses are not persisted. For continuation, pass `next_continuation` as `--continuation` with the same query/selectors. It retains member positions, dedupe state and generation so later pages do not replay the prefix. A bounded page can contain no new unique results while still having a continuation; its numeric offset may be unchanged. Offset-only continuation needs a current saved checkpoint and otherwise requests restart. `coverage_complete: false` and `unsearched_corpora` describe a source gap, not pagination. `--allow-partial` never establishes corpus-wide absence.

For `catalog-get`, resume with returned `--offset` and `--start-char` positions. A deferred item is not missing, and a truncated passage is not complete evidence. Preserve the same selected IDs/order and source generation when continuing; changed generations require fresh locators.

Catalog output budgets cover the whole JSON response. Writable cursors are short references to the existing receipt chain; dedupe keys are stored once, not copied into every output. Read-only cursors carry bounded inline state and explicitly fail if that state cannot fit the requested output budget. Restoring deep dedupe state reads prior receipts, not earlier corpus matches. Omit a custom `--receipt-id` after the first page. A changed receipt revision invalidates its old cursor instead of silently retargeting it.

After a local source changes, update its index, sync its receipt store, and run `catalog-sync`. Prior-generation corpus and composite receipts remain history but are not current. Registering, disabling, or changing any selected corpus also changes the catalog fingerprint.

## Catalog-bound research

Create research state only for a long or consequential investigation. The facet must exist before linking a search:

```bash
scripts/corpus research-init research.sqlite --scope "question" --catalog catalog.sqlite --project-id review-a --project-id review-b
scripts/corpus research-put research.sqlite facet F1 --question "answerable facet"
scripts/corpus catalog-search catalog.sqlite "search terms" --corpus-id CORPUS_A_ID --corpus-id CORPUS_B_ID --research-db research.sqlite --facet-id F1
scripts/corpus research-info research.sqlite --resume
```

Catalog research records the originating project IDs for explanation but freezes the concrete selected corpus IDs at initialization. Later membership changes neither broaden nor shrink an investigation silently. Resume and sync inspect only that frozen set; start a newly scoped investigation when newly attached corpora must enter coverage. This avoids rescanning unrelated projects and prevents later searches from linking an out-of-scope receipt. Research stores selected findings and links to either corpus receipts or catalog receipts; it does not absorb indexes, query snippets, or full source copies. Every catalog-bound evidence row requires `corpus_id`, so its passage can be reopened without guessing which physical index owns the ID. `research-sync --catalog catalog.sqlite` accepts changed generations within the frozen scope after source changes have been reviewed.

## Freshness, deduplication, and token cost across projects

- Store source content only in its corpus index. Project views, catalog receipts, and research rows reference lower levels instead of copying chunks or summaries.
- Re-register a changed source under the same stable corpus identity and update its generation; do not create a new corpus for every export or session. A transformation remains lineage under the original source unless it has an independent permission/version lifecycle.
- When the same source appears in several project-specific databases, prefer one shared corpus only if identity, permissions, retention, and version lifecycle are truly the same. Otherwise keep the physical copies separate and preserve aliases and alternate locators when exact results deduplicate; warm cached results must retain those locations too.
- Project membership changes are explicit metadata updates. Use exact anchors and corpus IDs; semantic similarity can suggest a candidate but cannot create or merge membership.
- Equivalent searches reuse per-corpus and composite receipts. Shared corpora in overlapping projects are expanded once, and exact returned passages are deduplicated before model context.
- Route first with relevant local metadata, then search the smallest resolved project or explicit corpus set. Refine within the authorized scope as evidence requires; expanding to related projects still requires source authority. Do not load the entire inventory, live-check every corpus, or fan out to all projects before each query.
- A receipt is current only for the selected corpus generations. Research keeps only selected evidence, conflicts, gaps, and locators; query variants, snippets, and project summaries do not become research memory.
- Do not delete by age or rely on lifecycle labels to define truth. Stale generations are excluded by fingerprints, while deliberate `--replace-corpora` changes the active project view. Remove derived databases only under explicit retention/cleanup authority.

## External adapter contract

For an answer, an authorized project tool or connector must provide identifiable source material and enough location/version context to verify decisive evidence. Missing cache machinery does not make otherwise verifiable evidence unusable. To reuse cached results or negative-search coverage, additionally require:

- a stable corpus/source identity and explicit authorization boundary;
- a source generation, revision, ETag, hash, or timestamp with documented semantics that changes whenever searchable content, filtering metadata, or locator resolution can materially change;
- a deterministic receipt-equivalence key covering the normalized query, search mode, filters, selected source set, authorization boundary, adapter/schema version, and source generation;
- bounded results plus a continuation cursor or a clear terminal outcome;
- a stable locator containing enough record, version/generation, and location identity to reopen the same item in the same access context or fail closed;
- enough version and location metadata to verify decisive evidence against the original.

A **verified locator** has been reopened successfully and matched to the intended record, version/generation, location, and authorization context. Two remote searches are **receipt-equivalent** only when every field in the equivalence key matches; a continuation cursor extends that receipt rather than defining a different query. A remote receipt is **current** only while the adapter confirms the same generation and equivalence semantics; elapsed time alone neither proves nor disproves freshness, and a timestamp counts only when the source documents it as the generation token. Missing generation/equivalence guarantees prohibit cached reuse and negative-search proof; missing verifiable source identity or locators limits output to leads until checked against originals.

Probe only the connector selected for the active sources. Use an existing authorized connection when it is the sufficient low-cost route; an equivalent current export or another capable reader need not be replaced. Acquire a missing connector only when needed for correctness or a concrete net gain after setup: if the runtime and existing authority permit installation, install, verify source/locator behavior, and use it; otherwise request authorization with the exact connector, sources, scopes, transfer implications, verification, and fallback limitation. Connecting an account, granting new scopes, accepting terms, or uploading data requires explicit authority. Do not silently lower evidence quality, block unaffected work for a preferred product, or repeat an unchanged proposal.

## ZIP safety

For an explicitly selected ZIP, follow [ZIP handoff](ingestion.md#zip-handoff). Register or index only reviewed, supported, authorized members; nested archives are not opened automatically.
