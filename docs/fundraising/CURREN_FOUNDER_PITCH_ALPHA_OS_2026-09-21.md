# Curren Reusable Founder Pitch — Alpha OS

Canonical for founder videos, accelerator applications, investor conversations and short verbal pitches from: 2026-09-21

Workflow authority: `sangtrx/sang-workspace#66`  
Product thesis: `docs/PRODUCT_THESIS.md`  
Fundraising thesis: `docs/fundraising/CURREN_ALPHA_OS_FUNDRAISING_THESIS_2026-09-21.md`

**DO NOT OVERENGINEER.**

## Core idea

Curren is not a generic backtesting service and not an AI bot that promises to discover profitable trades.

A human or AI agent may start with a rough market hypothesis. Curren turns that hypothesis into a formal quantitative research specification, runs it through bounded point-in-time and out-of-sample validation, includes realistic cost assumptions and robustness/statistical gates, retains failures, and promotes only evidence that survives.

The company-level loop is:

```text
rough human/agent hypothesis
  -> formal quant research specification
  -> PIT-safe bounded experiment
  -> OOS / cost / robustness / statistical falsification
  -> reject weak ideas
  -> Alpha Registry for survivors
  -> trader / API / agent / separately gated deployment
  -> prospective lifecycle + outcome
  -> durable evidence history
```

**Most ideas should fail.** That is a feature of the system, not a product failure.

## Humanized problem statement

AI has made generating trading ideas extremely cheap. The bottleneck is no longer idea generation; it is knowing whether an idea survives serious quantitative scrutiny without leakage, cherry-picking or repeated tuning until the backtest looks good.

Curren is built around that bottleneck.

## One-line options

Canonical company line:

> **Curren turns market hypotheses into validated, deployable alpha — for traders and AI agents.**

Plain-English verbal line:

> **Curren takes a rough market idea, turns it into a proper quant experiment, and tries to kill it before anyone trusts it.**

Why-now line:

> **AI can generate endless trading hypotheses. Curren is the validation layer that decides which ones deserve to survive.**

Do not replace the canonical company line in durable product/fundraising source without a separate accepted thesis change. The plain-English variants are translations for speech.

## Founder video — reusable 45–55 second master

Hi, I'm Sang, founder of Curren.

I've spent years building AI systems, and I'm now building Curren full-time.

AI has made it incredibly easy to come up with trading ideas. A trader might have a rough market intuition, and an agent can generate hundreds more. The hard part is knowing which ideas actually survive serious quantitative testing.

That's what I'm building Curren for.

Curren takes a hypothesis, turns it into a proper quant experiment, tests it with point-in-time and out-of-sample data, includes trading costs, and tries to break the idea before trusting it.

Most ideas should fail. The ones that survive can become strategies used by traders or AI agents.

I'm a solo technical founder, and I've built the system end to end.

## 20-second conversational pitch

AI can generate trading ideas all day. The hard part is validating them without fooling yourself with leakage or a pretty backtest. Curren takes a rough market hypothesis, turns it into a disciplined quant experiment, tries to falsify it, and only promotes what survives for traders or AI agents to use.

## 90-second investor expansion

Curren is an Alpha OS for traders and AI agents.

The starting point does not have to be an executable strategy. It can be a trader's intuition or an agent-generated hypothesis. Curren compiles that into a formal research specification: what market and universe to test, what information is allowed at each point in time, what the baselines are, how costs are modeled, and what evidence would falsify the idea.

Then the Alpha Factory runs bounded experiments with point-in-time-safe data, out-of-sample evaluation, robustness checks and statistical controls. Failures are retained instead of hidden, and most ideas are expected to die.

Strategies that survive can enter the Alpha Registry and flow into downstream products for traders, APIs and agents, with deployment kept behind separate safety gates. Over time, the hypothesis, experiment history, lifecycle and prospective outcome create a pre-outcome evidence dataset.

AI makes hypothesis generation abundant. Curren is building the system that makes rigorous alpha validation and deployment repeatable.

## What to emphasize by audience

- **YZi / agentic-market audience:** humans or agents can propose hypotheses at scale, but Curren constrains the research process so more agents do not mean more p-hacking. Emphasize trusted agentic market infrastructure.
- **Alliance / crypto-native audience:** one crypto-native Alpha OS from hypothesis to scientific validation to distribution, with private alpha private by default.
- **YC / generalist audience:** experienced traders have ideas; turning them into trustworthy strategies requires data engineering, rigorous testing and deployment infrastructure. Curren automates that loop.
- **Pear / design-partner audience:** a serious trader brings a real hypothesis; Curren produces evidence, failure reasons and, only if it survives, a strategy artifact. The commercial question is whether teams pay to repeat that workflow.
- **SEA / VC audience:** Vietnam-built AI/fintech infrastructure with a concrete initial buyer: serious traders, small trading teams and financial-agent builders.

## Claim boundaries

Do not say or imply:

- Curren already has a proven profitable native strategy;
- Curren autonomously generates guaranteed alpha;
- every surviving research artifact is immediately live-money deployable;
- Curren has paid design partners, revenue or meaningful traction unless new accepted evidence establishes it;
- a normal historical backtest by itself is validation;
- private user hypotheses or strategy logic are reused, published, trained on or traded without explicit opt-in.

Use **"eligible for downstream use/deployment"** when the exact deployment/economic gate has not separately passed.

## Recording rule

For founder videos, prefer normal spoken English over deck language. Do not recite "multiplicity-aware," "immutable experiment identity," or the full architecture unless the question specifically asks for methodology. Translate them into: **proper quant experiment, realistic costs, out-of-sample testing, robustness checks, and trying to prove the idea wrong.**

Alliance's current founder-intro constraint remains the strict master format where applicable: founder on camera, <=1 minute, unlisted YouTube, startup/founder introduction, no product demo/presentation/screen recording. Recheck the live form before submission.
