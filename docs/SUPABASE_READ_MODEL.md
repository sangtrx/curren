# Curren Supabase landing read model

Status: deployed as a bounded landing-page replica with the v2 publication bridge. The source in this repository is ahead of that deployment (see "Write path"). Private runtime publication remains disabled until the production publisher is explicitly activated and verified.

## Scope

This Supabase project is a narrow public read replica for `curren.tech`. It is not the canonical Curren public API, proof store, Premium/Agent entitlement service, or private trading datastore.

Canonical ownership remains:

```text
private signal runtime  -> private signal/lifecycle/outcome authority
curren           -> sanitized PublicationBatch contract and public distribution policy
Supabase         -> landing-only sanitized replica
curren-landing-page -> anonymous presentation consumer
```

The landing page must never connect directly to the private runtime database.

## Data flow

```text
private signal runtime standalone publication worker
  -> sanitized cumulative PublicationBatch
  -> POST https://gxvvsefvvpbahevhfgns.supabase.co/functions/v1/curren-api/internal/v1/publications
  -> Supabase signals replica
  -> security-invoker public views
  -> curren-landing-page server component
```

The publisher remains failure-isolated from signal generation, lifecycle processing, delivery, and trading. Its existing at-least-once checkpoint semantics remain authoritative.

## Public visibility contract

The landing replica follows the same public-tier boundary as the canonical Curren read model:

- active signals are not public before `published_at + 1800 seconds` unless a later explicit `public_available_at` is supplied;
- the first stored public-availability schedule is preserved on later snapshots;
- active public rows do not expose entry, stop, targets, lifecycle details, private source identifiers, or raw/private strategy data;
- public live rows may expose symbol, side, status, timestamps, mark, current R, and peak R;
- terminal `closed` results may expose realized R, close time, and normalized exit reason;
- stale publisher state must not be labelled live.

The replica views still withhold terminal entry, stop and targets, although the canonical API reveals stored levels once a signal is terminal. Exposing them here, an explicit exit price, a peak-observation time, and any outcome-correction policy are open decisions on `internal tracking`. Field meanings follow `docs/API_CONTRACT.md` ("Result semantics").

## Write path

The Edge Function validates the same strict `PublicationBatch` shape as the canonical API: unknown fields at any level, zone-less timestamps, duplicate signal ids, invalid targets or lifecycle events, and a `generated_at` that predates the projected state or runs ahead of the server clock are rejected with `422`. It then applies the whole batch with one call to `public.curren_ingest_publication` (migration `supabase/migrations/20260927090000_publication_ingest_parity.sql`), which runs in a single transaction with the canonical read-model rules:

- equal/older `generated_at` snapshots are stale-ignored per signal;
- source ownership, symbol, side, `published_at`, entry, stop and target prices are fixed after first publication;
- a terminal signal cannot return to a live state;
- a terminal outcome and its projection (status, realized R, close time, exit reason, terminal mark, peak R, target hit state) cannot be rewritten; `current_r` is live-only and stored as `null` once terminal;
- lifecycle events are append-only in `public.lifecycle_events`, identified by `(signal_id, event_type, event_at)`;
- any conflict returns `409` with the canonical `<reason> for <signal_id>` detail and leaves the replica unchanged.

Rows replicated before this migration are treated as recorded outcomes: they stay locked, and their targets are stored on the first accepted replay. Timestamps are stored at millisecond precision, the precision those rows already use. The empty `public.signal_targets` and `public.signal_lifecycle` tables from the first migration are no longer written by anything and were left in place.

## Freshness behavior

`public_live_signals` only returns delayed active rows whose `source_generated_at` is within 90 seconds of the database clock.

`public_feed_status` reports:

- `idle`: no delayed active rows currently exist;
- `fresh`: delayed active rows exist and the newest source snapshot is at most 90 seconds old;
- `stale`: delayed active rows exist but the newest source snapshot is older than 90 seconds.

The landing consumer should use the status view for disclosure. A stalled publisher therefore cannot leave an old active signal displayed as live.

Terminal results remain available independently of the active-feed freshness window because they are historical outcomes, not claims about current runtime liveness.

## Database access boundary

Current production migrations:

- `20260905111608 create_curren_public_read_model`
- `20260907202242 harden_curren_public_read_model_v2`

