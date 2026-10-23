# Requirement and queue migration coverage

Use [one-shot migration](governance-migration.md) for a full selected scope and
[on-touch conversion](legacy-transition.md) for ordinary work. The former task-schema
migration is legacy; the destination is always specifications, queues, and results.

A small conversion keeps its mapping in the old-source notice or work result.
Use detailed temporary coverage only for full/large migration or required audit traceability.

```md
# Migration coverage

| Source/version/range | Meaning/type | Specification/requirement | Work/result destination | Disposition | Reason or remaining question |
| --- | --- | --- | --- | --- | --- |
| <exact source> | <obligation/decision/work/verification/question> | <canonical locator or not applicable> | <Q/result/history locator or not applicable> | <converted/shared/historical/open> | <reason and exact remaining scope> |

## Recoverability and completion

- Preserved source: <immutable revision, exact copy, or patch>.
- Current scope: <source boundaries and acceptance>.
- Remaining: <unconverted ranges, conflicts, or unavailable sources>.
- Verification: <coverage, links, graph, history, and meaning checks actually completed>.
- Final location: <condensed result, or justified historical retention>.
```

Source-to-destination mapping must account for questions, exceptions, dependencies,
and completed/cancelled outcomes, not merely renamed files. Repeated entry reuses existing
destinations. Do not mark open/unmapped material migrated or preserve a permanent second
tracker. Cleanup/deletion follows explicit authority and verified recovery.
