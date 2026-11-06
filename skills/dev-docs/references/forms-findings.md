# Optional findings register

Use [maintenance](maintenance.md), [requirements](requirements.md), and
[queues](work-queue.md). Existing sources are assessed through
[on-touch conversion](source-transition.md).

Use a separate findings register only when the project actually needs an independent
observation/audit record. Otherwise keep the observation with its owning contract/result
and link necessary work in the queue. Do not create a second execution plan.

An optional observation records: stable identity, original source/version, confirmed
observation versus hypothesis, impact/severity, responsible owner, applicable contract/source,
remediation Q entry when independently actionable, and closure verification.
Preserve closed observations.
Finding states such as OPEN/PARTIAL/CLOSED describe the observation's disposition,
not a copied work status. A significant unresolved defect needs a linked remediation task, including explicitly
deferred work. An accepted risk/deferral decision belongs at its decision owner and
is linked from the task; it does not silently erase the remaining outcome.
