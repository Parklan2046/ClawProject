# Token Bill Dashboard

All AI accounts and token usage in one view. Cyberpunk terminal style.

## Status
🚧 **v0.1 — first draft template** · data is mocked, no backend yet

## Stack
- Static HTML + CSS + a sprinkle of JS
- No build step
- Single `index.html` (~38 KB)
- Served at `https://on9claw.com/token-bill-dashboard/`

## Design
Follows the on9claw cyberpunk-terminal standard:
- Black bg, JetBrains Mono font, scanlines, grid dots
- Pink / cyan / green / yellow / red palette
- Terminal windows with red/yellow/green dots
- Glitch titles with chromatic aberration
- Boot-line animations

## Sections
1. Hero / boot screen
2. Status strip + KPI row
3. Account cards (one per service)
4. Usage chart + by-model table
5. Recent activity feed
6. Alerts log
7. Action buttons

## Accounts tracked (planned)
- `chatgpt-plus` — parklan@gmail.com, Plus plan, $20/mo
- `minimax` — China account, M2.5 / M2.7 / M3
- `openai-api` — platform.openai.com (no credits yet)
- (extensible: anthropic, google, etc.)

## Data sources (planned)
- Codex OAuth /v1/usage for ChatGPT Plus
- MiniMax API for China account
- platform.openai.com usage endpoint (when credits)
- Local log file (`/var/log/llm-bill.log`) for cross-account activity

## Next steps
- [ ] Backend API at `https://on9claw.com/token-bill-dashboard/api/*`
- [ ] Real data sources per account
- [ ] Auto-refresh every 30s
- [ ] Telegram alerts on threshold breach
- [ ] CSV export
- [ ] Add accounts Parklan owns (TBD)
