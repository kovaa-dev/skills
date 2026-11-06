# Work entries and result artifacts

Use [work queues](work-queue.md), [requirements](requirements.md), and
[governance](documentation.md). Assess selected sources under
[source assessment](source-transition.md); reuse compatible work/result owners.

## Lean canonical queue entries

Insert linked rows into the existing queue/index; the path below is illustrative.
Follow [queue row and outcome rules](work-queue.md#one-work-item-one-result-boundary).
The requirement examples follow the [ID rules](documentation.md#layers-and-id-namespaces)
and the owners in the [specification example](forms-product.md). Q-001 is an illustrative
independent investigation; retain the project's existing work-ID convention.
Old aggregate task links can be replaced by covered requirement/result links under
[the transition rules](work-queue.md#existing-queues-during-transition).

```md
# Work queue

## Open work

- [Q-001 Establish a usable preferences representation](wiki/personal-preferences.md#representation-question) – ready
- [R-SYNC-001 Deliver cross-device preferences](wiki/personal-preferences.md#r-sync-001) – blocked

## Completed work

- [R-LOCAL-001 Preserve preferences locally](wiki/personal-preferences.md#r-local-001) – done
```

The queue status is copied from the linked owner. For example, a requirement section
may contain `Delivery status: blocked` with the revision/target and missing input; its
queue row repeats `blocked`. The investigation section owns its own `Work status: ready`.
Read those source fields before execution and keep all affected rows consistent.
These snippets illustrate different delivery states; do not infer them from a draft
requirement or unknown verification in another example.

In the linked question section, record the expected experiment/conclusion. In the linked
delivery context, identify the accepted representation result it waits for and the agreed
target. Completed result sections own actual dates, verification, and limits. These details
do not become additional queue fields or inline cards.

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
