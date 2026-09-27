// Test harness only: serve PostgREST under the /rest/v1 prefix supabase-js expects, then start the
// real Edge Function (it listens on Deno.serve's default port 8000).
const upstream = Deno.env.get("POSTGREST_URL") ?? "";

Deno.serve({ port: 3001 }, async (req: Request) => {
  const url = new URL(req.url);
  const target = upstream + url.pathname.replace(/^\/rest\/v1/, "") + url.search;
  const body = req.method === "GET" || req.method === "HEAD" ? undefined : await req.arrayBuffer();
  return await fetch(target, { method: req.method, headers: req.headers, body });
});

await import("../../supabase/functions/curren-api/index.ts");
