# Retrieval effort profiles

Read this reference only when converting the selected `compact`, `balanced`, or `thorough` profile into concrete retrieval budgets for a helper, connector, or project adapter. Effort changes search cost and recall; it never weakens the mandatory evidence and safety invariants in `SKILL.md`.

| Effort | Initial set | Total returned context | Expansion rounds | Additional verification search |
| --- | --- | --- | --- | --- |
| `compact` | 4–6 passages | 8,000–12,000 characters | 1 | Decisive claims only |
| `balanced` | 8–12 passages | About 20,000 characters | 2 | Decisive claims and discovered conflicts |
| `thorough` | 12–20 passages | Up to 40,000 characters | 3 | Contrary evidence and independent verification of material conclusions |

Start at the low end of the passage range. Move toward the high end only for a named gap, weak source diversity, truncated decisive context, or a conflict. Count an expansion round only when it issues another query or continuation for the same facet; reopening selected locators for mandatory verification is not an expansion round.

For normalized local Retrieval, the passage budget is also a round-trip budget. A cold or partial pass uses one auto-routed `evidence-pack` tool round that performs fingerprint/index/receipts/search/selection/get and cost estimation internally. It starts a fresh-context low-overhead worker only when a measured profile clears the saving threshold; otherwise the coordinator interprets inline. An exact verified warm pass returns findings without search, passage reopen, or worker. A stale receipt routes through fresh retrieval. An allowed expansion is not automatic permission for another call: spend it only on a named unresolved facet. Do not run a successful pack again to inspect receipt behavior.

## Map profiles to existing controls

Do not add or expect a `--effort` CLI option. Translate the profile into the controls already exposed by the selected tool:

- map the initial passage range to `evidence-pack --max-passages` and `--max-passages-per-question`; use `--limit-per-query` only to increase candidate breadth for a named coverage gap;
- map the context ceiling to `--max-total-chars`; it bounds reopened evidence rather than intermediate search snippets;
- use `--max-passage-chars` to deepen only selected passages; keep the default unless decisive context is clearly truncated;
- use the table's expansion count as the per-facet workflow cap;
- for `get`, resume, and list operations, request only the selected IDs or active records and keep their combined output inside the same context ceiling.

Exact deduplication, current-receipt checks and reuse, metadata filtering, valid continuation, and index reuse remain automatic; persisting a receipt still requires durable-write authority. Apply a per-source cap only when one source dominates useful diversity; it is evidence-dependent rather than an effort profile. Chunk size is a corpus-index design choice and must not change per query or effort level, because doing so would force re-indexing and invalidate receipts.

The `evidence-pack` defaults are the starting point for balanced work: two candidates per query, at most three selected passages per question, at most 16 unique passages, up to 3,500 characters per passage, and a 20,000-character evidence ceiling. The helper divides that ceiling across all selected passages and reports truncated passage IDs, so one long chunk cannot consume the context needed by later facets. The CLI rejects a retrieval payload ceiling above 40,000 characters. Do not override defaults upward before observing a named gap or truncation.

For an unchanged repeat covered by verified findings, these cold-start budgets do not apply. Reuse stable facet IDs/query plans and `--task-receipt`; the helper performs no searches and reopens no passages. A changed or disputed facet receives one targeted support/check pair; unaffected facets are not searched or transferred again. Explicit blind or independent review starts a new cold budget.

## Selection and local escalation

- “quick”, “draft”, or “minimum tokens” selects `compact`;
- an ordinary request selects `balanced`;
- “full audit”, high risk, a dispute, or a high cost of error selects `thorough`;
- a material conflict promotes only its facet from `compact` to `balanced` or from `balanced` to `thorough`.

Do not lower a high-risk facet merely to satisfy a token preference. Do not raise unaffected facets or repeat completed searches when one facet is promoted. Stop when every facet reaches a terminal status within its own budget; report unresolved gaps instead of treating budget exhaustion as negative evidence.
