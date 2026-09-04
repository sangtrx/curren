# Curren Public Platform Status

Last reviewed: 2026-09-04

Current release line: **v0.4.0 (alpha)**.

This file is the concise source of truth for what this public repository does and does not currently provide.

## Canonical repository role

`sangtrx/curren` is the canonical **public developer/platform surface** for Curren. It owns the
read-only public API contract, Python client, CLI, MCP server, sanitized publication read model,
proof/track-record projections, and public integrations/plugins.

It is **not** the Curren public landing page. The canonical landing/marketing frontend for
`https://curren.tech/` is `sangtrx/curren-landing-page`.

It is also not the private signal generator (`woodsbot-system`), quantitative research authority
(`curren-research`), or private access/payment authority (`curren-access`).

## Implemented

### Public platform

- FastAPI read-only API.
- SQLite/WAL read model isolated from the private trading runtime.
- Public, Premium, and Agent read entitlements.
- Strict private-to-public `PublicationBatch` schema (`extra=forbid`).
- Server-enforced delayed public visibility for active signals.
- Per-signal source ownership and monotonic `generated_at` replay watermark.
- Maximum future publisher clock-skew guard.
- Immutable initial signal-plan record/hash.
- Append-only lifecycle events with conflict detection.
- Immutable terminal outcome plus frozen terminal result projection.
- Proof-backed `/v1/results` and track record.
- Bounded process-local rate limits for public, authenticated, and ingestion traffic.
- Trusted reverse-proxy chain handling for client-IP rate-limit identity.
- Minimal health endpoint with no hidden signal-count side channel.

### Clients/integrations

- Async Python API client.
- Terminal CLI.
- Read-only MCP v2 server with six tools.
- Omarchy Quattro bar widget/panel using anonymous delayed/public proof only.
- Private publication client (`curren-publish`).
- Dockerfile and Docker Compose deployment shape.

### Security boundaries

- No public trade execution endpoints/tools.
- No private production database credential in public clients.
- No raw signal-source messages or source identifiers in the publication contract.
- No strategy/research/model internals in this repository.
- No Premium/ingestion/exchange key in Omarchy QML.
- MCP Streamable HTTP is loopback-only until a separately authenticated remote MCP resource-server/gateway exists.
- GitHub Actions are intentionally not configured; verification is local/host-side.

## Not yet connected to production

The public platform is not itself the Curren signal generator. Production usefulness requires these external/private integrations:

1. **`woodsbot-system` publication projector**
   - read canonical signal/lifecycle/outcome state;
   - normalize private lifecycle statuses to the public vocabulary;
   - produce cumulative sanitized `PublicationBatch` snapshots;
   - publish one-way to `/internal/v1/publications`.
2. **Production deployment for `api.curren.tech`**
   - TLS/reverse proxy;
   - persistent SQLite volume for initial scale;
   - network restriction for the ingestion path;
   - global ingress rate limits in addition to the process-local limiter.
3. **Curren access/entitlement integration**
   - provision/revoke Premium and Agent API credentials from the private access control plane rather than static environment configuration.

Until those are completed, the default `https://api.curren.tech` URL in clients/plugins is the intended production endpoint contract, not evidence that a live production feed is already available.

## Private runtime mapping required

Current Woodsbot lifecycle states include:

```text
pending
active
closed_win
closed_loss
closed_be
closed_partial_win
expired
manual_close
```

The public projector must map them to:

```text
pending -> pending
active -> active
closed_win -> closed
closed_loss -> closed
closed_be -> closed
closed_partial_win -> closed
manual_close -> closed
expired -> expired
```

Target state exposed publicly is intentionally only:

```text
pending | hit
```

A hit target must include its actual `hit_at` timestamp.

## Current public contract

Read endpoints:

```text
GET /healthz
GET /v1/public/summary
GET /v1/signals
GET /v1/signals/{signal_id}
GET /v1/signals/{signal_id}/lifecycle
GET /v1/results
GET /v1/track-record
GET /v1/signals/{signal_id}/verification
```

Private publication endpoint:

```text
POST /internal/v1/publications
```

MCP tools:

```text
curren_list_active_signals
curren_get_signal
curren_get_signal_lifecycle
curren_get_recent_results
curren_get_track_record
curren_verify_signal
```

## Validation

There is intentionally no GitHub Actions workflow. Before release/deployment run:

```bash
python -m pip install -e '.[dev,mcp]'
python -m compileall -q src
pytest -q
ruff check .
python -m build
docker build -t curren-api:local .
```

For Omarchy changes also run on Omarchy 4/Quattro:

```bash
omarchy plugin validate .
```

## Release readiness

The public repo is suitable for continued OSS/client development, but **do not market it as a live Curren signal API until the private projector and production endpoint are actually deployed and verified**.
