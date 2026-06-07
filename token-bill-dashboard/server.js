#!/usr/bin/env node
/**
 * Token Bill Dashboard — multi-account backend
 *
 * Sources polled:
 *   chatgpt-plus  — /root/.codex/auth.json → chatgpt.com/backend-api/codex/responses
 *   minimax (cn)  — /root/.minimax/api_key → api.minimaxi.com/v1/api/openplatform/coding_plan/remains
 *   opencode-go   — OPENCODE_API_KEY → opencode.ai/zen/go/v1/chat/completions
 *                   (small probe; if 429 GoUsageLimitError → parse retry-after + metadata)
 *   openrouter    — OPENROUTER_API_KEY → openrouter.ai/api/v1/auth/key + /api/v1/credits
 *
 * Each source is cached independently for 5 minutes. state[slot] preserves
 * last good data even on error.
 *
 * Endpoints (Caddy strips /token-bill-dashboard; backend sees /api/*):
 *   GET  /api/usage    → { data: { chatgpt, minimax, opencode_go, openrouter } }
 *   GET  /api/health   → liveness + per-source cache status
 *   GET  /api/cache    → raw cached snapshots, no upstream calls
 *   POST /api/refresh  → force all upstream polls
 */
import express from "express";
import { readFile } from "fs/promises";
import { fileURLToPath } from "url";
import { dirname } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT) || 8790;
const HOST = process.env.HOST || "127.0.0.1";
const CACHE_TTL_MS = 5 * 60 * 1000;

const CODEX_AUTH_PATH = "/root/.codex/auth.json";
const CODEX_BACKEND_URL = "https://chatgpt.com/backend-api/codex/responses";
const MM_API_KEY_PATH = "/root/.minimax/api_key";
const MM_QUOTA_URL = "https://api.minimaxi.com/v1/api/openplatform/coding_plan/remains";
const OC_GO_URL = "https://opencode.ai/zen/go/v1/chat/completions";
const OC_AUTH_KEY_PATH = "/root/.opencode/auth.key";
const OR_AUTH_KEY_PATH = "/root/.openrouter/auth.key";
const OR_KEY_URL = "https://openrouter.ai/api/v1/auth/key";
const OR_CREDITS_URL = "https://openrouter.ai/api/v1/credits";

const CODEX_PROBE = {
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

const OC_GO_PROBE = {
  model: "deepseek-v4-flash",
  messages: [{ role: "user", content: "ok" }],
  max_tokens: 1,
  stream: false,
};

const app = express();
app.disable("x-powered-by");
app.use(express.json());
app.use((req, res, next) => {
  res.set("Access-Control-Allow-Origin", "*");
  res.set("Cache-Control", "no-store");
  next();
});

function blankState() {
  return {
    ok: false, source: null, fetchedAt: null, cachedUntil: null, data: null, error: null,
  };
}
const state = {
  chatgpt: blankState(),
  minimax: blankState(),
  opencode_go: blankState(),
  openrouter: blankState(),
};
const isFresh = (s) =>
  s && s.cachedUntil && new Date(s.cachedUntil).getTime() > Date.now() && s.data;

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
function nowIso() { return new Date().toISOString(); }
function setError(slot, err) {
  state[slot] = {
    ok: false, source: "error", fetchedAt: nowIso(),
    cachedUntil: state[slot].cachedUntil, data: state[slot].data, error: err,
  };
}
function setOk(slot, data) {
  state[slot] = {
    ok: true, source: "live", fetchedAt: nowIso(),
    cachedUntil: new Date(Date.now() + CACHE_TTL_MS).toISOString(),
    data, error: null,
  };
}
async function readKey(path) {
  try { return (await readFile(path, "utf8")).trim(); } catch { return ""; }
}

// ═══════════════════════════════════════════════════════════════════════════
//  chatgpt-plus (Codex)
// ═══════════════════════════════════════════════════════════════════════════
function headerSnapshot(headers) {
  const out = {};
  for (const [k, v] of headers.entries()) {
    if (k.startsWith("x-codex-") || k.startsWith("x-ratelimit-") || k === "retry-after") {
      out[k] = v;
    }
  }
  return out;
}
function parseCodex(snap, accountId) {
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
      key: "primary", label: "5h window",
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
      key: "secondary", label: "7d window",
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
async function pollCodex() {
  let authRaw;
  try { authRaw = JSON.parse(await readFile(CODEX_AUTH_PATH, "utf8")); }
  catch (e) { return setError("chatgpt", `Cannot read ${CODEX_AUTH_PATH}: ${e.message}`); }
  const tokens = authRaw.tokens || authRaw;
  const accessToken = tokens.access_token;
  const accountId = tokens.account_id;
  if (!accessToken || !accountId) return setError("chatgpt", "auth.json missing access_token or account_id");

  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 15000);
  let resp;
  try {
    resp = await fetch(CODEX_BACKEND_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
        Accept: "text/event-stream",
        "chatgpt-account-id": accountId,
        session_id: crypto.randomUUID(),
        Referer: "https://chatgpt.com/",
        Origin: "https://chatgpt.com",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
      },
      body: JSON.stringify(CODEX_PROBE),
      signal: ctrl.signal,
    });
  } catch (e) { clearTimeout(t); return setError("chatgpt", `upstream fetch failed: ${e.message}`); }
  clearTimeout(t);

  const snap = headerSnapshot(resp.headers);
  try {
    if (resp.body) {
      const r = resp.body.getReader();
      await r.read().catch(() => null);
      try { await r.cancel(); } catch {}
    }
  } catch {}

  if (!snap["x-codex-plan-type"]) {
    return setError("chatgpt", `upstream returned no x-codex-* headers (HTTP ${resp.status})`);
  }
  return setOk("chatgpt", parseCodex(snap, accountId));
}

