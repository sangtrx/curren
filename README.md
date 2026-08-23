# Curren

**Verifiable trading intelligence for humans and AI agents.**

Curren is the public developer surface for [curren.tech](https://curren.tech/): a durable read-model API, terminal CLI, MCP server for AI agents, publication client, and native Omarchy Quattro plugin.

> The private Curren signal engine, strategy logic, raw source ingestion, AI guard, execution runtime, accounts, and production trading database are intentionally **not** part of this repository.

## What ships here

- **Curren API** — FastAPI + SQLite/WAL public read model with anonymous, Premium, and Agent views.
- **Publication boundary** — authenticated, idempotent ingestion of sanitized signal projections from the private runtime.
- **CLI** — active signals, lifecycle, results, track record, and publication-integrity verification.
- **MCP server** — the same read-only intelligence for MCP-compatible AI agents.
- **Omarchy plugin** — a native Quattro bar widget for delayed/public signal proof and recent results.
- **Contracts** — versioned Pydantic models shared across the server, publisher, CLI, and MCP adapters.

All public clients consume the API. None connects directly to the private trading runtime or its database.

## Architecture

```text
PRIVATE CURREN RUNTIME
signal generation / AI guard / lifecycle / execution
                    |
                    | sanitized outbound PublicationBatch
                    v
          POST /internal/v1/publications
                    |
                    v
+-------------------------------------------+
| CURREN PUBLIC READ MODEL                  |
| SQLite WAL + immutable initial snapshot   |
| + append-only lifecycle events            |
+---------------------+---------------------+
                      |
                      v
                 Curren API
             /        |        \
           CLI       MCP      Omarchy
```

The publication flow is one-way. The public service has no endpoint for placing orders, changing trading controls, or writing back into the private runtime.

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

Docker is also supported:

```bash
docker compose up --build
```

The SQLite database is persisted in the `curren-data` volume.

## Publishing real data

Set a private ingestion token on the API process:

```bash
export CURREN_INGEST_TOKEN='replace-with-a-long-random-secret'
curren-api
```

A private runtime integration sends a sanitized `PublicationBatch`:

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

For integration testing:

```bash
export CURREN_API_URL='http://127.0.0.1:8000'
export CURREN_INGEST_TOKEN='replace-with-a-long-random-secret'
curren-publish examples/publication.example.json
```

On first ingestion the API records an immutable hash over signal id, symbol, side, publication timestamp, entry, stop, and target prices. Later projections may update lifecycle/result state but cannot rewrite the original trade plan; conflicts return HTTP `409`.

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
| Closed results | full published plan + result | full |
| Active direction/status | after server-side delay | realtime |
| Active mark/R context | after server-side delay | realtime |
| Active entry/SL/TP prices | hidden | visible |
| Active lifecycle event prices | hidden/delayed | visible realtime |
| Track record | visible | visible |
| Integrity record | once signal is visible | realtime |

The default delay is 1,800 seconds. `CURREN_PUBLIC_DELAY_SECONDS` is an enforced **minimum** at the API boundary: a publisher may request a later public time but cannot shorten the server policy.

## CLI

```bash
export CURREN_API_URL='http://127.0.0.1:8000'
# export CURREN_API_KEY='crn_...'  # optional entitlement

curren summary
curren signals
curren signals --symbol HYPEUSDT --json
curren signal crn_sig_01
curren lifecycle crn_sig_01
curren results --limit 20
curren track-record
curren verify crn_sig_01
```

If the API omits a restricted field, the CLI reports it unavailable; it never reconstructs levels.

## MCP

Install the MCP extra:

```bash
python -m pip install -e '.[mcp]'
```

For normal agent use, run over stdio:

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
export CURREN_MCP_TRANSPORT=streamable-http
export CURREN_MCP_HOST=127.0.0.1
export CURREN_MCP_PORT=8001
curren-mcp
```

It uses MCP v2 stateless Streamable HTTP with JSON responses. The bundled v0.2 server deliberately rejects non-loopback HTTP binds because it does not yet ship an OAuth resource-server gate. Do not expose a paid upstream `CURREN_API_KEY` through an unauthenticated MCP endpoint; production remote MCP should sit behind a separately authenticated MCP resource server/gateway.

## Omarchy Quattro

The repository root is a third-party Omarchy plugin:

```bash
omarchy plugin add https://github.com/sangtrx/curren.git --enable
```

It exposes one `bar-widget`, reads only `/v1/public/summary`, and stores no API key, exchange credential, or execution permission in QML. `apiBaseUrl` is configurable for local/staging validation.

```bash
omarchy plugin validate .
```

## Verification semantics

`curren verify <signal-id>` recomputes the SHA-256 hash of the initial publication snapshot stored by the Curren API. The server rejects later changes to the immutable plan fields.

This detects mutation inside Curren's publication store. It is **not** an independent timestamp authority, blockchain proof, profitability guarantee, or third-party notary.

## Environment

| Variable | Purpose | Default |
| --- | --- | --- |
| `CURREN_DB_PATH` | Public read-model SQLite path | `./.local/curren.db` |
| `CURREN_PUBLIC_DELAY_SECONDS` | Minimum delay for active public visibility | `1800` |
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

The ingestion endpoint is disabled unless `CURREN_INGEST_TOKEN` is configured. Read entitlements use header credentials, never query-string secrets. For internet deployment, terminate TLS, add ingress rate limits, and network-restrict `/internal/v1/publications` in addition to its bearer token.

## Development

```bash
python -m pip install -e '.[dev,mcp]'
pytest -q
ruff check .
python -m build
```

See [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md), [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md), [`SECURITY.md`](SECURITY.md), and [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

MIT. See [`LICENSE`](LICENSE).
