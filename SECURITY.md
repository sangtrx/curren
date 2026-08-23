# Security Policy

## Scope

Security issues in the public Curren API, CLI, MCP adapter, publication client, read model, rate limiter, or Omarchy plugin are in scope for this repository.

The private Curren trading runtime is intentionally not published here. Do not open public issues containing private runtime credentials, source data, exchange keys, production IPs, database contents, or other sensitive evidence.

## Reporting

Please report suspected vulnerabilities privately through GitHub's **Report a vulnerability** / Security Advisory flow for this repository when available.

Do not include live credentials. Use redacted/disposable test values.

## Security and integrity invariants

- Public clients are read-only.
- No public endpoint/tool can place or manage trades.
- The public service does not receive private trading/account database credentials.
- Publication uses a dedicated ingestion bearer token separate from read API keys.
- Publication models reject unknown fields instead of silently accepting private/runtime data.
- Public publication status is a closed set: `pending`, `active`, `closed`, `expired`.
- Missing/unknown read credentials fail closed.
- Active public data is delayed server-side and omits exact trade levels.
- The publisher cannot shorten the configured public delay.
- Stale/equal per-signal `generated_at` projections cannot roll state backward.
- A signal id cannot switch publication source after source ownership is established.
- Initial trade-plan fields are immutable under a signal id.
- Lifecycle event identities are append-only and cannot be rewritten with different price/R values.
- The first terminal outcome is immutable under a signal id.
- A terminal signal cannot return to a live state.
- Track record is computed from immutable terminal outcome records, not mutable signal rows.
- Omarchy QML contains no Premium, ingestion, exchange, or execution credentials.
- Bundled MCP Streamable HTTP refuses non-loopback binds until a separate authenticated resource-server boundary exists.

Treat any change that weakens one of these invariants as security-sensitive even if it does not immediately produce an exploit.

## Rate limiting

Curren v0.3 includes a bounded-memory, process-local limiter for:

- anonymous/public API traffic;
- Premium/Agent API traffic;
- private publication traffic.

Raw tokens are never used as bucket identifiers. Valid credentials are represented by a non-secret SHA-256-derived identity. Unknown/invalid read tokens remain peer-IP limited so rotating bogus tokens cannot bypass the public quota.

The application deliberately does not trust `X-Forwarded-For` for its local bucket key. In multi-worker/replica deployments, use a trusted ingress/API gateway for global rate limits and real client-IP policy.

## Production guidance

- Use TLS for every network carrying bearer tokens.
- Restrict `/internal/v1/publications` by network policy in addition to the token.
- Keep ingress/global abuse controls even though the application has its own limiter.
- Keep SQLite on a protected persistent volume and use SQLite-safe backups.
- Never expose `CURREN_INGEST_TOKEN` to CLI, MCP, Omarchy, browsers, or end users.
- Give MCP only the minimum read entitlement it needs.
- Keep the public API/read-model deployment independent from the private trading runtime.

## Verification hashes

The verification endpoint checks two Curren-owned records:

1. the immutable initial publication snapshot;
2. the immutable terminal outcome snapshot when the signal has closed/expired.

These hashes detect mutation inside Curren's publication store. They are not an independent timestamp/notary system, blockchain proof, exchange attestation, or guarantee of profitability. Claims implying otherwise should be treated as a documentation/security issue because they could mislead downstream consumers.