// ═══════════════════════════════════════════════════════════════════════════
//  minimax (China)
// ═══════════════════════════════════════════════════════════════════════════
function parseMM(mr, kind) {
  const start = mr.start_time, end = mr.end_time;
  const weeklyStart = mr.weekly_start_time, weeklyEnd = mr.weekly_end_time;
  const now = Math.floor(Date.now() / 1000);
  const intervalEnd = end ? Math.floor(end / 1000) : null;
  const weeklyEndS = weeklyEnd ? Math.floor(weeklyEnd / 1000) : null;
  const remPct = mr.current_interval_remaining_percent;
  const wRemPct = mr.current_weekly_remaining_percent;
  return {
    service: "minimax", region: "cn", kind,
    label: kind === "general" ? "Text models (M3 / M2.7 / M2.5 / M2.1 / M2)" : "Video models",
    status: { interval: mr.current_interval_status, weekly: mr.current_weekly_status },
    interval: {
      windowMinutes: start && end ? Math.round((end - start) / 60000) : null,
      usedPct: remPct == null ? null : Math.max(0, Math.min(100, 100 - remPct)),
      remainingPct: remPct,
      usedCount: mr.current_interval_usage_count ?? 0,
      totalCount: mr.current_interval_total_count ?? 0,
      resetAt: intervalEnd,
      resetAtIso: intervalEnd ? new Date(intervalEnd * 1000).toISOString() : null,
      resetInSeconds: intervalEnd ? intervalEnd - now : null,
      resetInHuman: humanizeSeconds(intervalEnd ? intervalEnd - now : null),
      boostPermille: mr.interval_boost_permille ?? null,
    },
    weekly: {
      windowMinutes: weeklyStart && weeklyEnd ? Math.round((weeklyEnd - weeklyStart) / 60000) : null,
      usedPct: wRemPct == null ? null : Math.max(0, Math.min(100, 100 - wRemPct)),
      remainingPct: wRemPct,
      usedCount: mr.current_weekly_usage_count ?? 0,
      totalCount: mr.current_weekly_total_count ?? 0,
      resetAt: weeklyEndS,
      resetAtIso: weeklyEndS ? new Date(weeklyEndS * 1000).toISOString() : null,
      resetInSeconds: weeklyEndS ? weeklyEndS - now : null,
      resetInHuman: humanizeSeconds(weeklyEndS ? weeklyEndS - now : null),
      boostPermille: mr.weekly_boost_permille ?? null,
    },
    raw: mr,
  };
}
async function pollMinimax() {
  let key;
  try { key = (await readFile(MM_API_KEY_PATH, "utf8")).trim(); }
  catch (e) { return setError("minimax", `Cannot read ${MM_API_KEY_PATH}: ${e.message}`); }
  if (!key) return setError("minimax", `${MM_API_KEY_PATH} is empty`);

  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 15000);
  let resp;
  try {
    resp = await fetch(MM_QUOTA_URL, {
      method: "GET",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      signal: ctrl.signal,
    });
  } catch (e) { clearTimeout(t); return setError("minimax", `upstream fetch failed: ${e.message}`); }
  clearTimeout(t);

  let body;
  try { body = await resp.json(); }
  catch { return setError("minimax", `upstream returned non-JSON (HTTP ${resp.status})`); }

  if (body && body.base_resp && body.base_resp.status_code !== 0) {
    return setError("minimax", `upstream: ${body.base_resp.status_msg || `code ${body.base_resp.status_code}`}`);
  }
  const list = (body && Array.isArray(body.model_remains)) ? body.model_remains : [];
  if (!list.length) return setError("minimax", `upstream returned no model_remains (HTTP ${resp.status})`);

  const out = { service: "minimax", region: "cn", fetchedAtMs: Date.now(), models: {} };
  for (const mr of list) {
    const kind = (mr.model_name || "").toLowerCase();
    if (!out.models[kind]) out.models[kind] = parseMM(mr, kind);
  }
  return setOk("minimax", out);
}

