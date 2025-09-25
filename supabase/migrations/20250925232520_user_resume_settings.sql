create table if not exists public.user_resume_settings (
  resume_id uuid primary key,
  user_id uuid not null,
  template_id text not null references public.resume_templates(id),
  theme_overrides jsonb not null default '{}',   -- {accent, density, fonts...}
  updated_at timestamptz not null default now()
);

alter table public.user_resume_settings enable row level security;
-- RLS: owner can read/write their own rows 
create policy "resume owner read" on public.user_resume_settings
  for select to authenticated using (auth.uid() = user_id);
create policy "resume owner write" on public.user_resume_settings
  for insert with check (auth.uid() = user_id);
create policy "resume owner update" on public.user_resume_settings
  for update using (auth.uid() = user_id) with check (auth.uid() = user_id);
