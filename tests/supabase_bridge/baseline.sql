-- Test fixture only. Stands in for the production curren-public objects that
-- supabase/migrations/20260927090000_publication_ingest_parity.sql builds on. The earlier production
-- migrations are not in source control, so this reproduces what the v2 bridge is known to rely on:
-- Supabase's API roles and default privileges, and the signals columns the v2 bridge wrote.

create role anon nologin noinherit;
create role authenticated nologin noinherit;
create role service_role nologin noinherit bypassrls;
create role authenticator login noinherit password 'authenticator';
grant anon, authenticated, service_role to authenticator;

grant usage on schema public to anon, authenticated, service_role;
alter default privileges in schema public grant all on tables to anon, authenticated, service_role;
alter default privileges in schema public grant all on sequences to anon, authenticated, service_role;
alter default privileges in schema public grant all on functions to anon, authenticated, service_role;

create table public.signals (
  id text primary key,
  source text,
  source_generated_at timestamptz,
  symbol text not null,
  side text not null check (side in ('long', 'short')),
  status text not null check (status in ('pending', 'active', 'closed', 'expired')),
  published_at timestamptz not null,
  public_available_at timestamptz not null,
  entry numeric,
  stop numeric,
  mark numeric,
  current_r numeric,
  peak_r numeric,
  realized_r numeric,
  closed_at timestamptz,
  exit_reason text,
  updated_at timestamptz not null default now()
);

alter table public.signals enable row level security;
revoke all on table public.signals from anon, authenticated;
grant select (
  id, symbol, side, status, published_at, public_available_at, mark, current_r, peak_r,
  realized_r, closed_at, exit_reason, source_generated_at, updated_at
) on public.signals to anon;
create policy public_signals_read on public.signals for select to anon
  using (status in ('closed', 'expired') or public_available_at <= now());
