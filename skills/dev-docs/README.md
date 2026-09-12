# dev-docs

`dev-docs` is an agent skill for product discovery, documentation governance, and file-based task tracking without duplicating sources of truth.

It turns an idea or an existing product state into a sequence of usable increments while keeping requirements, technical work, decisions, maintenance, and documentation consistent.

## When to use it

Use `dev-docs` for:

- product discovery and staged grooming;
- PRDs and user-visible product outcomes;
- technical tasks organized by ownership layer;
- technical and architecture decisions;
- roadmap and backlog maintenance;
- bug, engineering finding, and product idea intake;
- documentation audits and controlled migrations;
- adopting or updating documentation rules in a repository.

## Why use it

- **Lifecycle coverage:** connects discovery, PRDs, technical decomposition, decisions, roadmap state, maintenance, audit, and migration instead of generating one isolated artifact.
- **Vertical Slice Development:** starts with the smallest end-to-end product slice that can be used and evaluated, then expands the same working product through independently useful features instead of completing isolated technical layers up front.
- **Just-in-time decisions:** uses general grooming to unblock the nearest stage and a short micro-grooming pass before each PRD implementation.
- **Context-efficient by design:** routes the agent through indexes, canonical links, and targeted references so unrelated product history, backlog, and technical documentation do not need to be loaded for the current question.
- **Explicit ownership:** gives each requirement, decision, task, status, and piece of evidence one canonical owner while keeping indexes navigational.
- **Existing-project support:** can establish the current product state, preserve shipped behavior, consolidate conflicting documentation, and build a forward roadmap without inventing historical stages.
- **Tool independence:** works with Markdown files and project-defined paths, layers, checks, and issue trackers; it does not require a particular execution skill or runtime.

## Scope boundaries

`dev-docs` governs product and documentation continuity; it is not a code-execution framework. It prepares durable product contracts, technical work, decisions, and roadmap state for the execution workflow already used by the project.

It does not require strict TDD, a particular agent orchestration model, or an autonomous report-to-PR loop. It also does not bundle executable validators: optional parser compatibility is documented separately and applies only when a project explicitly adopts compatible tooling.

## Example prompts

```text
Use dev-docs to shape this idea into the smallest usable Alpha. Start with overall grooming and do not write project files until we agree on the direction.

Before implementing PRD-012, run micro-grooming using the results of completed PRDs. Resolve only the open questions that block this PRD or the current delivery stage.

Audit the current documentation and task tracker. Report conflicting sources, duplicated rules, missing roadmap entries, and independent remediation tracks. Keep the audit read-only.
```

## Contents

- `SKILL.md` — the agent-facing entry point, action routing, and safety boundaries.
- `references/documentation.md` — documentation ownership, decision approval, consistency, and granularity.
- `references/product-discovery.md` — staged product discovery and just-in-time grooming.
- `references/task-tracker.md` — PRDs, technical tasks, statuses, dependencies, and roadmap rules.
- `references/maintenance.md` — bugs, findings, ideas, support work, and releases.
- `references/adoption.md` and `references/governance-migration.md` — adoption, audit, migration, and update workflows.
- `references/forms-*.md` — optional document and task templates.

`SKILL.md` and the applicable reference files are authoritative. This README only explains the purpose and layout of the skill.

## Independence

`dev-docs` does not require a specific engineering execution skill. Git, CI, agents, worktrees, and pull-request operations follow the active project-work policy or explicit user authority.

## Installation

Install the skill into the current project with the open-source [`skills`](https://github.com/vercel-labs/skills) CLI:

```bash
npx skills add kovaa-dev/skills --skill dev-docs
```

For a global installation, add `--global`. Repeat `--agent` for each desired global-capable target and add `--yes` for a non-interactive install. Without `--agent`, the CLI detects installed agents and asks which targets to use; see the root guide for the `skills@1.5.26` limitation on global `--agent '*'`.

Update or remove the skill with:

```bash
npx skills update dev-docs
npx skills remove dev-docs
```

See the repository [installation guide](../../README.md#install-with-npx-skills) for project/global scope, reproducible commit-pinned sources, telemetry, and Codex plugin installation.

## Language and version

The agent-facing instructions and baseline tracker schema are written in English. This skill is included in version `v0.1.0`.
