# dev-docs

An agent skill for product and technical documentation: sourced system descriptions,
references and guides, living requirements, lean work queues, decisions, and verified results.

PRD/product-task and layer-task tracking is officially legacy. Before continuing selected
legacy work, the agent captures its affected contract and remaining work into the new
scheme. Existing historical records remain available; unrelated backlog is not migrated
implicitly.

## When to use it

- Groom desired behavior, constraints, acceptance, and material open questions.
- Maintain descriptions, API references, guides/runbooks, and specifications in their owners.
- Plan code, research, documents, data, and other outcomes in lean queues.
- Analyze affected and preserved contracts, prerequisites, and conflicting obligations.
- Keep proposed replacements distinct from current contracts; retire stale routes with
  explicit successor/history notices.
- Register significant bugs, findings, and assigned ideas without duplicating requirements.
- Convert selected legacy material before continuing ordinary authorized work.
- Perform an explicitly requested one-shot migration or governance-source update.

## How the transition works

**Ordinary work:** capture the selected legacy requirement/task first, preserve its meaning
and history, link converted sections to their new owners, then continue from those records.
Unconverted sections of a shared source remain explicitly active until their own conversion.
Repeated entry reuses the same IDs and mapping. No init or complete backlog migration is required.
[Coverage reconciliation](references/legacy-transition.md#coverage-and-reconciliation) makes
existing meaning, destinations, new inputs, and remaining gaps explicit. Newly received
requirements/questions use ongoing capture directly in their owning documents.

**One-shot migrate:** convert the entire agreed scope, including active and completed
work, decisions, questions, acceptance sources, and verification. Reconcile the reading
routes and actual validators. Former task-schema/hard-renaming migrations use this
workflow; renaming files alone does not accomplish it.

Requirements describe obligations; queues describe work. A bug can create new repair work
against the same unchanged requirement. Research can produce an accepted negative
conclusion without implementing a product requirement. Multiple queue views preserve
one canonical work entry and cross-queue waits.

## Example prompts

- "Continue this legacy task. First capture its requirements and remaining work under
  dev-docs, preserve its history, and resume from the new canonical records."
- "Groom cross-device preferences. Keep accepted requirements distinct from implementation
  questions and prepare only the nearest useful research or delivery outcome."
- "Migrate this project's selected backlog and specifications to requirements and lean
  queues in one operation, preserving completed results and unresolved questions."
- "Audit conflicts and change impact in this area. Keep the audit read-only and show
  affected obligations, applicability, verification gaps, and proposed resolutions."

## Contents

- [SKILL.md](SKILL.md): material/owner route, mandatory on-touch conversion, and actions.
- [Requirements](references/requirements.md): identity, revisions, rationale, applicability,
  dependencies, conflicts, and impact.
- [Work queues](references/work-queue.md): readiness, multiple queues, result/history, and targets.
- [On-touch transition](references/legacy-transition.md): ordinary incremental conversion.
- [One-shot migration](references/governance-migration.md): full agreed scope.
- [Governance](references/documentation.md), [grooming](references/product-discovery.md),
  [maintenance](references/maintenance.md), and [forms](references/documentation-registers-template.md).
  Governance covers documentation purpose, decision acceptance, and work-context placement.
- [Legacy recognition](references/task-tracker.md): compatibility reader, not old authoring rules.

The skill ships Markdown guidance, not a tracker runtime or implicit automation. It
does not require PR-based delivery or replace the active engineering/deployment policy.

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

The agent-facing instructions and baseline tracker schema are written in English. This skill is included in version `v0.5.0`. <!-- x-release-please-version -->
