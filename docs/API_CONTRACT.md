# Curren API Contract

This document defines the v1 external read contract and the strict private-to-public publication contract implemented by Curren v0.3.

## Boundary

The Curren API is a publication/read-model boundary, not a façade over the private production trading database.

The private runtime sends a sanitized projection outward. The public service persists only fields required by public/Premium/Agent clients. It has no order-placement, exchange-account, trading-control, or execution endpoints.

Publication payloads must never contain raw source messages, private source identifiers, model features/artifacts, trade intents, exchange credentials, account state, or operator secrets. Unknown publication fields are rejected with HTTP `422` rather than silently ignored.

## Authentication and rate limits

Read requests may use:

```text
Authorization: Bearer crn_...
```

No header means `public` access. Configured API keys map to `premium` or `agent`. Unknown keys fail with HTTP `401`.

The ingestion endpoint uses a separate `CURREN_INGEST_TOKEN`; if unset, ingestion is disabled with HTTP `503`.

The application-level limiter defaults to a 60-second window:

- public/anonymous: 60 requests per peer IP
- Premium/Agent: 300 requests per valid API key
- ingestion: 120 requests per valid ingestion credential

Responses include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset-After`; `429` responses include `Retry-After`.

Invalid/unknown read tokens are still bucketed by peer IP, so rotating bogus tokens does not bypass the anonymous quota. The built-in limiter is process-local; multi-worker/replica deployments also need a global ingress limit.

## Read endpoints

### `GET /healthz`

Health checks are not rate limited.

```json
{
  "status": "ok",
  "signals": 12,
  "ingestion_enabled": true
}
```

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

`active_count` counts only active signals already visible under the public delay policy. It does not leak hidden realtime signal count.

### `GET /v1/signals`

Query parameters:

- `status`: `pending | active | closed | expired`, default `active`
- `symbol=<SYMBOL>` optional
- `limit=1..100`

Public pending/active records are visible only after `public_available_at` and omit entry, stop, target prices, and lifecycle prices. Premium/Agent records are realtime and include those fields when the publisher supplied them.

Terminal records are full public proof.

### `GET /v1/signals/{signal_id}`

Returns one visible signal projection.

### `GET /v1/signals/{signal_id}/lifecycle`

Returns stored lifecycle events in chronological order. Public active lifecycle is delayed and omits event prices. Premium/Agent sees stored lifecycle realtime. Terminal signals expose stored lifecycle publicly.

Lifecycle event identity is `(signal_id, event_type, event_at)`. A later publication that reuses that identity with different `price` or `r_multiple` is rejected with HTTP `409`.

### `GET /v1/results`

Returns recent `closed`/`expired` projections using the same `Signal` schema.

### `GET /v1/track-record`

Track record is derived from immutable terminal outcome records with non-null `realized_r`, not mutable signal rows.

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

After closure/expiry, the same response also carries the immutable outcome hash and verification fields.

These hashes verify integrity inside Curren's publication store. They are not an independent timestamp authority, blockchain proof, exchange attestation, profitability guarantee, or third-party notary.

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

Public signal status is a closed set:

```text
pending | active | closed | expired
```

The private projector must map internal states such as `closed_win`, `closed_loss`, or other runtime-specific terminal values to this contract before sending them.

All timestamps must be timezone-aware. `generated_at` must not predate the latest projected signal/lifecycle/target-hit state. Terminal records require `closed_at`; `closed` records also require `realized_r`. Non-terminal records cannot carry terminal outcome fields.

Prices must be positive/finite; R values must be finite.

## Replay ordering

Each signal row stores:

- publication `source`
- latest accepted `source_generated_at`

Once a signal has an accepted projection, an equal/older `generated_at` for that same signal is treated as a stale replay and counted as `stale_ignored`. It cannot roll mark/R/status/lifecycle state backward.

A signal id cannot change publication source after the source has been established.

Publishers should send cumulative state projections and generate a fresh `generated_at` for each new state snapshot. Retrying the exact same committed batch is safe; it will be ignored as stale.

## Immutable initial publication

On first ingestion Curren canonicalizes and hashes:

- signal id
- symbol
- side
- `published_at`
- entry price
- stop price
- ordered target prices
- record version

A newer conflicting projection returns HTTP `409`.

Mutable while live:

- public availability time, subject to the server minimum delay
- target hit status/timestamps, with prices fixed
- mark/current R/peak R
- append-only lifecycle events

## Immutable terminal outcome

When a signal first becomes `closed` or `expired`, Curren records a separate canonical outcome hash over:

- signal id
- terminal status
- `realized_r`
- `closed_at`
- `exit_reason`
- outcome record version

After that, the signal cannot return to a live state and those terminal outcome fields cannot be rewritten under the same signal id. Conflicts return HTTP `409` atomically.

Current versions:

```text
signal-publication.v1
signal-outcome.v1
```

## Clock meanings

- `generated_at`: when the private projector produced the outgoing batch; also the per-signal replay watermark.
- `published_at`: immutable signal-publication time supplied by the private runtime.
- `recorded_at`: when the public read model first stored an immutable record.
- `public_available_at`: when a live signal becomes public/delayed data.
- `available_at`: representation availability for the current caller.
- `closed_at`: terminal outcome time.

The server enforces `CURREN_PUBLIC_DELAY_SECONDS` as a minimum before response serialization.
