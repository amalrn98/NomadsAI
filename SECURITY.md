# Security and data handling

## Reporting vulnerabilities

Do not open public issues for suspected vulnerabilities. Report them privately through GitHub's security advisory workflow when it is enabled, or contact the repository maintainer privately.

## Automated security checks

Pull requests and the default branch are checked with:

- CodeQL security-extended analysis for Python and JavaScript/TypeScript.
- Gitleaks, which scans repository history for committed secrets.
- `pip-audit` for known Python package vulnerabilities.
- `npm audit --audit-level=high` for frontend dependency vulnerabilities.

Dependabot checks Python, npm, and GitHub Actions dependencies weekly. Security workflow runs are also scheduled weekly.

GitHub's dependency graph, secret scanning, and push protection should also be enabled in repository settings when available. The workflow scans are defense-in-depth checks and do not replace those repository-level protections. Dependency review is not active until the dependency graph is enabled.

### Triage policy

1. Treat confirmed critical vulnerabilities and exposed credentials as immediate incidents. Revoke or rotate exposed credentials before removing them from history.
2. Block release of known high-severity vulnerabilities unless the maintainer documents a time-bounded exception and mitigation.
3. Review medium and low findings during routine dependency maintenance.
4. Record the affected package, advisory, impact, mitigation, and verification result in the relevant issue or pull request.
5. Never paste secrets into issues, logs, commits, or chat.

## Data provenance

The local JSON event, flight, and hotel records are demonstration fixtures. API responses mark them as `sample`, `is_live: false`, and `verified: false`. They must not be presented as current prices, schedules, inventory, or availability.

Online news results include their source URL and retrieval timestamp, but remain unverified search results. Users must open the source before relying on time-sensitive details. The email digest excludes local sample fixtures.

## Persistent travel memory

Persistent memory remains disabled until authenticated ownership is implemented. Do not mount the legacy memory router or restore memory writes until an authentication provider verifies access tokens server-side and every database operation is scoped to the verified subject.

A client-supplied UUID, email address, or other opaque identifier is not proof of identity. When memory is reintroduced, add ownership metadata and migrations, enforce subject-scoped reads and writes, test cross-account read/update/delete denial, and document retention and account deletion.

Tracking: GitHub issues #13 and #18. These issues remain open until their full acceptance criteria are implemented and verified.
