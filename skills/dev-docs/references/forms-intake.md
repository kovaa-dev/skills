# Incoming work and questions

Use [maintenance](maintenance.md), [requirements](requirements.md), and
[queues](work-queue.md). These forms replace old bug/layer/PRD card examples.
Convert selected existing cards through [on-touch transition](legacy-transition.md).

## Bug

A minimal canonical queue entry can be:

```md
###### Q-004

**Restore preference propagation after reconnect** · backlog · bug · severity: <known or unknown>.
Contract/reproduction: <link to the existing requirement and owning failure scenario>.
Next result: reproduce and restore the agreed behavior.
Scheduling: <priority/deferral reason and review trigger when deferred>.
```

Place environment, reproduction, hypotheses, and verification under
[work-context ownership](documentation.md#work-context-and-results). Link an existing
requirement when violated; documentation/source-only corrections need no invented R-ID.

## Research or technical finding

```md
###### Q-005

**Determine why idle preferences generate excess traffic** · backlog · research.
Question: <link to the owning investigation section>.
Result: reproducible conclusion and any separately needed remediation.
```

The question section preserves observation versus hypothesis, known impact, method/criteria,
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
