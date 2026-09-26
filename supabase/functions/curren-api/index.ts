import { createClient } from "npm:@supabase/supabase-js@2.57.4";

// Mirrors the strict PublicationBatch contract in src/curren/models.py. State rules (replay
// watermark, source ownership, immutable publication/outcome/projection, append-only lifecycle)
// run atomically in public.curren_ingest_publication (supabase/migrations).

const SIGNAL_ID = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
const SYMBOL = /^[A-Z0-9._-]{2,32}$/;
const PUBLIC_NAME = /^[a-z0-9][a-z0-9._:-]{0,63}$/;
const ZONED_TIMESTAMP = /^\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?([Zz]|[+-]\d{2}:\d{2})$/;
const SIGNAL_STATUSES = new Set(["pending", "active", "closed", "expired"]);
const TERMINAL_STATUSES = new Set(["closed", "expired"]);
const SIGNAL_SIDES = new Set(["long", "short"]);
const TARGET_STATUSES = new Set(["pending", "hit"]);
const MAX_SIGNALS = 500;
const MAX_TARGETS = 16;
const MAX_LIFECYCLE_EVENTS = 512;
const BATCH_KEYS = new Set(["source", "generated_at", "signals"]);
const SIGNAL_KEYS = new Set([
  "id",
  "symbol",
  "side",
  "status",
  "published_at",
  "public_available_at",
  "entry",
  "stop",
  "targets",
  "mark",
  "current_r",
  "peak_r",
  "realized_r",
  "closed_at",
  "exit_reason",
  "lifecycle",
]);
const TARGET_KEYS = new Set(["price", "status", "hit_at"]);
const LIFECYCLE_KEYS = new Set(["event_type", "event_at", "price", "r_multiple"]);

class RequestError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });

const integerEnv = (name: string, fallback: number, min: number, max: number) => {
  const raw = Deno.env.get(name);
  if (raw == null || raw.trim() === "") return fallback;
  const value = Number(raw);
  if (!Number.isInteger(value) || value < min || value > max) return fallback;
  return value;
};

const onlyKeys = (value: Record<string, unknown>, allowed: Set<string>) =>
  Object.keys(value).every((key) => allowed.has(key));

const asObject = (value: unknown, label: string): Record<string, unknown> => {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new RequestError(422, `${label} must be an object`);
  }
  return value as Record<string, unknown>;
};

const optionalList = (value: unknown, label: string, max: number): unknown[] => {
  if (value === undefined) return [];
  if (!Array.isArray(value) || value.length > max) {
    throw new RequestError(422, `${label} must be an array of at most ${max} items`);
  }
  return value;
};

// Timestamps must carry an explicit zone. They are stored at millisecond precision, the precision
// every row in the replica already uses, so replayed snapshots compare equal.
const timestamp = (value: unknown, label: string): Date => {
  if (typeof value !== "string" || !ZONED_TIMESTAMP.test(value.trim())) {
    throw new RequestError(422, `${label} must be an ISO timestamp with a timezone`);
  }
  const parsed = new Date(value.trim());
  if (!Number.isFinite(parsed.getTime())) {
    throw new RequestError(422, `${label} must be an ISO timestamp with a timezone`);
  }
  return parsed;
};

const optionalTimestamp = (value: unknown, label: string): Date | null => {
  if (value == null) return null;
  return timestamp(value, label);
};

const optionalFiniteNumber = (value: unknown, label: string): number | null => {
  if (value == null) return null;
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new RequestError(422, `${label} must be a finite number`);
  }
  return value;
};

const optionalPositiveNumber = (value: unknown, label: string): number | null => {
  const number = optionalFiniteNumber(value, label);
  if (number != null && number <= 0) throw new RequestError(422, `${label} must be positive`);
  return number;
};

const iso = (value: Date | null) => value?.toISOString() ?? null;

