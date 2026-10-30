# Review of completed changes and codebases

Review checks whether the finished result meets the accepted contract and can be safely
changed and operated within its intended use. Tests and static tools supply evidence;
they do not replace inspection of the implementation and its interactions.

## Scope and baseline

Choose the mode from the requested result:

- **Change review** is part of implementation completion. Compare the final change
  with its base and inspect affected callers, dependencies, contracts, configuration,
  and failure paths. Go beyond changed lines where needed to establish consequences;
  do not turn a local change into an unrelated repository cleanup.
- **Codebase audit** checks an explicitly agreed repository, subsystem, or set of
  concerns. Map its entrypoints, owners, data flows, dependencies, and existing checks;
  prioritize concrete risks and retain a concise account of inspected and uncovered
  areas. A sample or one successful path cannot establish coverage of the whole codebase.

Identify the revision or comparison reviewed, including relevant uncommitted changes,
and the applicable requirements and environment assumptions. Findings and conclusions
apply to that baseline. Reuse available Git/PR and work context; a new snapshot system
or report file is not required.

A review-only request authorizes inspection and appropriate checks, not fixes or external
publication. During implementation, local fixes within the accepted scope are part of
the work. A codebase audit does not itself authorize remediation, intrusive probes,
production changes, or new performance infrastructure.

## Risk model and scenario tracing

Before detailed inspection, identify the critical outcomes, preserved invariants,
trust/ownership boundaries, irreversible effects, and existing paths the change can
affect. Prioritize plausible failures by consequence and reachability. Use accepted
contracts and actual usage; keep unknown assumptions visible. For a local change,
a few sentences suffice; no separate threat model or risk register is required.

Trace important scenarios across the affected components, including callers and side
effects: for example, user action, API, authorization, persistence, retry, and displayed
result. Inspect what happens when a step fails after an earlier step succeeds, a response
is lost, work is cancelled, or an operation repeats. Select relevant paths from the risk
model rather than attempting every combination or stopping at the changed file boundary.

## Review dimensions

For implementation completion, consider every dimension for the affected scope. A
focused review or audit covers its agreed concerns and names the exclusions; it cannot
establish general readiness. Explain non-applicability briefly; an applicable but
unexamined concern is a gap, not a pass. For a small change, a short combined account
is sufficient. For documentation-only work, inspect affected rules, links, examples,
and contract consistency; do not manufacture runtime scenarios.

| Dimension | Questions that guide inspection |
| --- | --- |
| Correctness | Does the result satisfy accepted behavior? Check boundaries, empty/invalid inputs, failure propagation, state transitions, concurrency, retries, and resource cleanup where relevant. |
| Security and data safety | Are authorization and ownership enforced at the actual boundary? Can untrusted input, secrets, sensitive data, retention, destructive operations, or recovery paths violate the accepted contract? |
| Regressions and compatibility | Which existing callers and user paths can change? Check public interfaces, persisted formats, defaults, migrations, dependency changes, and rollback compatibility where relevant. |
| Performance and resource use | Does actual expected usage expose excessive queries, repeated work, unbounded input, memory growth, blocking, or contention? Are accepted performance claims supported by suitable evidence? |
| Readability and maintainability | Can a maintainer understand and safely change the result? Check naming, responsibility boundaries, coupling, duplication, unnecessary abstractions, and stale comments against existing project patterns. |
| Test protection | Do the checks exercise significant outcomes and concrete failure mechanisms? Look for missing regression protection, brittle expectations, and mocks that hide the defect. |
| Operation and recovery | Where relevant, can failures be diagnosed and recovered from? Check useful diagnostics without sensitive-data exposure, timeouts, cancellation, retry behavior, configuration, rollout, and recovery instructions. |

