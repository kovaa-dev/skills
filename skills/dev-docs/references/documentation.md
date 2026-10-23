# Documentation governance

The work model uses [requirements/specifications](requirements.md), [work queues](work-queue.md),
decisions, and results alongside product/system descriptions and instructions. The old PRD/layer-task workflow is legacy:
[convert selected material before continuing](legacy-transition.md).
[Bootstrap](documentation-system-template.md) and [forms](documentation-registers-template.md)
apply these rules without becoming competing policy sources.

## Documentation purpose and ownership

Choose the material by the reader's question before selecting a form or creating IDs.
A document may contain clearly separated kinds of content; split only when their readers,
sources, or maintenance boundaries make that useful. These are responsibilities, not a
mandatory directory tree:

| Material | Question and canonical owner |
| --- | --- |
| Requirements/specification | What must hold, for whom, and under which conditions? [Requirement rules](requirements.md) own obligations and their acceptance. |
| System description/reference | How does the current product/system work? Architecture, API, data-model, configuration, and code descriptions own sourced implementation facts. |
| Guide/runbook | How does a reader use, operate, diagnose, migrate, or recover it? Own preconditions, ordered steps, expected results, limits, and recovery where relevant. |
| Rationale/decision | Why this goal or choice? The owning block or TD/ADR records reasoning and decision acceptance. |
| Work context | What does this execution need? An executor plan or existing work note/section holds useful reproduction, hypotheses, and implementation detail. |
| Result/verification | What was produced or checked? The appropriate result record/artifact owns observations, baseline, method, and limits. |
| Overview/navigation | Where is the answer and how do the parts fit? Own the reader's overview and links to detailed owners. |
| Queue | Which independently useful work is requested and in what state? [Queue rules](work-queue.md) own registration, readiness, waits, and history. |

Describing an existing API or updating a runbook does not by itself create a product
obligation. Source factual descriptions from the relevant code/configuration/interface,
observed behavior, or established sources; identify version and uncertainty where useful.
Recording a fact does not accept it as the desired invariant. If actual behavior conflicts
with an accepted requirement, distinguish the observation from the required behavior.

Update or create descriptions and instructions when a changed system or reader's actual
question makes them useful. Requirements and delivery records do not replace those
explanations. A documentation-only correction uses the existing owner without inventing
R-IDs or another Q entry inside already tracked work. Independently assigned/deferred
outcomes follow the queue's registration rule.

Canonical ownership prevents competing normative sources or work states. Overviews,
guides, and references may summarize and explain for their audience, linking to the
owning contract where it matters; they need not become link-only pages. Check their
accuracy together with affected sources.

## Work context and results

Keep durable product/system knowledge in its owning document, and the selected work's
state in its canonical queue entry. Keep short-lived plans, investigation trails, and
reproduction detail in the executor's working context or an existing relevant note/section.
Persist only what is needed for continuation, handoff, traceability, or a useful result,
within the existing write authority. A short context/acceptance note can fit inline in
the queue when sufficient; longer material is linked rather than copied into every view.

Do not force each repair to create an artifact file or append its incident history to
the specification. Create a separate document only for independently useful content.
Verification can live in an existing result, release, or relevant documentation section,
with the exact contract/source baseline and honest limits. Preserve useful findings in
the appropriate description, procedure, requirement, or decision.

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
Historical verification does not prove the current requirement revision. Working migration
coverage is control data; its checked mapping can remain historical source provenance.
Neither is a new evidence category or live tracker.
Classify existing generic evidence by meaning without inventing missing facts.

## Decision approval

Preserve explicit user decisions and binding project instructions. A new product/public,
ownership/data, architectural, or material operational choice needs a rationale and
acceptance source. Acceptance may come from the user, an authorized decision owner,
or application of a previously accepted policy within its stated bounds. Record the
applicable authority/source; stricter binding project/user requirements still apply.
The user may accept an unambiguous package or authorize a class of choices; do not
generalize a vague acknowledgment to unstated decisions.
Silence, a file, a passing test, or an agent recommendation is not user acceptance.

Routine reversible implementation details, editorial corrections, applying accepted rules,
and faithful on-touch capture of existing contracts are not new choices and do not
require renewed approval. Existing task-scoped authority covers necessary documentation
continuity. The initial request may already authorize the same work and execution brief.

