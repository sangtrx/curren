# Curren — Alliance ALL19 Application Packet

Last reconciled: 2026-09-08
Owner issue: SAN-54

This is the source-controlled review packet for Curren's Alliance ALL19 application. It must stay consistent with `docs/PROJECT_STATUS.md`, the reusable Curren fundraising packet in Linear, and the live Alliance application/terms.

## Authority and submission guardrails

- Live Alliance application: `https://alliance.xyz/apply`
- Early admission deadline: **2026-09-23**
- Regular admission deadline: **2026-11-18**
- ALL19 starts: **2027-01-11**
- Current live economics, rechecked 2026-09-08: **$400K upon admission at a $4M post-money valuation via SAFE + 1:1 token side letter**; Alliance's homepage separately advertises a **$400K follow-on at seed**.
- Recheck economics immediately before submission and before signing. Alliance has changed its published terms across recent cohorts.
- Current form publicly exposes only the first founder-email step before the applicant proceeds and agrees to application-status email communications. Do not infer that the downstream form is unchanged.
- The field map below is based on the current live entry step plus Alliance's longstanding application schema visible in prior public application captures/rehosts. Recheck every downstream label/required flag after entering the live form.
- Do not submit automatically, sign investment documents, or create legal/financial facts that are not already known.

## Current source truth

- Company/product: **Curren**
- Category: **verifiable decision intelligence for financial markets — crypto first**
- One-liner: **Curren turns market decisions into verifiable, machine-readable trading intelligence.**
- Founder: **Sang Truong**, solo technical founder in Vietnam
- Current professional role: **Head of Artificial Intelligence at EPIC TECHNOLOGY**
- Founder LinkedIn: `https://linkedin.com/in/tqsang`
- Fundraising email: `tqsang97@gmail.com`
- Fundraising phone: `+84582332694`
- Website: `https://curren.tech/`
- Canonical company X: `https://x.com/Currenlabs`
- Public developer repo: `https://github.com/sangtrx/curren`
- Stage: **pre-revenue; no meaningful customer/user traction yet**
- Legal status: **unincorporated**
- Current full-time team-member count: **1**
- Direct VC working raise outside fixed accelerator terms: **US$500K** via post-money SAFE at a working **US$8M post-money cap**
- Alliance logistics: founder is willing/able to attend the 2-week NYC onboarding, return for Demo Day, and transition to Curren full-time if accepted/funded.
- Public platform: v0.4 alpha with read-only API, Python client, CLI, six MCP tools, entitlements, immutable initial/terminal records, append-only lifecycle, verification, and replay protection.
- Public-feed truth: sanitized Supabase replica, publisher bridge, and source-side projector exist, but production publication is still disabled/not verified end to end; the replica had zero production signal rows at the latest checkpoint. **Do not claim a live public feed or live canonical API.**
- Research truth: evidence-first point-in-time workflow; latest frozen representative Stage-A campaign completed **88/88 trials with zero representative survivors and no retuning**. **Do not claim proven profitable native alpha.**

## Confirmed live first step

### Email (1st Founder) *

`tqsang97@gmail.com`

Note: proceeding from this step carries an application-status email communication consent. Do not advance on Sang's behalf merely to inspect fields.

## Working downstream field map

The labels below have appeared consistently in Alliance's historical application form. Treat them as prepared answers, not proof that ALL19 uses identical wording/order.

### Company name

**Curren**

### Website URL

`https://curren.tech/`

### Company Twitter / X URL

`https://x.com/Currenlabs`

### What are you building? — short field

**Verifiable trading decision intelligence**

### What is the problem that you're solving?

Crypto trading intelligence is abundant but difficult to trust. Signals and AI-generated market opinions often live in chats, screenshots, and mutable APIs, so a trader or software agent may not know what the original plan actually was, whether it changed after the fact, or whether historical performance was selected after outcomes were known.

