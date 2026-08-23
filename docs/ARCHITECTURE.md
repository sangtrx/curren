# Curren Public Platform Architecture

## Purpose

This repository is Curren's public distribution layer. It is intentionally separate from the private signal/trading runtime. The stable seam is a strict cumulative `PublicationBatch`.

## Components

```text
private runtime
    |
    | sanitized cumulative PublicationBatch
    v
PublicationClient
    |
    | HTTPS + ingestion bearer token
    v
FastAPI publication boundary
    |
    +--> strict schema validation
    +--> future-clock guard
    +--> server-side public delay
    +--> per-signal replay watermark
    +--> process-local rate limit
    |
    v
SQLite/WAL read model
    |
    +--> immutable initial publication
    +--> append-only lifecycle
    +--> immutable terminal outcome/result projection
    |
    +--> anonymous/public API
    +--> Premium API
    +--> Agent API
              |
              +--> CLI
              +--> MCP
              +--> Omarchy
```

### `curren.models`

Public response models are forward-compatible (`extra=ignore`). Publication models fail closed (`extra=forbid`). Public signal status is `pending | active | closed | expired`; target status is `pending | hit`. Runtime-specific lifecycle states must be normalized by the private projector.

### `curren.publisher`

Thin outbound client for private integrations. It sends validated `PublicationBatch` objects and imports no private runtime/SQL code.

### `curren.store`

Owns the SQLite/WAL read model.

Per signal it stores source ownership and the latest accepted `source_generated_at`. Equal/older snapshots cannot roll state backward. The initial trade plan and first public-availability schedule are fixed. Lifecycle events are append-only. The first terminal snapshot creates an immutable outcome record and freezes terminal result projection state. Public recent results are proof-backed by outcome records.

### `curren.rate_limit`

Dependency-free, bounded-memory, single-process fixed-window limiter. Public, authenticated, and ingestion scopes use separate buckets. Valid token identities are hashed before becoming bucket keys.

### `curren.server`

Owns HTTP authentication, entitlement, strict ingestion policy, clock-skew validation, delay enforcement, rate limiting, trusted proxy handling, and endpoint composition.

Forwarded client IPs are ignored by default. If the direct peer is allowlisted in `CURREN_TRUSTED_PROXY_IPS`, the application walks `X-Forwarded-For` from right to left, skips only trusted proxy hops, and uses the first untrusted hop as the client identity.

The unauthenticated `/healthz` endpoint is deliberately minimal and never exposes internal signal counts.

### `curren.client`

Read-only async HTTP client used by CLI and MCP. Restricted fields remain optional and are never reconstructed. HTTP `429` surfaces the server retry hint.

### `curren.mcp_server`

Read-only MCP v2 adapter with six tools. It delegates all data authority and entitlement to the HTTP API. No execution tool exists. Bundled Streamable HTTP is loopback-only until a separately authenticated remote MCP resource-server/gateway exists.

### Omarchy

The root `manifest.json` exposes one `bar-widget`. QML calls only anonymous `/v1/public/summary`, stores no credential, retains last valid data on failure, and visibly distinguishes `Live`, `Stale`, and `Offline` states.

## Data ownership

### Private runtime owns

- signal generation/filtering;
- strategy/research/source context;
- AI/model authority;
- market-data feature computation;
- lifecycle authority;
- execution/risk/account state;
- operator controls.

### Public platform owns

- sanitized publication contract;
- public delay/access policy;
- read API key/tier mapping;
- rate-limit policy;
- initial publication record/hash;
- public lifecycle projection;
- terminal outcome/result proof;
- public track record;
- client protocols/integrations.

## Failure isolation

A public API outage must not stop signal generation, lifecycle tracking, or execution in the private runtime. The private publisher can retry a committed snapshot safely; equal/older `generated_at` values are ignored as stale.

Public consumers fail independently:

- CLI/MCP errors never write trading state;
- Omarchy retains last valid public data and shows stale/offline status;
- malformed/unknown credentials fail closed;
- rate-limit exhaustion returns `429` without touching the read model.

## Security/correctness invariants

1. Public clients never receive private database credentials.
2. No public write path exists back into the trading runtime.
3. Ingestion credential is distinct from read credentials.
4. Publication input rejects unknown/private fields.
5. Active public data is delayed server-side.
6. Health does not reveal hidden signal activity.
7. Initial plan and first public-availability schedule cannot be rewritten.
8. Stale/future-poisoning snapshots cannot corrupt replay ordering.
9. Lifecycle event identities cannot be rewritten.
10. Terminal outcome and terminal result projection cannot be rewritten.
11. Public result lists/track record use proof-backed outcome rows.
12. No execution endpoint/tool exists in this repository.

## Scale boundary

SQLite/WAL is deliberate for the first public service: publication writes are low-frequency and reads are small indexed lookups. The built-in limiter is deliberately process-local.

When traffic requires multiple workers/replicas, put a trusted reverse proxy/API gateway in front for TLS, global rate limits, network ACLs, and abuse controls. Move the read model to PostgreSQL only when observed write contention/concurrency justifies it. Neither scale migration should require changing the public API or `PublicationBatch` semantics.
