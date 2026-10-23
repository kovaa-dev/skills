# Documentation governance

The current model is [requirements/specifications](requirements.md), [work queues](work-queue.md),
decisions, and result artifacts. The old PRD/layer-task workflow is legacy:
[convert selected material before continuing](legacy-transition.md).
[Bootstrap](documentation-system-template.md) and [forms](documentation-registers-template.md)
apply these rules without becoming competing policy sources.

## Necessity, sufficiency, and proportionality of a solution

Choose the simplest sufficient solution justified by the accepted result, implementation
time, and long-term maintenance. "Optimal", "reliable", and "room to grow" do not authorize
unbounded complexity, premature architecture, or scope expansion.

Explain material choices proportionately: a short rationale can suffice for a local
choice; costly/risky choices need alternatives and consequences. Do not invent precise
estimates. Measure only when the result can change a decision, acceptance, or material
risk assessment. Preserve the claim, sufficient method, observed result, and limits;
do not build a benchmark merely to make documentation look rigorous.

## Evidence vocabulary

| Purpose | Term | What it establishes | Owner |
| --- | --- | --- | --- |
| Support for factual claims | Research support | Identified sources, versions/locators, conflicts, coverage limits | Bounded research result or original artifact |
| Agreement on a contract/choice | Acceptance source | Who accepted what, when, and on which stated basis | Requirement/specification, decision, or accepted settings |
| Confirmation of a checked result | Verification record | Method, observed result, applicable revision/environment, limitations | Owning specification/result artifact or release record |

Research support does not accept a choice; acceptance does not prove implementation.
Historical verification does not prove the current requirement revision. Migration
coverage is temporary control data, not a new evidence category or live tracker.
Classify existing generic evidence by meaning without inventing missing facts.

## Decision approval

Preserve explicit user decisions and binding project instructions. A new product/public,
ownership/data, architectural, or material operational choice needs a rationale and
acceptance source. The user may accept an unambiguous package or authorize a policy that
covers a class of choices; do not generalize a vague acknowledgment to unstated decisions.
Silence, a file, a passing test, or an agent recommendation is not user acceptance.

Routine reversible implementation details, editorial corrections, applying accepted rules,
and faithful on-touch capture of existing contracts are not new choices and do not
require renewed approval. Existing task-scoped authority covers necessary documentation
continuity. The initial request may already authorize the same work and execution brief.

Record the problem, selected option, relevant alternatives including deferral/simpler
options, necessity/sufficiency, consequences, verification/revisit conditions, and date/source.
If no stable discussion URL exists, preserve an accurate accepted statement and date;
do not fabricate a quotation or link. Use a named block when sufficient; a separate
TD/ADR is useful only for a genuinely independently maintained decision.

