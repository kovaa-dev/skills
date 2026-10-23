# cost-audit

`cost-audit` is a read-only Agent Skill for finding material token and workflow overhead in recent agent sessions and the project instructions that may cause it. It samples expensive and anomalous sessions adaptively, distinguishes measured evidence from estimates, and returns a necessary and sufficient remediation plan.

The skill does not apply changes, edit session logs, install monitoring infrastructure, or treat generic optimization advice as a finding.

## What it audits

- reported input, cache, output, reasoning, and total-token usage when available;
- model and tool roundtrips, errors, exact repeats, compactions, and large tool results;
- effective instruction and configuration surfaces implicated by session evidence;
- measurement gaps, fixed costs, and quality constraints.

## Local analyzer

The optional standard-library helper aggregates supported local JSONL sessions without printing message content or tool payloads. It defaults to the current project and computes bounded-window usage from event timestamps rather than charging the lifetime of an active session:

```bash
python scripts/cost_audit.py sessions --since 7d --pretty
python scripts/cost_audit.py sessions --project-root PROJECT_ROOT --since 7d --pretty
python scripts/cost_audit.py sessions --input PATH --all-projects --pretty
python scripts/cost_audit.py inspect SESSION_JSONL --since 7d --max-buckets 20 --pretty
python scripts/cost_audit.py docs --root PROJECT_ROOT --cwd WORKING_DIRECTORY --pretty
```

The exact Python launcher is environment-specific. The helper writes JSON only to standard output and creates no database. Raw file locators are hidden unless `--include-locators` is explicitly supplied. Token coverage and byte-based proxy coverage remain separate; incomplete error visibility is emitted as `null` with `partial` or `unavailable` observability metadata. The `docs` report retains nested Git worktrees, labels the one containing `--cwd`, and calculates document totals and exact duplicates independently for each worktree.

## Package layout

- [`SKILL.md`](SKILL.md) defines the agent workflow and output contract.
- [`references/audit-method.md`](references/audit-method.md) defines evidence and adaptive sampling.
- [`references/apply-plan.md`](references/apply-plan.md) defines the remediation-plan handoff.
- `scripts/cost_audit.py` provides privacy-bounded local aggregation.
- `tests/test_cost_audit.py` covers the analyzer during skill development.
