# Retrieval effort profiles

Read this reference only when converting the selected `compact`, `balanced`, or `thorough` profile into concrete retrieval budgets for a helper, connector, or project adapter. Effort changes search cost and recall; it never weakens the mandatory evidence and safety invariants in `SKILL.md`.

| Effort | Suggested initial set | Suggested initial context | Additional verification search |
| --- | --- | --- | --- |
| `compact` | 4–6 passages | 8,000–12,000 characters | Decisive claims only |
| `balanced` | 8–12 passages | About 20,000 characters | Decisive claims and discovered conflicts |
| `thorough` | 12–20 passages | Up to 40,000 characters | Contrary evidence and independent verification of material conclusions |

These are soft starting budgets, not caps on research rounds or prerequisites for a larger first read. Choose enough breadth and depth for the question: a table, amendment, enumeration, or parent/child constraint may need more context immediately. Keep each call inside the tool's resource limits, consume valid continuation, and refine queries as evidence reveals useful terms or cross-references. Do not mistake exhausted output for an exhausted source.

Batch independent searches and reads with `evidence-pack`, `search-many`, or available parallel calls. Sequential refinement is normal when the next query depends on the previous result. Reuse current query receipts and exact verified findings, but retrieve again when the question, source generation, coverage, or needed context changes. No named-gap declaration or pack-first gate is required.

## Map profiles to existing controls

Do not add or expect a `--effort` CLI option. Translate the profile into the controls already exposed by the selected tool:

- map the initial passage range to `evidence-pack --max-passages`. `--max-passages-per-question` is the lookup cap; enumeration facets use bounded `max_items`/`group_by`, while schema facets use `max_items` for structural facts plus contextual passages. All remain inside the same per-call ceiling. Use `--limit-per-query` for needed candidate breadth;
- map the context ceiling to `--max-total-chars`; it bounds reopened evidence rather than intermediate search snippets;
- use `--max-passage-chars` to retain the necessary structural unit, including nearby conditions and parent definitions;
- for `get`, resume, and list operations, request selected IDs or active records, use returned continuation, and bound each response. A cumulative task budget is separate from a response limit.

Exact deduplication, current-receipt checks and reuse, metadata filtering, valid continuation, and index reuse remain automatic; persisting a receipt still requires durable-write authority. Apply a per-source cap only when one source dominates useful diversity; it is evidence-dependent rather than an effort profile. Chunk size is a corpus-index design choice and must not change per query or effort level, because doing so would force re-indexing and invalidate receipts.

The `evidence-pack` defaults are a balanced starting point: two candidates per query, at most three selected passages per lookup facet, 16 unique passages overall, up to 3,500 characters per passage, and a 20,000-character evidence ceiling. Structural facts and passages share that budget. The hard pack limits are 200,000 total characters, 100,000 characters per passage, 50 passages, and 50 candidates per query. These are resource ceilings, not suggested defaults. The helper retains useful whole chunks when possible and returns continuation for omitted context rather than dividing the budget equally across all candidates. `get --around QUERY` selects matching context; `--start-char` continues a passage. Candidate counts and lexical role coverage never prove the number of business variants or complete answers. Continue bounded retrieval where needed, then verify the claims explicitly.

For an unchanged repeat covered by verified findings, these cold-start budgets do not apply. Reuse stable facet IDs/query plans and `--task-receipt`; the helper performs no searches and reopens no passages. A changed or disputed facet receives targeted support and the contrary-evidence check appropriate to its verification intent; this need not be a separate query if the relevant evidence is already available. Unaffected facets are not searched or transferred again. Explicit blind or independent review starts a new cold budget.

## Selection and local escalation

- “quick”, “draft”, or “minimum tokens” selects `compact`;
- an ordinary request selects `balanced`;
- “full audit”, high risk, a dispute, or a high cost of error selects `thorough`;
- a material conflict promotes only its facet from `compact` to `balanced` or from `balanced` to `thorough`.

Do not lower a high-risk facet merely to satisfy a token preference. Do not repeat unchanged completed work when one facet needs more evidence. Stop when the question is answered with adequate support, further authorized retrieval would not resolve the limitation, or an explicit task/resource limit is reached. Report unresolved scope and continuation rather than treating budget exhaustion as negative evidence.
