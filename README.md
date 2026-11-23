# NomadsAI

AI-assisted travel planning with a Next.js frontend, FastAPI API, Google Gemini, and Supabase-backed accounts and private travel memories.

## Repository map

```text
.
├── backend/
│   ├── app/
│   │   ├── routers/       # HTTP API routes
│   │   ├── services/      # Gemini, search, email and domain services
│   │   ├── pipeline/      # Itinerary pipeline and fallback logic
│   │   └── utils/         # Shared backend utilities
│   └── tests/             # Backend tests
├── frontend/
│   ├── app/               # Next.js routes and layouts
│   ├── components/        # Shared UI components
│   └── lib/               # Client utilities and Supabase setup
├── supabase/
│   └── migrations/        # Versioned database migrations
├── .github/workflows/     # CI and security automation
├── .env.example           # Local environment variable template
└── render.yaml            # Render backend deployment configuration
```

## Local development

### Backend

Requires Python 3.11 or newer.

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Configure `GEMINI_API_KEY`, `SUPABASE_URL`, and `SUPABASE_PUBLISHABLE_KEY` in the backend environment.

### Frontend

Requires Node.js 22 or newer.

```bash
cd frontend
npm ci
npm run dev
```

Set `NEXT_PUBLIC_API_BASE`, `NEXT_PUBLIC_SUPABASE_URL`, and `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` in `.env.local`.

## Runtime architecture

- **Web:** Next.js App Router, deployed on Vercel.
- **API:** FastAPI, deployed on Render.
- **AI:** Google Gemini. Keep the Gemini API key on the backend only.
- **Identity:** Supabase Auth with email/password and PKCE.
- **User data:** Supabase PostgreSQL. The `travel_memories` table uses row-level security tied to `auth.uid()`.
- **Rate limits:** Redis via Upstash. Configure `RATE_LIMIT_STORAGE_URI` or `REDIS_URL`.
- **Travel signals:** Static fixtures are explicitly marked as sample data. Search results include source provenance.

## Database changes

SQL migrations live in `supabase/migrations/`. Apply migrations to the Supabase project before deploying code that depends on them. Do not edit an already-applied migration; add a new migration instead.

## Tests and checks

From the repository root:

```bash
cd backend
python -m pytest -q
```

Frontend production build:

```bash
cd frontend
npm ci
npm run build
```

GitHub Actions runs backend tests, frontend build, dependency audits, CodeQL, and secret scanning.

## Deployment configuration

- **Vercel:** Set the project root to `frontend`. Configure the three `NEXT_PUBLIC_*` variables above.
- **Render:** Use `render.yaml`. Configure Gemini, Supabase, CORS, and Redis values in the Render dashboard.
- **Supabase:** Configure the production Site URL and allowed Auth redirect URLs in the Supabase dashboard.

The project targets free-tier infrastructure. Free services may sleep, pause, or impose usage limits. Render filesystems are ephemeral, so user-owned data must remain in Supabase rather than local files.

## Security

Never commit API keys, service-role keys, access tokens, or production environment files. Use provider dashboards for secrets. See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## License

See [LICENSE](LICENSE).
