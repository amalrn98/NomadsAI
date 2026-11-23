# Local development

This guide takes a new contributor from a clean clone to a running frontend and backend.

## Prerequisites
- Git
- Python 3.11+
- Node.js 22+
- npm
- A Supabase project for authentication and persistent memories
- A Gemini API key for AI-backed features

Redis and SMTP are optional locally. Features depending on them will not work without configuration or may use local fallback behavior.

## 1. Clone
    git clone https://github.com/amalrn98/NomadsAI.git
    cd NomadsAI

## 2. Backend
    cd backend
    python -m venv .venv
    # macOS/Linux
    source .venv/bin/activate
    # Windows PowerShell
    .venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    cp .env.example .env

For Windows Command Prompt, use copy .env.example .env.

Edit backend/.env:
    GEMINI_API_KEY=your_gemini_api_key
    GEMINI_MODEL=gemini-3.8-flash
    CORS_ORIGINS=http://localhost:3000
    SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
    SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key

Create a Gemini key in Google AI Studio: https://aistudio.google.com/apikey. Keep it backend-only.

The checked-in backend/.env.example currently includes Gemini and CORS only. Add Supabase values when using account and memory features. Optional:
    RATE_LIMIT_STORAGE_URI=redis://default:password@host:port
    # Or REDIS_URL instead
    SMTP_HOST=
    SMTP_PORT=587
    SMTP_USER=
    SMTP_PASS=
    FROM_EMAIL=

Never commit .env.

Start from backend/:
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

## 3. Supabase
1. Create a Supabase project and copy its URL and publishable key.
2. In the SQL Editor, apply every file in supabase/migrations/ in ascending filename order.
3. Enable email signups if using email/password registration.
4. Add http://localhost:3000/** to allowed redirect URLs.
5. Set local Site URL to http://localhost:3000.

The migrations create public.travel_memories, enforce ownership, enable RLS, and grant authenticated users the required operations. Policies scope rows to auth.uid(). For the Supabase CLI, install it using official instructions, authenticate, link your own project, review pending migrations, then use supabase db push. Do not link a fork to the project owner's production database.

## 4. Frontend
Open a second terminal at repository root:
    cd frontend
    npm ci

Create frontend/.env.local:
    NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
    NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key

There is no checked-in frontend .env.example. These are the variables used by the frontend API and Supabase client. Start:
    npm run dev

Visit http://localhost:3000.

Only public configuration belongs in NEXT_PUBLIC_ variables. Never put Gemini, SMTP, Redis, or Supabase secret/service-role credentials in the browser.

## 5. Verify
- Frontend: http://localhost:3000
- Auth page: http://localhost:3000/auth
- API root: http://127.0.0.1:8000/
- OpenAPI docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/healthz
- AI configuration: http://127.0.0.1:8000/api/ai-status

/healthz only confirms the API process responds. /api/ai-status reports configuration, not a successful live Gemini generation.

## 6. Checks
Backend, from backend/: python -m pytest -q
Frontend, from frontend/: npm ci, npm run lint, npm run build

See TROUBLESHOOTING.md for common errors.
