# Curren

**Verifiable trading intelligence for humans and AI agents.**

Curren is the public developer surface for [curren.tech](https://curren.tech/): a read-model API, terminal CLI, MCP server for AI agents, publication client, and native Omarchy Quattro plugin.

> The private Curren signal engine, strategy logic, raw-source ingestion, AI guard, execution runtime, accounts, and production trading database are intentionally **not** part of this repository.

## What ships here

- **Curren API** — FastAPI + SQLite/WAL read model with Public, Premium, and Agent views.
- **Publication boundary** — strict authenticated ingestion of sanitized projections from the private runtime.
- **Replay safety** — per-signal source timestamps prevent stale retries from rolling state backward.
- **Verifiable records** — immutable initial trade-plan records plus separate immutable terminal-outcome hashes.
- **Rate limiting** — bounded application-level limits for public, authenticated, and ingestion traffic.
- **CLI** — active signals, lifecycle, results, track record, and verification.
- **MCP server** — the same read-only intelligence for MCP-compatible agents.
- **Omarchy plugin** — native Quattro bar widget for delayed/public signal proof and recent results.

All public clients consume the API. None connects directly to the private trading runtime or its database.

## Architecture

```text
PRIVATE CURREN RUNTIME
signal generation / AI guard / lifecycle / execution
                    |
                    | strict sanitized PublicationBatch
                    v
          POST /internal/v1/publications
                    |
                    v
+------------------------------------------------+
| CURREN PUBLIC READ MODEL                       |
| SQLite WAL                                     |
| immutable initial publication                  |
| append-only lifecycle events                   |
| immutable terminal outcome                     |
| per-signal replay watermark                    |
+------------------------+-----------------------+
                         |
                         v
                    Curren API
                /        |        \
              CLI       MCP      Omarchy
```

The flow is one-way. The public service has no endpoint for placing orders, changing trading controls, or writing back into the private runtime.

## Quick start

Python 3.11+ is required.

```bash
python -m pip install -e '.[dev,mcp]'
cp .env.example .env
curren-api
```

The API starts on `127.0.0.1:8000` with an empty read model. Empty means empty: this project never creates fake signals to make a demo look alive.

```bash
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/v1/public/summary
```

Docker:

```bash
docker compose up --build
```

## Publishing real data

Set a private ingestion token on the API process:

```bash
export CURREN_INGEST_TOKEN='replace-with-a-long-random-secret'
curren-api
```

A private runtime sends a strict sanitized `PublicationBatch`:

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
      "entry": 42.18,
      "stop": 40.90,
      "targets": [
        {"price": 43.45, "status": "pending"},
        {"price": 44.72, "status": "pending"}
      ],
      "mark": 42.60,
      "current_r": 0.33,
      "lifecycle": []
    }
  ]
}
```

Unknown fields are rejected rather than ignored. Public signal status is a closed set:

```text
pending | active | closed | expired
```

The private projector must normalize internal lifecycle states such as `closed_win` or `closed_loss` into that public contract before publication. A batch may contain each signal id at most once.

For integration testing:

```bash
export CURREN_API_URL='http://127.0.0.1:8000'
export CURREN_INGEST_TOKEN='replace-with-a-long-random-secret'
curren-publish examples/publication.example.json
```

### Replay and immutability rules

For each signal id, Curren stores the publication source and latest `generated_at` watermark. A later-arriving batch with an equal/older watermark is counted as `stale_ignored` and cannot roll the public state backward.

The first accepted public-availability schedule is retained for that signal id. A newer projection can update lifecycle/PnL state, but it cannot hide or accelerate an already scheduled public release by changing `public_available_at`.

On first publication the API hashes immutable plan fields: signal id, symbol, side, publication timestamp, entry, stop, and target prices. Attempts to mutate them return HTTP `409`.

When a signal first becomes terminal, Curren also records an immutable outcome hash over terminal status, `realized_r`, `closed_at`, and `exit_reason`. A later projection cannot rewrite that result under the same signal id. Track-record statistics are computed from these locked outcome records, not mutable signal rows.

Lifecycle records are append-only. Reusing the same `(signal_id, event_type, event_at)` with different price/R data is rejected.

## Entitlements

No read credential means `public` access. Premium/Agent keys are configured server-side:

```bash
export CURREN_API_KEYS_JSON='{
  "crn_example_premium_key":"premium",
  "crn_example_agent_key":"agent"
}'
```

Clients send `Authorization: Bearer crn_...`.

| Data | Public | Premium / Agent |
| --- | --- | --- |
| Closed results | full published plan + locked result | full |
| Active direction/status | after server-side delay | realtime |
| Active mark/R context | after server-side delay | realtime |
| Active entry/SL/TP prices | hidden | visible |
| Active lifecycle event prices | hidden/delayed | visible realtime |
| Track record | visible | visible |
| Publication verification | once signal is visible | realtime |
| Terminal outcome verification | for terminal signals | realtime |

`CURREN_PUBLIC_DELAY_SECONDS` is an enforced **minimum** at the API boundary: a publisher may request a later public time on first publication but cannot shorten server policy.

## Rate limiting

The API ships a bounded single-process limiter. Defaults are per 60-second window:

```text
Public / anonymous     60 requests
Premium / Agent       300 requests per API key
Private ingestion     120 requests per ingestion credential
```

Responses include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset-After`. HTTP `429` includes `Retry-After`.

