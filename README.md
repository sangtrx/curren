# Curren

**Verifiable trading intelligence for humans and AI agents.**

This is the public developer surface for [Curren](https://curren.tech/): API contracts, a terminal CLI, an MCP server for AI agents, and a native Omarchy Quattro plugin.

> The private Curren signal engine, strategy logic, source ingestion, AI guard, execution runtime, and production database are **not** part of this repository. Public clients talk only to the Curren API boundary.

## What is here

- **CLI** — inspect active signals, lifecycle, recent results, track record, and verification records from a terminal.
- **MCP server** — give MCP-compatible AI agents read-only access to the same Curren intelligence.
- **Omarchy plugin** — a native Quattro bar widget for Curren status and public proof/results.
- **Contracts** — versioned public models shared by every client.

All clients consume the same external API contract. No client connects directly to the private trading runtime or its database.

## Status

This repository is being bootstrapped as the public Curren developer platform. Client interfaces are intentionally fail-closed: if the Curren API endpoint is unavailable or an entitlement does not allow a field, clients do not invent or backfill data.

## Python quick start

Python 3.11+ is required.

```bash
python -m pip install 'git+https://github.com/sangtrx/curren.git'
export CURREN_API_KEY='crn_...'
curren signals
```

Use another API endpoint during development:

```bash
export CURREN_API_URL='http://127.0.0.1:8000'
```

Machine-readable output is available from the CLI:

```bash
curren signals --json
curren signal crn_sig_example --json
curren results --limit 20 --json
curren track-record --json
curren verify crn_sig_example --json
```

## MCP

Install the MCP extra:

```bash
python -m pip install 'git+https://github.com/sangtrx/curren.git#egg=curren[mcp]'
```

Then configure an MCP host to run:

```text
curren-mcp
```

The initial read-only tool surface is deliberately small:

- `curren_list_active_signals`
- `curren_get_signal`
- `curren_get_signal_lifecycle`
- `curren_get_recent_results`
- `curren_get_track_record`
- `curren_verify_signal`

The MCP server is a thin adapter over the Curren API. It contains no signal-generation or execution logic.

## Omarchy Quattro

This repository is also a valid Omarchy plugin repository: `manifest.json` lives at the repository root and points to the QML implementation under `omarchy/`.

```bash
omarchy plugin add https://github.com/sangtrx/curren.git --enable
```

The first Omarchy surface uses only the public proof/status endpoint and stores no exchange credentials. Authenticated realtime signal access will use a separate secure entitlement flow rather than embedding private trading credentials in QML.

Validate on Omarchy 4/Quattro:

```bash
omarchy plugin validate .
```

## Architecture

```text
private Curren runtime
        |
        | one-way sanitized publication
        v
Curren public read model
        |
        v
    Curren API
   /    |     \
 CLI   MCP   Omarchy
```

The public side is read-only. A public client must never have credentials capable of writing into the signal, lifecycle, trading-intent, execution, or operator state of the private runtime.

## Environment

| Variable | Purpose | Default |
| --- | --- | --- |
| `CURREN_API_URL` | Curren API base URL | `https://api.curren.tech` |
| `CURREN_API_KEY` | Optional API entitlement token | unset |
| `CURREN_TIMEOUT_SECONDS` | HTTP request timeout | `10` |
| `CURREN_MCP_TRANSPORT` | MCP transport (`stdio` or `streamable-http`) | `stdio` |

## Security boundary

This repository intentionally does **not** include:

- Discord/source ingestion details
- raw source messages
- strategy/scoring implementation
- AI model features or model artifacts
- production database credentials
- trade intents, venue orders, account state, or execution controls
- deployment credentials or operator tooling

Signal and outcome fields exposed by the API are filtered by server-side entitlement. Omitting a restricted field is part of the contract, not an error for clients to work around.

## Development

```bash
python -m pip install -e '.[dev,mcp]'
pytest
ruff check .
```

## License

MIT. See `LICENSE`.
