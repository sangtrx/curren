# Curren API Contract

This document defines the v1 external read contract and the strict private-to-public publication contract implemented by Curren v0.4.

## Boundary

The Curren API is a publication/read-model boundary, not a facade over the private production trading database.

The private runtime sends a sanitized projection outward. The public service persists only fields required by Public/Premium/Agent clients. It has no order-placement, exchange-account, trading-control, or execution endpoint.

Publication payloads must never contain raw source messages, private source identifiers, model features/artifacts, trade intents, exchange credentials, account state, or operator secrets. Unknown publication fields are rejected with HTTP `422`.

## Authentication and rate limits

Read requests may use:

```text
Authorization: Bearer crn_...
```

No header means `public`. Configured keys map to `premium` or `agent`. Unknown keys fail with HTTP `401`.

Private ingestion uses a separate `CURREN_INGEST_TOKEN`; if unset, ingestion is disabled with HTTP `503`.

Default application limiter window is 60 seconds:

- public/anonymous: 60 requests per resolved client identity;
- Premium/Agent: 300 requests per valid API key;
- ingestion: 120 requests per valid ingestion credential.

Responses include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset-After`; `429` also includes `Retry-After`.

Invalid/unknown read tokens stay in the anonymous client bucket. Forwarded client IP is considered only when the direct peer is allowlisted by `CURREN_TRUSTED_PROXY_IPS`; the server walks the forwarding chain from right to left and skips only trusted proxy hops. Multi-worker/replica deployments still require a global ingress quota.

## Read endpoints

### `GET /healthz`

Health is intentionally minimal and not application-rate-limited:

```json
{
  "status": "ok"
}
```

It does not expose database row counts, ingestion state, hidden signal activity, credentials, or operator metadata.

### `GET /v1/public/summary`

Anonymous proof surface used by Omarchy.

```json
{
  "active_count": 2,
  "delayed_signals": [],
  "recent_results": [],
  "as_of": "2026-08-23T12:00:00Z"
}
```

`active_count` counts only active signals already visible under the public delay policy. It does not leak hidden realtime signal count. `recent_results` contains only terminal rows backed by immutable outcome records.

### `GET /v1/signals`

Query parameters:

- `status`: `pending | active | closed | expired`, default `active`;
- `symbol=<SYMBOL>` optional;
- `limit=1..100`.

Public pending/active rows appear only after their established `public_available_at` and omit entry, stop, target prices, and active lifecycle prices. Premium/Agent rows are realtime and include stored exact levels.

### `GET /v1/signals/{signal_id}`

Returns one visible signal projection. Signal IDs accept only letters, digits, `.`, `_`, `:`, and `-`, up to 128 characters.

### `GET /v1/signals/{signal_id}/lifecycle`

Returns lifecycle events chronologically. Public active lifecycle is delayed and omits event prices. Premium/Agent sees stored lifecycle realtime. Terminal signals expose stored lifecycle publicly.

Lifecycle identity is `(signal_id, event_type, event_at)`. Reusing an identity with different `price` or `r_multiple` returns HTTP `409`.

### `GET /v1/results`

Returns recent terminal projections **only when an immutable outcome record exists**. Legacy/migrated terminal signal rows without an outcome proof are deliberately excluded rather than presented as verified results.

### `GET /v1/track-record`

Track record is derived only from immutable `closed` outcome records with non-null `realized_r`, not mutable signal rows.

```json
{
  "sample_size": 100,
  "wins": 58,
  "losses": 39,
  "breakeven": 3,
  "win_rate": 0.58,
  "net_r": 24.1,
  "average_r": 0.241,
  "as_of": "2026-08-23T12:00:00Z",
  "methodology": "Immutable terminal outcome records with a recorded realized R multiple."
}
```

### `GET /v1/signals/{signal_id}/verification`

Active example:

```json
{
  "signal_id": "crn_sig_01",
  "published_at": "2026-08-23T11:30:00Z",
  "content_hash": "sha256:...",
  "verified": true,
  "immutable": true,
  "record_version": "signal-publication.v1",
  "recorded_at": "2026-08-23T11:30:01Z",
  "outcome_content_hash": null,
  "outcome_verified": null,
  "outcome_record_version": null,
  "outcome_recorded_at": null
}
```

After closure/expiry the response also carries outcome integrity fields.

These hashes verify Curren-owned stored records. They are not an independent timestamp authority, blockchain proof, exchange attestation, profitability guarantee, or third-party notary.

## Publication endpoint

### `POST /internal/v1/publications`

Requires:

```text
Authorization: Bearer <CURREN_INGEST_TOKEN>
```

Maximum 500 signals per batch. The schema is strict (`extra=forbid`) at every publication nesting level.

```json
{
  "source": "curren-runtime",
  "generated_at": "2026-08-23T12:01:01Z",
  "signals": [
    {
      "id": "crn_sig_01",
      "symbol": "HYPEUSDT",
      "side": "long",
      "status": "active",
      "published_at": "2026-08-23T12:00:00Z",
      "public_available_at": "2026-08-23T12:30:00Z",
      "entry": 42.18,
      "stop": 40.90,
      "targets": [
        {"price": 43.45, "status": "pending"},
        {"price": 44.72, "status": "pending"}
      ],
      "mark": 42.60,
      "current_r": 0.33,
      "peak_r": 0.40,
      "lifecycle": [
        {
          "event_type": "entry_hit",
          "event_at": "2026-08-23T12:01:00Z",
          "price": 42.18,
          "r_multiple": 0.0
        }
      ]
    }
  ]
}
```

Response:

```json
{
  "accepted": 1,
  "inserted": 1,
  "updated": 0,
  "stale_ignored": 0,
  "lifecycle_events_inserted": 1,
  "outcome_records_inserted": 0
}
```

## Publication validation

Signal status is:

```text
pending | active | closed | expired
```

The private projector must normalize runtime-specific statuses before publication. Current Woodsbot terminal variants such as `closed_win`, `closed_loss`, `closed_be`, `closed_partial_win`, and `manual_close` map to public `closed`; `expired` remains `expired`.

Target status is:

```text
pending | hit
```

A `hit` target requires `hit_at`. A `pending` target cannot contain `hit_at`.

All timestamps must be timezone-aware. `generated_at` must not predate any state represented by the batch and must not exceed server time by more than `CURREN_MAX_CLOCK_SKEW_SECONDS` (default 300 seconds). This prevents a bad future timestamp from poisoning the replay watermark.

Terminal rows require `closed_at`; `closed` also requires `realized_r`. Non-terminal rows cannot carry terminal outcome fields. Prices must be positive/finite and R values finite.

## Replay ordering

Each signal stores its publication `source` and latest accepted `source_generated_at`.

An equal/older `generated_at` for the same signal is `stale_ignored`; it cannot roll mark/R/status/lifecycle state backward. A signal id cannot switch source after ownership is established.

Publishers should send cumulative state projections and generate a fresh `generated_at` only for a new committed state snapshot.

## Immutable initial publication and availability schedule

On first ingestion Curren canonicalizes and hashes:

- signal id;
- symbol;
- side;
- `published_at`;
- entry;
- stop;
- ordered target prices;
- record version.

A conflicting newer projection returns HTTP `409`.

The first server-enforced `public_available_at` is also retained for that signal id. Later snapshots cannot accelerate or hide a signal by changing that clock.

While live, mutable projection fields are target hit status/timestamp (target prices fixed), mark/current R/peak R, and new append-only lifecycle events.

## Immutable terminal outcome and result projection

When a signal first becomes `closed` or `expired`, Curren records a separate canonical outcome hash over:

- signal id;
- terminal status;
- `realized_r`;
- `closed_at`;
- `exit_reason`;
- outcome record version.

That first terminal snapshot also freezes the public terminal result projection (target hit state, mark/current R/peak R, outcome fields). A newer cumulative snapshot may add previously unseen lifecycle events but cannot rewrite already-published terminal result context. Conflicts return HTTP `409` atomically.

Current record versions:

```text
signal-publication.v1
signal-outcome.v1
```

## Clock meanings

- `generated_at`: projector snapshot time and per-signal replay watermark;
- `published_at`: immutable signal publication clock from the private runtime;
- `recorded_at`: public read-model persistence clock for an immutable record;
- `public_available_at`: first established public/delayed availability for a live signal;
- `available_at`: representation availability for the current caller;
- `closed_at`: terminal outcome time.

The server enforces `CURREN_PUBLIC_DELAY_SECONDS` as a minimum before public live visibility.
