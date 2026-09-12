# Kovaa Agent Skills

A collection of independent Agent Skills for product documentation and reliable software delivery workflows.

[![Validate](https://github.com/kovaa-dev/skills/actions/workflows/validate.yml/badge.svg)](https://github.com/kovaa-dev/skills/actions/workflows/validate.yml)
[![skills.sh](https://skills.sh/b/kovaa-dev/skills)](https://skills.sh/kovaa-dev/skills)

## Included skills

| Skill | Purpose | Source |
| --- | --- | --- |
| `dev-docs` | Product discovery, PRDs, technical tasks, decisions, roadmaps, maintenance, and documentation governance. | [`skills/dev-docs/`](skills/dev-docs/) |
| `dev-rules` | Engineering execution covering scope, implementation, validation, Git, pull requests, agents, and handoffs. | [`skills/dev-rules/`](skills/dev-rules/) |

The skills are independent and can be installed separately. Their scopes are complementary, but neither requires the other: each integrates through the canonical sources and policies already selected by the target project.

## Install with `npx skills`

The open-source [`skills`](https://github.com/vercel-labs/skills) CLI discovers both skills directly from this public repository. Node.js and `npx` are required; no global CLI installation is necessary.

List the available skills without installing them:

```bash
npx skills add kovaa-dev/skills --list
```

Install one skill into the current project:

```bash
npx skills add kovaa-dev/skills --skill dev-docs
npx skills add kovaa-dev/skills --skill dev-rules
```

Install both skills into the current project:

```bash
npx skills add kovaa-dev/skills --skill '*'
```

Project installation is the default. The CLI detects compatible agents and lets you choose the targets and whether to use symlinks or copies.

### Global and agent-specific installation

Install one skill globally:

```bash
npx skills add kovaa-dev/skills --skill dev-docs --global
```

Install both skills globally and choose from the detected global-capable agents:

```bash
npx skills add kovaa-dev/skills --skill '*' --global
```

For a non-interactive installation, repeat `--agent` for each desired target:

```bash
npx skills add kovaa-dev/skills --skill dev-rules --global --agent codex --agent cursor --yes
```

Without `--agent`, the CLI detects installed agents and prompts for a selection. Do not combine `--global` with `--agent '*'` in `skills@1.5.26`: the registry also contains project-only agents that cannot accept a global installation.

### Use without installing

Generate a prompt for a skill without keeping an installed copy:

```bash
npx skills use kovaa-dev/skills --skill dev-docs
npx skills use kovaa-dev/skills --skill dev-rules
```

### Update or remove

```bash
npx skills update dev-docs dev-rules
npx skills remove dev-docs dev-rules
```

Use `--global` with update or remove when managing a global installation.

### Reproducible installation

For a repository-pinned project policy, install from an immutable commit instead of a moving branch:

```bash
npx skills add https://github.com/kovaa-dev/skills/tree/<commit-sha> --skill dev-docs
```

Replace `<commit-sha>` with a full commit SHA reviewed by the project.

### CLI telemetry and skills.sh

For confirmed public GitHub repositories, the `skills` CLI sends anonymous repository and skill identifiers used by [skills.sh](https://skills.sh) discovery and ranking. It does not send project contents or personal information. Disable this telemetry when needed:

```bash
DISABLE_TELEMETRY=1 npx skills add kovaa-dev/skills --list
```

No separate submission to skills.sh is required. A telemetry-enabled installation from the public repository makes the skills eligible for indexing; appearance and ranking are controlled by skills.sh.

## Install as a Codex plugin

This repository also contains a Codex plugin manifest and a self-hosted marketplace. Add the marketplace, then install the bundle:

```bash
codex plugin marketplace add kovaa-dev/skills
codex plugin add kovaa-agent-skills@kovaa-dev
```

The plugin installs both independent skills. Restart the active Codex conversation after installation or update so newly installed instructions can be discovered.

The self-hosted marketplace works independently of inclusion in the curated [`openai/plugins`](https://github.com/openai/plugins) marketplace. Curated inclusion requires a separate upstream review and cannot be guaranteed by this repository.

## Repository contents

- `skills/dev-docs/` — source files for the `dev-docs` skill;
- `skills/dev-rules/` — source files for the `dev-rules` skill;
- `.codex-plugin/plugin.json` — Codex plugin manifest;
- `.agents/plugins/marketplace.json` — self-hosted Codex marketplace entry;
- `skills.sh.json` — presentation metadata for the skills.sh repository page;
- `scripts/validate.py` — dependency-free repository validation;
- `.github/workflows/validate.yml` — pull-request and `main` validation;
- `CHANGELOG.md` — repository release history;
- `CONTRIBUTING.md` — contribution guidelines;
- `SECURITY.md` and `PRIVACY.md` — security and privacy information.

Each skill directory contains:

- `SKILL.md` — the agent-facing entry point and routing instructions;
- `references/` — detailed rules, procedures, and templates;
- `README.md` — a short human-facing overview.

## Development and validation

Run the same local checks used by CI:

```bash
python3 scripts/validate.py
DISABLE_TELEMETRY=1 npx --yes skills@1.5.26 add . --list
```

The validator checks frontmatter, names, descriptions, local Markdown links and anchors, fenced blocks, machine-local paths, manifests, and the skills.sh grouping.

## Version

The current repository and plugin version is `v0.1.0`.

## License

Licensed under the [MIT License](LICENSE).