Curren's thesis is that provenance, lifecycle state, and permission boundaries should be part of the market-intelligence product itself. A useful decision should be captured before the outcome, updated append-only through its lifecycle, resolved transparently, and exposed in a form both humans and software can verify.

### Expand on the product that you're building

Curren turns each market decision into a durable, machine-readable object: original thesis/setup, publication time and provenance, lifecycle updates, invalidation/targets, terminal outcome, and verification. Humans are intended to consume the same bounded decision state through Curren Pro that trading teams and software agents consume through Curren's read-only API, Python client, CLI, and MCP interface.

Under the product, Curren separates point-in-time research, private live evaluation/lifecycle processing, sanitized publication, and execution authority. The public developer platform is already v0.4 alpha. A sanitized landing replica and publication path are implemented, but production publication is still disabled/not yet verified end to end, so Curren does not claim a live public feed today.

### Founder video — optional if the live form still makes it optional

**Prepared but not uploaded.** Use the current 60-second Alliance founder script from the Linear application-drafts document. Do not block submission solely on this artifact if the live ALL19 form confirms it remains optional.

### Demo — optional if the live form still makes it optional

Preferred once SAN-119 is explicitly approved, deployed, and publicly verified: `https://curren.tech/investors`

Until that happens, **do not use `/investors` as a live demo URL**. The public developer source may be referenced separately: `https://github.com/sangtrx/curren`.

### Where are the founders located?

**Asia — Vietnam**

### First Name (1st Founder)

**Sang**

### Last Name (1st Founder)

**Truong**

### Role (1st Founder)

**Founder / Engineer**

### LinkedIn URL (1st Founder)

`https://linkedin.com/in/tqsang`

### Personal Twitter / X URL (1st Founder)

**UNRESOLVED — do not substitute the company X account unless the live form explicitly accepts a company profile here.**

### Email (1st Founder)

`tqsang97@gmail.com`

### Summarize your professional and academic background

I am an AI engineering lead and solo technical founder based in Vietnam. I currently lead AI at EPIC TECHNOLOGY and have more than six years of hands-on experience across applied AI, backend/data systems, architecture, infrastructure, and user-facing products. My recent work includes clinical decision-support systems, conversational and agentic AI, multimodal/video intelligence, and trading infrastructure.

I completed a Master of Engineering in Computer Engineering at the University of Arkansas with a 4.0/4.0 GPA. With Curren, I have built across the research, private live runtime, public API/CLI/MCP, publication, and product boundaries myself.

### Describe an instance where you demonstrated exceptional creativity or perseverance

While building Curren's research stack, I repeatedly found that attractive trading hypotheses became much weaker once I enforced point-in-time data, explicit out-of-sample gates, and no-retuning rules. Instead of relaxing those rules or cherry-picking a backtest, I rebuilt the workflow around preserving failures as evidence. In the latest frozen representative campaign, the system completed all 88 planned trials and promoted zero survivors, with no retuning.

I consider that result useful rather than embarrassing: it forced the product away from "trust this winning backtest" and toward a harder, more defensible problem — making every market decision verifiable from the moment it is made through its final outcome.

### Additional founders / when founders met

**Not applicable — solo founder.**

### Equity breakdown between founders

Curren is currently **unincorporated**, so there is no issued company equity or formal cap table yet. Sang is the sole founder; there is no co-founder equity split to report. Do not invent incorporation or issued-share details.

### What ecosystem are you building on?

Curren is **chain-agnostic / not dependent on a specific blockchain**. It starts with crypto market workflows and exposes read-only intelligence through standard API/CLI/MCP surfaces. If the form forces a listed ecosystem choice, use **Other** unless a genuinely shipped chain-specific product exists by submission time.

### Are all founders committed full-time to the startup?

Not yet. I currently lead AI at EPIC TECHNOLOGY while building Curren as a solo founder. If accepted/funded through Alliance, I am willing to transition to Curren full-time and commit fully to the program, including the New York onboarding and Demo Day.

