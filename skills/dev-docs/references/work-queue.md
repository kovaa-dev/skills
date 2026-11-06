# Work queues and delivered results

The queue requests work and links its owning contract, documentation, or question;
[requirements](requirements.md) retain their normative text. Use [maintenance](maintenance.md)
for intake/severity and [on-touch conversion](source-transition.md) when existing contract/work ownership needs reconciliation.

## One work item, one result boundary

A queue is a list of linked rows, grouped by useful headings. Each row has this form:

```md
- [Q-001 Establish a usable preferences representation](wiki/personal-preferences.md#representation-question) – ready
- [R-SYNC-001 Cross-device preferences](wiki/personal-preferences.md#r-sync-001) – planned
```

Keep only the ID, name/link, and delivery status in the row. Use the project's compatible
status tokens, separator punctuation, and inline-code styling if established.
Keep unaffected rows unchanged during a scoped conversion. Requirements, questions, context,
waits, owner, priority, delivery target, acceptance, dates, and verification belong at
the linked owning document/section. Reuse that owner; a row does not require its own file.
Do not turn queue entries into inline work cards or append a second context/status table.

A requirement ID may directly identify its initial delivery; no wrapper work item is
needed. A later work-bearing revision uses `<requirement-id>@<n>` under
[revision delivery](requirements.md#revision-delivery-and-history). Its block in the
requirement owns the status; register that block and its queue row in the same change.
The earlier completed delivery stays closed. Queue identity is the full delivery key,
so `R-MEDIA-001` and `R-MEDIA-001@2` are different deliveries of one requirement.
The requirement owns its delivery status; the queue explicitly repeats that status for
scanning. This is a required projection, not a second authority. Definition/acceptance
and implementation/verification remain distinct fields in the requirement.
For independent repair/research work, the linked work-context section owns its status;
its row repeats that value without changing the requirement's delivery status.
Research can live [inside the specification](documentation.md#research-alongside-requirements)
with its own ID, anchor, and status; a separate work row does not require a separate file.
A historical row always reads its own delivery/revision result, not the current
requirement's newest delivery status; do not overwrite history during reconciliation.
A separate repair against an unchanged requirement or an independent investigation uses
its own work ID under the project's [ID namespace](documentation.md#layers-and-id-namespaces)
and links its owning context; Q-001 is a fallback only when no convention exists. Do not
create both requirement and work rows for the same delivery merely to satisfy a schema. Several
requirements delivered together can share execution context without wrapper subtasks.

Register a separately useful requested/deferred outcome for the product, system, or its
users, or an independently actionable unresolved blocker/significant enduring risk.
Being an explicit instruction or an executed step alone is insufficient: ask what useful
outcome requires selection or follow-up beyond bookkeeping of the current work.
Required documentation capture, queue edits, migration notices, and closure recording
are supporting steps of that work; their performance does not itself create another
queued deliverable. Independently useful documentation, research, datasets, configurations,
and external results remain valid outputs under the same outcome test. Do not invent
product requirements, tasks, or artifact files merely to record having maintained records.

## Existing queues during transition

Reuse the project's existing queue or task index for existing and newly captured work. Place
new result-oriented entries alongside old entries in the relevant area/milestone;
link their requirements in the owning specifications rather than copying obligations
into the queue. Do not create another queue or duplicate the backlog merely because
some entries use the new model. Existing useful partitions may remain; migration state
alone is not a reason to separate work selection.

Listing/selecting an existing entry does not require advance migration of the backlog or
certify its readiness. Its unconverted contract and work remain in the old source until
the selected scope follows [on-touch conversion](source-transition.md). Capture new
requirements directly in their owners and register work only at the threshold above.

During conversion, replace the selected existing selection links with the covered
requirements/results, keeping one row per selected result and preserving delivery grouping,
history, incoming resolution, and any active remainder. Retain an existing work ID when
it still identifies the same result. If an aggregate task is replaced by extracted R-ID
rows or consolidated outcomes, keep its old ID accessible as a source/redirect with the
verified mapping; do not retain it as a second active delivery of the same scope.
A source work ID does not become a requirement ID by renaming. Conversion alone does not
require new Q-items. Split/consolidate only along actual result boundaries. For partial
conversion, name the exact converted/residual scope and their status owners at the linked
source; whole-source coverage still follows the transition protocol. Completed/cancelled
results retain the history described below.

This transition needs no generator, synchronization script, separate status register, or
permanent migration register. Use existing project checks; adapt real enforcement only
when it blocks the selected mixed format under [validator compatibility](validator-compatibility.md).

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

A short execution brief restores the selected result, sources, target, applicable/preserved
contracts where present, and checks. It can be a concise response or executor plan;
a separate brief document is not required. The initial user request may already authorize
this work; do not add a redundant confirmation merely for a status change. New choices
follow [decision governance](documentation.md#decision-approval).

When a contract applies, resolve its current revision/state and applicability before
execution under the [requirement lifecycle](requirements.md#current-contract-and-nonbinding-material).
Ready proposal-evaluation work is not authority to deliver an unaccepted replacement.
If the target changed or was retired, reconcile the unfinished entry before continuing;
keep historical completion against its original baseline.

Before starting/resuming work, read the linked owner and its applicable delivery
baseline; do not rely on the queue copy. If the statuses differ, the owner takes
precedence: repair the queue projection before proceeding. A missing owner status is
an explicit gap to resolve from actual evidence, not a reason to promote the copied
queue value silently.

For a status change, update the owner first and all affected maintained queue rows in
the same change. Before closure, verify that their values agree. A discovered runtime
discrepancy still requires reconciling the owner against evidence under normal rules.
Generated projections are optional; manual copying is supported and no synchronization
script is required. Ordinary Markdown links navigate to a source; they do not include
a live field value. Do not claim automatic synchronization without actual tooling.

## Dependencies and multiple queues

Implementation prerequisites belong to requirements. For each missing input, the linked
work context records the specific supplying work/condition, for example "Q-002 waits for
Q-001's accepted representation experiment". The queue row shows the waiting status.
Do not pretend that Markdown computes this mapping.
Keep the reason/result explicit; a done supplier is insufficient if its required result
was not actually delivered or is invalid for the target baseline.

Multiple queues/files are allowed by capability, team, work kind, or delivery group.
Each work item has one primary selection entry and one linked status owner. Other
queue views may repeat ID/name/link/status under the same reconciliation rule; plain
navigation links need no copied status. Repeated views do not represent separate work
or competing status owners. Use project-wide unique IDs and cross-queue links. Moving
an item preserves its ID and inbound navigation.

Queues do not block queues. Individual work waits on individual results across any
grouping; skip blocked items when choosing other ready work. Selection follows accepted
priority and resource/ownership constraints, not merely the first row of a file.

Keep the prerequisite graph acyclic. Requirements delivered together can be ordered
inside one item; if a real cycle exists, identify the minimum common contract or jointly
deliver the coupled result. A separate integration item is justified only by its own
verifiable outcome, not by a routine merge. Parallel execution/write isolation is owned
by project-work policy, not inferred from queue grouping.

## Completion, history, and current truth

Keep completed and cancelled rows visible in the queue's history or one linked archive
using the same ID/name/link/status format. Their linked result owns the completion
date/version, evidence, cancellation reason, and limitations where known. Historical done entries,
acceptance, and verification are not rewritten for a later regression or new scope.
A new repair can reference the same unchanged requirement and earlier delivery; it does
not need a duplicate requirement. A changed obligation that needs further work instead uses a revision delivery
row, preserving the original completed row and its baseline. Preserve uncertainty when
importing historical records.

The completed row links the actual artifact/result or its owning verification section.
The verification owner records requirements/baseline checked, method, observed result,
and material limitations. Product/manual acceptance follows the existing execution
policy; no inferred automation or relaxed gate is introduced by this skill.

If production behavior is the agreed target, a commit, green test, PR merge, tag, or
artifact upload alone does not complete delivery. Record the actual target version and
runtime acceptance as required by that contract. For research, done means an accepted
answer/experiment, not that the product requirement is implemented. For an external
action, require confirmation of the intended effect; retries must not blindly repeat it.

## Delivery interface

The executor receives the selected item, sources and applicable requirement revisions, preserved
contracts, input artifacts, acceptance/result destination, and authority/constraints.
The returned result identifies produced artifacts, checks, delivery target/version, and
remaining gaps. Keep retries/attempt logs outside the lean queue.

Delivery can use PRs, direct integration under checks, publication of a document/dataset,
or another authorized adapter. Do not prescribe a forge, runner, database, protocol,
autonomous deployment, or approval bypass. Multiple agents changing a shared boundary
need verification of the integrated candidate even when their items are independently ready.
