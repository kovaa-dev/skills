# dev-docs

An agent skill for product and technical documentation: sourced system descriptions,
references and guides, living requirements, lean work queues, decisions, and verified results.

The target model is independent of a project's starting documentation scheme. Assess
actual sources, reuse compatible records, and reconcile selected contract/work ownership
before continuing dependent work. Preserve source meaning and history; do not migrate
unrelated backlog implicitly.

## When to use it

- Groom desired behavior, constraints, acceptance, and material open questions.
- Maintain descriptions, API references, guides/runbooks, and specifications in their owners.
- Plan code, research, documents, data, and other outcomes in lean queues.
- Recover undocumented requirements from code with explicit source paths and inspected baseline.
- Analyze affected and preserved contracts, prerequisites, and conflicting obligations.
- Keep proposed replacements distinct from current contracts; retire stale routes with
  explicit successor/history notices.
- Register significant bugs, findings, and assigned ideas without duplicating requirements.
- Reconcile selected sources when their meaning or ownership needs conversion.
- Perform an explicitly requested one-shot migration or governance-source update.

## How the transition works

**Ordinary work:** assess selected sources, reuse compatible owners, and capture only
scope that needs reconciliation. Preserve its meaning and history, link converted sections to their new owners, then continue from those records.
Unconverted sections of a shared source remain explicitly active until their own conversion.
Repeated entry reuses the same IDs and mapping. No init or complete backlog migration is required.
Existing and newly captured work share the existing queue/index as ID/name/link/status rows. Selected
source aggregates are replaced by covered requirement/result links with preserved provenance.
Requirements live in their owners. No parallel transition queue or generator is required.
[Coverage reconciliation](references/source-transition.md#coverage-and-reconciliation) makes
existing meaning, destinations, new inputs, and remaining gaps explicit. Newly received
requirements/questions use ongoing capture directly in their owning documents.

**One-shot migrate:** convert the entire agreed scope, including active and completed
work, decisions, questions, acceptance sources, and verification. Reconcile the reading
routes and actual validators. Renaming files alone does not accomplish it.

Requirements describe obligations; queues describe work. A bug can create new repair work
against the same unchanged requirement. Research can produce an accepted negative
conclusion without implementing a product requirement. Multiple queue views preserve
one canonical work entry and cross-queue waits.

## Example prompts

- "Continue this work. Assess its existing sources and reconcile requirements and remaining work under
  dev-docs, preserve its history, and resume from the new canonical records."
- "Groom cross-device preferences. Keep accepted requirements distinct from implementation
  questions and prepare only the nearest useful research or delivery outcome."
- "Migrate this project's selected backlog and specifications to requirements and lean
  queues in one operation, preserving completed results and unresolved questions."
- "Audit conflicts and change impact in this area. Keep the audit read-only and show
  affected obligations, applicability, verification gaps, and proposed resolutions."

## Contents

- [SKILL.md](SKILL.md): material/owner route, source assessment and scoped conversion, and actions.
- [Requirements](references/requirements.md): identity, revisions, rationale, applicability,
  dependencies, conflicts, and impact.
- [Work queues](references/work-queue.md): readiness, multiple queues, result/history, and targets.
- [On-touch transition](references/source-transition.md): ordinary incremental conversion.
- [One-shot migration](references/governance-migration.md): full agreed scope.
- [Governance](references/documentation.md), [grooming](references/product-discovery.md),
  [maintenance](references/maintenance.md), and [forms](references/documentation-registers-template.md).
  Governance covers documentation purpose, decision acceptance, and work-context placement.

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

See the repository [installation guide](https://github.com/kovaa-dev/skills#install-with-npx-skills) for project/global scope, reproducible commit-pinned sources, telemetry, and Codex plugin installation.

## Language and version

The agent-facing instructions and documentation forms are written in English. This skill is included in version `v1.0.0`. <!-- x-release-please-version -->
