# SAN-64 execution checkpoint — 2026-09-08

This addendum records durable execution after `docs/fundraising/SEA_VIETNAM_SEED_BATCH_2026-09-08.md` was created. It does **not** mean any investor was contacted or any form was submitted.

## Durable transitions completed

### Stable current-deck URL

The current 12-slide **Curren Seed Deck v0.3** now has a bounded web representation at:

- `https://curren.tech/investors/deck`

Source authority:

- repository: `sangtrx/curren-landing-page`
- deck-route source commit: `c836b9d30f04359d405ec919373b1ab5a7ed63b2`
- one-shot production trigger commit: `8ad0f320cb3d825125e55516817366fa5daf2433`
- Netlify production deploy: `6aa03ab1f2156c0008d92d2b`
- deploy state: `ready`
- deployed `commit_ref`: `8ad0f320cb3d825125e55516817366fa5daf2433`
- trigger cleanup commit on `main`: `18780aa1a367323372cac27d6010d45527e89a83`

The route explicitly preserves the canonical truth boundaries: v0.4 alpha, pre-revenue, unincorporated, no meaningful customer traction, no profitability claim, and public live-feed integration not claimed as active end to end.

The ChatGPT Library PDF/PPTX remain the canonical visual deck artifacts. The web route is the stable link-safe representation for investor forms that require a URL; it is not permission to substitute the superseded 11-slide deck.

A temporary Firestorage copy was also created during execution for transport testing, but it expires on 2026-09-22 and is **not** the canonical fundraising link. Do not place that expiring URL into investor submissions while the stable `curren.tech` route is available.

### Backup Gmail drafts refreshed

The six existing backup drafts were updated in place and remain unsent:

1. AVV — `contact@avv.co`
2. Do Ventures — `contact@doventures.vc`
3. ThinkZone Ventures — `contact@thinkzone.vn`
4. Touchstone Partners — `hello@touchstone.vc`
5. Insignia Ventures Partners — `hello@insignia.vc`
6. Golden Gate Ventures — `hello@goldengate.vc`

Each draft now uses:

- investor demo: `https://curren.tech/investors`
- seed deck v0.3: `https://curren.tech/investors/deck`
- fund-specific framing rather than mass-identical copy
- explicit pre-revenue / no-meaningful-traction language where relevant
- the US$500k raise without invented traction, returns, incorporation, partnerships, or live-feed claims

No draft was sent.

### Warm-intro scan

A Gmail scan across the current Tier 1/Tier 2 fund domains found no non-draft direct correspondence with:

- `500.co`
- `avv.co`
- `doventures.vc`
- `thinkzone.vn`
- `touchstone.vc`
- `insignia.vc`
- `goldengate.vc`

Therefore no genuine warm-intro relationship is currently evidenced by the connected mailbox. For Golden Gate Ventures, continue to prefer a real mutual introduction if one is discovered elsewhere, but do not fabricate one; the published direct-email fallback remains the prepared route.

## Remaining work

Safe autonomous preparation is materially exhausted for this batch. The packet already contains current form truth values and fund-specific copy, the stable deck URL exists, and backup drafts are refreshed.

Immediately before any real outbound submission, reread the live authenticated/rendered form fields because fund forms can change. That readback is preparation, not submission.

## Outbound gate

Sending an investor email or submitting an investor form is an external fundraising action. Do not count any prepared packet, draft, form answer, or deck link as outreach.

A current explicit founder authorization is required immediately before real outbound submission. Until then SAN-64 should remain resumable at the outbound gate rather than falsely marked complete.
