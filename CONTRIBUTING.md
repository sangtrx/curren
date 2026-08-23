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

The private signal-generation, strategy, raw-source, model, account, and execution runtime is intentionally outside this repository.

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

1. Public clients remain read-only.
2. Do not add trade execution tools/endpoints to this public repo.
3. Do not add exchange, ingestion, or Premium secrets to Omarchy/QML.
4. Do not reconstruct fields omitted by server entitlement.
5. Publication input is strict: private/source/model/account/execution fields must fail validation rather than be ignored.
6. Public signal status stays normalized to `pending | active | closed | expired`.
7. Treat initial signal id/symbol/side/publication timestamp/entry/stop/target prices as immutable.
8. Treat the first terminal outcome as immutable.
9. Preserve per-signal `generated_at` replay ordering; stale projections must not roll state backward.
10. Lifecycle event identities are append-only and cannot be rewritten with different values.
11. Keep rate-limit bucket memory bounded; do not use/log raw credentials as bucket identities.
12. Be precise about verification: Curren hashes verify Curren-owned records, not an independent notary/timestamp authority.

## Pull requests

Keep changes focused and include regression tests for behavior changes. Security-sensitive boundary changes should state which invariant is affected and why the new design remains safe.

Do not include real credentials, private signal-source content, production database rows, or exchange account information in issues, tests, fixtures, screenshots, or pull requests.
