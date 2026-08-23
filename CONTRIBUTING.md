# Contributing to Curren

Thanks for helping improve the public Curren developer platform.

## Good contribution areas

- API/client correctness and compatibility
- MCP interoperability
- Omarchy/Quattro UX and compatibility
- documentation and examples
- reliability, security, and test coverage

The private signal-generation, strategy, raw-source, model, account, and execution runtime is intentionally outside this repository.

## Development

Run the local verification suite before opening a pull request:

```bash
python -m pip install -e '.[dev,mcp]'
python -m compileall -q src
pytest -q
ruff check .
python -m build
docker build -t curren-api:local .
```

For Omarchy changes, also validate on Omarchy 4/Quattro:

```bash
omarchy plugin validate .
```

## Public contract rules

Please preserve these invariants:

1. Public clients remain read-only.
2. Do not add trade execution tools/endpoints to the public repo.
3. Do not add exchange, ingestion, or Premium secrets to Omarchy/QML.
4. Do not reconstruct fields omitted by server entitlement.
5. Keep private-runtime/source/model/account state out of `PublicationBatch`.
6. Treat initial signal id/symbol/side/publication timestamp/entry/stop/target prices as immutable.
7. Be precise about verification: the hash checks Curren's recorded snapshot; it is not an independent notary.

## Pull requests

Keep changes focused and include tests for behavior changes. Security-sensitive boundary changes should call out which invariant is affected and why the new design remains safe.

Do not include real credentials, private signal-source content, production database rows, or exchange account information in issues, tests, fixtures, screenshots, or pull requests.
