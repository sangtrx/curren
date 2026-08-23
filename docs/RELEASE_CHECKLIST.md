# Public Release Checklist

Use this checklist before publishing a Curren public-platform release.

## Automated gates

- [ ] Python 3.11 CI passes.
- [ ] Python 3.12 CI passes.
- [ ] Python 3.13 CI passes.
- [ ] `pytest -q` passes.
- [ ] `ruff check .` passes.
- [ ] source distribution and wheel build successfully.
- [ ] API Docker image builds successfully.

## Contract/security gates

- [ ] Public clients remain read-only.
- [ ] No strategy/source/model/account/execution internals are present in `PublicationBatch`.
- [ ] Ingestion is disabled when `CURREN_INGEST_TOKEN` is unset.
- [ ] Unknown read API keys fail closed.
- [ ] The server-enforced public delay cannot be shortened by a publisher payload.
- [ ] Active public responses omit exact entry/SL/TP and lifecycle prices.
- [ ] Closed results expose only the intended public proof fields.
- [ ] Initial publication plan fields remain immutable under a signal id.
- [ ] Verification documentation does not imply an independent timestamp/notary authority.
- [ ] Bundled MCP Streamable HTTP refuses non-loopback unauthenticated binds.
- [ ] Omarchy QML contains no API, ingestion, exchange, or execution credentials.

## Host validation gates

- [ ] `omarchy plugin validate .` passes on Omarchy 4/Quattro.
- [ ] Omarchy widget renders correctly against an empty API.
- [ ] Omarchy widget renders delayed active signals and recent results against a staging API.
- [ ] CLI smoke test succeeds against staging.
- [ ] MCP stdio smoke test succeeds from a supported MCP host.

## Production-data gate

- [ ] Private runtime publication integration has been reviewed in its own repository under that repository's required code-intelligence/impact workflow.
- [ ] Production publication uses a dedicated ingestion credential and network restriction.
- [ ] No fake/example signal has been sent to the production read model.
