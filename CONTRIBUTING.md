# Contributing

Thank you for your interest in improving these agent skills.

## Principles

- Keep each skill focused on its declared responsibility.
- Put detailed rules in `SKILL.md` or the appropriate reference, not in README files.
- Avoid duplicating normative requirements across skills and references.
- Preserve existing product and engineering semantics unless a change is explicitly proposed.
- Keep examples illustrative; do not turn placeholders into mandatory architecture.
- Use relative links for files within a skill.

## Making a change

Open an issue before substantial behavioral, governance, or compatibility changes so the scope can be agreed before implementation. External contributions are accepted through pull requests; only the maintainer can update protected branches or merge changes.

1. Identify the canonical file that owns the rule or template.
2. Check related references for contradictions before editing.
3. Make the smallest coherent change.
4. Update affected templates and navigation.
5. Verify frontmatter, relative links, Markdown fences, and whitespace.
6. Run the development checks described below.
7. Describe behavioral or compatibility effects in the pull request.

Changes that alter the meaning of both `dev-docs` and `dev-rules` should be reviewed as one coherent update.

## Development and validation

Use Python 3.12 or newer and install the pinned validation dependencies in your
development environment (for example, a virtual environment). Run the same checks as CI:

```bash
python3 -m pip install -r scripts/requirements-validation.txt
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/validate.py --check-cli
```

The release-policy check uses Release Please 17.3.0, matching the engine bundled in the pinned release action. Keep that test dependency aligned when upgrading the action. Install it outside the repository so validation does not scan its files:

```bash
RELEASE_POLICY_DEPS="$(mktemp -d)"
export RELEASE_POLICY_DEPS
npm install --prefix "$RELEASE_POLICY_DEPS" --no-save --package-lock=false --ignore-scripts --no-audit --no-fund release-please@17.3.0
node --test scripts/release-policy.test.cjs
rm -rf "$RELEASE_POLICY_DEPS"
```

The validator checks YAML metadata, names, descriptions, local Markdown links and anchors,
fenced blocks, machine-local paths, manifests, and the skills.sh grouping. Skill links
must stay within their distributable folder. In a Git checkout, Markdown checks include
tracked and new nonignored files; untracked ignored local artifacts are excluded. An exported
repository checks root Markdown and skill folders; an isolated skill checks its own tree.
The tests also copy each skill into an isolated installation and check its links.

`--check-cli` runs `skills@1.5.26` with telemetry disabled and requires the exact expected
skill names and count, rather than trusting its exit code. That pinned CLI has no JSON
mode for `--list`; an unrecognized output format fails validation. Update the discovery
check when upgrading the CLI. Omit the flag to run only static checks without Node.js.

## Releases

The repository uses [Conventional Commits](https://www.conventionalcommits.org/) and Release Please. After each push to `main`, the workflow creates or updates a release PR from releasable commits. It updates `CHANGELOG.md`, plugin manifests, and README version markers together. Merging the release PR creates the corresponding `vX.Y.Z` tag and GitHub Release.

To rerun the same release pipeline manually, open Actions > Release Please > Run workflow and select `main`, or use GitHub CLI:

```bash
gh workflow run release-please.yml --repo kovaa-dev/skills --ref main
```

The manual entry point becomes available after this workflow is on `main`. Runs from other branches skip the release job. It uses the same release policy and accumulated commits as the automatic run, creating or updating a release PR when needed. If there are no unreleased changes, no new version is created. Merging a release PR still publishes the release through the normal workflow.

Skill instructions are the product in this repository, so ordinary `docs:` changes are releasable by default. Use a Conventional Commit title for the squash merge:

- `docs:`, `fix:`, `perf:`, and `revert:` create a patch release.
- `feat:` (or `feature:`) creates a minor release.
- `!` or a `BREAKING CHANGE:` footer creates a major release, including before 1.0.
- `chore:`, `ci:`, `test:`, `build:`, `style:`, and `refactor:` alone do not create a release unless marked as breaking.

The largest applicable bump wins when several commits accumulate. Documentation changes appear under Documentation in the changelog; they do not require a manual version bump or a `Release-As` override. A release is published after the generated release PR passes validation and is merged.

The `v0.2.0` release is the automation baseline. Subsequent versions are calculated from Conventional Commit types and breaking-change markers; do not edit managed version fields independently.

## Pull requests

A pull request should include:

- the problem being solved;
- the intended behavior;
- affected skills and references;
- validation performed;
- migration notes when existing installations may retain older rules.

Do not include secrets, private repository content, personal data, or proprietary project requirements in examples or tests.
