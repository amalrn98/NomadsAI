# Troubleshooting

Start with the exact error, the service that emitted it, and provider logs. Change one setting at a time.

## Backend does not start
- Confirm Python 3.11+.
- Activate the virtual environment.
- Install requirements from backend/.
- Start Uvicorn with backend/ as the working directory: uvicorn app.main:app --reload --host 127.0.0.1 --port 8000.

## Frontend cannot reach backend
- Confirm backend is listening at http://127.0.0.1:8000.
- Confirm NEXT_PUBLIC_API_BASE in frontend/.env.local.
- Confirm CORS_ORIGINS in backend/.env includes exact frontend origin, normally http://localhost:3000.
- Restart Next.js after changing .env.local.
- Inspect browser network tools and backend logs.

## Supabase sign-in or registration fails
- Confirm NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY in frontend/.env.local.
- Confirm SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY in backend/.env for protected memory APIs.
- Confirm email signup is enabled if using email/password.
- Confirm current origin and callback URL are allowed in Supabase Auth.
- Check whether email confirmation is enabled and inspect inbox/spam.
- Do not disable confirmation or broaden redirect URLs as a blind workaround.

## Memory endpoints return 401
- Sign in through frontend and ensure a current session exists.
- Confirm API request includes Authorization: Bearer <access-token>.
- Sign in again if token expired.
- Backend validates the token with Supabase Auth. A user ID is not a substitute for a valid session.

## Memory endpoints return 503
Supabase environment values may be missing, or Supabase may be unavailable. Check backend settings and logs. Never put a service-role key in frontend.

## Gemini features fail
- Confirm GEMINI_API_KEY exists in backend environment, not NEXT_PUBLIC_.
- Confirm key validity and API access in Google AI Studio.
- Confirm GEMINI_MODEL is available to the project.
- Inspect backend logs for quota, auth, and provider errors.
- /api/ai-status reports configuration, not successful generation. Test a real controlled request.

## Rate limits are inconsistent
- Check RATE_LIMIT_STORAGE_URI or REDIS_URL.
- Confirm URI is the provider TLS connection string and database is active.
- Current code falls back to in-memory storage when Redis is absent. Limits then reset on process restart and are not shared across instances.
- See issue #16.

## Hosted backend is slow
Render free instances may sleep. Check service events and logs before assuming an application defect. Do not add paid compute without owner approval.

## Frontend build or lint fails
Run npm ci, npm run lint, and npm run build from frontend/. Use Node.js 22+. Fix the first meaningful TypeScript/ESLint error, then rerun checks. Do not casually regenerate or bypass the lockfile.

## Backend tests fail
Run python -m pytest -q from backend/. Isolate the failing test while debugging, then rerun the full suite. Do not delete or weaken tests to make CI green. Mock external services using established test patterns.

## Travel data looks inaccurate
Static event, flight, and hotel fixtures are demonstrations. Search results are not verified availability or pricing. Check source provenance and timestamps.

## Production deployment did not update
- Confirm intended commit is on main.
- Inspect provider build logs and deployment status.
- Check free-tier deployment quotas and service limits.
- Verify the public URL after deployment. A merged PR does not prove production deployment succeeded.
