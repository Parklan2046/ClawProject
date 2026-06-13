"""
ESPN public API client — no key required.
Docs: https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard
Leagues we care about: World Cup, major European + South American competitions.
"""
from __future__ import annotations
import time
import logging
import httpx
from typing import Any

log = logging.getLogger("pulse.espn")

# A curated set of leagues to poll. ESPN slug -> (display name, country code)
LEAGUES: list[tuple[str, str, str]] = [
    ("fifa.world",            "World Cup",         "WORLD"),
    ("fifa.worldq",           "WC Qualifiers",     "WC-Q"),
    ("uefa.champions",        "UEFA Champions",    "UCL"),
    ("uefa.europa",           "UEFA Europa",       "UEL"),
    ("uefa.euro",             "UEFA Euro",         "EURO"),
    ("eng.1",                 "Premier League",    "EPL"),
    ("esp.1",                 "La Liga",           "LIGA"),
    ("ger.1",                 "Bundesliga",        "BUN"),
    ("ita.1",                 "Serie A",           "SER"),
    ("fra.1",                 "Ligue 1",           "LG1"),
    ("por.1",                 "Primeira Liga",     "POR"),
    ("ned.1",                 "Eredivisie",        "ERE"),
    ("bra.1",                 "Brasileirão",       "BRA"),
    ("arg.1",                 "Liga Profesional",  "ARG"),
    ("usa.1",                 "MLS",               "MLS"),
    ("ksa.1",                 "Saudi Pro League",  "SAU"),
    ("jpn.1",                 "J1 League",         "JPN"),
]

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"


class EspnClient:
    def __init__(self, timeout: float = 12.0):
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": "Pulse/0.1 (ClawProject)"},
            follow_redirects=True,
        )

    async def close(self):
        await self._client.aclose()

    async def fetch_league(self, slug: str) -> dict[str, Any]:
        url = f"{BASE}/{slug}/scoreboard"
        r = await self._client.get(url)
        r.raise_for_status()
        return r.json()

    async def fetch_all(self) -> list[dict[str, Any]]:
        """Fetch all configured leagues, normalise + tag with display name."""
        out: list[dict[str, Any]] = []
        for slug, name, code in LEAGUES:
            try:
                data = await self.fetch_league(slug)
            except Exception as e:  # noqa: BLE001
                log.warning("ESPN %s failed: %s", slug, e)
                continue
            for ev in data.get("events", []):
                norm = self._normalise(ev, name, code)
                if norm:
                    out.append(norm)
        return out

    @staticmethod
    def _normalise(ev: dict, league_name: str, league_code: str) -> dict | None:
        try:
            comp = ev["competitions"][0]
            status = comp.get("status", {})
            status_type = status.get("type", {})
            state = status_type.get("state", "pre")  # pre | in | post
            clock = status.get("displayClock", "")
            period = status.get("period", 0)

            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                return None
            home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
            away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

            def team(c):
                t = c.get("team", {})
                return {
                    "id": t.get("id"),
                    "name": t.get("displayName") or t.get("name"),
                    "short": t.get("abbreviation") or t.get("shortDisplayName"),
                    "logo": (t.get("logos") or [{}])[0].get("href"),
                    "color": t.get("color"),
                    "score": int(c.get("score") or 0),
                    "winner": c.get("winner"),
                }

            return {
                "id": ev.get("id"),
                "uid": ev.get("uid"),
                "name": ev.get("name"),
                "short": ev.get("shortName"),
                "date": ev.get("date"),
                "league": league_name,
                "league_code": league_code,
                "state": state,                 # pre | in | post
                "clock": clock,                 # "67'" or "HT" or "FT"
                "period": period,               # 1, 2, 5 (pens)
                "status_detail": status_type.get("detail", ""),
                "venue": (comp.get("venue") or {}).get("fullName"),
                "home": team(home),
                "away": team(away),
                "fetched_at": int(time.time()),
            }
        except Exception:  # noqa: BLE001
            return None
