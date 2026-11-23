# Security and data handling

## Reporting vulnerabilities

Do not open public issues for suspected vulnerabilities. Report them privately through GitHub's security advisory workflow when it is enabled, or contact the repository maintainer privately.

## Automated security checks

Pull requests and the default branch are checked with:

- CodeQL security-extended analysis for Python and JavaScript/TypeScript.
- Dependency review, which rejects newly introduced vulnerabilities rated high or critical.
- Gitleaks, which scans repository history for committed secrets.
- `pip-audit` for known Python package vulnerabilities.
- `npm audit --audit-level=high` for frontend dependency vulnerabilities.

Dependabot checks Python, npm, and GitHub Actions dependencies weekly. Security workflow runs are also scheduled weekly.

### Triage policy

1. Treat confirmed critical vulnerabilities and exposed credentials as immediate incidents. Revoke or rotate exposed credentials before removing them from history.
2. Block release of known high-severity vulnerabilities unless the maintainer documents a time-bounded exception and mitigation.
3. Review medium and low findings during routine dependency maintenance.
4. Record the affected package, advisory, impact, mitigation, and verification result in the relevant issue or pull request.
5. Never paste secrets into issues, logs, commits, or chat.

GitHub repository settings should also have secret scanning and push protection enabled when available. The workflow scan is a defense-in-depth check and does not replace those account-level protections.

## Persistent travel memory

Persistent memory is intentionally disabled until authenticated ownership is implemented. Do not mount the legacy memory router or restore memory writes until an authentication provider verifies access tokens server-side and every database operation is scoped to the verified subject.

A client-supplied UUID, email address, or other opaque identifier is not proof of identity. When memory is reintroduced, add ownership metadata and migrations, enforce subject-scoped reads and writes, test cross-account read/update/delete denial, and document retention and account deletion.

Tracking: GitHub issue #13. The issue remains open until an authentication provider and tenant-scoped persistence are implemented and verified.
