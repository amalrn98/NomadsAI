# Supabase travel-memory backup and restore

NomadsAI stores account-owned travel memories in Supabase PostgreSQL. The SQL schema and RLS policies are versioned in `supabase/migrations/`. The free Supabase plan does not provide automatic database backups, so backups are a manual operator task. This procedure uses PostgreSQL client tools and does not require a paid backup service.

## What is covered

The backup command below exports rows from `public.travel_memories`. The schema and RLS policies are recreated by applying the versioned migrations to the restore project first. Supabase Auth users are not exported by this procedure. A restored memory row still references its original `auth.users.id`, so restore the matching Auth users separately or use a dedicated test project with matching user IDs before validating account access.

## Create a backup

1. Install PostgreSQL client tools compatible with the Supabase PostgreSQL version.
2. In the Supabase Dashboard, copy a direct database connection string or Session Pooler connection string. Do not use a transaction pooler for `pg_dump`.
3. Keep the connection string out of shell history and source control. Read it into the environment interactively:

```bash
read -rsp "Supabase database URL: " SUPABASE_DB_URL
echo
export SUPABASE_DB_URL
```

4. Create a private backup directory and export the memory rows:

```bash
umask 077
mkdir -p "$HOME/nomadsai-backups"
pg_dump \
  --format=custom \
  --data-only \
  --no-owner \
  --no-privileges \
  --table=public.travel_memories \
  "$SUPABASE_DB_URL" \
  --file="$HOME/nomadsai-backups/travel-memories-$(date -u +%F).dump"
```

5. Confirm the file exists and record its size. Keep it encrypted and outside the Git repository. Do not upload it to a public file host.

Repeat this manually on a schedule appropriate to the amount of new memory data, and before risky schema changes. The application does not currently automate or retain backups.

## Restore test

Use a separate, empty Supabase project. Never test restoration by overwriting production.

1. Apply every migration in `supabase/migrations/` to the restore project in filename order.
2. Set the restore connection string without committing it:

```bash
read -rsp "Restore database URL: " RESTORE_DATABASE_URL
echo
export RESTORE_DATABASE_URL
```

3. Restore the memory rows:

```bash
pg_restore \
  --data-only \
  --no-owner \
  --no-privileges \
  --exit-on-error \
  --dbname="$RESTORE_DATABASE_URL" \
  "$HOME/nomadsai-backups/travel-memories-YYYY-MM-DD.dump"
```

4. Verify row counts and RLS:

```sql
select count(*) from public.travel_memories;
select relrowsecurity
from pg_class
where oid = 'public.travel_memories'::regclass;
```

5. If the restore project does not contain the corresponding Auth users, the foreign-key references will prevent restoring those rows. Do not disable the foreign key or RLS to bypass this. Use a controlled test project with matching Auth identities or restore the matching Auth users through an approved process.
6. Sign in as two separate test accounts and verify that each can read, update, and delete only its own rows.

## Operational limits

- This is a manual backup procedure, not an automated backup service.
- Supabase Auth user records and other application data are outside the table-only dump.
- Backup files contain personal travel memories. Restrict access, encrypt at rest, and delete old copies securely.
- A backup is not considered verified until a restore test completes successfully.
- No paid database plan, storage service, or recurring backup service is required by this procedure.
