# Curren Supabase landing read model

Status: source-backed and deployed as a bounded landing-page replica. Private runtime publication remains disabled until the production publisher is explicitly activated and verified.

## Scope

This Supabase project is a narrow public read replica for `curren.tech`. It is not the canonical Curren public API, proof store, Premium/Agent entitlement service, or private trading datastore.

Canonical ownership remains:

```text
woodsbot-system  -> private signal/lifecycle/outcome authority
curren           -> sanitized PublicationBatch contract and public distribution policy
Supabase         -> landing-only sanitized replica
curren-landing-page -> anonymous presentation consumer
```

The landing page must never connect directly to the private runtime database.

## Data flow

```text
woodsbot-system standalone publication worker
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

The Edge Function validates the bounded publication shape, rejects unsupported top-level/signal fields, enforces normalized identifiers/statuses, rejects malformed/future timestamps, enforces source ownership, and ignores equal/older `generated_at` snapshots.

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

Supabase Security Advisor must remain clean after schema/RLS changes.

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

## Woodsbot activation contract

The private standalone publisher can target this bridge without changing its publication protocol:

```dotenv
CURREN_PUBLICATION_API_URL=https://gxvvsefvvpbahevhfgns.supabase.co/functions/v1/curren-api
CURREN_PUBLICATION_INGEST_TOKEN=<publisher secret>
CURREN_PUBLICATION_ENABLED=true
```

Activation is a production operation. Before enabling it:

1. verify the current `woodsbot-system` publication projector and this Edge Function source at their exact accepted SHAs;
2. configure the URL/token without exposing the secret;
3. run one bounded publication cycle and require an accepted response;
4. confirm Supabase receives sanitized rows and the public views enforce delay/redaction/freshness;
5. only then run the standalone publisher continuously.

A network, authentication, contract, or database failure must leave the Woodsbot checkpoint unchanged so the next cycle can replay safely.

## Current activation state

At the SAN-6 hardening checkpoint on 2026-09-08, the Supabase schema/RLS/views and Edge Function v2 are deployed, but the `signals` replica still contains zero rows. This is infrastructure readiness, not evidence that the production publication worker is enabled or that the landing page currently has a live feed.