const secretMaterial = (): { dbSecret: string; acceptedBearer: Set<string> } => {
  const serviceRole = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")?.trim() ?? "";
  const acceptedBearer = new Set<string>();
  let secretMap: Record<string, unknown> = {};

  try {
    const raw = Deno.env.get("SUPABASE_SECRET_KEYS") ?? "{}";
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      secretMap = parsed as Record<string, unknown>;
    }
  } catch {
    secretMap = {};
  }

  for (const value of Object.values(secretMap)) {
    if (typeof value === "string" && value.trim()) acceptedBearer.add(value.trim());
  }
  if (serviceRole) acceptedBearer.add(serviceRole);

  const preferred = secretMap.default;
  const dbSecret =
    (typeof preferred === "string" && preferred.trim()) ||
    serviceRole ||
    [...acceptedBearer][0] ||
    "";

  return { dbSecret, acceptedBearer };
};

const requirePublisherAuthorization = (req: Request, acceptedBearer: Set<string>) => {
  const header = req.headers.get("authorization") ?? "";
  const match = /^Bearer\s+(.+)$/i.exec(header);
  const token = match?.[1]?.trim() ?? "";
  if (!token || !acceptedBearer.has(token)) {
    throw new RequestError(401, "publisher authorization failed");
  }
};

const normalizeTarget = (raw: unknown, id: string) => {
  const target = asObject(raw, `target for ${id}`);
  if (!onlyKeys(target, TARGET_KEYS)) {
    throw new RequestError(422, `target contains unsupported fields for ${id}`);
  }
  const price = optionalPositiveNumber(target.price, `target price for ${id}`);
  if (price == null) throw new RequestError(422, `target price is required for ${id}`);
  const status = target.status === undefined ? "pending" : target.status;
  if (typeof status !== "string" || !TARGET_STATUSES.has(status)) {
    throw new RequestError(422, `invalid target status for ${id}`);
  }
  const hitAt = optionalTimestamp(target.hit_at, `target hit_at for ${id}`);
  if (status === "hit" && !hitAt) throw new RequestError(422, `hit targets require hit_at for ${id}`);
  if (status === "pending" && hitAt) {
    throw new RequestError(422, `pending targets cannot contain hit_at for ${id}`);
  }
  return { price, status, hitAt };
};

const normalizeLifecycleEvent = (raw: unknown, id: string) => {
  const event = asObject(raw, `lifecycle event for ${id}`);
  if (!onlyKeys(event, LIFECYCLE_KEYS)) {
    throw new RequestError(422, `lifecycle event contains unsupported fields for ${id}`);
  }
  const rawType = event.event_type;
  const eventType = typeof rawType === "string" && rawType.length <= 64 ? rawType.trim().toLowerCase() : "";
  if (!PUBLIC_NAME.test(eventType)) throw new RequestError(422, `invalid lifecycle event_type for ${id}`);
  return {
    eventType,
    eventAt: timestamp(event.event_at, `lifecycle event_at for ${id}`),
    price: optionalPositiveNumber(event.price, `lifecycle price for ${id}`),
    rMultiple: optionalFiniteNumber(event.r_multiple, `lifecycle r_multiple for ${id}`),
  };
};

