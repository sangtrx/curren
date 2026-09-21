# Curren — Alliance ALL19 Application Packet

Last reconciled: 2026-09-21
Owner issue: `sangtrx/sang-workspace#69`; thesis migration: `sangtrx/sang-workspace#861`

This is the source-controlled review packet for Curren's Alliance ALL19 application. It must stay consistent with `docs/PROJECT_STATUS.md`, the 2026-09-21 Alpha OS fundraising thesis, GitHub Issues, and the live Alliance application/terms.

## Authority and submission guardrails

- Live Alliance application: `https://alliance.xyz/apply`
- Early admission deadline: **2026-09-23**
- Regular admission deadline: **2026-11-18**
- ALL19 starts: **2027-01-11**
- Current official economics, rechecked 2026-09-21: **$500K at a $5M post-money valuation via SAFE + 1:1 token side letter**. Recheck immediately before submission/signing because program terms can change.
- Recheck economics immediately before submission and before signing. Alliance has changed its published terms across recent cohorts.
- Current form publicly exposes only the first founder-email step before the applicant proceeds and agrees to application-status email communications. Do not infer that the downstream form is unchanged.
- The field map below is based on the current live entry step plus Alliance's longstanding application schema visible in prior public application captures/rehosts. Recheck every downstream label/required flag after entering the live form.
- Do not submit automatically, sign investment documents, or create legal/financial facts that are not already known.

## Current source truth

- Company/product: **Curren**
- Company thesis: **Alpha OS for traders and AI agents — crypto first**
- One-liner: **Curren turns market hypotheses into validated, deployable alpha — for traders and AI agents.**
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

**AI alpha factory for traders & agents**

### What is the problem that you're solving?

Trading has three versions of the same bottleneck. Retail traders want a clear entry, invalidation and targets without rebuilding the analysis every time. More experienced traders have market hypotheses but usually do not have the point-in-time data, statistical controls, cost modeling and deployment infrastructure to test them rigorously. AI agents can generate hypotheses at massive scale, but without strict search budgets and validation they mostly scale overfitting.

Curren's thesis is that hypothesis generation is becoming cheap while trustworthy alpha validation remains scarce. Curren turns a human or agent hypothesis into a formal, bounded research program, rejects weak ideas, promotes only what survives, and makes accepted decisions consumable by traders and software.

### Expand on the product that you're building

Curren is building an Alpha OS with one engine and three user surfaces.

**Retail / Signals / Pro:** accepted decisions become clear entry, stop/invalidation, targets and lifecycle so a trader can act with less repeated analysis.

**Research Pro / Team:** a trader brings a hypothesis; Curren formalizes it, constructs point-in-time evidence, runs bounded cost-aware experiments, compares baselines and robustness gates, explains failure/survival, and produces a deployable artifact only when the evidence survives.

**Agent-native Alpha Factory:** humans or AI agents can generate hypotheses at scale, but the same finite-search, point-in-time and failure-retention rules prevent the system from becoming a backtest-optimization machine.

Underneath this product, Curren separates scientific research, live decision/lifecycle processing, sanitized publication and execution authority. The public developer platform is alpha; the live public publication path is not claimed active until separately verified. User hypotheses and strategy logic are private by default.

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

I completed a Master of Science in Computer Engineering at the University of Arkansas with a 4.0/4.0 GPA. With Curren, I have built across the research, private live runtime, public API/CLI/MCP, publication, and product boundaries myself.

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

I started building the current Curren product in **August 2026** after working on crypto signal, trading and research systems and seeing two sides of the same problem. Retail users want actionable decisions instead of another research burden, while serious traders can have good market hypotheses but still lack the infrastructure to test them without leakage, cherry-picking or unrealistic execution assumptions.

As I added AI agents to the research process, the problem became sharper: generating hypotheses became easy, but making large-scale search scientifically honest became the hard part. That pushed Curren toward one Alpha OS: hypothesis → bounded evidence → accepted strategy → distribution/deployment → prospective outcome.

### What is your unfair advantage in solving this problem?

My advantage is that I have already built across the full boundary myself: point-in-time quantitative research and falsification, live signal/lifecycle processing, AI quality gates, public API/CLI/MCP, access/payment rails, distribution and separately gated execution architecture.

That lets Curren dogfood the same research-to-alpha workflow it intends to sell. The longer-term compounding asset is not a secret indicator; it is the pre-outcome history of hypothesis + evidence + experiment lineage + lifecycle + outcome + regime/context + downstream usage, accumulated under explicit ownership rules.

### What other companies are solving this problem today or could if they wanted to? Why will you succeed against them?

Adjacent products include strategy builders/backtest platforms, market-data terminals, copy/signal products, quant infrastructure and AI trading agents. Some can generate strategy code quickly; others have strong execution or data breadth.

