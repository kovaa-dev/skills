# Work queues and delivered results

The queue requests outcomes against [requirements](requirements.md); it does not own
their normative text. Use [maintenance](maintenance.md) for intake/severity and
[on-touch conversion](legacy-transition.md) before continuing old task-based work.

## One work item, one result boundary

Use a short canonical entry with a stable project-wide ID, default Q-001, a result-oriented
title, status, and links to the relevant requirement/specification or artifact question.
Include owner, priority, work kind, delivery target, or an exact wait only when useful
for selecting/executing the work. Put shared owner/context at queue level where practical.

The entry may live inline in a shared Markdown queue; one file per item is not required.
Keep acceptance details, reasoning, implementation plans, research material, and full
verification beside the owning specification or result artifact. Link to them. A separate
artifact document is needed only when the result warrants it; a named section can suffice.

Work can implement several requirements or have no new product requirement: a repair,
investigation, documentation update, dataset, experiment, configuration, or external action.
Name the expected deliverable and how/where it will be accepted. Do not invent a PRD,
requirement, TD, or subtask hierarchy merely to fit work into a template.

Register explicitly assigned/deferred work, an independently actionable unresolved
blocker, or significant enduring risk. A local step or defect resolved within current
work stays there. Do not turn every conversation, question, or observation into a queue item.

## State and readiness

Use project-compatible tokens; these meanings are the default:

| Status | Meaning |
| --- | --- |
| backlog | A recorded outcome not yet ready/selected; known gaps remain explicit. |
| ready | Scope, acceptance/result locator, authority, owner, and required inputs are sufficient; no unmet external prerequisite. |
| in-progress | Authorized execution has actually started. |
| need-info | A material question/contract conflict prevents the affected work from continuing; name the needed answer. |
| blocked | A required artifact, implemented capability, environment, or other observable prerequisite is unavailable; link the supplier/condition. |
| done | The agreed result reached its target and applicable acceptance was completed; link the result. |
| cancelled | Work was dropped with a reason and, if applicable, a replacement link. |

An existing project may call ready work "planned"; keep its token when semantics match.
Grooming prepares requirements and work separately. Unknown implementation detail alone
does not make accepted requirements draft or require a separate research item.
A substantial feasibility question may make investigation ready while implementation
waits for its accepted result.

A short execution brief restores the agreed result, affected/preserved contracts, and
checks. The initial user request may already authorize this work; do not add a redundant
confirmation merely for a status change. New choices follow decision governance.

Before execution, resolve the linked contract's current revision/state and applicability
under the [requirement lifecycle](requirements.md#current-contract-and-nonbinding-material).
Ready proposal-evaluation work is not authority to deliver an unaccepted replacement.
If the target changed or was retired, reconcile the unfinished entry before continuing;
keep historical completion against its original baseline.

Do not duplicate canonical status in a card plus an index. If a project uses generated
views, they project the canonical entry. A manual secondary view contains links, not an
independently maintained copy of status, dependencies, or acceptance.

## Dependencies and multiple queues

Implementation prerequisites belong to requirements. For each missing input, the queue
also records the specific supplying work/condition, for example "Q-002 waits for Q-001's
accepted representation experiment". Do not pretend that Markdown computes this mapping.
Keep the reason/result explicit; a done supplier is insufficient if its required result
was not actually delivered or is invalid for the target baseline.

Multiple queues/files are allowed by capability, team, work kind, or delivery group.
Each work item has one canonical entry. Other appearances are links or actual generated
views. Use project-wide unique IDs and cross-queue links. Moving an item preserves its
ID and inbound navigation; avoid duplicates.

Queues do not block queues. Individual work waits on individual results across any
grouping; skip blocked items when choosing other ready work. Selection follows accepted
priority and resource/ownership constraints, not merely the first row of a file.

Keep the prerequisite graph acyclic. Requirements delivered together can be ordered
inside one item; if a real cycle exists, identify the minimum common contract or jointly
deliver the coupled result. A separate integration item is justified only by its own
verifiable outcome, not by a routine merge. Parallel execution/write isolation is owned
by project-work policy, not inferred from queue grouping.

## Completion, history, and current truth

Keep completed and cancelled work visible in the queue's history or one linked archive,
with result and meaningful completion date/version where known. Historical done entries,
acceptance, and verification are not rewritten for a later regression or new scope.
A new repair can reference the same unchanged requirement and earlier delivery; it does
not need a duplicate requirement. Preserve uncertainty when importing historical records.

A concise completion entry links the actual artifact/result and applicable verification.
The verification owner records requirements/baseline checked, method, observed result,
and material limitations. Product/manual acceptance follows the existing execution
policy; no inferred automation or relaxed gate is introduced by this skill.

If production behavior is the agreed target, a commit, green test, PR merge, tag, or
artifact upload alone does not complete delivery. Record the actual target version and
runtime acceptance as required by that contract. For research, done means an accepted
answer/experiment, not that the product requirement is implemented. For an external
action, require confirmation of the intended effect; retries must not blindly repeat it.

## Delivery interface

The executor receives the selected item, applicable requirement revisions, preserved
contracts, input artifacts, acceptance/result destination, and authority/constraints.
The returned result identifies produced artifacts, checks, delivery target/version, and
remaining gaps. Keep retries/attempt logs outside the lean queue.

Delivery can use PRs, direct integration under checks, publication of a document/dataset,
or another authorized adapter. Do not prescribe a forge, runner, database, protocol,
autonomous deployment, or approval bypass. Multiple agents changing a shared boundary
need verification of the integrated candidate even when their items are independently ready.
