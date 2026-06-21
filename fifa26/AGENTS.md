# AGENTS.md — FIFA 26 世界盃 / FIFA 26 Dashboard

A single-page dashboard for the 2026 FIFA World Cup. Group-stage score sheet + knockout bracket, dark by default, polled live from ESPN's public scoreboard endpoint. The project is a static HTML frontend (`index.html`) and a tiny stdlib-only Python HTTP server (`fifa26_server.py`) that proxies ESPN. No SPA framework, no build step, no `node_modules`.

The directory is intentionally minimal — no `package.json`, no `requirements.txt`, no Makefile, no CI. The source files plus a handful of PWA assets are the entire project. Run directly with the commands below.

## Essential commands

```bash
# No dependencies to install — stdlib only.
python fifa26_server.py
# Defaults: HOST=127.0.0.1, PORT=8773. Override with FIFA26_HOST / FIFA26_PORT env vars.
# Open http://127.0.0.1:8773
```

There are no tests, linters, type checkers, or CI. Manual smoke test: open the URL, confirm the 分組賽 tab renders the group tables and the 淘汰賽 tab renders the bracket. Polling runs in the background; manual refresh is not required.

## Architecture & data flow

### `index.html` — Static single-page client
- Single-file SPA, two tabs (分組賽 / 淘汰賽), all CSS + JS inline, dark default theme (`#0B1220` bg, `#E11D2E` accent).
- Fetches from same-origin `/api/snapshot` only — never directly to ESPN. The Python server is the only thing that talks to `site.api.espn.com`.
- Polling interval on the client is 60s. UI shows a "更新於 X 秒前" timestamp plus a small pulsing countdown dot that turns amber when a refresh is due.
- State persisted in `localStorage` under one namespaced key (`fifa26_state_v1`): theme (light/dark), active tab (分組賽/淘汰賽), active round within the bracket, and tableView (groups grid vs master table).
- Group table is sorted by points → goal diff → goals scored → name (same order as the 2026 WC tiebreaker rules). Knockout bracket is grouped by round (R32 → R16 → QF → SF → F) with the active round highlighted.
- No external runtime dependencies — no React, no Tailwind, no jQuery. Vanilla JS only.
- Accessibility: `role="tablist"` / `role="tab"` / `aria-selected` on tabs, `role="dialog"` + `aria-modal` + focus-trap on the match modal, `aria-live="polite"` on the main content area, `aria-pressed` on round pills, `:focus-visible` outline, `prefers-reduced-motion` honoured. Skeleton placeholders (`.skel`) used during initial load.
- PWA: small "?" help button bottom-right shows the iOS / Android / desktop install hint per UA. Chrome/Edge/Android install prompt is wired via `beforeinstallprompt`.

### `fifa26_server.py` — HTTP server + polling thread
- `http.server.ThreadingHTTPServer` with a custom `BaseHTTPRequestHandler`.
- Routes:
  - `GET /` → serves `index.html` with `Cache-Control: no-cache` (other assets are `no-store`).
  - `GET /api/standings` → JSON: `{ "groups": [{"letter":"A","teams":[...]}], "updated_at": <unix-ts> }`.
  - `GET /api/bracket` → JSON: `{ "rounds": [{"label":"R16","key":"r16","matches":[...]}, ...], "updated_at": <unix-ts> }`.
  - `GET /api/snapshot` → raw contents of `data/snapshot.json` (debug aid; what the client polls).
  - `GET /api/health` → `{"ok": true, "ts": ..., "uptime_s": N, "last_update": ..., "last_poll": ..., "match_count": N, "errors": [...]}`.
  - `GET /sw.js`, `/manifest.webmanifest`, `/icon.svg`, `/favicon.ico`, `/robots.txt`, `/static/*` → static file serving.
- A daemon thread polls ESPN every 60s. On 429 it backs off to 300s for the next attempt and reverts to 60s on the next success. Each successful poll rewrites `data/snapshot.json` atomically (`snapshot.json.tmp` → `os.replace`).
- CORS is NOT set — same-origin only (no `Access-Control-Allow-Origin`). The local dev flow is `http://127.0.0.1:8773` end-to-end.
- Listens on `127.0.0.1` by default — does NOT bind `0.0.0.0`. Override with `FIFA26_HOST` env var if you really want LAN access.

