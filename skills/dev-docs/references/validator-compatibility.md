# Validator compatibility during the transition

The canonical schemas are [requirements](requirements.md) and [work queues](work-queue.md).
Inspect actual project parsers and constraints; retain compatible checks and adapt only
assumptions that conflict with the target model. Use [source assessment](source-transition.md)
for selected work and [migration](governance-migration.md) for an explicit one-shot transition.

The skill does not ship project validators. Inspect actual tools/configuration before
naming commands, assuming paths, or claiming automation. Do not install another tracker
or runtime merely for compatibility.

## Adapt real enforcement

An existing parser may constrain paths, ID syntax, document structure, status fields,
or relationships between an index and its owners. Scope those checks to
remaining source sources while adapting affected samples and checks for:

- specification requirement IDs/anchors, revision/applicability, and real links;
- one primary selection entry and status owner, matching queue status copies,
  cross-queue references, and result/history links;
- prerequisite versus reference/supersedes/rationale relationships and self/cycle checks;
- historical verification versus proof of the current requirement revision;
- converted notices and the route to new canonical owners.

Do not force requirements or queues into incompatible source formats, silently disable CI, or
claim that Markdown computes reverse links/readiness. Update parser assumptions,
fixtures, and callers together when that enforcement change is authorized.
A stale parser that makes the transition impossible is an explicit blocker to resolve,
not permission to continue affected implementation without capture.

## Limits and portability

Keep project-specific paths, number length, languages, retired paths, and ignored
directories configurable. Another repository's source checker is not automatically
portable. If an existing root TODO redirect is required by an obsolete parser, adapt
the requirement rather than creating an unnecessary competing entrypoint.

Use the project's actual checks. Verify a representative converted requirement,
cross-queue wait, completed result, and remaining source redirect when applicable.
Structural validation does not prove accepted meaning, factual truth, complete migration,
or product/security behavior; compare source and destination semantics separately.
