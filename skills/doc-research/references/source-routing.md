# Mixed-source routing

Use this reference only when the selected evidence spans several directories or projects, archives, chat attachments, URLs, wikis, connected services, or more than one authorization boundary.

## Logical union, physical isolation

Do not build one opaque mega-index. Keep one local index and receipt store per independently versioned or permissioned corpus, then register them in one logical `catalog.sqlite`. The catalog stores routing metadata, logical project membership, and composite locator-only receipts; it does not copy passages, findings, or credentials. One corpus may belong to several overlapping projects without duplicating its index. One `research.sqlite` may bind to a frozen concrete subset of that catalog when a single investigation intentionally spans its corpora.

```text
local/normalized corpus A -> index A + receipts A --+
local/normalized corpus B -> index B + receipts B ----> catalog -> optional research
remote source descriptor ----------------------------+
```

This separation makes source changes, retention, access review, and removal local to one corpus. It also prevents identical filenames or passage IDs from colliding: federated locators use `CORPUS_ID=PASSAGE_ID`.

## Resolve projects without creating noise

A project is a retrieval view, not a source container, permission boundary, or second evidence store. Its only durable data is a stable ID, one or more stable anchors, and many-to-many links to registered corpora. Shared corpora are searched once after project unions are deduplicated. Reuse the catalog already bound by active research or configured by the current workspace. If none is known, do not scan the machine for databases: continue with an explicitly selected corpus, or create a catalog only in an authorized durable derived-data location and report that path.

Routing precedence is: an active research binding; an explicit project/corpus selection; one unambiguous stable context-anchor match; then a projectless explicitly bounded corpus search. Never select a project by recency alone. A term associated with another project is a reason to propose or perform a named-gap expansion, not permission to broaden the initial search.

Resolve an unnamed project from an authorized stable anchor:

```bash
scripts/corpus catalog-project-resolve catalog.sqlite --anchor-kind filesystem --anchor CURRENT_WORKSPACE
scripts/corpus catalog-search catalog.sqlite "search terms" --project-id RESOLVED_PROJECT
```

Filesystem resolution uses the most specific containing anchor and returns less-specific related projects. Connector and manual anchors match exactly. If equally specific projects match, keep the result ambiguous and select explicitly; do not merge them or search all of them by default. A named facet may intentionally search several `--project-id` values; their corpus union is deduplicated before retrieval.

When durable setup is authorized, create-or-attach by stable anchor and an existing corpus:

```bash
scripts/corpus catalog-project-resolve catalog.sqlite --anchor-kind filesystem --anchor CURRENT_WORKSPACE --access-boundary workspace-a --create --corpus-id project-a
```

This operation is idempotent. It attaches to one unambiguous containing project or creates a deterministic `auto-*` project. It refuses empty projects and ambiguous matches. Never auto-create from a natural-language query, topic similarity, filename, transient chat ID, or generated summary. Without a stable anchor or durable-write authority, keep the task projectless and search explicitly selected corpus IDs or one access boundary; do not persist a synthetic “misc” or “inbox” project.

Use `catalog-project-put` for an explicit project or additional anchor. Repeated `--corpus-id` values add memberships; `--replace-corpora` deliberately makes that list authoritative without deleting corpus databases. `catalog-put --project-id` can attach a newly registered corpus to existing projects. Project and member corpora must share one access boundary; the project ID never grants access.

## Classify each source before routing

| Source | Default route | Durable reuse |
| --- | --- | --- |
| Existing local `.md`, `.txt`, or normalized `.jsonl` | Corpus index | Keep its index and receipt store beside authorized derived state |
| ZIP archive | Explicit safe extraction, then classify/index supported members | Keep the extraction manifest and archive hash; never recurse automatically |
| PDF, office file, scan, table | Use the conditional ingestion path, then index normalized output | Preserve the original locator and extraction lineage |
| Chat attachment | Use task-local access for one-off work | Copy to an authorized persistent corpus only when durable writes and retention are explicitly allowed |
| Wiki, drive, repository, or internal service | Prefer its authorized connector | For repeatable common search, export/materialize only the needed authorized records into a normalized corpus; otherwise keep it connector-local |
| Public URL | Fetch directly when allowed and current access is required | Persist a versioned export only when reuse justifies it and the user authorized storage |

A catalog entry with adapter `external` is a coverage descriptor, not an executable connector. The helper reports it as unsearched unless the caller explicitly accepts a partial local search. Never imply that a remote source was searched merely because it was registered. To make it participate in repeatable helper search, materialize an authorized, versioned export and register the resulting local index.

## First durable run

For each local or materialized corpus, create its own index and receipt store. Then register it once:

```bash
scripts/corpus index CORPUS_A --db project-a.index.sqlite
scripts/corpus receipts-init project-a.receipts.sqlite --corpus CORPUS_A --index project-a.index.sqlite
scripts/corpus catalog-init catalog.sqlite
scripts/corpus catalog-put catalog.sqlite project-a --adapter local-index --access-boundary workspace-a --index project-a.index.sqlite --receipts-db project-a.receipts.sqlite
```

Register a remote source only to make coverage and freshness explicit:

```bash
scripts/corpus catalog-put catalog.sqlite wiki-a --adapter external --access-boundary workspace-a --locator wiki://space/page --generation VERSION
```

`access-boundary` is a stable permission or tenant label, not a credential. If a catalog contains several boundaries, `catalog-search` requires explicit `--project-id`, `--access-boundary`, or `--corpus-id` selection. A single search is capped at 16 corpora; partition larger collections by a meaningful boundary or named facet rather than paying an unbounded fan-out cost.

