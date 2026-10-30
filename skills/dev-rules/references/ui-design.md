# UI design and visual verification

Use for work that creates, changes, or reviews interface appearance, layout, components,
interaction, or accessibility. Pure backend/configuration work with no UI effect does
not load design skills. This reference coordinates design expertise; it does not copy
an external skill's visual methodology or require one particular skill to be installed.

## Select a design skill

Use the current skill catalog or the project's established skill entrypoint. Discover
candidates once for the task and reuse the result unless availability or scope changes.
Do not enumerate unrelated skills or search the filesystem/network merely to assemble
a larger collection.

1. Prefer a skill explicitly selected by the user/project. Otherwise choose one
   available primary skill whose actual scope fits the product and work.
2. Read its real `SKILL.md` from the available location; a familiar name or description
   is not a substitute. Respect invocation restrictions and use only needed references
   and resources. Distinguish a missing skill from missing tools/resources in an installed one.
3. Apply its design discipline within the accepted contract. Add a second skill only
   for a distinct need the primary skill or existing checks do not already cover.
   Do not run several complete design processes for the same component.

These are recommended candidates, not hard dependencies or an exhaustive list:

| Skill and upstream source | Typical role |
| --- | --- |
| [`interface-design`](https://github.com/Dammyjay93/interface-design) | Primary for product interfaces: dashboards, settings, tools, and applications; composition, component reuse, tokens, and consistency. |
| [`frontend-design`](https://github.com/anthropics/skills/tree/main/skills/frontend-design) | Primary for expressive websites, landing pages, or a new visual direction; apply an existing project's accepted language when extending it. |
| [`ui-ux-pro-max`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | Targeted UX, platform, typography, color, and interaction guidance; consult relevant results without regenerating an existing system for each page. |
| [`web-design-guidelines`](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines) | Focused review of implemented web UI against interface guidelines. |

If the preferred optional skill is unavailable, use a compatible available alternative
when permitted, or proceed with the project sources and guidance below. Once per task,
briefly recommend the relevant missing skill and a verified upstream/project installation
source; verify current installation instructions before giving a command. Do not install,
download-and-execute, or copy an external skill merely because it is recommended.
If the user/project explicitly requires that exact skill, report the missing prerequisite
and continue only independent work. Never claim an unavailable skill was applied.

Skill composition is an instruction route, not an invented package dependency or an
automatic installer. Keep external skills separately maintained; use a project-approved
source/revision when one exists. Companion instructions do not grant new execution or
delivery authority, supersede accepted project design decisions, or require a parallel
design-document tree. Material incompatibilities remain explicit.

## Existing product or new direction

For an existing product, inspect its canonical design guidance, tokens/theme, reusable
components and variants, styling conventions, and relevant implemented screens before
choosing new styles. A new page in an established product still follows that system.
Treat missing documented guidance as a reason to inspect existing patterns, not as
permission to redesign. Distinguish observed conventions from accepted obligations.

Reuse an existing component first, then an existing variant or composition. Add a new
component only for a current unmet need, following the established ownership and styling
patterns. Reuse semantic tokens and interaction/accessibility behavior. Do not hand-roll
an available control, add a second theme, or introduce dependencies solely because an
external skill prefers them. Existing scope and dependency rules govern any such change.

For a new project or an authorized redesign, derive a coherent direction from the
actual audience, content, primary task, and stated brand constraints. Decide hierarchy,
typography, color roles, density, spacing, and interaction character together. Use
concrete content or realistic fixtures rather than a generic template as the design's
justification. A short direction note or specimen suffices; confirm only material
ambiguity or a consequential change outside the accepted brief.

Keep the smallest useful token/component foundation for the current deliverable.
Record durable agreed design decisions in the project's owning sources and implementation;
reuse those sources instead of introducing a skill-specific file tree by default.
Apply established decisions to small additions without repeating a whole brand
exploration, generating palettes, or requesting the same confirmation for each control.

## Visual verification

For UI implementation, the agent independently starts/renders the affected interface,
inspects it with available tools, and corrects in-scope defects before handoff. This is
authorized task verification; starting a local preview or taking screenshots does not
need another approval when already permitted by the task and environment. Tool use
and interactions with external systems remain within existing authority. A review-only
request permits inspection and findings, not unsolicited edits.

- Inspect the actual integrated surface and materially affected components/states.
  Use relevant viewport sizes, content lengths, and data states based on the change;
  a localized fix needs a focused pass, not every screen/viewport/state combination.
- Check composition and hierarchy, spacing and alignment, text flow and legibility,
  visual consistency, assets, and relevant loading/empty/error/focus/disabled states.
  Check interaction and accessibility behavior with appropriate existing tools; pixels
  alone do not establish keyboard or assistive-technology behavior.
- Fix concrete visual defects and material deviations from the chosen direction, then
  re-inspect changed areas. Reuse evidence that remains valid. Stop when the affected
  result meets its accepted direction and usable states; do not invent rounds of polish.

An inline specimen or isolated component preview can help choose a direction, but does
not prove that the integrated application renders correctly. Source inspection, passing
builds, and generated mockups are not observations of the implemented UI. Record the
actual view/state/viewport inspected and meaningful findings or limits in the existing
work/result context; no per-control report or screenshot archive is required.

Use existing preview and capture facilities; do not add a bespoke visual runner,
snapshot system, or evidence framework solely for this pass. Retain only useful evidence
and clean up task-created previews and temporary artifacts under existing resource rules.
Do not stop shared services or delete user data as cleanup.

If a usable rendering environment is unavailable, continue suitable source/static checks,
name what was not visually inspected, and provide focused user verification cases.
Do not claim visual verification or invent evidence. Required acceptance and any unresolved
verification blocker still follow the normal completion rules.

Agent visual inspection supplies engineering evidence, not user approval. The
[manual usability gate](../SKILL.md#4-user-owned-manual-usability-gate) defines when user
confirmation is required and remains pending until the user supplies it. Distinguish
agent inspection, executed automated tests, and user acceptance in the result.
