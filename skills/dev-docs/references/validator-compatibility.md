# Optional validator compatibility profile

This is a reference for a legacy constrained parser, not a mandatory format for every
project and not a bundle of executable tools. Scripts are not shipped with the skill.
Apply it only if the project already has them or has explicitly chosen to adopt them.
Do not assume where their source files are located. If they are unavailable, do not suggest
a nonexistent command; use the project's checks or a minimal manual check.

## Tracker profile

The existing optional `check-tracker.mjs` is a constrained Markdown parser,
not a universal governance engine. The compatible profile uses:

- the `docs/tasks`, `docs/solutions`, and `docs/architecture/decisions` directories;
- exactly three-digit numbers and prefixes made of uppercase ASCII letters/digits;
- `- Status:`, `- Grooming:`, `- Dependencies:`, `- Product dependencies:`, and
  `- Decision dependencies:`; dependencies are inline Markdown links or `none`;
- the PRD section `## Technical tasks` for composition links;
- `## Open questions` for backlog items without a decision, `## Needs information` for
  `need-info`, `## Closure` for PRDs and technical tasks, and `## Evidence` for bug/
  investigation result records; `blocked` requires both `- Blocker:` and
  `- Unblock condition:`;
- `index.md` / `backlog.md` as navigation filenames; the entry point is `docs/tasks/index.md`.

For the fully English `dev-docs` profile, use the English schema tokens listed above. Update
`check-tracker.mjs`, its tests, every parser fixture, and all copied task/decision templates and
cards atomically; replace the legacy dependency sentinel with `none`. Until those changes are
complete, a parser configured for legacy tokens is not compatible with the English profile.
Example prose and non-schema headings may vary. Other paths and number lengths require adapting
the check; the normative rules remain unchanged. The check
does not prove that evidence is genuine, requirements are complete, the owner is correct, or an
accepted decision exists.


## Checks and portability limits

The Markdown bundle is portable without runtime tooling. The example paths represent the selected profile,
not a universal structure for every repository. When paths change, update the
links in snippets/cards and the configuration of the selected checks.

The existing `check-docs.mjs` is **not fully generic**: it hardcodes
`ignoredDirectories` and `retiredReferences`, including obsolete architecture paths
from the source repository. Before enabling it, review these lists for the new project,
history handling, Markdown fences/anchors, and the root location. Do not declare
another repository's retired paths forbidden in a new project by default.

`check-tracker.mjs` fixes the directories, ID regex, fields, headings, and navigation format;
it also includes special handling for DOC. It does not validate the full meaning of the governance rules.
Preserve the compatible profile or adapt the parser and tests. Node.js checks
require a compatible Node runtime; configure package scripts/CI separately.
After copying and adapting the checks, run them from the target repository root:

```sh
node scripts/check-docs.mjs
node scripts/check-tracker.mjs
node --test scripts/tests/check-docs.test.mjs scripts/tests/check-tracker.test.mjs
```

Run only checks that have been copied. Before claiming portability, test
a small fixture for the new project containing its prefixes, a PRD, a technical task,
a technical decision (TD)/architecture decision record (ADR), and links. A successful lint does not confirm that acceptance was actually met,
the migration is complete, or product constraints have been accepted; those require review.

Older parser versions may require a root-level TODO file. When adopting such
a tool, remove that requirement and test a fixture without a redirect
instead of creating an unnecessary file solely for compatibility.
