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

Run the same local checks used by CI:

```bash
python3 scripts/validate.py
DISABLE_TELEMETRY=1 npx --yes skills@1.5.26 add . --list
```

The validator checks frontmatter, names, descriptions, local Markdown links and anchors, fenced blocks, machine-local paths, manifests, and the skills.sh grouping.

## Releases

The repository uses [Conventional Commits](https://www.conventionalcommits.org/) and Release Please. After each push to `main`, the workflow creates or updates a release PR from releasable commits. It updates `CHANGELOG.md`, plugin manifests, and README version markers together. Merging the release PR creates the corresponding `vX.Y.Z` tag and GitHub Release.

The `v0.2.0` release is the automation baseline. Subsequent versions are calculated from Conventional Commit types and breaking-change markers; do not edit managed version fields independently.

## Pull requests

A pull request should include:

- the problem being solved;
- the intended behavior;
- affected skills and references;
- validation performed;
- migration notes when existing installations may retain older rules.

Do not include secrets, private repository content, personal data, or proprietary project requirements in examples or tests.
