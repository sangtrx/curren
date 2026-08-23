# Curren Public Platform Architecture

## Purpose

This repository is the public distribution layer for Curren intelligence. It is intentionally separate from the private signal/trading runtime.

The public platform must remain useful even if the private runtime implementation changes. The stable seam is `PublicationBatch`.

## Components

```text
private runtime
    |
    | sanitized PublicationBatch
    v
PublicationClient
    |
    | Bearer-authenticated HTTPS
    v
FastAPI ingestion endpoint
    |
    v
SQLite/WAL read model
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

Owns the external contracts. Clients and publishers share these models so shape drift is caught before data reaches storage.

### `curren.publisher`

A thin client for the private integration. It only knows how to send sanitized `PublicationBatch` objects. It contains no SQL or private-runtime imports.

### `curren.store`

Owns the public read model. It uses one SQLite database with WAL enabled.

The initial trade plan is insert-once/immutable at the semantic level. Later updates may change lifecycle/result projection fields but cannot rewrite the original symbol, side, publication timestamp, entry, stop, or target prices.

Lifecycle events are append-only and idempotent.

### `curren.server`

Owns HTTP auth, entitlement selection, validation, response policy, and endpoint composition.

The public tier receives delayed active context without exact levels. Premium/Agent receives realtime stored context. Terminal results become full public proof.

### `curren.client`

Read-only async HTTP client used by CLI and MCP. Restricted fields are modeled as optional and are never reconstructed.

### `curren.mcp_server`

Read-only MCP v2 adapter. It exposes six compact tools and delegates all authority to the HTTP API.

It has no trading/execution tool and no private data connector.

### Omarchy

The root `manifest.json` exposes one `bar-widget`. QML calls only the anonymous `/v1/public/summary` endpoint and contains no API/exchange credentials.

## Data ownership

### Private runtime owns

- signal generation and filtering
- strategy/source context
- AI guard/model authority
- market-data feature computation
- lifecycle authority
- execution/risk/account state
- operator controls

### Public platform owns

- sanitized signal projection
- public availability policy
- public API keys/tier mapping
- immutable publication snapshot/hash
- public lifecycle projection
- public track-record projection
- client protocols and integrations

## Failure isolation

A public API outage must not stop signal generation, lifecycle tracking, or execution in the private runtime.

A private publisher should retry failed publication later. The endpoint is idempotent, so replaying recent sanitized state is safe.

Public consumers can fail independently:

- CLI/MCP API errors do not write state.
- Omarchy retains its last valid public response in memory and displays stale/offline state.
- Unknown or malformed credentials fail closed.

## Security invariants

1. Public clients never receive private database credentials.
2. The public service has no write path back into the trading runtime.
3. Ingestion uses a credential distinct from user API keys.
4. Active public data is delayed before serialization.
5. Omitted entry/SL/TP values are an entitlement decision, not missing data for clients to infer.
6. Immutable initial publication fields cannot be rewritten under the same signal id.
7. No execution endpoints exist in this repository.

## Scale boundary

SQLite/WAL is deliberate for the first public service: writes are low-frequency sanitized publications and reads are small indexed lookups.

Move the read model to PostgreSQL only when observed concurrency/write contention justifies it. The API and `PublicationBatch` contracts should not need to change for that migration.

Rate limiting, TLS, network ACLs, and horizontal ingress controls belong at the reverse proxy/load balancer. Do not add distributed infrastructure preemptively.
