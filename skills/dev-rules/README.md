# dev-rules

`dev-rules` is an agent skill that defines a consistent workflow for completing software engineering tasks safely and efficiently.

It focuses on how work is executed: scope control, worktree and branch safety, user-visible-first implementation, complexity limits, validation, CI boundaries, subagents, Git, pull requests, and handoffs.

## When to use it

Use `dev-rules` for:

- implementing code, configuration, CI, or delivery changes;
- selecting the correct repository, worktree, and branch;
- keeping implementation within an accepted scope;
- choosing proportionate tests and manual validation;
- coordinating independent agents and integration work;
- managing commits and pull-request readiness;
- auditing, adopting, migrating, or updating project-work rules.

## Why use it

- **Scope authority:** distinguishes accepted product behavior from reversible implementation detail and stops changes that would silently expand the contract.
- **User-visible-first execution:** when choosing the next increment, prioritizes the smallest end-to-end user-visible path and an early manual usability gate before auxiliary harnesses or speculative infrastructure.
- **Risk-proportionate validation:** selects the cheapest reliable test level for each risk instead of requiring every task to use the same TDD, E2E, or full-suite ceremony.
- **Complexity stops:** requires a current consumer and accepted purpose for new abstractions, persistent state, services, runners, corpora, and execution paths.
- **Conservative orchestration:** keeps subagents off by default and requires independent value, disjoint write scopes, and coordinator-owned integration.
- **Explicit delivery authority:** separates branch, commit, push, ready, merge, release, and deploy permissions rather than treating them as one implicit grant.
- **Recoverable handoffs:** keeps durable state in canonical tasks, PRs, and Git while validating transient handoff context against the exact worktree and branch.
- **Documentation independence:** consumes whatever canonical product requirements, tasks, and decisions the project already uses; no companion documentation skill is required.

## Scope boundaries

`dev-rules` is an execution policy, not a product discovery system, issue tracker, or documentation framework. It consumes the project's accepted sources and leaves their ownership and format unchanged.

It does not require strict TDD, a subagent for every task, or a full validation suite for every change. It also does not bundle a runtime orchestrator, debugging methodology, research workflow, or evaluation harness; specialized tools and skills can be added independently when the task requires them.

## Example prompts

```text
Use dev-rules to implement this change within the existing product contract. Preserve the current Surface and workflow, and validate the smallest user-visible path first.

Audit the active project-work instructions and automation. Show conflicts and semantic duplicates, but do not modify anything.

Prepare the completed scope for a ready PR: integrate the current base, run risk-based checks, report remaining blockers, and do not merge.
```

## Contents

- `SKILL.md` — the complete engineering execution workflow and routing rules.
- `references/adoption.md` — adoption, audit, migration, update, and compatibility procedures.

`SKILL.md` and its references are authoritative. This README only explains what the skill contains and why it is used.

## Independence

`dev-rules` does not require a particular PRD, task-tracking, or documentation system. It consumes the canonical sources already selected by the project and asks for clarification when they are absent or contradictory.

## Installation

Install the skill into the current project with the open-source [`skills`](https://github.com/vercel-labs/skills) CLI:

```bash
npx skills add kovaa-dev/skills --skill dev-rules
```

For a global installation, add `--global`. Repeat `--agent` for each desired global-capable target and add `--yes` for a non-interactive install. Without `--agent`, the CLI detects installed agents and asks which targets to use; see the root guide for the `skills@1.5.26` limitation on global `--agent '*'`.

Update or remove the skill with:

```bash
npx skills update dev-rules
npx skills remove dev-rules
```

See the repository [installation guide](../../README.md#install-with-npx-skills) for project/global scope, reproducible commit-pinned sources, telemetry, and Codex plugin installation.

## Language and version

The agent-facing instructions are written in English. This skill is included in version `v0.3.0`. <!-- x-release-please-version -->