const normalizeSignal = (
  raw: unknown,
  generatedAt: Date,
  publicDelaySeconds: number,
) => {
  const signal = asObject(raw, "signal");
  if (!onlyKeys(signal, SIGNAL_KEYS)) {
    throw new RequestError(422, "signal contains unsupported fields");
  }

  const id = typeof signal.id === "string" ? signal.id.trim() : "";
  const symbol = typeof signal.symbol === "string" ? signal.symbol.trim().toUpperCase() : "";
  const side = typeof signal.side === "string" ? signal.side : "";
  const status = typeof signal.status === "string" ? signal.status : "";

  if (!SIGNAL_ID.test(id)) throw new RequestError(422, "invalid signal id");
  if (!SYMBOL.test(symbol)) throw new RequestError(422, `invalid symbol for ${id}`);
  if (!SIGNAL_SIDES.has(side)) throw new RequestError(422, `invalid side for ${id}`);
  if (!SIGNAL_STATUSES.has(status)) throw new RequestError(422, `invalid status for ${id}`);

  const publishedAt = timestamp(signal.published_at, `published_at for ${id}`);
  const requestedPublicAt = optionalTimestamp(signal.public_available_at, `public_available_at for ${id}`);
  if (requestedPublicAt && requestedPublicAt.getTime() < publishedAt.getTime()) {
    throw new RequestError(422, `public_available_at predates published_at for ${id}`);
  }

  let exitReason: string | null = null;
  if (signal.exit_reason != null) {
    if (typeof signal.exit_reason !== "string" || signal.exit_reason.length > 128) {
      throw new RequestError(422, `exit_reason must be a string for ${id}`);
    }
    const normalized = signal.exit_reason.trim().toLowerCase();
    if (normalized && !PUBLIC_NAME.test(normalized)) {
      throw new RequestError(422, `invalid exit_reason for ${id}`);
    }
    exitReason = normalized || null;
  }

  const closedAt = optionalTimestamp(signal.closed_at, `closed_at for ${id}`);
  const realizedR = optionalFiniteNumber(signal.realized_r, `realized_r for ${id}`);
  const currentR = optionalFiniteNumber(signal.current_r, `current_r for ${id}`);
  const terminal = TERMINAL_STATUSES.has(status);
  if (terminal && !closedAt) throw new RequestError(422, `terminal signal requires closed_at for ${id}`);
  if (!terminal && (closedAt || realizedR != null || exitReason != null)) {
    throw new RequestError(422, `non-terminal signal contains terminal fields for ${id}`);
  }
  if (status === "closed" && realizedR == null) {
    throw new RequestError(422, `closed signal requires realized_r for ${id}`);
  }
  if (closedAt && closedAt.getTime() < publishedAt.getTime()) {
    throw new RequestError(422, `closed_at predates published_at for ${id}`);
  }

  const targets = optionalList(signal.targets, `targets for ${id}`, MAX_TARGETS).map((item) =>
    normalizeTarget(item, id)
  );
  const lifecycle = optionalList(signal.lifecycle, `lifecycle for ${id}`, MAX_LIFECYCLE_EVENTS).map((item) =>
    normalizeLifecycleEvent(item, id)
  );
  const stateTimes = [
    ...targets.flatMap((target) => (target.hitAt ? [target.hitAt] : [])),
    ...lifecycle.map((event) => event.eventAt),
  ];
  for (const at of stateTimes) {
    if (at.getTime() < publishedAt.getTime()) {
      throw new RequestError(422, `target or lifecycle time predates published_at for ${id}`);
    }
    if (closedAt && at.getTime() > closedAt.getTime()) {
      throw new RequestError(422, `target or lifecycle time is after closed_at for ${id}`);
    }
  }
  const latestState = Math.max(
    (closedAt ?? publishedAt).getTime(),
    ...stateTimes.map((at) => at.getTime()),
  );
  if (generatedAt.getTime() < latestState) {
    throw new RequestError(422, `generated_at predates projected state for ${id}`);
  }

  const minimumPublicAt = new Date(publishedAt.getTime() + publicDelaySeconds * 1000);
  const firstPublicAt = requestedPublicAt && requestedPublicAt > minimumPublicAt
    ? requestedPublicAt
    : minimumPublicAt;

  return {
    id,
    symbol,
    side,
    status,
    published_at: iso(publishedAt),
    public_available_at: iso(firstPublicAt),
    entry: optionalPositiveNumber(signal.entry, `entry for ${id}`),
    stop: optionalPositiveNumber(signal.stop, `stop for ${id}`),
    targets: targets.map((target) => ({ price: target.price, status: target.status, hit_at: iso(target.hitAt) })),
    mark: optionalPositiveNumber(signal.mark, `mark for ${id}`),
    // Live-only: a closed signal has no open remainder (same rule as src/curren/store.py).
    current_r: terminal ? null : currentR,
    peak_r: optionalFiniteNumber(signal.peak_r, `peak_r for ${id}`),
    realized_r: realizedR,
    closed_at: iso(closedAt),
    exit_reason: exitReason,
    lifecycle: lifecycle.map((event) => ({
      event_type: event.eventType,
      event_at: iso(event.eventAt),
      price: event.price,
      r_multiple: event.rMultiple,
    })),
  };
};

