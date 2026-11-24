# Data, retention, and deletion

## Data stored

When a signed-in user saves a travel memory, NomadsAI stores these fields in Supabase PostgreSQL:

- Supabase Auth user ID (ownership key)
- Title, text content, destination
- Optional image URL, mood, weather, and companion labels
- Creation timestamp

The application does not store a user's password. Supabase Auth handles credentials. The frontend uses a publishable key; backend memory requests validate the Supabase access token and pass that token to Supabase PostgREST so row-level security is enforced.

## Access controls

Every memory read, create, update, and delete operation is scoped to the authenticated subject. The database has RLS policies that require `auth.uid() = user_id`. The API derives `user_id` from the verified token and does not accept it from the request body.

## Retention

There is no automatic age-based deletion or scheduled retention window. A memory remains stored until the user deletes it or the account is deleted by a project administrator. The database foreign key uses `ON DELETE CASCADE`, so deleting the corresponding Supabase Auth user also deletes that user's travel-memory rows.

## User deletion controls

- Individual memories can be deleted from the travel journal.
- Full account deletion is not currently self-service in the application. It must be performed by a Supabase project administrator through the Auth user-management controls.
- If a user requests full account deletion, the maintainer must verify the account identity, delete the Auth user, and confirm the associated memory rows were removed.
- Manual database backups can retain deleted memory data until those backup files are securely removed under the backup operator's retention policy. See [DATABASE_BACKUPS.md](DATABASE_BACKUPS.md).

## Verification status

Automated tests cover token-derived ownership and user-scoped API filters. Live cross-account isolation and full account-deletion behavior still require verification against the production Supabase project using two test accounts. Do not treat those live checks as complete until they pass.
