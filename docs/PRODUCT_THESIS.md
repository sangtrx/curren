# Curren Product Thesis — Alpha OS

Last reconciled: 2026-09-21
Workflow authority: `sangtrx/sang-workspace#861`

**DO NOT OVERENGINEER.**

## Company thesis

**Curren turns market hypotheses into validated, deployable alpha — for traders and AI agents.**

Long-term vision: **the operating system where humans and AI agents discover, validate, deploy, distribute, and monetize trading alpha.**

Verification, provenance, immutable experiment identity and lifecycle integrity remain core system primitives, but they are substrate. They are not the primary retail-facing promise.

## Three user jobs, one engine

### 1. Retail trader — actionable trading decisions

Retail users want less analysis overhead: a clear entry, stop/invalidation, targets, lifecycle updates and a disciplined decision they can follow manually or, only when separately authorized and certified, through automated execution.

`woodsbot-system` is Curren's first production consumer/distribution runtime for this layer. It proves the end-to-end lifecycle and gives the Alpha Factory a real prospective downstream consumer.

### 2. Experienced trader / researcher — hypothesis to alpha

A user brings a market hypothesis. Curren should translate it into a formal, point-in-time testable specification, identify required data, construct causal features, execute bounded experiments, apply fees/slippage/funding and statistical controls, compare against baselines, explain failures, and promote only evidence that survives the frozen gates.

`curren-research` is the scientific Alpha Factory authority for this layer.

### 3. Quant team / AI agent — agent-native alpha discovery

Humans or agents may generate hypotheses at scale, but Curren must not become a p-hacking machine. Search remains finite, preregistered, point-in-time, multiplicity-aware, failure-retaining and promotion-gated. Agents may propose, compile, execute and inspect experiments only through accepted contracts and evidence boundaries.

## Product loop

```text
human hypothesis OR agent hypothesis
                ↓
        Curren Alpha Factory
                ↓
      falsification / validation
                ↓
          Alpha Registry
                ↓
   ┌────────────┼───────────────┐
   ↓            ↓               ↓
retail signals  API/agents      paper/live deployment
   └────────────┴───────────────┘
                ↓
     prospective lifecycle/outcome
                ↓
        durable evidence history
```

## Repository ownership

- `curren-research` — Alpha Factory, research contracts, evidence and scientific promotion authority.
- `woodsbot-system` — signal/lifecycle/distribution runtime and separately gated execution; first dogfood consumer of accepted alpha.
- `curren` — public product/API/CLI/MCP and sanitized alpha/decision read surfaces.
- `curren-access` — memberships, payments, consent/access/control plane; not research authority.
- `curren-landing-page` — customer/investor sales and product demo surface.
- `curren-social-factory` — acquisition/content/distribution; never market-performance truth authority.
- `curren-tradingview` — trader-facing chart/product/acquisition surface; never private research authority.

## Alpha ownership and privacy

User hypotheses, strategy logic, research artifacts and private deployments are **private by default**.

Curren must not silently reuse, train on, publish, sell, trade or distribute a user's private alpha. Any pooled learning or contribution requires explicit opt-in with bounded terms. A future marketplace may allow creators to voluntarily publish or monetize validated strategies with explicit ownership, visibility and revenue-sharing rules.

## Near-term commercial sequence

1. Dogfood `curren-research -> woodsbot-system -> prospective outcomes`.
2. Ship one bounded hypothesis-to-alpha design-partner workflow before expanding architecture breadth.
3. Treat Curren API/Team and Research Pro pilots as the primary commercial validation; Curren Pro/Signals is the retail distribution surface.
4. Add agent-native research contracts only after the human workflow and evidence contracts are stable.
5. Keep managed execution as a later opt-in extension behind exact venue/account/risk certification.

## Truth boundaries

Do not claim:

- proven profitable native alpha unless a separately accepted research result establishes it;
- a production-live public feed until end-to-end publication is verified;
- multi-user managed trading before the exact venue/account tuple is certified;
- users, revenue, paid design partners, partnerships or retention without evidence;
- that hashes/MCP/API schemas alone are the moat.

The intended compounding moat is the longitudinal pre-outcome record: hypothesis + ex-ante evidence + experiment history + lifecycle + outcome + regime/context + downstream usage, accumulated under explicit ownership and point-in-time rules.