# Curren

**Verifiable crypto trading intelligence for humans and AI agents.**

Curren is the public developer/distribution surface for [curren.tech](https://curren.tech/): a read-model API, terminal CLI, MCP server, publication client, and native Omarchy Quattro plugin.

> The private signal engine, strategy/research logic, raw-source ingestion, AI guard, execution runtime, accounts, and production trading database are intentionally **not** part of this repository.

## Project status

**Current release line: v0.4.0 (alpha).** The public platform and contracts are implemented; the remaining production integration is the private `woodsbot-system` projector plus deployment/entitlement wiring. Until that feed is deployed, `https://api.curren.tech` should be treated as the production-default endpoint contract, not as a promise that live signal data is already available.

See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) for the exact implemented/pending boundary.

## What ships here

- **Curren API** — FastAPI + SQLite/WAL public read model with Public, Premium, and Agent views.
- **Strict publication boundary** — authenticated sanitized projections only; unknown/private fields fail closed.
- **Replay safety** — per-signal source timestamps prevent stale retries from rolling state backward.
- **Integrity records** — immutable initial trade plan, append-only lifecycle, immutable terminal outcome/result projection.
- **Rate limiting** — bounded process-local quotas for anonymous, authenticated, and ingestion traffic, with trusted-proxy handling.
- **CLI** — signals, lifecycle, results, track record, and verification.
- **MCP server** — six read-only tools for MCP-compatible AI agents.
- **Omarchy plugin** — native Quattro bar widget for delayed active context and proof-backed results.

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
| immutable terminal outcome/result projection   |
| per-signal replay watermark                    |
+------------------------+-----------------------+
                         |
                         v
                    Curren API
                /        |        \
              CLI       MCP      Omarchy
```

The flow is one-way. The public service has no endpoint/tool for placing orders, changing trading controls, or writing back into the private runtime.

## Quick start

Python 3.11+:

```bash
python -m pip install -e '.[dev,mcp]'
cp .env.example .env
curren-api
```

The API starts on `127.0.0.1:8000` with an empty read model. It never fabricates signals to make a demo look active.

```bash
curl http://127.0.0.1:8000/healthz
# {"status":"ok"}

curl http://127.0.0.1:8000/v1/public/summary
```

Docker Compose also binds to loopback by default:

```bash
docker compose up --build
```

Override `CURREN_BIND_ADDRESS` only when you deliberately put the service behind an appropriate network/TLS boundary.

## Publishing real data

Enable private ingestion on the API:

```bash
export CURREN_INGEST_TOKEN='replace-with-a-long-random-secret'
curren-api
```

A private projector sends a strict sanitized `PublicationBatch`:

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

Publication signal status is intentionally small:

```text
pending | active | closed | expired
```

The private projector must normalize internal states. For the current Woodsbot lifecycle that means, for example:

```text
closed_win
closed_loss
closed_be
closed_partial_win
manual_close
        -> closed

