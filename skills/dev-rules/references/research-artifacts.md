# Research artifacts

Rules for investigations, benchmarks, capacity probes, and experimental comparisons.
Retain conclusions and the inputs needed for meaningful reproduction while bounding
working data. Follow the project's documentation settings; this reference does not
create a tracker, evidence registry, archive service, or authority for external storage.

## Necessary and sufficient measurements

Every measurement must be necessary and sufficient for a specific question in the
current authorized task, current risk, or material claim. Necessary means it resolves a named uncertainty
that affects the choice or verification; if existing evidence is sufficient, a new
run is unnecessary. Sufficient means the smallest reliable scope that supports the
stated conclusion, without extra metrics, scenarios, repeats, or infrastructure.

- Before running, name the question, measurement rationale, comparison baseline,
  material metrics, representative workload, and stopping criterion. Agree on unknown
  thresholds instead of inventing them. A small smoke run does not establish production
  capacity or an SLO.
- Performance measurement is needed for an accepted SLO/capacity/cost/support claim,
  a known hot path/constrained workload, a new resource-sensitive mechanism, or an
  observed budget regression. Do not create benchmark infrastructure for a routine
  UI/correctness/refactor change without such a reason.
- Start with a simple baseline and the smallest set sufficient for the current
  conclusion. Expand the corpus or repeats only for material variability, an uncovered
  boundary, or a new hypothesis; justify the uncertainty the expansion will resolve.
- Stop when the criterion is met. If evidence is insufficient, bound the conclusion
  or report an inconclusive result; do not expand indefinitely for evidence completeness.
  A successful repeat without a new reason does not require another repeat.
- A numeric metric is not mandatory for every check: an observable scenario, test,
  or reasoned comparison may be sufficient. This does not waive required correctness,
  security, or recovery checks.

## Before running

- Check existing generators, reports, and corpora; reuse suitable inputs without
  copying them for each algorithm. A small run before scaling also establishes
  expected disk usage.
- Use one gitignored working directory per run according to project settings;
  otherwise use `.evidence/research/<study-slug>/<run-id>/` in the current worktree
  with a local ignore. Separate inputs from regenerable outputs; parallel runs have
  distinct run IDs. `/tmp` is not durable storage.
- Estimate peak disk needs for inputs, outputs, temporary databases, packaging, and
  restoration checks. Check free space and choose a working limit for the disk and task.
  If size is unknown, measure a small run before scaling; an estimate is not a measurement.
- Use normal shared Go/pnpm/toolchain caches. An isolated cache or dependency copy
  needs a specific isolation/version check; keep it in the working directory and
  include it in cleanup. Do not back up the entire previous run before a rerun.
- Temporary processes, containers, volumes, and databases have an identifiable study
  owner. Shared development services and application data are outside its cleanup.
  Use synthetic data; exclude credentials and user content from published evidence
  and archives.

## During work

- After the small run and before expansion, measure disk usage, file count, and free
  space. Summed content sizes omit the overhead of many small files and are not disk usage.
- Process variants sequentially when concurrency is not needed by the measurement.
  Do not keep a full corpus at every step; delete verified derived data when no longer
  needed.
- Near the working limit, stop generation, remove unnecessary outputs, or reduce the
  set. Do not continue through unaccounted directories.
- Use existing `finally`/`trap`/teardown for created processes and temporary resources.
  After a crash or resume, inspect the run's leftovers before creating more resources.
  Do not overwrite unique inputs that cannot be recovered.

## What to retain

| Artifact | Rule |
| --- | --- |
| Conclusions, material measurements, limitations, and reproduction code | In the existing canonical report/evidence and benchmark scope, under version control |
| Deterministic synthetic inputs | By default retain the generator, parameters, seed, versions, and command; regenerate data |
| Exact inputs for a current architectural comparison or regression | A minimal compressed corpus when regeneration cannot provide the required match |
| Derived formats, temporary databases, browser profiles, repeated outputs, isolated caches | Delete after validating the result |
| Closed/rejected experiments with no concrete consumer for original bytes | Keep the report and recipe, without the working environment |

For each retained corpus, name the current conclusion or regression it verifies.
For a defect, prefer a minimal reproducer to a full corpus. Do not archive everything
just in case.

Distinguish semantic from byte-for-byte reproduction. A seed does not guarantee the
same CRDT bytes: account for client IDs, time, operation order, and library versions.
Do not promise identical timings; retain measurement conditions and method.

## Archive and restoration

- Package only necessary inputs in one archive using an available tool, such as
  `tar.zst` or `tar.gz`. Do not install a compressor solely for packaging or promise
  large savings for already compressed data.
- Keep the archive outside the disposable run in the configured gitignored location;
  the local default is `.evidence/research/<study-slug>/archive/`. Do not add large
  binaries to Git. Use external disks/cloud storage only within existing authorization.
- In the existing report/evidence README, record the revision and preservation of
  changed sources, commands, parameters, versions, corpus contents, input/archive
  SHA-256, actual size, location, and restoration commands. Do not create a new registry.
- Before deleting the only original corpus, extract the archive into a clean temporary
  directory, verify hashes, and run a minimal reading/reproduction check. Successful
  packaging or an archive listing does not replace restoration validation.
- Remove the verification extraction; unpack a corpus only for the duration of a
  repeated study. A local archive is not a backup against disk loss. If verified
  preservation is unavailable, retain required originals and report their paths and
  reason; do not claim cleanup is complete.

## Completion and handoff

Before completing a study, retain the report and minimal measurements, check the
reproduction commands, and eliminate undocumented dependencies on old `/tmp` data.
Inputs must be regenerable or restorable from the specified archive. Stop created
processes and remove the run's containers/volumes/databases, isolated caches,
dependency copies, and working outputs; do not use global prune.

Before deleting, verify the exact path and run owner. Do not use a wildcard to remove
neighboring studies, shared caches, or application data. These rules do not authorize
bulk cleanup of old directories or reduction of accepted evidence-retention obligations.

In the final response, report what was cleaned, actual remaining artifact size,
location, and restoration method. For each retained working resource, name its reason
and cleanup condition. On pause/handoff, keep the minimum needed to continue and
exact paths in the existing handoff/report; a pause does not replace completed-run cleanup.
