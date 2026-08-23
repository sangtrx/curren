# Contributing to Curren

Thanks for helping improve the public Curren developer platform.

## Good contribution areas

- API/client correctness and compatibility
- publication/read-model integrity
- rate-limit and abuse resistance
- MCP interoperability
- Omarchy/Quattro UX and compatibility
- documentation/examples
- reliability, security, and test coverage

The private signal-generation, strategy/research, raw-source, model, account, and execution runtime is intentionally outside this repository.

## Development

This repository intentionally has no GitHub Actions workflow. Run local/host validation before opening or merging a pull request:

```bash
python -m pip install -e '.[dev,mcp]'
python -m compileall -q src
pytest -q
ruff check .
python -m build
docker build -t curren-api:local .
```

For Omarchy changes also validate on Omarchy 4/Quattro:

```bash
omarchy plugin validate .
```

## Public contract rules

Preserve these invariants:

1. Public clients remain read-only; do not add execution tools/endpoints.
2. Do not add exchange, ingestion, Premium, or private-runtime secrets to public clients/QML.
3. Do not reconstruct fields omitted by server entitlement.
4. Publication input is strict: private/source/model/account/execution fields fail validation.
5. Public signal status stays `pending | active | closed | expired`; target state stays `pending | hit`.
6. Initial signal id/symbol/side/publication timestamp/entry/stop/target prices are immutable.
7. The first server-established public availability schedule is retained.
8. Terminal outcome and terminal result projection are immutable after the first terminal snapshot.
9. Per-signal `generated_at` preserves replay ordering; stale/future-poisoning snapshots must not corrupt state.
10. Lifecycle event identities are append-only and cannot be rewritten with different values.
11. Public result lists and track record must remain proof-backed by immutable outcome records.
12. Health checks must not expose hidden/realtime signal activity.
13. Rate-limit bucket memory stays bounded; raw credentials are never bucket keys/log material.
14. Forwarded client identity is trusted only through explicitly allowlisted proxy hops.
15. Verification claims stay precise: Curren-owned integrity hashes are not an independent notary/timestamp authority.

## Pull requests

Keep changes focused and include regression tests for behavior changes. Security-sensitive boundary changes should state which invariant is affected and why the new design remains safe.

Do not include real credentials, private signal-source content, production database rows, or exchange account information in issues, tests, fixtures, screenshots, or pull requests.
