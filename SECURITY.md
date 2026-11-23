# Security and data handling

## Reporting vulnerabilities

Do not open public issues for suspected vulnerabilities. Report them privately through GitHub's security advisory workflow when it is enabled, or contact the repository maintainer privately.

## Automated security checks

Pull requests and the default branch are checked with CodeQL security-extended analysis, Gitleaks repository-history scanning, pip-audit for Python dependencies, and npm audit for frontend dependencies. Dependabot checks Python, npm, and GitHub Actions dependencies weekly.

GitHub's dependency graph, secret scanning, and push protection should also be enabled in repository settings when available. Workflow scans do not replace repository-level protections. Dependency review is not active until the dependency graph is enabled.

## Data provenance

Local event, flight, and hotel records are demonstration fixtures, not current prices, schedules, inventory, or availability. Online news results include source URLs and retrieval timestamps but remain unverified search results. The email digest excludes local sample fixtures.

## Authentication and travel memory

Supabase Auth is the identity provider. The backend validates every bearer token with Supabase Auth's `/auth/v1/user` endpoint before processing memory requests. It forwards the same user access token, not a service-role key, to Supabase Data API. The database enforces ownership with row-level security policies on every read, insert, update, and delete.

The `user_id` stored on a memory is assigned from the verified Auth user, never from request input. API queries also filter by that verified subject. Deleting an Auth user cascades to their memories.

The frontend uses the Supabase publishable key only. Never expose a Supabase secret or service-role key in frontend variables or source code. Persistent memory is account-scoped; chat does not yet retrieve or write long-term memories.

Tracking: GitHub issues #13 and #16. Issue #13 remains open until cross-account behavior is tested against the live project and account deletion/retention controls are documented.