### When did you start working on this idea and why did you choose it?

I started building the current Curren product in **August 2026**, after working on crypto signal, trading, and research systems and repeatedly hitting the same trust problem: it was easier to generate an opinion than to prove what was actually known and recommended before the market moved.

That pushed me to separate point-in-time research, live decisioning, publication, and execution, and to treat the decision lifecycle itself as a product object rather than another chat message or mutable dashboard row.

### What is your unfair advantage in solving this problem?

My advantage is being able to build and evaluate the full system boundary myself. I have spent more than six years across applied AI, backend/data engineering, architecture, infrastructure, and production reliability, and I have already implemented Curren across point-in-time research, private live lifecycle processing, public API/CLI/MCP access, immutable publication/outcome records, replay protection, and a separate execution authority boundary.

The moat I am pursuing is not a secret indicator. It is the accumulating evidence chain from ex-ante market decision + context through lifecycle + terminal outcome, plus the product and infrastructure discipline required to make that record trustworthy to both humans and autonomous software.

### What other companies are solving this problem today or could if they wanted to? Why will you succeed against them?

Several adjacent products could move into parts of this problem: market-data/analytics platforms, AI crypto-research products, trading terminals, social/copy-trading products, and agent-automation tools. Some Alliance portfolio companies also sit near the trading/automation boundary.

Curren is deliberately not trying to beat them on raw data breadth, chat UX, or trade execution. The product is designed around a narrower primitive that most adjacent systems treat as secondary: preserving the original decision before the outcome, append-only lifecycle state, immutable terminal resolution, and a permissioned machine-readable interface. If this becomes valuable, Curren's advantage compounds in the longitudinal dataset of ex-ante decision + evidence + lifecycle + outcome rather than in any single prediction model.

### What does your founding team believe in that very few people agree with you on?

The most valuable AI-trading product will not necessarily be the model that produces the highest-looking backtest. As models and market data become cheaper, the scarce layer will be **trustworthy decision state**: what was known, what was recommended before the move, what changed, what the system was authorized to do, and what ultimately happened.

I think preserving losers and rejected ideas can become more valuable than marketing only winners because autonomous financial software will need auditable evidence and calibrated trust, not screenshots of past success.

### What's your current traction?

Pre-revenue and no meaningful customer/user traction yet.

The strongest current evidence is technical execution rather than commercial usage: Curren's public developer platform is v0.4 alpha with read-only API/CLI/MCP surfaces, immutable initial/terminal records, append-only lifecycle and verification/replay protection; the private runtime implements live evaluation/lifecycle workflows; and the point-in-time research stack is operational. The latest frozen representative research campaign completed all 88 planned trials and promoted zero survivors with no retuning.

The next milestone is not to manufacture a traction number; it is to activate one bounded production publication path, verify it end to end, and convert focused design-partner conversations into willingness-to-pay evidence.

### Large recognizable customers

**None.** Curren is pre-revenue and does not have a large recognizable customer or formal customer commitment to claim.

### What unique insights do you have about your users?

Curren does **not** yet claim validated customer insight from a meaningful user base. The working product hypothesis is that small crypto trading teams and builders of financial/trading agents already spend effort reconstructing decisions across feeds, messages, and internal tools, while automated consumers need explicit state and provenance rather than narrative alone.

The next customer-discovery question is whether those users will pay first for a human Pro workflow or a machine/team API workflow. Alliance is attractive partly because its crypto-native founder network can pressure-test that assumption quickly.

### What's your distribution strategy?

Start with a narrow founder-led loop: **public proof/content -> product demo -> design partner -> paid validation -> repeatable workflow**.

The content itself should mirror the product: before-the-move setups, lifecycle updates, invalidation/loser autopsies, rejected/no-trade cases, regime notes, and API/agent demos. I would use those artifacts to reach small trading teams and financial-agent builders directly, then concentrate distribution around whichever Pro or API workflow shows real willingness to pay.

