# Routing policy

Read this reference only when more than one route remains plausible or the current route must change.

## Eligibility before preference

Apply these constraints in order; a later preference cannot override an earlier one:

1. user scope, authorization, privacy, safety, and project policy;
2. required capability, format, access, write boundary, and verification;
3. runtime availability, health, task budget, and material time constraints;
4. an explicit user choice of tool, executor, or workflow;
5. total effort to produce a usable, verified result.

Do not silently substitute a user-pinned route when that changes semantics, data handling, authority, or output. Explain the incompatibility and offer the nearest eligible route.

## Minimal route matrix

| Work unit | Prefer | Avoid |
| --- | --- | --- |
| Exact lookup, structured query, deterministic transform, repository inspection, or supported mutation | Authorized native tool or existing helper | Reimplementing native behavior in prose or browser steps |
| Short synthesis, warm-context judgment, or integration | Coordinator | A worker that must reread the same context |
| Large self-contained extraction or independent component | One bounded worker | Parent history or a worker per source |
| Several independent units with isolated writes | Small parallel worker set | Parallel mutation of one state owner |
| Consequential ambiguity or conflict | One checker with disputed evidence only | Re-running the complete task |
| Missing capability or authority | Tool-acquisition flow or exact request with fallback | Working around access controls |

## Compare total effort without invented scores

Use observed runtime metrics when available. Otherwise compare eligible routes qualitatively by:

- setup and startup;
- context that must be transferred or reread;
- known attempts and failure history;
- tool calls and round-trips;
- integration and artifact transfer;
- verification before the result is usable;
- maintenance created by acquisition;
- impact of an incorrect or incomplete result.

Select a route that is no worse on the decisive constraints and is simpler on at least one of them. Do not spend a separate model call estimating cost and do not manufacture numeric probabilities. A cheap call is not cheap when it predictably causes retries; a stronger executor is not justified merely because the task is long.

## Stability and change

Keep the route while its assumptions remain true. Re-route only at a natural unit boundary after a material change in intent, required capability, access, health, budget, outcome, ambiguity, verification, or explicit user direction.

Classify evidence correctly:

- **transport outcome:** a command, call, or worker completed, failed, timed out, or was cancelled;
- **operation outcome:** returned data parsed, a transformation was valid, or a bounded analysis met its contract;
- **task outcome:** the user's requested result and acceptance are complete.

Transport completion and executor self-report are not verified task success. Preserve valid completed units and re-run only affected work.

## Trace and stopping

Create no trace for a successful fast path. After acquisition, delegation, a route change, or a material failure, keep at most: selected route, decisive reason, observed outcome, and next action in existing task state. Do not persist prompts, full output, sources, speculative scores, or a new ledger.

Stop orchestrating when acceptance is verified, remaining issues are explicit limitations or blockers, and another route would repeat covered work. Stop delegation when its startup and integration are not smaller than the remaining bounded coordinator work.
