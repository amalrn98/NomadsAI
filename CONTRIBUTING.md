# Contributing to NomadsAI

Thank you for considering a contribution.

## Before you start
1. Read README.md.
2. Follow docs/LOCAL_DEVELOPMENT.md.
3. Read docs/ARCHITECTURE.md for changes crossing frontend, backend, auth, database, or deployment boundaries.
4. Check existing GitHub issues and pull requests for duplicate work.
5. Read SECURITY.md before touching auth, secrets, user data, or public endpoints.

For a large change, open an issue first to agree on scope and acceptance criteria.

## Branch workflow
Start from an up-to-date main branch and create a descriptive branch. Suggested prefixes: feat/, fix/, docs/, test/, refactor/, chore/. Make focused commits. Never commit .env files, credentials, local databases, build output, or generated caches. Push the branch and open a pull request against main. Do not push directly to main.

## Local checks
Backend, from backend/: python -m pytest -q
Frontend, from frontend/: npm ci, npm run lint, npm run build

Run checks relevant to the change. If a check cannot run, explain why in the PR. Add regression tests for bug fixes and tests for new behavior where practical.

## Pull request expectations
Include:
- Problem and expected behavior.
- Solution and affected components/routes/tables/workflows.
- Exact validation commands and results.
- Security and data impact, including auth, RLS, personal data, secrets, external services, and rate limits.
- Deployment impact, including environment variables, migrations, provider settings, and rollout steps.
- Known limitations and unverified behavior.

Keep PRs reviewable. Update docs when setup, configuration, behavior, API contracts, or operations change.

## Engineering conventions
- Follow existing conventions in the affected module.
- Prefer explicit types and validation at API boundaries.
- Keep secrets server-side.
- Derive identity from validated Supabase sessions, never client-supplied user IDs.
- Preserve RLS and least-privilege database access.
- Label sample and unverified travel data.
- Avoid new dependencies when existing dependencies or the standard library suffice.
- Do not add paid infrastructure or metered services. The operating budget is ₹0/month, free-tier-only.
- Avoid unrelated refactoring.

## Database migrations
Add a new timestamped SQL migration under supabase/migrations/. Never rewrite a migration that may have been applied. Include constraints, indexes, grants, and RLS policies as appropriate. Explain migration order and rollback considerations. Never disable RLS as a workaround. Do not apply a production migration as part of a code-only PR without explicit authorization.

## Security and review
Do not publish vulnerability details or credentials in public issues. Follow SECURITY.md for private reporting. A PR is ready when scope is clear, relevant tests pass, CI is green, docs are current, and deployment/migration steps are explicit. Do not merge with unresolved security or data-isolation concerns.