### `providers/espn.py` — ESPN client
- Stdlib port of pulse's ESPN client. Hits `https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard`. No API key.
- User-Agent is fixed to `Mozilla/5.0 (fifa26-dashboard)` so ESPN's bot detection can be reasoned about. 429 responses are surfaced so the caller can back off.
- Parses `events[].competitions[0].competitors[]` to extract home/away, score, status. Group letter comes from `events[].competitions[0].altGameNote` ("Group A") → `competitions[0].groupings[].name` → `events[].groupings[].name` → `competitions[0].groups[].name` → `competitions[0].notes[].headline`, with a last-resort lookup against `providers/group_table.GROUP_TABLE` (the 12-group A–L composition).
- Status normalised to `scheduled` / `in_progress` / `final` / `postponed` from ESPN's `pre` / `in` / `post` plus the detail string for postponement detection.
- Knockout round labels normalised from both ESPN's slug (`round-of-32` etc.) and free-text `competitions[0].type.text` ("Round of 32", "Octavos de final", "準決賽" etc.) into `round-of-32` / `round-of-16` / `quarterfinals` / `semifinals` / `third-place` / `final` slugs with Chinese display labels.
- Returns a normalised dict per match with `status`, `round_slug`, `round`, `group`, `home`, `away`, `venue`, `date`. The HTTP layer applies additional shape transforms.

### `providers/group_table.py` — Static 12-group composition
- Hard-coded 2026 WC group composition (A–L, 4 teams each). Used as last-resort when ESPN omits the grouping on a group-stage match. Document the lineup here if FIFA changes it.

### `data/snapshot.json` — auto-generated cache
- Regenerated on each successful poll. Gitignored — the directory `data/` is committed with a `.gitkeep` so the path exists in fresh clones.
- Atomic write: `data/snapshot.json.tmp` → `os.replace` → `data/snapshot.json`. Readers (`/api/snapshot`) never see a partial file.
- Schema: `{ ts, last_update, last_poll_ts, matches: [...] }`.

## Naming & style

- **Frontend**: terse identifiers in `index.html` — `gs` (group stage), `ko` (knockout), `tab`, `tabG`, `tabK`, `renderGS`, `renderKO`, `pulse`, `flash`. This is intentional minimalism; the file is one big inline script and verbose names just bloat the bundle. Don't rename without a reason.
- **Backend**: standard snake_case Python. Uses `urllib.request` (no `requests`), `json`, `threading`, `http.server`, `pathlib`. No type hints beyond what's natural.
- **Language**: UI strings are **Traditional Chinese (Hong Kong / 粵語風格)** — 分組賽, 淘汰賽, 十六強, 八強, 準決賽, 決賽, 入球, 失球, 勝, 和, 負. Server log messages are English.
- **Comments**: absent in code. AGENTS.md is verbose-by-design. The Python file has no docstring beyond the module-level one-liner; the HTML file uses Unicode section dividers like `// ── POLLING ──` to mark regions in the inline script. Match this.
- **No emojis** in source code or commit messages.

## Gotchas (these will trip you up)

1. **ESPN endpoint slug is `fifa.world`** — NOT `fifa.wc`, NOT `fifaworldcup`, NOT `world.cup`. The full URL is `https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard`. Wrong slug returns 404 and the parser silently gets an empty events list.
2. **Group letter source is phase-dependent.** For group stage matches, the letter is in `events[].competitions[0].groups[0].name` ("Group A") — or sometimes in `events[].groupings[0].name`. The parser tries both and falls back to inspecting `competitors[].team.displayName` against a static group table as a last resort. Knockout matches have no group field — their round is in `competitions[0].type.text` or `events[].type.text`.
3. **Round label mapping.** ESPN returns a mix of "Round of 32" / "Round of 16" / "Quarterfinal" / "Semifinal" / "Final" (and their Spanish/French siblings on the World Cup feed — "Octavos de final", etc.). The normaliser matches all variants to canonical slugs: `round-of-32` / `round-of-16` / `quarterfinals` / `semifinals` / `third-place` / `final`, then maps to short display labels R32 / R16 / QF / SF / F. If ESPN adds a new round, it'll appear in `bracket.rounds[].label` as whatever slug it returned until you update the patterns.
4. **No CORS issue** — the client and server are on the same origin (`127.0.0.1:8773`). Don't add `Access-Control-Allow-Origin: *` to the server thinking you need it; you don't, and it's a footgun.
5. **Polling interval is 60s — ESPN rate-limits harshly.** Don't lower it. The user-agent header is fixed to `Mozilla/5.0 (fifa26-dashboard)` so ESPN's bot detection can be reasoned about. On 429 the server automatically backs off to 5 minutes for the next attempt; the next successful poll reverts to 60s.
6. **`data/snapshot.json` is gitignored** but the directory `data/` is committed with a `.gitkeep`. If a fresh clone complains about a missing snapshot, the server just creates an empty one on first poll.
7. **Theme + tab + active round + tableView persist in `localStorage`** under one namespaced key (`fifa26_state_v1`). Bump the suffix to invalidate on a breaking UI change.
8. **Server does NOT bind `0.0.0.0`.** Only `127.0.0.1`. LAN access requires `FIFA26_HOST=0.0.0.0` — and at that point CORS should be re-evaluated for safety.
9. **No tests, no CI, no type checker.** Don't try to run `pytest`, `npm test`, `mypy`, `tsc` — they don't exist. Manual smoke test is: open `http://127.0.0.1:8773`, switch tabs, confirm scores update, check that polling still works after 60s (`/api/health.uptime_s` keeps incrementing; `last_poll` updates after the next refresh).
10. **Commit style.** The sibling 722-eta project uses a `fix(722-eta):` prefix. For fifa26, prefer `feat(fifa26):` / `fix(fifa26):` / `chore(fifa26):`.
11. **Server processes can be sneaky on Windows.** If `python fifa26_server.py` seems to start but the running process is serving stale code (e.g. wrong CORS headers, old response shape), there may be a leftover process on port 8773 from a previous session. Check with `powershell "Get-NetTCPConnection -LocalPort 8773"` and kill the PID before restarting.

