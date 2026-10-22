# Orchestra

`orchestra` helps an agent choose between direct work, a purpose-built tool, a deterministic helper, and a bounded subagent. It activates only when that choice is material, a capability is missing, work can be isolated, or the current route failed. Routine work stays on the direct fast path.

Use it for meaningful tool-versus-agent choices, missing capabilities, independent work units, large inputs that benefit from context isolation, targeted verification, or recovery from a failed route. Repetition alone does not activate orchestration when a known route is already efficient.

The skill is model-, vendor-, and tool-agnostic. It uses only capabilities exposed by the current environment and does not require a specific MCP server, model catalog, database, or runtime service. It cannot switch the coordinator's model unless the host exposes that control; when supported, model/reasoning selection applies to bounded workers.

Its main rules are:

- permissions, privacy, project policy, and required capabilities are hard filters;
- total expected cost of successful completion matters more than one cheap call;
- tool discovery checks one best candidate first; setup must avoid current repeated work or be necessary for correctness;
- tools handle exact native operations, the coordinator owns integration, and workers receive independent bounded units;
- a completed call is not automatically a completed task;
- equivalent failures are not retried more than twice without changing the method;
- large context and full parent history are not copied into workers.

Package contents:

- `SKILL.md` — fast path, routing workflow, failure handling, and safety invariants;
- `references/routing-policy.md` — detailed selection, switching, outcome, and stopping rules;
- `references/tool-acquisition.md` — capability discovery, installation authority, connection safety, and verification;
- `references/delegation.md` — fresh-context capsule, concurrency, write ownership, and return contract;
- `tests/routing-cases.md` — maintainer-facing behavioral cases for route decisions;
- `agents/openai.yaml` — optional UI metadata.

The package contains no executable code and creates no persistent state.