Treat `access-boundary` as permission scope, not project identity. An explicit `--project-id` is also a valid bounded selection because every membership is checked against that project's boundary. A search may select up to eight projects and sixteen deduplicated corpora.

## Later search and continuation

```bash
scripts/corpus catalog-info catalog.sqlite --live
scripts/corpus catalog-search catalog.sqlite "search terms" --access-boundary workspace-a --limit 8
scripts/corpus catalog-get catalog.sqlite project-a=12 project-b=7
```

Skip `catalog-info --live` on routine searches when no source changed; `catalog-search` validates selected local bindings and checks its deterministic composite receipt. A hit returns locators without passage text. Without durable-write authority, add `--read-only`: current catalog/member receipts may be reused, but misses are not persisted and research state cannot be linked. Continue the same query only when `next_offset` is returned. `has_more` means another local page is available; `coverage_complete: false` and `unsearched_corpora` describe an external or unavailable-source gap, not a continuation. Use `--allow-partial` only when that gap is acceptable for the current claim; an incomplete search cannot support a corpus-wide absence claim.

After a local source changes, update its index, sync its receipt store, and run `catalog-sync`. Prior-generation corpus and composite receipts remain history but are not current. Registering, disabling, or changing any selected corpus also changes the catalog fingerprint.

## Catalog-bound research

Create research state only for a long or consequential investigation. The facet must exist before linking a search:

```bash
scripts/corpus research-init research.sqlite --scope "question" --catalog catalog.sqlite --project-id review-a --project-id review-b
scripts/corpus research-put research.sqlite facet F1 --question "answerable facet"
scripts/corpus catalog-search catalog.sqlite "search terms" --corpus-id project-a --corpus-id project-b --research-db research.sqlite --facet-id F1
scripts/corpus research-info research.sqlite --resume
```

Catalog research records the originating project IDs for explanation but freezes the concrete selected corpus IDs at initialization. Later membership changes neither broaden nor shrink an investigation silently. Resume and sync inspect only that frozen set; start a newly scoped investigation when newly attached corpora must enter coverage. This avoids rescanning unrelated projects and prevents later searches from linking an out-of-scope receipt. Research stores selected findings and links to either corpus receipts or catalog receipts; it does not absorb indexes, query snippets, or full source copies. Every catalog-bound evidence row requires `corpus_id`, so its passage can be reopened without guessing which physical index owns the ID. `research-sync --catalog catalog.sqlite` accepts changed generations within the frozen scope after source changes have been reviewed.

## Freshness, deduplication, and token cost across projects

- Store source content only in its corpus index. Project views, catalog receipts, and research rows reference lower levels instead of copying chunks or summaries.
- Re-register a changed source under the same stable corpus identity and update its generation; do not create a new corpus for every export or session. A transformation remains lineage under the original source unless it has an independent permission/version lifecycle.
- When the same source appears in several project-specific databases, prefer one shared corpus only if identity, permissions, retention, and version lifecycle are truly the same. Otherwise keep the physical copies separate and preserve alternate locators when exact results deduplicate.
- Project membership changes are explicit metadata updates. Use exact anchors and corpus IDs; semantic similarity can suggest a candidate but cannot create or merge membership.
- Equivalent searches reuse per-corpus and composite receipts. Shared corpora in overlapping projects are expanded once, and exact returned passages are deduplicated before model context.
- Route first with local SQLite metadata, then search the smallest resolved project or explicit corpus set. Expand to related projects only for a named gap. Do not load the project inventory, live-check every corpus, or fan out to all projects before each query.
- A receipt is current only for the selected corpus generations. Research keeps only selected evidence, conflicts, gaps, and locators; query variants, snippets, and project summaries do not become research memory.
- Do not delete by age or rely on lifecycle labels to define truth. Stale generations are excluded by fingerprints, while deliberate `--replace-corpora` changes the active project view. Remove derived databases only under explicit retention/cleanup authority.

## External adapter contract

Use an existing project tool or MCP/connector as an adapter only if it can provide:

- a stable corpus/source identity and explicit authorization boundary;
- a source generation, revision, ETag, hash, or timestamp with documented semantics that changes whenever searchable content, filtering metadata, or locator resolution can materially change;
- a deterministic receipt-equivalence key covering the normalized query, search mode, filters, selected source set, authorization boundary, adapter/schema version, and source generation;
- bounded results plus a continuation cursor or a clear terminal outcome;
- a stable locator containing enough record, version/generation, and location identity to reopen the same item in the same access context or fail closed;
- enough version and location metadata to verify decisive evidence against the original.

A **verified locator** has been reopened successfully and matched to the intended record, version/generation, location, and authorization context. Two remote searches are **receipt-equivalent** only when every field in the equivalence key matches; a continuation cursor extends that receipt rather than defining a different query. A remote receipt is **current** only while the adapter confirms the same generation and equivalence semantics; elapsed time alone neither proves nor disproves freshness, and a timestamp counts only when the source documents it as the generation token. If the adapter cannot meet this contract, use its output as a lead, not durable evidence or reusable negative-search proof.

The skill cannot silently install, authorize, or configure an MCP server or connector. Probe only the selected capability. If it is missing and materially better than local export, make one proposal naming the connector, affected sources, expected gain, permissions/data scope, setup action, fallback, and limitation; proceed only after user authorization. Do not repeat that proposal in an unchanged environment.

## ZIP safety

For an explicitly selected ZIP, follow [ZIP handoff](ingestion.md#zip-handoff). Register or index only reviewed, supported, authorized members; nested archives are not opened automatically.
