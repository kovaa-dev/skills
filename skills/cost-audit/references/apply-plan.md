# Apply Plan Contract

This reference owns recommendation ranking and the handoff produced by the audit. The skill does not execute the plan.

## Admission rule

An action belongs in the necessary plan only when it:

1. addresses a material observed or reconstructed mechanism;
2. names the affected scope and an owner or exact control surface when known;
3. preserves required quality, safety, authorization, and traceability;
4. has a verification method capable of disproving the expected effect; and
5. is not made redundant by another action.

An estimated saving may rank actions, but estimation alone cannot establish the underlying mechanism. Put speculative changes under optional experiments or non-actions.

## Ranking

Rank by expected avoidable workload, confidence, blast radius, and implementation cost. Prefer changes that improve both efficiency and quality, such as eliminating identical failed retries or bounding unused tool output. Separate:

- **necessary:** required to address a supported material finding;
- **conditional:** needed only if a stated measurement or rollout result crosses a threshold;
- **optional experiment:** useful to learn, not justified for immediate rollout;
- **non-action:** considered but unsupported, immaterial, fixed, or harmful.

Priority labels without materiality are insufficient.

## Common mechanisms

Consider these only when the evidence supports them:

- reduce an actually repeated instruction or context prefix;
- replace serial model/tool roundtrips with a bounded batch;
- cap, filter, summarize, or store outside context tool results that are demonstrably oversized;
- remove deterministic error loops and identical retries;
- stop standalone working-directory calls by setting the tool working directory;
- expose only tool schemas required by the active profile when schemas materially enlarge each request;
- route detailed instructions through progressive disclosure when they are being loaded eagerly;
- add a deterministic preflight for a repeatedly missing capability;
- reuse verified structured results instead of repeating an unchanged search;
- continue an existing session when repeated startup cost is measured and task isolation is not required.

Do not assume that model downgrades, local models, embeddings, more compaction, fewer sessions, subagents, or new storage reduce total cost. Those are valid only as measured, quality-preserving responses to a finding.

## Action schema

For every action, provide:

| Field | Requirement |
| --- | --- |
| `action_id` | Stable identifier linked to finding IDs |
| `class` | Necessary, conditional, or experiment |
| `target` | File, configuration, wrapper, runtime owner, or workflow boundary |
| `change` | Minimum behavior change; no implementation essay |
| `preserve` | Quality, safety, and compatibility properties that must remain |
| `expected_effect` | Measured range when defensible, otherwise structural direction |
| `dependencies` | Ordering or external authority required |
| `validation` | Before/after cohort, metrics, window, and success threshold |
| `rollback` | Reversible step or recovery path |

Do not provide a patch unless separately requested. If the exact target is unknown, assign discovery to the responsible owner as a conditional first step rather than inventing a file.

## Validation design

Use the smallest comparison that can detect the intended effect:

- hold task type and quality gate constant;
- compare enough similar sessions to avoid relying on one outlier;
- measure the mechanism directly, such as calls per turn or model-visible tool-result characters;
- include task success, correction rate, or verification coverage so savings are not purchased by hidden quality loss;
- state the observation window and rollback threshold before rollout.

Do not promise a percentage reduction when the audit only supports directionality. Do not aggregate provider metrics with incompatible semantics without preserving provider-level results.

## Report skeleton

```markdown
# Cost audit

## Scope and coverage
...

## Baseline
...

## Material findings
| ID | Mechanism | Evidence | Scope | Materiality | Confidence |
| --- | --- | --- | --- | --- | --- |

## Necessary and sufficient apply plan
| Action | Findings | Target | Change | Expected effect | Validation | Rollback |
| --- | --- | --- | --- | --- | --- | --- |

## Conditional experiments
...

## Non-actions and limits
...
```

When no change clears the admission rule, replace the plan with **No apply plan justified** and name the smallest measurement needed for a future decision.