// ═══════════════════════════════════════════════════════════════════════════
//  opencode-go (workspace monthly quota)
// ═══════════════════════════════════════════════════════════════════════════
async function pollOpencodeGo() {
  let key = await readKey(OC_AUTH_KEY_PATH);
  if (!key) key = process.env.OPENCODE_API_KEY || "";
  if (!key) return setError("opencode_go", "no OPENCODE_API_KEY");

  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 15000);
  let resp;
  try {
    resp = await fetch(OC_GO_URL, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${key}`,
        "Content-Type": "application/json",
        "User-Agent": "opencode-cli/1.16.2",
      },
      body: JSON.stringify(OC_GO_PROBE),
      signal: ctrl.signal,
    });
  } catch (e) { clearTimeout(t); return setError("opencode_go", `upstream fetch failed: ${e.message}`); }
  clearTimeout(t);

  const retryAfter = Number(resp.headers.get("retry-after")) || null;
  let body = null;
  try { body = await resp.json(); } catch {}

  if (resp.status === 200) {
    return setOk("opencode_go", {
      service: "opencode-go",
      label: "OpenCode Go (workspace)",
      endpoint: OC_GO_URL,
      status: "ok",
      monthly: { usedPct: null, used: null, limit: null, resetAt: null, resetInSeconds: null, resetInHuman: null, note: "within quota (probe succeeded)" },
      raw: { httpStatus: 200, retryAfter, body },
    });
  }

  if (resp.status === 429 && body && body.error && body.error.type === "GoUsageLimitError") {
    const meta = body.metadata || {};
    const resetIn = retryAfter != null ? retryAfter : null;
    return setOk("opencode_go", {
      service: "opencode-go",
      label: "OpenCode Go (workspace)",
      endpoint: OC_GO_URL,
      status: "limit_reached",
      workspace: meta.workspace || null,
      limitName: meta.limitName || "monthly",
      monthly: {
        usedPct: 100,
        used: null, limit: null,
        resetInSeconds: resetIn,
        resetInHuman: humanizeSeconds(resetIn),
        note: "Monthly usage limit reached. Resets in " + humanizeSeconds(resetIn) + ".",
      },
      upgradeUrl: meta.workspace ? `https://opencode.ai/workspace/${meta.workspace}/go` : "https://opencode.ai/workspace",
      raw: { httpStatus: 429, retryAfter, body },
    });
  }

  return setError("opencode_go", `upstream returned HTTP ${resp.status}: ${body && body.error ? body.error.message : "unknown"}`);
}

// ═══════════════════════════════════════════════════════════════════════════
//  openrouter (credits + spend breakdown)
// ═══════════════════════════════════════════════════════════════════════════
function parseOpenRouter(key, credits) {
  const d = (key && key.data) || {};
  const c = (credits && credits.data) || {};
  const totalCredits = typeof c.total_credits === "number" ? c.total_credits : null;
  const totalUsage   = typeof c.total_usage   === "number" ? c.total_usage   : null;
  const remaining    = (totalCredits != null && totalUsage != null) ? Math.max(0, totalCredits - totalUsage) : null;
  return {
    service: "openrouter",
    label: "OpenRouter (credits)",
    endpoint: OR_KEY_URL,
    accountId: d.creator_user_id || null,
    keyLabel: d.label || null,
    isFreeTier: !!d.is_free_tier,
    isManagementKey: !!d.is_management_key,
    limit: d.limit,
    limitReset: d.limit_reset || null,
    limitRemaining: d.limit_remaining,
    includeByokInLimit: !!d.include_byok_in_limit,
    spend: {
      lifetime: typeof d.usage === "number" ? d.usage : null,
      daily:    typeof d.usage_daily === "number" ? d.usage_daily : null,
      weekly:   typeof d.usage_weekly === "number" ? d.usage_weekly : null,
      monthly:  typeof d.usage_monthly === "number" ? d.usage_monthly : null,
      byokLifetime: typeof d.byok_usage === "number" ? d.byok_usage : null,
      byokDaily:    typeof d.byok_usage_daily === "number" ? d.byok_usage_daily : null,
      byokWeekly:   typeof d.byok_usage_weekly === "number" ? d.byok_usage_weekly : null,
      byokMonthly:  typeof d.byok_usage_monthly === "number" ? d.byok_usage_monthly : null,
    },
    credits: {
      total: totalCredits,
      used:  totalUsage,
      remaining,
      remainingPct: (totalCredits != null && totalUsage != null && totalCredits > 0)
        ? Math.max(0, Math.min(100, (remaining / totalCredits) * 100))
        : null,
      usedPct: (totalCredits != null && totalUsage != null && totalCredits > 0)
        ? Math.max(0, Math.min(100, (totalUsage / totalCredits) * 100))
        : null,
    },
    expiresAt: d.expires_at || null,
    raw: { key, credits },
  };
}
async function pollOpenRouter() {
  let key = await readKey(OR_AUTH_KEY_PATH);
  if (!key) key = process.env.OPENROUTER_API_KEY || "";
  if (!key) return setError("openrouter", "no OPENROUTER_API_KEY");

  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), 15000);
  let k, c;
  try {
    const [kr, cr] = await Promise.all([
      fetch(OR_KEY_URL, { method: "GET", headers: { Authorization: `Bearer ${key}` }, signal: ctrl.signal }),
      fetch(OR_CREDITS_URL, { method: "GET", headers: { Authorization: `Bearer ${key}` }, signal: ctrl.signal }),
    ]);
    clearTimeout(t);
    if (!kr.ok) return setError("openrouter", `/api/v1/auth/key HTTP ${kr.status}`);
    if (!cr.ok) return setError("openrouter", `/api/v1/credits HTTP ${cr.status}`);
    k = await kr.json();
    c = await cr.json();
  } catch (e) {
    clearTimeout(t);
    return setError("openrouter", `upstream fetch failed: ${e.message}`);
  }

  return setOk("openrouter", parseOpenRouter(k, c));
}

