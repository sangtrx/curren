# Security Policy

## Scope

Security issues in the public Curren API, CLI, MCP adapter, publication client, or Omarchy plugin are in scope for this repository.

The private Curren trading runtime is intentionally not published here. Do not open public issues containing private runtime credentials, source data, exchange keys, production IPs, database contents, or other sensitive evidence.

## Reporting

Please report a suspected vulnerability privately through GitHub's **Report a vulnerability** / Security Advisory flow for this repository when available.

Do not include live credentials in a report. Use redacted or disposable test values.

## Security invariants

The project is designed around these boundaries:

- Public clients are read-only.
- No public endpoint can place or manage trades.
- The public service does not receive private trading/account database credentials.
- Publication uses a dedicated ingestion bearer token separate from read API keys.
- Missing/unknown API credentials fail closed.
- Active public data is delayed server-side and omits exact trade levels.
- Omarchy QML contains no Premium, ingestion, exchange, or execution credentials.
- Initial published trade-plan fields are immutable under a signal id.

A change that violates one of these invariants should be treated as a security-sensitive change even if it does not immediately produce an exploit.

## Production guidance

- Use TLS for every network carrying bearer tokens.
- Restrict `/internal/v1/publications` by network policy in addition to the token.
- Put rate limiting and abuse controls at the ingress/reverse proxy.
- Keep SQLite storage on a protected persistent volume and use SQLite-safe backups.
- Never expose `CURREN_INGEST_TOKEN` to CLI, MCP, Omarchy, browsers, or end users.
- Give MCP only the minimum read API entitlement it needs.

## Verification hashes

The verification endpoint checks integrity against Curren's own recorded initial publication snapshot. It is not an independent timestamp/notary system. Treat claims that imply otherwise as a documentation/security issue because they could mislead downstream consumers.
