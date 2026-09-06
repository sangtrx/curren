# Curren Seed Deck — 2026-09-06

Canonical investor deck source for Curren fundraising applications.

## Fundraising facts

- Target raise: **US$500,000**
- Working post-money cap: **US$8,000,000**
- Preferred generic instrument: post-money SAFE unless a program specifies its own terms
- Founder: **Sang Truong**
- Email: `tqsang97@gmail.com`
- Phone: `+84582332694`
- Current full-time team count: **1**
- Stage: **pre-revenue / pre-seed**
- Founder is willing to transition to Curren full-time if accepted/funded

Do not invent traction, revenue, partnerships, returns, or funding history.

---

## Slide 1 — Curren

**Verifiable crypto trading intelligence for humans and AI agents.**

Curren
Vietnam · Pre-revenue · Solo technical founder

`curren.tech`

## Slide 2 — The problem

### Crypto intelligence is hard to trust

Traders and software agents consume a flood of signals, screenshots, model outputs, and market commentary, but the evidence trail is usually weak:

- initial calls can be edited after the fact;
- lifecycle updates are fragmented across channels;
- backtests can hide selection and timing mistakes;
- AI agents need structured machine-readable context, not screenshots;
- execution and private strategy systems should not be exposed just to make intelligence consumable.

**The missing layer is not another alert feed. It is trustworthy market intelligence with explicit provenance and access boundaries.**

## Slide 3 — The product

### One intelligence layer, multiple consumers

Curren is building a pipeline where market intelligence can move from research to live evaluation to a sanitized public read model.

```text
PIT research
    ↓
private signal evaluation + lifecycle
    ↓
strict one-way publication boundary
    ↓
verifiable public read model
    ↓
API · CLI · MCP · human interfaces
```

Humans can consume the same bounded state that software agents query programmatically.

## Slide 4 — What is already built

### This is not just a deck

**Research**

- Curren Research V9 point-in-time evidence factory
- immutable data/evidence identities
- OOS / purging / embargo / holdout discipline
- rejected candidates remain preserved

**Private runtime**

- market-event ingestion and normalization
- signal quality gates
- lifecycle tracking
- distribution workflows
- isolated admin-only execution lane

**Public platform — v0.4 alpha**

- read-only API
- terminal CLI
- six MCP tools
- sanitized publication boundary
- replay protection
- immutable initial publication and terminal outcome records

## Slide 5 — Trust by construction

### A signal should leave a trail, not a rewritten screenshot

Curren's public model freezes the first accepted trade plan and appends lifecycle events over time.

Core primitives already implemented:

- strict publication schema;
- per-signal source ownership;
- monotonic publication timestamps;
- immutable initial signal-plan hash;
- append-only lifecycle events;
- immutable terminal outcome and result projection;
- public verification endpoint;
- read-only clients with no public execution controls.

These hashes are mutation detection inside Curren — **not** blockchain proof, exchange attestation, timestamp authority, or a profitability guarantee.

## Slide 6 — AI-agent native

### Market intelligence should be queryable, not scraped

Curren's MCP server currently exposes six read-only tools:

- `curren_list_active_signals`
- `curren_get_signal`
- `curren_get_signal_lifecycle`
- `curren_get_recent_results`
- `curren_get_track_record`
- `curren_verify_signal`

This creates a path for AI agents to consume structured market state without receiving exchange keys, execution permissions, or private strategy logic.

## Slide 7 — Research discipline is part of the product

### We are willing to produce a negative result

The current V9 representative Stage-A campaign completed:

**88 / 88 trials**

**0 representative survivors**

**No retuning**

The one-shot terminal holdout remains untouched.

Curren does **not** currently claim a profitable strategy from this campaign.

The goal is reproducible evidence, not attractive backtests. A research system that can reject its own ideas is more valuable than one optimized to always produce a chart that looks good.

## Slide 8 — Business model hypothesis

### Monetization plumbing exists; monetization is not yet validated

Curren Access already implements the product-side infrastructure for:

- Premium memberships;
- Telegram / Discord access state;
- exchange-partner onboarding;
- optional USDT / USDC checkout;
- support and referral workflows.

Stablecoin checkout is currently default-off and Curren is pre-revenue.

Initial business-model hypotheses to validate:

1. Premium intelligence for serious retail traders.
2. API / agent access for automated workflows and AI products.
3. B2B intelligence / research infrastructure for trading teams or fintech products.

Do not present these as validated revenue streams yet.

## Slide 9 — Why now

### AI agents are becoming financial software users

The market is moving from human-only dashboards toward software that can continuously read, reason over, and act on structured financial context.

That increases the cost of weak provenance: an agent needs to know what was known when, what changed later, and which fields it is actually authorized to see.

Curren is being built around those constraints from the beginning rather than bolting an API onto a screenshot-first signal product.

## Slide 10 — Next 12 months

### From infrastructure to validated product

**0–3 months**

- connect the private-to-public production projector;
- ship and verify `api.curren.tech`;
- complete investor/design-partner demo surface;
- run focused customer discovery with traders, agent builders, and fintech teams.

**3–6 months**

- validate the highest-value human vs agent use cases;
- turn entitlement infrastructure into a real paid pilot if demand exists;
- improve proof-backed lifecycle and result UX;
- continue governed alpha research without weakening holdout discipline.

**6–12 months**

- expand the public intelligence layer around the validated buyer;
- build durable agent/API workflows;
- test B2B or platform distribution where evidence supports it;
- scale research and data coverage only behind reproducible gates.

## Slide 11 — Founder / ask

### Sang Truong — solo technical founder

Current professional anchor: Head of Artificial Intelligence at EPIC TECHNOLOGY.

Background spans applied AI systems, agentic/LLM products, computer vision, backend/frontend, infrastructure, and research. Curren is an independent project built hands-on across research, runtime, public platform, access, and product surfaces.

**Current fundraising stage:** pre-revenue / pre-seed.

**Raise:** US$500,000 via a post-money SAFE at a working US$8,000,000 cap unless a program specifies its own terms.

Sang is willing to transition to Curren full-time if accepted/funded.

What funding would accelerate:

- product and customer validation;
- production public data integration;
- market/data infrastructure;
- agent/API productization;
- research execution capacity;
- first focused hires after product demand is clearer.

---

## Application-specific opening variants

### YZi Labs

Lead with trusted-agent infrastructure + programmable markets; do not invent chain/token implementation.

### Alliance

Lead with crypto-native technical depth, agent-compatible market infrastructure, evidence discipline, and ability to ship across the stack.

### YC

Lead with the large product insight: AI agents need verifiable, structured financial intelligence; Curren is building the trust and data layer rather than another signal feed.

### Base Batches

Only use Base-native claims that are implemented and verified. The bounded intended wedge is selective onchain attestation of Curren verification records while keeping strategy and execution private/offchain.

---

## Rendered asset manifest

Generated in the fundraising work session on 2026-09-06:

- `Curren_Seed_Deck_2026-09-06.pdf`
  - SHA-256: `8d48b07c975edd740b93ed0b91df5ab54319476d10630a0d0bc8d53ff9ffc411`
  - 11 pages
- `Curren_Seed_Deck_2026-09-06.pptx`
  - SHA-256: `a84aa3cf60b8c176bd212d5b98a03f757965b1a4f3d9057fe4a0d9a741c60cf6`

The rendered binaries are generated artifacts of this canonical source. Do not claim a GitHub binary path unless those exact assets are uploaded and the hashes match.