function sourceSummary(s) {
  return { ok: s.ok, source: s.source, fresh: isFresh(s), fetchedAt: s.fetchedAt, error: s.error };
}

app.get("/api/health", (req, res) => {
  res.json({
    ok: true,
    service: "token-bill-dashboard",
    uptimeSec: Math.round(process.uptime()),
    sources: {
      chatgpt:     sourceSummary(state.chatgpt),
      minimax:     sourceSummary(state.minimax),
      opencode_go: sourceSummary(state.opencode_go),
      openrouter:  sourceSummary(state.openrouter),
    },
  });
});

async function collect(refresh) {
  if (refresh || !isFresh(state.chatgpt))     await pollCodex();
  if (refresh || !isFresh(state.minimax))     await pollMinimax();
  if (refresh || !isFresh(state.opencode_go)) await pollOpencodeGo();
  if (refresh || !isFresh(state.openrouter))  await pollOpenRouter();
  return {
    ok: state.chatgpt.ok || state.minimax.ok || state.opencode_go.ok || state.openrouter.ok,
    source: "live",
    fetchedAt: nowIso(),
    data: {
      chatgpt:     state.chatgpt.data,
      minimax:     state.minimax.data,
      opencode_go: state.opencode_go.data,
      openrouter:  state.openrouter.data,
    },
    errors: {
      chatgpt:     state.chatgpt.error,
      minimax:     state.minimax.error,
      opencode_go: state.opencode_go.error,
      openrouter:  state.openrouter.error,
    },
  };
}

app.get("/api/usage", async (req, res) => {
  const refresh = String(req.query.refresh || "") === "1";
  res.json(await collect(refresh));
});

app.get("/api/cache", (req, res) => {
  res.json({
    ok: true,
    sources: {
      chatgpt:     { ...state.chatgpt, fresh: isFresh(state.chatgpt) },
      minimax:     { ...state.minimax, fresh: isFresh(state.minimax) },
      opencode_go: { ...state.opencode_go, fresh: isFresh(state.opencode_go) },
      openrouter:  { ...state.openrouter, fresh: isFresh(state.openrouter) },
    },
  });
});

app.post("/api/refresh", async (req, res) => {
  res.json(await collect(true));
});

(async () => {
  try {
    await Promise.all([pollCodex(), pollMinimax(), pollOpencodeGo(), pollOpenRouter()]);
    console.log(`[boot] codex:        ok=${state.chatgpt.ok}     err=${state.chatgpt.error || "-"}`);
    console.log(`[boot] minimax:      ok=${state.minimax.ok}     err=${state.minimax.error || "-"}`);
    console.log(`[boot] opencode-go:  ok=${state.opencode_go.ok} err=${state.opencode_go.error || "-"}`);
    console.log(`[boot] openrouter:   ok=${state.openrouter.ok}  err=${state.openrouter.error || "-"}`);
  } catch (e) {
    console.error(`[boot] initial poll threw: ${e.message}`);
  }
  app.listen(PORT, HOST, () => {
    console.log(`[ready] token-bill-dashboard listening on http://${HOST}:${PORT}`);
  });
})();
