# Deployment

This guide describes the intended topology for deploying your own fork. Provider dashboards and free-tier limits change; verify current settings before applying changes.

The infrastructure constraint is ₹0/month and free-tier-only. Do not select paid plans or create resources with recurring charges.

## Topology
- Frontend: Vercel, project root frontend.
- Backend: Render, configured by render.yaml, root directory backend, Docker.
- Auth/database: Supabase, apply supabase/migrations/.
- Shared rate limiting: Upstash Redis, required for production startup.
- Email: SMTP provider, optional.

## Before deploying
- Confirm tests and GitHub Actions pass on the commit.
- Review pending Supabase migrations.
- Confirm required environment variables are set in provider secret settings.
- Confirm CORS origins and Supabase Auth URLs match the frontend domain.
- Deploy reviewed commits from main, not unreviewed branches.
- Never commit or share secrets.

## Supabase
1. Create/select a Supabase project. Use a separate project for a fork.
2. Record project URL and publishable key.
3. Apply all SQL migrations in ascending filename order. For an existing database, check which migrations already ran before manually applying SQL.
4. Keep RLS enabled on public.travel_memories.
5. Enable intended signup methods in Auth settings.
6. Set Site URL to the frontend origin, e.g. https://your-domain.example.
7. Add the frontend callback pattern, e.g. https://your-domain.example/**, to allowed redirect URLs.
8. Use only the publishable key in browser variables. Never put a secret/service-role key in NEXT_PUBLIC_.

## Render backend
render.yaml defines a Docker web service named NomadAI-backend, plan free, root directory backend, health check /healthz.

Configure these values in Render:
- GEMINI_API_KEY: secret from Google AI Studio.
- GEMINI_MODEL: optional, currently gemini-3.8-flash.
- SUPABASE_URL: project URL.
- SUPABASE_PUBLISHABLE_KEY: publishable key.
- SMOKE_TEST_TOKEN: high-entropy secret used only by the manual production smoke test.
- CORS_ORIGINS: exact frontend origin, e.g. https://your-domain.example.
- RATE_LIMIT_STORAGE_URI: Upstash Redis TLS connection URI, required in production.
- REDIS_URL: alternative if RATE_LIMIT_STORAGE_URI is not set.

render.yaml marks deployment-specific values sync: false. Supply them in the dashboard. Optional email variables: SMTP_HOST, SMTP_PORT (defaults 587), SMTP_USER, SMTP_PASS, FROM_EMAIL.

Do not assume email delivery works until tested. /healthz checks only process responsiveness, not Gemini, Supabase, Redis, or SMTP. /readyz checks that the required Gemini, Supabase, and Redis configuration is present, but does not prove each upstream service is reachable.

## Vercel frontend
1. Import the repository.
2. Set project root to frontend.
3. Use Next.js framework settings.
4. Set:
   - NEXT_PUBLIC_API_BASE: public Render backend URL.
   - NEXT_PUBLIC_SUPABASE_URL: Supabase project URL.
   - NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: Supabase publishable key.
5. Set values for the intended Production, Preview, and Development environments.
6. Deploy a reviewed main commit.

NEXT_PUBLIC_ values are included in the browser bundle and must not contain private credentials.

## Upstash Redis
Redis is optional locally and recommended for shared hosted rate limits. Create a free-tier database only after checking current limits, copy its TLS connection URI, and set RATE_LIMIT_STORAGE_URI in Render. Verify connectivity and actual limiter behavior. Do not paste the URI into source or chat.

Production startup fails when Redis is absent unless ALLOW_IN_MEMORY_RATE_LIMIT=true is explicitly set. Do not enable that override in production. Outside production, the limiter uses process-local memory. Verify that RATE_LIMIT_STORAGE_URI is set in Render and that the free Upstash database is reachable.

## Automated production smoke test

The backend exposes a hidden synthetic test route at /internal/smoke/gemini. It is disabled unless SMOKE_TEST_TOKEN is configured. Set a high-entropy value as SMOKE_TEST_TOKEN in Render and set the same value as PRODUCTION_SMOKE_TOKEN in GitHub Actions secrets. Set PRODUCTION_API_BASE as a GitHub Actions repository variable, or supply the backend URL when manually dispatching the Production smoke test workflow.

The workflow is manual only. It checks /healthz, /readyz, and /api/ai-status, then performs one small Gemini generation request and one streaming request. This consumes Gemini API quota, so run it deliberately and confirm the requests remain within the free quota. Never put the smoke token in source control or workflow inputs.

## Post-deployment verification
1. Homepage loads on production domain.
2. /auth loads and signup/sign-in UI is present.
3. Signup confirmation redirects to the intended domain.
4. Sign-in and sign-out work.
5. Backend /healthz responds and /readyz reports required configuration.
6. Run the manual Production smoke test workflow to verify Gemini generation and streaming.
7. Authenticated memory create/list/update/delete work.
8. Two test accounts cannot access each other's memories.
9. Redis-backed limits behave as expected across restarts and instances.
10. Test email delivery separately if digest is enabled.

A successful deployment or /healthz response does not prove every product feature works. Issue #17 tracks automated production smoke tests.

## Rollback
For application changes, redeploy the last known-good commit from provider deployment history. For database changes, prefer a reviewed forward-fix migration unless a safe rollback was explicitly prepared. Never delete or rewrite applied migrations to roll back.

## Free-tier caveats
Free services can sleep, impose daily/monthly quotas, limit compute, or change eligibility. A sleeping backend may have cold-start delay. A provider may block deployments after quotas are exhausted. Do not upgrade to paid plans without owner approval.
