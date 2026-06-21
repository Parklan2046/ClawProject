"""
FIFA26 — ESPN public API client (stdlib only).
Docs: https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard
"""
from __future__ import annotations
import json
import logging
import re
import time
import urllib.error
import urllib.request

log = logging.getLogger("fifa26.espn")

LEAGUES: list[tuple[str, str, str]] = [
    ("fifa.world", "世界盃", "世界盃"),
]

BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
USER_AGENT = "Mozilla/5.0 (fifa26-dashboard)"

_ROUND_SLUG_TO_LABEL = {
    "group-stage": "分組賽",
    "round-of-32": "32強",
    "round-of-16": "16強",
    "quarterfinals": "半準決賽",
    "semifinals": "準決賽",
    "third-place": "季軍戰",
    "final": "決賽",
}

_ROUND_LABEL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"third[-\s]?place", re.IGNORECASE), "third-place"),
    (re.compile(r"round of 16|round-of-16|16強|十六強|octavos(?:\s+de\s+final)?|dieciseisavos|dieciséisavos|八分之一", re.IGNORECASE), "round-of-16"),
    (re.compile(r"round of 32|round-of-32|32強|三十二強|treinta y dos|treintaidosavos", re.IGNORECASE), "round-of-32"),
    (re.compile(r"quarter[-\s]?final|半準決賽|準決賽.*8|quarterfinal|八強|四強|cuartos", re.IGNORECASE), "quarterfinals"),
    (re.compile(r"semi[-\s]?final|準決賽|半决赛", re.IGNORECASE), "semifinals"),
    (re.compile(r"\bfinal\b|大決賽", re.IGNORECASE), "final"),
    (re.compile(r"group stage|分組賽", re.IGNORECASE), "group-stage"),
]

_GROUP_RE = re.compile(r"Group\s+([A-L])\b", re.IGNORECASE)


class EspnClient:
    def __init__(self, timeout: float = 12.0):
        self._timeout = timeout
        self._headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    def fetch_league(self, slug: str) -> tuple[dict | None, bool]:
        """Return (payload, was_rate_limited)."""
        url = f"{BASE}/{slug}/scoreboard"
        req = urllib.request.Request(url, headers=self._headers)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                return json.loads(resp.read().decode("utf-8", "ignore")), False
        except urllib.error.HTTPError as e:
            if e.code == 429:
                log.warning("ESPN %s HTTP 429 — backing off", slug)
                return None, True
            log.warning("ESPN %s fetch failed: %s", slug, e)
            return None, False
        except Exception as e:  # noqa: BLE001
            log.warning("ESPN %s fetch failed: %s", slug, e)
            return None, False

    def fetch_all(self) -> tuple[list[dict], bool]:
        """Return (matches, was_rate_limited). was_rate_limited=True triggers backoff."""
        out: list[dict] = []
        rate_limited = False
        for slug, name, code in LEAGUES:
            data, rl = self.fetch_league(slug)
            if rl:
                rate_limited = True
            if not data:
                continue
            for ev in data.get("events", []):
                norm = self._normalise(ev, name, code)
                if norm:
                    out.append(norm)
        return out, rate_limited

    @staticmethod
    def _normalise_status(state: str, detail: str = "") -> tuple[str, str]:
        """Map ESPN state -> (status, status_label). status in {scheduled, in_progress, final, postponed}."""
        s = (state or "pre").lower()
        d = (detail or "").lower()
        if s == "in":
            return "in_progress", detail or "進行中"
        if s == "post":
            return "final", detail or "完場"
        if "postpone" in d or "suspend" in d:
            return "postponed", detail or "延期"
        return "scheduled", detail or "未開賽"

    @staticmethod
    def _normalise_round(round_slug: str | None, comp_type_text: str | None) -> tuple[str, str]:
        """Map round -> (slug, label)."""
        if round_slug and round_slug in _ROUND_SLUG_TO_LABEL:
            return round_slug, _ROUND_SLUG_TO_LABEL[round_slug]
        if comp_type_text:
            for pat, slug in _ROUND_LABEL_PATTERNS:
                if pat.search(comp_type_text):
                    return slug, _ROUND_SLUG_TO_LABEL.get(slug, comp_type_text)
        if round_slug:
            return round_slug, _ROUND_SLUG_TO_LABEL.get(round_slug, round_slug)
        return "group-stage", "分組賽"

    @staticmethod
    def _normalise(ev: dict, league_name: str, league_code: str) -> dict | None:
        try:
            comp = ev["competitions"][0]
            status = comp.get("status", {})
            status_type = status.get("type", {})
            raw_state = status_type.get("state", "pre")
            status_key, status_label = EspnClient._normalise_status(
                raw_state, status_type.get("detail", "")
            )
            clock = status.get("displayClock", "")
            period = status.get("period", 0)

            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                return None
            home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
            away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])

            def team(c):
                t = c.get("team", {})
                logos = t.get("logos") or []
                logo = t.get("logo")
                if not logo and logos:
                    logo = logos[0].get("href")
                iso = t.get("id") or ""
                raw_score = c.get("score")
                try:
                    score_val = int(raw_score) if raw_score is not None else 0
                except (TypeError, ValueError):
                    score_val = 0
                return {
                    "id": t.get("id"),
                    "iso": iso,
                    "name": t.get("displayName") or t.get("name"),
                    "short": t.get("abbreviation") or t.get("shortDisplayName"),
                    "logo": logo,
                    "color": t.get("color"),
                    "score": score_val,
                    "winner": bool(c.get("winner")),
                }

            season = ev.get("season") or {}
            comp_type = comp.get("type") or {}
            comp_type_text = comp_type.get("text") or comp_type.get("name") if isinstance(comp_type, dict) else None
            round_slug, round_label = EspnClient._normalise_round(season.get("slug"), comp_type_text)

            group_letter = None
            alt = comp.get("altGameNote") or ev.get("altGameNote") or ""
            m = _GROUP_RE.search(str(alt))
            if m:
                group_letter = m.group(1).upper()
            if not group_letter:
                for src in (comp.get("groupings"), ev.get("groupings"),
                            comp.get("groups"), comp.get("notes")):
                    if not src:
                        continue
                    for item in src:
                        if not isinstance(item, dict):
                            continue
                        for k in ("name", "abbreviation", "shortName", "label"):
                            v = item.get(k)
                            if isinstance(v, str):
                                mm = _GROUP_RE.search(v)
                                if mm:
                                    group_letter = mm.group(1).upper()
                                    break
                        if group_letter:
                            break
                    if group_letter:
                        break

            if not group_letter and round_slug == "group-stage":
                home_name = (home.get("team") or {}).get("displayName") or ""
                away_name = (away.get("team") or {}).get("displayName") or ""
                from providers.group_table import GROUP_TABLE  # noqa: PLC0415
                for letter, members in GROUP_TABLE.items():
                    if home_name in members and away_name in members:
                        group_letter = letter
                        break

            return {
                "id": ev.get("id"),
                "uid": ev.get("uid"),
                "name": ev.get("name"),
                "short": ev.get("shortName"),
                "date": ev.get("date"),
                "league": league_name,
                "league_code": league_code,
                "status": status_key,
                "status_label": status_label,
                "status_detail": status_type.get("detail", ""),
                "state": raw_state,
                "clock": clock,
                "period": period,
                "venue": (comp.get("venue") or {}).get("fullName"),
                "round_slug": round_slug,
                "round": round_label,
                "group": group_letter,
                "home": team(home),
                "away": team(away),
                "fetched_at": int(time.time()),
            }
        except Exception:  # noqa: BLE001
            return None