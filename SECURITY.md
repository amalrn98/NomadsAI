# Security and data handling

## Reporting vulnerabilities

Do not open public issues for suspected vulnerabilities. Report them privately through GitHub's security advisory workflow when it is enabled, or contact the repository maintainer privately.

## Automated security checks

Pull requests and the default branch are checked with CodeQL security-extended analysis for Python and JavaScript/TypeScript, Gitleaks repository-history scanning, pip-audit for Python dependencies, and npm audit for frontend dependencies. Dependabot checks Python, npm, and GitHub Actions dependencies weekly.

GitHub's dependency graph, secret scanning, and push protection should also be enabled in repository settings when available. Workflow scans do not replace repository-level protections. Dependency review is not active until the dependency graph and a dependency-review workflow are enabled.

## Data provenance

The local JSON event, flight, and hotel records are demonstration fixtures. API responses mark them as `sample`, `is_live: false`, and `verified: false`. They must not be presented as current prices, schedules, inventory, or availability.

Online news results include their source URL and retrieval timestamp, but remain unverified search results. Users must open the source before relying on time-sensitive details. The email digest excludes local sample fixtures.

## Authentication and travel memory

Supabase Auth is the identity provider. The backend validates every bearer token with Supabase Auth's `/auth/v1/user` endpoint before processing memory requests. It forwards the same user access token, not a service-role key, to Supabase Data API. The database enforces ownership with row-level security policies on every read, insert, update, and delete.

The `user_id` stored on a memory is assigned from the verified Auth user, never from request input. API queries also filter by that verified subject. Deleting an Auth user cascades to their memories.

The frontend uses the Supabase publishable key only. Never expose a Supabase secret or service-role key in frontend variables or source code. Persistent memory is account-scoped; chat does not yet retrieve or write long-term memories.

Tracking: GitHub issues #13 and #16. Issue #13 remains open until cross-account behavior is tested against the live project and account deletion/retention controls are documented.

## Vulnerability triage

1. Treat confirmed critical vulnerabilities and exposed credentials as immediate incidents. Revoke or rotate exposed credentials before removing them from history.
2. Block merges that introduce known high-severity vulnerabilities unless the maintainer records a time-bounded exception and mitigation.
3. Review medium and low findings during routine dependency maintenance.
4. Record the affected package, advisory, impact, mitigation, and verification result in the relevant issue or pull request.
5. Never paste secrets into issues, logs, commits, or chat.

The dependency-review workflow checks pull requests for newly introduced high-severity vulnerabilities when the repository Dependency graph is enabled and the DEPENDENCY_GRAPH_ENABLED repository variable is set to true. Python and npm audit jobs run independently of that setting. Dependabot is configured to open weekly grouped update PRs for Python, npm, and GitHub Actions dependencies. CodeQL, Gitleaks, pip-audit, and npm audit run through the existing CI/security workflows. Repository-level Dependency graph, secret scanning, push protection, and required checks must still be verified in GitHub settings. The Dependency Review action currently skips until the graph is enabled; its first run confirmed the graph is disabled.
