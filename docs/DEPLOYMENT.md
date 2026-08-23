# Curren Public API Deployment

## Initial production shape

```text
private Curren publisher
        |
        | HTTPS + ingestion bearer token
        v
trusted reverse proxy / load balancer
        |
        | TLS + global rate limit + network ACL
        v
single Curren API process
        |
        | process-local rate limiter
        v
persistent SQLite/WAL volume
```

The public API is operationally independent from the private trading runtime.

## Container

```bash
docker build -t curren-api:0.4.0 .

docker run --rm \
  -p 127.0.0.1:8000:8000 \
  -v curren-data:/data \
  -e CURREN_INGEST_TOKEN='replace-with-long-random-secret' \
  -e CURREN_PUBLIC_DELAY_SECONDS=1800 \
  -e CURREN_MAX_CLOCK_SKEW_SECONDS=300 \
  -e CURREN_PUBLIC_RATE_LIMIT=60 \
  -e CURREN_AUTH_RATE_LIMIT=300 \
  -e CURREN_INGEST_RATE_LIMIT=120 \
  -e CURREN_API_KEYS_JSON='{"crn_premium_example":"premium"}' \
  curren-api:0.4.0
```

`docker compose up --build` also binds to `127.0.0.1` by default. Override `CURREN_BIND_ADDRESS` only deliberately.

## Required production controls

### TLS and ingestion ACL

Terminate TLS before bearer-token traffic. Restrict `/internal/v1/publications` to the private publisher network in addition to the ingestion token.

### Secrets

Treat `CURREN_INGEST_TOKEN` and every key inside `CURREN_API_KEYS_JSON` as secrets. Never put real values in Git, images, examples, QML, screenshots, or logs.

### Persistent SQLite

`CURREN_DB_PATH` must live on persistent storage. Back up SQLite with a SQLite-safe online backup or while stopped; copying only the main file from a live WAL database is not sufficient.

### Rate limiting and proxy identity

Default local limits per 60 seconds:

- public: 60 per resolved client;
- Premium/Agent: 300 per valid API key;
- ingestion: 120 per ingestion credential.

Configuration:

```text
CURREN_RATE_LIMIT_WINDOW_SECONDS
CURREN_PUBLIC_RATE_LIMIT
CURREN_AUTH_RATE_LIMIT
CURREN_INGEST_RATE_LIMIT
CURREN_TRUSTED_PROXY_IPS
```

`CURREN_TRUSTED_PROXY_IPS` is empty by default, so forwarded IP headers are ignored. If a direct peer is allowlisted, Curren walks `X-Forwarded-For` from right to left, skips only trusted proxy hops, and uses the first untrusted hop as the client identity. Do not allowlist networks that can be reached directly by untrusted clients.

The built-in limiter is process-local. Multiple workers/replicas require a global ingress/API-gateway quota.

### Publisher clock safety

`CURREN_MAX_CLOCK_SKEW_SECONDS` defaults to 300. A `generated_at` farther in the future is rejected with HTTP `422` before it can become a replay watermark. Keep publisher and API hosts time-synchronized.

### Health check

```text
GET /healthz
```

Expected body:

```json
{"status":"ok"}
```

Health is not application-rate-limited and intentionally exposes no internal signal count or ingestion state.

## Configuration

| Variable | Guidance |
| --- | --- |
| `CURREN_DB_PATH` | persistent read-model path |
| `CURREN_API_HOST` | `0.0.0.0` inside container |
| `CURREN_API_PORT` | normally `8000` |
| `CURREN_BIND_ADDRESS` | Compose host bind; default `127.0.0.1` |
| `CURREN_HOST_PORT` | Compose host port; default `8000` |
| `CURREN_PUBLIC_DELAY_SECONDS` | minimum public active delay |
| `CURREN_MAX_CLOCK_SKEW_SECONDS` | maximum accepted future projector clock skew |
| `CURREN_RATE_LIMIT_WINDOW_SECONDS` | app limiter window |
| `CURREN_PUBLIC_RATE_LIMIT` | anonymous requests/window |
| `CURREN_AUTH_RATE_LIMIT` | Premium/Agent requests/key/window |
| `CURREN_INGEST_RATE_LIMIT` | publisher requests/window |
| `CURREN_TRUSTED_PROXY_IPS` | trusted proxy IPs/CIDRs |
| `CURREN_INGEST_TOKEN` | private publisher credential |
| `CURREN_API_KEYS_JSON` | server-side machine entitlements |
| `CURREN_LOG_LEVEL` | normally `info` |

## Publication retry model

The private runtime should send cumulative committed snapshots instead of depend on exactly-once delivery.

Requirements:

1. use one stable `source`;
2. emit a fresh monotonic `generated_at` only for new state;
3. normalize runtime status to `pending | active | closed | expired`;
4. normalize target state to `pending | hit` and include `hit_at` for hits;
5. include cumulative lifecycle events;
6. never send private/source/model/account/execution fields;
7. do not attempt to change the established `public_available_at` after first publication.

Equal/older snapshots are `stale_ignored`. Conflicting plan, lifecycle, terminal outcome/result projection, source ownership, or terminal-to-live transitions return HTTP `409` atomically.

## Storage evolution

v0.3 introduced `source`, `source_generated_at`, and `outcome_records`. v0.4 makes terminal result presentation proof-backed and freezes terminal result projection after the first outcome record.

Legacy terminal rows without `outcome_records` are deliberately excluded from `/v1/results` and track-record statistics until a valid newer terminal snapshot creates an immutable outcome record.

Before schema/behavior changes, back up the read model, deploy independently from the private runtime, verify health/public/Premium/terminal-proof paths, and roll back the public service independently if necessary.

## Omarchy

The plugin calls anonymous `/v1/public/summary` only. Do not add Premium/read/ingestion keys to QML. Validate on Omarchy 4/Quattro with:

```bash
omarchy plugin validate .
```

## MCP

Prefer `stdio` for agent integrations. Bundled Streamable HTTP is development-only and refuses non-loopback binds:

```bash
CURREN_MCP_TRANSPORT=streamable-http \
CURREN_MCP_HOST=127.0.0.1 \
CURREN_MCP_PORT=8001 \
curren-mcp
```

A public remote MCP endpoint needs a separately authenticated MCP resource-server/gateway. Never expose a paid upstream Curren API key through a globally reachable unauthenticated MCP process.

## Validation without GitHub Actions

This repository intentionally has no GitHub Actions workflow. Run before release/deployment:

```bash
python -m pip install -e '.[dev,mcp]'
python -m compileall -q src
pytest -q
ruff check .
python -m build
docker build -t curren-api:0.4.0 .
```
