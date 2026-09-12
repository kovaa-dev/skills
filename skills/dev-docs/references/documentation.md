# Documentation Governance

Canonical documentation governance, independent of repository name,
tooling, and the presence of `RULES.md`. The format of tasks and decisions is defined by the
[task tracker rules](task-tracker.md). The [bootstrap guide](documentation-system-template.md)
and [forms](documentation-registers-template.md) help apply the governance rules,
but do not override them.

## Necessity, sufficiency, and proportionality of a solution

Choose the simplest sufficient solution justified by the final outcome,
implementation time, and long-term maintenance complexity. This is not a requirement to always
choose the fastest option: consider operations, risks, and future changes,
but do not build complexity for hypothetical needs.

Phrases such as “as efficiently as possible,” “optimal,” “reliable,” or “with room to grow” do not permit
unbounded complexity, premature optimization, or scope expansion.
Compare the practical benefit of added complexity with development time and the cost of
adoption, maintenance, and dependencies. If a simple option satisfies the accepted
requirements and constraints, prefer it; a more complex option requires
a concrete rationale, not an appeal to an abstract best practice.

The rationale must be proportional to the choice: a few sentences
are sufficient for an obvious local decision, while an expensive or risky one requires a comparison
of options. Do not invent precise estimates of time or benefit without data.

Verifiability does not mean that a numeric metric is always required. Measurements are needed when they
affect the choice or substantiate a material claim: for example, performance,
cost, load, or a claimed optimization effect. In that case, choose the minimum
set of measurements and a meaningful criterion based on available data; agree on unknown
thresholds rather than inventing them. In other cases, an observable
scenario, test, or reasoned comparison is sufficient. Do not add KPIs, telemetry,
benchmarks, numeric targets, or separate measurement infrastructure indiscriminately.
This does not waive mandatory correctness and security checks.

## Decision approval

Every product, architectural, or technical decision
recorded in documentation must include a rationale and explicit acceptance by the user.
A routine reversible implementation detail that does not change behavior, the public contract,
a data/ownership boundary, a dependency/runtime default, or the operating model does not
require a separate decision document or approval. Until accepted, an actual choice is a
proposal/open question, not a binding contract. An agent cannot accept
its own recommendation on the user's behalf. Silence, a successful check, creation
of a file, or a general request to “build the product” does not constitute approval of a specific choice.

When sources conflict, apply this priority: the user's most recent direct decision;
an accepted canonical product source; the actually delivered UX as the preservation default,
but not automatically as the desired requirement; an accepted technical decision; an implementation
fact; a proposal/inference. Code alone does not become an accepted product invariant.
Escalate conflicts between higher-priority sources to the user; do not choose the most convenient interpretation.
A decision that changes the Surface, Action, Visible result, actor, workflow, or ownership
requires precise confirmation of those changes so that the technical target does not override
the product interface.

In a canonical decision document, preserve: the problem, the selected option, alternatives
(including the simpler option/deferral), necessity and sufficiency,
consequences, verification method, and user confirmation with date/source.
If there is no stable link to the discussion, preserve a concise, exact statement
of the accepted choice and the date; do not invent a URL or quotation. For requirements,
acceptance may be sourced from an explicit user instruction. A related package may be accepted
if its contents and options are listed unambiguously; do not extend a vague “OK”
to unmentioned decisions. Do not require a separate ADR for every choice: the rationale
remains in the corresponding PRD, TD/ADR, or settings section.

Applying accepted rules is not a new decision: registering a card,
assigning a preliminary severity under the scale, and ordering work under an accepted policy
do not require separate approval for each step. A new technical choice,
a change to product scope, or an exception to an accepted policy requires
approval. If ambiguous, preserve the preliminary assessment and the question;
do not present it as an accepted exception. Organizational actions are performed
within the request and project authority, rather than requiring approval merely because
any card was changed.