## Files

- `C:/Users/parkl/OneDrive/文件/GitHub/ClawProject/fifa26/index.html` — single-file client (~1000 lines, all CSS+JS inline, lang `zh-Hant-HK`, two tabs).
- `C:/Users/parkl/OneDrive/文件/GitHub/ClawProject/fifa26/fifa26_server.py` — stdlib HTTP server, ~330 lines, polls ESPN every 60s, writes `data/snapshot.json` atomically, 5-minute backoff on 429.
- `C:/Users/parkl/OneDrive/文件/GitHub/ClawProject/fifa26/providers/espn.py` — ESPN client, ~210 lines, stdlib `urllib` only, normalises group letter + status enum + round label.
- `C:/Users/parkl/OneDrive/文件/GitHub/ClawProject/fifa26/providers/group_table.py` — static 12-group composition (A–L, 4 teams each), last-resort group resolver.
- `C:/Users/parkl/OneDrive/文件/GitHub/ClawProject/fifa26/data/snapshot.json` — auto-generated cache, gitignored, atomic write. Server creates on first poll; do not commit.
- `C:/Users/parkl/OneDrive/文件/GitHub/ClawProject/fifa26/data/.gitkeep` — placeholder so the `data/` directory exists in fresh clones.
- `C:/Users/parkl/OneDrive/文件/GitHub/ClawProject/fifa26/manifest.webmanifest` — PWA web manifest (name, single icon, standalone).
- `C:/Users/parkl/OneDrive/文件/GitHub/ClawProject/fifa26/icon.svg` — PWA icon (navy `#0B1220` bg, red `#E11D2E` heavy "26" glyph, used at all sizes).
- `C:/Users/parkl/OneDrive/文件/GitHub/ClawProject/fifa26/sw.js` — service worker, app shell only (NEVER caches `/api/*`). Versioned cache `fifa26_shell_v1` — bump suffix to invalidate.
- `C:/Users/parkl/OneDrive/文件/GitHub/ClawProject/fifa26/AGENTS.md` — this file.

## PWA

- **Install hint**: small "?" button bottom-right shows platform-specific instructions: iOS Safari share → add to home screen, Android tap the ⬇ button in the topbar, desktop browser install icon.
- **Service worker registration** is silently skipped on `file://` (feature-detected). Registration error is `.catch` swallowed — no user-facing noise.
- **Theme color** in the manifest matches the body bg (`#0B1220`) so Android's address bar tints correctly on install.

## Data shape (reference)

`GET /api/standings` response:

```json
{
  "groups": [
    {
      "letter": "A",
      "teams": [
        { "id": "...", "iso": "439", "name": "Mexico", "short": "MEX", "logo": "...",
          "color": "...", "flag": "...",
          "played": 0, "won": 0, "drawn": 0, "lost": 0,
          "gf": 0, "ga": 0, "gd": 0, "pts": 0,
          "qualified": "top2" }
      ]
    }
  ],
  "updated_at": 1782023849
}
```

`GET /api/bracket` response:

```json
{
  "rounds": [
    {
      "label": "R16",
      "key": "r16",
      "matches": [
        { "id": "...", "home": "TBD", "away": "TBD", "score": null,
          "status": "scheduled", "kickoff": "2026-06-28T20:00:00Z",
          "venue": "...", "round": "16強" }
      ]
    }
  ],
  "updated_at": 1782023849
}
```

`GET /api/health` response:

```json
{
  "ok": true,
  "ts": 1782023873,
  "uptime_s": 24,
  "last_update": 1782023849,
  "last_poll": 1782023849,
  "match_count": 3,
  "errors": []
}
```

`GET /api/snapshot` response: raw `data/snapshot.json`, shape `{ ts, last_update, last_poll_ts, matches: [...] }`. Each match has the ESPN-normalised shape from `providers/espn.py`.

`status` is one of `scheduled` / `in_progress` / `final` / `postponed`. `score` is `null` until the match starts; once started it becomes `"H-A"` (e.g. `"1-0"`); once final it stays the final score.