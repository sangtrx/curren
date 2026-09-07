import { createClient } from "npm:@supabase/supabase-js@2.57.4";

const SIGNAL_ID = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;
const SYMBOL = /^[A-Z0-9._-]{2,32}$/;
const PUBLIC_NAME = /^[a-z0-9][a-z0-9._:-]{0,63}$/;
const SIGNAL_STATUSES = new Set(["pending", "active", "closed", "expired"]);
const SIGNAL_SIDES = new Set(["long", "short"]);
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

const timestamp = (value: unknown, label: string): Date => {
  if (typeof value !== "string" || value.trim() === "") {
    throw new RequestError(422, `${label} must be an ISO timestamp`);
  }
  const parsed = new Date(value);
  if (!Number.isFinite(parsed.getTime())) {
    throw new RequestError(422, `${label} must be an ISO timestamp`);
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

const normalizeSignal = (
  raw: unknown,
  source: string,
  generatedAt: Date,
  publicDelaySeconds: number,
) => {
  const signal = asObject(raw, "signal");
  if (!onlyKeys(signal, SIGNAL_KEYS)) {
    throw new RequestError(422, "signal contains unsupported fields");
  }

  const id = typeof signal.id === "string" ? signal.id.trim() : "";
  const symbol = typeof signal.symbol === "string" ? signal.symbol.trim().toUpperCase() : "";
  const side = typeof signal.side === "string" ? signal.side.trim().toLowerCase() : "";
  const status = typeof signal.status === "string" ? signal.status.trim().toLowerCase() : "";

  if (!SIGNAL_ID.test(id)) throw new RequestError(422, "invalid signal id");
  if (!SYMBOL.test(symbol)) throw new RequestError(422, `invalid symbol for ${id}`);
  if (!SIGNAL_SIDES.has(side)) throw new RequestError(422, `invalid side for ${id}`);
  if (!SIGNAL_STATUSES.has(status)) throw new RequestError(422, `invalid status for ${id}`);

  const publishedAt = timestamp(signal.published_at, `published_at for ${id}`);
  const requestedPublicAt = optionalTimestamp(signal.public_available_at, `public_available_at for ${id}`);
  if (requestedPublicAt && requestedPublicAt.getTime() < publishedAt.getTime()) {
    throw new RequestError(422, `public_available_at predates published_at for ${id}`);
  }

  const closedAt = optionalTimestamp(signal.closed_at, `closed_at for ${id}`);
  const realizedR = optionalFiniteNumber(signal.realized_r, `realized_r for ${id}`);
  const terminal = status === "closed" || status === "expired";
  if (terminal && !closedAt) throw new RequestError(422, `terminal signal requires closed_at for ${id}`);
  if (status === "closed" && realizedR == null) {
    throw new RequestError(422, `closed signal requires realized_r for ${id}`);
  }
  if (!terminal && (closedAt || realizedR != null || signal.exit_reason != null)) {
    throw new RequestError(422, `non-terminal signal contains terminal fields for ${id}`);
  }
  if (closedAt && closedAt.getTime() < publishedAt.getTime()) {
    throw new RequestError(422, `closed_at predates published_at for ${id}`);
  }

  const entry = optionalFiniteNumber(signal.entry, `entry for ${id}`);
  const stop = optionalFiniteNumber(signal.stop, `stop for ${id}`);
  const mark = optionalFiniteNumber(signal.mark, `mark for ${id}`);
  const currentR = optionalFiniteNumber(signal.current_r, `current_r for ${id}`);
  const peakR = optionalFiniteNumber(signal.peak_r, `peak_r for ${id}`);
  for (const [label, value] of [["entry", entry], ["stop", stop], ["mark", mark]] as const) {
    if (value != null && value <= 0) throw new RequestError(422, `${label} must be positive for ${id}`);
  }

  let exitReason: string | null = null;
  if (signal.exit_reason != null) {
    if (typeof signal.exit_reason !== "string") {
      throw new RequestError(422, `exit_reason must be a string for ${id}`);
    }
    const normalized = signal.exit_reason.trim().toLowerCase();
    if (normalized && !PUBLIC_NAME.test(normalized)) {
      throw new RequestError(422, `invalid exit_reason for ${id}`);
    }
    exitReason = normalized || null;
  }

  const minimumPublicAt = new Date(publishedAt.getTime() + publicDelaySeconds * 1000);
  const firstPublicAt = requestedPublicAt && requestedPublicAt > minimumPublicAt
    ? requestedPublicAt
    : minimumPublicAt;

  return {
    id,
    source,
    source_generated_at: generatedAt.toISOString(),
    symbol,
    side,
    status,
    published_at: publishedAt.toISOString(),
    public_available_at: firstPublicAt.toISOString(),
    entry,
    stop,
    mark,
    current_r: currentR,
    peak_r: peakR,
    realized_r: realizedR,
    closed_at: closedAt?.toISOString() ?? null,
    exit_reason: exitReason,
    updated_at: new Date().toISOString(),
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

    if (!Array.isArray(payload.signals) || payload.signals.length > 500) {
      throw new RequestError(422, "signals must be an array of at most 500 items");
    }

    const publicDelaySeconds = integerEnv("CURREN_PUBLIC_DELAY_SECONDS", 1800, 0, 86400);
    const rows = payload.signals.map((signal) =>
      normalizeSignal(signal, source, generatedAt, publicDelaySeconds)
    );

    const db = createClient(supabaseUrl, dbSecret, {
      auth: { persistSession: false, autoRefreshToken: false },
    });

    let inserted = 0;
    let updated = 0;
    let staleIgnored = 0;

    for (const row of rows) {
      const { data: existing, error: existingError } = await db
        .from("signals")
        .select("source,source_generated_at,public_available_at")
        .eq("id", row.id)
        .maybeSingle();
      if (existingError) return json({ detail: "database read failed" }, 500);

      if (existing?.source && existing.source !== source) {
        return json({ detail: `publication source conflict for ${row.id}` }, 409);
      }

      if (existing?.source_generated_at) {
        const previous = new Date(existing.source_generated_at).getTime();
        if (!Number.isFinite(previous)) return json({ detail: "invalid stored replay watermark" }, 500);
        if (previous >= generatedAt.getTime()) {
          staleIgnored += 1;
          continue;
        }
      }

      if (existing?.public_available_at) {
        row.public_available_at = existing.public_available_at;
      }

      const { error: upsertError } = await db.from("signals").upsert(row, { onConflict: "id" });
      if (upsertError) return json({ detail: "signal write failed" }, 500);

      if (existing) updated += 1;
      else inserted += 1;
    }

    return json({
      accepted: rows.length,
      inserted,
      updated,
      stale_ignored: staleIgnored,
      lifecycle_events_inserted: 0,
      outcome_records_inserted: 0,
    });
  } catch (error) {
    if (error instanceof RequestError) return json({ detail: error.message }, error.status);
    return json({ detail: "internal server error" }, 500);
  }
});
