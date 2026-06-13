"""
Pulse — Live Football x Polymarket dashboard server.
Run: uvicorn server:app --reload --port 8770
"""
from __future__ import annotations
import asyncio
import json
import logging
import time
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from providers.espn import EspnClient, LEAGUES as ESPN_LEAGUES
from providers.polymarket import PolymarketClient
from providers.matcher import attach_markets_to_matches

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
log = logging.getLogger("pulse")

ROOT = Path(__file__).parent
STATIC = ROOT / "static"
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
DB_PATH = DATA / "pulse.db"

# --- in-memory state --------------------------------------------------------

class State:
    matches: list[dict] = []           # ESPN matches enriched with market + edge
    markets: list[dict] = []           # Polymarket markets not attached to a match
    markets_unmatched: list[dict] = [] # markets not matched to any match
    snapshots: dict[str, list[dict]] = {}  # market_id -> [{ts, price, volume24h}]
    last_update: dict[str, int] = {}   # section -> unix ts
    errors: list[dict] = []            # recent errors for debugging UI


state = State()

# --- SQLite snapshot store --------------------------------------------------

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS market_snapshots (
                market_id TEXT NOT NULL,
                ts INTEGER NOT NULL,
                price REAL,
                volume_24h REAL,
                PRIMARY KEY (market_id, ts)
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS match_events (
                match_id TEXT NOT NULL,
                ts INTEGER NOT NULL,
                score_home INTEGER,
                score_away INTEGER,
                state TEXT,
                PRIMARY KEY (match_id, ts)
            )
        """)


def save_snapshot(market_id: str, ts: int, price: float, vol24: float):
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT OR REPLACE INTO market_snapshots (market_id, ts, price, volume_24h) VALUES (?,?,?,?)",
            (market_id, ts, price, vol24),
        )


def save_match_event(match_id: str, ts: int, h: int, a: int, s: str):
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            "INSERT OR REPLACE INTO match_events (match_id, ts, score_home, score_away, state) VALUES (?,?,?,?,?)",
            (match_id, ts, h, a, s),
        )


def load_recent_snapshots(market_id: str, window_sec: int = 600) -> list[dict]:
    """For edge detection: compare current price to rolling consensus."""
    cutoff = int(time.time()) - window_sec
    with sqlite3.connect(DB_PATH) as con:
        rows = con.execute(
            "SELECT ts, price, volume_24h FROM market_snapshots "
            "WHERE market_id = ? AND ts >= ? ORDER BY ts ASC",
            (market_id, cutoff),
        ).fetchall()
    return [{"ts": r[0], "price": r[1], "vol24": r[2]} for r in rows]


# --- Edge / pulse calculation -----------------------------------------------

def calc_edge(match: dict) -> dict:
    """For the match's attached market, compare current price to recent average.
    Returns {edge_pct, volatility, direction, sparkline, has_history}.
    """
    out = {
        "edge_pct": 0.0,
        "volatility": 0.0,
        "direction": "flat",   # up | down | flat
        "sparkline": [],
        "has_history": False,
    }
    mk = match.get("market")
    if not mk:
        return out

    pm = mk["primary_market"]
    # Take the favourite price (max outcome price) as the proxy for "this team"
    fav_price = max((o["price"] or 0) for o in pm["outcomes"]) if pm["outcomes"] else 0
    snap = {"ts": int(time.time()), "price": fav_price, "vol24": pm["volume_24h"]}
    state.snapshots.setdefault(mk["id"], []).append(snap)
    # keep last 60 points in memory
    state.snapshots[mk["id"]] = state.snapshots[mk["id"]][-60:]

    # persist
    save_snapshot(mk["id"], snap["ts"], fav_price, pm["volume_24h"])

    history = load_recent_snapshots(mk["id"], window_sec=900)
    out["sparkline"] = [round(h["price"], 4) for h in history[-30:]]
    out["has_history"] = len(history) >= 3
    if not out["has_history"]:
        return out

    # Consensus = mean of last 5-15 min prices
    prices = [h["price"] for h in history[:-1]]  # exclude the just-added point
    if not prices:
        return out
    consensus = sum(prices) / len(prices)
    out["edge_pct"] = round((fav_price - consensus) * 100, 2)
    # volatility = stdev-like range
    if len(prices) > 1:
        rng = max(prices) - min(prices)
        out["volatility"] = round(rng, 4)
    if out["edge_pct"] > 0.5:
        out["direction"] = "up"
    elif out["edge_pct"] < -0.5:
        out["direction"] = "down"
    return out


# --- Polling loop ------------------------------------------------------------

async def poll_espn(espn: EspnClient, polymkt: PolymarketClient):
    """Single combined poller. ESPN every 30s, Polymarket every 60s."""
    while True:
        try:
            t0 = time.time()
            matches = await espn.fetch_all()
            log.info("ESPN fetched %d matches in %.2fs", len(matches), time.time() - t0)
            state.matches = matches
            state.last_update["espn"] = int(time.time())
            # persist score events
            for m in matches:
                if m["state"] in ("in", "post"):
                    save_match_event(
                        m["id"], int(time.time()),
                        m["home"]["score"], m["away"]["score"], m["state"]
                    )
        except Exception as e:  # noqa: BLE001
            log.exception("ESPN poll failed: %s", e)
            state.errors.insert(0, {"ts": int(time.time()), "src": "espn", "msg": str(e)})
            state.errors = state.errors[:20]

        # every other tick: pull polymarket
        if int(time.time()) // 30 % 2 == 0:
            try:
                t0 = time.time()
                events = await polymkt.fetch_football_events(limit=80)
                log.info("Polymarket fetched %d events in %.2fs", len(events), time.time() - t0)
                state.markets = events
                state.last_update["polymarket"] = int(time.time())
            except Exception as e:  # noqa: BLE001
                log.exception("Polymarket poll failed: %s", e)
                state.errors.insert(0, {"ts": int(time.time()), "src": "polymarket", "msg": str(e)})
                state.errors = state.errors[:20]

        # Attach markets to matches + compute edges
        state.matches, state.markets_unmatched = attach_markets_to_matches(
            state.matches, state.markets
        )
        for m in state.matches:
            m["edge"] = calc_edge(m)
        if not hasattr(state, "markets_unmatched"):
            state.markets_unmatched = []

        await asyncio.sleep(30)


# --- WebSocket fan-out -------------------------------------------------------

class WSManager:
    def __init__(self):
        self.clients: set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.clients.add(ws)

    def disconnect(self, ws: WebSocket):
        self.clients.discard(ws)

    async def broadcast(self, msg: dict):
        if not self.clients:
            return
        dead = []
        payload = json.dumps(msg, default=str)
        for ws in self.clients:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.clients.discard(ws)


ws_mgr = WSManager()


async def push_loop():
    """Push a lightweight delta to all clients every 5s."""
    last_matches = None
    last_markets = None
    while True:
        try:
            snap = {
                "type": "snapshot",
                "ts": int(time.time()),
                "last_update": state.last_update,
                "matches": state.matches,
                "markets_unmatched": state.markets_unmatched[:20],
            }
            # Naive change detection: hash of essentials
            digest_matches = json.dumps(state.matches, sort_keys=True, default=str)
            digest_markets = json.dumps(state.markets_unmatched[:20], sort_keys=True, default=str)
            if digest_matches != last_matches or digest_markets != last_markets:
                await ws_mgr.broadcast(snap)
                last_matches = digest_matches
                last_markets = digest_markets
        except Exception as e:  # noqa: BLE001
            log.exception("push_loop error: %s", e)
        await asyncio.sleep(5)


# --- App lifecycle -----------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    espn = EspnClient()
    poly = PolymarketClient()
    app.state.espn = espn
    app.state.poly = poly
    poll_task = asyncio.create_task(poll_espn(espn, poly))
    push_task = asyncio.create_task(push_loop())
    log.info("Pulse started — serving on http://localhost:8770")
    try:
        yield
    finally:
        poll_task.cancel()
        push_task.cancel()
        await espn.close()
        await poly.close()


app = FastAPI(title="Pulse — Live Football x Polymarket", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


@app.get("/")
async def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/snapshot")
async def api_snapshot():
    return {
        "ts": int(time.time()),
        "last_update": state.last_update,
        "matches": state.matches,
        "markets_unmatched": state.markets_unmatched[:20] if getattr(state, "markets_unmatched", None) else [],
        "leagues": [{"slug": s, "name": n, "code": c} for s, n, c in ESPN_LEAGUES],
    }


@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "ts": int(time.time()),
        "last_update": state.last_update,
        "match_count": len(state.matches),
        "market_count": len(state.markets),
        "client_count": len(ws_mgr.clients),
        "errors": state.errors[:5],
    }


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws_mgr.connect(ws)
    # send initial snapshot
    try:
        await ws.send_text(json.dumps({
            "type": "snapshot",
            "ts": int(time.time()),
            "last_update": state.last_update,
            "matches": state.matches,
            "markets_unmatched": getattr(state, "markets_unmatched", [])[:20],
        }, default=str))
        while True:
            # We don't need inbound messages, but read to detect disconnect
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_mgr.disconnect(ws)
