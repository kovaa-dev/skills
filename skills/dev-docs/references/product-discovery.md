# Product Discovery and Incremental Planning

The `discover` workflow turns an idea into an agreed minimum marketable product,
granular documents, and executable near-term work. It is not deployment infrastructure.
`init` connects the documentation system; `discover` shapes the content by applying the
[documentation rules](documentation.md) and [task tracker](task-tracker.md). It applies
to both a new product and a new capability in an existing product.

## Independence from init and write mode

`discover` does not require prior `init`, existing code, or a layer registry.
First determine the mode: discussion/read-only or authorized document creation.
In discussion mode, record conclusions in responses without creating files. In write
mode, follow the existing rules; if none exist, agree on the minimum paths and format
and create only the necessary documents. Do not choose the skill adoption method
implicitly: setup and verification can be requested separately through init or migrate,
including together with discover. Claim that information has been recorded in the project only after it has actually
been written. Layers emerge as technical boundaries are agreed, not
in advance.

## Delivery principle

Use iterative, incremental feature delivery: begin with
an intentionally simple but working vertical outcome, then extend it through useful
increments and revise it in response to feedback. Detail the nearest outcome enough for
execution; describe later outcomes only through known goals, risks, and open questions
(rolling-wave planning). Do not create a horizontal plan of “the entire backend, then
the entire frontend, then the product.” Scrum, sprints, and ceremonies are optional.

For a new product, propose the sequence `Alpha` → `Beta` → `RC` → `Release` → `Next`
by default, but agree it with the user: stages may be renamed, combined, extended, or
replaced with another clear sequence. A standard `Alpha` is the minimum usable outcome
and a technical proving ground; `Beta` provides the core capabilities while allowing
breaking changes; `RC` is for feature freeze, fixes, data recovery, and operational
readiness; `Release` contains the work required for the target or current publicly
supported boundary; `Next` covers subsequent capabilities and maintenance. A group
expresses queue intent, not proof of delivery.

For a commercial launch, use the Minimum Marketable Product (MMP) as the target: the
smallest offering suitable for real use and market entry. In the standard sequence,
this is the target for `Release`, not a requirement for `Alpha` to be complete. An MVP
emphasizes hypothesis validation; a prototype alone does not demonstrate commercial
product readiness. Do not promise sales or demand based on documentation.

For an existing product, first examine the behavior actually delivered, the current
supported boundary, and active documents and tasks. Then determine the current state
and future sequence with the user. Do not force a mature product to retroactively pass
through or label itself with `Alpha`/`Beta`/`RC`; do not invent an unknown historical
stage.

## 1. Idea and source facts

Identify the user and buyer, the problem, the existing way they solve it, the value of
the offering, and one target end-to-end scenario. Review existing documents and code,
if present; distinguish facts, requirements, and hypotheses. Existing code describes
an implemented fact, but does not automatically become an accepted requirement.
Unless a change has been explicitly accepted, preserve the current Surface, actor,
Action, Visible result, workflow, ownership, and data boundaries.
Do not require a complete business plan before starting: retain unknowns as open
questions. Register in the backlog only explicitly assigned ideas, agreed deferred work,
and unresolved independently actionable/high-risk questions that meet the tracker
threshold; leave other suggestions in the discussion summary without automatically
accepting them into the first release.

## 2. Solution grooming with the user

Before developing a new product, conduct overall initial grooming. It must establish the baseline direction for the work and
incremental delivery, the product direction, the minimum first usable outcome, and the
baseline technical decisions, boundaries, and constraints required to begin safely.
Place known work in the selected roadmap; before execution, detail only the nearest
stage.

Initial grooming is complete when the direction is
agreed, the nearest outcome has verifiable acceptance and clear dependencies, and the
required product and technical decisions allow work to begin without unacceptable
risk. Under the standard sequence, this means unblocking `Alpha`. Do not try to design
future stages or make every task-level decision in advance: that is not a readiness
criterion and would make grooming endless.

Continue grooming incrementally. Resolve an open
question as close to implementation as possible, but before its absence blocks the
nearest stage or makes implementation risky. Later groups retain direction, material
risks, dependencies, and open questions without premature detail.

Before implementing each PRD, conduct brief micro-grooming: reread the PRD, its sources,
and applicable decisions; re-establish the user, problem, and expected outcome; account
for the outcome and feedback from previous PRDs, new information, dependencies, and
open questions. Resolve only the questions required for the current PRD and nearest
stage. If new evidence invalidates an earlier choice, propose revisiting it and, after
agreement, explicitly record the previous decision, the new accepted decision, the
reason, the source, and the affected PRDs/TDs/ADRs; update the canonical contract before
implementing the change.

Micro-grooming is complete when the current PRD is once again clear, verifiable, and
safe to begin. It does not repeat full discovery, detail future PRDs, or require local,
reversible decisions to be accepted in advance. Such decisions may be made just in time
during development. A minimal backlog PRD containing an ID, source, hypothesis, owner
or `unassigned`, and open questions may be registered before grooming; until grooming
is sufficient, do not present it as an agreed product contract, invent scope/acceptance,
or begin implementation.

