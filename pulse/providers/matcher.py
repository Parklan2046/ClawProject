"""
Team-name normalisation + fuzzy match between ESPN matches and Polymarket markets.
Goal: take an ESPN match (e.g. "Arsenal" vs "Paris Saint-Germain") and find the
corresponding Polymarket market if one exists.
"""
from __future__ import annotations
import re
import logging
from difflib import SequenceMatcher
from typing import Iterable

log = logging.getLogger("pulse.matcher")

# Common aliases — covers WC and top clubs. Keys lowercase, no punctuation.
ALIASES: dict[str, list[str]] = {
    "manchester united": ["man utd", "man united", "united"],
    "manchester city": ["man city", "city"],
    "paris saint-germain": ["psg", "paris sg"],
    "tottenham hotspur": ["spurs", "tottenham"],
    "real madrid": ["real"],
    "atletico madrid": ["atletico", "atlético", "atl madrid"],
    "bayern munich": ["bayern", "fc bayern"],
    "borussia dortmund": ["dortmund", "bvb"],
    "rb leipzig": ["leipzig"],
    "inter milan": ["inter", "internazionale"],
    "ac milan": ["milan"],
    "newcastle united": ["newcastle", "nufc"],
    "west ham united": ["west ham"],
    "brighton and hove albion": ["brighton"],
    "wolverhampton wanderers": ["wolves", "wolverhampton"],
    "nottingham forest": ["forest", "nott'm forest"],
    "afc bournemouth": ["bournemouth"],
    "leicester city": ["leicester"],
    "aston villa": ["villa"],
    "crystal palace": ["palace"],
    "los angeles fc": ["lafc"],
    "inter miami": ["inter miami cf"],
    "saudi arabia": ["ksa", "saudi"],
    "south korea": ["korea republic", "korea"],
    "ivory coast": ["côte d'ivoire", "cote d'ivoire"],
    "united states": ["usa", "us", "usmnt"],
}


def normalise(name: str) -> str:
    s = (name or "").lower()
    s = re.sub(r"\b(fc|cf|sc|cd|afc|the|club|deportivo|united)\b", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def expand(name: str) -> list[str]:
    n = normalise(name)
    variants = {n}
    for canonical, alts in ALIASES.items():
        if n == canonical or n in alts:
            variants.add(canonical)
            for a in alts:
                variants.add(a)
    return list(variants)


def _similar(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.9
    return SequenceMatcher(None, a, b).ratio()


def score_pair(home_name: str, away_name: str, market_title: str) -> float:
    """Higher = better match. We need BOTH team names to find the market."""
    title_n = normalise(market_title)
    home_variants = expand(home_name)
    away_variants = expand(away_name)
    best = 0.0
    for hv in home_variants:
        for av in away_variants:
            h_score = _similar(hv, title_n)
            a_score = _similar(av, title_n)
            # both teams should be present
            if h_score > 0.55 and a_score > 0.55:
                best = max(best, (h_score + a_score) / 2)
            elif h_score > 0.7 or a_score > 0.7:
                # one strong hit, accept weaker
                best = max(best, max(h_score, a_score) * 0.7)
    return best


def attach_markets_to_matches(
    matches: list[dict], markets: list[dict], threshold: float = 0.65
) -> tuple[list[dict], list[dict]]:
    """For each match, attach the best-matching market. Returns (matches, unmatched_markets)."""
    used_market_ids: set[str] = set()
    for m in matches:
        m["market"] = None
        m["market_match_score"] = 0.0
        if m.get("state") == "post":
            continue
        best = None
        best_score = 0.0
        for mk in markets:
            if mk["id"] in used_market_ids:
                continue
            s = score_pair(m["home"]["name"], m["away"]["name"], mk["title"])
            if s > best_score:
                best_score = s
                best = mk
        if best and best_score >= threshold:
            m["market"] = best
            m["market_match_score"] = round(best_score, 3)
            used_market_ids.add(best["id"])
    unmatched = [m for m in markets if m["id"] not in used_market_ids]
    return matches, unmatched
