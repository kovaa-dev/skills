# Engineering findings

Rules — [maintenance](maintenance.md), [tracker](task-tracker.md),
[documentation policy](documentation.md).
Use this form only when the project has selected a separate findings register. Without one,
record a finding that crosses the registration threshold in an existing or required technical
task; do not create a second status, owner, or remediation plan.

```md
# Engineering findings

## FIND-001 <Short confirmed finding>

- Status: OPEN
- Severity: <project severity level>
- Owner: <one accountable owner>
- Found at: <date/version/environment>
- Research support: <path/lines/reproduction/measurement or source locator>
- Impact: <observed impact>
- Remediation: [AUTH-001 Validate sign-in requests](../tasks/auth/AUTH-001.md)
- Expected closure: <verifiable result>
- Closure verification: pending
```

Allowed finding statuses are `OPEN`, `PARTIAL`, and `CLOSED`. An OPEN or PARTIAL finding
requires a technical task. The finding status describes the observation, not progress of the
remediation task; product composition remains in the PRD. After remediation, update closure
verification without rewriting the original research support, and do not delete closed records.
