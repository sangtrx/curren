# Curren Seed Deck — v0.3 — 2026-09-07

Canonical investor-deck source for Curren fundraising applications.

Identity authority: **Curren Identity & Commercial Thesis v1.0 — Verifiable Decision Intelligence**.

## Truth lock

- Category: **verifiable decision intelligence for financial markets**; crypto is the beachhead.
- Default one-liner: **Curren turns market decisions into verifiable, machine-readable trading intelligence.**
- Founder: **Sang Truong**, solo technical founder based in Vietnam.
- Stage: **pre-revenue**; no meaningful customer/user traction yet.
- Direct VC raise: **US$500,000**.
- Working direct-VC instrument: **post-money SAFE**.
- Working direct-VC cap: **US$8,000,000 post-money** unless a program specifies its own terms.
- Public platform: **v0.4 alpha**; public live-feed integration remains pending until verified otherwise.
- No claimed profitable native alpha strategy.
- Current legal/incorporation status: **Unincorporated. Curren is not currently owned by or incorporated as an existing legal entity.** Do not invent a jurisdiction, incorporation date, legal entity, or cap table.

Do not invent users, revenue, partnerships, adoption, funding history, returns, institutional usage, or chain-native implementation.

---

## Slide 1 — Curren

### Verifiable decision intelligence for financial markets

**Curren turns market decisions into verifiable, machine-readable trading intelligence.**

Crypto first · Vietnam · Pre-revenue · Solo technical founder

`curren.tech`

---

## Slide 2 — The problem

### Markets have plenty of information. Trustworthy decisions are still scarce.

A market call usually loses the evidence trail that matters:

- what was actually recommended before the move;
- what context was available at that time;
- whether the original plan was later edited or selectively deleted;
- how entry, invalidation, targets, expiry and updates evolved;
- what the terminal outcome was.

For a human this creates manual reconstruction. For software agents it creates a machine-trust problem.

**The missing primitive is a durable market-decision object with provenance, lifecycle and outcome.**

---

## Slide 3 — The product

### Turn each decision into a record that can be trusted and queried

A Curren decision record contains:

1. original thesis / setup;
2. publication time and provenance;
3. bounded evidence/context;
4. entry / invalidation / target / expiry rules;
5. append-only lifecycle updates;
6. terminal outcome;
7. verification of the original and final record.

The first accepted plan is preserved instead of being silently rewritten after the outcome is known.

---

## Slide 4 — One product, two commercial surfaces

### Curren Intelligence

**Curren Pro** — human interface for real-time/full-detail decision intelligence, lifecycle state and proof/history.

**Curren API** — read-only machine/team access for trading agents, automated workflows and small crypto trading teams.

Team contracts are packaging around the API, not a separate product line.

**Customers pay for action-ready, auditable intelligence — not raw market data and not a black-box promise of returns.**

---

## Slide 5 — The demo

### One decision, before the move through final resolution

```text
Original decision
(timestamp + thesis + plan + provenance)
        ↓
Lifecycle events
(entry / update / target / invalidation / expiry)
        ↓
Terminal outcome
        ↓
Verification + history
        ↓
Same record in Curren Pro / API / MCP
```

The investor demo must use clearly labeled fixture/sample data unless a live public record has been production-verified. Never present fixture data as live trading intelligence.

---

## Slide 6 — Why now

### AI agents are becoming financial-software users

Human-only dashboards can tolerate screenshots, narrative context and manual interpretation. Automated workflows require explicit state, timestamps, permissions, replay safety and machine-readable outcomes.

Crypto is the fastest beachhead because it is 24/7, programmable and already combines human traders, bots, APIs and communities in the same workflow.

**As software moves from reading market data to consuming decisions, provenance becomes infrastructure.**

---

## Slide 7 — Beachhead customer

### Start where the pain is already operational

**Primary initial buyer:** small crypto trading teams and builders of trading/financial agents that already run automated or semi-automated workflows.

Today they often monitor multiple feeds, parse messages, reconstruct lifecycle state and evaluate providers manually.

Curren aims to replace that fragmented process with one structured decision stream and auditable history.

Serious active traders are a secondary validation/distribution market through Curren Pro. Curren is not being built as a mass-retail Telegram signal group.

---

## Slide 8 — What is already built

### Strong technical foundation; commercial validation is next

**Public platform — v0.4 alpha**

- read-only FastAPI API;
- Python client + CLI;
- MCP server;
- entitlements;
- immutable initial publication records;
- append-only lifecycle events;
- terminal outcomes/results;
- verification and replay protection.

**Private live runtime**

- live source ingestion and normalization;
- quality gates;
- lifecycle processing;
- distribution workflows;
- separately gated admin-only execution lane.