Use concrete failure mechanisms and accepted constraints to choose depth. A directory
name or theoretical possibility alone does not justify an extensive security audit,
benchmark, new harness, or additional test level. Apply the existing
[testing rules](../SKILL.md#5-tests-e2e-and-auxiliary-complexity-boundaries) and
[research artifact rules](research-artifacts.md) when new measurements are justified.
Do not invent numerical performance budgets or claim measured behavior from inspection.

For domain-specific failure mechanisms, read only the relevant section of
[review profiles](review-profiles.md): data/migrations, asynchronous work, APIs,
interfaces, dependencies/builds, or performance. Profiles guide inspection; they do not
require unrelated checks or the whole profile reference to be loaded for every review.

## Evidence and findings

Derive expected outcomes from accepted requirements and preserved behavior rather than
treating the implementation as its own specification.
Reconcile code, tests, configuration, and affected documentation where they disagree.

Use existing diagnostics and targeted checks to test consequential uncertainty. Separate
static inspection, agent visual inspection, executed automated checks, user-reported
manual acceptance, and unverified assumptions. Record what was actually run and its
result; green CI, coverage percentages, and an absence of findings do not independently
prove correctness.

For a material uncertainty, state a testable failure hypothesis and its triggering
conditions, then trace the mechanism and look for evidence that confirms or disproves it.
Check whether caller constraints, guards, transactions, or existing tests already prevent
the failure. Prefer an existing check or minimal reproducer when execution adds useful
confidence; a clear static causal explanation can establish a defect without a new test.
Do not execute every hypothesis or create test infrastructure merely to fill the report.

A finding identifies:

- the exact code/configuration/document location, with a line or symbol where useful;
- the triggering condition and concrete consequence for behavior, data, operation, or
  future changes;
- evidence or a clear causal explanation, with observations distinguished from
  hypotheses and unknowns;
- for a change review, whether the defect is introduced, pre-existing but newly exposed,
  independently pre-existing, or of unknown origin; compare the base where necessary
  instead of inferring origin from its proximity to changed lines;
- severity and whether it blocks the selected result under the project's accepted
  policy, plus the smallest useful correction or next check when known.

Origin and severity are separate: a newly reachable old defect can block the change,
while an unrelated old defect may be separate work. Consolidate findings with an
established common cause, retaining distinct consequences and affected locations.
Do not merge independent defects solely because their symptoms resemble one another.

Follow the project's existing severity and work-registration rules. Do not invent a
parallel scale or register a separate task for each local defect fixed during the work.
Separate defects and material maintenance risks from optional style preferences.
Personal taste alone does not block completion or justify unrelated refactoring.
An unconfirmed concern remains a question or verification gap; do not present it as a
proven defect or silently dismiss a potentially blocking uncertainty.

## Resolution and recheck

During implementation, correct in-scope blockers and verify the original failure and
affected behavior. Keep existing regression-protection obligations. If resolution
requires a new product decision or material scope expansion, name that dependency and
continue unaffected authorized work. Report unrelated findings through the existing
project route; they block this result only when their consequences prevent its acceptance.

After fixes, review the changed paths and interactions again and rerun checks whose
evidence was invalidated. Integration or later edits require renewed review of affected
assumptions, not an automatic repeat of the entire audit. Stop when blockers are resolved
and applicable evidence remains valid for the final baseline; do not add rounds merely
to produce more findings or polish optional preferences.

Self-review is the default. Independent review can help a complex or high-risk decision,
but follows the existing [subagent rules](../SKILL.md#7-subagents-and-orchestration)
and is not mandatory for every change. Identify its actual scope when used; do not
describe self-review as independent approval.

## Result and completion

Keep the result proportional, in chat or the existing canonical result/PR/work context:

- reviewed baseline, scope, and material exclusions;
- applicable dimensions and evidence, distinguishing checked with no known findings,
  findings present, not checked, and not applicable with a reason;
- unresolved findings, verification gaps, and their effect on acceptance;
- fixes and meaningful rechecks, plus accepted deferrals or remaining work when present.

For substantial audits, summarize coverage in a compact table in the same result:
area, concern/scenario, method/evidence, and findings or gaps. Distinguish inspected code
from executed paths; count neither sampled checks nor file counts as complete coverage.
When continuing an audit, reuse valid prior coverage and recheck baseline-dependent
assumptions. Do not create a second mutable tracker or a row for every file by default.

Order remaining corrections by blocking impact, risk, and dependencies. Identify shared
fixes and how their outcomes should be verified, so the result provides a useful repair
sequence. Do not treat the number of findings as a quality metric or invent priorities
that conflict with the project's accepted scheduling decisions.

A change passes review when its agreed scope has been examined, completion-blocking
findings are resolved and verified, and no mandatory verification remains missing.
Any exception must follow the existing project authority and acceptance rules, with
its reason and consequences explicit; a reviewer cannot waive an accepted obligation
or downgrade severity merely to finish. Deferred non-blocking improvements use existing
work records when their registration threshold applies.

Completing an audit can mean delivering a report with unresolved findings when that was
the agreed result. It does not mean the audited codebase has been remediated or is ready
for release. A readiness conclusion requires the agreed coverage and acceptance checks;
unreviewed areas and missing evidence remain explicit limits.

State conclusions for the reviewed baseline and scope, such as "no known blocking
findings within the reviewed scope." Do not certify absence of all bugs, universal
security, or performance at untested workloads. Review does not replace the
[manual usability gate](../SKILL.md#4-user-owned-manual-usability-gate), documentation
closure reconciliation, or separate delivery authority.
