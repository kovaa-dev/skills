# Optional findings register

Use [maintenance](maintenance.md), [requirements](requirements.md), and
[queues](work-queue.md). Legacy finding/task sources route through
[on-touch conversion](legacy-transition.md).

Use a separate findings register only when the project actually needs an independent
observation/audit record. Otherwise keep the observation with its owning contract/result
and link necessary work in the queue. Do not create a second execution plan.

An optional observation records: stable identity, original source/version, confirmed
observation versus hypothesis, impact/severity, responsible owner, linked requirement,
remediation Q entry, and closure verification. Preserve closed observations.
Finding states such as OPEN/PARTIAL/CLOSED describe the observation's disposition,
not a copied work status. A significant unresolved finding needs visible remediation
or an explicit accepted deferral with a review condition.
