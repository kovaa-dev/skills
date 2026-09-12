# Kovaa Agent Skills

A collection of reusable agent skills for product documentation and software delivery workflows.


## Included skills

| Skill | Purpose | Source |
| --- | --- | --- |
| `dev-docs` | Product discovery, PRDs, technical tasks, decisions, roadmaps, maintenance, and documentation governance. | [`dev-docs/`](dev-docs/) |
| `dev-rules` | A consistent engineering workflow covering scope, implementation, validation, Git, pull requests, agents, and handoffs. | [`dev-rules/`](dev-rules/) |

The skills are independent and can be installed separately. Their scopes are complementary, but neither skill requires the other: each integrates through the active canonical sources and policies of the target project.

## Repository contents

- `dev-docs/` — source files for the `dev-docs` skill.
- `dev-rules/` — source files for the `dev-rules` skill.
- `skills.sh.json` — optional presentation metadata for the skills.sh repository page.
- `CHANGELOG.md` — repository release history.
- `CONTRIBUTING.md` — contribution guidelines.
- `SECURITY.md` — security reporting policy.

Each skill directory contains:

- `SKILL.md` — the agent-facing entry point and routing instructions;
- `references/` — detailed rules, procedures, and templates;
- `README.md` — a short human-facing overview.

## Installation

Compatible agents can install the skills through the open-source [`skills`](https://github.com/vercel-labs/skills) CLI:

```bash
npx skills add <owner>/<repository> --list
npx skills add <owner>/<repository> --skill dev-docs
npx skills add <owner>/<repository> --skill dev-rules
```

Use `--global` for a user-level installation or omit it for a project-level installation. The CLI selects the appropriate directory for the chosen agent.

For reproducible project use, install from an immutable Git commit SHA rather than a moving branch.

## Version

The current repository version is `v0.1.0`.

## License

Licensed under the [MIT License](LICENSE).
