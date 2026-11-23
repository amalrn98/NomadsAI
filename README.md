# NomadsAI

NomadsAI is an AI-assisted travel planning application built with Next.js, FastAPI, Google Gemini, Supabase Auth/PostgreSQL, and optional Redis-backed rate limiting.

This repository is intended to be independently understandable and runnable. Start with this guide, then use the linked documentation for setup, architecture, deployment, and contribution.

## Project status and limitations

NomadsAI is actively developed. Static travel fixtures and local destination knowledge are illustrative, not live pricing, schedules, inventory, or booking availability. Search results are not automatically verified. See [Architecture](docs/ARCHITECTURE.md#travel-data-and-provenance).

The deployment target is free-tier infrastructure. Free services can sleep, impose quotas, change limits, or become unavailable. Do not add paid infrastructure without explicit approval.

## Repository map

| Path | Responsibility |
| --- | --- |
| frontend/ | Next.js App Router application, public pages, auth UI, chat, memories, digest, pricing |
| backend/app/routers/ | FastAPI HTTP endpoints |
| backend/app/services/ | Gemini, search, email, and supporting services |
| backend/app/pipeline/ | Itinerary generation and destination knowledge |
| backend/app/mock_data/ | Demonstration event, flight, and hotel fixtures |
| backend/tests/ | Backend API, auth, security, and behavior tests |
| supabase/migrations/ | Versioned PostgreSQL schema and access-control migrations |
| .github/workflows/ | CI, dependency audits, CodeQL, secret scanning |
| render.yaml | Render backend configuration |
| CLAUDE.md | Persistent project context and coding-agent handoff |
| docs/ | Setup, architecture, deployment, and troubleshooting guides |

## Architecture

- **Frontend:** Next.js App Router, React, TypeScript, hosted on Vercel.
- **Backend:** FastAPI on Python 3.11, hosted on Render.
- **AI:** Google Gemini, called server-side. Keep its API key out of the browser.
- **Identity:** Supabase Auth using browser publishable key and PKCE.
- **User data:** Supabase PostgreSQL. travel_memories uses row-level security tied to auth.uid().
- **Rate limiting:** SlowAPI with Redis when RATE_LIMIT_STORAGE_URI or REDIS_URL is configured. In production (Render, or APP_ENV/ENVIRONMENT=production) the backend refuses to start without Redis unless ALLOW_IN_MEMORY_RATE_LIMIT=true is set deliberately. Outside production it uses process-local memory, which is not shared across instances and resets on restart.
- **Travel data:** Local fixtures and cached/curated destination knowledge are not live booking inventory.

See [Architecture](docs/ARCHITECTURE.md) for request flows, trust boundaries, and data ownership.

## Quick start

### Requirements

- Git
- Python 3.11+
- Node.js 22+
- npm
- A Supabase project for auth and persistent memories
- A Gemini API key for AI-backed features

Redis and SMTP are optional for local development.

### 1. Clone

    git clone https://github.com/amalrn98/NomadsAI.git
    cd NomadsAI

### 2. Backend

    cd backend
    python -m venv .venv

Activate the environment:

    # macOS / Linux
    source .venv/bin/activate

    # Windows PowerShell
    .venv\Scripts\Activate.ps1

Install and create the backend environment file:

    python -m pip install --upgrade pip
    pip install -r requirements.txt
    cp .env.example .env

For Windows Command Prompt, use copy .env.example .env.

Edit backend/.env and set:

    GEMINI_API_KEY=your_gemini_api_key
    GEMINI_MODEL=gemini-3.8-flash
    CORS_ORIGINS=http://localhost:3000
    SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
    SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key

Start the API from backend/:

    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

Useful endpoints:

- API root: http://127.0.0.1:8000/
- Interactive API docs: http://127.0.0.1:8000/docs
- Process health: http://127.0.0.1:8000/healthz
- AI configuration: http://127.0.0.1:8000/api/ai-status

The health endpoint only confirms that the API process responds. It does not prove Gemini, Supabase, Redis, or email works.

### 3. Supabase

1. Create a Supabase project.
2. Copy its URL and publishable key into the backend environment and frontend environment below.
3. Apply all SQL files in supabase/migrations/ in ascending filename order.
4. Enable email signups if using email/password registration.
5. Add http://localhost:3000/** to allowed Auth redirect URLs and use http://localhost:3000 as the local Site URL.

The migrations create public.travel_memories and enforce per-user access with RLS. Do not disable RLS to work around a failing request. For a fork, use your own Supabase project, never the project owner's database.

### 4. Frontend

Open a second terminal at the repository root:

    cd frontend
    npm ci

Create frontend/.env.local:

    NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
    NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key

Start:

    npm run dev

Open http://localhost:3000.

Only public values belong in NEXT_PUBLIC_ variables. Never put Gemini credentials, SMTP passwords, Redis credentials, or Supabase secret/service-role keys in the browser.

## Tests and checks

Backend, from backend/:

    python -m pytest -q

Frontend, from frontend/:

    npm ci
    npm run lint
    npm run build

GitHub Actions also runs dependency audits, CodeQL, and Gitleaks. Check actual workflow results on each PR.

## Environment variables

| Variable | Location | Purpose |
| --- | --- | --- |
| GEMINI_API_KEY | Backend only | Google AI Studio API key |
| GEMINI_MODEL | Backend | Model identifier, code default gemini-3.8-flash |
| SUPABASE_URL | Backend | Supabase project URL |
| SUPABASE_PUBLISHABLE_KEY | Backend | Supabase publishable key for Auth validation and user-scoped data access |
| CORS_ORIGINS | Backend | Comma-separated allowed frontend origins |
| RATE_LIMIT_STORAGE_URI | Backend | Redis URI for shared rate limits |
| REDIS_URL | Backend | Alternative Redis URI |
| ALLOW_IN_MEMORY_RATE_LIMIT | Backend | Set to true only to knowingly run production with process-local rate limits |
| TRUSTED_PROXY_HOPS | Backend | Number of trusted reverse proxies appending to X-Forwarded-For; 0 (default) uses the socket address. Verify against the real deployment before setting |
| SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL | Backend | Optional email delivery configuration |
| NEXT_PUBLIC_API_BASE | Frontend | FastAPI base URL |
| NEXT_PUBLIC_SUPABASE_URL | Frontend | Supabase project URL |
| NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY | Frontend | Supabase publishable key |

The backend template is backend/.env.example. There is currently no frontend .env.example; create frontend/.env.local using the values above.

## Documentation and contribution

- [Local development](docs/LOCAL_DEVELOPMENT.md)
- [Architecture and data boundaries](docs/ARCHITECTURE.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Contributing](CONTRIBUTING.md)
- [Claude Code and coding-agent handoff](CLAUDE.md)
- [Security](SECURITY.md)

## License

See [LICENSE](LICENSE).
