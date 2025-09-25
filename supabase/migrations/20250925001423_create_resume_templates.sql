-- =========================================================
-- Resume template metadata table
-- =========================================================

-- 1) Enum types
do $$
begin
  if not exists (select 1 from pg_type where typname = 'resume_template_tier') then
    create type public.resume_template_tier as enum ('ATS','Professional','Creative');
  end if;

  if not exists (select 1 from pg_type where typname = 'template_engine') then
    create type public.template_engine as enum ('jinja2','handlebars','latex','docx-xml');
  end if;
end $$;

-- 2) Updated-at trigger helper (idempotent)
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end $$;

-- 3) Templates table
create table if not exists public.resume_templates (
  id                text primary key,                    -- e.g. "two_col_modern"
  name              text not null,
  tier              public.resume_template_tier not null,
  engine            public.template_engine not null default 'jinja2',
  ats_strict        boolean not null default true,

  -- Structure & capabilities
  layout            jsonb not null,                      -- slots & default order
  supported_sections jsonb not null,                     -- {required:[], optional:[]}
  design_tokens     jsonb not null,                      -- default tokens; theme overrides can layer on top
  capabilities      jsonb not null,                      -- ["sidebar","timeline-accent",...]
  print_options     jsonb not null,                      -- {page:"A4",margins_mm:16,min_font_pt:10.5}

  -- Where the actual skeleton (HTML/Jinja/LaTeX/DOCX-XML) lives in storage/CDN
  skeleton_handle   text,                                -- e.g. "templates/two_col_modern/v3/index.html"
  active_version    integer not null default 1,          -- pointer for current published version
  changelog         text,                                -- optional notes for this template row

  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

-- 4) Trigger to maintain updated_at
drop trigger if exists trg_resume_templates_updated_at on public.resume_templates;
create trigger trg_resume_templates_updated_at
before update on public.resume_templates
for each row execute function public.set_updated_at();

-- 5) Helpful indexes for querying/filtering
create index if not exists idx_resume_templates_layout           on public.resume_templates using gin (layout);
create index if not exists idx_resume_templates_supported        on public.resume_templates using gin (supported_sections);
create index if not exists idx_resume_templates_capabilities     on public.resume_templates using gin (capabilities);
create index if not exists idx_resume_templates_tier             on public.resume_templates (tier);
create index if not exists idx_resume_templates_engine           on public.resume_templates (engine);
create index if not exists idx_resume_templates_active_version   on public.resume_templates (active_version);

-- 6) Row Level Security (RLS)
alter table public.resume_templates enable row level security;

-- Allow anyone (anon or authenticated) to read templates (you can tighten later if needed)
drop policy if exists "Public read templates" on public.resume_templates;
create policy "Public read templates"
on public.resume_templates
for select
to anon, authenticated
using (true);

-- Restrict writes to service_role only (API key with elevated privileges)

-- Inserts
drop policy if exists "Service role can insert templates" on public.resume_templates;
create policy "Service role can insert templates"
on public.resume_templates
for insert
to service_role
with check (true);

-- Updates
drop policy if exists "Service role can update templates" on public.resume_templates;
create policy "Service role can update templates"
on public.resume_templates
for update
to service_role
using (true)
with check (true);

-- Deletes
drop policy if exists "Service role can delete templates" on public.resume_templates;
create policy "Service role can delete templates"
on public.resume_templates
for delete
to service_role
using (true);
