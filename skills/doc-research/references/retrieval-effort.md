# Retrieval effort profiles

Read this reference only when converting the selected `compact`, `balanced`, or `thorough` profile into concrete retrieval budgets for a helper, connector, or project adapter. Effort changes search cost and recall; it never weakens the mandatory evidence and safety invariants in `SKILL.md`.

| Effort | Initial set | Total returned context | Expansion rounds | Additional verification search |
| --- | --- | --- | --- | --- |
| `compact` | 4–6 passages | 8,000–12,000 characters | 1 | Decisive claims only |
| `balanced` | 8–12 passages | About 20,000 characters | 2 | Decisive claims and discovered conflicts |
| `thorough` | 12–20 passages | Up to 40,000 characters | 3 | Contrary evidence and independent verification of material conclusions |

Start at the low end of the passage range. Move toward the high end only for a named gap, weak source diversity, truncated decisive context, or a conflict. Count an expansion round only when it issues another query or continuation for the same facet; reopening selected locators for mandatory verification is not an expansion round.

## Map profiles to existing controls

Do not add or expect a `--effort` CLI option. Translate the profile into the controls already exposed by the selected tool:

- map the initial passage range to `--limit`, or divide it across batched queries with `--limit-per-query`;
- map the context ceiling to `--max-total-chars`; for batched search, divide the same ceiling across `--max-per-query-chars` instead of multiplying the total by the number of queries;
- use `--max-chars` and `--snippet-tokens` to deepen only selected passages; keep their existing defaults unless snippets are clearly truncated or bloated;
- use the table's expansion count as the per-facet workflow cap;
- for `get`, resume, and list operations, request only the selected IDs or active records and keep their combined output inside the same context ceiling.

Exact deduplication, current-receipt checks and reuse, metadata filtering, valid continuation, and index reuse remain automatic; persisting a receipt still requires durable-write authority. Apply a per-source cap only when one source dominates useful diversity; it is evidence-dependent rather than an effort profile. Chunk size is a corpus-index design choice and must not change per query or effort level, because doing so would force re-indexing and invalidate receipts.

## Selection and local escalation

- “quick”, “draft”, or “minimum tokens” selects `compact`;
- an ordinary request selects `balanced`;
- “full audit”, high risk, a dispute, or a high cost of error selects `thorough`;
- a material conflict promotes only its facet from `compact` to `balanced` or from `balanced` to `thorough`.

Do not lower a high-risk facet merely to satisfy a token preference. Do not raise unaffected facets or repeat completed searches when one facet is promoted. Stop when every facet reaches a terminal status within its own budget; report unresolved gaps instead of treating budget exhaustion as negative evidence.