Record the problem, selected option, relevant alternatives including deferral/simpler
options, necessity/sufficiency, consequences, verification/revisit conditions, and date/source.
If no stable discussion URL exists, preserve an accurate accepted statement and date;
do not fabricate a quotation or link. Use a named block when sufficient; a separate
TD/ADR is useful only for a genuinely independently maintained decision. Decision
acceptance can precede implementation; do not require verification that can only exist
after executing the accepted choice. Investigate essential feasibility questions separately.

When sources disagree, classify scope, applicability, acceptance, and historical versus
current state. Explicit new user decisions replace earlier ones only in their stated scope.
A proposal, later timestamp, technical choice, or code observation does not override an
accepted product obligation. Delivered behavior is a preservation default, not automatic
proof of the desired contract. Resolve [current, proposed, and obsolete material](requirements.md#current-contract-and-nonbinding-material)
before [conflict resolution](requirements.md#conflicts-and-importance);
do not select a convenient source or weaken another obligation for implementation convenience.

### Product decision history

Requirement identity, semantic revisions, applicability, and preserved meaning follow
[the requirement lifecycle](requirements.md#identity-state-and-revision). Work completion
and later regressions follow [queue history](work-queue.md#completion-history-and-current-truth).
Legacy facts follow [the transition rules](legacy-transition.md#history-and-unresolved-material).

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

Before marking work done, compare the delivered outcome with the agreed question/result,
applicable requirement revisions and decisions where present, preserved contracts, and
the delivery target. For descriptions/guides, check relevant sources, audience usefulness,
and examples/procedures as feasible; disclose unverified steps and source gaps.

- Resolve discrepancies with accepted obligations before closure: correct the result or
  obtain the normal accepted change. Source-backed factual/editorial corrections follow
  ordinary documentation maintenance.
- Update affected requirements, system descriptions/references, and user/operational
  instructions in the same workstream when their content changes or is needed.
- Reconcile [new/changed requirements and material questions](requirements.md#questions-during-work)
  received during the work, including capture before handoff; migration also checks
  [baseline coverage](legacy-transition.md#coverage-and-reconciliation).
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

One document covers one coherent reader question, explanation, contract, result, or
operational procedure. A technical layer does not justify a giant file; do not split
mechanically by line count or create a micro-file for each sentence.

Use the [purpose/ownership table](#documentation-purpose-and-ownership) to choose placement.
A requirement is addressable inside a specification; related content can share a document.
Guides and runbooks may explain ordered procedures, including migration and rollback.
Scheduling, assignees, progress, and completion of particular executions remain queue state.

Use descriptive filenames and readable headings. Only independently addressable records
need IDs; not every paragraph. Label links by purpose. Do not add universally mandatory
headers or empty template trees. Keep acceptance readable without a chain of unrelated
micro-documents.

### Minimum-context route

1. Read applicable instructions/settings; identify the reader's question, material type,
   and existing owner under [documentation purpose](#documentation-purpose-and-ownership).
2. For selected legacy work or an applicable uncaptured obligation, follow
   [on-touch conversion](legacy-transition.md). A factual description needs no invented requirement.
3. Read relevant sources and context for that material. When requirements/decisions apply,
   resolve their current revision, acceptance, and applicability under
   [the lifecycle](requirements.md#current-contract-and-nonbinding-material).
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

Maintain the owner selected under [documentation purpose](#documentation-purpose-and-ownership)
and [work-context placement](#work-context-and-results). A technical choice need not be
architectural, and a bugfix against a clear contract need not create a decision.

Use project checks for affected links, anchors, schema, and whitespace. Do not manually
run unrelated code checks solely for prose. Actual hooks/CI are governed by project-work
policy and must not be silently disabled. Do not invent unavailable commands/tools.

Follow the release policy for changelogs/versions; never manually edit generated fields
merely because documentation changed. Preserve history through accessible immutable
revisions when appropriate, with correct locators. Deletion needs explicit authority
and verified recovery; archived text does not remain active policy. Apply the
[stale-material lifecycle](requirements.md#retiring-stale-material) to remove obsolete
routes without discarding unresolved obligations or treating proposals as replacements.

Register significant unresolved/deferred bugs, findings, and assigned ideas under
[maintenance](maintenance.md). An optional findings register describes observations and
links remediation work; it does not copy work status or become another execution plan.
Separate observation, hypothesis, and confirmed cause.

Numeric conclusions affecting choices need reproducible inputs/assumptions/method.
A formula suffices for simple arithmetic; preserve a script only for a genuinely
repeatable/complex calculation. Maintain an existing code map for material structural
changes without duplicating requirements in it.
