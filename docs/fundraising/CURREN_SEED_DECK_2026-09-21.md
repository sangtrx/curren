# Curren Seed Deck — v0.4 — 2026-09-21

Canonical investor-deck source for new Curren fundraising applications from 2026-09-21.

Workflow authority: `sangtrx/sang-workspace#861`
Product thesis: `docs/PRODUCT_THESIS.md`
Fundraising thesis: `docs/fundraising/CURREN_ALPHA_OS_FUNDRAISING_THESIS_2026-09-21.md`

## Truth lock

- Company thesis: **Curren turns market hypotheses into validated, deployable alpha — for traders and AI agents.**
- Long-term vision: **Alpha OS** for discovering, validating, deploying, distributing and monetizing trading alpha.
- Crypto first; broader financial markets only as a future category direction.
- Founder: Sang Truong, solo technical founder based in Vietnam.
- Stage: pre-revenue; no meaningful customer/user traction unless newer evidence is recorded.
- Legal status: unincorporated unless explicitly changed by legal evidence.
- Direct VC raise: US$500,000.
- Working direct-VC instrument: post-money SAFE.
- Working direct-VC cap: US$8,000,000 post-money unless a program sets its own terms.
- Public product remains alpha; do not claim a production-live public feed until end-to-end verified.
- No proven profitable native alpha strategy is claimed.
- User hypotheses/strategy logic are private by default; do not imply Curren appropriates private user alpha.

**DO NOT OVERENGINEER.**

---

## Slide 1 — Curren

### Turn market hypotheses into validated, deployable alpha

**Curren is building an Alpha OS for traders and AI agents.**

Crypto first · Vietnam · Pre-revenue · Solo technical founder

`curren.tech`

---

## Slide 2 — The users

### The same market creates three levels of research burden

**Retail traders** want a clear entry, invalidation/stop and targets without rebuilding the analysis every time.

**Experienced traders** have market hypotheses but often lack the data engineering, point-in-time controls, statistical validation, cost modeling and deployment infrastructure to test them rigorously.

**AI agents** can generate thousands of hypotheses, but unconstrained search can turn that abundance into selection bias and attractive backtests.

---

## Slide 3 — The product

### One engine: hypothesis → evidence → alpha → distribution

```text
human hypothesis OR agent hypothesis
                ↓
        Curren Alpha Factory
                ↓
 point-in-time validation + falsification
                ↓
          Alpha Registry
                ↓
 retail signals | team/API | agents
                ↓
      prospective lifecycle/outcome
```

Curren does not promote an idea merely because one backtest looks good.

---

## Slide 4 — Retail: Signals / Pro

### Good trading UX starts after the research is done

Retail users consume:

- entry;
- stop / invalidation;
- targets;
- lifecycle state;
- bounded context and history.

`woodsbot-system` is Curren's first live signal/lifecycle/distribution runtime and dogfood consumer.

The value proposition is **less repeated analysis and more disciplined execution**, not guaranteed returns.

---

## Slide 5 — Research Pro / Team

### Bring a hypothesis; Curren turns it into rigorous evidence

A design partner can bring an idea such as a price/funding/regime relationship.

Curren should:

1. formalize the hypothesis;
2. identify and freeze required data;
3. construct point-in-time features;
4. run bounded experiments;
5. model fees, slippage and funding;
6. compare against baselines/controls;
7. apply robustness and statistical gates;
8. explain why the idea failed or survived;
9. produce a deployable artifact only when accepted.

This is the primary near-term higher-value commercial validation.

---

## Slide 6 — Agent-native Alpha Factory

### Scale hypothesis generation without scaling p-hacking

Humans or AI agents may generate hypotheses at scale, but Curren keeps search finite, preregistered, point-in-time, multiplicity-aware and failure-retaining.

Agent-native research is a scale layer after the human workflow and evidence contracts work.

---

## Slide 7 — Alpha ownership

### Private by default

