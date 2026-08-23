# Curren Public API Contract

This document defines the first external contract consumed by the public CLI, MCP server, and Omarchy plugin.

## Boundary

The Curren API is a read-only publication boundary. It is not a façade over the private production database and it must not expose operator, source-ingestion, model-feature, trade-intent, venue-order, account, or execution state.

The private runtime publishes a sanitized read model outward. Public clients only consume that read model.

## Authentication

Authenticated requests use:

```text
Authorization: Bearer crn_...
```

Tokens belong in HTTP headers, never query strings. Entitlement is enforced server-side.

A response may omit exact trade levels when the caller is not entitled to them. Clients must not reconstruct or infer omitted fields.

## Endpoints

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
      "current_r": 1.2,
      "access": "delayed"
    }
  ],
  "recent_results": [],
  "as_of": "2026-08-23T12:00:00Z"
}
```

The public endpoint must not expose exchange credentials, execution state, raw source identifiers, or internal model data.

### `GET /v1/signals`

Query parameters:

- `status=active`
- `symbol=<SYMBOL>` optional
- `limit=1..100`

Response:

```json
{
  "items": [],
  "next_cursor": null
}
```

### `GET /v1/signals/{signal_id}`

Returns one public signal projection.

Exact levels are optional by entitlement:

```json
{
  "id": "crn_sig_01",
  "symbol": "HYPEUSDT",
  "side": "long",
  "status": "active",
  "published_at": "2026-08-23T11:30:00Z",
  "available_at": "2026-08-23T11:30:01Z",
  "entry": 42.18,
  "stop": 40.90,
  "targets": [
    {"price": 43.45, "status": "hit", "hit_at": "2026-08-23T11:58:00Z"}
  ],
  "mark": 43.52,
  "current_r": 1.04,
  "peak_r": 1.20,
  "access": "realtime"
}
```

For lower entitlements, `entry`, `stop`, `targets`, or current lifecycle fields may be absent/null.

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

### `GET /v1/results`

Returns recent closed public signal projections using the same `Signal` schema.

### `GET /v1/track-record`

```json
{
  "sample_size": 100,
  "wins": 58,
  "losses": 42,
  "breakeven": 0,
  "win_rate": 0.58,
  "net_r": 24.1,
  "average_r": 0.241,
  "as_of": "2026-08-23T12:00:00Z",
  "methodology": "server-published closed signal outcomes"
}
```

Track-record methodology must be explicit. The API must not manufacture a statistic when the necessary closed records do not exist.

### `GET /v1/signals/{signal_id}/verification`

```json
{
  "signal_id": "crn_sig_01",
  "published_at": "2026-08-23T11:30:00Z",
  "content_hash": "sha256:...",
  "verified": true,
  "immutable": true,
  "record_version": "signal-public.v1"
}
```

Verification is intended to prove what Curren published and when. It is not a profitability guarantee.

## Publication clocks

The public publication layer should keep distinct clocks where applicable:

- `generated_at`: private runtime generated the accepted signal.
- `published_at`: immutable public publication record was created.
- `available_at`: the current entitlement was allowed to access this representation.

Delayed tiers must be implemented by server-side availability policy, not by asking clients to hide already-delivered realtime data.

## Versioning

The first public record version is `signal-public.v1`.

Breaking semantic changes require a new record/API version. Adding optional fields that older clients ignore is non-breaking.
