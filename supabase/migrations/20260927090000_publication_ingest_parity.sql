-- Curren landing replica: apply publication batches with the canonical read-model rules.
--
-- Rule authority: sangtrx/curren src/curren/store.py (ReadStore._upsert_signal) and
-- docs/API_CONTRACT.md. The Edge Function supabase/functions/curren-api/index.ts validates and
-- normalizes the PublicationBatch shape, then calls public.curren_ingest_publication once per
-- batch, so every batch is applied or rejected atomically.
--
-- Additive only. No existing view, policy, grant or row is changed and no public view gains a
-- column. The earlier empty tables public.signal_targets and public.signal_lifecycle are left as
-- they are; nothing writes them.
--
-- Stored terminal rows are treated as recorded outcomes, including rows replicated before this
-- migration: a later snapshot cannot rewrite them. Changing a published outcome needs an explicit
-- correction policy (internal tracking), not a silent overwrite.

-- Anonymous reads of public.signals must be column-scoped; otherwise the new targets column would
-- become readable. Refuse before changing anything.
do $$
begin
  if has_table_privilege('anon', 'public.signals', 'SELECT')
    or has_table_privilege('authenticated', 'public.signals', 'SELECT')
  then
    raise exception 'publication ingest objects must stay private from role anon/authenticated (table-level SELECT on public.signals)';
  end if;
end;
$$;

-- Target plan and hit state (FastAPI: signals.targets_json). NULL only on rows replicated before
-- this migration; the next accepted snapshot stores them.
alter table public.signals add column targets jsonb;

-- Append-only lifecycle (FastAPI: lifecycle_events). Identity is (signal_id, event_type, event_at).
create table public.lifecycle_events (
  id bigint generated always as identity primary key,
  signal_id text not null references public.signals (id) on delete cascade,
  event_type text not null,
  event_at timestamptz not null,
  price double precision,
  r_multiple double precision,
  recorded_at timestamptz not null default now(),
  unique (signal_id, event_type, event_at)
);

alter table public.lifecycle_events enable row level security;
revoke all on table public.lifecycle_events from public, anon, authenticated;
revoke all on sequence public.lifecycle_events_id_seq from public, anon, authenticated;
grant select, insert on table public.lifecycle_events to service_role;
revoke update, delete, truncate on table public.lifecycle_events from service_role;

create function public.curren_ingest_publication(
  p_source text,
  p_generated_at timestamptz,
  p_signals jsonb
) returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_item jsonb;
  v_event jsonb;
  v_row public.signals%rowtype;
  v_stored_event public.lifecycle_events%rowtype;
  -- Incoming values use the stored column types so comparisons are exact.
  v_id public.signals.id%type;
  v_source public.signals.source%type := p_source;
  v_generated_at public.signals.source_generated_at%type := p_generated_at;
  v_symbol public.signals.symbol%type;
  v_side public.signals.side%type;
  v_status public.signals.status%type;
  v_published_at public.signals.published_at%type;
  v_public_available_at public.signals.public_available_at%type;
  v_entry public.signals.entry%type;
  v_stop public.signals.stop%type;
  v_mark public.signals.mark%type;
  v_current_r public.signals.current_r%type;
  v_peak_r public.signals.peak_r%type;
  v_realized_r public.signals.realized_r%type;
  v_closed_at public.signals.closed_at%type;
  v_exit_reason public.signals.exit_reason%type;
  v_targets jsonb;
  v_terminal boolean;
  v_event_type text;
  v_event_at timestamptz;
  v_event_price double precision;
  v_event_r double precision;
  v_inserted integer := 0;
  v_updated integer := 0;
  v_stale integer := 0;
  v_events integer := 0;
  v_outcomes integer := 0;
