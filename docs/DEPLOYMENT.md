# Curren Public API Deployment

## Deployment shape

The first production shape remains intentionally small:

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

The public API is not the private trading runtime. Deploy/restart it independently.

## Container

Build:

```bash
docker build -t curren-api:0.3.0 .
```

Run:

```bash
docker run --rm \
  -p 8000:8000 \
  -v curren-data:/data \
  -e CURREN_INGEST_TOKEN='replace-with-long-random-secret' \
  -e CURREN_PUBLIC_DELAY_SECONDS=1800 \
  -e CURREN_PUBLIC_RATE_LIMIT=60 \
  -e CURREN_AUTH_RATE_LIMIT=300 \
  -e CURREN_INGEST_RATE_LIMIT=120 \
  -e CURREN_TRUSTED_PROXY_IPS='' \
  -e CURREN_API_KEYS_JSON='{"crn_premium_example":"premium"}' \
  curren-api:0.3.0
```

Or use `docker compose up --build`.

## Required production controls

### TLS

Terminate TLS before exposing the API publicly. Do not send read or ingestion bearer tokens over plaintext networks.

### Ingestion network restriction

In addition to the bearer token, restrict `/internal/v1/publications` at the reverse proxy/security-group layer to the private publisher network when possible.

### Secrets

Treat these as secrets:

- `CURREN_INGEST_TOKEN`
- every key inside `CURREN_API_KEYS_JSON`

Do not put real values in Git, images, examples, QML, screenshots, or logs.

### Persistent volume

`CURREN_DB_PATH` must live on persistent storage. The Docker image defaults to `/data/curren.db`.

Back up SQLite with a SQLite-safe online backup method or while the service is stopped. Copying a live WAL database without its WAL/shm state is not a valid backup plan.

### Rate limiting

The API has a bounded single-process limiter. Defaults are per 60-second window:

- anonymous/public: 60 per resolved client identity
- Premium/Agent: 300 per valid API key
- ingestion: 120 per valid ingestion token

Configure with:

```text
CURREN_RATE_LIMIT_WINDOW_SECONDS
CURREN_PUBLIC_RATE_LIMIT
CURREN_AUTH_RATE_LIMIT
CURREN_INGEST_RATE_LIMIT
CURREN_TRUSTED_PROXY_IPS
```

By default `CURREN_TRUSTED_PROXY_IPS` is empty. In that mode Curren ignores `X-Forwarded-For` and uses the direct ASGI peer, preventing clients from spoofing new rate-limit identities.

If the API sits behind a trusted proxy, explicitly allowlist that proxy IP or CIDR, for example:

```bash
export CURREN_TRUSTED_PROXY_IPS='127.0.0.1/32,172.18.0.0/16'
```

Only when the direct peer matches an allowlisted network does Curren accept the left-most `X-Forwarded-For` address as the anonymous client identity. The trusted proxy **must overwrite/sanitize** incoming forwarding headers; do not configure an untrusted network here.

This limiter is a local guard, not a distributed quota authority. If you run multiple Uvicorn workers or replicas, each process has its own counters. Enforce the global policy at trusted ingress as well.

### Health check

Use:

```text
GET /healthz
```

Health checks are not application-rate-limited. A healthy empty database is valid. `ingestion_enabled=false` means no ingestion token is configured; it does not mean the service is unhealthy.

## Configuration

| Variable | Production guidance |
| --- | --- |
| `CURREN_DB_PATH` | persistent volume path |
| `CURREN_API_HOST` | usually `0.0.0.0` inside container |
| `CURREN_API_PORT` | usually `8000` |
| `CURREN_PUBLIC_DELAY_SECONDS` | enforced minimum public delay |
| `CURREN_RATE_LIMIT_WINDOW_SECONDS` | app limiter window |
| `CURREN_PUBLIC_RATE_LIMIT` | anonymous requests/window |
| `CURREN_AUTH_RATE_LIMIT` | Premium/Agent requests/key/window |
| `CURREN_INGEST_RATE_LIMIT` | publisher requests/window |
| `CURREN_TRUSTED_PROXY_IPS` | comma-separated trusted proxy IPs/CIDRs; empty by default |
| `CURREN_INGEST_TOKEN` | long random secret, private publisher only |
| `CURREN_API_KEYS_JSON` | server-side machine entitlements |
| `CURREN_LOG_LEVEL` | `info` normally |

## Publication retry model

The private runtime should send cumulative state projections rather than depend on exactly-once delivery.

For each signal the public read model stores the latest accepted `generated_at`. Equal/older projections are returned as `stale_ignored` and cannot roll the state back. Therefore a publisher can safely retry after timeout/restart without a distributed queue at the initial scale.

Publisher requirements:

1. Use one stable `source` identifier.
2. Generate a fresh monotonic `generated_at` for new state snapshots.
3. Include cumulative lifecycle state expected downstream.
4. Normalize private statuses to `pending | active | closed | expired`.
5. Never send private/source/model/account/execution fields; strict validation rejects them.
6. Do not expect to change `public_available_at` after the first accepted publication; the original schedule is retained.

A single batch may contain each signal id at most once.

Conflicts return HTTP `409` when a newer projection attempts to rewrite:

- immutable initial trade plan;
- an existing lifecycle event identity with different values;
- a terminal outcome;
- a terminal signal back to a live state;
- the established publication source.

## Storage evolution

v0.3 adds `source`, `source_generated_at`, and `outcome_records`. Initialization performs additive `ALTER TABLE` migration for the two signal columns and `CREATE TABLE IF NOT EXISTS` for terminal outcomes.

Legacy terminal rows created before v0.3 do not have an outcome record until the private publisher republishes a valid newer terminal snapshot. Track record intentionally reads only immutable `outcome_records`, so this migration can temporarily reduce reported sample size rather than trust mutable legacy outcomes.

Before storage/schema changes:

1. Back up the read-model database safely.
2. Deploy the new application version.
3. Verify `/healthz`, anonymous summary, one Premium read, and verification for one active and one terminal signal.
4. Roll back the application independently of the private runtime if necessary.

Breaking storage migrations should introduce an explicit migration mechanism before production use.

## Omarchy

The Omarchy plugin calls only anonymous `/v1/public/summary`. Leave `apiBaseUrl` at `https://api.curren.tech` in production.

Do not add Premium/read/ingestion keys to QML.

## MCP

Prefer `stdio` for agent integrations.

Local Streamable HTTP is development-only:

```bash
CURREN_MCP_TRANSPORT=streamable-http \
CURREN_MCP_HOST=127.0.0.1 \
CURREN_MCP_PORT=8001 \
curren-mcp
```

The bundled v0.3 MCP process refuses non-loopback binds. It only needs a read API key (`CURREN_API_KEY`) and `CURREN_API_URL`; it never needs `CURREN_INGEST_TOKEN`.

A public remote MCP endpoint must sit behind a separately authenticated MCP resource-server/gateway. Never expose a paid upstream Curren API key through a globally reachable unauthenticated MCP process.

## Validation without GitHub Actions

This repository intentionally has no GitHub Actions workflow. Run on the deployment/staging host before release:

```bash
python -m pip install -e '.[dev,mcp]'
python -m compileall -q src
pytest -q
ruff check .
python -m build
docker build -t curren-api:0.3.0 .
```

On Omarchy 4/Quattro also run:

```bash
omarchy plugin validate .
```
