# Frontend

This directory contains the NomadsAI Next.js App Router application.

For full setup, architecture, environment variables, and deployment, see:
- [Main README](../README.md)
- [Local development](../docs/LOCAL_DEVELOPMENT.md)
- [Architecture](../docs/ARCHITECTURE.md)
- [Deployment](../docs/DEPLOYMENT.md)

## Quick start
Requires Node.js 22+.

Install dependencies with npm ci.

Create .env.local in this directory:
- NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
- NEXT_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
- NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key

Start with npm run dev and visit http://localhost:3000.

## Checks
Run npm run lint and npm run build.

Only public client configuration belongs in NEXT_PUBLIC_ variables. Never put Gemini, SMTP, Redis, or Supabase secret/service-role credentials in this directory or browser environment.
