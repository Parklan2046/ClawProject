# AGENTS.md — 巴膠仔 / Bus ETA

Hong Kong bus ETA + chatbot web app. A static HTML frontend (`index.html`) and a tiny Python HTTP server (`busbot_server.py`) that proxies chat to OpenRouter.

The directory is not a git repo and has no `package.json` / `requirements.txt` / Makefile. The two source files are the entire project. Run them directly with the commands below.

## Essential commands

```bash
# Install dependency (stdlib only — no install needed; the `urllib` import is the only network code)
# If `urllib.request.urlopen` aliasing is added (see Gotchas), no change. Otherwise: zero deps.

# Run the chat backend
OPENROUTER_API_KEY=sk-... python3 busbot_server.py
# Defaults: HOST=127.0.0.1, PORT=8772 (override with BUSBOT_HOST / BUSBOT_PORT env vars)
# Listens on http://127.0.0.1:8772/busbot-api/message (POST)

# Run the frontend — just open the file in a browser, or serve it:
python3 -m http.server 8080
# Then open http://127.0.0.1:8080/index.html
```

There are no tests, linters, or build steps. The frontend is a single self-contained HTML file (all CSS + JS inline, no bundler, no `node_modules`).

## Architecture & data flow

### `index.html` — Static single-page client
- All data fetches go directly from the browser to **Hong Kong public transport APIs** (no app server in the middle for ETA lookups):
  - KMB: `https://data.etabus.gov.hk/v1/transport/kmb/{route,stop,route-stop,eta/{stop}/{route}/{service_type}}`
  - Citybus: `https://rt.data.gov.hk/v2/transport/citybus/{route/CTB/{route},stop/{stop_id},route-stop/CTB/{route}/{dir},eta/CTB/{stop}/{route}}`
- The HTML's stop-id format disambiguates operator: `^[0-9A-F]{16}$` ⇒ KMB, `^\d{6}$` ⇒ Citybus, anything else ⇒ query both (see `detectCO` around line 480).
- Stop ID concatenation with `+` (e.g. `KMB_ID+CTB_ID`) means "also fetch partner operator at the geographically nearest stop" — used to merge ETAs across operators at a single physical stop. See `openEtaWithPartner` ~line 601.
- Bookmarks persisted in `localStorage` under key `citybus_eta_bk_v7` (yes, the key says "citybus" — legacy). Bumped to `v7` if you ever need to invalidate. Fallback in-memory array `memoryBK` if storage is unavailable.
- Polls ETA every 10s with a visible countdown; supports pause/resume. `silent` refetches skip the loading splash.
- The chat panel posts to `/chatbot-api/message` — but the **server only implements `/busbot-api/message`** (see Gotchas).

### `busbot_server.py` — Chat proxy
- `BaseHTTPRequestHandler` serving exactly one route: `POST /busbot-api/message`.
- Request body: `{"messages": [{"role": "user|assistant", "content": "..."}, ...]}`.
- Response: `{"ok": true, "reply": "...", "model": "..."}` or `{"ok": false, "error": "..."}`.
- Takes the last user message, runs heuristic `get_bus_data()` to scrape KMB/Citybus APIs and append route/stop context to the system prompt, then forwards to OpenRouter's `/api/v1/chat/completions`.
- Truncates history to the last 12 user/assistant messages (`incoming[-12:]`).
- Default model `xiaomi/mimo-v2-pro`; override with `BUSBOT_MODEL` env var.
- 90s timeout on the upstream OpenRouter call; 10s on each HK data API.

## Hong Kong API quirks (worth knowing before changing the code)

- **KMB `service_type` is required** in the ETA URL: `.../eta/{stop}/{route}/1`. The `1` is hardcoded in both files — special routes use other codes; only `1` is fetched.
- **Citybus route URL is versioned** at `/v2/transport/citybus/...`. `/v1` paths exist for some endpoints and return a different shape.
- **KMB `route-stop` returns ALL routes for ALL directions** in one giant list — the frontend caches it (`_kmbRouteStopCache`, 1h TTL). Don't refetch per route in a tight loop.
- **KMB `bound` is `O` (outbound) / `I` (inbound)**. **Citybus uses `outbound` / `inbound` as a URL path segment**, not a single letter.
- **Coordinates are tiny** — distance threshold `0.003` (decimal degrees, ~300m) is used to match KMB+CTB stops. The math is a flat equirectangular approximation; good enough for HK, wrong near the poles (irrelevant here).
- Station name matching also falls back to substring on CJK names and on the first comma/paren segment of English names (see `pickDir` ~line 555–563).