Do not ask for approval again when conditions have not changed. Before implementing
each PRD, micro-grooming restores context and checks for new information after
previous results; it does not require reconfirming decisions that remain current.
An editorial correction, a move with no change in meaning, and execution of an accepted contract are not
new choices. First propose any elaboration that changes behavior, scope, data, or constraints
to the user; until the response, a proposed document may be prepared, but the choice must not
be implemented as accepted. New information may justify a decision that conflicts with
an earlier one: after approval, preserve the previous and new formulations, the reason, the source, and
the affected documents without silently rewriting history. The workflow is defined by
[product discovery](product-discovery.md).

### Product decision history

If an accepted product choice changes before its owning PRD is closed, add a concise
`Decision changes` section to it: previous accepted formulation → new formulation, reason, date, and exact
source of confirmation. The section appears only when an actual revision occurs and is not
a log of internal editorial changes.

A PRD with status `done` remains an immutable historical task. A change
to a delivered user-facing result is recorded as a new PRD with a `Replaces` field and
a link to the previous one; do not create a separate ADR solely for a product choice. A cancelled PRD
may be returned to active work while preserving the cancellation reason and the basis for resuming it.
The roadmap shows each card exactly once: `done` remains in the last
assigned delivery group or is moved to `History`, while the new PRD appears in
its own active group. The new link establishes continuity but does not rewrite
the closure of the old task.

## Project documentation consistency check

For `audit`, `migrate`, and `update`, first compare project documents with one another within
the agreed scope, and only then compare them with the skill rules. Neither the directory nor the filename
excludes a document from review: include product/marketing/backend/frontend/operations docs,
README/CONTRIBUTING, PRDs, technical tasks, TDs/ADRs, settings, specs, runbooks, research,
evidence, indexes, templates, and any other documents if they are within the selected
scope. A full audit/migrate covers all project documents; an affected-scope check
covers every document type related to the affected result/contract, but does not
read unrelated parts of the repository without need.

First classify the actual type and purpose of each document, then apply
the same baseline rules regardless of directory: one coherent question/contract, one canonical
owner, accepted separate from proposal, task status/checklist only in the task card, a decision
only in a TD/ADR or explicitly permitted owning source, and an index only for navigation. Identical
rules do not mean identical names: PRD/task/TD/ADR use ID-based naming, while
a current spec, README, marketing source, or runbook may have a stable
human-readable name and must not masquerade as a task.

Compare statements by Surface, actor, Action, Visible result, scope/non-goals,
ownership and data boundaries, public/API contract, dependencies, and current decision.
Classify them as aligned, describing different aspects, semantic duplicates,
active versus historical/superseded, directly contradictory, or ambiguous.

For a contradiction, show both exact formulations, paths/sections, status/source,
the practical difference, a recommendation, and an alternative. Two incompatible accepted
sources block the affected migration and implementation until the user decides;
`proposed` does not override `accepted`, and code serves as implementation evidence but does not
determine the correct requirement.

After approval, retain one canonical contract, update links and acceptance, and
mark the replaced decision under the history rules above or as `superseded`. Repeat the
check for the affected documents. A full repository-wide consistency scan is needed
only for an explicitly full audit/migration; routine work checks directly
related sources, not the entire graph.

## Implementation closure reconciliation

Before moving a technical task to `done`, reconcile the behavior actually implemented
with the applicable canonical PRD, task, TD/ADR, and accepted settings. Check only
the affected contract: user-visible Surface/Action/Visible result, public interface,
data/ownership boundary, dependency/runtime default, and operating model.

- Do not treat a material discrepancy as an implementation detail or a silent clarification.
  It requires an explicit user decision and an acceptance source.
- Update canonical documents in the same workstream before closing the task. Implemented
  code alone does not replace this update.
- If an earlier `accepted` decision changed, do not silently rewrite or delete it:
  mark it `superseded` with the reason, date, and a link to the successor decision, or
  preserve an equivalent explicit change record in the owning canonical document. The new
  decision receives its own confirmation. Git history alone is insufficient as
  the sole record of replacement of an active contract.
- The task closure statement identifies the actual observable result, the current
  canonical decision source, and the completed verification. Do not copy the full
  PRD/TD/ADR text into the task.
- If the discrepancy is unresolved or the documents still describe the previous active
  contract, the task remains `in-progress`/`blocked`, and the implementation is not declared
  complete.
- Routine reversible implementation details that do not require a separate decision
  do not generate documentation or history solely for this gate.

