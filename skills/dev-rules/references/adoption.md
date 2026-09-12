# Adopting, auditing, migrating, and updating project-work rules

This reference governs only the rules for performing engineering work. Requirements,
PRDs, the task tracker, TDs/ADRs, and documentation history remain in their respective
canonical project sources; this skill does not require a specific documentation system.

## How a project uses the skill

During `init`, the user explicitly chooses one of two clear approaches:

### Project-local copy

The complete skill directory is stored at a project-local path, typically
`.agents/skills/dev-rules/`, and committed with the project. The repository is
self-contained: the agent entrypoint points to this specific copy. Unless the user
chooses another approach, propose this option by default.

### Pinned published skill/reference

The repository retains a short agent entrypoint, project settings, scoped exceptions,
and a reference to a publicly accessible `dev-rules` source pinned to an immutable Git
commit SHA or reproducible content digest. A branch, a tag without an immutable target,
`latest`, and a personal absolute path are not reproducible sources. This approach is
permitted only after an explicit user choice or under organization policy.

Do not create a `mode`, `profile`, or `rule_source` field or a separate selection
registry. The project structure makes the approach unambiguous: either a complete
project-local copy exists, or the entrypoint contains a pinned public reference. Ask for
the decision during `init`; ask again only during an explicitly invoked
`migrate`/`update` if the user wants to change the approach or the operation affects
adoption. An ordinary engineering task does not ask again.

Until an approach has been accepted and verified, the existing project rules remain in
force, and the skill is used only to make a proposal or perform a read-only audit.
Temporary migration status lives in the migration task/PR itself and is removed or
closed with it; it is not permanent governance state.

## Verification depth

Do not store a separate adoption profile. By default, perform normal verification of the affected scope:

- active sources in scope are listed;
- conflicts are resolved by the user;
- unique project settings and scoped exceptions are preserved;
- semantic duplicates are removed or excluded from the active route;
- the selected adoption approach is reproducible;
- one typical project-work route finds the correct skill and settings;
- automation does not continue enforcing a removed rule.

Full verification is required only when explicitly requested or when repository,
organization, or compliance policy requires it. It additionally covers the entire
agreed source scope, old-to-new mapping, enforcement in hooks/CI/scripts, source availability to everyone who needs to use it, and reproducible evidence. It verifies
governance; it does not certify the product or code.

## `init`

1. Find existing project-work instructions and automation. In an empty project, do not
   create artificial history, CI, hooks, branches, or a task system.
2. Agree on the minimum settings: default branch/base, Git/PR authority, required
   project commands, generated files, and scoped exceptions. Add a worktree-local
   handoff path/ignore only if the project actually uses handoff; do not create empty
   state.
3. Ask the user to choose either a “project-local copy” or a “pinned published
   skill/reference.” Do not encode this choice in an additional state field.
4. For existing local rules, `migrate` itself begins with an affected-scope audit; a
   separate preliminary `audit` is not required.
5. After write access is authorized, create either the project-local copy or the pinned
   pointer and a short entrypoint. Do not leave competing active duplicates alongside
   it.
6. Perform normal verification or the explicitly required full verification. Only
   after it succeeds does ordinary work automatically apply the adopted skill without
   manual invocation.

## `audit`

An audit is a standalone read-only action used when the user wants to understand the
current state before deciding on migration. `migrate` and `update` perform the same
analysis within their affected scope and do not require a separate audit run. Limit the
search to the explicitly specified process/governance scope; use the full scope only for
a full audit:

- root and nested agent instructions, RULES/CONTRIBUTING, and project settings;
- task runner scripts, hooks, CI workflows, and release automation that enforce process
  rules;
- branch/worktree/PR/handoff tooling, including tracked singleton `current` pointers,
  shared cross-branch state, and active scoped exceptions.

Do not read the product backlog or implementation code unless the question requires it.
Classify every rule found as one of the following:

- an exact or semantic duplicate of the skill;
- a unique project setting;
- a scoped exception;
- a conflict;
- historical/non-active text;
- automation that in practice enforces old or different behavior.

