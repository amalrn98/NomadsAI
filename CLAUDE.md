# NomadsAI: persistent engineering context

Read this file before making changes. It is the durable handoff for Claude Code and other coding agents, so work should not depend on previous chat history.

## Start here
1. README.md: product overview and quick start.
2. docs/ARCHITECTURE.md: component boundaries, request flow, data ownership.
3. docs/LOCAL_DEVELOPMENT.md: setup from a clean clone.
4. docs/DEPLOYMENT.md: hosted configuration and release checks.
5. CONTRIBUTING.md: branch, test, and pull-request workflow.
6. SECURITY.md: security boundaries and reporting.

Treat documentation as a guide, not proof that implementation still matches it. Inspect relevant source, tests, GitHub issues, recent commits, and deployed configuration before changing behavior.

## Mission
Maintain NomadsAI, an AI-assisted travel planning application. Prefer small, reviewable, tested changes. Preserve security boundaries and keep the project independently runnable.

## Repository map
- frontend/: Next.js App Router, React, TypeScript, Supabase browser client.
- backend/app/main.py: FastAPI app factory, middleware, router registration, health/status endpoints.
- backend/app/routers/: HTTP API route handlers.
- backend/app/services/: Gemini provider/client, web search, email, supporting services.
- backend/app/pipeline/: itinerary pipeline and local destination knowledge.
- backend/app/auth.py: Supabase bearer-token validation.
- backend/app/routers/memory.py: authenticated travel-memory API.
- backend/app/rate_limit.py: SlowAPI limiter and storage selection.
- backend/tests/: backend regression and security tests.
- supabase/migrations/: ordered SQL migrations.
- .github/workflows/: CI and security scans.
- render.yaml: Render backend descriptor.

## Current architecture
- Frontend: Next.js hosted on Vercel, project root frontend.
- Backend: FastAPI on Python 3.11, Dockerfile in backend/, hosted on Render.
- Identity and database: Supabase Auth and PostgreSQL. public.travel_memories uses RLS scoped to auth.uid().
- AI: Google Gemini, called server-side. The API key must never reach the browser.
- Rate limiting: SlowAPI uses Redis when RATE_LIMIT_STORAGE_URI or REDIS_URL is configured. Current code falls back to memory:// when neither exists. This is process-local and unsuitable for horizontally scaled production. Issue #16 tracks fail-closed behavior.
- Local destination knowledge and fixtures are not authoritative live travel inventory.
- Render free instances may sleep and local filesystem state is ephemeral. Never store durable user data on Render filesystem.

## Hard constraints
The infrastructure budget is ₹0/month, free-tier-only. Do not add paid services, paid plans, metered dependencies, or infrastructure that silently incurs recurring charges. If a feature cannot fit this constraint, document the limitation and propose a no-cost alternative. Do not upgrade plans or create paid resources.

## Non-negotiable engineering rules
1. Never commit secrets. Do not request credentials in chat, issues, PRs, logs, or source. Use provider secret managers. Never expose Gemini, SMTP, Redis, or Supabase secret/service-role credentials in NEXT_PUBLIC_ variables.
2. Preserve user isolation. Never trust a user ID supplied by the browser. Validate the Supabase access token and derive the user ID from the validated identity. Keep RLS enabled. Never use a service-role key as a shortcut.
3. Keep durable user data in Supabase. SQLite, local JSON fixtures, process memory, and Render filesystem are not durable user storage.
4. Label data honestly. Static fixtures are samples, not live prices, schedules, inventory, or availability. Search snippets are unverified until checked at source.
5. Avoid unsupported production claims. A health response is not an end-to-end readiness check. Do not call a feature production-ready unless relevant behavior is tested in its deployed context.
6. Use PRs. Work on a descriptive branch, never push directly to main. Open a PR with rationale, scope, tests, risks, and dashboard steps.
7. Do not close issues just to reduce backlog. Close only when acceptance criteria are met and evidence exists.
8. Keep changes focused. Check imports, runtime references, workflows, docs, and tests before deleting files.
9. Test the changed subsystem. Run narrow tests, then full backend and frontend checks when practical. Report skipped checks.
10. Do not change production infrastructure, secrets, DNS, provider plans, or apply production migrations without an approved plan.

## Protocol for every task
1. Inspect git status, current branch, and latest main. Never overwrite uncommitted work.
2. Read relevant source, tests, docs, issue/PR, and recent history.
3. Define acceptance criteria before editing.
4. Make the smallest complete change on a feature/fix/docs branch.
5. Add or update tests and docs alongside behavior changes.
6. Run tests; inspect final diff for secrets, generated files, stale docs, and unrelated changes.
7. Push branch and open PR against main. Do not merge unless explicitly authorized and all required checks pass.
8. PR description must state changes, tests, untested areas, deployment/migration requirements, and unresolved risks.
9. Handoff must include PR, checks, deployment status, manual actions, and remaining work.
10. Update this file when a lasting architecture or workflow decision changes.

## Quality gates
Backend: from backend/, run python -m pytest -q.
Frontend: from frontend/, run npm ci, npm run lint, npm run build.
CI includes backend tests, Python and npm audits, frontend build, CodeQL, and Gitleaks. Check actual GitHub Actions results. Never assume a check passed because it exists in YAML.

## Known open engineering work
This list was current as of 2026-11-23. Re-check GitHub before acting.
- #13: live cross-account verification and account deletion/retention documentation remain after Auth/RLS implementation.
- #16: Redis shared limits are supported, but missing Redis currently falls back to process-local memory. Production fail-closed behavior and tests remain.
- #17: safe production smoke tests for Gemini and chat streaming remain. /healthz alone is insufficient.
- #18: initial travel-source provenance and fixture labeling work was merged. Re-check issue status.
- #19: CodeQL, Gitleaks, pip-audit, and npm audit workflows exist. Verify repository-level secret scanning and push protection separately.
- #20: email digest abuse controls require review, including opt-in, quotas, idempotency, and bot/abuse protection.
This is not necessarily the complete or current backlog. Query GitHub issues and PRs at the start of a task.

## Product and operational constraints
- Minimize manual work, but identify dashboard-only actions clearly and give exact steps.
- Never claim a deployment is live until the deployed URL and relevant route are checked.
- Free services can sleep, hit quotas, or change limits.
- Keep frontend responsive and accessible, with loading, error, and empty states.

## Required final handoff
- Result: what changed and why.
- PR: URL and branch.
- Validation: exact commands/checks and pass/fail/skip status.
- Deployment: whether required and whether verified.
- Manual action: exact user action, or None.
- Remaining work: unresolved issue numbers and risks.

Do not make the owner reconstruct context from chat.
