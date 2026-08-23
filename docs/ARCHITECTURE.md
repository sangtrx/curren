# Curren Public Platform Architecture

## Purpose

This repository is Curren's public distribution layer. It is intentionally separate from the private signal/trading runtime.

The stable seam is a strict `PublicationBatch`; the public platform must remain useful even if the private runtime implementation changes.

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
    +--> server-side public delay
    +--> per-signal replay watermark
    +--> application rate limit
    |
    v
SQLite/WAL read model
    |
    +--> immutable initial publication
    +--> append-only lifecycle
    +--> immutable terminal outcome
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

Public response models are forward-compatible (`extra=ignore`) so older clients tolerate optional response extensions.

Publication models are fail-closed (`extra=forbid`). Private/source/model/account/execution fields cannot silently cross the private/public boundary.

The publication status vocabulary is deliberately small: `pending`, `active`, `closed`, `expired`. Private runtime states must be normalized by the projector.

### `curren.publisher`

Thin outbound client for private integrations. It sends only validated `PublicationBatch` objects and contains no private SQL/runtime imports.

### `curren.store`

Owns the public SQLite/WAL read model.

Per signal it stores the publication source and latest accepted `source_generated_at`. Equal/older projections are stale and cannot roll state backward.

The initial trade plan is immutable. Lifecycle events are append-only; replaying an existing event identity with changed values conflicts. The first terminal state creates a second immutable outcome record used by track-record calculations.

### `curren.rate_limit`

Dependency-free, bounded-memory, single-process fixed-window limiter. It protects public, authenticated, and ingestion surfaces independently.

It intentionally does not trust forwarded client-IP headers. A trusted ingress/global limiter should enforce distributed limits when the API runs multiple workers or replicas.

### `curren.server`

Owns HTTP auth, entitlement, strict request policy, delay enforcement, rate limiting, and endpoint composition.

The public tier receives delayed active context without exact levels. Premium/Agent receives realtime stored context. Terminal results become full public proof.

### `curren.client`

Read-only async HTTP client used by CLI and MCP. Restricted fields are optional and never reconstructed. HTTP `429` is surfaced with the server's retry hint.

### `curren.mcp_server`

Read-only MCP v2 adapter with six compact tools. It delegates all data authority and entitlements to the HTTP API.

No execution tools exist. Streamable HTTP is restricted to loopback until a separately authenticated MCP resource-server boundary exists.

### Omarchy

The root `manifest.json` exposes one `bar-widget`. QML calls only anonymous `/v1/public/summary` and contains no API, ingestion, exchange, or execution credential.

## Data ownership

### Private runtime owns

- signal generation/filtering
- strategy/source context
- AI/model authority
- market-data feature computation
- lifecycle authority
- execution/risk/account state
- operator controls

### Public platform owns

- strict sanitized projection contract
- public delay/access policy
- read API keys/tier mapping
- rate-limit policy
- immutable initial publication/hash
- append-only public lifecycle projection
- immutable terminal outcome/hash
- public track record
- client protocols/integrations

## Failure isolation

A public API outage must not stop signal generation, lifecycle tracking, or execution in the private runtime.

A private publisher may retry a committed batch safely: the same/older `generated_at` is ignored as stale. Publishers should send cumulative state snapshots so a newer projection contains all lifecycle state required downstream.

Public consumers fail independently:

- CLI/MCP errors never write state.
- Omarchy retains the last valid public response in memory and shows stale/offline state.
- Unknown/malformed credentials fail closed.
- Rate-limit exhaustion returns `429` without touching the read model.

## Security/correctness invariants

1. Public clients never receive private database credentials.
2. The public service has no write path back into the trading runtime.
3. Ingestion uses a credential distinct from read API keys.
4. Publication input rejects unknown fields.
5. Active public data is delayed server-side.
6. Omitted entry/SL/TP values are entitlement decisions, not data clients should infer.
7. Initial publication fields are immutable under a signal id.
8. Terminal outcome fields are immutable under a signal id.
9. Stale projections cannot roll state backward.
10. Lifecycle event identities cannot be rewritten.
11. No execution endpoints/tools exist in this repository.

## Scale boundary

SQLite/WAL is deliberate for the first public service: publication writes are low-frequency and reads are small indexed lookups.

The built-in limiter is also deliberately process-local. When observed traffic requires multiple workers/replicas, put a trusted reverse proxy/API gateway in front for TLS, global rate limits, network ACLs, and abuse controls. Move the read model to PostgreSQL only when observed write contention/concurrency justifies it.

Neither scale migration should require changing the public API or `PublicationBatch` semantics.
