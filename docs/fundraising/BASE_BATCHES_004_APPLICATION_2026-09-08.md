# Base Batches 004 — Curren application packet — 2026-09-08

Status: **offline submission packet ready; founder video recording + authenticated final submission remain manual gates**.

Official program authority:

- https://www.base.org/batches
- https://www.base.org/batches/apply
- https://blog.base.org/introducing-base-batches-004

Application deadline shown by Base: **September 9, 2026**. The public apply page says the application requires both a written and video submission and does not save drafts, so use this file as the copy/paste source of truth.

## 1. Truth lock

Use these facts consistently. Do not strengthen them in the portal unless new evidence lands first.

- Company/product: **Curren**
- Category: **verifiable decision intelligence for financial markets — crypto first**
- One-liner: **Curren turns market decisions into verifiable, machine-readable trading intelligence.**
- Founder: **Sang Truong**, solo technical founder based in Vietnam
- Stage: **pre-revenue; no meaningful customer/user traction yet**
- Legal status: **unincorporated**
- Formal Seed round raised: **no**
- Public product: **v0.4 alpha**
- Public investor demo: **https://curren.tech/investors**
- Investor-demo truth boundaries: clearly labeled demonstration/fixture data; no profitability claim; public live-feed integration remains pending
- Public platform/runtime truth: current public API/CLI/MCP and sanitized decision model exist, but production signal publication is not active end to end yet
- Native research truth: current representative V9 Stage-A campaign completed 88/88 trials with zero representative survivors and no retuning; do not claim proven profitable native alpha
- Existing Base implementation: **not yet shipped**
- Base commitment: founder has approved Base as the default chain/network for Curren's first onchain product surface. Interoperability may be added later, but Base is the default implementation choice for this wedge.

The public repo authority for current product state is `docs/PROJECT_STATUS.md`. Do not call the canonical API or landing replica a live signal feed until the production publication path is actually verified end to end.

## 2. Why Curren is a credible Base-first company

Base Batches 004 explicitly targets early teams in trading, payments, agents, financing, and asset issuance, and says teams do not need to be fully live on Base yet if Base is their primary/default network.

Curren's strongest Base-native wedge sits at the intersection of **trading + agents + payments**:

### Base Decision Receipts

Each Curren decision already has an original record, timestamp/provenance, lifecycle updates, terminal outcome, and verification semantics. The Base-native extension is to commit a bounded decision receipt on Base before the outcome is known, then append lifecycle/outcome receipts later.

The onchain receipt should contain only bounded public proof material, for example:

- decision/publication identifier;
- schema/version;
- commitment/hash of the immutable initial record;
- publication timestamp;
- lifecycle/outcome commitment references;
- optional publisher identity/namespace.

It should **not** put private strategy internals, private source messages, exchange credentials, or sensitive execution state onchain.

### Agent-native paid access on Base

Curren API/MCP already exposes read-only machine-consumable decision intelligence. The second Base-native surface is Base/USDC-native metered access for software agents, with x402-style payment/access rails where technically and commercially appropriate.

This gives an agent a coherent path:

`discover decision intelligence -> pay for bounded access -> consume API/MCP record -> verify decision receipt on Base`

### Default-network commitment

For the first onchain product surface, Base is the default network of choice for:

1. decision/provenance receipts;
2. agent-native payment/access experiments;
3. public verification UX built around those receipts.

Other-chain interoperability may be added later if customer evidence requires it, but it should not replace Base as the default implementation during this wedge.

## 3. What exists today vs what is planned

### Implemented today

- point-in-time research and explicit OOS/rejection discipline;
- private live ingestion/lifecycle/distribution runtime;
- read-only public FastAPI contract;
- Python client + CLI;
- read-only MCP server;
- sanitized publication read model;
- immutable initial publication records/hashes;
- append-only lifecycle events;
- terminal outcome/results projections;
- replay/stale-update protection;
- entitlement views;
- investor-facing deterministic demo at https://curren.tech/investors.

### Not implemented yet

- no Base smart contract is currently claimed;
- no Base decision receipt is currently claimed;
- no x402/USDC paid API path is currently claimed;
- no token is required or claimed;
- public live signal publication is not yet active end to end.

This distinction is mandatory in the application and video.

## 4. Core application answers

These are reusable answers for likely written fields. Match the portal's exact character limits when copying them; do not change the facts.

### Company name

Curren

### Website / demo

https://curren.tech/investors

### One-liner

Curren turns market decisions into verifiable, machine-readable trading intelligence.

### Short description

Curren turns each market decision into a durable record: what was recommended before the move, the evidence and provenance available at that time, lifecycle updates, and the terminal outcome. Humans consume that state through Curren Pro; trading teams and software agents consume the same bounded state through a read-only API and MCP interface. Crypto is the beachhead.

