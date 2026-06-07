#!/usr/bin/env node
/**
 * Token Bill Dashboard — Codex backend
 * Polls chatgpt.com/backend-api/codex/responses with the existing Codex OAuth
 * token (read from /root/.codex/auth.json) and returns parsed x-codex-* headers
 * as JSON. Caches for 5 minutes to avoid burning tokens on every page load.
 *
 * Endpoints:
 *   GET /api/usage        → live Codex usage state (or last cached)
 *   GET /api/health       → liveness
 *   GET /api/cache        → last cached snapshot (no upstream call)
 */
import express from "express";
import { readFile } from "fs/promises";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT) || 8790;
const HOST = process.env.HOST || "127.0.0.1";
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes
const AUTH_PATH = "/root/.codex/auth.json";
const BACKEND_URL = "https://chatgpt.com/backend-api/codex/responses";

// Tiny probe body — OpenAI counts every input token, so keep it minimal.
// We just need the response headers, not a useful completion.
const PROBE_BODY = {
  model: "gpt-5.5",
  stream: true,
  store: false,
  instructions: "ping",
  input: [{ role: "user", content: [{ type: "input_text", text: "ok" }] }],
  text: { verbosity: "low" },
  reasoning: {},
  tools: [],
  tool_choice: "auto",
};

const app = express();
app.disable("x-powered-by");
app.use(express.json());

// ── CORS — only same-origin is fine, but allow the public site too ──
app.use((req, res, next) => {
  res.set("Access-Control-Allow-Origin", "*");
  res.set("Cache-Control", "no-store");
  next();
});

// ── State ──
let cache = {
  ok: false,
  fetchedAt: null,
  cachedUntil: null,
  source: null, // "live" | "cache" | "error"
  data: null,
  error: null,
};

function readAuthJson() {
  return readFile(AUTH_PATH, "utf8").then(JSON.parse);
}

function headerSnapshot(headers) {
  // Pull every x-codex-* header, plus a few standard rate-limit ones for safety.
  const out = {};
  for (const [k, v] of headers.entries()) {
    if (
      k.startsWith("x-codex-") ||
      k.startsWith("x-ratelimit-") ||
      k.startsWith("x-ratelimit") ||
      k === "retry-after"
    ) {
      out[k] = v;
    }
  }
  return out;
}

function parseUsage(snap, accountId) {
  // Convert the raw x-codex-* header dict into the dashboard's data shape.
  const num = (v) => (v == null || v === "" ? null : Number(v));
  const primaryReset = num(snap["x-codex-primary-reset-at"]);
  const secondaryReset = num(snap["x-codex-secondary-reset-at"]);
  const primaryResetAfter = num(snap["x-codex-primary-reset-after-seconds"]);
  const secondaryResetAfter = num(snap["x-codex-secondary-reset-after-seconds"]);
  const now = Math.floor(Date.now() / 1000);

  return {
    service: "chatgpt-plus",
    label: "ChatGPT Plus (Codex OAuth)",
    planType: snap["x-codex-plan-type"] || null,
    activeLimit: snap["x-codex-active-limit"] || null,
    accountId,
    primary: {
      key: "primary",
      label: "5h window",
      usedPct: num(snap["x-codex-primary-used-percent"]),
      windowMinutes: num(snap["x-codex-primary-window-minutes"]),
      overSecondaryLimitPct: num(snap["x-codex-primary-over-secondary-limit-percent"]),
      resetAt: primaryReset,
      resetAtIso: primaryReset ? new Date(primaryReset * 1000).toISOString() : null,
      resetAfterSeconds: primaryResetAfter,
      resetInSeconds: primaryReset ? primaryReset - now : primaryResetAfter,
      resetInHuman: humanizeSeconds(primaryReset ? primaryReset - now : primaryResetAfter),
    },
    secondary: {
      key: "secondary",
      label: "7d window",
      usedPct: num(snap["x-codex-secondary-used-percent"]),
      windowMinutes: num(snap["x-codex-secondary-window-minutes"]),
      resetAt: secondaryReset,
      resetAtIso: secondaryReset ? new Date(secondaryReset * 1000).toISOString() : null,
      resetAfterSeconds: secondaryResetAfter,
      resetInSeconds: secondaryReset ? secondaryReset - now : secondaryResetAfter,
      resetInHuman: humanizeSeconds(secondaryReset ? secondaryReset - now : secondaryResetAfter),
    },
    credits: {
      hasCredits: snap["x-codex-credits-has-credits"] === "True" || snap["x-codex-credits-has-credits"] === "true",
      unlimited: snap["x-codex-credits-unlimited"] === "True" || snap["x-codex-credits-unlimited"] === "true",
      balance: snap["x-codex-credits-balance"] || null,
    },
    rawHeaders: snap,
  };
}

