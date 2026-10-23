# Specification and requirement form

Use [requirements](requirements.md) and [governance](documentation.md).
This replaces the legacy product-task/PRD form. Convert selected old work under
[on-touch transition](legacy-transition.md); do not create a new PRD to use this example.

## A specification with addressable requirements

Illustrative docs/wiki/personal-preferences.md; adapt placement/language and omit unused
fields. Shared metadata applies until a requirement needs a narrower scope.

```md
# Personal preferences

Area: personal-preferences. Owner: <known owner or unassigned>.
Definition: draft. Implementation: unknown.
Scope: <actor, account/workspace, online/offline, current or rollout condition>.
Acceptance source: pending.

## Rationale

### WHY-001 Continue work across devices

<Accepted goal/source, or explicitly labeled hypothesis. Other specifications can link here.>

## Preserve a saved preference across reload

###### R-001

Revision: 1. Basis: [Continue work across devices](#why-001-continue-work-across-devices).

<One separately meaningful obligation under the stated conditions.>

Acceptance: <observable scenario and method; use existing tests when sufficient>.
Verification: unknown; no current result established.

## Apply remote changes on active devices

###### R-002

Revision: 1. Basis: [Continue work across devices](#why-001-continue-work-across-devices).
Prerequisites: <actual required capability/result, or none>.

<Expected behavior, including accepted conditions; do not invent a freshness bound.>

Acceptance: <scenario, applicable conditions, and verification method>.
Verification: unknown.

## Open questions

<Unsettled behavior, limit, or decision; owner and next useful step where known.>

## Representation question

<Question, criteria for an acceptable answer, and known constraints. Link resulting
experiment/report here when work produces it; no implementation checklist.>

## Verification results

<Actual results by requirement revision/baseline, method, date/version when needed,
limitations, and artifacts. Historical results remain labeled as historical.>
```

Promote only genuinely agreed obligations to accepted and capture their acceptance source.
Unknown implementation does not itself invalidate an agreed requirement. Requirement
IDs stay stable across clarification and semantic revisions. A new independent obligation
gets a new ID, not a renamed completed task.

Shared rationale can be a named block without an extra file/ID. A technical choice belongs
in an existing decision block or [decision form](forms-decisions.md) when independently useful.
Work to realize this contract belongs in the [queue](forms-technical.md).

## A proposed revision and a historical redirect

When proposing a revision to an existing accepted R-002, retain its accepted formulation.
A separate candidate block can live in the same specification; it overrides any inherited
accepted metadata. Illustrative only; use actual IDs/revisions and known facts:

```md
## Proposed change to R-002

Definition: proposed. Target: R-002 revision 3, <link to current accepted formulation>.
Proposes to replace: <exact behavior/scope; no effective supersession yet>.
Rationale: <problem and expected benefit, with sources or labeled hypothesis>.

Candidate: <alternative behavior, conditions and acceptance method>.
Acceptance source: pending.
Decision questions: <material trade-offs and criteria>.
Revisit: <known owner/trigger when useful>.
```

An optimization proposal such as WebSocket delivery can coexist with the current
cross-device settings contract. Neither a candidate implementation nor an experiment
silently waives the currently accepted propagation/offline guarantees.

For an established replacement, preserve an old anchor with a short notice rather than
leaving historical wording looking current:

```md
###### R-017

Definition: superseded in <scope/version>; historical, nonbinding for <current target>.
Successor: <link to current requirement/revision>.
Changed: <date, reason and acceptance source>.
Historical formulation/results: <exact locator; retain original applicability>.
```

For retirement without a replacement, state retired and why there is no successor.
Apply [the lifecycle](requirements.md#retiring-stale-material); do not use this notice to
invent acceptance or disable obligations still applicable to supported baselines.