## Naming & style

- **Frontend**: all identifiers in `index.html` are 1-3 char abbreviations or compressed — `bk`, `bm`, `cd`, `bmEditMode`, `openEta`, `renderBK`, `findRoute`, `pickDir`. This is intentional minimalism for inline JS size. Don't rename to verbose names without a reason.
- **Backend**: standard snake_case Python. Uses `urllib.request` (no `requests` lib).
- **Language**: UI strings and chatbot persona are **Traditional Chinese (Hong Kong / Cantonese)** — 巴膠仔, 九巴, 城巴, 唔好意思, etc. The system prompt is in Cantonese. Keep new user-facing strings in the same register.
- The two files disagree on chat endpoint path — preserve whatever you fix (see Gotchas).

## Gotchas (these will trip you up)

1. **Chat endpoint is `/busbot-api/message`** (matches both the Python handler and the frontend `fetch`). The frontend previously posted to `/chatbot-api/message`; this was fixed in 2026-06.

2. **CORS is open (`*`)** in the Python server — fine for local dev, dangerous if exposed. The `/busbot-api/message` route sets CORS headers but `do_OPTIONS` short-circuits without going through `send_json`, so preflight works.

4. **Two different `get_bus_data` paths.** The HTML fetches the HK data APIs directly from the browser (no proxy). The Python server *also* fetches them server-side to enrich the LLM prompt. The two implementations are independent and can drift; if you change one API URL, change both.

5. **KMB route-stop cache is dual-layer.** `_kmbRouteStopCache` / `_kmbRouteCache` are module-globals (lost on reload), but `loadKMBCache()` IIFE on init rehydrates from `localStorage` (keys `kmb_rs_cache_v1`, `kmb_r_cache_v1`, TTL 1h, versioned — bump suffix to invalidate). `saveKMBCache()` is called from `findRoute` after a successful fetch. Same `storageOK()` guard pattern as the bookmarks.

6. **Stop-id regexes in the HTML are hardcoded to current HK formats.** If KMB/CTB ever change stop ID lengths, `detectCO` (~line 480) silently misclassifies and the wrong operator's API gets queried.

7. **Avatar asset is referenced but not in the repo.** `index.html:281, 284` reference `/assets/busbot-avatar.jpg` — the file doesn't exist in this directory, so the chat toggle shows a broken image. Either add the asset or remove the `<img>` tags.

8. **No version control.** The directory is not a git repo (`Is directory a git repo: no`). Don't run `git` commands; treat this as a flat file drop.

9. **No tests, no CI, no type checker.** Don't try to run `pytest`, `npm test`, `tsc`, etc. — they don't exist. Manual smoke test is: open `index.html` in a browser, type a route/stop, confirm ETA cards render.

10. **Comment style.** `busbot_server.py` uses Chinese in the docstring + Cantonese in the system prompt; code comments are absent. `index.html` uses Unicode section dividers like `// ── THEME ──`. Match the existing terseness — don't add docstrings or block comments unless asked.

11. **The `BUSBOT_MODEL` default is a non-OpenAI-native model** (`xiaomi/mimo-v2-pro`) routed through OpenRouter. If you swap providers, the request body shape changes (this code is OpenAI-Chat-Completions compatible only).

## Files

- `C:/Users/parkl/OneDrive/文件/GitHub/ClawProject/722-eta/index.html` — single-file client (~648 lines, all CSS+JS inline, lang `zh-Hant-HK`).
- `C:/Users/parkl/OneDrive/文件/GitHub/ClawProject/722-eta/busbot_server.py` — ~200 line chat proxy, stdlib only.
- `.crush/` — Crush editor state (sessions, logs, sqlite DB). Ignore unless debugging the editor itself.
