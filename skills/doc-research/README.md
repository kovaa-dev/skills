# doc-research

`doc-research` supports evidence-grounded analysis of large documents and collections without repeatedly loading the corpus into model context. It provides cost-aware cold retrieval, bounded batched search, facet-level replay, verified-finding reuse, cross-session query reuse, version-aware citations, conflict checks, and optional resumable research state.

When the skill is invoked explicitly, its execution contract is binding. Retrieval/Research over normalized local sources uses the bundled SQLite helper or a named capability-equivalent adapter; serial raw-text search is not a valid substitute.

Conditional external tools are operational choices, not passive recommendations. The agent names the selected adapter and tool decision, uses an existing authorized capability, installs a missing dependency in an authorized isolated scope when it can do so safely, or asks for a concrete setup/connection with the exact action and fallback. Tools irrelevant to the selected source format are not installed or probed.

Use it for multi-document investigations, version comparisons, tenders, contracts, standards, policies, page-level evidence, or conflict/gap analysis. A short single source is usually better read directly.

## How it works

The agent selects two things:

- **Route:** Direct, Retrieval, or Research determines the process and whether investigation state is useful.
- **Effort:** compact, balanced, or thorough determines retrieval breadth and verification search. Balanced is the default.
- **Executor:** a deterministic router always runs first. It keeps bounded interpretation in the coordinator by default and uses a no-parent-history low-overhead worker only when a measured profile shows a material saving. Exact verified-finding hits use neither passages nor a worker.

The storage model is deliberately separated:

```text
authorized sources -> reusable index -> query receipts
                                      -> task receipt
                                      -> optional investigation research state
multiple isolated corpora -> optional catalog routing
```

The index is rebuildable retrieval data, including a persistent semantic node graph for standalone or Markdown-embedded XSD. Raw schema code stays in the original; model-facing FTS contains only compact facts with source lines. Query receipts remember completed searches by locator, the transient task receipt maps active facet hashes to verified locators and bounded atomic findings, and research state keeps only selected facets, evidence, conflicts, gaps, and the next action. Exact schemas and lifecycle rules live in [evidence schema](references/evidence-schema.md).

Catalog registration can derive opaque stable project/corpus IDs from canonical context while keeping a separate editable human-readable label; source-routing rules own the exact identity contract.

Generated databases belong in an authorized persistent derived-data location, not in the installed skill, a temporary directory, or among originals. A caller may select the path; otherwise an authorized project/runtime cache is used and reported. Existing compatible project stores or connectors can serve as adapters instead of creating parallel state.

For interoperability, the skill accepts a bounded request describing the question, facets,
authorized sources/versions, known locators, intended output, and constraints. It returns conclusions
by facet with source locators, versions, conflicts, gaps, searched scope, coverage limits, and
verification limitations. The caller remains responsible for any downstream decision or acceptance.

## Quick start

From the skill root, for an authorized normalized corpus:

```bash
scripts/corpus evidence-pack CORPUS_PATH questions.json --db index.sqlite --task-receipt task-receipt.json --execution-route auto --pack-output evidence-pack.json
scripts/corpus findings-save task-receipt.json findings.json --execution-route coordinator-direct
scripts/corpus findings-save task-receipt.json findings.json --execution-route low-overhead-worker --executor ACTUAL_ROUTE --worker-context capsule-no-parent-history-v1
scripts/corpus evidence-pack CORPUS_PATH questions.json --db index.sqlite --task-receipt task-receipt.json --execution-route coordinator-warm
scripts/corpus index CORPUS_PATH --db index.sqlite
scripts/corpus normalize-xml-schema SOURCE.md --include-records --limit 20
scripts/corpus receipts-init receipts.sqlite --corpus CORPUS_PATH --index index.sqlite
scripts/corpus search-many index.sqlite queries.json --purpose named-gap --task-receipt task-receipt.json --gap-facet F1 --receipts-db receipts.sqlite --dedupe-exact
scripts/corpus search index.sqlite "search terms" --purpose named-gap --task-receipt task-receipt.json --gap-facet F1 --receipts-db receipts.sqlite --limit 8 --max-total-chars 20000 --dedupe-exact
scripts/corpus get index.sqlite 12 18 24 --purpose locator-verification --task-receipt task-receipt.json
```

For a cold local request, `auto` performs index update, facet/query receipt reuse, all missing support/control searches, coverage-aware selection, deduplication, passage reopen, and deterministic route estimation inside one process. With no measured routing profile it emits one bounded inline payload for the coordinator. If the profile shows that delegation clears the configured saving margin, stdout emits a compact manifest and the full evidence stays in `pack_path`; one no-history worker reads that file, saves compact findings, and never repeats retrieval. The command divides the evidence budget across selected passages so one long chunk cannot hide later facets and reports truncated passage IDs for targeted continuation.

After interpretation, `findings-save` records only bounded atomic claims whose passage IDs belong to their facet. An unchanged verified repeat returns those findings with zero searches and zero reopened passages. A partial repeat matches stable facet IDs plus query plans, reuses those findings, and retrieves only new or changed facets. A changed corpus fingerprint or malformed receipt fails closed.

The question file accepts up to eight questions and three queries per question. Every explicit plan requires both `support` and `check`; use `check` for contrary, exception, variant, cardinality, and required-field probes. If queries are omitted, the helper creates a lexical fallback plan with both roles. If all explicit queries for one role miss, it performs one compact deterministic fallback for that role inside the same run and reports `fallback_search_count`; no extra model-planning turn is needed. Search mode remains `auto`: FTS expressions, prefix terms, and ordinary literal terms are resolved without silently treating `OR` or `*` as plain words.

The POSIX launcher and `scripts\corpus.cmd` select a compatible Python but do not themselves install it. If none is available, the agent follows the external-tool acquisition contract: install in an authorized scope or present the exact platform setup. Run `scripts/corpus doctor --write-dir EXISTING_DIR` only in a new or changed runtime, after a relevant failure, or on request. Use `--read-only-receipts` when the task may read but not update durable query memory.

`evidence-pack` creates `INDEX_STEM.receipts.sqlite` by default; use `--receipts-db` to select another persistent or task-local path. A corpus may be one normalized Markdown, text, page-aware JSONL, or XSD file, or a directory of them. Complete fenced XSD inside Markdown is normalized automatically into reusable SQLite schema records and compact searchable facts; no separate preprocessing command is required. The helper uses standard-library SQLite FTS5, bounded output, exact deduplication, continuation, locator-only receipts, atomic delta indexing, optional catalog routing across isolated corpora, and optional investigation state. The CLI requires an execution route and task receipt so these optimizations cannot be silently bypassed. Lower-level search/get commands are guarded: named-gap use must match a gap facet in the task receipt, locator verification is restricted to receipt passage IDs, and diagnostic/custom-adapter use records a reason. Inspect command-specific `--help` instead of reading implementation files.

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

## Installation

Install into the current project with the open-source [`skills`](https://github.com/vercel-labs/skills) CLI:

```bash
npx skills add kovaa-dev/skills --skill doc-research
```

For a global installation, add `--global`. See the repository [installation guide](../../README.md#install-with-npx-skills) for agent selection, reproducible commit-pinned sources, telemetry, and plugin installation.

## Language and version

The agent-facing instructions are written in English. This skill is included in version `v0.4.3`. <!-- x-release-please-version -->
