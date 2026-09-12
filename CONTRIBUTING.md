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

1. Identify the canonical file that owns the rule or template.
2. Check related references for contradictions before editing.
3. Make the smallest coherent change.
4. Update affected templates and navigation.
5. Verify frontmatter, relative links, Markdown fences, and whitespace.
6. Describe behavioral or compatibility effects in the pull request.

Changes that alter the meaning of both `dev-docs` and `dev-rules` should be reviewed as one coherent update.

## Pull requests

A pull request should include:

- the problem being solved;
- the intended behavior;
- affected skills and references;
- validation performed;
- migration notes when existing installations may retain older rules.

Do not include secrets, private repository content, personal data, or proprietary project requirements in examples or tests.
