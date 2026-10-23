# Requirements and specifications

This reference owns the model for new and converted requirements/specifications.
Other documentation follows [purpose and ownership](documentation.md#documentation-purpose-and-ownership);
registered work follows [queues](work-queue.md), and selected legacy scope follows
[on-touch transition](legacy-transition.md). Legacy task schemas are not an alternative
for new work.

## Names and ownership

A **specification** is a Markdown document describing one coherent capability, domain
contract, or artifact/process contract. Use a descriptive stable filename and readable
title, such as personal-settings.md. An individual **requirement** is a separately
meaningful, verifiable obligation. It can concern product behavior, technical limits,
documentation, data, operations, or a process; it need not describe code.

A requirement says what must hold and under which conditions. "Conduct research" is
normally a [work request](work-queue.md), whose output may be an experiment and report.
A rule that every protocol change undergo compatibility research is a process
requirement; each concrete investigation is work.

Keep one canonical formulation per obligation. Specifications may group requirements
without becoming product tasks or lists of implementation steps. Split by independently
useful contracts, not one file per sentence or one giant file per technical layer.

## Identity, state, and revision

Use stable, readable IDs, default R-001, R-002, with project-wide uniqueness across
specifications. Numbers do not encode priority, phase, section order, or file position.
Never renumber on reorder/rename or reuse a retired ID. Preserve existing stable
requirement IDs when converting; do not copy a legacy task ID onto every extracted rule.

A requirement needs its ID, readable behavior/obligation, applicability, verification
method or an explicit method gap, and known state. Shared context/metadata can live at
specification level.
Use only fields needed for this contract; no per-line IDs or universal empty header.

Distinguish:

- definition state: draft, proposed, accepted, rejected, withdrawn, superseded, or retired;
  use the [lifecycle meanings](#current-contract-and-nonbinding-material) below;
- implementation/verification state: unknown, not implemented, partial, verified, or
  violated, with a locator/version where established;
- work readiness: belongs to the queue, not the requirement's definition state.

A requirement can be accepted while implementation, feasibility, or its verification method
is unresolved. Record missing verification methods as gaps; work readiness and completion
still follow [queue rules](work-queue.md#state-and-readiness). Keep unsettled behavior or
observable bounds as draft/questions separate from established accepted meaning.
"Accepted" future behavior must state its activation/rollout condition; it does not
silently replace the current contract before that condition holds.

Keep the ID when clarifying or revising the same obligation. Record a semantic revision,
previous and new meaning, reason, date, acceptance source, applicability, and affected
checks when the contract changes.
Editorial corrections need not create a semantic revision. A new independently useful
obligation gets a new ID; a truly different replacement links to what it supersedes.

References in current prose use the stable ID/anchor. Verification and delivery records
identify the exact revision/baseline they checked. Do not carry an old green result
forward as proof of a changed requirement. A requirements change may need work; it does
not mechanically create a new queue entry or reopen a historical completed entry.

## Recovering requirements from code

Recover undocumented requirements when asked to reconstruct a specification, or when the
selected work, audit, or migration exposes a relevant documentation gap. Scope recovery
to the affected capability; routine work does not require a repository-wide extraction.

1. Inspect the relevant reachable implementation paths and their callers, configuration,
   flags, and supporting tests. Recover observable behavior, actors/data boundaries,
   conditions, exceptions, errors, and meaningful constraints. A function, private
   algorithm, unused branch, comment, or test fixture is not automatically a requirement.
2. Match each recovered meaning against existing contracts. Reuse the owning R-ID and
   add implementation provenance when it supports that obligation. For a missing
   independently meaningful contract, write a readable requirement in its owning specification;
   keep descriptive implementation facts in their own documentation. Do not stop at an
   unpersisted finding when the documentation write is authorized.
3. Mark a newly recovered requirement **Origin: recovered from code**. For existing
   requirements, retain their origin and add **Implementation sources**. Record repository-relative
   source paths with symbols or useful line locators, and the actual inspected baseline
   (commit SHA or exact snapshot/digest). For uncommitted code, preserve or identify the
   inspected scoped content rather than citing HEAD as its version. Distinguish implementation,
   test expectations, configuration, comments, and inferred meaning; label unsupported
   rationale/intent as unknown or inferred. A separate source registry or code mirror is not required.
4. Keep implementation origin separate from acceptance source. A coherent recovered
   obligation without established agreement is proposed; incomplete meaning stays draft
   or an explicit question. Record it without waiting for adoption approval, using
   [ongoing capture](#questions-during-work). Existing acceptance or an applicable accepted
   preservation policy may establish its binding scope; cite that authority separately.
   Code, comments, and test expectations alone do not establish agreement. When implementation
   contradicts an accepted requirement, record the actual deviation under [maintenance](maintenance.md);
   do not rewrite or downgrade the agreed obligation.
5. Separate source inspection from execution evidence. Reading code or a test does not
   establish a passing check, deployed behavior, or support for every mode. Record checks
   actually run and their baseline, plus uninspected paths and material uncertainty.
   Code absence does not retire an accepted obligation or recover unimplemented intent.

Keep recovered behavior readable without opening source code. Code-derived candidates
need no legacy conversion map merely because they were undocumented. Existing legacy
documents still require their own coverage; code recovery does not substitute for reading
or preserving their requirements, questions, and history. Register separate work only
under the normal queue threshold.

## Current contract and nonbinding material

Definition state is not a work status. Use compatible project tokens with these meanings:

| State | Meaning and use |
| --- | --- |
| draft | Desired behavior or observable bounds are unsettled or unagreed; not a binding obligation. |
| proposed | A coherent candidate awaiting a decision; may intentionally contradict the current contract. |
| accepted | Agreed obligation, binding only for its stated applicability and activation condition. |
| rejected | A candidate was considered and declined; retain the reason/source. |
| withdrawn | A candidate was dropped without becoming a binding obligation; retain the reason/source. |
| superseded | An accepted obligation/revision was replaced in a stated scope; link the successor and handoff boundary. |
| retired | An accepted obligation ceased to apply without a successor; record the accepted reason and boundary. |

Apply this distinction to requirements, decisions, and the rationale they cite. A proposal
in an accepted specification needs its own explicit nonbinding state; it must not inherit
acceptance from the file. An archive directory or old date alone does not establish state.

Before starting/resuming work or using any found text as authority, resolve its canonical
owner, definition state, acceptance source, revision, and applicability. Follow replacement
notices to the current owner. Missing/looping redirects or incompatible successors leave
only the affected authority question unresolved. Search snippets, old tasks, copied checklists, and cached
context are locators, not independent authority. Read enough surrounding metadata to
distinguish current text from candidates and history. Recheck at a material contract change;
do not let an earlier context snapshot override an accepted update.

Only accepted obligations applicable to the target baseline constrain ordinary delivery.
Draft/proposed alternatives and rejected/withdrawn/superseded/retired text can explain a
choice or investigation; they do not reintroduce obligations into that baseline.
Unknown or contradictory acceptance/applicability remains an explicit question: do not
pick the newest file, trust the folder name, or infer retirement from implementation.

An accepted future replacement must state the handoff condition. Keep the previous
contract applicable until that condition holds, and retain it for older supported
versions/modes where needed. Mark supersession per affected scope/baseline rather than
globally disabling an obligation still required elsewhere. Historical acceptance and
verification retain their original revision and scope.

Classify an apparent contradiction before resolving it: two current obligations need
[conflict resolution](#conflicts-and-importance); a candidate versus the current contract
needs a proposal decision; obsolete text versus the current contract needs route/history
cleanup. Do not present all three as competing current requirements.

## Proposed replacements

Keep an unaccepted change separate from the accepted formulation. A candidate revision
of the same obligation can be a named subsection or proposal document targeting the
existing ID and semantic revision; do not overwrite the accepted text or issue a second
current R-ID merely for a competing wording. A genuinely different replacement may
have its own requirement ID. A technical alternative belongs in its decision owner.

State the candidate's target ID/revision and scope, proposed behavior, rationale, material
questions/decision criteria, and pending acceptance. Use a relation such as "proposes to
replace", not an effective "supersedes". Link back to the current contract. Add an owner
or revisit trigger when known/useful; do not create a new registry or queue entry for
every idea. Rejected/withdrawn alternatives remain nonbinding history with their reason.

A conflicting proposal alone does not block repair or implementation of the current
accepted contract. Evaluation/research may be ready independently, and an explicitly
authorized experiment may explore the candidate; neither accepts it for ordinary
delivery or waives the current production contract. A queue priority/status, completed
experiment, promising benchmark, or proposal timestamp is not acceptance.

When the decision is made, first compare the candidate against the then-current target
revision and preserved obligations; an old baseline must not silently undo intervening
changes. Record acceptance or rejection/withdrawal at the owning contract/decision.
For an accepted change, publish the semantic revision or successor, acceptance source,
scope and activation boundary, then reconcile affected checks, references, and unfinished
work. Supersede the prior meaning only where/when the accepted handoff applies. Reopening
a rejected/withdrawn alternative requires an explicit new review, not incidental retrieval.

## Retiring stale material

Review touched material during ordinary work/grooming, affected contract changes, and
scoped audits/migrations. Do not require a full backlog sweep or periodic service.
Age, lack of recent implementation, an abandoned task, or a new proposal does not
authorize retiring an accepted obligation; use an accepted replacement/retirement,
an already accepted expiry condition, or an authorized decision.

Within the affected scope:

1. Establish whether the text is still applicable, a duplicate projection, a candidate,
   or history. Preserve unresolved unique obligations/questions rather than calling
   inconvenient content garbage. If current authority is unclear, resolve only the
   affected decision/work; do not silently downgrade the requirement.
2. For established supersession/retirement, record state, reason/date/source, affected
   scope, and successor or explicit no-successor outcome at the original ID/anchor.
   Keep a visible historical/nonbinding notice beside retained old text or on its
   archive page. Preserve stable IDs, inbound links, and meaningful history; do not
   reuse IDs or delete sources without the normal cleanup authority/recovery.
3. Update affected active navigation, instructions/templates, copied summaries, and
   current-contract links to the canonical owner. Keep proposal and history routes
   visibly separate where they exist; same-file sections are sufficient. Existing
   search/index tools may filter them from default current-contract views, but the
   agent must still check state when retrieving them. No new tool is implied.
4. Reconcile unfinished work and prerequisite links against the applicable replacement:
   reuse/re-scope existing entries, or cancel obsolete work with a reason. Preserve
   done/cancelled results and verification of the original baseline; never turn them
   into proof of the replacement. Identify needed check/code changes as work rather
   than claiming that a documentation edit changed the implementation.

Correcting a proven stale route or recording an already accepted retirement needs no
new product decision. Deciding that a still-accepted obligation should be dropped does.
Repeated cleanup follows the existing current owner/notices without duplicating records.

## Shared rationale and decisions

Store shared rationale once in a named section of the appropriate specification or
thematic wiki page. Link to it from each applicable requirement. A stable WHY-001 ID is
optional when the block needs independent references; do not mandate a rationale file
or ID for every paragraph. Preserve the factual source or accepted goal honestly.

Rationale explains why and does not introduce hidden obligations. A choice between
alternatives is a decision: keep the chosen option, alternatives, consequences, acceptance
source, and revisit condition under [decision governance](documentation.md#decision-approval).
Existing TD/ADR records can remain canonical and active. Decisions explain the selected
solution; the independently verifiable obligations remain explicitly addressable.

## Applicability and common contracts

Identify the capability/domain affected, actor/data owner, conditions or modes, and
activation/version boundary where relevant. Default shared applicability at specification
level and override locally only when needed. Examples are account versus workspace,
online versus offline, active versus background, or current versus future rollout.

Put shared behavior in one owning specification and reference it from feature-specific
specifications. For example, date labels and filters can share the personal-settings
contract for propagation, offline convergence, authorization, and isolation. They retain
their own independent formatting/filter requirements.

Do not manually connect every pair of similar requirements. Relate them through the
affected capability/public interface and shared constraints. Same words, filenames, or
code ownership alone do not establish logical dependency or semantic equivalence.

## Prerequisites and impact

Store an actual implementation prerequisite at the dependent requirement: "R-002 needs
the verified capability defined by R-001", including the necessary portion/result when
only part is needed. Keep prerequisite, constrains/applies-to, shared rationale, and
supersedes links distinguishable. An ordinary reference is not a blocker.

The [queue](work-queue.md#dependencies-and-multiple-queues) records which work currently
supplies a missing prerequisite. Requirements describe a durable dependency; queue waits
describe the current execution plan. An already available prerequisite needs no new work.
When both requirements are delivered by one item, order them within that work instead
of creating a self-blocking queue dependency.

For a proposed change, identify obligations it implements/changes and existing obligations
it must preserve. Start with affected components and their contracts, then check relevant
consumers and cross-cutting security, ownership, durability, and operational constraints.
Maintain useful requirement-to-code/test links in their owning sources; derive reverse
views/search rather than maintaining duplicate manual registries.

A short impact result lists affected IDs/revisions, preserved obligations, selected
checks, unresolved assumptions, and any required decisions. Place it with the relevant
work context or result under [documentation ownership](documentation.md#work-context-and-results),
not as a copied requirement catalog in the queue.
No tag/index/LLM guarantees complete discovery. Missing mapping or checks is a disclosed
gap; run broader affected checks when a concrete unresolved concern justifies them.

## Conflicts and importance

Before accepting a new or changed requirement, resolve the
[current contract and nonbinding material](#current-contract-and-nonbinding-material),
then compare it with applicable accepted contracts in the affected area. Compare actor,
object, condition/mode, time/version, observable result, bounds, and normative strength. Different modes or an explicitly
superseded revision are not simultaneous contradictory obligations.

Separate obligatory conditions from optimization goals/preferences. A strict cost
budget can be obligatory; "reduce cost" may be an optimization goal. Do not assume a
universal ordering of security, freshness, UX, and cost, invent a budget/SLA, or treat
a high queue priority as authority to violate another accepted requirement.

If two applicable accepted obligations cannot hold together:

1. Show both formulations, sources/revisions, and the shared scope.
2. Explain the incompatible outcomes and provide feasible alternatives with consequences
   and measurements where needed.
3. Obtain the accepted trade-off from the authorized decision owner, or apply an already
   accepted policy that unambiguously covers it. A proposal, newest file, or convenient
   implementation does not silently win. Follow binding higher-level instructions.
4. Revise/supersede the affected contract and its checks together, preserving history.
   Block only the affected work until resolution; continue independent work.

A user may explicitly replace an earlier choice, but do not generalize that decision to
unstated scopes or erase unrelated obligations. Tools can detect structural/numeric
conflicts and suggest semantic candidates; successful lint or an agent review is not
proof of universal consistency.

## Questions during work

During authorized write work, capture material new/changed requirements and open questions
as they arise, before dependent implementation and no later than closure or handoff.
This includes input received while converting legacy sources, discoveries in implementation,
and answers that change scope. Read-only discussion records the proposed capture in the
response; do not claim it persisted in project documentation.

1. Preserve the actual input/source and date/locator where available; distinguish a user's
   decision, a proposal, an observation, and an executor's hypothesis. No stable chat URL
   means an accurate statement/source summary, not a fabricated citation or approval.
2. Match meaning against the current owner. Clarification updates the same obligation;
   a changed contract follows [semantic revision](#identity-state-and-revision); an
   independent obligation gets a new ID. A proposed replacement targets the existing
   revision; an unsettled question stays explicit at its owner. Facts, research requests,
   and routine implementation choices follow their own material type rather than becoming
   fictional product requirements.
3. Capture enough known behavior/scope, rationale/source, definition state, and uncertainty
   to retain the intent. Record missing implementation or verification detail under
   [definition and verification state](#identity-state-and-revision); do not discard the
   input, promote an unclear alternative, or invent agreement to complete a template.
4. Keep a concise input-to-owner locator in existing work context when needed to verify
   capture, then update the canonical document. No separate inbox, permanent duplicate
   catalog, or Q entry per requirement is required. Queue registration remains independent.
5. Before dependent execution and at closure/handoff, reconcile material inputs since the
   last captured baseline: each has its updated/new canonical destination or a visible
   unresolved question with source and next needed answer. Do not leave agreed obligations,
   scoped exceptions, or material pending requirements only in chat, a local plan, or a
   completed queue note.

The executor chooses routine reversible details under [decision governance](documentation.md#decision-approval).
Use a separate investigation only for an independently useful result. After its conclusion,
update relevant facts/questions and queue readiness; a negative finding may complete
research while leaving the obligation unfulfilled.
