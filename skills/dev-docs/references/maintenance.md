# Maintenance and continuing development

Use [requirements](requirements.md), [work queues](work-queue.md), and
[governance](documentation.md). Assess existing material through [source assessment](source-transition.md)
and reconcile only scope that needs canonical ownership.

## Intake and registration

Apply this flow to defects found by users, tests, audits, implementation, or operations,
not just code/requirement mismatches. A material defect must be fixed and verified in
current work or captured in an existing/new remediation task visible in the shared queue.
A report, test log, or chat message alone is not follow-up. Check for an existing defect
and task before adding another; a local fix inside current scope needs no extra task.
Read-only requests produce findings and proposed follow-up only, unless registration
is authorized. A bug report is not authority for unrelated code/product changes.

The defect owner preserves symptom, environment/reproduction, expected versus observed
behavior, its basis or uncertainty, impact and verification criteria. Link an existing
requirement when applicable. Keep observations, hypotheses, and established causes
separate. A short section in the topic document can suffice; no mandatory incident file
or new requirement is needed. The task links that defect/contract and owns execution
status; reports link tasks without a competing status register.

Choose remediation from evidence and acceptance:

- An implementation violates a current accepted contract: repair code against the same
  requirement. A recurring bug does not create another obligation or reopen historical work.
- Documentation misstates an already accepted decision: correct its owner with that basis.
- Desired behavior changes: obtain/use actual acceptance, revise the same requirement
  where its identity is unchanged, and target that revision from a task.
- Expected behavior is unknown: preserve the question and a clarification/investigation
  task as needed. Missing requirements do not prevent registering a defect; current code
  does not decide the contract. Recovered expectations retain source and definition state.

A substantial independently useful investigation can finish separately; it must leave
significant unresolved fixes explicitly linked to tasks. Completing research does not
complete remediation. Prioritize real dependencies, not a forced linear chain of every
finding. Unreproduced defects stay uncertain rather than being declared absent.

## Severity and order

Severity describes consequences; priority chooses execution order. Preserve ratings,
rationale, and an explicit scheduling/deferral decision at the defect/decision owner with task priority linked,
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

Close remediation only after verifying the original failure and affected preserved
behavior against the applicable contract under the actual project-work testing policy.
If documentation changed, verify its accepted basis and agreement with implementation;
an edit alone does not prove the defect resolved. Record the method/result and gaps without calling manual checking an
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