Discuss one small, cohesive group of questions at a time, starting with those that block
the nearest outcome.
Accompany every question with a recommended option, realistic alternatives, and their
consequences rather than presenting a questionnaire without helping the user choose.
For each decision, briefly assess:

- necessity: what real problem or material benefit justifies the decision;
- sufficiency: whether a simple option covers the scenario and constraints without
  unnecessary complexity;
- a simpler option, including doing nothing, deferring, or allowing a manual operation;
- basis: a requirement, fact, research finding, or unvalidated hypothesis;
- trade-offs: resulting value relative to implementation time, maintenance complexity,
  risks, reversibility, and the cost of delay;
- verification: an observable outcome; use measurements only when required to choose
  or substantiate a material promise, not as mandatory metrics for everything.

Apply the “Necessity, sufficiency, and proportionality of a solution” section of the
[documentation rules](documentation.md). Do not interpret a request for maximum
efficiency as permission to build the most complex solution or measurement
infrastructure.

Acceptance and recording of rationale follow the “Decision approval” section of the
documentation rules. The outcome of a discussion is one of: accepted, requires research,
deferred, or rejected with a reason. The agent explains a technical question in terms
of product impact and provides a recommendation; the user is not required to design the
solution independently.

## 3. Boundary of the nearest product outcome and commercial release

Propose the smallest complete scenario from user entry to receiving the outcome. For
each element, show why it is required now. The first usable outcome may already be a
commercial MMP, but a standard `Alpha` may be narrower: internal use or a limited group
for technical proving. Do not impose `RC`/`Release` requirements on it prematurely.

Separately determine which operational, security, data-recovery, and legal conditions
are already mandatory for the nearest use and which become gates for a later stage; do
not invent requirements for a specific jurisdiction. Minimal scope does not permit
unacceptable data loss or an unsafe system.

Do not automatically include in-app payments, every integration, scaling for
hypothetical load, or automation of rare operations. A manual workaround is acceptable
only after agreeing on load, responsibility, and constraints. Do not silently reduce
accepted requirements: the user approves the near-term scope and deferred scope.
Deferred work remains in the roadmap with stable IDs.

## 4. Layers and product slices

First identify and agree the actual layer responsibility boundaries required for the
nearest outcome. A layer evolves through a sequence of small technical tasks; its tasks,
contracts, and documents are not named after phases.

A PRD is a product task with a user outcome, not an executable assignment. A phase or
product slice is assembled in the PRD from technical tasks across layers; those tasks
are its executable children and contain local steps. The tracker defines composition
rules. A phase does not require completing an entire layer.
Do not structure delivery as “the entire backend, then the entire frontend, then
launch.” Every product slice provides a working
scenario. Blocking technical research may precede it, but is not called a commercial
outcome.

Illustration, not a ready backlog: the first slice takes minimum access from the
identity layer, a basic form from the interface layer, and data persistence from the
domain layer. The next slice adds invitations, new interface states, and the
corresponding contract. Layers accumulate detail; initial tasks do not become permanent
checklists. Create a separate card for every new independently acceptable outcome.

Check dependencies and the critical path. Propose removing optional dependencies from
the nearest slice, but do not bypass real prerequisites to meet a launch date. Agree
the PRD order, end-to-end acceptance, and readiness conditions for a real release.

## 5. Documents as decisions are accepted

Do not create a monolithic PRD, complete architecture, or detailed specifications for
the entire future product in advance. Create only the necessary granular cards and
decisions: a user outcome belongs in a PRD, a technical contract in a TD, a cross-layer
choice in an ADR, and work in a layer card. Rationale and agreement live with the
canonical source; other documents link to it. Do not create a second general decision
log.

For near-term work, agree only the applicable blocking, cross-layer, risky, or
difficult-to-reverse decisions, clear dependencies, and verifiable acceptance. Local,
reversible decisions may be made just in time during development. A later backlog may
contain direction and substantive open questions without detail or an accepted
decision. Document readiness does not mean implementation is complete or demand is
validated.

## 6. Transition to implementation and feedback

Before implementing the nearest slice, verify that:

- the user has explicitly agreed on the outcome, scope, and new product, cross-layer,
  risky, or difficult-to-reverse decisions required to begin safely, including
  intentional changes to the existing Surface, Action, Visible result, and workflow;
- all required parts of the end-to-end scenario are covered and optional parts do not
  block launch;
- layer tasks are small enough for independent verification and correctly linked;
- documents can be read through a targeted route without loading the entire backlog or
  unrelated neighboring topics;
- decision acceptance, product acceptance, technical verification, and release fact
  are not conflated.

Begin implementation only within work authorized by the user. After delivery, compare
the outcome with feedback and propose the next minimum increment. Transitioning to
maintenance does not require a separate PRD or a new product phase: all registered bugs,
findings, and ideas remain visible in the roadmap and follow the rules for
[maintenance and continuous development](maintenance.md). A change to an earlier
accepted decision must be agreed again; update the agreed documents in place while
preserving history.