Show the conflicting wording, scope, practical consequence, recommended option, and an
alternative. Do not automatically choose the skill, the local rule, or the newer text.
Do not delete or change anything during an audit. A successful grep/lint does not
replace semantic comparison.

## `migrate`

Migrate requires authorized write and cleanup scope and begins with its own
affected-scope audit. Before making changes:

1. resolve all conflicts with the user;
2. record the source-to-destination mapping and the list of deletions;
3. preserve a minimal recoverable checkpoint for substantial uncommitted work;
4. separate shared rules from project settings and genuine scoped exceptions;
5. confirm the current adoption approach or agree on changing it; do not create a mode.

Move content in small, verifiable batches. After a conflict has been resolved, you may
delete the conflicting local rule and its automation or exclude historical text from
the active route. Remove semantic duplicates instead of retaining them “just in case.”
Do not rewrite product requirements or documentation governance.

Align automation with the selected rule: hooks, CI, task scripts, and handoff/worktree
checks must not continue enforcing a removed rule. When parallel work is possible,
replace a tracked singleton handoff with verified gitignored worktree-local state after
moving unique durable information to the canonical task/PR. Do not create a new
validator, evidence harness, or migration framework when a diff, existing checks, and
one typical route smoke test are sufficient.

Completion criteria:

- the project-local copy is complete, or the external pointer is public and pinned;
- only settings/exceptions and the necessary entrypoint remain locally;
- conflicts and deduplications are covered by the agreed mapping;
- the required verification depth has passed;
- a partial migration explicitly remains an unfinished task/PR rather than becoming a
  new governance mode.

## `update`

Update applies when the available skill revision has changed. It performs its own
affected-scope `audit + migrate`; it does not require a separate audit and does not add
new text on top of old text.

1. Determine the current source from the project-local directory or pinned pointer. Do
   not look for a separate selection field.
2. Compare the revision in use with the new revision. For a project-local copy, compare
   its contents with the new version; for a published source, compare the old and new
   immutable commits/digests. If the previous source is unavailable, audit the current
   rules/automation against the new version and state the comparison limit explicitly.
3. Classify changes as added, strengthened, weakened, removed, renamed/moved, or
   clarification. A weakened or removed rule is a material change, not an “absence of
   diff.”
4. Find project copies, scoped exceptions, and automation that preserve the old
   behavior. Show incompatibilities and consequences to the user.
5. After agreement, update the complete copy or pinned pointer and migrate only the
   affected scope. If the new version weakened or removed a rule, delete the old local
   requirement and the automation enforcing it; retain a stricter version only as an
   explicitly accepted scoped exception.
6. Reverify the affected criteria and one ordinary project route. A full rerun of all
   verification is not required for a compatible local diff.
7. Change the commit SHA/content digest in a pointer as the final step. A project-local
   copy does not need a separate revision record: its committed content is the revision
   in use. If blocked, leave the previous working source in place and list what remains.

Do not call an update complete while stale active project-work rules or automation that
enforces them remain in effect.

## Coordinated update with other governance sources

A coordinated update is required when project-work rules and related
product/documentation governance sources change together, or when a rule moves across
the boundary between them. No specific second skill is required; do not create a
separate compatibility registry.

1. Determine the actual source of every affected governance source independently.
2. Compare the old and new revisions and produce one list of changed rules, ownership
   moves, conflicts, stale copies, and enforcement.
3. Update the canonical owner of each rule first, then consumer references and project
   settings; do not tie ownership to a tool name.
4. Do not leave a rule canonical in two sources or allow a gap during the move. If the
   owner source is unavailable, block only the dependent portion.
5. Update related sources in one coherent project diff, even if their adoption
   approaches differ.
6. Verify responsibility boundaries, references, and the absence of active duplicates;
   commit only with explicit authority or authority stored in project policy.

If a change to one skill does not affect another and does not change ownership or a
cross-reference, update it independently without a coordinated-update ceremony.