Deno.serve(async (req: Request) => {
  try {
    const url = new URL(req.url);
    if (
      req.method === "GET" &&
      (url.pathname.endsWith("/healthz") || url.pathname.endsWith("/curren-api"))
    ) {
      return json({ status: "ok" });
    }
    if (req.method !== "POST" || !url.pathname.endsWith("/internal/v1/publications")) {
      return json({ detail: "not found" }, 404);
    }

    const supabaseUrl = Deno.env.get("SUPABASE_URL")?.trim() ?? "";
    const { dbSecret, acceptedBearer } = secretMaterial();
    if (!supabaseUrl || !dbSecret || acceptedBearer.size === 0) {
      return json({ detail: "server configuration error" }, 500);
    }
    requirePublisherAuthorization(req, acceptedBearer);

    let rawPayload: unknown;
    try {
      rawPayload = await req.json();
    } catch {
      throw new RequestError(400, "invalid json");
    }

    const payload = asObject(rawPayload, "publication batch");
    if (!onlyKeys(payload, BATCH_KEYS)) {
      throw new RequestError(422, "publication batch contains unsupported fields");
    }

    const source = typeof payload.source === "string" ? payload.source.trim().toLowerCase() : "";
    if (!PUBLIC_NAME.test(source)) throw new RequestError(422, "invalid publication source");

    const generatedAt = timestamp(payload.generated_at, "generated_at");
    const maxClockSkewSeconds = integerEnv("CURREN_MAX_CLOCK_SKEW_SECONDS", 300, 0, 3600);
    if (generatedAt.getTime() > Date.now() + maxClockSkewSeconds * 1000) {
      throw new RequestError(422, "generated_at exceeds allowed clock skew");
    }

    if (!Array.isArray(payload.signals) || payload.signals.length > MAX_SIGNALS) {
      throw new RequestError(422, `signals must be an array of at most ${MAX_SIGNALS} items`);
    }

    const publicDelaySeconds = integerEnv("CURREN_PUBLIC_DELAY_SECONDS", 1800, 0, 86400);
    const rows = payload.signals.map((signal) => normalizeSignal(signal, generatedAt, publicDelaySeconds));
    const seen = new Set<string>();
    for (const row of rows) {
      if (seen.has(row.id)) throw new RequestError(422, `duplicate signal id in publication batch: ${row.id}`);
      seen.add(row.id);
    }

    const db = createClient(supabaseUrl, dbSecret, {
      auth: { persistSession: false, autoRefreshToken: false },
    });

    // One transaction per batch: a conflict anywhere leaves the replica unchanged.
    const { data, error } = await db.rpc("curren_ingest_publication", {
      p_source: source,
      p_generated_at: iso(generatedAt),
      p_signals: rows,
    });
    if (error) {
      if (error.code === "PT409") return json({ detail: error.message }, 409);
      if (error.code === "PT422") return json({ detail: error.message }, 422);
      return json({ detail: "database write failed" }, 500);
    }

    if (!data || typeof data !== "object" || Array.isArray(data)) {
      return json({ detail: "database write failed" }, 500);
    }
    const result = data as Record<string, unknown>;
    return json({
      accepted: result.accepted,
      inserted: result.inserted,
      updated: result.updated,
      stale_ignored: result.stale_ignored,
      lifecycle_events_inserted: result.lifecycle_events_inserted,
      outcome_records_inserted: result.outcome_records_inserted,
    });
  } catch (error) {
    if (error instanceof RequestError) return json({ detail: error.message }, error.status);
    return json({ detail: "internal server error" }, 500);
  }
});
