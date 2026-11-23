# NomadsAI

AI-assisted travel planning with a Next.js frontend and FastAPI backend. Gemini is the sole supported generative AI provider.

## Stack

- Frontend: Next.js, React and TypeScript
- Backend: FastAPI and Python
- AI: Google Gemini Developer API
- Authentication and user data: Supabase Auth and PostgreSQL
- Deployment: Vercel (frontend) and Render (backend)

## Features

- AI-generated travel itineraries
- Conversational travel planning
- Destination context and travel signals
- Email/password authentication
- Private travel memories with per-account PostgreSQL row-level security

## Configure the backend

Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey).

Set these variables in the backend environment:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.8-flash
CORS_ORIGINS=http://localhost:3000
SUPABASE_URL=https://ggisuouanswimpvslluf.supabase.co
SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key
```

The Gemini API key must remain server-side. Never add it to frontend environment variables, source control, browser code, or client requests.

The Supabase publishable key is intended for public clients. Never use a Supabase secret or `service_role` key in frontend configuration.

## Local development

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
# Add GEMINI_API_KEY and SUPABASE_PUBLISHABLE_KEY to .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend

Use Node.js 22 or newer, matching the Supabase JavaScript client requirement and the Vercel project runtime.

```bash
cd frontend
npm install
npm run dev
```

Set these frontend variables in `.env.local`:

```dotenv
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=https://ggisuouanswimpvslluf.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key
```

## Supabase Auth and private memories

NomadsAI uses the separate Supabase project `ggisuouanswimpvslluf` in the Mumbai region (`ap-south-1`). The migration in `supabase/migrations/` creates `public.travel_memories`, a user-owned table with row-level security policies for select, insert, update, and delete. Deleting an Auth user cascades to their memories.

The frontend uses Supabase email/password authentication with PKCE and the public publishable key. The FastAPI backend validates each bearer access token with Supabase Auth's `/auth/v1/user` endpoint. Memory requests forward that same user token to PostgREST, where RLS enforces ownership. The backend never uses a service-role key.

In the Supabase Dashboard for this project:

1. Confirm the Email provider is enabled.
2. Set the Site URL to the production frontend origin.
3. Add the production origin plus `/memories` to the allowed redirect URLs. Add local development (`http://localhost:3000/**`) and the exact Vercel preview origins you intend to test.
4. Configure SMTP if you need reliable account confirmation email delivery. Keep SMTP credentials in Supabase Auth settings, never in Git.

## Deployment

In Render, configure these backend variables:

- `GEMINI_API_KEY` (secret)
- `GEMINI_MODEL=gemini-3.8-flash`
- `SUPABASE_URL=https://ggisuouanswimpvslluf.supabase.co`
- `SUPABASE_PUBLISHABLE_KEY` (publishable key)
- `CORS_ORIGINS` (comma-separated exact Vercel production and preview origins)
- `RATE_LIMIT_STORAGE_URI` or `REDIS_URL` (a Redis URL for shared rate limits)

In Vercel, configure `NEXT_PUBLIC_API_BASE` to the actual Render backend URL, along with the two `NEXT_PUBLIC_SUPABASE_*` values. The public Supabase URL and publishable key are configured for development, preview, and production. Do not expose backend secrets through `NEXT_PUBLIC_` variables.

Free-tier caveats: Supabase may pause inactive free projects and does not provide automatic backups on the free plan. Render free services sleep when idle and have ephemeral filesystems. User data must stay in Supabase, not local SQLite. Use Redis for shared rate limits; the in-memory limiter fallback is not suitable for multiple instances.

## API health

- `GET /healthz`: application health
- `GET /api/ai-status`: Gemini configuration and selected model
- `GET /api/pipeline-status`: pipeline status
- `GET /api/memory/`: authenticated user-scoped memory list
- `POST /api/memory/`: create a memory
- `PATCH /api/memory/{id}`: update a memory
- `DELETE /api/memory/{id}`: delete a memory

The AI status endpoint never returns the API key.

## Security notes

- Client-supplied identity values are never trusted for memory authorization.
- Chat does not yet read or write persistent long-term memory.
- Rotate a key immediately if it is accidentally committed or exposed.
- Restrict the Gemini key to the Gemini API in Google AI Studio / Google Cloud where available.
- Use an explicit list of trusted frontend origins in `CORS_ORIGINS`, not a wildcard.
- Public chat and itinerary-generation routes have per-IP limits. Configure Redis for shared limits across backend instances; the in-memory fallback is intended only for development or a single instance.

## Contributing

1. Create a focused feature branch.
2. Make one logically scoped change.
3. Add or update tests.
4. Run the backend and frontend checks relevant to the change.
5. Open a pull request with the motivation, implementation notes, and test results.

## License

See [LICENSE](LICENSE).
