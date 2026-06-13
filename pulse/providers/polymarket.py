"""
Polymarket Gamma API client — no key required.
Docs: https://docs.polymarket.com/#gamma-api
We pull active football-related events with their markets + current prices.
"""
from __future__ import annotations
import time
import logging
import httpx
from typing import Any

log = logging.getLogger("pulse.polymarket")

GAMMA = "https://gamma-api.polymarket.com"


class PolymarketClient:
    def __init__(self, timeout: float = 15.0):
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": "Pulse/0.1 (ClawProject)"},
            follow_redirects=True,
        )

    async def close(self):
        await self._client.aclose()

    async def fetch_football_events(self, limit: int = 100) -> list[dict[str, Any]]:
        """Fetch active football events. Tag slug 'soccer' gets us the world cup + club football."""
        url = f"{GAMMA}/events"
        params = {
            "active": "true",
            "closed": "false",
            "limit": str(limit),
            "order": "volume24hr",
            "ascending": "false",
            "tag_slug": "soccer",
        }
        r = await self._client.get(url, params=params)
        r.raise_for_status()
        events = r.json()

        out: list[dict[str, Any]] = []
        for ev in events:
            norm = self._normalise_event(ev)
            if norm:
                out.append(norm)
        return out

    @staticmethod
    def _normalise_event(ev: dict) -> dict | None:
        try:
            markets = ev.get("markets") or []
            if not markets:
                return None
            # Use the highest-volume market as the "headline" market
            markets_sorted = sorted(
                markets, key=lambda m: float(m.get("volume24hr") or 0), reverse=True
            )
            primary = markets_sorted[0]

            # Parse outcome prices like '["0.42","0.58"]' or "[0.42, 0.58]"
            def parse_prices(raw):
                if isinstance(raw, list):
                    return [float(x) for x in raw if x is not None]
                if isinstance(raw, str):
                    raw = raw.strip("[] ")
                    parts = [p for p in raw.replace('"', "").split(",") if p]
                    return [float(p) for p in parts if p]
                return []

            outcomes_raw = primary.get("outcomes")
            if isinstance(outcomes_raw, str):
                try:
                    import json as _json
                    outcomes = _json.loads(outcomes_raw)
                except Exception:
                    outcomes = []
            else:
                outcomes = outcomes_raw or []
            prices = parse_prices(primary.get("outcomePrices"))

            # Pair outcomes with prices
            outcome_pairs = []
            for i, o in enumerate(outcomes):
                p = prices[i] if i < len(prices) else None
                outcome_pairs.append({"name": str(o), "price": p})

            # Volume + liquidity
            volume24 = float(primary.get("volume24hr") or 0)
            volume_total = float(primary.get("volumeNum") or 0)
            liquidity = float(primary.get("liquidity") or 0)

            return {
                "id": ev.get("id"),
                "slug": ev.get("slug"),
                "title": ev.get("title"),
                "description": ev.get("description", "")[:300],
                "end_date": ev.get("endDate"),
                "category": ev.get("category"),
                "tags": [t.get("label") for t in (ev.get("tags") or []) if isinstance(t, dict)],
                "primary_market": {
                    "id": primary.get("id"),
                    "question": primary.get("question"),
                    "group_item_title": primary.get("groupItemTitle"),
                    "outcomes": outcome_pairs,
                    "best_bid": float(primary.get("bestBid") or 0) or None,
                    "best_ask": float(primary.get("bestAsk") or 0) or None,
                    "spread": float(primary.get("spread") or 0) or None,
                    "volume_24h": volume24,
                    "volume_total": volume_total,
                    "liquidity": liquidity,
                },
                "all_markets_count": len(markets),
                "fetched_at": int(time.time()),
            }
        except Exception:  # noqa: BLE001
            return None
