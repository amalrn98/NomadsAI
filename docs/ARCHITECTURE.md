# Architecture

This guide describes the current high-level structure and security boundaries. Confirm details in source and tests before relying on them for implementation changes.

## System context
Browser -> Vercel frontend (Next.js) -> Render backend (FastAPI) -> Google Gemini.
The browser also authenticates with Supabase Auth. Protected backend memory requests validate the user's Supabase bearer token and access Supabase PostgreSQL under RLS. FastAPI can use Upstash Redis for shared rate-limit storage and an SMTP provider for optional email.

## Frontend
frontend/ is a Next.js App Router application. Routes are in frontend/app/, shared UI in frontend/components/, and the browser Supabase client in frontend/lib/.

The browser reads NEXT_PUBLIC_API_BASE, NEXT_PUBLIC_SUPABASE_URL, and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY. Supabase client uses PKCE, persists sessions, refreshes tokens, and detects auth callbacks. NEXT_PUBLIC_ values are public by design.

## Backend
backend/app/main.py constructs FastAPI, configures CORS and rate limiting, and mounts routers:
- /api/signals
- /api/digest
- /api/chat
- /api/plan
- /api/memory

Interactive OpenAPI docs are at /docs.

## AI
Gemini calls are server-side through backend services. GEMINI_API_KEY must never reach the browser or source control. GEMINI_MODEL selects the model, with code default gemini-3.8-flash. /api/ai-status reports configuration, not successful live generation. The itinerary generator attaches timestamped web search references when available, but all generated itinerary content remains unverified. The results page labels this limitation and links the search references.

## Identity and user data
Supabase Auth is the identity provider. Protected memory requests carry a bearer access token. backend/app/auth.py validates it through Supabase Auth /auth/v1/user and derives the user ID from the returned identity.

backend/app/routers/memory.py forwards the user's access token to Supabase Data API. public.travel_memories references auth.users(id) with ON DELETE CASCADE and uses RLS policies scoped to auth.uid().

Invariants:
1. Never trust user_id supplied in request input as identity.
2. Derive ownership from validated Supabase identity.
3. Keep RLS enabled and preserve per-user policies.
4. Never use a service-role key in the browser.
5. Never broaden grants or policies to bypass an authorization failure.

The SQL migrations are authoritative. Cross-account behavior still requires live verification tracked by issue #13.

## Readiness and smoke tests

/healthz is a liveness check. /readyz checks that Gemini, Supabase, and Redis configuration is present; it does not perform live upstream requests. The hidden /internal/smoke/gemini route requires SMOKE_TEST_TOKEN and performs one synthetic generation plus one streaming request. It is intended for the manual GitHub Actions Production smoke test workflow only.

## Rate limiting
backend/app/rate_limit.py uses SlowAPI. It selects RATE_LIMIT_STORAGE_URI, then REDIS_URL. In production (RENDER=true, or APP_ENV/ENVIRONMENT=production) the app refuses to start without Redis unless ALLOW_IN_MEMORY_RATE_LIMIT=true is set. Outside production it falls back to memory://, which is process-local and development-only. Callers are identified by socket address unless TRUSTED_PROXY_HOPS is set, in which case the X-Forwarded-For entry appended by the trusted proxy is used (leftmost entries are client-controlled and never trusted). Behind a shared proxy without this setting, all clients may share one rate-limit bucket. Production startup fails if Redis is missing unless ALLOW_IN_MEMORY_RATE_LIMIT=true is explicitly set; that override is not suitable for production.

## Travel data and provenance
backend/app/mock_data/ contains static demonstration fixtures. These are not live flight, hotel, event, price, inventory, or booking data. Preserve sample/unverified labels.

Web search results include source context but are not automatically verified. Do not present snippets as confirmed facts or live availability. Users should check primary sources for time-sensitive details.

Render filesystems are ephemeral. Never store durable user-owned memories in SQLite, JSON fixtures, or the Render filesystem. Supabase free-tier backups are manual; see DATABASE_BACKUPS.md for the travel-memory export and restore procedure.

## Email
The email service reads SMTP settings from backend environment variables. Delivery requires SMTP host, username, password, and sender configuration. Do not claim delivery works until tested. Never expose SMTP credentials to frontend. Without SMTP configured, local development writes to a file outbox; in production the send fails with an error instead of pretending to succeed. /api/digest/send requires a signed-in session and only sends to the verified email of that account; the client cannot choose a recipient.

## Data ownership
- User identity/session: Supabase Auth.
- Saved travel memories: Supabase PostgreSQL.
- Demo fixtures: repository JSON files, version-controlled samples.
- Rate-limit counters: Upstash Redis in production; process memory only in local development or when the explicit production override is enabled.
- Frontend assets: Vercel deployment artifact.

## Operational caveats
- Render free services can sleep and local storage is ephemeral.
- Free-tier quotas and limits can change.
- /healthz is a process health check, not end-to-end readiness.
- A configured Gemini key does not prove model requests succeed.
- A configured Redis URL does not prove connectivity or fail-closed behavior.
- Signup redirects, RLS isolation, and account deletion require deployment-level verification.
See DEPLOYMENT.md for release configuration.