When sources disagree, classify scope, applicability, acceptance, and historical versus
current state. Explicit new user decisions replace earlier ones only in their stated scope.
A proposal, later timestamp, technical choice, or code observation does not override an
accepted product obligation. Delivered behavior is a preservation default, not automatic
proof of the desired contract. Follow [conflict resolution](requirements.md#conflicts-and-importance);
do not select a convenient source or weaken another obligation for implementation convenience.

### Product decision history

Living requirements keep stable IDs and change through accepted semantic revisions.
Record old and new meaning, reason, date/source, applicability, and affected checks.
A changed obligation does not require a replacement PRD or a new task containing the
same product requirement. A genuinely independent obligation receives its own ID.

Completed queue results and original verification remain historical. A new regression
or changed scope creates new work when it crosses the registration threshold; it does
not reopen a done entry or rewrite its result. Preserve legacy closure/history under
[the transition rules](legacy-transition.md#history-and-unresolved-material).

## Project documentation consistency check

For audit, migrate, update, and affected contract changes, compare related project docs
with one another before comparing their format to the skill. Include every relevant type,
regardless of directory: specifications, decisions, queues, legacy PRDs/tasks, research,
verification, operational/product/marketing docs, README, instructions, and templates.
A full check covers the agreed full scope; ordinary work checks the affected contracts
and consumers without reading the whole repository.

Classify actual meaning: obligation, rationale/decision, work, source fact, verification,
navigation, or historical material. Keep one canonical owner and distinguish accepted,
proposed, current, future, and superseded. Compare actors, surfaces/actions/results,
conditions, data boundaries, interfaces, dependencies, and operational constraints.

Show contradictory formulations with exact locators, applicability/revision, practical
effects, and feasible alternatives. An unresolved accepted conflict blocks only affected
work. Update its accepted resolution, links, and checks together; proposals do not silently
win. Traceability and lint find some problems but do not certify semantic completeness,
underlying factual truth, security, or product behavior.

For source-heavy factual uncertainty, use [bounded research handoff](research-handoff.md);
keep the affected conclusion open rather than expanding a documentation check into an
unrequested corpus research workflow.

## Implementation closure reconciliation

Before marking work done, compare the delivered outcome with applicable requirement
revisions, accepted decisions, preserved contracts, and the agreed delivery target.

- Material discrepancies require a recorded decision, not an undocumented implementation detail.
- Update affected canonical documentation in the same workstream.
- Keep superseded meaning/reasons/acceptance accessible; Git history alone is not the
  explanation for why the current contract replaced an accepted one.
- The queue links to the actual result and its verification; it does not copy the specification.
- Missing decisions use need-info; a missing required result uses blocked with an exact
  wait. Do not claim completion or production delivery from a file/commit/tag alone.
- Routine details do not generate new documents merely for this reconciliation.

If a discrepancy is discovered after completion, preserve the old record and plan necessary
corrective work against the same requirement or its explicitly accepted revision.

## Rules source and project settings

Routine work does not require init or adopting this skill as project governance.
Use the [maintenance contract](adoption.md#routine-maintenance-without-adoption).
Compatible paths, language, IDs, and explicit project constraints remain intact; selected
legacy content still follows bounded on-touch conversion where authorized.
A binding no-migration/old-format instruction is a real conflict to disclose, not permission
to create a hidden parallel tracker.

For explicit governance adoption use a complete project-local copy or a pinned public
source. Keep only necessary settings in an existing project document:

- specification/wiki and queue entrypoints, decision/result/history locations;
- stable ID namespaces, compatible metadata language, and selected checks;
- optional delivery grouping and handling of completed/cancelled entries;
- accepted scope/ownership boundaries and scoped exceptions;
- a reproducible immutable public source when that adoption method was chosen.

A technical layer is optional context, not a mandatory task namespace or separate team.
Example paths do not imply a vendor, service, SLO, budget, jurisdiction, or platform.
Preserve unknowns as questions; coordinate schema changes with actual parsers.

## Granularity of any document

One document covers one coherent contract, independently useful question/result, or
operational procedure. A technical layer does not justify a giant file; do not split
mechanically by line count or create a micro-file for each sentence.

| Material | Unit and placement |
| --- | --- |
| Specification | Related requirements for one capability/contract; shared context once |
| Requirement | Separately meaningful obligation with stable ID/anchor inside its specification |
| Queue entry | One independently useful result boundary; inline entries are sufficient |
| Shared rationale | Named block in its owning specification/thematic page |
| Decision | One choice and its consequences; TD/ADR only when useful independently |
| Research/report/dataset | One question or produced result; large inputs/logs remain linked artifacts |
| Verification | Checks of identified contract revisions/results, beside the specification/artifact |
| Navigation/code map | Routes, responsibilities, interfaces, and references; no second contract/work state |
| Release record | Actual delivered version/target and verification, not a future plan |

Use descriptive filenames and readable headings. Only independently addressable records
need IDs; not every paragraph. Label links by purpose. Do not add universally mandatory
headers or empty template trees. Keep acceptance readable without a chain of unrelated
micro-documents.

### Minimum-context route

1. Read applicable instructions/settings and locate the selected outcome.
2. If legacy/uncaptured, follow [on-touch conversion](legacy-transition.md) before continuing.
3. Read the owning requirement/specification, acceptance, rationale/decisions, and direct
   prerequisites needed for this result.
4. Identify changed/preserved contracts and relevant consumers, including cross-cutting
   ownership, security, durability, and operational constraints.
5. Use headings/search and targeted locators; load only relevant versions/history and
   retain useful verified context instead of rereading the entire graph.
6. Reconcile actual results and report concise outcomes, checks, and remaining gaps.

When moving/splitting material, preserve identities, inbound links, meaningful source
content, and verification. Use copy/move plus local edits where safer. Keep one active
formulation and a usable reading route. Source-to-destination coverage is scoped under
[migration](governance-migration.md), not a permanent extra registry.

## Maintaining documentation changes

Within authorized work, preserve agreed obligations, assigned/deferred outcomes, and
material questions. Do not turn every remark or idea into a requirement/work item.
Discussion/read-only mode writes nothing. A later write grant captures only the agreed
scope, not every prior conversation.

Specifications own obligations and acceptance; rationale/decisions own reasons and
choices; queues own work state and concrete waits; artifacts own produced content and
verification. Overview pages link to these owners. A technical choice need not be
architectural, and a bugfix against a clear contract need not create a decision.

Use project checks for affected links, anchors, schema, and whitespace. Do not manually
run unrelated code checks solely for prose. Actual hooks/CI are governed by project-work
policy and must not be silently disabled. Do not invent unavailable commands/tools.

Follow the release policy for changelogs/versions; never manually edit generated fields
merely because documentation changed. Preserve history through accessible immutable
revisions when appropriate, with correct locators. Deletion needs explicit authority
and verified recovery; archived text does not remain active policy.

Register significant unresolved/deferred bugs, findings, and assigned ideas under
[maintenance](maintenance.md). An optional findings register describes observations and
links remediation work; it does not copy work status or become another execution plan.
Separate observation, hypothesis, and confirmed cause.

Numeric conclusions affecting choices need reproducible inputs/assumptions/method.
A formula suffices for simple arithmetic; preserve a script only for a genuinely
repeatable/complex calculation. Maintain an existing code map for material structural
changes without duplicating requirements in it.
