# doc-research

`doc-research` supports evidence-grounded analysis of large documents and collections without repeatedly loading the corpus into model context. It provides scoped retrieval, optional evidence batching, verified-finding reuse, version-aware citations, conflict checks, and optional resumable research state.

Choose the smallest sufficient route. Direct scoped search/reading can answer a question without an index, JSON plan, or receipt, even in a large single source. Indexed `search`, `search-many`, `get`, structural `schema-query`, and the `evidence-pack` batch helper are normal alternatives when they help. Independent operations can be batched; dependent refinement follows the evidence.

Optimizations are required when their stated conditions apply: check and reuse current memory, batch independent work, expand insufficient context, save new search/analysis state on every route within write authority, and change an ineffective route. Implementations remain interchangeable. A working reader or note does not need replacement by a preferred tool, index, or database. New tools are acquired only for missing evidence capability or a concrete net benefit after setup; irrelevant tools are not installed or probed.

Use it for multi-document investigations, version comparisons, tenders, contracts, standards, policies, page-level evidence, or conflict/gap analysis. A short single source is usually better read directly.

## How it works

The agent selects a route and useful initial effort:

- **Route:** Direct, Retrieval, or Research determines the process and whether investigation state is useful.
- **Effort:** compact, balanced, or thorough determines retrieval breadth and verification search. Balanced is the default.
- **Executor:** interpretation stays in the current agent by default. An optional cost estimate can inform authorized delegation; no routing ceremony is required before retrieval.

The storage model is deliberately separated:

```text
authorized sources -> reusable index -> query receipts
                                      -> task receipt
                                      -> optional investigation research state
multiple isolated corpora -> optional catalog routing
```

The index is rebuildable retrieval data, including a structural node graph for standalone or Markdown-embedded XSD. Raw schema code stays in the original; model-facing FTS contains compact facts with source lines. Query receipts remember searches and continuation. Choose one owner for analytical findings, conflicts, and progress: a task receipt, Research state, or compatible existing store. Helpers maintain locators and retrieval memory; analysts verify meaning and completeness. Exact schemas and lifecycle rules live in [evidence schema](references/evidence-schema.md).

Catalog registration can derive opaque stable project/corpus IDs from canonical context while keeping a separate editable human-readable label; source-routing rules own the exact identity contract.

