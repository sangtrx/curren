# Curren Public API Deployment

## Deployment shape

The first production shape is intentionally small:

```text
private Curren publisher
        |
        | HTTPS + ingestion bearer token
        v
reverse proxy / load balancer
        |
        v
single Curren API service
        |
        v
persistent SQLite/WAL volume
```

The public API is not the private trading runtime. Deploy and restart it independently.

## Container

Build:

```bash
docker build -t curren-api:0.2.0 .
```

Run:

```bash
docker run --rm \
  -p 8000:8000 \
  -v curren-data:/data \
  -e CURREN_INGEST_TOKEN='replace-with-long-random-secret' \
  -e CURREN_PUBLIC_DELAY_SECONDS=1800 \
  -e CURREN_API_KEYS_JSON='{"crn_premium_example":"premium"}' \
  curren-api:0.2.0
```

Or use `docker compose up --build`.

## Required production controls

### TLS

Terminate TLS before exposing the API publicly. Do not send API or ingestion bearer tokens over plaintext networks.

### Ingestion network restriction

In addition to the bearer token, restrict `/internal/v1/publications` at the reverse proxy/security-group layer to the private publisher network when possible.

### Secrets

Treat these as secrets:

- `CURREN_INGEST_TOKEN`
- every key inside `CURREN_API_KEYS_JSON`

Do not put real values in Git, container images, example files, QML, screenshots, or logs.

### Persistent volume

`CURREN_DB_PATH` must live on persistent storage. The Docker image defaults to `/data/curren.db`.

Back up the SQLite database with a SQLite-safe online backup method or while the service is stopped. Copying a live WAL database without its WAL/shm state is not a valid backup plan.

### Rate limiting

Apply public rate limiting at the ingress/proxy. Keep application request limits bounded (`limit <= 100`) regardless of proxy policy.

### Health check

Use:

```text
GET /healthz
```

A healthy empty database is valid. `ingestion_enabled=false` means the service is read-only because no ingest token is configured; it does not mean the API is unhealthy.

## Configuration

| Variable | Production guidance |
| --- | --- |
| `CURREN_DB_PATH` | persistent volume path |
| `CURREN_API_HOST` | usually `0.0.0.0` inside container |
| `CURREN_API_PORT` | usually `8000` |
| `CURREN_PUBLIC_DELAY_SECONDS` | enforced minimum public-delay policy |
| `CURREN_INGEST_TOKEN` | long random secret, private publisher only |
| `CURREN_API_KEYS_JSON` | provisioned server-side machine entitlements |
| `CURREN_LOG_LEVEL` | `info` normally |

The API enforces `published_at + CURREN_PUBLIC_DELAY_SECONDS` as the earliest active public availability. A publisher can delay a record further but cannot request an earlier public time.

## Publication retry model

The private runtime should publish a recent window/state projection repeatedly rather than depending on exactly-once delivery.

The ingestion contract is replay-safe:

- existing signal ids update mutable projection fields;
- identical initial plans are accepted;
- duplicate lifecycle events are ignored;
- changed immutable trade-plan fields return HTTP `409`.

This means a publisher can retry after timeout/restart without needing a distributed queue for the initial scale.

## Rollback

Application rollback is independent of the private trading runtime.

Before changing schema behavior:

1. Back up the public read-model database.
2. Deploy the new API version.
3. Verify `/healthz`, anonymous summary, Premium read, and one known verification record.
4. If needed, roll the application image back while leaving the private trading runtime untouched.

The current schema evolution is create-if-missing and additive. Breaking storage migrations should introduce an explicit migration mechanism before production use.

## Omarchy

The Omarchy plugin calls only the anonymous public summary. For production, leave its `apiBaseUrl` at `https://api.curren.tech`.

For staging/local testing set the plugin's `apiBaseUrl` setting to the reachable test API. Do not add Premium bearer keys to the QML plugin.

## MCP

For agent integrations, prefer `stdio`; its security boundary is the process that launches the server.

Local Streamable HTTP is available for development only:

```bash
CURREN_MCP_TRANSPORT=streamable-http \
CURREN_MCP_HOST=127.0.0.1 \
CURREN_MCP_PORT=8001 \
curren-mcp
```

The bundled v0.2 MCP process refuses non-loopback binds. It needs only a read API key (`CURREN_API_KEY`) and `CURREN_API_URL`; it never needs `CURREN_INGEST_TOKEN`.

A future public remote MCP endpoint must be deployed as an authenticated MCP resource server (OAuth 2.1 bearer validation / protected-resource metadata) or behind an equivalently authenticated gateway. Do not expose an upstream paid Curren API key through a globally reachable unauthenticated MCP process.