**Research authority**

- point-in-time evidence workflow;
- OOS / purging / embargo / holdout discipline;
- rejected research remains recorded.

**Commercial truth:** pre-revenue; meaningful customer validation is still to be established.

---

## Slide 9 — Moat

### A compounding dataset captured before outcomes are known

The moat is not a hash, an API schema or MCP by itself.

Curren is designed to accumulate a proprietary longitudinal dataset of:

**ex-ante decision + evidence + lifecycle + outcome + regime/context + consumer behavior**

That history can improve source/model evaluation, confidence calibration, quality gates, agent routing, provider reputation and team workflows.

Because the record begins before the outcome, it cannot be reconstructed later from only the successful examples.

---

## Slide 10 — Business model + GTM

### Validate one product and two ways to pay

**Commercial hypotheses**

- **Curren Pro** — subscription for human decision-intelligence access.
- **Curren API** — machine/team entitlement for agents and automated workflows.

No current revenue is claimed.

**Initial GTM loop**

```text
public proof/content
      ↓
product demo
      ↓
design partner
      ↓
paid validation
      ↓
repeatable workflow
```

Public proof should include losers, invalidations, no-trades and rejected research — not cherry-picked screenshots.

---

## Slide 11 — Evidence discipline

### We are willing to reject our own ideas

Current V9 frozen representative Stage-A campaign:

**88 / 88 trials completed**

**0 representative survivors**

**No retuning**

Curren does **not** currently claim a profitable native research strategy from this campaign.

The point is process integrity: point-in-time evidence, explicit rejection gates and preservation of failed candidates instead of manufacturing an attractive backtest.

Current private runtime may still use external signal-source inputs while source-independent research is developed.

---

## Slide 12 — Founder + ask

### Sang Truong — solo technical founder

AI engineering lead and hands-on full-stack builder with experience across applied AI, agentic/LLM systems, backend/frontend, infrastructure, evaluation and auditability.

Curren has been built end to end across research, live runtime, public API/CLI/MCP, access rails and product surfaces.

**Raise:** US$500,000

**Working instrument:** post-money SAFE

**Working cap:** US$8,000,000 post-money

Capital is intended to:

1. turn the existing stack into one live customer product;
2. recruit design partners and validate willingness to pay;
3. make the Pro vs API wedge evidence-driven;
4. build repeatable acquisition around public proof and integrations;
5. expand research/data infrastructure behind strict evidence gates;
6. hire selectively after a real product bottleneck is proven.

---

## Investor Q&A guardrails

### Are you a signal company?

Curren can deliver market setups, but the product is not a black-box signal feed. The product is the structured, verifiable decision lifecycle — what was decided, when, how it changed and what happened.

### Are you a data company?

No. Curren consumes market data but is not trying to out-cover large data vendors. It sits one layer higher: decisions and their provenance/outcomes.

### Are you an AI trading bot?

No. AI/agent consumers are an important interface, but public Curren is read-only intelligence. Execution remains separately authorized and is not the current commercial wedge.

### Where is the moat if competitors add hashes or MCP?

The intended moat is the accumulated ex-ante decision/evidence/lifecycle/outcome dataset and the workflows built around it, not a single transport protocol or integrity primitive.

### Why crypto first?

Crypto has continuous markets, programmable venues and existing automated workflows, making it the fastest environment to validate machine-readable decision intelligence. The longer-term category is financial-market decision intelligence, not crypto data alone.

---

## Asset status

- This Markdown file is the current canonical deck source.
- Current rendered deck is **v0.3 / 12 slides**, generated 2026-09-07 and hash-verified against the canonical source.
- PDF: `Curren_Seed_Deck_v0.3_2026-09-07.pdf` — SHA-256 `ce4605a40ece7b5e2cd8c85920c20a8a038c8bcf0b0852b88097ad1ac1483699`.
- PPTX: `Curren_Seed_Deck_v0.3_2026-09-07.pptx` — SHA-256 `712d26569fb96a492e12d3467d70a888988c31f1fe9028cd4108a01ffdfe2fdc`.
- The old 2026-09-06 11-slide PDF/PPTX remain superseded and **must not be sent to investors**.
- The v0.3 binaries are preserved in the ChatGPT Library, but are not yet committed to GitHub or published at a stable public asset URL; do not claim otherwise.
- `https://curren.tech/investors` is deployed, independently public-readback verified, and approved for accelerator/investor application evidence. Keep its current truth boundaries: v0.4 alpha, pre-revenue, no profitability claim, public live-feed integration pending, and clearly labeled demonstration data.
- Founder video recording/upload remains a user-only/manual gate.
- Recheck each accelerator/VC form and terms at actual submission time.