Every route checks relevant known memory before retrieval and saves new search/analysis state before completion when writing is authorized, even without an announced repeat. A small Markdown/JSON note can hold compact non-helper search outcomes and supported findings with scope, source generation, locators, conditions, and unresolved limits; no index or special schema is required. Reuse an existing owner, update only changed state, and report its location; unchanged notes need no rewrite or session stamp. If storage is unauthorized, unavailable, or fails, return a compact resume block and disclose that it was not persisted. The canonical contract is in [SKILL.md](SKILL.md#freshness-memory-and-context-isolation).

Generated databases belong in an authorized derived-data location, separate from originals and other inputs. Use task-local temporary paths when persistence is not authorized; a trusted project/runtime cache requires established write authority, not merely a writable path. Existing compatible tools/stores need no migration solely for this skill. A connector can supply verifiable evidence without a cache; reusable caching requires reliable identity, generation, scope, and locators.

For interoperability, the skill accepts a bounded request describing the question, facets,
authorized sources/versions, known locators, intended output, and constraints. It returns conclusions
by facet with source locators, versions, conflicts, gaps, searched scope, coverage limits, and
verification limitations. The caller remains responsible for any downstream decision or acceptance.

## Quick start

For a direct question, search/read the authorized source and retain its version and line/page locations. For indexed work, ordinary scoped retrieval is available without a question plan:

```bash
scripts/corpus index CORPUS_PATH --db index.sqlite
scripts/corpus search index.sqlite "CargoMass" --mode literal
scripts/corpus get index.sqlite PASSAGE_ID --around "CargoMass"
scripts/corpus schema-query index.sqlite CargoMass --kind element
```

Use returned IDs and continuation, and inspect relevant parents/definitions before making a requiredness claim. For several independent questions, an optional bounded plan batches the initial work:

```json
{
  "questions": [
    {"id": "owner", "question": "Who signs it?", "kind": "lookup", "verification": "exact"},
    {"id": "types", "question": "Which message types exist?", "kind": "enumeration", "group_by": "section", "max_items": 12, "verification": "control"},
    {"id": "mass", "question": "What constrains CargoMass?", "kind": "schema", "verification": "exact", "queries": [{"query": "CargoMass", "role": "support", "mode": "literal"}]}
  ]
}
```

```bash
scripts/corpus evidence-pack CORPUS_PATH questions.json --db index.sqlite --task-receipt task-receipt.json
scripts/corpus findings-save task-receipt.json findings.json
```

The pack combines index/receipt reuse, missing searches, bounded enumeration continuation, structural XSD lookup, deduplication, passage reopen, and source locations. It returns inline evidence by default. Optional `--execution-route auto --pack-output PATH` adds a route estimate when measured worker costs and context justify it; unknown worker costs must not be treated as zero. An interpretation-only worker returns gaps for the coordinator to resolve; it does not silently broaden its assignment.

When the task receipt owns findings, `findings-save` records bounded atomic claims whose evidence belongs to the facet. Scoped helper retrieval registers new locators without manual state editing. An unresolved finding may have no claims. An exact unchanged question/scope/version repeat returns saved findings with their status and locators without unnecessary searches or passage reopen. Unresolved findings and conflicts stay visible, not silently promoted to verified or discarded. Upserts preserve unrequested facets and conflicts. Changed question meaning or corpus freshness invalidates affected reuse, even if lexical queries remain identical.

The question file accepts up to 50 facets and 20 explicit queries per facet; use smaller batches when sufficient. `lookup` selects a small fact set; `enumeration` uses `group_by` and `max_items` for candidates; `schema` adds structural XSD facts. `verification: exact` calls for authoritative support. `verification: control` calls for checking contrary evidence and exceptions for universal, negative, or high-risk claims. Query roles guide retrieval; they are not a mechanical save gate or proof of answer coverage. Check relevant variants, parent conditions, and exceptions; a bounded candidate list is not necessarily a complete list of business cases.

Effort profiles set soft starting budgets. Keep hard per-call resource limits, but use continuation, new queries, or deeper scoped reading when needed. Preserve the full relevant condition, table unit, or schema parent relationship; no fixed round count determines completion.

Memory and context isolation are independent. Normal work reuses current indexes, query receipts, and verified findings. For a fresh-storage test, use new task-local database/receipt paths. For an isolated-context test, use a no-history worker. Use both only for a full cold benchmark; there is no durable no-memory mode.

The POSIX launcher and `scripts\corpus.cmd` select a compatible Python but do not themselves install it. A sufficient existing route remains usable if Python is absent. Acquire Python when the helper's benefit justifies setup, within authority. Run `scripts/corpus doctor --write-dir EXISTING_DIR` after a relevant failure, on request, or for a concrete environment risk; it is not a mandatory first-run step. Use `--read-only-receipts` when the task may read but not update durable query memory.

`evidence-pack` creates `INDEX_STEM.receipts.sqlite` by default; use `--receipts-db` to select another authorized path. A corpus may be a normalized Markdown, text, page-aware JSONL, or XSD file, or a directory. Complete fenced XSD inside Markdown is normalized automatically. `index`, `search`, `get`, `schema-query`, receipt, catalog, and Research commands are ordinary tools for their respective needs. Read command-specific help when an option is unclear; no named-gap proof is required.

## Read the relevant guide

- [Ingestion](references/ingestion.md): conversion, OCR, Docling, ZIP extraction, normalized inputs, indexing, and runtime checks.
- [Source routing](references/source-routing.md): multiple corpora, projects, attachments, URLs, wikis, connectors, catalogs, and adapter contracts.
- [Project integration](references/project-integration.md): classification and safe use, migration, or cleanup of existing research artifacts and rules.
- [Evidence schema](references/evidence-schema.md): the canonical memory model, durable research fields, receipts, resume, and synthesis.
- [Retrieval effort](references/retrieval-effort.md): numeric compact, balanced, and thorough budgets.
- [Orchestration](references/orchestration.md): deterministic cost routing, compact worker packets, measured break-even, fallbacks, and targeted escalation.
- [Quality gates](references/quality-gates.md): checks for high-stakes or conflict-heavy work.

`SKILL.md` contains only shared routing, invariants, and the compact workflow. Each reference owns its branch details; this README is a non-normative human overview.

## Package contents

- `SKILL.md` — agent entrypoint;
- `references/` — conditional guidance;
- `scripts/corpus` and `scripts/corpus.cmd` — platform launchers;
- `scripts/corpus.py` — stable thin CLI entrypoint;
- `scripts/doc_research/` — standard-library implementation split by domain;
- `tests/` — development test suites.

## Developer benchmark protocol

Pin the actual `SKILL.md`, launcher, and helper implementation paths used by every runner. Record the commit plus a content digest of the loaded files and dirty changes, model and reasoning effort, source hashes/versions, prompt, storage paths/mode, and model-context mode. Verify the pinned digest before each run; stop on a mismatch. An installed plugin and a modified checkout are different test subjects even when their skill names match.

Compare before/after on the same model, effort, source snapshot, question, and quality rubric. Give both sides equal access, tool and persistence authority. Test cold storage with fresh context, exact repeat in another no-history agent, subset follow-up followed by the full request, a changed question with the same terms, and a changed source when relevant to the change. To test default persistence, do not announce a future repeat or instruct the agent to save a note; provide only task sources and an authorized artifact location. A repeat is warm only if the first run actually saved reusable state; do not seed it manually or count a missed save as proof that warm reuse works. Record storage coldness separately from model-context isolation. Use isolated temporary derived state; do not add a runtime no-memory mode or alter originals.

Measure the completed task: total input/cache/output tokens, all model/tool calls and retries, elapsed time, answer correctness/completeness, preserved conditions/exceptions, and locator validity. Include instruction loading, later retrieval, workers, and final synthesis. First-pack bytes or helper runtime cannot establish whole-task savings. Confirm unchanged warm reuse and subset preservation alongside fresh-source invalidation. Run cheap regression fixtures first; repeat paired model runs when results are close or unstable. Report observed results with their limits, never a general model-performance or token-saving promise from one run.

## Installation

Install into the current project with the open-source [`skills`](https://github.com/vercel-labs/skills) CLI:

```bash
npx skills add kovaa-dev/skills --skill doc-research
```

For a global installation, add `--global`. See the repository [installation guide](../../README.md#install-with-npx-skills) for agent selection, reproducible commit-pinned sources, telemetry, and plugin installation.

## Language and version

The agent-facing instructions are written in English. This skill is included in version `v0.4.3`. <!-- x-release-please-version -->