expired -> expired
```

Targets use `pending | hit`; a `hit` target requires `hit_at` and a `pending` target cannot carry `hit_at`.

Unknown fields are rejected, each batch may contain a signal id only once, all clocks must be timezone-aware, and `generated_at` cannot exceed the configured future-clock-skew allowance (`CURREN_MAX_CLOCK_SKEW_SECONDS`, default 300s).

For integration testing:

```bash
export CURREN_API_URL='http://127.0.0.1:8000'
export CURREN_INGEST_TOKEN='replace-with-a-long-random-secret'
curren-publish examples/publication.example.json
```

### Replay and integrity rules

For each signal id Curren stores the publication source and latest accepted `generated_at`. An equal/older projection is counted as `stale_ignored` and cannot roll state backward. The first accepted `public_available_at` schedule is also retained; later projections cannot hide or accelerate an already scheduled public release.

The initial publication hash locks signal id, symbol, side, publication timestamp, entry, stop, and ordered target prices. Lifecycle identities are append-only. The first terminal snapshot records an immutable outcome hash, and its terminal result projection is frozen as well; later attempts to rewrite result/target/PnL context return HTTP `409`.

`/v1/results` only exposes terminal rows backed by an immutable outcome record. Track-record statistics are also computed only from those immutable outcome records.

## Entitlements

No read credential means `public`. Premium/Agent keys are configured server-side:

```bash
export CURREN_API_KEYS_JSON='{
  "crn_example_premium_key":"premium",
  "crn_example_agent_key":"agent"
}'
```

| Data | Public | Premium / Agent |
| --- | --- | --- |
| Proof-backed terminal results | full | full |
| Active direction/status | after server delay | realtime |
| Active mark/R context | after server delay | realtime |
| Active entry/SL/TP prices | hidden | visible |
| Active lifecycle prices | hidden/delayed | visible realtime |
| Track record | visible | visible |
| Initial publication verification | once visible | realtime |
| Terminal outcome verification | terminal signals | realtime |

`CURREN_PUBLIC_DELAY_SECONDS` is a server-enforced minimum. A publisher may choose a later first availability time but cannot shorten it or change the schedule after first publication.

## Rate limiting

Default application limits per 60-second window:

```text
Public / anonymous     60 requests per client identity
Premium / Agent       300 requests per API key
Private ingestion     120 requests per ingestion credential
```

Responses expose `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset-After`; HTTP `429` also includes `Retry-After`. Valid token bucket identities are SHA-256-derived rather than raw secrets. Rotating invalid Bearer tokens stays in the anonymous client bucket.

By default forwarded IP headers are ignored. Behind a trusted proxy, allowlist only the direct proxy networks:

```bash
export CURREN_TRUSTED_PROXY_IPS='127.0.0.1/32,172.18.0.0/16'
```

Curren then walks the `X-Forwarded-For` chain from the application backward, skips only allowlisted proxy hops, and uses the first untrusted hop as the client identity. The built-in limiter remains process-local; multi-worker/replica production deployments still need a global ingress/API-gateway quota.

`/healthz` is intentionally not rate limited and intentionally returns no signal counts or entitlement state, so it cannot be polled as a side channel for hidden signal activity.

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

The CLI never reconstructs entitlement-hidden fields and surfaces API rate-limit retry hints.

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

Read-only tools:

- `curren_list_active_signals`
- `curren_get_signal`
- `curren_get_signal_lifecycle`
- `curren_get_recent_results`
- `curren_get_track_record`
- `curren_verify_signal`

Local Streamable HTTP is development-only:

```bash
CURREN_MCP_TRANSPORT=streamable-http \
CURREN_MCP_HOST=127.0.0.1 \
CURREN_MCP_PORT=8001 \
curren-mcp
```

The bundled v0.4 MCP process refuses non-loopback HTTP binds because it does not ship an OAuth resource-server gate. Do not expose a paid upstream `CURREN_API_KEY` behind an unauthenticated remote MCP endpoint.

## Omarchy Quattro

The repository root is an Omarchy plugin:

```bash
omarchy plugin add https://github.com/sangtrx/curren.git --enable
```

It exposes one `bar-widget`, reads only `/v1/public/summary`, stores no API/exchange/execution credential in QML, and explicitly displays `STALE`/`OFFLINE` rather than presenting cached data as live.

```bash
omarchy plugin validate .
```

## Verification semantics

`curren verify <signal-id>` checks Curren's stored SHA-256 initial publication record and, for terminal signals, the terminal outcome record.

These hashes detect mutation inside Curren's publication store. They are **not** independent timestamp authority, blockchain proof, exchange attestation, profitability guarantee, or third-party notary.

## Environment

| Variable | Purpose | Default |
| --- | --- | --- |
| `CURREN_DB_PATH` | SQLite read-model path | `./.local/curren.db` |
| `CURREN_PUBLIC_DELAY_SECONDS` | Minimum public active delay | `1800` |
| `CURREN_MAX_CLOCK_SKEW_SECONDS` | Maximum accepted future publisher clock skew | `300` |
| `CURREN_RATE_LIMIT_WINDOW_SECONDS` | Process-local limiter window | `60` |
| `CURREN_PUBLIC_RATE_LIMIT` | Anonymous requests/window | `60` |
| `CURREN_AUTH_RATE_LIMIT` | Premium/Agent requests/key/window | `300` |
| `CURREN_INGEST_RATE_LIMIT` | Publication requests/window | `120` |
| `CURREN_TRUSTED_PROXY_IPS` | Trusted proxy IPs/CIDRs | unset |
| `CURREN_INGEST_TOKEN` | Enable/protect publication endpoint | unset = disabled |
| `CURREN_API_KEYS_JSON` | API key → `premium`/`agent` | `{}` |
| `CURREN_API_HOST` | API bind inside process | `127.0.0.1` |
| `CURREN_API_PORT` | API port | `8000` |
| `CURREN_BIND_ADDRESS` | Compose host bind | `127.0.0.1` |
| `CURREN_HOST_PORT` | Compose host port | `8000` |
| `CURREN_API_URL` | Client/publisher base URL | `https://api.curren.tech` |
| `CURREN_API_KEY` | Optional read entitlement | unset |
| `CURREN_TIMEOUT_SECONDS` | Client timeout | `10` |
| `CURREN_MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `CURREN_MCP_HOST` | MCP local HTTP bind | `127.0.0.1` |
| `CURREN_MCP_PORT` | MCP local HTTP port | `8001` |

## Security boundary

This repository intentionally does **not** publish raw source messages/identifiers, strategy/scoring/research code, model features, private runtime database credentials, trade intents, venue/account state, exchange keys, kill switches, or operator secrets.

For internet deployment: use TLS, network-restrict `/internal/v1/publications`, keep ingress/global rate limits, and keep the public service operationally independent from the private trading runtime.

## Development

This repository intentionally has no GitHub Actions workflow. Validate locally/on the target host:

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

See [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md), [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md), [`SECURITY.md`](SECURITY.md), and [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT. See [`LICENSE`](LICENSE).
