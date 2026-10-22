# doc-research

`doc-research` supports evidence-grounded analysis of large document collections without repeatedly loading the corpus into model context. It provides bounded retrieval, cross-session query reuse, version-aware citations, conflict checks, and optional resumable research state.

Use it for multi-document investigations, version comparisons, tenders, contracts, standards, policies, page-level evidence, or conflict/gap analysis. A short single source is usually better read directly.

## How it works

The agent selects two things:

- **Route:** Direct, Retrieval, or Research determines the process and whether investigation state is useful.
- **Effort:** compact, balanced, or thorough determines retrieval breadth and verification search. Balanced is the default.

The storage model is deliberately separated:

```text
authorized sources -> reusable index -> query receipts
                                      -> optional investigation research state
multiple isolated corpora -> optional catalog routing
```

The index is rebuildable retrieval data, receipts remember completed searches by locator, and research state keeps only selected facets, evidence, conflicts, gaps, and the next action. Exact schemas and lifecycle rules live in [evidence schema](references/evidence-schema.md).

Catalog registration can derive opaque stable project/corpus IDs from canonical context while keeping a separate editable human-readable label; source-routing rules own the exact identity contract.

Durable paths are caller-selected. Generated databases belong in an authorized persistent derived-data location, not in the installed skill, a temporary directory, or among originals. Existing compatible project stores or connectors can serve as adapters instead of creating parallel state.

For interoperability, the skill accepts a bounded request describing the question, facets,
authorized sources/versions, known locators, intended output, and constraints. It returns conclusions
by facet with source locators, versions, conflicts, gaps, searched scope, coverage limits, and
verification limitations. The caller remains responsible for any downstream decision or acceptance.

## Quick start

From the skill root, for an authorized normalized corpus:

```bash
scripts/corpus index CORPUS_DIR --db index.sqlite
scripts/corpus receipts-init receipts.sqlite --corpus CORPUS_DIR --index index.sqlite
scripts/corpus search index.sqlite "search terms" --receipts-db receipts.sqlite --limit 8 --max-total-chars 20000 --dedupe-exact
scripts/corpus get index.sqlite 12 18 24
```

The POSIX launcher and `scripts\corpus.cmd` select a compatible Python and do not install it. Run `scripts/corpus doctor --write-dir EXISTING_DIR` only in a new or changed runtime, after a relevant failure, or on request. Use `--read-only-receipts` when the task may read but not update durable query memory.

Initialize a receipt store once per corpus/index pair, then reuse it. The helper accepts normalized Markdown, text, and page-aware JSONL. It uses standard-library SQLite FTS5, bounded output, exact deduplication, continuation, locator-only receipts, atomic delta indexing, optional catalog routing across isolated corpora, and optional investigation state. Inspect command-specific `--help` instead of reading implementation files.

## Read the relevant guide

- [Ingestion](references/ingestion.md): conversion, OCR, Docling, ZIP extraction, normalized inputs, indexing, and runtime checks.
- [Source routing](references/source-routing.md): multiple corpora, projects, attachments, URLs, wikis, connectors, catalogs, and adapter contracts.
- [Project integration](references/project-integration.md): classification and safe use, migration, or cleanup of existing research artifacts and rules.
- [Evidence schema](references/evidence-schema.md): the canonical memory model, durable research fields, receipts, resume, and synthesis.
- [Retrieval effort](references/retrieval-effort.md): numeric compact, balanced, and thorough budgets.
- [Orchestration](references/orchestration.md): capability-based delegation for independent work packets.
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