function humanizeSeconds(s) {
  if (s == null) return null;
  if (s <= 0) return "now";
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (d > 0) return `${d}d ${h}h`;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m`;
}

async function pollOnce() {
  let authRaw;
  try {
    authRaw = await readAuthJson();
  } catch (e) {
    const err = `Cannot read ${AUTH_PATH}: ${e.message}`;
    cache = {
      ok: false,
      source: "error",
      fetchedAt: new Date().toISOString(),
      cachedUntil: cache.cachedUntil, // keep prior TTL
      data: cache.data,
      error: err,
    };
    return cache;
  }
  const tokens = authRaw.tokens || authRaw;
  const accessToken = tokens.access_token;
  const accountId = tokens.account_id;
  if (!accessToken || !accountId) {
    const err = "auth.json missing access_token or account_id";
    cache = {
      ok: false,
      source: "error",
      fetchedAt: new Date().toISOString(),
      cachedUntil: cache.cachedUntil,
      data: cache.data,
      error: err,
    };
    return cache;
  }

  // Build a minimal Codex backend request — we just need the headers.
  const body = JSON.stringify(PROBE_BODY);
  const reqHeaders = {
    Authorization: `Bearer ${accessToken}`,
    "Content-Type": "application/json",
    Accept: "text/event-stream",
    "chatgpt-account-id": accountId,
    "session_id": crypto.randomUUID(),
    Referer: "https://chatgpt.com/",
    Origin: "https://chatgpt.com",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
  };

  const ctrl = new AbortController();
  const timeoutId = setTimeout(() => ctrl.abort(), 15000);
  let response;
  try {
    response = await fetch(BACKEND_URL, {
      method: "POST",
      headers: reqHeaders,
      body,
      signal: ctrl.signal,
    });
  } catch (e) {
    clearTimeout(timeoutId);
    const err = `upstream fetch failed: ${e.message}`;
    cache = {
      ok: false,
      source: "error",
      fetchedAt: new Date().toISOString(),
      cachedUntil: cache.cachedUntil,
      data: cache.data,
      error: err,
    };
    return cache;
  }
  clearTimeout(timeoutId);

  // Read headers, then drain the streaming body so the socket closes cleanly.
  const snap = headerSnapshot(response.headers);
  try {
    if (response.body) {
      const reader = response.body.getReader();
      // Read up to 1KB then bail — we don't care about the body.
      const { value } = await reader.read().catch(() => ({ value: null }));
      if (value) {
        // discard
      }
      try { await reader.cancel(); } catch {}
    }
  } catch {}

  if (!snap["x-codex-plan-type"]) {
    const err = `upstream returned no x-codex-* headers (HTTP ${response.status})`;
    cache = {
      ok: false,
      source: "error",
      fetchedAt: new Date().toISOString(),
      cachedUntil: cache.cachedUntil,
      data: cache.data,
      error: err,
    };
    return cache;
  }

  const usage = parseUsage(snap, accountId);
  const nowIso = new Date().toISOString();
  cache = {
    ok: true,
    source: "live",
    fetchedAt: nowIso,
    cachedUntil: new Date(Date.now() + CACHE_TTL_MS).toISOString(),
    data: usage,
    error: null,
  };
  return cache;
}

function cacheFresh() {
  return (
    cache &&
    cache.cachedUntil &&
    new Date(cache.cachedUntil).getTime() > Date.now() &&
    cache.data
  );
}

// ── Routes ──
app.get("/health", (req, res) => {
  res.json({
    ok: true,
    service: "token-bill-dashboard",
    uptimeSec: Math.round(process.uptime()),
    cache: {
      ok: cache.ok,
      source: cache.source,
      fetchedAt: cache.fetchedAt,
      cachedUntil: cache.cachedUntil,
      fresh: cacheFresh(),
    },
  });
});

app.get("/usage", async (req, res) => {
  if (cacheFresh()) {
    return res.json({
      ok: cache.ok,
      source: "cache",
      fetchedAt: cache.fetchedAt,
      cachedUntil: cache.cachedUntil,
      ageSeconds: Math.round((Date.now() - new Date(cache.fetchedAt).getTime()) / 1000),
      data: cache.data,
      error: cache.error,
    });
  }
  const fresh = await pollOnce();
  return res.json({
    ok: fresh.ok,
    source: fresh.source,
    fetchedAt: fresh.fetchedAt,
    cachedUntil: fresh.cachedUntil,
    ageSeconds: 0,
    data: fresh.data,
    error: fresh.error,
  });
});

app.get("/cache", (req, res) => {
  res.json({
    ok: cache.ok,
    source: cache.source,
    fetchedAt: cache.fetchedAt,
    cachedUntil: cache.cachedUntil,
    fresh: cacheFresh(),
    data: cache.data,
    error: cache.error,
  });
});

app.post("/refresh", async (req, res) => {
  const fresh = await pollOnce();
  res.json({
    ok: fresh.ok,
    source: fresh.source,
    fetchedAt: fresh.fetchedAt,
    cachedUntil: fresh.cachedUntil,
    data: fresh.data,
    error: fresh.error,
  });
});

// ── Boot: warm the cache so the first page load is fast ──
(async () => {
  try {
    await pollOnce();
    console.log(`[boot] initial poll: ok=${cache.ok} source=${cache.source} err=${cache.error || "-"}`);
  } catch (e) {
    console.error(`[boot] initial poll threw: ${e.message}`);
  }
  app.listen(PORT, HOST, () => {
    console.log(`[ready] token-bill-dashboard listening on http://${HOST}:${PORT}`);
  });
})();
