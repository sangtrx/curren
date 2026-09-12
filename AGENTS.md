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
2. `WORKFLOW_AUTHORITY.md`
3. the current target `sangtrx/sang-workspace` GitHub Issue
4. `AI_START_HERE.md`
5. `docs/PROJECT_STATUS.md`
6. `README.md`
7. `docs/API_CONTRACT.md`
8. `docs/ARCHITECTURE.md`
9. task-specific source/tests

Repository Git, current source/tests, and the files above outrank prior chats, old Curren repositories,
search-index snippets, generated summaries, or historical Linear/SAN records.

## Workflow authority

GitHub Issues in `sangtrx/sang-workspace` are the only durable task/workflow authority. Put task status,
checkpoints, blockers, next actions, user gates, active execution/session/worktree references, writer
ownership, and acceptance evidence there. GitHub repositories/PRs/commits remain source/artifact
authority. ChatGPT Web is the primary orchestrator; BigLinux/Alpha-Linux and other hosts are bounded
execution infrastructure.

Linear is retired and read-only historical only. Do not create, update, comment on, checkpoint, or route
active work through Linear. Historical `SAN-*`/Linear references in dated fundraising or delivery packets
are provenance labels only; use the corresponding current GitHub Issue for live workflow truth.

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

Normal source work is Web/GitHub-first:

```text
ChatGPT Web + GitHub -> candidate branch / exact pushed SHA
                     -> SentinelX on Big Linux for build/test/runtime evidence
                     -> Orca/Codex only when another coding/reasoning worker is useful
```

GitHub is durable source authority. Big Linux keeps a canonical checkout synchronized safely with
GitHub, fast-forwarding only clean non-ahead `main`; dirty/diverged local work is preserved. Big Linux
is the canonical Orca worktree/terminal host, not a permanently preferred source writer.

When ChatGPT Web needs structural code context before merge, the shared infrastructure may fetch the
exact feature-branch SHA into one reusable GitNexus shadow analysis checkout. This does not create a
second source writer. If source work is explicitly escalated to Orca/Codex, that delegated worktree
owns the writer lease until it pushes its result, and ChatGPT Web acts as reviewer/supervisor meanwhile.
Record that live ownership on the current GitHub Issue and clear it when the delegated session ends.

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
focused/full checks pass on the exact accepted checkout, the full diff is reviewed, the current
`sangtrx/sang-workspace` GitHub Issue records the durable acceptance transition and clears finished
execution/session/worktree refs, and the accepted commit is durably present in GitHub `main`. Temporary
task branches/worktrees should then be cleaned up through the shared authorized lifecycle rather than
accumulated indefinitely. Do not infer a production deployment from a source merge.