### Problem

Markets already have abundant data, dashboards, alerts, and AI commentary. The harder problem is trust after a decision leaves the model or analyst: what was actually recommended before the move, what changed later, whether the original plan was edited, and what the final outcome was. Humans reconstruct this manually; software agents need explicit machine-readable state, provenance, timestamps, and outcomes.

### Solution

Curren makes the market decision itself a durable object. Each record preserves the original thesis/setup, publication time and provenance, bounded context, entry/invalidation/target/expiry rules, append-only lifecycle changes, terminal outcome, and verification. The same bounded state is available to humans through Curren Pro and to trading teams/agents through Curren API/MCP. Execution remains separately authorized rather than bundled into the public intelligence product.

### Why now

AI agents are moving from reading information to continuously acting on structured financial context. As that happens, screenshots and mutable narrative feeds stop being enough: automated consumers need explicit state, provenance, permissions, replay safety, and outcomes. Crypto is the fastest beachhead because it is 24/7, programmable, and already combines human traders, bots, APIs, and agent workflows.

### Who is the initial customer?

The primary initial buyer is a small crypto trading team or builder of trading/financial agents that already runs automated or semi-automated workflows. These teams often monitor multiple feeds, parse messages, reconstruct lifecycle state, and evaluate sources manually. Serious active traders are a secondary validation/distribution market through Curren Pro.

### Business model

Curren Intelligence is one product with two initial commercial surfaces: Curren Pro, a subscription interface for humans, and Curren API, machine/team entitlement for agents and automated workflows. Curren is currently pre-revenue; pricing and packaging remain hypotheses until willingness to pay is observed.

### What is already built?

Curren already has a point-in-time research workflow, a private live lifecycle runtime, and a public v0.4 alpha developer platform with a read-only API, Python client, CLI, MCP server, immutable initial records, append-only lifecycle events, terminal outcomes, verification primitives, replay protection, and sanitized public read models. The investor demo is live at https://curren.tech/investors using clearly labeled demonstration data. Production public signal publication is not yet active end to end, and Curren does not claim a proven profitable native alpha strategy.

### Traction

Curren is pre-revenue and does not yet have meaningful customer/user traction. The current evidence is product and engineering velocity rather than commercial adoption. The next milestone is to recruit focused design partners, connect the existing private runtime to the public product end to end, and validate willingness to pay for Pro vs API workflows.

### Founder / founder-market fit

Sang Truong is the solo technical founder of Curren and currently leads AI engineering at EPIC TECHNOLOGY. He has more than six years of hands-on experience across applied AI, agentic/LLM systems, backend/frontend, data, infrastructure, evaluation, safety boundaries, and auditability. He has built Curren end to end across research, live runtime, public API/CLI/MCP, access rails, and product surfaces. He holds a Master of Engineering in Computer Engineering from the University of Arkansas with a 4.0/4.0 GPA.

Do not claim a completed PhD, institutional trading track record, or unsupported company-scale impact.

### Why Base?

Curren's product is fundamentally about making financial decisions trustworthy to both humans and software agents. Base is a strong default network for the first onchain extension because it is focused on global onchain finance and agent-native financial infrastructure, while Base Batches 004 explicitly prioritizes trading and agents. Curren plans to use Base for bounded decision/provenance receipts and for agent-native Base/USDC payment/access experiments around its API/MCP surface. Base will be the default network for this first onchain wedge; interoperability can come later without changing that default.

### What will be built on Base?

The first Base-native surface is **Base Decision Receipts**: a bounded onchain commitment for the initial decision record before the outcome, followed by lifecycle/outcome receipt references. This makes the before-the-move provenance externally verifiable without putting private strategy data onchain. The second surface is agent-native paid access to Curren API/MCP using Base/USDC and x402-style rails where appropriate. Neither surface is claimed as shipped today.

### Why does this need a chain?

The core intelligence product can operate offchain, but the trust problem improves when a bounded commitment to the initial decision exists on a neutral, independently verifiable timestamped network before the outcome is known. Base provides that public verification layer while keeping the detailed intelligence and private strategy state offchain. The chain is used for provenance/receipts and payment/access rails, not as a reason to force every product component onchain.

### Why Base-first rather than chain-agnostic?

For this product wedge, concentration is more valuable than superficial multi-chain coverage. Curren will make Base the default network for decision receipts and agent-native payment/access experiments, build the verification UX around Base first, and only add other chains when customer evidence justifies the maintenance cost. This is a genuine implementation choice rather than application-only branding.

### Current chain status

