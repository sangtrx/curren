# Curren API Contract

This document defines the v1 external read contract and the private-to-public publication contract consumed by the API server in this repository.

## Boundary

The Curren API is a publication boundary, not a direct façade over the private production trading database.

The private runtime sends a sanitized projection outward. The public service persists only fields required by Curren clients. It has no order-placement, exchange-account, trading-control, or execution endpoints.

The publication payload must never contain raw source messages, private source identifiers, model features/artifacts, trade intents, exchange credentials, account state, or operator secrets.

## Authentication and access

Read requests may use:

```text
Authorization: Bearer crn_...
```

No header means `public` access. Configured API keys map to `premium` or `agent` server-side. Unknown keys fail with HTTP `401`.

The private ingestion endpoint uses a separate bearer token from `CURREN_INGEST_TOKEN`. If no ingestion token is configured, ingestion is disabled with HTTP `503`.

Credentials belong in headers, never query strings.

## Read endpoints

### `GET /healthz`

```json
{
  "status": "ok",
  "signals": 12,
  "ingestion_enabled": true
}
```

No secret, database path, or operator metadata is returned.

### `GET /v1/public/summary`

Anonymous/public proof surface used by Omarchy.

```json
{
  "active_count": 2,
  "delayed_signals": [
    {
      "id": "crn_sig_01",
      "symbol": "HYPEUSDT",
      "side": "long",
      "status": "active",
      "published_at": "2026-08-23T11:30:00Z",
      "available_at": "2026-08-23T12:00:00Z",
      "entry": null,
      "stop": null,
      "targets": [],
      "current_r": 1.2,
      "access": "public"
    }
  ],
  "recent_results": [],
  "as_of": "2026-08-23T12:00:00Z"
}
```

`active_count` counts only active signals already visible under the public delay policy. It does not leak realtime hidden-signal count.

### `GET /v1/signals`

Query parameters:

- `status=active` by default
- `symbol=<SYMBOL>` optional
- `limit=1..100`

Response:

```json
{
  "items": [],
  "next_cursor": null
}
```

Public active records are returned only after `public_available_at`. Active public records omit entry, stop, target prices, and lifecycle prices. Premium/Agent records are realtime and include those fields when the publisher supplied them.

Closed records are full public proof and may expose the original plan and realized outcome.

### `GET /v1/signals/{signal_id}`

Returns one visible signal projection.

Premium/Agent example:

```json
{
  "id": "crn_sig_01",
  "symbol": "HYPEUSDT",
  "side": "long",
  "status": "active",
  "published_at": "2026-08-23T11:30:00Z",
  "available_at": "2026-08-23T11:30:00Z",
  "entry": 42.18,
  "stop": 40.90,
  "targets": [
    {"price": 43.45, "status": "hit", "hit_at": "2026-08-23T11:58:00Z"}
  ],
  "mark": 43.52,
  "current_r": 1.04,
  "peak_r": 1.20,
  "access": "premium"
}
```

Clients must never infer omitted restricted levels.

### `GET /v1/signals/{signal_id}/lifecycle`

```json
{
  "items": [
    {
      "event_type": "entry_hit",
      "event_at": "2026-08-23T11:31:00Z",
      "price": 42.18,
      "r_multiple": 0.0
    }
  ]
}
```

Public active lifecycle events are delayed by the server and omit event prices. Premium/Agent sees the stored lifecycle in realtime. Closed signals expose their full stored lifecycle publicly.

### `GET /v1/results`

Returns recent terminal/closed signal projections using the same `Signal` schema.

### `GET /v1/track-record`

The current implementation derives the track record only from closed/terminal server-published signals with non-null `realized_r`.

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
  "methodology": "Closed server-published signals with a recorded realized R multiple."
}
```

The API does not manufacture statistics when no closed records exist.

### `GET /v1/signals/{signal_id}/verification`

```json
{
  "signal_id": "crn_sig_01",
  "published_at": "2026-08-23T11:30:00Z",
  "content_hash": "sha256:...",
  "verified": true,
  "immutable": true,
  "record_version": "signal-publication.v1",
  "recorded_at": "2026-08-23T11:30:01Z"
}
```

`verified=true` means the SHA-256 hash recomputed from the stored initial snapshot matches the hash recorded by this Curren publication service.

It is **not** proof from an independent timestamp authority, blockchain, exchange, or third-party notary. It does not guarantee profitability. The immutable record is designed so a future transparency log/notary can anchor the same hash without changing client semantics.

## Publication endpoint

### `POST /internal/v1/publications`

Requires:

```text
Authorization: Bearer <CURREN_INGEST_TOKEN>
```

Maximum 500 signals per batch.

```json
{
  "source": "curren-runtime",
  "generated_at": "2026-08-23T12:00:05Z",
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
      "realized_r": null,
      "closed_at": null,
      "exit_reason": null,
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
  "lifecycle_events_inserted": 1
}
```

Repeated publication of the same projection is idempotent. Lifecycle events are append-only under `(signal_id, event_type, event_at)` uniqueness.

## Immutable publication fields

On first ingestion, the server canonicalizes and hashes:

- signal id
- symbol
- side
- `published_at`
- entry price
- stop price
- ordered target prices
- record version

After the first accepted publication these fields cannot change for that signal id. A conflicting batch is rejected atomically with HTTP `409`.

Mutable projection fields include:

- status
- `public_available_at`
- target hit status/timestamps, as long as target prices are unchanged
- mark/current R/peak R
- realized R
- close timestamp/reason
- new lifecycle events

## Clocks

The contract distinguishes:

- `generated_at`: when the private integration produced this outgoing batch.
- `published_at`: the immutable signal-publication clock supplied by the source runtime.
- `recorded_at`: when the public read model first persisted the immutable snapshot.
- `public_available_at`: when an active record becomes public/delayed data.
- `available_at`: the time the current API representation is available to that caller.

Delays are enforced server-side before response serialization.

## Versioning

The current initial-publication record version is `signal-publication.v1`.

Breaking semantic changes require a new record/API version. Adding optional fields that older clients ignore is non-breaking.
