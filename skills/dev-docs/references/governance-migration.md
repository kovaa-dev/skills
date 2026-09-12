# Rule consolidation during migration

This is a mandatory part of `migrate` when the scope includes a transition to the
documentation system. Use together with the [policy](documentation.md) and
[bootstrap](documentation-system-template.md). The goal is one active rule in one
canonical source, not a new set alongside old, scattered rules. The skill defines source
responsibilities; specific project paths are recorded in the documentation index. Adoption
of the shared rules is completed by [verification of the selected source](adoption.md);
until then, preserve the existing rules and any changes to the current migration task/PR
that were explicitly agreed.

## 1. Find existing rules

First find instructions and reading routes, then inventory every document in the agreed
scope: root and nested AGENTS/RULES, README/CONTRIBUTING,
product/marketing/backend/frontend/operations docs, PRD/tasks/TD/ADR, specs, runbooks,
research/evidence, indexes, templates, TODO/backlog, agent instructions, and check
settings. A full audit/migrate covers every document in the repository; an
affected-scope audit covers every related type, without excluding a directory because of
its name. Do
not treat filenames as a guarantee: a rule, task status, decision, or backlog item may be
hidden in a spec, marketing document, report, or README.
Treat higher-level instructions as external constraints and do not edit them without
separate permission. Do not treat a complete project-local copy of the skill as a
duplicate when the user selected that adoption method; paraphrased local policies remain
candidates for cleanup. Do not read every document in full, one after another: inventory
and headings/search cover each file in scope, after which only targeted sections and
related sources are read. This progressive scan does not permit excluding a document type
from a full audit.

Separate documentation rules from product requirements, implementation contracts,
examples, and historical records. Before comparing rules with one another, perform an
affected-scope consistency check of related PRD/tasks/TD/ADR/settings according to the
policy's “Project documentation consistency check” section. Do not move its
product/contract conflicts into the governance mapping or resolve them automatically.
Checks expose actual tool constraints but do not automatically become accepted rules. The
presence of old text does not prove that it remains current; consider its acceptance source
and scope.

## 2. Map meaning and scope

Maintain a compact mapping from each source to its canonical destination in the existing
migration task. Create a separate source mapping only for an explicitly full/large
migration, compliance, or required traceability. Keep `Relation to canonical`—unique rule,
exact duplicate, semantic duplicate, supplement, conflict, historical/inapplicable
record—separate from `Disposition`—accepted, open, rejected, unmapped—and store the
reason separately. Do not copy complete rule text or task statuses: the mapping is
temporary migration evidence, not a policy or roadmap.

After completion, every open/unmapped item must be resolved or explicitly left as
remaining migration scope. Collapse a separate mapping into a compact closure summary in
the migration task/PR and delete it after a checkpoint and user permission. Preserve it as
historical evidence only when required by an external audit, compliance, repository policy,
or explicitly accepted long-term traceability; ordinary work neither reads nor updates it.

Compare semantic duplicates by their conditions, exceptions, and normative strength.
Different wording does not necessarily mean different rules, and similar wording does not
prove duplication. Preserve a local clarification for a narrower scope as a scoped rule;
do not remove it as a conflict with a general rule. Do not generalize a restriction from
one layer to the entire project.

## 3. Prepare independent migration tasks

Check existing TODO/backlog/findings and every identified remediation result for real
dependencies. An independent task has one verifiable outcome, one layer owner, explicit
prerequisites/acceptance, and does not require simultaneous writing to another owner's
canonical source. Group non-blocking tasks into parallel-ready tracks; in a read-only audit,
show a proposed task map, and when migration writes are authorized, create or update the
canonical cards. Do not split a small sequential migration or create tasks merely to
increase the number of workers.

Shared indexes, cross-layer contracts, source mapping, and final conflict resolution remain
a separate shared boundary. Create an integration task only when reconciling them has its
own verifiable outcome and does not fit in a single incoming task. It depends on all
required tracks, owns only the shared boundary, verifies the combined result, and does not
copy the status/acceptance of child tasks. If an ordinary merge and coordinator review are
sufficient, no separate card is needed.

The task graph describes permitted independence but does not grant authority to start work
in parallel. Agents, branches/worktrees, disjoint write scopes, feedback, and integration
review follow the active project-work policy; this skill provides the execution workflow
with canonical tasks, sources, dependencies, and acceptance.

## 4. Resolve conflicts with the user

For every incompatible pair, show the original wording and links, scopes, practical effects,
the recommended option, and alternatives. Do not automatically choose the old rule, the
skill wording, or the later record. Continue to follow higher-level instructions; a request
for agreement does not permit bypassing them. Record acceptance of a new project rule with
its source/date according to the policy.

Until a conflict is resolved, do not replace disputed rules with new accepted text and do
not delete sources. Mark the relevant part of the migration as blocked. Independent,
non-conflicting parts may be migrated; do not declare the entire transition complete.

## 5. Assign content to canonical sources

