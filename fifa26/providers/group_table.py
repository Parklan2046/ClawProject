"""Static 2026 World Cup group composition — fallback group-letter resolver.

The 2026 FIFA World Cup has 12 groups of 4 teams each (A–L), 48 teams in total.
ESPN's scoreboard occasionally omits groupings on individual match records; in
that case we cross-reference the home/away displayName against this table.
"""
from __future__ import annotations

GROUP_TABLE: dict[str, list[str]] = {
    "A": ["Mexico", "South Africa", "South Korea", "Denmark"],
    "B": ["Canada", "Italy", "Qatar", "Switzerland"],
    "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
    "D": ["United States", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Côte d'Ivoire", "Ecuador", "Curaçao"],
    "F": ["Netherlands", "Japan", "Tunisia", "Sweden"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Uruguay", "Cape Verde", "Saudi Arabia"],
    "I": ["France", "Senegal", "Norway", "Gabon"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "Colombia", "Uzbekistan", "DR Congo"],
    "L": ["England", "Croatia", "Panama", "Ghana"],
}