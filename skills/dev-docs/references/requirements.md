# Requirements and specifications

This is the canonical model for new and converted documentation. Apply
[documentation governance](documentation.md), [work queues](work-queue.md), and the
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

A requirement needs its ID, readable behavior/obligation, applicability, acceptance
method, and known state. Shared context/metadata can live at specification level.
Use only fields needed for this contract; no per-line IDs or universal empty header.

Distinguish:

- definition state: draft, accepted, superseded, or retired;
- implementation/verification state: unknown, not implemented, partial, verified, or
  violated, with a locator/version where established;
- work readiness: belongs to the queue, not the requirement's definition state.

A requirement can be accepted while implementation is unknown or not feasible yet.
Unclear desired behavior or acceptance remains draft with explicit questions.
Unavailable feasibility proof does not erase an already accepted obligation.
"Accepted" future behavior must state its activation/rollout condition; it does not
silently replace the current contract before that condition holds.

Keep the ID when clarifying or revising the same obligation. Record a semantic revision,
previous and new meaning, reason, date, and acceptance source when the contract changes.
Editorial corrections need not create a semantic revision. A new independently useful
obligation gets a new ID; a truly different replacement links to what it supersedes.

References in current prose use the stable ID/anchor. Verification and delivery records
identify the exact revision/baseline they checked. Do not carry an old green result
forward as proof of a changed requirement. A requirements change may need work; it does
not mechanically create a new queue entry or reopen a historical completed entry.

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
checks, unresolved assumptions, and any required decisions. Keep it with the work's
result or owning specification, not as a copied requirement catalog in the queue.
No tag/index/LLM guarantees complete discovery. Missing mapping or checks is a disclosed
gap; run broader affected checks when a concrete unresolved concern justifies them.

## Conflicts and importance

Before accepting a new or changed requirement, compare it with applicable accepted
contracts in the affected area. Compare actor, object, condition/mode, time/version,
observable result, bounds, and normative strength. Different modes or an explicitly
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

Keep material open questions next to the affected requirement/contract. A question's
answer may clarify an existing requirement, revise it, add an independent obligation,
or select a technical implementation; do not automatically create a requirement or
task for every answer.

The executor chooses routine reversible details within the agreed contract. A product,
public/data/ownership, or material operational change requires normal decision acceptance.
Use a separate investigation only when it has an independently useful result. After its
conclusion, update the relevant facts/questions and queue readiness; a negative feasibility
finding can complete research while leaving implementation unfulfilled.
