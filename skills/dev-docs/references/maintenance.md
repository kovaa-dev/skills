# Maintenance and continuous development

Use together with the [task tracker core](task-tracker.md) and the [policy](documentation.md).

## Continuous development, bugs, and incoming ideas

The task tracker covers work that crosses the registration threshold below, regardless of
the current product slice. Every registered task appears exactly once in the shared
roadmap: an active task in its current or future delivery group, and a `done`/`cancelled`
task in its last assigned group or in `History`. After the first version, support and
development continue as an ongoing flow; product stages, sprints, and inclusion of every
technical task in a PRD are optional, but every task must have a place in the roadmap.
A PRD describes a new user outcome; it is not a container for every fix. Bringing an
implementation into compliance with an existing contract does not require a new PRD or
TD/ADR; changing the behavior or contract itself requires a decision by the appropriate
owner and agreement with the user. Research may refer to existing requirements or a
contract; if none exist, keeping the question and validation plan in the task itself is
sufficient. Do not create a TD merely to authorize starting research.

### Registration and triage

- The card type does not change the ID namespace: product `idea`, `feature`, and
  `improvement` items use PRD; technical `bug`, `investigation`, and `maintenance` items
  use the layer prefix. This is an intake classification, not a required field on every
  technical task. Migration, refactor/debt, security, reliability/performance,
  operations, dependency updates, CI/tooling, and platform work are descriptively
  classified as `maintenance` unless the project has approved a narrower extension; a
  user outcome still requires a PRD.
- A card is required for an unresolved defect, deferred fix, recurring/systemic problem,
  high/critical risk, or an explicit request to register the item. A local defect that is
  fully fixed and verified within the current task does not require a separate card. Do
  not automatically register irrelevant findings or new ideas: report them briefly and
  preserve them only on explicit request or when they create unresolved blocker/high-risk
  work. In read-only mode, do not claim that a record was created.
- The minimum registration record is: ID, type, `backlog`, source/date, summary, known
  impact, next step, triage owner or `unassigned`, and a link from the roadmap. Do not
  require complete design, an estimate, a deadline, a PRD, or a product stage merely to
  preserve the item. Choose a preliminary placement according to the currently affected
  delivery boundary and refine it after triage; do not create a separate queue alongside
  the roadmap.
- Check for duplicates before creating a card. When merging, preserve useful sources and
  evidence; close the duplicate as cancelled with a link to the canonical card.
- If the technical layer is unknown, an explicitly project-registered `TRIAGE` prefix is
  permitted. Preserve the ID after triage and state the current layer in the card. Do not
  create `TRIAGE` automatically when the owning layer is known.
- An observation, a causal hypothesis, and a confirmed cause are distinct. Preserve
  reproduction steps and evidence; do not present a guess as an established defect.
- A small investigation and its fix may live in one task. If the investigation is closed
  separately, every remaining fix receives an open card and a link; completing the
  investigation does not mean the problem has been resolved.
- Groom a backlog card before `planned`: assign an owner, accept a verifiable outcome,
  dependencies, and priority, and record evidence. Only then may selected work become
  `planned`; a missing answer becomes `need-info`, while an unmet adjacent prerequisite
  becomes `blocked` with a reason and observable unblock condition. Triage the backlog
  regularly before selecting the next work and before release; review old records rather
  than deleting them automatically.

### Bug severity and execution order

Severity describes consequences; priority describes execution order. Store both ratings
and their rationale in the card, not in registry copies. Impact scale, workaround
availability, data loss, security, and disruption of the primary flow matter more than
emotive wording. Unknown severity requires prompt triage, not a silent low-priority
assignment.

Every registered unresolved/deferred bug must receive an explicit severity-based execution
decision: placement in the roadmap relative to the affected stage/release boundary, or a
justified deferral with a review condition in the card. A local defect fixed and verified
within the current task does not require a separate card. Registering an unresolved bug
without roadmap placement is insufficient. Use the task index as the sole queue; do not
create a second plan. The index stores order, links, and status projection; the card stores
priority, rationale, and the next step.

Default profile, unless the project has approved another:

| Severity | Consequences | Planning |
| --- | --- | --- |
| critical | Active security threat, data loss/corruption, or widespread unavailability of a key flow with no workaround | Escalate immediately; propose safe containment and place remediation ahead of ordinary development; block the affected release |
| high | The primary flow is substantially broken, with no acceptable workaround for affected users | Put in the nearest fix queue ahead of non-critical improvements; release the affected flow only after the fix or explicit risk acceptance |
| medium | Limited defect with an acceptable workaround | Include in the regular queue according to impact and dependencies; if deferred, record the reason and review trigger |
| low | Cosmetic issue or minor inconvenience that does not compromise the primary outcome | Plan with other layer work or explicitly defer with a review condition |

These are not invented SLAs: the project defines timelines and emergency-response
authority. The agent must raise a critical risk and propose replanning, but this does not
grant permission to change scope, production, or data arbitrarily. Record exceptions to
the ordering with a rationale and responsible owner; do not silently lower severity.
Register and plan a finding that does not block the current work but crosses the
registration threshold above, then continue the original task. Briefly reporting other
observations is sufficient. Link a blocking problem as a dependency and explicitly report
the blocker.

Close a bug by verifying the original reproduction and applying the project's current
regression/validation policy. `dev-docs` records the selected method, result, and any open
blocker/exception, but does not duplicate test categories, test levels, or harness rules.
Do not present manual evidence as an automated test.

A fixed and verified bug is `done`; this status is terminal. A duplicate, confirmed absence
of a defect, or agreed rejection is `cancelled`, with a reason and replacement when one
exists; a cancelled task may be reopened while preserving the previous reason and the
basis for resuming work. “Not reproduced” does not mean “no defect”: keep the task open
with conditions for the next verification. A new regression after `done` receives a new,
linked task; do not rewrite the closure history or evidence.

### Completion and release

The `done` status means the task's acceptance has been completed, while the `Release`
delivery group contains work for the target or currently supported public boundary;
neither proves delivery. Store the fact of release in one release record: version/deployment,
date, and task links. It does not copy task statuses or the future plan. A user-facing
changelog describes visible changes and does not duplicate contracts. A release does not
automatically close unverified cards; afterward, tasks remain in their last assigned group
or move exactly once to `History`, according to project settings.
