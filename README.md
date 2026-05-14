# Parklan Clawhub

> A curated hub of AI-powered tools, experiments, and dashboards — built with a retro-futuristic pulse.

**Live at [on9claw.com](https://on9claw.com)** · **GitHub Actions auto-deploy to DigitalOcean**

---

## Projects

### Transport & Commute

#### 🚌 Bus ETA (`722-eta/`) — Ready
Real-time bus arrival checker for KMB (九巴) and Citybus (城巴).
- Dual-operator ETA lookup with route / stop search
- Joint-route auto-merge for shared stops
- Bookmarked stops with auto-refresh countdown
- Built-in Cantonese AI chatbot for bus route enquiries
- Data source: data.gov.hk Transport APIs

#### 🅿️ Parking Monitor (`parking-monitor/`) — Ready
Real-time parking slot availability at Heung Yuen Wai (香園圍) border checkpoint.
- Live slot counts by vehicle type (private car, motorcycle, goods vehicle, disabled)
- Day-by-day booking window display
- Deep-link to official booking site

---

### Financial / Markets

#### 📊 AI Stock Investment Report (`stock-report/`) — POC
AI-generated Cantonese stock analysis report. Enter a ticker (HK/US) — get fundamentals, technicals, risk, and recommendation.
- HK & US stock autocomplete search with validation
- yfinance data: PE, EPS, ROE, beta, MA20/50, RSI, analyst ratings
- Cantonese AI report via OpenRouter (MiMo v2 Pro)
- Visual score circle, buy/hold/sell banner, sectioned report cards

#### 📈 US Market Radar (`us-market-radar/`) — Beta
US market snapshot dashboard for key indices (SPY, QQQ, DIA, IWM, VIX).
- 6-index summary grid (price, change %, open monitor)
- Individual stock quote lookup
- Server-side Yahoo Finance quote fetcher via cron / GitHub Actions
- Dark-mode panel UI

#### 🧪 BTC 5m Strategy Lab (`btc-5m-strategy-lab/`) — Beta
Paper-trading sandbox for 5-minute BTC prediction market strategies (Polymarket).
- Strategy rule builder (entry price, take profit %, stop loss %)
- Break-even win rate calculator
- Simulated trade journal and expectancy tracking
- Paper-only mode — no real orders

#### 🔒 Polymarket Execution (`polymarket-execution/`) — Private
Private execution dashboard for Polymarket trading (Phase 1 — staging).
- Account connection plumbing (wallet / API auth placeholders)
- Execution modes: Paper / Preview / Live (disabled)
- Risk controls: stake cap, max trades, loss limits, kill-switch
- Log panel and order preview UI

---

### AI & Productivity

#### 📝 QuickNotes (`quicknotes/`) — Ready
AI-powered personal note organizer. Send notes via Signal — AI auto-organizes.
- Captures notes from Signal messaging
- AI auto-categorization, tagging, and summarization
- Searchable timeline dashboard with smart date/reminder detection
- Private, local JSON storage

#### 🎧 Ebook Cantonese Narration (`ebook-canto-poc/`) — POC
Convert EPUB / text into natural spoken Cantonese narration.
- EPUB / plain text import
- AI-powered Cantonese rewriting (MiniMax M2.5)
- Text-to-speech playback (MiniMax TTS + browser SpeechSynthesis)
- Emotion and prosody tagging

---

### Office & Social

#### 🧋 Tea Treat (`tea-treat/`) — POC
Office group tea/drink ordering helper. Create, share, auto-consolidate.
- Generate a shareable order link
- Scrape menus from Foodpanda / Keeta links
- Colleagues pick their drinks individually
- Automatic master order consolidation
- SQLite storage for order data

#### 💰 Lunch Wallet (`lunch-wallet/`) — Private
Shared wallet tool for group lunch expense tracking and balance settling.
- Multi-member group tracking
- Expense entry per person
- Balance / owe summaries
- Password-protected, localStorage persistence

---

### Entertainment

#### 🎵 Spotify AI Dashboard (`spotify-dashboard/`) — Beta
Polished Spotify control panel with now-playing and device management.
- Now-playing display with album art
- Active devices list and queue preview
- Play / pause / skip / search controls
- Access-code protected (OAuth proxy behind `spotify_dashboard_server.py`)

---

### Price Tracking

#### ✈️ HKExpress Price Scanner (`hkexpress-price-scanner/`) — Ready
Periodic flight price scanner for configured HKExpress routes.
- Configurable route definitions (`config.yaml`)
- Playwright-based web scraping
- Historical price tracking in SQLite
- Telegram / email price-drop alerts
- APScheduler continuous scanning
- Auto-generated HTML price history report

---

## Tech Stack

| Layer | Tech |
|-------|------|
| **Backend** | Python 3 (`http.server`, Flask), OpenRouter API, yfinance, Playwright, APScheduler |
| **Frontend** | Vanilla HTML5 / CSS3 / JS (no frameworks), glass-morphism dark themes, CSS grid layouts |
| **AI** | OpenRouter (MiMo v2 Pro), MiniMax (M2.5 chat + TTS) |
| **Data** | Yahoo Finance, Polymarket CLOB, Spotify Web API, data.gov.hk, SQLite, JSON |
| **Infra** | DigitalOcean VPS, GitHub Actions CI/CD, Nginx reverse proxy |

---

## Deployment

Push to `main` triggers GitHub Actions (`.github/workflows/deploy.yml`) which:
1. SSH into a DigitalOcean Droplet
2. Pulls latest code
3. Restarts all Python micro-servers (ports 8766–8770, 5000)
4. Serves static files via Nginx at `on9claw.com`

---

## Disclaimer

All projects are **personal tools and experiments**. Financial tools (stock report, BTC lab, Polymarket execution) are for educational / paper-trading use only and do not constitute investment advice. Private projects are access-controlled.

---

<p align="center">Built with 🦞 by Parklan</p>
