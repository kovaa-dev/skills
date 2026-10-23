# Product grooming and incremental delivery

Use [requirements](requirements.md), [queues](work-queue.md), and
[documentation governance](documentation.md). Selected old PRD/task work first follows
[on-touch conversion](legacy-transition.md). New discovery produces specifications,
questions, decisions, and work requests, not new legacy cards.

## Start with the nearest useful result

Discovery does not require init, an existing codebase, a layer registry, or a complete
business plan. Respect discussion/read-only mode; write only authorized content.
Distinguish facts, hypotheses, accepted obligations, and delivered behavior. Code can
establish an implementation observation without becoming the desired product contract.

Identify the user/buyer, problem, value, current behavior, and nearest end-to-end outcome.
Preserve the accepted interface, actor, workflow, ownership, and data boundaries unless
a change was authorized. Use small vertical increments rather than completing entire
technical layers before anything usable exists.

For a new product, propose/adapt Alpha, Beta, RC, Release, and Next only when useful:
early usable scope, core capabilities, stabilization, target supported release, and
future work. An existing product needs its actual current state and forward sequence,
not invented historical stages. Stages express queue intent, not requirements or proof
of deployment. A commercial minimum is the smallest offering fit for the agreed real use;
a prototype does not establish demand or launch readiness.

## Groom the contract and work separately

Grooming has two outputs:

1. A coherent specification: desired behavior/result, rationale, applicability, examples,
   constraints, acceptance, conflicts, implementation prerequisites, and open questions.
   Agreed obligations become accepted; uncertain desired outcomes remain draft and
   coherent alternatives awaiting a decision remain proposed.
2. A prepared queue: independently useful deliverables, priorities, exact prerequisite
   suppliers, owner/authority, target, and concise acceptance or links to its existing owner.

Shared rationale belongs in one named block. Requirements in different specifications
can refer to the same reason or decision without depending on one another. Check the
affected area for conflicting or duplicate obligations before accepting new ones.
Use the [proposal/retirement lifecycle](requirements.md#proposed-replacements) to review
candidates and stale material in the touched area without dropping accepted obligations.
Do not turn every grooming question into a work item.

Knowing what is wanted does not require knowing every implementation detail.
A material feasibility/representation question can produce ready research while delivery
waits for its accepted result. Routine reversible details are chosen by the executor.
Research can finish with an infeasibility finding; revisit the affected requirement
rather than silently weakening it or claiming implementation complete.

Resolve only the questions needed for the nearest safe, verifiable outcome.
Later work retains direction, risks, and questions without speculative design.
Discuss a small cohesive set, explain options and product consequences, and recommend
the simplest sufficient choice. Justify material complexity with facts and trade-offs;
do not make the user design the solution without assistance.

Readily available direct facts can support a local choice. Source-heavy, version-aware,
or conflicting-corpus questions use the [bounded research handoff](research-handoff.md).
Research support does not itself approve a decision.

## Start and respond to new questions

Start prepared work using [queue readiness and execution briefs](work-queue.md#state-and-readiness).
Keep the brief in the existing execution context rather than creating another document
by default.

When a question arises, determine its effect:

- clarify the same obligation and its examples;
- revise its accepted contract under the same ID, with a semantic revision and acceptance;
- add a separately meaningful requirement;
- choose a technical implementation without changing the agreed contract.

Keep material uncertainty with its owner. A missing answer/conflict puts only affected
work in need-info; a missing external result puts it in blocked with an observable wait.
Continue independent work. A new requirement need not create another queue item when
it belongs to the already accepted delivery scope; scope expansion still needs agreement.

## Feedback and ongoing development

Verify the combined end-to-end result, not merely technical sub-results. Capture the
artifact, actual target/version where needed, and verification against applicable
requirement revisions. User/manual gates follow the active execution policy.

After delivery, use observations to refine the next useful increment. Revise living
requirements while preserving old verification and completed work. A regression against
an unchanged requirement is repair work, not a reason to duplicate the requirement.
Use [maintenance](maintenance.md) for significant incoming issues and deferred outcomes.
