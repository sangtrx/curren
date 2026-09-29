-- Read-only evidence query. Run inside BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
-- SET LOCAL TIME ZONE 'UTC'; then COMMIT. Retain the single JSON result privately.
-- All row columns are preserved as PostgreSQL JSON text (including numeric precision).
select jsonb_build_object(
  'catalog', jsonb_build_object(
    'columns', (select jsonb_agg(to_jsonb(c) order by table_name, ordinal_position)
      from information_schema.columns c where table_schema = 'public'
      and table_name in ('signals', 'lifecycle_events', 'signal_targets', 'signal_lifecycle')),
    'relations', (select jsonb_agg(jsonb_build_object('name', c.relname,
      'kind', c.relkind, 'rls', c.relrowsecurity, 'force_rls', c.relforcerowsecurity,
      'acl', c.relacl, 'options', c.reloptions) order by c.relname)
      from pg_class c join pg_namespace n on n.oid = c.relnamespace
      where n.nspname = 'public'),
    'constraints', (select coalesce(jsonb_agg(jsonb_build_object(
      'table', c.conrelid::regclass::text, 'name', c.conname,
      'definition', pg_get_constraintdef(c.oid)) order by c.conrelid::regclass::text, c.conname), '[]'::jsonb)
      from pg_constraint c where c.conrelid in
      ('public.signals'::regclass, 'public.lifecycle_events'::regclass,
       'public.signal_targets'::regclass, 'public.signal_lifecycle'::regclass)),
    'foreign_keys', (select coalesce(jsonb_agg(jsonb_build_object(
      'table', c.conrelid::regclass::text, 'name', c.conname,
      'definition', pg_get_constraintdef(c.oid), 'delete_action', c.confdeltype)
      order by c.conrelid::regclass::text, c.conname), '[]'::jsonb)
      from pg_constraint c where c.contype = 'f' and c.confrelid = 'public.signals'::regclass),
    'triggers', (select coalesce(jsonb_agg(pg_get_triggerdef(t.oid) order by t.oid), '[]'::jsonb)
      from pg_trigger t where not t.tgisinternal and t.tgrelid in
      ('public.signals'::regclass, 'public.lifecycle_events'::regclass,
       'public.signal_targets'::regclass, 'public.signal_lifecycle'::regclass)),
    'functions', (select jsonb_agg(jsonb_build_object('definition', pg_get_functiondef(p.oid),
      'body', p.prosrc, 'acl', p.proacl) order by p.oid)
      from pg_proc p join pg_namespace n on n.oid = p.pronamespace
      where n.nspname = 'public' and p.proname = 'curren_ingest_publication'),
    'policies', (select coalesce(jsonb_agg(to_jsonb(p) order by tablename, policyname), '[]'::jsonb)
      from pg_policies p where schemaname = 'public'),
    'grants', (select coalesce(jsonb_agg(to_jsonb(g) order by table_name, column_name, grantee, privilege_type), '[]'::jsonb)
      from information_schema.column_privileges g where table_schema = 'public'),
    'views', (select coalesce(jsonb_agg(to_jsonb(v) order by viewname), '[]'::jsonb)
      from pg_views v where schemaname = 'public')
  ),
  'signals', (select coalesce(jsonb_agg(to_jsonb(s)::text order by id), '[]'::jsonb) from public.signals s),
  'children', jsonb_build_object(
    'lifecycle_events', (select coalesce(jsonb_agg(to_jsonb(e)::text order by id), '[]'::jsonb) from public.lifecycle_events e),
    'signal_targets', (select coalesce(jsonb_agg(to_jsonb(e)::text order by to_jsonb(e)::text), '[]'::jsonb) from public.signal_targets e),
    'signal_lifecycle', (select coalesce(jsonb_agg(to_jsonb(e)::text order by to_jsonb(e)::text), '[]'::jsonb) from public.signal_lifecycle e)
  ),
  'counts', jsonb_build_object('signals', (select count(*) from public.signals),
    'lifecycle_events', (select count(*) from public.lifecycle_events),
    'signal_targets', (select count(*) from public.signal_targets),
    'signal_lifecycle', (select count(*) from public.signal_lifecycle))
);
