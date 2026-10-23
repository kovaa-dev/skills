# Maintenance and continuing development

Use [requirements](requirements.md), [work queues](work-queue.md), and
[governance](documentation.md). Existing legacy bug/task/PRD work first follows
[on-touch conversion](legacy-transition.md); do not create new legacy cards.

## Intake and registration

A regression against an unchanged obligation is repair work linked to the same
requirement. Changing desired behavior revises/adds a requirement under normal
acceptance. A technical implementation choice need not become a new product requirement.

Register explicitly requested/deferred work, unresolved or recurring defects, independently
actionable blockers, and significant enduring risks. A local defect fully fixed within
current work does not require another item. Report other observations without automatically
creating a backlog. Check for duplicates and preserve useful sources when merging.

A minimum queue entry identifies the observed/desired result, source, known impact,
next useful action/result, and state. Assign an accountable owner before execution.
Detailed reproduction, causal hypotheses, research support, acceptance, and verification
belong with the affected specification or result artifact. Link rather than copy them.
No PRD, complete design, estimate, stage, or separate issue document is required just
to preserve a finding.

Keep observation, hypothesis, and established cause distinct. "Not reproduced" does
not prove "no defect". A small diagnosis/fix can be one work item; a separately completed
investigation links every significant unresolved fix as remaining work. Completing
research does not complete remediation or implement the product requirement.

Unclear behavior/questions stay beside their contract. ready work has adequate scope,
authority, inputs, acceptance, and target. need-info names the needed decision;
blocked names the missing external result. Do not demand repeated grooming or start
permission when the user's instruction already authorizes the accepted result.

## Severity and order

Severity describes consequences; priority chooses execution order. Preserve ratings,
rationale, and an explicit scheduling/deferral decision in the canonical work context,
not duplicate registries. Do not infer low severity from missing information or lower
it silently to fit a release. Priority never authorizes violating an accepted requirement.

Default triage when the project has no accepted alternative:

| Severity | Consequences | Planning |
| --- | --- | --- |
| critical | Active security threat, data loss/corruption, or widespread key-flow failure without a workaround | Raise immediately; propose containment and remediation ahead of ordinary development; block the affected release |
| high | Primary flow substantially broken without an acceptable workaround | Nearest fix queue ahead of ordinary improvements; affected release needs a fix or explicit risk decision |
| medium | Limited defect with an acceptable workaround | Regular priority/dependencies, or justified deferral with a review trigger |
| low | Cosmetic/minor inconvenience preserving the primary outcome | Plan or explicitly defer with a review condition |

These are not SLAs or production authority. Follow accepted emergency scope; reporting
a critical issue does not authorize arbitrary data/production changes. A material exception
needs its rationale and responsible acceptance. Continue independent authorized work
after registering a significant non-blocking follow-up.

## Close and release honestly

Verify the original failure and the applicable contract under the actual project-work
testing policy. Record the method/result and gaps without calling manual checking an
automated test. Done is terminal historical work; a later regression receives new
linked work while keeping the same unchanged requirement.

A duplicate, rejected idea, or confirmed absence of a defect can be cancelled with a
reason and canonical replacement where applicable. Preserve prior reasons if cancelled
work later resumes. Unresolved reproduction remains open with the next check conditions.

A release record identifies actual version/target/date, artifact, relevant requirements/
work, and runtime verification when required. A delivery grouping, commit, tag, or green
build alone does not prove production behavior. Research and documentation can have
different agreed targets. A user-facing changelog describes visible changes without
copying specifications or future work state.
