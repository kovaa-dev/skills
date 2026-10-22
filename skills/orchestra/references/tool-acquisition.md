# Tool discovery and acquisition

Read this reference only when a capability is missing, an installation or connection is being considered, or repeated work may justify a helper.

## Define the capability, then stop early

Specify the smallest useful contract: input/output format, operation, required fidelity, scale, access boundary, platform, verification, and current repetition. Do not begin with a product name.

Check the single best likely candidate in this order:

1. runtime-provided app, API, MCP tool, or connector;
2. project command, script, dependency, runtime, or package environment;
3. installed CLI or native application with a documented interface;
4. isolated task-local dependency or disposable helper;
5. durable project dependency/helper, system package, plugin, or service with the required authority;
6. bounded browser or manual fallback.

Probe availability and one representative capability operation. Presence alone does not prove fitness. Consider a second candidate only when the first is unavailable, loses required semantics, or cannot provide required verification. Expand beyond that only if correctness would otherwise be blocked. Use authoritative current documentation when installation or usage semantics are unknown.

## Acquisition threshold

Acquire when either condition holds:

- it avoids at least two expected repetitions in the current task or an already established repeated workflow; or
- native parsing, identity, structure, validation, or verification is necessary for a reliable result.

Do not acquire for a small reliable one-off, convenience alone, or speculative future reuse. Complexity by itself is not a reason. Compare setup, startup, maintenance, context saved, calls and retries avoided, output boundedness, and verification quality; do not build a benchmark or make a model call just to estimate them.

## Authority

| Acquisition | Proceed without another question only when | Otherwise |
| --- | --- | --- |
| Task-local package, environment, or disposable helper | Existing policy permits it; isolated and reversible; no elevation, credentials, terms, upload, broader access, or persistent project change | Request the exact action and scope |
| Project dependency or durable helper | Current task and project policy authorize the change, it has a current consumer, and no material runtime or maintenance trade-off is introduced | Request approval and describe persistence and affected files |
| System/global package, daemon, or extension | Existing authority covers that exact system-level change | Request approval; never elevate implicitly |
| MCP, plugin, SaaS, account, or connector | Already installed, connected, authorized for the data scope, and permitted for the requested operation | Request the exact connection, account/scopes, data transfer, and fallback |
| Credential, paid service, license acceptance, or external upload | Never infer authority | Obtain explicit authorization first |

Use native approval and connection flows. Do not edit hidden global configuration, scrape credentials, invoke undocumented private interfaces, or ask a worker to acquire a capability for the coordinator.

## Update, verify, and use

Before a material acquisition or connection, state once: required capability and unit, selected action and persistence, expected gain, permissions or data transfer, representative verification, and bounded fallback. This is an update rather than a redundant question when existing authority already permits the exact action.

After acquisition:

1. verify identity/version only as compatibility requires;
2. run one safe representative capability check;
3. use the tool for the intended operation in the same task;
4. keep output bounded and retain only actionable diagnostics;
5. remove a disposable failed or unused install when safe, or report its residue.

Reuse a successful route from existing session/task/project state without reprobe while environment, version, source boundary, required capability, and prior outcome remain unchanged. Do not create a tool inventory or recommendation database.

Retry once only for a plausibly transient transfer or corrected invocation. Otherwise change candidate, use the stated fallback, or report the blocker. Stop after two equivalent failures.

## Custom helper

Use a task-local helper only for a deterministic operation when no sufficient tool exists and the helper is cheaper than the repeated work. Make it durable only for a current repeated consumer and established project owner. Test the behavior that justifies it, then remove a disposable helper unless it is the minimum reproducible artifact the task requires.