Unknown/invalid read tokens do **not** receive their own buckets; they remain limited by client identity so rotating bogus Bearer tokens cannot bypass the anonymous quota. Raw API keys are never used as bucket identifiers.

By default Curren ignores `X-Forwarded-For` and uses the direct ASGI peer. If the API sits behind a reverse proxy, explicitly allowlist only that trusted proxy IP/CIDR:

```bash
export CURREN_TRUSTED_PROXY_IPS='127.0.0.1/32,172.18.0.0/16'
```

Only an allowlisted direct peer may provide the forwarded client identity. The trusted proxy must overwrite/sanitize incoming forwarding headers.

The built-in limiter is intentionally process-local. If you run multiple workers/replicas, enforce a global/distributed limit at the reverse proxy/API gateway as well.

## CLI

```bash
export CURREN_API_URL='http://127.0.0.1:8000'
# export CURREN_API_KEY='crn_...'

curren summary
curren signals
curren signals --symbol HYPEUSDT --json
curren signal crn_sig_01
curren lifecycle crn_sig_01
curren results --limit 20
curren track-record
curren verify crn_sig_01
```

The client reports rate-limit retry hints and never reconstructs fields omitted by server entitlement.

## MCP

Install:

```bash
python -m pip install -e '.[mcp]'
```

Normal agent use is stdio:

```bash
export CURREN_API_URL='https://api.curren.tech'
export CURREN_API_KEY='crn_...'
curren-mcp
```

Tools:

- `curren_list_active_signals`
- `curren_get_signal`
- `curren_get_signal_lifecycle`
- `curren_get_recent_results`
- `curren_get_track_record`
- `curren_verify_signal`

Local Streamable HTTP is available for development:

```bash
CURREN_MCP_TRANSPORT=streamable-http \
CURREN_MCP_HOST=127.0.0.1 \
CURREN_MCP_PORT=8001 \
curren-mcp
```

The bundled v0.3 server rejects non-loopback HTTP binds because it does not ship an OAuth resource-server gate. Do not expose a paid upstream `CURREN_API_KEY` through an unauthenticated MCP endpoint.

## Omarchy Quattro

The repository root is a third-party Omarchy plugin:

```bash
omarchy plugin add https://github.com/sangtrx/curren.git --enable
```

It exposes one `bar-widget`, reads only `/v1/public/summary`, and stores no API key, exchange credential, or execution permission in QML.

```bash
omarchy plugin validate .
```

## Verification semantics

`curren verify <signal-id>` verifies the stored SHA-256 initial publication record and, after closure/expiry, the terminal outcome record.

These hashes detect mutation inside Curren's publication store. They are **not** an independent timestamp authority, blockchain proof, profitability guarantee, or third-party notary.

## Environment

| Variable | Purpose | Default |
| --- | --- | --- |
| `CURREN_DB_PATH` | Public read-model SQLite path | `./.local/curren.db` |
| `CURREN_PUBLIC_DELAY_SECONDS` | Minimum delay for active public visibility | `1800` |
| `CURREN_RATE_LIMIT_WINDOW_SECONDS` | Limiter window | `60` |
| `CURREN_PUBLIC_RATE_LIMIT` | Anonymous requests/window | `60` |
| `CURREN_AUTH_RATE_LIMIT` | Premium/Agent requests/key/window | `300` |
| `CURREN_INGEST_RATE_LIMIT` | Publication requests/window | `120` |
| `CURREN_TRUSTED_PROXY_IPS` | Trusted proxy IPs/CIDRs allowed to supply forwarded client IP | unset |
| `CURREN_INGEST_TOKEN` | Protect/enable internal publication endpoint | unset = disabled |
| `CURREN_API_KEYS_JSON` | API key → `premium`/`agent` mapping | `{}` |
| `CURREN_API_HOST` | API bind host | `127.0.0.1` |
| `CURREN_API_PORT` | API bind port | `8000` |
| `CURREN_API_URL` | Client/publisher API base URL | `https://api.curren.tech` |
| `CURREN_API_KEY` | Optional client entitlement token | unset |
| `CURREN_TIMEOUT_SECONDS` | Client timeout | `10` |
| `CURREN_MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `CURREN_MCP_HOST` | Local HTTP bind host | `127.0.0.1` |
| `CURREN_MCP_PORT` | Local HTTP port | `8001` |

## Security boundary

This repository intentionally does **not** publish raw source messages/identifiers, strategy/scoring code, model artifacts/features, private runtime DB credentials, trade intents, venue/account state, exchange credentials, kill switches, or operator secrets.

The ingestion endpoint is disabled unless `CURREN_INGEST_TOKEN` is configured. Read entitlements use header credentials, never query-string secrets. For internet deployment, terminate TLS, network-restrict `/internal/v1/publications`, and enforce ingress rate limits in addition to the built-in limiter.

## Development

This repository intentionally does not run GitHub Actions. Validate changes locally/on the target host:

```bash
python -m pip install -e '.[dev,mcp]'
python -m compileall -q src
pytest -q
ruff check .
python -m build
docker build -t curren-api:local .
```

For Omarchy changes also run:

```bash
omarchy plugin validate .
```

See [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md), [`SECURITY.md`](SECURITY.md), and [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT. See [`LICENSE`](LICENSE).
