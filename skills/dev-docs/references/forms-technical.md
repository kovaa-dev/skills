# Tasks and result artifacts

Use [work queues](work-queue.md), [requirements](requirements.md), and
[ownership](documentation.md#work-context-and-results). Examples use illustrative
paths/statuses; preserve the actual project's IDs and known facts.

## Queue and task

```md
- [Q-001 Investigate preferences representation](wiki/personal-preferences/work.md#q-001) – ready
- [Q-002 Implement cross-device preferences](wiki/personal-preferences/work.md#q-002) – blocked
- [Q-003 Preserve preferences locally](wiki/personal-preferences/work.md#q-003) – done
```

The linked task is the execution-status authority. A compact task section is enough:

```md
## Q-002

Implement cross-device preferences.
Status: blocked.
Implements:
- [R-SYNC-001 revision 1](requirements.md#r-sync-001).
- [R-LOCAL-001 revision 1](requirements.md#r-local-001).
Preserves:
- [Existing account isolation](../account-access/requirements.md#account-isolation).
Depends on:
- [Q-001 representation result](#q-001).
Result: <link when available>.
```

The task links criteria/constraints, never copies them. Research questions, defect
reproduction, rationale and implementation decisions remain in their topic owners.
Assignee/priority/target are optional execution metadata, not grounds for another file.
The links select a coherent result without copying contract text. Use a precise section
when a requirement is only partly selected. Record coverage of all selected obligations
and affected preserved constraints in the result before closing the task. Local steps
stay executor plans.
Historical tasks keep their original baselines, status and result locators.

## Result or investigation section

Reuse an existing relevant section or useful artifact:

```md
## Representation result

Question and answer criteria: <link to owning question>.
Inputs/baseline: <reproducible source/version and applicable constraints>.
Method: <enough to repeat the significant check>.
Result: <observed behavior/measurements and artifact locators>.
Conclusion: <supported answer, limits and unresolved issues with remediation task links>.
Requirements checked: <IDs/revisions, including preserved contracts>.
Delivery: <actual target/version or not delivered, as applicable>.
```

An accepted negative answer can finish an investigation without implementing the product.
Task completion links the result; neither the task nor queue duplicates its evidence.