Curren is not yet live on Base. The existing product is a v0.4 alpha public developer platform plus private live runtime. The founder has committed to making Base the default network for the first onchain decision-receipt/payment wedge. Do not state that a Base contract, Base mainnet deployment, or x402 production path exists until the corresponding source and deployment evidence land.

### Competitive differentiation

Curren is not trying to be a generic crypto data API, AI chatbot, or black-box signal service. The product is the decision lifecycle itself: ex-ante thesis/setup, provenance, append-only changes, outcome, and verification. The intended compounding asset is a longitudinal dataset of decisions captured before outcomes are known, plus their evidence, lifecycle, outcomes, regimes, and consumer behavior.

### Fundraising / financing status

Curren has not raised a formal Seed round. It is currently unincorporated and pre-revenue. For direct VC fundraising outside programs, the working target is US$500,000 on a post-money SAFE with an US$8,000,000 post-money cap, but Base Batches program terms should supersede this if selected.

## 5. Base Batches 8-week execution plan

This is a proposed program plan, not a claim of completed work.

### Weeks 1-2 — decision receipt primitive

- finalize the public receipt schema and privacy boundary;
- implement a minimal Base testnet contract or equivalent Base-native receipt primitive;
- anchor fixture/sample decision commitments;
- add deterministic verification tests and a simple receipt verifier.

### Weeks 3-4 — agent access rail

- prototype Base/USDC metered access for read-only API/MCP usage;
- evaluate x402-compatible request/payment flow;
- keep entitlements and execution authorization separate;
- measure developer friction and transaction economics.

### Weeks 5-6 — product integration

- add Base receipt verification to Curren Pro/investor demo UX;
- expose Base receipt references in bounded API/MCP responses;
- onboard a small number of design partners for workflow feedback without inventing traction targets.

### Weeks 7-8 — validation and fundraising readiness

- evaluate which receipt/payment workflow customers actually value;
- tighten pricing/packaging based on observed usage;
- publish transparent proof including failures/no-trades rather than cherry-picked outcomes;
- prepare a repeatable investor/customer story around verified market-decision infrastructure.

## 6. Founder video — Base-tailored version

Target roughly 70-90 seconds unless the portal specifies another limit.

> Hi, I'm Sang, the solo founder of Curren, based in Vietnam.
>
> Markets already have more data, alerts, and AI commentary than anyone can follow. The harder problem is trust: what was actually recommended before the move, what changed afterward, and what the final outcome was.
>
> Curren turns market decisions into verifiable, machine-readable trading intelligence. Each decision becomes a durable record with its original thesis, timestamp, provenance, lifecycle updates, and terminal outcome. Humans use Curren Pro, while trading teams and software agents can consume the same bounded state through a read-only API and MCP interface.
>
> I already have the core research, private live lifecycle runtime, and public v0.4 alpha platform working. Curren is pre-revenue, and the public live feed is not yet active end to end.
>
> For Base, I'm making the first onchain product wedge Base-first: decision receipts committed before outcomes, plus Base-native payment and access experiments for agent consumers. I haven't shipped that Base layer yet, so I'm applying with a concrete implementation plan rather than pretending it already exists.
>
> I want Curren to make trustworthy market decisions usable infrastructure for both humans and autonomous financial software.

Recording rules:

- speak plainly on camera;
- no return/win-rate claims;
- no fake user/revenue numbers;
- do not say Base integration is live;
- if showing product footage, use https://curren.tech/investors and keep its **DEMONSTRATION DATA · NOT LIVE** labeling visible.

## 7. Submission checklist

Before opening the live application:

- [x] Base-first founder decision approved
- [x] Current Base Batches 004 deadline/eligibility rechecked against official Base pages on 2026-09-08
- [x] Written answer bank prepared offline
- [x] Investor demo URL accepted: https://curren.tech/investors
- [x] Truth boundaries reconciled to current `docs/PROJECT_STATUS.md`
- [x] Base-native product wedge defined without claiming implementation
- [ ] Founder records/uploads required video
- [ ] Exact live form labels/character limits are reconciled while copying answers
- [ ] Founder reviews any legal/consent/investment acknowledgements presented by the portal
- [ ] Authenticated final submission completed before the September 9 deadline

## 8. Final fail-closed rules

Do not submit wording that says any of the following unless new evidence lands first:

- "live on Base";
- "deployed Base contract";
- "x402 payments are live";
- "profitable alpha";
- "live public signal feed";
- meaningful user/customer traction;
- revenue;
- partnerships or institutional usage;
- incorporation in a jurisdiction that has not actually occurred.

The strongest truthful story is: **a technically substantial pre-revenue decision-intelligence platform, a verified investor demo, a founder-approved Base-first wedge that directly uses Base for decision provenance and agent-native access, and a concrete implementation plan that does not pretend the Base layer is already shipped.**
