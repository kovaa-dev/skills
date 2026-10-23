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

Every route reads relevant known memory **before searching source content**; listing the artifact folder does not count. A current complete result can answer an unchanged request without search, source reopening, or another write. Partial memory narrows retrieval to missing facts. New findings are saved within write authority, even without an announced repeat, as answer-ready facts/tables with scope, source generation, citations and limits—not just pointers to omitted answers. The canonical [read-before-search](SKILL.md#first-action-read-memory-then-decide-whether-to-search) and [persistence](SKILL.md#freshness-memory-and-context-isolation) contracts also cover unavailable storage and unknown provenance.

On a cold miss, the agent uses the ordinary search/read best suited to the questions; a section map is optional, not another mandatory phase. A conditional tool call can check memory and start retrieval only if it is absent. Reads retain complete relevant units within the combined outer-tool budget and continue omitted ranges after truncation. A simple note saves the same cited factual answer with provenance, not a second expanded report. Existing adequate evidence satisfies verification without a compulsory second representation or reread. These rules target avoidable work; instruction loading and authorized persistence still have a cost, so savings require whole-task measurement.

Generated databases belong in an authorized derived-data location, separate from originals and other inputs. Use task-local temporary paths when persistence is not authorized; a trusted project/runtime cache requires established write authority, not merely a writable path. Existing compatible tools/stores need no migration solely for this skill. A connector can supply verifiable evidence without a cache; reusable caching requires reliable identity, generation, scope, and locators.

For interoperability, the skill accepts a bounded request describing the question, facets,
authorized sources/versions, known locators, intended output, and constraints. It returns conclusions
by facet with source locators, versions, conflicts, gaps, searched scope, coverage limits, and
verification limitations. The caller remains responsible for any downstream decision or acceptance.

## Quick start

After reading any relevant analytical memory, search only missing evidence. For a direct question, use the authorized source and retain its version and line/page locations.

For local text, `read-text` combines memory lookup, current source hashing and scoped retrieval; `save-answer` batches prepared answer points with separate assessments and evidence. Current confirmed points need no repeated source check; interpretations and open questions retain their qualifications. Corrections replace points and invalidate explicitly dependent conclusions, not the whole answer. No index is required. Unknown/rephrased scopes return candidate findings before a new search. Reading is read-only, with explicit continuation after actually received lines; it never marks generated output as read. See [commands and limits](references/evidence-schema.md#lightweight-memory-and-existing-work). Ordinary tools and existing memory owners remain valid; no chat hooks are installed and saving does not capture the final response automatically.

For indexed work with authorized storage, ordinary scoped retrieval is available without a question plan:

```bash
scripts/corpus index CORPUS_PATH --db index.sqlite
scripts/corpus search index.sqlite "CargoMass" --mode literal --receipts-db receipts.sqlite
scripts/corpus get index.sqlite PASSAGE_ID --around "CargoMass"
scripts/corpus schema-query index.sqlite CargoMass --kind element
```

Use returned IDs and generation-bound continuation, and inspect relevant parents/definitions before making a requiredness claim. Long schema records continue within the record without losing the tail; search/get limits include JSON metadata, not just passage text. For several independent questions, an optional bounded plan batches the initial work:

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

When the task receipt owns findings, `findings-save` records claim-level assessments, basis, scope and limits—not one verification flag over a mixed answer. Scoped retrieval registers locators without manual state editing. An unchanged repeat reuses current findings; merely enlarging a search budget does not invalidate confirmation. Open findings remain visible. Changed sources invalidate affected reuse, while old findings remain leads for targeted rechecking. `research-sync` cannot turn stale evidence into current confirmation. See the canonical [memory contract](references/evidence-schema.md) for formats and limits.

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
