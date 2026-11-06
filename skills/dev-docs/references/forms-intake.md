# Incoming work and questions

Use [maintenance](maintenance.md), [requirements](requirements.md), and
[queues](work-queue.md). Reconcile existing material when needed through
[source assessment](source-transition.md), independent of its format.

## Bug

A queue row links the remediation task, which links the owning failure scenario:

```md
- [Q-004 Restore preference propagation after reconnect](wiki/personal-preferences/work.md#q-004) – backlog
```

The task owns action/status and links the defect. The defect owns impact, reproduction,
expected behavior and its basis, uncertainty, and criteria for verifying the fix.

Place environment, reproduction, hypotheses, and verification under
[work-context ownership](documentation.md#work-context-and-results). Link an existing
requirement when violated; documentation/source-only corrections need no invented R-ID.

## Research or technical finding

```md
- [Q-005 Explain idle preference traffic](wiki/personal-preferences/work.md#q-005) – backlog
```

The task links the question section, which preserves observation versus hypothesis, known impact, method/criteria,
and material unknowns. No TD/ADR or fictional product requirement is needed merely to start
research. A separately completed investigation leaves significant unresolved fixes visible.

## Product idea

Capture a requested idea as a draft/proposed obligation or an open question in its
appropriate owner under [documentation purpose](documentation.md#documentation-purpose-and-ownership).
Preserve source, potential value, known boundaries, and open questions without inventing
acceptance or a predetermined implementation. Add queue work only when a concrete
discovery/delivery result is assigned or meets the registration threshold.

Groom the specification and work separately. A draft can remain while research is ready;
an accepted obligation can remain unimplemented while delivery is blocked.