begin
  if jsonb_typeof(p_signals) is distinct from 'array' then
    raise exception 'signals must be an array' using errcode = 'PT422';
  end if;

  for v_item in select value from jsonb_array_elements(p_signals) loop
    v_id := v_item ->> 'id';
    v_symbol := v_item ->> 'symbol';
    v_side := v_item ->> 'side';
    v_status := v_item ->> 'status';
    v_published_at := v_item ->> 'published_at';
    v_public_available_at := v_item ->> 'public_available_at';
    v_entry := v_item ->> 'entry';
    v_stop := v_item ->> 'stop';
    v_mark := v_item ->> 'mark';
    v_current_r := v_item ->> 'current_r';
    v_peak_r := v_item ->> 'peak_r';
    v_realized_r := v_item ->> 'realized_r';
    v_closed_at := v_item ->> 'closed_at';
    v_exit_reason := v_item ->> 'exit_reason';
    v_targets := coalesce(v_item -> 'targets', '[]'::jsonb);
    v_terminal := (v_item ->> 'status') in ('closed', 'expired');
    if v_terminal then
      v_current_r := null;
    end if;

    select * into v_row from public.signals where id = v_id for update;

    if found then
      if v_row.source is not null and v_row.source <> v_source then
        raise exception 'publication source changed for %', v_id using errcode = 'PT409';
      end if;
      if v_row.source_generated_at is not null and v_generated_at <= v_row.source_generated_at then
        v_stale := v_stale + 1;
        continue;
      end if;
      if v_row.status::text in ('closed', 'expired') and not v_terminal then
        raise exception 'terminal signal cannot return to a live state for %', v_id using errcode = 'PT409';
      end if;
      if v_row.symbol is distinct from v_symbol
        or v_row.side is distinct from v_side
        or v_row.published_at is distinct from v_published_at
        or v_row.entry is distinct from v_entry
        or v_row.stop is distinct from v_stop
        or (
          v_row.targets is not null
          and jsonb_path_query_array(v_row.targets, '$[*].price')
            <> jsonb_path_query_array(v_targets, '$[*].price')
        )
      then
        raise exception 'immutable publication fields changed for %', v_id using errcode = 'PT409';
      end if;

      if v_row.status::text in ('closed', 'expired') then
        if v_row.status is distinct from v_status
          or v_row.realized_r is distinct from v_realized_r
          or v_row.closed_at is distinct from v_closed_at
          or v_row.exit_reason is distinct from v_exit_reason
        then
          raise exception 'immutable terminal outcome changed for %', v_id using errcode = 'PT409';
        end if;
        -- current_r is live-only and not part of the frozen projection.
        if v_row.mark is distinct from v_mark
          or v_row.peak_r is distinct from v_peak_r
          or (v_row.targets is not null and v_row.targets <> v_targets)
        then
          raise exception 'immutable terminal projection changed for %', v_id using errcode = 'PT409';
        end if;
        update public.signals
        set source_generated_at = v_generated_at,
            targets = coalesce(targets, v_targets),
            current_r = null,
            updated_at = now()
        where id = v_id;
      else
        update public.signals
        set source = coalesce(source, v_source),
            source_generated_at = v_generated_at,
            status = v_status,
            public_available_at = coalesce(public_available_at, v_public_available_at),
            targets = v_targets,
            mark = v_mark,
            current_r = v_current_r,
            peak_r = v_peak_r,
            realized_r = v_realized_r,
            closed_at = v_closed_at,
            exit_reason = v_exit_reason,
            updated_at = now()
        where id = v_id;
        if v_terminal then
          v_outcomes := v_outcomes + 1;
        end if;
      end if;
      v_updated := v_updated + 1;
    else
      insert into public.signals (
        id, source, source_generated_at, symbol, side, status, published_at, public_available_at,
        entry, stop, targets, mark, current_r, peak_r, realized_r, closed_at, exit_reason, updated_at
      ) values (
        v_id, v_source, v_generated_at, v_symbol, v_side, v_status, v_published_at, v_public_available_at,
        v_entry, v_stop, v_targets, v_mark, v_current_r, v_peak_r, v_realized_r, v_closed_at, v_exit_reason, now()
      );
      v_inserted := v_inserted + 1;
      if v_terminal then
        v_outcomes := v_outcomes + 1;
      end if;
    end if;

    for v_event in select value from jsonb_array_elements(coalesce(v_item -> 'lifecycle', '[]'::jsonb)) loop
      v_event_type := v_event ->> 'event_type';
      v_event_at := v_event ->> 'event_at';
      v_event_price := v_event ->> 'price';
      v_event_r := v_event ->> 'r_multiple';
      insert into public.lifecycle_events (signal_id, event_type, event_at, price, r_multiple)
      values (v_id, v_event_type, v_event_at, v_event_price, v_event_r)
      on conflict (signal_id, event_type, event_at) do nothing;
      if found then
        v_events := v_events + 1;
      else
        select * into v_stored_event
        from public.lifecycle_events
        where signal_id = v_id and event_type = v_event_type and event_at = v_event_at;
        if v_stored_event.price is distinct from v_event_price
          or v_stored_event.r_multiple is distinct from v_event_r
        then
          raise exception 'immutable lifecycle event changed for %', v_id using errcode = 'PT409';
        end if;
      end if;
    end loop;
  end loop;

  return jsonb_build_object(
    'accepted', jsonb_array_length(p_signals),
    'inserted', v_inserted,
    'updated', v_updated,
    'stale_ignored', v_stale,
    'lifecycle_events_inserted', v_events,
    'outcome_records_inserted', v_outcomes
  );
end;
$$;

revoke all on function public.curren_ingest_publication(text, timestamptz, jsonb) from public, anon, authenticated;
grant execute on function public.curren_ingest_publication(text, timestamptz, jsonb) to service_role;

-- Fail closed if an anonymous or signed-in client could read or call the new private objects.
do $$
declare
  v_role text;
begin
  foreach v_role in array array['anon', 'authenticated'] loop
    if has_column_privilege(v_role, 'public.signals', 'targets', 'SELECT')
      or has_table_privilege(v_role, 'public.lifecycle_events', 'SELECT, INSERT, UPDATE, DELETE')
      or has_sequence_privilege(v_role, 'public.lifecycle_events_id_seq', 'USAGE, SELECT, UPDATE')
      or has_function_privilege(v_role, 'public.curren_ingest_publication(text, timestamptz, jsonb)', 'EXECUTE')
    then
      raise exception 'publication ingest objects must stay private from role %', v_role;
    end if;
  end loop;
end;
$$;

notify pgrst, 'reload schema';
