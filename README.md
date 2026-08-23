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
            /         |         \
          CLI        MCP      Omarchy
```

The publication flow is one-way. The public service has no endpoint for placing orders, changing trading controls, or writing back into the private runtime.

## Quick start

Python 3.11+ is required.

```bash
python -m pip install -e '.[dev,mcp]'
cp .env.example .env
curren-api
```

By default the API starts on `127.0.0.1:8000` with an empty read model. Empty means empty: this project never creates fake signals to make a demo look alive.

Check it:

```bash
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/v1/public/summary
```

Or use Docker:

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

For integration testing, save that JSON to a file and run:

```bash
export CURREN_API_URL='http://127.0.0.1:8000'
export CURREN_INGEST_TOKEN='replace-with-a-long-random-secret'
curren-publish publication.json
```

On first ingestion the API records an immutable hash over the initial trade-plan fields: signal id, symbol, side, publication timestamp, entry, stop, and target prices. Later projections may update status, target-hit state, mark/PnL, close data, and append lifecycle events. Attempts to mutate the initial trade plan return HTTP `409`.

## Entitlements

Missing credentials are treated as the public tier.

Configure Premium/Agent API keys on the server with JSON:

```bash
export CURREN_API_KEYS_JSON='{
  "crn_example_premium_key":"premium",
  "crn_example_agent_key":"agent"
}'
```

Clients send:

```text
Authorization: Bearer crn_...
```

Policy in v0.2:

| Data | Public | Premium / Agent |
| --- | --- | --- |
| Closed results | full published plan + result | full |
| Active direction/status | after server-side delay | realtime |
| Active mark/R context | after server-side delay | realtime |
| Active entry/SL/TP prices | hidden | visible |
| Active lifecycle event prices | hidden/delayed | visible realtime |
| Track record | visible | visible |
| Integrity record | visible once signal is visible | visible realtime |

The default public delay is 1,800 seconds and is controlled by `CURREN_PUBLIC_DELAY_SECONDS` on the server. Delays are enforced before data leaves the API; clients are never asked to hide already-delivered realtime data.

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

Every read command supports structured JSON where useful. If the API omits a restricted field, the CLI prints it as unavailable; it never reconstructs levels.

## MCP

Install the MCP extra:

```bash
python -m pip install -e '.[mcp]'
```

Local/stdio mode:

```bash
export CURREN_API_URL='https://api.curren.tech'
export CURREN_API_KEY='crn_...'
curren-mcp
```

The tool surface is deliberately small:

- `curren_list_active_signals`
- `curren_get_signal`
- `curren_get_signal_lifecycle`
- `curren_get_recent_results`
- `curren_get_track_record`
- `curren_verify_signal`

For a remote MCP endpoint:

```bash
export CURREN_MCP_TRANSPORT=streamable-http
export CURREN_MCP_HOST=0.0.0.0
export CURREN_MCP_PORT=8001
curren-mcp
```

The HTTP mode uses MCP v2 Streamable HTTP in stateless JSON-response mode. MCP remains a thin adapter over the Curren API and exposes no execution tools.

## Omarchy Quattro

The repository root is a valid third-party Omarchy plugin:

```bash
omarchy plugin add https://github.com/sangtrx/curren.git --enable
```

It contains a single `bar-widget` entry point and reads only `/v1/public/summary`. It does not store API keys, exchange credentials, or execution permissions in QML.

The API base URL is a plugin setting, so a development Omarchy machine can point at a local/staging API without editing the plugin source.

Validate on Omarchy 4/Quattro:

```bash
omarchy plugin validate .
```

## Verification semantics

`curren verify <signal-id>` recomputes the SHA-256 hash of the initial publication snapshot stored by the Curren API. The server rejects later changes to those immutable trade-plan fields.

This is useful for detecting mutation inside the Curren publication store, but it is **not** an independent timestamp authority, blockchain proof, profitability guarantee, or third-party notary. A future transparency-log/notary layer can build on the stored content hash without changing the client contract.

## Environment

| Variable | Purpose | Default |
| --- | --- | --- |
| `CURREN_DB_PATH` | Public read-model SQLite path | `./.local/curren.db` |
| `CURREN_PUBLIC_DELAY_SECONDS` | Delay for active public visibility | `1800` |
| `CURREN_INGEST_TOKEN` | Enables/protects internal publication endpoint | unset = disabled |
| `CURREN_API_KEYS_JSON` | API key → `premium`/`agent` mapping | `{}` |
| `CURREN_API_HOST` | API bind host | `127.0.0.1` |
| `CURREN_API_PORT` | API bind port | `8000` |
| `CURREN_API_URL` | Client/publisher API base URL | `https://api.curren.tech` |
| `CURREN_API_KEY` | Optional client entitlement token | unset |
| `CURREN_TIMEOUT_SECONDS` | Client timeout | `10` |
| `CURREN_MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `CURREN_MCP_HOST` | Remote MCP bind host | `127.0.0.1` |
| `CURREN_MCP_PORT` | Remote MCP port | `8001` |

## Security boundary

This repository intentionally does **not** publish:

- raw Discord/source messages or source identifiers
- strategy/scoring implementation
- model features, model artifacts, or private AI-guard decisions
- private production database credentials
- trade intents, venue orders, account state, or exchange credentials
- kill switches, operator controls, or deployment secrets

The ingestion endpoint accepts only the sanitized public contract and is disabled unless `CURREN_INGEST_TOKEN` is configured. API-key entitlements are enforced server-side using header credentials, never query-string secrets.

For internet deployment, terminate TLS and enforce network/rate controls at the reverse proxy/load balancer. Keep `/internal/v1/publications` reachable only from the private publisher network in addition to using its bearer token.

## Development

```bash
python -m pip install -e '.[dev,mcp]'
pytest -q
ruff check .
python -m build
```

See:

- [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)
- [`SECURITY.md`](SECURITY.md)

## License

MIT. See [`LICENSE`](LICENSE).
