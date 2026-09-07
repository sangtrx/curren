# Curren Public Platform Status

Last reviewed: 2026-09-08

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

### Landing read replica

- Supabase project `curren-public` is provisioned as a landing-only sanitized replica, not a private-runtime datastore.
- Production migrations `20260905111608 create_curren_public_read_model` and `20260907202242 harden_curren_public_read_model_v2` define the bounded read model and hardened anonymous boundary.
- `public_live_signals` exposes delayed, freshness-bounded active status/R context without active entry, stop, targets, lifecycle, or private source identifiers.
- `public_recent_results` exposes terminal closed outcomes independently of active-feed freshness.
- `public_feed_status` distinguishes `idle`, `fresh`, and `stale` replica state.
- Anonymous writes are revoked; base tables use RLS; the public views use `security_invoker`.
- `supabase/functions/curren-api/index.ts` is the source authority for the Supabase publication bridge. The deployed v2 bridge enforces its own publisher Bearer authorization, the 1800-second minimum public delay, source ownership, bounded batch size, future-clock guard, and monotonic replay watermark.
- See `docs/SUPABASE_READ_MODEL.md` for the exact landing-replica contract and activation procedure.

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

## Not yet activated end to end

The public platform is not itself the Curren signal generator. The source-side publication projector and the Supabase landing replica now exist, but production signal publication is not yet active end to end.

1. **`woodsbot-system` publication projector activation**
   - the standalone sanitized projector is implemented and failure-isolated;
   - it remains disabled by default;
   - it must be configured to target the Supabase bridge, run one bounded accepted cycle, and then be verified before continuous publication is enabled;
   - at this checkpoint the Supabase `signals` replica contains zero rows, so no live-feed claim is valid.
2. **Canonical production deployment for `api.curren.tech`**
   - the separate FastAPI public API contract still requires its own verified production deployment if that canonical API hostname is to be marketed as live;
   - TLS/reverse proxy, persistent storage, ingestion network restriction, and global ingress rate limits remain deployment concerns for that service.
3. **Curren access/entitlement integration**
   - Premium and Agent credentials still need to be provisioned/revoked from the private access control plane rather than static environment configuration.

The Supabase landing read replica does not prove that `https://api.curren.tech` is live. Likewise, deployed Supabase infrastructure with zero replicated rows does not prove that production publication is enabled.

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

The public projector maps them to:

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

For the Supabase landing replica, additionally verify the current migration list, RLS/grants, `security_invoker` views, Security Advisor, deployed Edge Function source/version, and a bounded publisher cycle before calling the feed active.

## Release readiness

The public repo is suitable for continued OSS/client development, but **do not market either the canonical API or the Supabase landing replica as a live Curren signal feed until the production publisher is enabled and current runtime evidence verifies end-to-end publication**.