Private user hypotheses and strategy logic are not silently reused, distributed, sold or traded by Curren.

Future modes can be explicit:

- **Private** — user-only research/deployment.
- **Contribute** — explicit bounded opt-in to share evidence.
- **Marketplace** — creator voluntarily publishes validated alpha under explicit ownership and revenue-sharing terms.

Only Private is a current policy; do not present contribution/marketplace as shipped.

---

## Slide 8 — What is already built

### Strong technical foundation; commercial validation is the bottleneck

**Curren Research**
- point-in-time research contracts;
- finite hypothesis execution;
- OOS / purge / embargo / statistical diagnostics;
- retained failures and immutable evidence.

**Curren runtime**
- live source ingestion and normalization;
- signal construction + AI quality gate;
- lifecycle tracking and distribution;
- separately gated admin execution.

**Public/product stack**
- read-only API, Python client, CLI and MCP;
- immutable initial decision and terminal outcome records;
- access/payment infrastructure;
- investor/customer and social distribution surfaces.

---

## Slide 9 — Moat

### A longitudinal pre-outcome alpha record compounds

The intended moat is:

**hypothesis + ex-ante evidence + experiment lineage + lifecycle + outcome + regime/context + downstream usage**

That history can improve source evaluation, calibration, model selection, agent routing, risk gates and future research.

The moat is not a hash, MCP, API schema or one strategy by itself.

---

## Slide 10 — Go to market

### Dogfood first. Then get paid for the workflow.

```text
Curren Research
    ↓
accepted strategy / decision
    ↓
Woodsbot prospective distribution
    ↓
real lifecycle + outcome evidence
    ↓
design partner brings hypothesis
    ↓
Research Pro / Team pilot
    ↓
paid repeat usage
```

Signals remain retail distribution. Research Pro / Team is the primary paid-validation wedge. Agent-native research is the scale layer.

---

## Slide 11 — Evidence discipline

### Weak research is allowed to fail

Curren preserves failed candidates instead of hiding them.

A historical representative V9 campaign completed **88 / 88 trials with zero representative survivors and no retuning**.

That result is evidence of falsification discipline. It is **not** presented as profitable native alpha.

---

## Slide 12 — Founder + raise

### Sang Truong — solo technical founder

AI engineering lead and hands-on builder across agents/LLMs, quantitative research systems, backend/frontend, infrastructure, evaluation and auditability.

**Raise:** US$500,000

**Working direct-VC instrument:** post-money SAFE

**Working direct-VC cap:** US$8M post-money

Capital is intended to:

1. ship one end-to-end customer loop;
2. land paid hypothesis-to-alpha design partners;
3. strengthen prospective research/runtime evidence;
4. validate repeat willingness to pay for Research Pro / Team/API;
5. scale agent-native research only after the human workflow works;
6. hire after a real bottleneck is proven.

---

## Investor Q&A

### Are you a signal company?

Signals are the retail distribution layer and Curren's first dogfood consumer. The broader company turns hypotheses into validated, deployable alpha.

### Are you an AI trading bot?

No. Curren separates hypothesis generation, research validation, decision publication and execution authority. Agentic research is a product interface; execution remains separately gated.

### Why not just use an LLM to write a backtest?

Generating code is not the hard part. Point-in-time data, search-budget control, baselines, costs, multiplicity, robustness, preserved failures and prospective evaluation are what make large-scale alpha search trustworthy.

### Do you take users' strategies?

No by default. User hypotheses and strategy logic are private unless the user explicitly opts into a future contribution/marketplace mode.

### Where is the moat?

The compounding asset is the pre-outcome research and decision history across hypotheses, evidence, lifecycle, outcomes and usage—not a transport protocol or a single model.

## Supersession

`CURREN_SEED_DECK_2026-09-07.md` remains historical evidence of the prior 'verifiable decision intelligence' positioning and is superseded for new fundraising by this v0.4 source.