Curren is differentiated by treating **alpha discovery and scientific validation as one bounded system** rather than stopping at code generation or a visually attractive backtest. The workflow preserves point-in-time inputs, explicit baselines, finite search budgets, costs, retained failures and prospective outcomes. The same accepted alpha can then serve retail, team/API and agent consumers.

Curren does not need every user strategy to become Curren property. Private user hypotheses stay private by default; future contribution/marketplace modes require explicit opt-in.

### What does your founding team believe in that very few people agree with you on?

AI will make market-hypothesis generation abundant. That does **not** make durable alpha abundant; it makes research discipline more valuable.

I believe the winning infrastructure is not the model that can generate the most strategies or the backtest with the highest-looking Sharpe. It is the system that can let humans and agents search broadly while preserving point-in-time evidence, finite opportunity budgets, failures, costs and prospective truth — and then route the survivors into products people can actually use.

### What's your current traction?

Pre-revenue and no meaningful customer/user traction yet.

The strongest current evidence is technical execution rather than commercial usage: Curren's public developer platform is v0.4 alpha with read-only API/CLI/MCP surfaces, immutable initial/terminal records, append-only lifecycle and verification/replay protection; the private runtime implements live evaluation/lifecycle workflows; and the point-in-time research stack is operational. The latest frozen representative research campaign completed all 88 planned trials and promoted zero survivors with no retuning.

The next milestone is not to manufacture a traction number; it is to activate one bounded production publication path, verify it end to end, and convert focused design-partner conversations into willingness-to-pay evidence.

### Large recognizable customers

**None.** Curren is pre-revenue and does not have a large recognizable customer or formal customer commitment to claim.

### What unique insights do you have about your users?

Curren does **not** yet claim validated insight from a meaningful paying-user base. The working segmentation is explicit and testable:

- retail traders want less analysis burden and clearer entry/exit/risk decisions;
- experienced traders want to turn their own market hypotheses into rigorously tested strategies without assembling a full quant stack;
- agent builders need machine-readable research and decision primitives that can scale hypothesis generation without silently scaling selection bias.

The immediate customer-learning objective is to test the second segment through paid hypothesis-to-alpha design partners while Curren dogfoods the first segment itself.

### What's your distribution strategy?

Start with a founder-led loop rather than a broad consumer launch:

**dogfood Alpha Factory → publish prospective signal/lifecycle evidence → recruit a trader/team with a real hypothesis → run a bounded Research Pro / Team pilot → charge for repeated workflow → productize the repeatable interface.**

Retail Signals/Pro remains a distribution surface and evidence generator. Technical communities around trading automation and financial agents are the initial B2B/design-partner pool. The agent-native API expands only after the human research workflow demonstrates value.

### How big could your product become?

The initial wedge is crypto because it is 24/7, programmable and already mixes human traders, APIs and bots. If the workflow works, Curren can become an Alpha OS where humans and AI agents discover, validate, deploy and optionally monetize systematic trading strategies across more markets.

The platform can expand from retail signal distribution and Research Pro / Team into an agent-native Alpha Factory, strategy registry/marketplace with explicit creator ownership, and separately authorized non-custodial execution. Those later layers are roadmap, not current shipped claims.

### If you failed five years from now, why?

The biggest product risk is that buyers may agree provenance is useful but still pay almost entirely for raw alpha, execution, or broad data rather than for trustworthy decision lifecycle. A second risk is that Curren may fail to produce or aggregate intelligence valuable enough for the verification layer to matter. A third is founder/GTM concentration: as a solo technical founder, I can build quickly but could underinvest in distribution if I do not force customer discovery early.

I would rather test those risks directly now than hide them behind engagement or backtest metrics.

### Fundraising history and future plans

Curren has not raised a formal institutional round. Outside a program with fixed terms, the current direct-VC working plan is to raise **US$500K** via a post-money SAFE at a working **US$8M post-money cap**.

For Alliance, current official program economics override the generic plan: **US$500K at a US$5M post-money valuation via SAFE + 1:1 token side letter**, rechecked 2026-09-21. Re-read the live terms immediately before submission and again before signing.

### Investment track — only if ALL19 still asks this

Choose the **standard early-stage / admission deal** unless the current live form presents materially different options. Curren is early, pre-revenue, and has no reason to claim a later-stage exception.

### How did you first hear about Alliance?

**UNRESOLVED PORTAL CHOICE.** Select the truthful source from the live form. Do not guess for optimization.

### Why are you applying to Alliance? What help are you looking for?

I can build the full stack, but the current bottleneck is commercial learning rather than more architecture. I want to turn Curren's Alpha Factory into one workflow that real traders and small teams repeatedly pay for: bring a hypothesis, receive rigorous evidence, deploy only if it survives, and then consume the same accepted decision through human or machine interfaces.

Alliance is unusually relevant because it is crypto/fintech-native, accepts deeply technical teams before revenue, and can pressure-test product, distribution and fundraising. I also want a founder community that understands trading infrastructure and autonomous financial software, so Curren can grow beyond a small signal subscription without pretending it already has PMF.

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