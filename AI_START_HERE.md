# AI start here

Use this as the cold-start navigation for `sangtrx/curren`.

## Authority order

1. `AGENTS.md`
2. `docs/PROJECT_STATUS.md`
3. `README.md`
4. `docs/API_CONTRACT.md`
5. `docs/ARCHITECTURE.md`
6. affected source/tests

Resolve current checkout identity with Git before changing code. Do not infer current behavior from old
chat history, archived Curren repositories, or public marketing copy.

## What this repo is

This is the public Curren developer/platform repository:

```text
private sanitized publication input
 -> strict public publication contract
 -> read model / proof projections
 -> read-only HTTP API
 -> Python client / CLI / MCP / integrations
```

The canonical public landing page is `sangtrx/curren-landing-page` and is a separate repository.

## Sibling ownership

```text
curren-research      -> quantitative research / accepted releases
woodsbot-system      -> private signal/runtime/publication source
curren-access        -> private access/community/payment truth
curren-social-factory-> social content rendering/review preparation
curren-landing-page  -> canonical public curren.tech landing page
curren               -> this public API/CLI/MCP/developer surface
```

Cross-repository facts must be verified in the owning sibling. Integrate through sanitized versioned
contracts, not source copying or private database access.

## Safe local/host checks

```bash
python -m pip install -e '.[dev,mcp]'
python -m compileall -q src
pytest -q
ruff check .
python -m build
```

Use Docker/plugin checks when the changed scope requires them. Production deployment/publication remains
a separate explicitly authorized action.