### How big could your product become?

The initial wedge is verifiable crypto market intelligence for humans and software agents. If the core primitive works, Curren can expand from a feed/API product into the trust and decision layer between market data, AI agents, and capital: permissioned decision state, team/agent workflows, provider/research reputation, evaluation history, and eventually separately authorized non-custodial execution where legal and product boundaries support it.

The long-term category is broader than signals: **decision provenance + lifecycle intelligence for autonomous financial software**. The value capture starts with Curren Pro and Curren API and can deepen as the ex-ante decision/evidence/outcome dataset compounds.

### If you failed five years from now, why?

The biggest product risk is that buyers may agree provenance is useful but still pay almost entirely for raw alpha, execution, or broad data rather than for trustworthy decision lifecycle. A second risk is that Curren may fail to produce or aggregate intelligence valuable enough for the verification layer to matter. A third is founder/GTM concentration: as a solo technical founder, I can build quickly but could underinvest in distribution if I do not force customer discovery early.

I would rather test those risks directly now than hide them behind engagement or backtest metrics.

### Fundraising history and future plans

Curren has **not raised external funding** and is currently **unincorporated**.

Outside a program with fixed terms, the current direct-VC working plan is to raise **US$500K** via a post-money SAFE at a working **US$8M post-money cap**. For Alliance, the program's current published standard economics override that generic plan: **$400K at a $4M post-money valuation via SAFE + 1:1 token side letter**, with the homepage separately advertising a **$400K seed follow-on**.

### Investment track — only if ALL19 still asks this

Choose the **standard early-stage / admission deal** unless the current live form presents materially different options. Curren is early, pre-revenue, and has no reason to claim a later-stage exception.

### How did you first hear about Alliance?

**UNRESOLVED PORTAL CHOICE.** Select the truthful source from the live form. Do not guess for optimization.

### Why are you applying to Alliance? What help are you looking for?

Alliance is one of the few accelerators where being pre-revenue, solo, and deeply technical is not something I need to disguise. I can build the system, but Curren's current bottleneck is product wedge and distribution: which trading-team or financial-agent workflow values provenance/lifecycle enough to pay, and how to turn that into a repeatable acquisition loop.

I want crypto-native pressure on product, GTM, and fundraising from people who understand trading infrastructure and early financial products. I also want a community that will push Curren toward a venture-scale decision-intelligence layer rather than a small signal-subscription business.

### Alliance member referral

**UNRESOLVED.** No referral is currently recorded in the canonical fundraising packet. Leave blank or answer "No" only after confirming there is no genuine Alliance member/founder referral to include.

## Review blockers and non-blockers

### Not blockers

- Curren is pre-revenue / low traction — Alliance explicitly accepts this stage.
- Solo founder — Alliance explicitly accepts solo founders.
- Founder video, if the current ALL19 form still labels it optional.
- Live `/investors` demo, if the current ALL19 form still labels demo optional; the GitHub developer surface can support technical diligence without pretending the production investor route is live.

### Must be rechecked in the live form before final submission

1. Every downstream ALL19 field label, required/optional flag, and character/word limit after the founder-email consent step.
2. Current economics immediately before submission and again before signing.
3. Whether a personal X profile is required.
4. The truthful "How did you hear about Alliance?" choice.
5. Whether there is a genuine Alliance member/founder referral.
6. Whether SAN-119 has been explicitly approved, deployed at the accepted SHA, and publicly verified before using `https://curren.tech/investors`.

## Final truth check

Do not claim:

- revenue, paying customers, meaningful user traction, partnerships, or investor commitments that do not exist;
- a live public signal feed while production publication is disabled/unverified;
- a live canonical `api.curren.tech` deployment unless independently verified;
- profitable native alpha or representative research survivors;
- incorporation, jurisdiction, issued equity, or a cap table before they exist;
- a chain-specific implementation that has not shipped;
- automatic/managed execution as part of the current public product.
