# Tracker Rules

Canonical rules for tasks and decisions; no external `RULES.md` is required.
General requirements and project settings are defined in the [documentation policy](documentation.md).
The [card forms](documentation-registers-template.md) follow these rules;
historical templates no longer apply.

- Each file contains exactly one product task, `PRD-NNN`, or one technical task,
  `<LAYER>-NNN`. The number is stable, does not encode a release or phase, and is never
  reused. Technical prefixes come only from the project's explicit layer registry
  (for example, AUTH and WEB). PRD, TD, and ADR are reserved for record types;
  DOC may be explicitly designated for documentation maintenance. A prefix does not
  automatically assign a team or implementer. Subtasks such as `<LAYER>-NNN.1` are
  local checkboxes; work that can be planned independently belongs in a separate task.
- A fully groomed product task defines the outcome, scenario, constraints, acceptance
  criteria, product dependencies, and links to technical tasks when independently
  planned technical work is actually needed. Product-slice composition is defined only
  here. A PRD represents a user outcome of any size, not necessarily a phase. Before
  grooming, a minimal backlog PRD may be registered with a stable ID, source,
  hypothesis/problem, an owner or `unassigned`, and open questions. Do not fill it with
  invented scope, acceptance criteria, a delivery/release date, or a predetermined
  solution; preserve the date of a known source. A `backlog → planned` transition
  requires accepted grooming. If a new outcome changes the contract of an already
  closed PRD, the new card gets a `Replaces` link to the previous one; the `done` card
  and its closure are not rewritten.
- A PRD is a product task: it defines the user outcome to achieve and how to accept it.
  An implementer may take an entire `planned` PRD as one product workstream after the
  start brief is confirmed. A small, single-owner PRD with no independently planned
  technical outcomes may be implemented directly and does not receive fictitious child
  cards. If a PRD contains several independent layer outcomes, an agent may take the
  whole slice, but canonical technical tasks retain their own statuses and move to
  `in-progress` only when work on them actually starts. A PRD always requires end-to-end
  user acceptance before `done`, not merely closure of its children.
- A PRD's composition is defined through links to technical layer tasks. Each describes
  a complete, verifiable increment within one layer and may contain local checkbox
  subtasks. One technical task may relate to `0..N` PRDs, but the composition and
  end-to-end acceptance of each PRD belong to its product owner; the technical owner is
  responsible only for the technical outcome. A backlink registry of PRDs is
  unnecessary in the technical card: relationships are discovered through owning PRDs.
  If shared work has different delivery boundaries or independently accepted parts,
  split it into separate tasks. A PRD does not select individual checkboxes from an
  incomplete card. Layers grow through sequential tasks, not an endless checklist.
- A technical task may be part of a feature, a bug, or a standalone engineering outcome:
  a migration, dependency/runtime update, technical debt/refactor, security,
  reliability/performance, observability/operations, CI/tooling, investigation,
  platform capability, or removal of an obsolete system. These are descriptive
  categories, not mandatory status/type tokens. If the project uses intake types,
  standalone work defaults to `maintenance`, except for `bug` and `investigation`, or
  to an explicitly configured extension. A standalone task without a PRD is allowed only
  when it has a specific source/rationale, an observable outcome, impact, acceptance
  criteria, an owner, and a place on the roadmap. If the work is needed by only one
  feature, link it to the PRD; if it changes the user-facing contract, create or update
  a PRD. Do not create a fictitious PRD for work that has no new user outcome. Deferred
  technical work receives its own ID only when the user has asked to preserve it or when
  it is an independently actionable blocker, dependency, or unresolved high-risk item
  that outlives the current task. Local steps toward the current outcome remain its
  checkboxes.
- During `audit` and `migrate`, refine registered work into a dependency-ready graph:
  identify independently executable outcomes, each with one layer owner, explicit
  prerequisites, acceptance criteria, and no hidden dependency on a shared canonical
  file or decision. Mark non-blocking tasks with links to indicate that they may run in
  parallel, but this does not automatically launch agents. Do not split a small sequential
  migration merely to create parallelism, and do not create a card without an independent
  outcome.
- If independent tracks require a separate consolidation of shared indexes, contracts,
  or source mappings, conflict resolution, or end-to-end verification, create an
  integration task only when it has its own verifiable outcome. It depends on all input
  tracks, owns only the shared boundary, and does not copy their acceptance criteria or
  statuses. A trivial merge or coordinator review does not warrant a fictitious
  integration task. Actual agents, worktrees, and integration follow the active
  project-work policy.
- In a read-only audit, this decomposition remains a proposed task map in the response;
  cards are created only when writes are permitted and after checking for duplicates and
  applying the registration threshold.
- Do not turn every request, question, or line of reasoning from a conversation into a
  card. Register an explicitly requested backlog item, agreed deferred work, or a
  significant unresolved outcome that meets the criteria above. Other ideas and
  suggestions remain in the final response or read-only discussion until the user
  explicitly asks to preserve them. Before creating a card, check existing cards and
  preserve the actual source.
