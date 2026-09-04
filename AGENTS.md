# Curren public platform agent rules

This file is the canonical entrypoint for AI coding agents working in `sangtrx/curren`.

## Repository role

This repository is the **public Curren developer/platform surface**. It owns the public read-only API
contract, Python client, CLI, MCP server, sanitized publication ingestion/read model, proof and
track-record projections, and public integrations/plugins.

It is **not** the Curren landing page. The canonical public landing page is
`sangtrx/curren-landing-page` at `https://curren.tech/`.

It is also not the private alpha generator, research repository, access/payment authority, or live
trade-execution runtime.

## Start here

Read in this order:

1. `AGENTS.md`
2. `AI_START_HERE.md`
3. `docs/PROJECT_STATUS.md`
4. `README.md`
5. `docs/API_CONTRACT.md`
6. `docs/ARCHITECTURE.md`
7. task-specific source/tests

Repository Git, current source/tests, and the files above outrank prior chats, old Curren repositories,
search-index snippets, or generated summaries.

## Ownership boundaries

- `sangtrx/curren-landing-page` owns the public landing/marketing frontend and metadata.
- `sangtrx/woodsbot-system` owns private signal generation, lifecycle, delivery, and private
  execution/reconciliation boundaries. This repository may consume only explicitly sanitized public
  publication contracts from that runtime.
- `sangtrx/curren-research` owns V9 quantitative research and accepted research releases.
- `sangtrx/curren-access` owns private membership/access/support/referral/payment truth.
- `sangtrx/curren-social-factory` owns content rendering/review/distribution preparation.
- `sangtrx/curren-workspace` owns cross-repository routing documentation only.

Never import private runtime databases, credentials, raw source messages, research working state, or
exchange/account secrets into this public repository.

## Coding/control path

Normal source work runs through the current shared infrastructure authority:

```text
controller -> Big Linux Orca -> fresh worktree -> Codex CLI via codex-lb
           -> checks -> commit -> push exact SHA to GitHub
```

Big Linux is the normal source writer. Alpha Linux is controller/Keros-gateway infrastructure, not a
runtime requirement for this repository. MacBook takeover follows the shared infrastructure emergency
policy and must not create a second simultaneous writer.

This repository does not use Keros or Kaggle merely because those Curren Research lanes exist; choose
a non-Big runner only when a task explicitly requires and authorizes it.

## Safety and public/private contract

- Never read or commit `.env` secrets. `.env.example` is documentation only.
- Keep public ingestion strict and one-way: private systems publish sanitized contract objects; public
  clients never gain a path back into private source state.
- Do not add public trade-execution endpoints or MCP tools unless the user explicitly changes product
  scope and the private execution/security architecture is separately designed and reviewed.
- Do not claim `api.curren.tech` or a live signal feed is operational unless current deployment/runtime
  evidence verifies it.
- Do not expose private strategy names, raw Discord/Telegram source IDs/messages, account IDs, exchange
  credentials, or private database structure through API errors, health endpoints, proofs, logs, or
  examples.
- Preserve server-enforced entitlement/visibility rules; clients/plugins must not be trusted to enforce
  private timing or authorization boundaries.
- Production deploys, credential changes, publication to a live endpoint, or external mutations require
  explicit operator authorization.

## Validation

For ordinary source changes, use the repository's current validation contract. At minimum inspect
`docs/PROJECT_STATUS.md`, `pyproject.toml`, and affected tests before deciding the gate.

The current full local/host release gate is:

```bash
python -m pip install -e '.[dev,mcp]'
python -m compileall -q src
pytest -q
ruff check .
python -m build
docker build -t curren-api:local .
```

For Omarchy/plugin changes also run the repository-documented plugin validation on the supported host.
Do not claim a command passed unless it actually ran successfully.

## Completion

A change is complete only when ownership is correct, public/private boundaries remain intact, relevant
focused/full checks pass on the exact accepted checkout, the full diff is reviewed, and the accepted
commit is durably present in GitHub `main`. Do not infer a production deployment from a source merge.
