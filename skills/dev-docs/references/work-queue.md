# Work queues and delivered results

The queue selects tasks; tasks link their owning contracts, documentation, or questions;
[requirements](requirements.md) retain their normative text. Use [maintenance](maintenance.md)
for intake/severity and [on-touch conversion](source-transition.md) when existing contract/work ownership needs reconciliation.

## One work item, one result boundary

A task is an execution record, separate from the contract it implements. It owns only:
ID and action, links to precise grounds/targets, execution status, actual dependencies
on other tasks/results, and result links. Optional assignee/priority/target are execution
metadata when the project uses them. A task does not own or copy product context,
rationale, criteria, bug reproduction, hypotheses, or decisions. These belong to linked
requirements, defects, questions, decisions, research, or results under
[documentation ownership](documentation.md#work-context-and-results).

A queue selects tasks using linked ID/name/status rows:

```md
- [Q-001 Investigate preferences representation](wiki/personal-preferences/work.md#q-001) – ready
- [Q-002 Implement cross-device preferences](wiki/personal-preferences/work.md#q-002) – blocked
```

The linked task is the status authority; the row repeats its execution status. Reuse
project task IDs and compatible status tokens. A task can be a compact section in an
existing file; it does not require a file or wrapper artifact of its own. Reuse an
existing task record and link it from the queue instead of creating a duplicate tracker. Topic navigation can
link these files without pretending that a whole topic has one delivery state.

Requirement IDs and revision keys identify contracts, not tasks. Link the exact target
revision/baseline from the task; a new bug against an unchanged contract does not create
a new requirement. A changed contract has its own revision and a task to deliver the
change. Research tasks link a question and its answer criteria instead of inventing a
product requirement. Code, documents, datasets, research, and external results are valid
outputs. One task may satisfy several coupled requirements; one requirement may need
several tasks. Split tasks only at independently useful, verifiable result boundaries.

For a task spanning several requirements, keep only links and distinguish their roles:
**implements** (selected obligations/deltas), **preserves** (material existing constraints),
and **depends on** (supplying tasks/results). Do not treat a related contract as a task
prerequisite or imply that every preserved requirement is being delivered again.
Target exact revisions or addressable sections when only part of a requirement is selected;
keep the scope and criteria at that owner, not as a paraphrase in the task. Link only what
is needed to define or materially constrain the coherent result, not the whole area catalog.

Close the task only when its entire selected implementation scope and affected preservation
checks are satisfied, with coverage recorded at the linked result. Partial success stays
explicit and remaining work stays selectable. A narrower completion requires an explicitly
agreed scope change and a linked disposition/task for the remainder; do not silently drop
requirement links to make a task done.

Register separately useful requested/deferred outcomes, independently actionable
blockers, and significant enduring defects/risks. Fixing a local defect within current
work requires capture and verification there, not automatically another task. Necessary
document maintenance and queue updates are supporting steps, not queued outcomes in
their own right. Do not manufacture a task for every criterion or every requirement.

Keep the queue lean; execution briefs are temporary executor context and do not replace
canonical knowledge. Closing or archiving a task must not hide needed product knowledge.

## Existing queues during transition

Reuse the project's existing queue or task index for existing and newly captured work. Place
new result-oriented entries alongside old entries in the relevant area/milestone;
link tasks to requirements in their owning specifications rather than copying obligations
into the queue. Do not create another queue or duplicate the backlog merely because
some entries use the new model. Existing useful partitions may remain; migration state
alone is not a reason to separate work selection.

Listing/selecting an existing entry does not require advance migration of the backlog or
certify its readiness. Its unconverted contract and work remain in the old source until
the selected scope follows [on-touch conversion](source-transition.md). Capture new
requirements directly in their owners and register work only at the threshold above.

During conversion, separate source knowledge from execution under
[task conversion](source-transition.md#convert-before-continuing). Preserve a task's ID,
status, and result boundary when unchanged; move its context to canonical owners and
replace it with links. Do not replace tasks with requirement rows. Split only independently
useful remaining outcomes and consolidate only actual duplicates, preserving historical
IDs, results, and redirects. Previously extracted requirements/results are reused, not
extracted again. A requirement-only selection entry becomes a task only when it represents
actual execution; pure contract listings become navigation.

Existing and converted work share the same queue/index. Conversion needs no parallel
tracker, generator, or permanent migration-mode flag. Unconverted selected sources remain
explicitly active until their meaning and work are accounted for.

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
| cancelled | Work was dropped with a linked reason and, if applicable, a replacement task. |

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

Implementation prerequisites belong to requirements. For each missing input, the dependent
task links the specific supplying work/condition, for example "Q-002 waits for
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
not need a duplicate requirement. A changed obligation that needs further work gets a requirement revision and a new
or updated unfinished task targeting it, preserving completed tasks and their baselines. Preserve uncertainty when
importing historical records.

The completed row still links its task; the task links the actual artifact/result or
its owning verification section.
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