- Architectural decisions have IDs of the form `ADR-NNN`, and technical decisions use
  `TD-<LAYER>-NNN`. Each has one canonical document, a status of `proposed`, `accepted`,
  or `superseded`, boundaries, contract/data, consequences, verification, and
  migration/rollback guidance. A decision is neither a task nor a milestone.
- Technical decisions and technical cards do not contain product phases, PRD scope,
  MVP codes, or release queues. A technical card links to decisions and technical
  prerequisites; decisions depend on other decisions, not on the closure of a UI task.
  Product-slice scope is defined only in the PRD. A technical task may link to a specific
  PRD requirement as its source, but not as a reverse registry of phase membership. Such
  a link is not a prerequisite and does not copy the scope, statuses, release order, or
  requirement text. Do not present a pending decision as accepted or an implementation
  as complete.
- Every task and decision has one canonical status and one accountable owner, recorded
  in the canonical card. `unassigned` is permitted when an item is first registered in
  the backlog. Before `planned`, an owner is assigned, scope and acceptance are
  accepted, explicit dependencies are named, and the card contains
  `- Grooming: completed YYYY-MM-DD; source: <exact confirmation or stable link>`.
  Substantive results remain in normal contract/acceptance/decision sections rather
  than being copied into this field. A `planned` task without grooming evidence is a
  migration defect, not ready work. Do not retrospectively rewrite historical `done`
  cards solely to add the new field. Contributors do not become a second owner. Scope
  and API definitions remain in their canonical sources.
- The shared task index is the sole roadmap and lists every registered task exactly once.
  For a new product, propose the delivery groups `Alpha`, `Beta`, `RC`, `Release`, and
  `Next` by default, but the user may rename, combine, extend, or replace them with a
  different sequence. Within a group, Product and actual technical-layer subgroups are
  allowed. An active task belongs to exactly one delivery group. A completed or cancelled
  task remains in its last assigned group or is moved exactly once to `History`.
  `History` is a visible part of the roadmap, but it is not a delivery stage or evidence
  of delivery. For an existing product, first determine the current state and future
  sequence: assign an open legacy task to a current or future group without claiming a
  past stage, and place a historical `done` or `cancelled` task in `History` if its former
  group is unknown.
- The standard groups mean: **Alpha** — a minimally usable working product for personal use
  or a narrow group, plus technical shakedown; **Beta** — core capabilities, with
  breaking changes still permitted; **RC** — feature freeze, fixes, data recovery, and
  operational readiness; **Release** — work for the target or currently supported public
  boundary; **Next** — capabilities and maintenance beyond that boundary. A group
  expresses queue intent, not a milestone, product contract, or proof of delivery, and
  is not encoded in the ID. The actual release is recorded in a release record. When
  replanning, move the task rather than duplicating it. General grooming prepares the
  nearest stage for a safe start; later stages are refined closer to implementation based
  on feedback.
- Beside each link, the task index shows a compact status projection from the card so
  reviewing the queue does not require opening every file. The projection uses the same
  explicit token (`backlog`, `planned`, `in-progress`, `need-info`, `blocked`, `done`, or `cancelled`),
  does not become a second source of truth, and is updated in the same change as the
  canonical status. A mismatch between the card and index is a defect. Strikethrough may
  be used only as supplementary formatting, never instead of the token, because it cannot
  distinguish `done` from `cancelled`. The index/backlog still contains only the delivery
  group, internal grouping/order, links, and status projection; it does not copy the
  owner, acceptance criteria, dependencies, progress, blocker, or task description.
- The entry point is the task index configured by the project (by default,
  `docs/tasks/index.md`). The README and instructions link directly to it, with no root
  redirect file. Delivery phases are not a second plan. A layer contains a decision
  index, not another list of phases or tasks. Backlinks are derived rather than manually
  maintained in a second location.
- Update progress when the state of an independently meaningful step changes materially:
  when it starts, finishes, becomes blocked, is cancelled, or gets a new next action. Do
  not create or update a checkbox for every internal action in one session. An incomplete
  tracked step remains `[ ]`; the blocker and next action belong in the card, not the
  index.
- Task statuses are `backlog`, `planned`, `in-progress`, `need-info`, `blocked`,
  `done`, and `cancelled`. They represent actual state rather than a rigid state
  machine, but each token has one meaning. `backlog` contains unscheduled or not-yet-
  groomed work. `planned` means the grooming contract is accepted and the task is in
  an executable queue with no unmet blocking prerequisite. `in-progress` is set only
  after a short execution brief and explicit user confirmation to start. A direct
  `backlog → in-progress` transition is prohibited: even within one session, record
  accepted grooming and `planned` first. The initial request may already confirm the
  same brief, in which case no redundant question is required.
