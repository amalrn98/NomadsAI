create table public.travel_memories (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  title text not null check (char_length(title) between 1 and 160),
  content text not null default '' check (char_length(content) <= 10000),
  destination text not null check (char_length(destination) between 1 and 160),
  image_url text,
  mood text check (mood is null or char_length(mood) <= 32),
  weather text check (weather is null or char_length(weather) <= 32),
  companions text[] not null default '{}',
  created_at timestamptz not null default now()
);

create index travel_memories_user_created_idx
  on public.travel_memories (user_id, created_at desc);

alter table public.travel_memories enable row level security;

revoke all on table public.travel_memories from anon;
grant select, insert, update, delete on table public.travel_memories to authenticated;

create policy "Users can read their own travel memories"
  on public.travel_memories for select
  to authenticated
  using ((select auth.uid()) = user_id);

create policy "Users can create their own travel memories"
  on public.travel_memories for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

create policy "Users can update their own travel memories"
  on public.travel_memories for update
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

create policy "Users can delete their own travel memories"
  on public.travel_memories for delete
  to authenticated
  using ((select auth.uid()) = user_id);