If a discrepancy is discovered after closure, do not rewrite the historical closure
as though the error never occurred: create the necessary corrective task, accept the replacement
decision, and link it to the superseded source.

## Rules source

Apply the [adoption conditions](adoption.md). The user chooses either a complete copy of the skill
in the repository or a pinned link to a public source; no separate mode/profile is
stored. Existing project rules remain in effect until adoption is verified. After that,
use the selected source, project settings, and explicit scoped exceptions. Installing
a global copy alone does not change project rules.

## Project settings

When adopting the package, explicitly record the following in one section of an existing
project document (for example, the documentation index):

- the path to the navigation index and accepted scoped exceptions; for an external
  published source, a public link to an immutable Git SHA/content digest;
- directories for PRDs, technical tasks, TDs, ADRs, and history;
- the selected roadmap sequence and how to display `done`/`cancelled`: in the last
  assigned group or in `History`; standard stage names are not mandatory;
- a register of independent layers: unique ID prefix, responsibility, and, when decisions
  already exist, the path to their index; actual owners are assigned in canonical cards;
- prose language, exact metadata/heading format, and selected checks;
- where findings, code maps, and temporary source mapping are registered, the latter only for
  a full/large migration or required traceability;
- applicable product/engineering constraints and the source of their acceptance.

These are settings, not a second governance document or a copy of statuses/contracts. `AUTH`, `WEB`,
and paths in templates are examples, not mandatory architecture. Do not infer from them
the presence of a service, platform, SLO, budget, compliance requirement, or separate team.
Record unknowns as questions with an owner, not as invented constraints.
Any prose language may be selected; when an existing validator is used,
do not translate metadata fields independently of its parser/tests (see the tracker rules).

## Granularity of any document

This rule applies to all materials created or modified through the skill,
including the governance documents, templates, research, reports, and operational records themselves:
**one document — one coherent question, outcome, or contract with one reason
to change**. A layer is a responsibility boundary, not justification for a giant file.
Do not split mechanically by line count, and do not create a file for every sentence.

| Element | Unit of content | When to separate |
| --- | --- | --- |
| PRD | One verifiable user outcome and its end-to-end acceptance | Outcomes can be independently accepted, deferred, or released; the overall concept remains a concise overview with links |
| Technical task | One independently plannable and verifiable outcome within one layer | Different owners, blockers, dependencies, acceptance, or the ability to execute independently |
| Subtask | A local step toward the parent task's outcome | The step requires separate planning, an assignee with independent responsibility, or is used as a prerequisite for another task |
| TD | One technical contract/decision within a responsibility boundary | Parts can be independently accepted, changed, or replaced |
| ADR | One architectural choice with alternatives and consequences | Another independent choice; do not turn an ADR into a full system description |
| Bug, finding, idea | One problem, hypothesis, or opportunity | Independent causes/fixes/user outcomes; related manifestations of one defect may remain together |
| Spec, UX, guide, runbook | One scenario, contract, or operational procedure | Different readers, preconditions, lifecycle, or an independently usable scenario |
| Research | One decision question with sources and a conclusion | Independent research questions; substantial primary materials become separate evidence links |
| Code/architecture map | Concise system navigation; details of one module/boundary | The detail requires reading modules unrelated to the question |
| Index, backlog, register | A route to canonical documents by purpose/layer | Groups become difficult to search; add child indexes without copying cards |
| Report, evidence, source mapping | One check, audit scope, or migration batch | Independent checks/batches and large logs; the summary links to artifacts rather than copying them |
| Release note/changelog | One release or bounded period of changes | History obstructs reading the current state; a version index points to separate records |
| Governance/reference/template | One operational question or family of related forms | Applying one rule requires reading unrelated procedures; use named sections or separate references |

Size is a signal, not an acceptance criterion: if a document requires hundreds of lines
of irrelevant context, identify semantic boundaries first. Do not replace a coherent
contract with a chain of micro-files without which even its invariants cannot be understood.
Do not introduce a mandatory ID for every paragraph: cards/decisions use tracker IDs;
other documents use a stable path and named sections.

