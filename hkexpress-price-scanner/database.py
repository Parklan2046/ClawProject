"""
HKExpress Price Scanner - Database Module
SQLite storage for flight prices and historical tracking.
"""
import sqlite3
import os
from datetime import datetime
from typing import Optional


class PriceDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    route_from TEXT NOT NULL,
                    route_to TEXT NOT NULL,
                    flight_date TEXT NOT NULL,
                    lowest_price REAL,
                    currency TEXT DEFAULT 'HKD',
                    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_route_date
                ON price_snapshots(route_from, route_to, flight_date)
            """)
            conn.commit()

    def insert_price(self, route_from: str, route_to: str, flight_date: str,
                     lowest_price: Optional[float]):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT INTO price_snapshots (route_from, route_to, flight_date, lowest_price)
                   VALUES (?, ?, ?, ?)""",
                (route_from, route_to, flight_date, lowest_price)
            )
            conn.commit()

    def get_latest_prices(self, route_from: str, route_to: str, limit: int = 30):
        """Get latest prices for a route, grouped by flight_date."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT DISTINCT flight_date, lowest_price, scraped_at
                FROM price_snapshots
                WHERE route_from = ? AND route_to = ?
                ORDER BY flight_date ASC, scraped_at DESC
            """, (route_from, route_to)).fetchall()
            # Keep latest snapshot per date
            seen = {}
            for r in rows:
                if r["flight_date"] not in seen:
                    seen[r["flight_date"]] = dict(r)
            return list(seen.values())

    def get_price_history(self, route_from: str, route_to: str, flight_date: str,
                          limit: int = 20):
        """Get price history for a specific route+date."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT lowest_price, scraped_at
                FROM price_snapshots
                WHERE route_from = ? AND route_to = ? AND flight_date = ?
                ORDER BY scraped_at DESC
                LIMIT ?
            """, (route_from, route_to, flight_date, limit)).fetchall()
            return [dict(r) for r in rows]

    def get_previous_price(self, route_from: str, route_to: str,
                           flight_date: str) -> Optional[float]:
        """Get the most recent previous price for comparison."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT lowest_price FROM price_snapshots
                WHERE route_from = ? AND route_to = ? AND flight_date = ?
                  AND id < (SELECT MAX(id) FROM price_snapshots
                            WHERE route_from = ? AND route_to = ? AND flight_date = ?)
                ORDER BY id DESC LIMIT 1
            """, (route_from, route_to, flight_date,
                  route_from, route_to, flight_date)).fetchone()
            return row[0] if row else None

    def get_routes_summary(self):
        """Get summary stats for all routes."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT route_from, route_to,
                       MIN(lowest_price) as min_price,
                       AVG(lowest_price) as avg_price,
                       COUNT(*) as scans,
                       MAX(scraped_at) as last_scan
                FROM price_snapshots
                GROUP BY route_from, route_to
                ORDER BY route_to
            """).fetchall()
            return [dict(r) for r in rows]
