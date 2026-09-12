# Adopting, auditing, migrating, and updating documentation rules

This is the sole source of the requirements governing adoption of `dev-docs` in a project.
[Bootstrap](documentation-system-template.md) creates the minimum structure, while
[migration](governance-migration.md) addresses existing rules. Installing the skill alone does not
change the project's active rules.

## How a project uses the skill

During `init`, the user explicitly chooses one of two clear methods:

### Copy in the repository

The complete skill directory is stored at a project-local path, usually
`.agents/skills/dev-docs/`, and committed with the project. The repository is self-contained: the
documentation/agent entrypoint points to this exact copy. If the user has not selected another
method, propose this option by default.

### Link to the published skill

The repository retains the product documentation, task tracker, project settings, scoped
exceptions, and a short entrypoint linking to a publicly available `dev-docs`, pinned to an
immutable Git commit SHA or reproducible content digest. A branch, a tag without an immutable
target, `latest`, and a personal absolute path are not reproducible sources. This method is allowed
only after an explicit user choice or under organization policy.

Do not create a `mode`, `profile`, or `rule_source` field or a separate selection registry. The
method is unambiguous from the project structure: either a complete project-local copy exists, or
the entrypoint contains a pinned public link. Request the decision during `init`; ask again only
during an explicitly invoked `migrate`/`update` when the user wants to change the method or the
operation affects adoption. Do not ask again during ordinary docs/tasks work.

Until either method has been accepted and verified, the existing project rules remain in effect,
and the skill is used only for proposals or a read-only audit. Temporary status and compact source
mapping for a migration live in the migration task/PR itself. Create a separate working mapping file
only for a full/large migration or explicitly required policy traceability; condense or delete it
after verification. Preserve long-term mapping evidence only when explicitly required, and do not
turn it into permanent governance state.

## Verification depth

Do not store a separate adoption profile. By default, perform the normal affected-scope check:

- active docs/task rule sources in the scope are listed;
- every document type in the selected scope is checked, with no exclusions based on directory/name;
- related project docs are checked against each other, and the user resolves conflicts;
- when migration/audit remediation exists, independently executable work is ordered by dependency,
  and a shared integration boundary gets a separate task only when it has its own result;
- unique project settings and scoped exceptions are preserved;
- semantic duplicates are removed or excluded from the active route;
- the selected adoption method is reproducible;
- one typical docs/task request finds the correct skill without reading the entire backlog;
- changed links, IDs, and dependencies pass the applicable project checks.

A full check is required only when explicitly requested or when repository/org/compliance policy
requires it. It additionally covers the entire agreed source scope, a temporary old→new mapping,
requirements and history, docs parser/validator enforcement, source availability to every
necessary executor, and reproducible evidence. Every applicable criterion must be met; this checks
the documentation system, not the product, code, or security.

## Safe adoption

1. Within the authorized `init`/`migrate`, locate active docs/task rules, settings, related
   product/technical documents, and automation that enforces their format. First perform an
   affected consistency check of project docs. Do not change agent instructions, hooks, CI, Git,
   or handoff without authority under the active project-work policy.
2. Ask the user to choose "copy in the repository" or "link to the published skill." Do not encode
   the choice in an additional state field.
3. Show local↔local and local↔skill conflicts with their practical consequences. Do not
   independently choose the skill, one of the project sources, or the later text.
4. After write permission is granted, create either the complete project-local copy or a pinned
   pointer, preserve project settings/scoped exceptions, and remove the agreed active duplicates.
   Preserve historical records, but exclude them from the active route.
5. Perform the normal check or the explicitly required full check. Only after it succeeds does
   ordinary work automatically apply the adopted skill without manual invocation.
6. If it fails, leave the previous working sources available and list the blocker and remaining work
   in the migration task/PR. Do not create a permanent `migrating` mode.

An empty new project follows the same path without artificial history, a backlog, or code. Missing
materials do not require fictitious evidence.

## What remains in the project

Regardless of the adoption method, the project retains product requirements, PRDs, tasks,
decisions, history, navigation, specific paths/layers/language, project settings, and
explicitly accepted scoped exceptions. The general policy is represented either by a complete
project-local copy of the skill or by a pinned public link; do not create a third paraphrased copy.

Agree new local exceptions and explicitly limit their scope. Propose a new general principle as a
separate change to the source skill rather than adding it silently to one project.

## Update

When a new revision becomes available, `update` performs a limited affected-scope `audit + migrate`
itself; it does not require a separate preliminary audit run.

1. Identify the current source from the project-local directory or pinned pointer. Do not look for
   a separate selection field.
2. For a project-local copy, compare its content with the new revision; for a published source,
   compare the old and new immutable commits/digests. If the previous source is unavailable, audit
   the current rules against the new version and explicitly state the comparison limitation.
3. Classify rules as added, strengthened, weakened, removed, renamed/moved, or clarification.
   Weakening and removal are significant changes.
4. Find docs/task copies, settings, exceptions, templates, and parser/validator rules that preserve
   the old behavior. Show conflicts and consequences to the user.
5. After agreement, update the complete copy or pinned pointer and migrate only the affected scope.
   Remove a stale local requirement and docs/task enforcement if the new revision weakened or
   removed it; retain a stricter variant only as an explicitly accepted scoped exception.
6. Recheck the affected criteria and one ordinary docs/task route. A full repeat of every check is
   unnecessary for a compatible local diff.
7. Change the commit SHA/content digest in the pointer as the final step. For a project-local copy,
   no separate revision record is required: its committed content is the revision in use. If there
   is a blocker, leave the previous working source in place and list the remaining work.

In read-only mode, keep the result and migration plan in the response. Update does not authorize
silently changing product decisions or deleting historical evidence.

## Coordinated update with project-work governance

When documentation governance and independent project-work rules are updated together, or a rule
moves between their scopes, update the canonical owner first, followed by consumer references and
project settings. Change related project-local copies or pinned pointers in one coherent diff. No
specific execution skill is required; do not duplicate orchestration here or create a compatibility
registry.