- `need-info` means a specific question or conflict arose after `planned` and safe work
  cannot continue without an external answer or decision. The card states the question,
  why it blocks, the recommended option, realistic alternatives, and the answer owner.
  A routine reversible implementation detail is not `need-info`. After an answer, the
  task returns to `planned` or `in-progress`; a materially changed contract updates the
  grooming evidence and `Decision changes` before work continues.
- `blocked` means an unmet prerequisite, external artifact/event/environment result, or
  another adjacent dependency—not a child relationship and not missing information.
  The card must contain `- Blocker: <exact link/condition and reason>` and
  `- Unblock condition: <observable result>`. PRD→task defines composition, while
  task→task or PRD→PRD prerequisites define blocking relationships; a child does not
  block automatically. Once unblocked, a task that never started returns to `planned`;
  paused work returns to `in-progress`. A PRD becomes `blocked` only when the entire
  remaining path to the user outcome is blocked, not because one independently
  avoidable child is blocked.
- `cancelled` requires a reason and, when applicable, a replacement link;
  `backlog → cancelled` does not require full grooming. A cancelled task may resume
  without erasing its previous reason. `done` is terminal: a regression, new scope, or
  changed outcome receives a new linked task, while the completed task's closure,
  checklist, and evidence remain unchanged. Transition to `done`, including from
  `blocked`, is allowed only after actual acceptance.
  A routine `done` task needs only one closure statement: the observable result, the
  current canonical decision source, and the verification or manual path used. For an
  implemented or changed documented contract, first perform the
  [implementation closure reconciliation](documentation.md#implementation-closure-reconciliation):
  any unresolved discrepancy blocks `done`. A date, version, or artifact is required only
  for a release, migration, external audit, benchmark, security/privacy evidence, or an
  outcome that cannot be reconstructed from the task, commit, or PR. PRD acceptance is an
  end-to-end user outcome, not an automatic consequence of closing technical tasks.
- Perform migrations in small, verifiable increments: declare the boundaries, sources,
  destinations, and acceptance criteria for the current increment. Before rewriting,
  preserve a recoverable checkpoint (an available VCS revision, patch, or exact copy);
  do not rely on reconstructing text from memory. After producing a substantial new
  result, preserve it before the next move or rewrite. During migration, a scoped
  replacement of old text with pointers and relocation into clearly designated history
  are allowed after checkpointing and copying/moving. Do not accumulate two current
  versions. Historical `*.history.md` files are not plans; their internal wording is no
  longer authoritative, and closed evidence remains unchanged. During an agreed naming
  migration, previous IDs, including those of closed records, may be reassigned by
  applying the “Hard migration: names and IDs of historical documents” section of the
  [migration process](governance-migration.md). Outside such a transition, IDs remain
  stable.
- Before completing a routine migration, check only the active changed mappings, links,
  agreement between the status projections and canonical cards of affected tasks,
  uniqueness of affected IDs, and absence of lost or duplicated tasks. A complete
  reconciliation of every requirement, question, dependency, and piece of evidence is
  required only for an explicitly requested full review or full backlog migration. List
  any agreed scope that was not migrated; do not present a partial migration as complete.

## Related Workflows

- [Maintenance, bugs, findings, and continuous improvement](maintenance.md).
- [Product discovery](product-discovery.md).

## Baseline Format

The baseline format uses one H1, `# <ID> <Title>`; a filename of `<ID>.md`; and separate
`- Status: backlog`, `- Owner: <one accountable owner>`, and
`- Grooming: incomplete` lines. Explicitly use `unassigned` for backlog items without
an assigned owner. After accepted grooming, replace the value with the completion date
and exact source. `blocked` additionally requires `- Blocker:` and
`- Unblock condition:`. Task and decision statuses use the lowercase tokens listed
above, not free-form text. Product dependencies are PRD→PRD,
technical prerequisites are task→task, and decision dependencies are decision→decision.
`Replaces` is a historical relationship between a new PRD and its closed predecessor,
not a prerequisite or a reason to change the old card. Decision links in tasks belong in
a separate field, not among technical prerequisites. A task links to the applicable
requirements source or technical contract when one exists; the absence of a TD/ADR does
not itself block work. A new TD/ADR is needed for a genuine technical choice, not for
every fix or investigation. Uncertainty and the plan for resolving it belong to the
owning PRD or task. Agree on a new choice just in time, before the implementation it
changes; do not resolve future questions prematurely merely to create formal readiness.

The project chooses paths, the language of metadata fields, and the number length. The
format above is the default profile, not a requirement for every parser. If validation
exists, coordinate changes with it. See [Optional compatibility](validator-compatibility.md).

## Optional Assignments

If the project-work process uses assignments, each assignment links to the canonical task
and may contain only the sub-scope or expected handoff outcome that is necessary. An
assignment does not copy the task's status, owner, acceptance criteria, or decisions, and
does not become a second tracker. Rules for launching workers, write scopes, the
coordinator, and review belong to the active project-work policy; this tracker does not
define them.