At the start of a substantive document, briefly state its question/purpose, boundaries,
and required input links when they are not obvious from the standard form.
Label links by purpose: contract, prerequisite, evidence, reference.
Do not add a universally mandatory header with dozens of empty fields.
Headings must make it possible to read the required section independently; do not hide current rules
in a historical report or an adjacent task.

### Minimum-context route

1. Read the applicable project instructions and settings; use the index to find the exact
   card or question. Do not automatically read every document linked from the index.
2. Read the target card, its acceptance, constraints, and open questions.
3. Load only applicable TDs/ADRs and direct prerequisites.
   Follow the dependency chain only where needed to resolve the question;
   do not load the entire transitive graph or the history of closed tasks by default.
4. When changing a cross-layer contract, read the affected sides and check
   consumers/backlinks. Context efficiency does not permit ignoring
   related invariants or mandatory security/reliability constraints.
5. Use headings/search and targeted ranges first; do not reread
   unchanged text that has already been loaded. Store long logs as artifacts,
   leaving the result and exact path to evidence in the card.
6. In the final response, briefly state the changes, checks performed, and remaining
   blockers. Do not repeat document contents or the entire work process.

When splitting, preserve record identities, inbound links, and existing
traceability to sources. Create separate source mapping only at the threshold defined by
the [migration process](governance-migration.md). IDs remain stable except for an explicitly
accepted rename during migration under the
[migration process](governance-migration.md). Do not split closed evidence again. For current materials,
retain one canonical source; an overview contains only its own aspect and links.
Check not only links but also whether a typical task can be performed by reading
its route without adjacent independent topics.

## Maintaining documentation changes

Rules change only upon an explicit user request; installing the skill does not
permit replacement of local rules. Record an accepted change as an agreed package
in canonical documents, not as a scattering of contradictory additions.
Before editing, read the applicable governance document; before coding, read the corresponding tasks
and decisions if they exist or if the work changes a documented contract.
Prefer local edits over regenerating files.

For documentation changes, choose relevant checks for links, anchors,
structure, whitespace, and stale paths. Do not manually run unrelated code
checks solely for documentation. The skill does not own hooks/CI and does not change them during
routine documentation work. Active project policy must not be silently bypassed, but its contents
may be changed in a separate, explicitly assigned project-governance task. Take commands from
the actual project, not from examples.

Update the changelog only under the active project release policy. The skill does not
assume a manual changelog entry after a documentation edit and does not touch
generated changelog/version sources. It is sufficient to describe completed documentation work in the
canonical task/commit/PR, if those are used. Git, publication, versioning,
language, and release rules belong to project policy; the skill neither grants nor revokes authority.

History may be preserved as immutable Git links to a specific revision instead of
local history copies, if the source is available to all required participants.
Verify that paths and anchors resolve in the preserved version. Do not make private
history mandatory context for users of a portable skill.
Deleting a local copy requires permission and verified recovery;
historical materials do not carry stale rules into current governance.

## General rules

Maintain documentation where it is needed to understand and perform the work, and update it
together with changes to the corresponding contract. Do not duplicate what is already unambiguously
expressed by a canonical source, tests, comments, or linters.

When writing to files is permitted, carry over only explicitly accepted requirements,
assigned backlog/deferred scope, and material open questions that must be
preserved after the current discussion. Do not turn every remark, question, emotion, or
agent suggestion into a card. Clearly distinguish proposed from accepted. In
discussion/read-only mode, write nothing: summarize in the response. If write permission is
granted later, carry over only the confirmed scope; do not call chat content
preserved project documentation.

Separate materials by meaning—requirements, plans, technologies, and README content must not be mixed.
Split documentation by independently useful questions and layers; do not create a giant
file or a micro-file for every sentence.

Separate content by canonical owner:

- a PRD owns the user outcome, product contract, slice contents, and end-to-end
  acceptance;
- a TD owns the technical contract and decision for one layer;
- an ADR owns a cross-layer architectural choice, ownership, and system-wide boundaries;
- a technical task owns executable scope, steps, dependencies, acceptance, and closure.

