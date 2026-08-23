# Security Policy

## Scope

Security issues in the public Curren API, CLI, MCP adapter, publication client, read model, rate limiter, or Omarchy plugin are in scope for this repository.

The private Curren trading runtime is intentionally not published here. Do not open public issues containing private runtime credentials, source data, exchange keys, production IPs, database contents, or other sensitive evidence.

## Reporting

Please report suspected vulnerabilities privately through GitHub's **Report a vulnerability** / Security Advisory flow for this repository when available. Do not include live credentials; use redacted/disposable test values.

## Security and integrity invariants

- Public clients are read-only; no public endpoint/tool can place or manage trades.
- The public service receives sanitized projections, not private trading/account database credentials.
- Publication uses a dedicated ingestion bearer token separate from read API keys.
- Publication models reject unknown/private fields.
- Public signal status is `pending | active | closed | expired`; target status is `pending | hit`.
- Missing/unknown read credentials fail closed.
- Active public data is delayed server-side and omits exact trade levels.
- The publisher cannot shorten or later rewrite the established public-availability schedule.
- Equal/older per-signal `generated_at` snapshots cannot roll state backward.
- Excessively future `generated_at` values are rejected before they can poison replay watermarks.
- A signal id cannot switch publication source after ownership is established.
- Initial trade-plan fields are immutable under a signal id.
- Lifecycle event identities are append-only and cannot be rewritten with different price/R values.
- The first terminal outcome and terminal result projection are immutable under a signal id.
- A terminal signal cannot return to a live state.
- Public recent results and track record are backed by immutable outcome records.
- Unauthenticated `/healthz` exposes only service health, not hidden signal counts or ingestion state.
- Omarchy QML contains no Premium, ingestion, exchange, or execution credentials and surfaces stale/offline state explicitly.
- Bundled MCP Streamable HTTP refuses non-loopback binds until a separate authenticated resource-server boundary exists.

Treat any change that weakens these invariants as security-sensitive.

## Rate limiting and proxy identity

Curren v0.4 includes a bounded-memory, process-local limiter for anonymous/public, Premium/Agent, and private publication traffic.

Raw tokens are never used as bucket identifiers. Valid credentials use a SHA-256-derived identity. Unknown/invalid read tokens remain client-identity limited so rotating bogus tokens cannot bypass the public quota.

Forwarded IP headers are ignored unless the direct ASGI peer is explicitly allowlisted via `CURREN_TRUSTED_PROXY_IPS`. For an allowlisted proxy chain, Curren walks `X-Forwarded-For` from right to left and skips only trusted proxy hops. Configure the allowlist narrowly and keep a global rate limit at ingress when using multiple workers/replicas.

## Production guidance

- Use TLS for every network carrying bearer tokens.
- Restrict `/internal/v1/publications` by network policy in addition to the token.
- Keep ingress/global abuse controls even though the application has a local limiter.
- Keep `CURREN_MAX_CLOCK_SKEW_SECONDS` aligned with realistic clock drift; do not disable it casually.
- Keep SQLite on a protected persistent volume and use SQLite-safe backups.
- Never expose `CURREN_INGEST_TOKEN` to CLI, MCP, Omarchy, browsers, or end users.
- Give MCP only the minimum read entitlement it needs.
- Keep the public API/read-model deployment independent from the private trading runtime.
- Docker Compose binds to loopback by default; broaden `CURREN_BIND_ADDRESS` only behind a deliberate network boundary.

## Verification hashes

The verification endpoint checks Curren-owned immutable initial publication and terminal outcome records. The application separately freezes the public terminal result projection after the first terminal snapshot.

These controls detect/prevent mutation inside Curren's publication service. They are not an independent timestamp/notary system, blockchain proof, exchange attestation, or guarantee of profitability. Claims implying otherwise should be treated as a documentation/security issue.
