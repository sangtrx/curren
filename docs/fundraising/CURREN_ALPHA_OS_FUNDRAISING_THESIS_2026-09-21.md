# Curren Fundraising Thesis — Alpha OS

Canonical for new fundraising/application copy from: 2026-09-21
Workflow authority: `sangtrx/sang-workspace#861`
Product thesis: `docs/PRODUCT_THESIS.md`

**DO NOT OVERENGINEER.**

## Canonical positioning

**Curren turns market hypotheses into validated, deployable alpha — for traders and AI agents.**

Long-term: **the operating system where humans and AI agents discover, validate, deploy, distribute and monetize trading alpha.**

Crypto is the first market because it is 24/7, programmable and already combines retail traders, research communities, APIs, bots and autonomous workflows.

## Problem by user maturity

### Retail trader

Retail traders do not want another research terminal. They want an actionable entry, invalidation/stop, targets and lifecycle they can follow without repeatedly reconstructing the market thesis themselves.

### Experienced trader / researcher

More experienced traders often have hypotheses but lack the data engineering, point-in-time controls, statistical validation, cost modeling and deployment infrastructure to turn an idea into evidence-backed alpha.

### Quant team / AI agent

AI can generate many hypotheses, but unconstrained search mostly generates selection bias and attractive backtests. Agent-native research needs bounded search, point-in-time data, explicit baselines, retained failures, multiplicity-aware statistics and promotion gates.

## Product

Curren connects these users through one system:

```text
hypothesis
  -> formal research specification
  -> PIT-safe evidence + bounded experiment
  -> falsification / robustness / cost gates
  -> Alpha Registry
  -> retail signal | team/API | agent | paper/live deployment
  -> prospective lifecycle + outcome
  -> durable evidence history
```

Current stack evidence:

- `curren-research`: scientific Alpha Factory with PIT/OOS/falsification/failure-retention contracts.
- `woodsbot-system`: live signal/lifecycle/distribution runtime and separately gated execution lane.
- `curren`: public API/CLI/MCP + sanitized immutable decision/outcome read model.
- `curren-access`: membership/payment/access infrastructure.
- `curren-landing-page`: investor/customer demo surface.
- `curren-social-factory`: acquisition engine.
- `curren-tradingview`: commercial trader-facing chart/product surface.

## Commercial wedge

Near-term primary validation is **not** 'build every layer'. It is:

1. dogfood the Alpha Factory into Curren's own prospective distribution/runtime;
2. recruit design partners who bring real hypotheses;
3. run a bounded hypothesis-to-alpha workflow;
4. convert at least the useful workflow into a paid Research Pro / Team/API pilot;
5. only then expand the agent-native surface and marketplace.

Curren Signals/Pro remains the retail distribution product. Research Pro / Team/API is the primary near-term higher-value validation. Agent-native Alpha Factory is the scale layer.

## Moat

The moat is not 'we have MCP' or 'we hash signals'. The intended moat is the longitudinal dataset and workflow captured **before outcomes are known**:

`hypothesis + ex-ante evidence + experiment lineage + lifecycle + outcome + regime/context + downstream usage`.

That history can improve source evaluation, strategy calibration, model selection, agent routing, risk gates and future research while preserving private-by-default ownership.

## User-alpha ownership

Private user hypotheses and strategy logic are private by default. Curren does not silently appropriate user alpha.

Future contribution modes may include:

- private: user-only research/deployment;
- explicit contribution: opt-in bounded evidence sharing for credits/benefits;
- marketplace: creator voluntarily publishes validated alpha and receives an explicit revenue share.

Do not describe any marketplace or revenue-sharing feature as shipped until it is actually implemented.

## Current truth lock

- Founder: Sang Truong, solo technical founder in Vietnam.
- Stage: pre-revenue; no meaningful customer/user traction yet unless new evidence is recorded.
- Legal status: unincorporated unless later changed by explicit legal evidence.
- Direct VC working raise: US$500,000.
- Working direct-VC instrument: post-money SAFE.
- Working direct-VC cap: US$8,000,000 post-money unless a program imposes its own terms.
- Public platform remains alpha and must not be described as a production-live public feed until separately verified.
- Do not claim a profitable native alpha strategy. Failed/rejected research is retained as evidence.

## Accelerator / investor framing

### YZi Labs EASY Residency S5

Lead with **trusted agentic market infrastructure**: humans or agents propose hypotheses; Curren applies point-in-time scientific validation; surviving strategies can become machine-readable decisions and later separately authorized execution. This maps naturally to YZi's current focus on programmable capital, markets, trusted agent systems and accountability.

Current official S5 deadline: Sept 21 at 23:59 GMT-7. Current program page says up to US$500K: US$150K for 5% via SAFE plus an additional US$350K on an uncapped SAFE. Re-read the live terms at submission/signing time.

### Alliance ALL19

Lead with **crypto-native Alpha OS** and founder velocity: one system from hypothesis → validation → distribution, with agent scale and explicit private-alpha ownership. Do not over-center 'verifiable decision intelligence' as an abstract category.

Current official Alliance page: US$500K funding at a US$5M post-money valuation via SAFE with a 1:1 token side letter; early deadline Sept 23; ALL19 starts Jan 11, 2027. Re-read immediately before submission/signing.

### PearX W27

Lead with the customer-learning loop: trader brings hypothesis → Curren produces rigorous evidence → useful strategy is paper/deployed → customer pays for repeated workflow. Make first paid design partners the milestone, not additional architecture.

Current official regular deadline: Oct 4 at 11:59 PM PST.

### YC Winter 2027

Use the simplest language: experienced traders have ideas but turning them into trustworthy strategies is hard; Curren automates the research-to-deployment loop, while retail traders consume the strategies that survive. Show usage/customer learning before technical depth.

Current official on-time deadline: Nov 2 at 8 PM PT.

### Base

Batch 004 is closed. Do not pretend Batch 005 dates exist until Base publishes them. A future Base-native application is valid only if Curren has a real Base-first product path; the Alpha OS story can emphasize agent/trading infrastructure but must not bolt on a fake chain thesis.

### Vietnam / SEA seed VC

Lead with a Vietnam-built AI/fintech infrastructure company with a concrete commercial wedge:

- first product proof: Curren dogfoods its own Alpha Factory;
- buyer: small trading teams / serious researchers / financial-agent builders;
- paid workflow: hypothesis-to-alpha research + API/team consumption;
- retail distribution: signals/pro surface;
- expansion: agent-native discovery and opt-in execution.

Do not make investors infer the buyer from a generic 'decision intelligence' category.

## Main-deck narrative

Recommended order:

1. User problem across retail → researcher → agent.
2. One Alpha OS linking those jobs.
3. Product demo: one hypothesis through evidence to a deployable decision.
4. Why now: AI makes hypothesis generation abundant; rigorous validation becomes scarce.
5. Current stack / dogfood proof.
6. Commercial wedge and first paid design partners.
7. Alpha ownership / trust model.
8. Moat and compounding evidence flywheel.
9. Roadmap: retail distribution → Research Pro/Team → agent-native factory → separately gated execution.
10. Founder + raise.

Research failures such as the historical 88/88 representative campaign with zero survivors may be used as diligence evidence for falsification discipline, but should not dominate the main commercial story.

## Supersession

This file supersedes the **positioning** in the 2026-09-07 seed-deck source and 2026-09-08 fundraising packets for new applications. Those dated files remain historical evidence and should not be silently rewritten into a false contemporaneous state.