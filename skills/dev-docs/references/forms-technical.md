# Work entries and result artifacts

Use [work queues](work-queue.md), [requirements](requirements.md), and
[governance](documentation.md). This replaces the legacy technical-task form.
Selected old layer tasks first follow [on-touch conversion](legacy-transition.md).

## Lean canonical queue entries

Illustrative docs/queue.md. These entries share one owner/context where appropriate.
Link the relevant contract, documentation, or result question. A short acceptance/context
note is sufficient when useful; follow [work-context placement](documentation.md#work-context-and-results)
for longer material.

```md
# Work queue

Owner: <known accountable owner>. Updated: <actual date when useful>.

## Open work

###### Q-001

**[Establish a usable preferences representation](wiki/personal-preferences.md#representation-question)** · ready · research.
Result: an accepted experiment/conclusion sufficient to choose the representation.

###### Q-002

**[Deliver cross-device preferences](wiki/personal-preferences.md#r-002)** · blocked.
Waits for: [Q-001](#q-001), the accepted representation result.
Target: <agreed application/environment or other destination>.

## Completed work

###### Q-003

**<Prior independently useful result>** · done · <known completion date>.
Result: <exact result/verification locator and historical limits>.
```

Set ready only when actual scope, acceptance, inputs, authority, and owner are sufficient.
Use project tokens such as planned where they already represent readiness. Do not fill
dates, acceptance, current verification, or owner from the illustrative text.

Local steps can remain an executor plan. Use another work entry only for a result with
independent planning/acceptance or a real prerequisite supplied to other work.
The same entry may implement several requirements and produce code, documents, or data.

## Result or investigation section

Use an existing relevant result/documentation section or a separate artifact when its
content is independently useful; a repair or execution brief needs no new file by default:

```md
## Representation result

Question and acceptance: <link to the owning question>.
Inputs/baseline: <reproducible source/version and actual constraints>.
Method: <enough to repeat the significant check>.
Result: <observed behavior/measurements and artifact locators>.
Conclusion: <supported answer, limits, and unresolved issues>.
Requirements checked: <IDs/revisions, including preserved contracts>.
Delivery: <actual target/version or not delivered, as applicable>.
```

A report may establish infeasibility and still complete the investigation. It does not
make the product requirement implemented. Long logs and retries do not belong in the queue.
