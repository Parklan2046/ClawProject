# Pulse — Live Football × Polymarket

A live dashboard where **match scores and prediction-market odds breathe together**.
When a goal goes in, you watch the odds move on the same card. No tab-switching.

> **Vibe:** dark glass-morphism, cyan/pink/gold accents, animated aurora,
> signature **pulse bar** on every card (heartbeat speeds up with market volatility).

---

## Quick start

```bash
cd ClawProject/pulse
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
uvicorn server:app --reload --port 8770
```

Open <http://localhost:8770> — that's it. No API keys, no accounts.

---

## Data sources (both public, both key-free)

| Source | What we get | Endpoint |
|---|---|---|
| **ESPN public API** | live + upcoming + recent scores, status, clock, team logos, events | `https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard` |
| **Polymarket Gamma API** | active football prediction markets, prices, 24h volume | `https://gamma-api.polymarket.com/events?tag_slug=soccer` |

Polled every 30s (ESPN) and 60s (Polymarket) — pushed to the browser over WebSocket.

---

## Signature features

1. **🔴 Live Pulse Bar** — every match card has a heartbeat that speeds up
   as the attached market's recent volatility rises. Boring 0-0 with stable
   odds = calm pulse. Wild 2-2 with odds swinging = thumping.

2. **📐 Edge Detector** — for each match with a matched market, we compare
   current price to the 5-15min consensus. If the favourite's probability
   has shifted >0.5¢, a badge lights up (green for up, red for down, gold
   pulsing if the move >3¢). The card also gets a tiny sparkline of recent
   prices.

3. **🌍 "Where the Money Is"** — top 8 standalone Polymarket football
   markets by 24h volume, in the right rail. Click around — they'll open
   on polymarket.com.

4. **📈 Markets Moved feed** — left rail shows every >1¢ shift in attached
   markets since you opened the page, with relative timestamps.

---

## Project layout

```
pulse/
├── server.py              # FastAPI app, WebSocket, polling loop
├── providers/
│   ├── espn.py            # ESPN public API client
│   ├── polymarket.py      # Polymarket Gamma API client
│   └── matcher.py         # team-name fuzzy matching
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js             # vanilla JS + WebSocket + sparkline SVG
├── data/                  # SQLite snapshot history (auto-created)
├── requirements.txt
└── README.md
```

---

## Adding more leagues

Edit the `LEAGUES` list in `providers/espn.py`. ESPN slugs are easy to find —
browse <https://www.espn.com/soccer/> and look at the URL.

Examples of what's already in:

- `fifa.world` — FIFA World Cup
- `fifa.worldq` — WC qualifiers
- `uefa.champions`, `uefa.europa`, `uefa.euro`
- `eng.1`, `esp.1`, `ger.1`, `ita.1`, `fra.1`
- `bra.1`, `arg.1`, `usa.1`, `jpn.1`, `por.1`, `ned.1`, `ksa.1`

---

## API surface

| Route | What it does |
|---|---|
| `GET /` | The dashboard |
| `GET /api/snapshot` | Current full state (JSON) |
| `GET /api/health` | Liveness + counts |
| `WS /ws` | Live delta stream (5s heartbeat) |

---

## Roadmap (post-MVP)

- [ ] Country-flag cluster map ("globe of suffering")
- [ ] Click a match card → drawer with full event timeline
- [ ] Push notification on >5¢ moves (web push API)
- [ ] Multi-tab awareness with shared state
- [ ] Historical replay for past matches (use ESPN scoreboard `?dates=`)

---

## Disclaimer

This is a **read-only** dashboard. No bets, no wallet, no execution — that's
what `polymarket-execution` is for, and that's gated behind explicit user
consent there too. Pulse is for *watching* the market dance.

ESPN and Polymarket are used under their public-API terms. Don't republish
their data commercially without checking.