Do not duplicate one aspect across multiple document types. Put an engineering constraint
in a TD or ADR according to its actual scope rather than treating every technical
decision as architectural. Each normative decision has one canonical source;
other documents briefly describe only their own aspect and link to it.
Store pre-acceptance discussion and options with the owner of the open question or in a decision
with status `proposed`; `open-decisions` is navigation only. Only explicitly
accepted decisions become normative requirements.

Create an index of a layer's canonical technical decisions when the layer has decisions
or the project already uses such an index; an empty index is not a prerequisite for work.
Decisions record the responsibility boundary, public contract, data ownership,
technical dependencies, non-goals, open questions, checks, and migration/rollback
semantics when applicable. Implementation steps and acceptance criteria remain in
technical tasks. A material technical decision must not remain only in chat or
a navigation index. Product slice composition, statuses, and navigation are defined by
the tracker rules.

When partially moving, splitting, or reorganizing an existing file, first
use available `copy`/`move` operations (environment tools, terminal commands,
or `git mv`) to preserve the original content and history, then precisely
edit only the necessary sections. Do not retype an entire existing
file or manually replace unchanged parts when moving/copying and
a local edit solves the task more safely.

Unresolved/deferred/high-risk bugs and explicitly assigned technical observations or
product ideas are registered under the [maintenance and evolution rules](maintenance.md).
A local defect fixed in the current task and an irrelevant idea do not automatically
receive cards. Do not present hypotheses as confirmed facts. For
an independent audit trail, the project may choose a separate findings register; when it
appears, add a navigation link to the index. The following requirements apply
only to such a register.
Each entry has an ID, status, severity, code evidence, owner, a link to the remediation
task, and expected closure. Record a new finding before completing the
review/audit; after code changes, update its status/evidence, and do not delete closed
entries. OPEN/PARTIAL findings must have a technical task owned by the responsible party;
inclusion in a PRD is not mandatory and, when needed, is determined only in the PRD. Remediation
priority and queue position are defined by the tracker rules, not by a second plan in the register.
A finding's status describes the observation and does not duplicate the implementation task's status.
The register does not replace the owner's canonical decision.

Tasks marked `done`, their closure, and their evidence are semantically immutable historical records.
An accepted rename of a file, heading, or structural ID during migration is permitted
under the [migration process](governance-migration.md); it does not change the fact of completion,
acceptance, or verification results. A later audit, regression, or new scope does not
reopen `done` or rewrite status, checklist, evidence, or acceptance: create
a new task with a stable ID and a link to the previous one for follow-up. `Cancelled` does not
prove an implemented result and may be returned to active work while preserving
the previous cancellation reason and the new basis. Update current normative documents
in place; historical ordering is defined by the tracker rules.

Product goals, UX, and delivery gates are recorded in product documents; architectural
boundaries and engineering constraints are recorded in architectural documents and decisions
for the corresponding layers.

If applicable canonical tasks/decisions already exist for assigned work, or if it
changes a documented product, layer, or cross-layer contract, read only those
sources and direct dependencies. Record an accepted new choice with its
canonical owner before implementation; closure reconciliation checks the actual result.
A routine bugfix/refactor within an unambiguous existing contract does not require creating
a layer, task, PRD, TD/ADR, or complete dependency graph merely to begin coding. The order of engineering execution is defined by the active project-work policy.

If one PRD includes parts from several layers, each independently plannable piece
remains in a technical task for its layer, while end-to-end UX and acceptance criteria remain in the PRD.
When changing a cross-layer contract, update both sides and dependent links; do not
duplicate normative text between documents.

Numeric conclusions that affect a decision must be reproducible: preserve
sources, inputs, assumptions, and calculation method. For a simple comparison,
a formula and input values in the document are sufficient. Preserve a script with inputs
for a complex, repeatable, or data-sensitive calculation.
Do not create a script for arithmetic and do not require measurements without need
under the proportionality principle above.

Maintain the code map at the path from project settings (for example,
`docs/development/codebase-map.md`) as a navigation map of the actual
code once the structure of layers and entry points has stabilized. Record
package and module boundaries, their responsibilities, entry points, and cross-layer
contracts—without duplicating product and architectural requirements. Update
the map together with material structural changes.