The three base tables have RLS enabled. Anonymous clients have no INSERT/UPDATE/DELETE privileges. Anonymous access is restricted to the landing read views and safe column-level reads needed by their security-invoker definitions. In particular, anonymous clients cannot read `signals.entry`, `signals.stop`, `signals.source`, `signal_targets`, or `signal_lifecycle`.

The ingest migration keeps its new objects private: `public.signals.targets` and `public.lifecycle_events` have no anonymous or signed-in grants (RLS on, no policies), and only `service_role` may execute `public.curren_ingest_publication`. The migration refuses to run if `anon` or `authenticated` holds a table-level `SELECT` on `public.signals`, because the new column would then become readable.

Supabase Security Advisor must remain clean after schema/RLS changes; the INFO-level "RLS enabled, no policy" notice for `public.lifecycle_events` is intended (deny-all to API roles). The two earlier production migrations are not in source control.

## Edge Function

Source authority: `supabase/functions/curren-api/index.ts`.

The function is deployed with platform JWT verification disabled because it performs its own exact Bearer-token check against server-side secret material before any write. This avoids treating an ordinary public project JWT as publisher authorization. Database writes use server-side secret credentials only; no service/secret key is exposed to the landing frontend.

Public health check:

```text
GET /functions/v1/curren-api/healthz
```

Publisher endpoint:

```text
POST /functions/v1/curren-api/internal/v1/publications
Authorization: Bearer <publisher secret>
```

Do not commit or print the publisher secret.

Deployment order. Every step is a production operation that needs explicit operator authorization:

1. Capture the live `public` schema into `supabase/migrations/` (for example with `supabase db pull`, which also records the two earlier remote-only versions). Check that `public.signals` still has the columns and privileges `tests/supabase_bridge/baseline.sql` assumes, update the baseline if it differs, and rerun the parity check.
2. Apply the ingest migration.
3. Deploy the function.
4. Run one bounded publisher cycle and verify it, as in the activation contract below.

A function deployed without the migration fails closed with `500` and changes nothing, and the publisher replays from its unchanged checkpoint.

Local verification against Postgres, PostgREST and the real function (needs Docker):

```bash
CURREN_SUPABASE_BRIDGE_PARITY=1 pytest -q tests/test_supabase_bridge_parity.py
```

It sends the same batches to the canonical FastAPI read model and to this bridge. For every batch it requires the same status code, the same counts when accepted and the same detail on a `409`, and it compares the final stored state of one signal. It also covers the lock on pre-migration rows, the privacy of the new objects and the migration's refusal guard. `tests/supabase_bridge/baseline.sql` stands in for the unversioned earlier migrations.

## private producer activation contract

The private standalone publisher can target this bridge without changing its publication protocol:

```dotenv
CURREN_PUBLICATION_API_URL=https://gxvvsefvvpbahevhfgns.supabase.co/functions/v1/curren-api
CURREN_PUBLICATION_INGEST_TOKEN=<publisher secret>
CURREN_PUBLICATION_ENABLED=true
```

Activation is a production operation. Before enabling it:

1. verify the current `private signal runtime` publication projector and this Edge Function source at their exact accepted SHAs;
2. configure the URL/token without exposing the secret;
3. run one bounded publication cycle and require an accepted response;
4. confirm Supabase receives sanitized rows and the public views enforce delay/redaction/freshness;
5. only then run the standalone publisher continuously.

A network, authentication, contract, or database failure must leave the private producer checkpoint unchanged so the next cycle can replay safely.

## Current activation state

At the 2026-09-08 hardening checkpoint the Supabase schema/RLS/views and Edge Function v2 were deployed with zero replicated rows.

At the 2026-09-18 activation checkpoint a bounded one-shot publication cycle from the private publisher was accepted and verified in the replica (sanitized rows only; public delay/RLS policy intact). Continuous publication was **not** enabled. The replica therefore holds a point-in-time backfill, not evidence of a live feed; active rows age out of `public_live_signals` through the freshness window rather than being presented as live.

An earlier unbounded backfill attempt exceeded the private publisher's read timeout because the v2 Edge Function performed sequential, non-transactional per-signal read/upsert round trips. The current source applies each batch in one transactional database call; it is not deployed yet.
