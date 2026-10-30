# Focused review profiles

Use these profiles with the [review method](review.md). Read only the sections relevant
to the affected mechanism or agreed audit concern. Questions guide inspection; depth
and executed checks follow the risk, scope, and evidence rules in that method.

## Data and migrations

- Trace compatibility between old/new code and stored representations, including
  mixed versions during rollout. Check defaults and existing records, not only new data.
- Inspect partial application, interruption, reruns, transactions, and concurrent writes.
  Look for violated invariants, silent truncation, and unintended destructive effects.
- Check recovery/rollback assumptions against actual transformations. A reverse migration
  does not necessarily restore lost data; verify the accepted recovery path and its inputs.

## Asynchronous and concurrent work

- Trace duplicate, delayed, reordered, and overlapping operations against their actual
  delivery guarantees. Check idempotency scope, deduplication lifetime, and ownership of
  locks or leases where used; do not assume exactly-once execution.
- Inspect the boundary between committing a side effect and acknowledging completion.
  Check retries, lost responses, cancellation, timeouts, and restart recovery there.
- Follow state and resource ownership during races: late completions, stale reads,
  shared mutable state, released resources, and pending work after shutdown.

## APIs and integrations

- Trace the actual client/server contract: input validation, authorization, defaults,
  error semantics, persisted/exchanged formats, and old consumers where affected.
- Check partial success and ambiguous failure across the remote boundary. Inspect
  timeouts, bounded retries, rate limits, idempotency, and downstream failure propagation
  where relevant to the accepted behavior.
- Verify integration assumptions against supported versions and configuration. Distinguish
  contract evidence from mocks that merely reproduce the implementation's assumptions.

## User interfaces

- Trace usable success, empty, waiting, error, and retry states on the accepted surface.
  Check preservation of input, duplicate submission, stale responses, navigation, and
  recovery from failure where relevant.
- Inspect keyboard operation, focus, accessible names, semantics, and communication of
  status/errors for affected controls. Use existing automated checks where sufficient.
- Keep responsive and assistive-technology claims within actual evidence. Manual UI
  acceptance remains [user-owned](../SKILL.md#4-user-owned-manual-usability-gate).
  Apply [design-skill routing and agent visual verification](ui-design.md), then prepare
  any required user acceptance cases; agent inspection does not close that gate.

## Dependencies and builds

- Inspect changed dependency behavior, supported runtime versions, lockfile consistency,
  installation/build scripts, package sources, and permissions in the actual delivery path.
- Verify what enters the built artifact: configuration, secrets, generated assets,
  platform assumptions, and availability of required runtime dependencies. Check relevant
  reproducibility and compatibility claims using existing build tooling.
- For a vulnerability concern, establish the resolved version, authoritative advisory,
  applicability, and reachable mechanism. A scanner match is a lead requiring assessment;
  lack of current advisory data is a verification limit, not evidence of safety.

## Performance and resource use

- Trace work growth under actual expected data volumes and request patterns: query count,
  repeated computation, allocation/retention, contention, blocking, and unbounded queues
  or input where relevant.
- Identify the constrained resource and concrete uncertainty before measuring; use
  accepted budgets where defined. Compare representative conditions with a meaningful baseline, accounting
  for cache state, workload distribution, and variability that affect the conclusion.
- Apply [measurement and artifact rules](research-artifacts.md) when measurements are
  justified. Prefer existing instrumentation/benchmarks; separate measured results from
  complexity-based hypotheses and bound conclusions to the workloads checked.
