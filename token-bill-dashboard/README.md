# Token Bill Dashboard

All AI accounts and token usage in one view. Cyberpunk terminal style.

## Status
🚧 **v0.2 — chatgpt-plus wired live** · minimax + openai-api still mocked

## What's live now
- **chatgpt-plus card** (the +/green one) → real data from `chatgpt.com` Codex backend
  - 5h window % + reset countdown
  - 7d window % + reset countdown
  - Tier badge (premium / standard / etc.)
  - Auto-refreshes every 30s
  - Source label shows `live` / `cache` / age in seconds

## What's still mocked
- minimax card (orange) — placeholder values until MiniMax exposes per-window cap headers
- openai-api card (dim) — empty / offline (no platform.openai.com credits yet)
- KPI row ($24.18, 2.41M, 1842, 1308) — static
- Status strip (month, spend) — static
- Chart, model table, activity feed, alerts log — static
- Action buttons (refresh now, export csv, view raw json) — not wired to handlers

## Stack
- Static `index.html` (~42 KB) + Node.js backend (`server.js`)
- Express on `127.0.0.1:8790`
- Caddy reverse-proxies `/token-bill-dashboard/api/*` → `127.0.0.1:8790`
- systemd unit: `/etc/systemd/system/token-bill-dashboard.service`
- Served at `https://on9claw.com/token-bill-dashboard/`

## Data sources (live)
- **chatgpt-plus**: `https://chatgpt.com/backend-api/codex/responses` with the same OAuth token used by `codex-proapi`. Backend reads `x-codex-*` response headers and returns them as JSON via `/token-bill-dashboard/api/usage`. 5-minute in-memory cache to avoid burning tokens on every page load.

## API endpoints
- `GET /api/usage` → live Codex usage state (or last cached if fresh)
- `GET /api/health` → liveness
- `GET /api/cache` → last cached snapshot (no upstream call)
- `POST /api/refresh` → force upstream poll

## Next steps
- [ ] Wire minimax card (needs an upstream that exposes cap headers; current `api.minimaxi.com` does not)
- [ ] Real KPI rollups from a local token-usage log
- [ ] Make the "refresh now" button call `POST /api/refresh`
- [ ] CSV export
- [ ] Add accounts Parklan owns (TBD)
