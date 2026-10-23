# Navigation and settings

Use [requirements](requirements.md), [queues](work-queue.md), and
[governance](documentation.md). New navigation points to specifications and canonical work;
old task entrypoints explicitly route through [conversion](legacy-transition.md).

## Minimal navigation

Reuse a README or documentation index instead of creating an extra redirect file.
Illustrative links below are placeholders for documents that actually exist:

```md
# Documentation

- [Personal preferences contract](../wiki/personal-preferences.md).
- [Work and completed results](../queue.md).
- [Accepted architecture choices](../architecture/decisions/index.md).
- Legacy tasks: historical/unconverted sources only; selected work is captured into
  requirements and queue entries before continuation.
```

Add only existing targets. No empty layer/decision registry is needed.
Group current contracts, proposals under consideration, and history visibly when those
routes exist; sections of the same document are enough. Historical links retain their
baseline, while ordinary execution links resolve to the applicable current owner.
Search results still require the [state/applicability check](requirements.md#current-contract-and-nonbinding-material).

## Multiple queues and views

Canonical entries can be partitioned by capability, team, or work kind. Each work ID has
one home; other views are links or actual generated projections. Do not manually
duplicate statuses/dependencies across several queue tables.
Completed/cancelled work stays visible in history, with its result locator.

Dependency links cross queues. A blocked entry does not freeze the group.
Stages/sprints are optional selection/grouping, not requirement IDs or implementation
proof. Replanning moves work while preserving its identity and links.

## Project settings when needed

Record only choices the project actually uses in an existing settings section:

- specification/wiki, queue, decision, result, and history locations;
- selected skill copy or immutable public pointer, when governance adoption was requested;
- requirement/work ID conventions and prose/metadata language;
- compatible state tokens and whether any views are actually generated;
- accepted delivery groups, ownership/area boundaries, and scoped exceptions;
- actual documentation/parser checks and code-map locator when useful.

Do not turn settings into a second policy, requirement catalog, or work plan.
Preserve accepted source availability and history; no permanent migration-mode field.