| Content | Canonical destination after transition |
| --- | --- |
| Requirements ownership, granularity, agreement, write mode | documentation.md in the skill |
| Rules for IDs, tasks, statuses, dependencies, and PRD contents | task-tracker.md in the skill; the cards themselves remain in the project |
| Rules for bugs, findings, the support queue, and release | maintenance.md in the skill; the records remain in the project |
| Grooming and product formation | product-discovery.md in the skill |
| Adoption and migration | adoption.md, documentation-system-template.md, and this workflow in the skill |
| Paths, layers, language, selected checks, and scoped project settings | Project settings in the documentation index |
| Forms | forms files in the skill; completed documents remain in the project |
| Details of the selected validator | Compatibility reference in the skill; tool settings remain in the project |

Preserve each unique, applicable project-specific behavior as an agreed setting or
scoped exception, with rationale and links to the applicable shared rules. A substantial,
standalone exception may have a separate local document, but not a copy of the policy.
Propose a generally useful rule as a separate change to the source skill; migrating one
project does not authorize changing published rules for everyone. Product requirements and
engineering contracts remain in PRD/TD/ADR and do not move into the documentation policy.
Make required changes to AGENTS/RULES, handoff, hooks, and CI only under the active
project-work policy. This skill defines the required docs pointer/settings but does not own
the agent entrypoint or delivery automation.

## Hard migration: names and IDs of historical documents

Hard migration runs only on explicit request and may rename already closed tasks and
product stages/PRDs without changing historical facts. For the transition, propose one
consistent renaming plan for the entire selected scope: active and already closed tasks,
product stages/PRDs, TD/ADR, research, reports, and all other documents. Closed status
alone does not exclude a document from the new naming system. First show the user a batch
of old path/ID/title → new path/ID/title mappings with reasons; apply only the agreed batch,
and do not rename all history merely because `migrate` was started. Do not require an ID
for a free-form document when the new methodology specifies only a stable path for its
type.

Renaming changes representation, not historical facts:

- preserve the exact original content in an accessible revision/patch/checkpoint before
  making changes;
- use move/rename and targeted replacements; do not recreate content from memory;
- update the filename, H1, structural IDs, and prefixes of local subtasks consistently;
  do not combine an identifier change with a new task or new technical decision;
- preserve owners, dates, historical statuses, checkbox states, the meaning of scope and
  acceptance, results, and evidence of completion; do not reopen closed tasks;
- do not change commit hashes, commit messages, PR numbers/URLs, or their remote history;
- do not rewrite IDs inside quotations, logs, command output, or other primary evidence:
  they are source facts. Link them to the new record through the old→new mapping;
- update current inbound links, dependencies, indexes, and anchors. List external links
  that cannot be fixed and provide an agreed way to resolve old names through the
  mapping/preserved revision instead of leaving a second active document;
- verify uniqueness of new IDs, non-reuse of old IDs, absence of cycles and lost records,
  preservation of evidence, and consistency of the dependency graph.

Do not mechanically give an old stage a PRD ID when its meaning does not correspond to a
product outcome. For an incompatible type, ambiguous split, or historical status, propose
a transformation or explicit exception to the user. Do not present merging/splitting
multiple outcomes as a simple rename. The transformation map lives in the temporary source
mapping until hard migration is complete; afterward, it is collapsed or preserved as
historical evidence under the rules above and never becomes a second task tracker.
A historical decision with `accepted` status may remain active: exclude obsolete rules
from reading routes, not every document with an old date.

## 6. Remove active duplicates and verify the result

Create a checkpoint before making changes. In agreed files, replace migrated normative
sections with precise links or remove the redundant copy. Removing duplicates is included
in the explicitly authorized scope of such consolidation; invoking `init` once or making a
general audit request does not grant this permission. If the specific cleanup scope has
not been authorized, first propose a list of files/sections. Do not delete entire files
without separate permission; preserve other rules and user changes.

Update docs/task templates and parser rules so they do not generate old rules. Make
changes to agent instructions, hooks/CI/handoff under the active project-work policy; do
not silently disable checks for the migration.
Do not rewrite historical meaning or primary evidence. Perform renaming according to the
section above; exclude only obsolete rules from the current-rule route while preserving
accessible history and links to decisions that remain active.

Repeat the consistency/type check for every document in the original scope and search for
normative wording. Verify that every file is classified by its actual purpose; task
status/checklists do not remain in specs/README/marketing; the task index shows every
registered task exactly once and its status projection matches the canonical cards;
PRD/task/TD/ADR use the agreed ID-based naming; and a descriptive source does not pretend
to be a card.
For every rule, verify its destination, preservation of conditions/exceptions, absence of
an active copy, and working links to the old location. For the task graph, verify the
absence of cycles and hidden shared-write dependencies; an integration task exists only
where its outcome is genuinely required. Verify the route from AGENTS/RULES to the
canonical section and the absence of a second policy in templates. List unavailable
sources, unresolved conflicts, and remaining scope. Search and lint do not prove semantic
equivalence: separately compare the source rules with the result. Migration is complete
only after coverage of the entire agreed scope has been verified, not after reference
files have been copied.
