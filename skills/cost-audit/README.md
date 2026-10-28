# cost-audit

`cost-audit` is a read-only Agent Skill for finding material token and workflow overhead in recent agent sessions and the project instructions that may cause it. It samples expensive and anomalous sessions adaptively, distinguishes measured evidence from estimates, and returns a necessary and sufficient remediation plan.

The skill does not apply changes, edit session logs, install monitoring infrastructure, or treat generic optimization advice as a finding.

## What it audits

- reported input, cache, output, reasoning, and total-token usage when available;
- model and tool roundtrips, errors, exact repeats, compactions, and large tool results;
- effective instruction and configuration surfaces implicated by session evidence;
- measurement gaps, fixed costs, and quality constraints.

## Local analyzer

The optional local helper aggregates supported `.jsonl` and `.jsonl.zst` sessions without printing message content or tool payloads. It defaults to the current project and computes bounded-window usage from event timestamps rather than charging the lifetime of an active session:

```bash
python scripts/cost_audit.py sessions --since 7d --pretty
python scripts/cost_audit.py sessions --project-root PROJECT_ROOT --since 7d --pretty
python scripts/cost_audit.py sessions --input PATH --all-projects --pretty
python scripts/cost_audit.py inspect SESSION_JSONL_OR_ZST --since 7d --until SNAPSHOT_UNTIL --max-buckets 20 --pretty
python scripts/cost_audit.py docs --root PROJECT_ROOT --cwd WORKING_DIRECTORY --pretty
```

The exact Python launcher is environment-specific. Python 3.14+ reads Zstandard through its standard library. Python 3.10–3.13 needs `backports.zstd==1.8.0`; the helper reports that exact command when it is missing and never installs it itself. It streams compressed input and does not create a plaintext copy.

The helper writes JSON only to standard output and creates no database. Session inventory and inspection use schema version 2. `sessions` captures an inclusive upper event-time bound at command start and emits it as `scope.until`; reuse that exact value for every inspection or repeated inventory in the same audit. Relative lower bounds such as `7d` are anchored to this fixed upper bound. Reported session bytes and modification time are bounded to included events, so an active log cannot change proxy selection after the snapshot boundary.

For Codex cumulative counters, the helper subtracts an observed pre-window sample when available. At the start of a log it removes an inherited baseline only when the first cumulative value can be reconciled with the matching `last_token_usage` field; otherwise that field remains `null` and coverage is `partial` or `unavailable`. Repeated cumulative snapshots are deduplicated. `model_usage_steps` counts distinct provider usage increments, `assistant_messages` counts message records, and compatibility field `model_calls` prefers usage steps with a message-count fallback.

Raw file locators are hidden unless `--include-locators` is explicitly supplied. Token coverage and byte-based proxy coverage remain separate; incomplete error visibility is emitted as `null` with `partial` or `unavailable` observability metadata. The `docs` report retains nested Git worktrees, labels the one containing `--cwd`, and calculates document totals and exact duplicates independently for each worktree.

## Package layout

- [`SKILL.md`](SKILL.md) defines the agent workflow and output contract.
- [`references/audit-method.md`](references/audit-method.md) defines evidence and adaptive sampling.
- [`references/apply-plan.md`](references/apply-plan.md) defines the remediation-plan handoff.
- `scripts/cost_audit.py` provides privacy-bounded local aggregation.
- `tests/test_cost_audit.py` covers the analyzer during skill development.
