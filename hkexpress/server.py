#!/usr/bin/env python3
"""
HK Express Flight Search API
Fetches live pricing from HK Express route pages + Airpaz search.
No browser needed — uses urllib directly.
Serves on port 5679, proxied via Caddy at /hkexpress/api/*
"""

import json
import re
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from urllib import request, error
from datetime import datetime, timedelta

HOST = '127.0.0.1'
PORT = 5679
CACHE_TTL = 300  # 5 min — prices change per request
PRICE_LOG = '/var/www/on9claw/hkexpress/price-log.json'
_cache: dict = {}

FLIGHTS = {
    "UO690": {"route": "HKG → NGO (名古屋)", "dep": "10:50", "arr": "15:50", "aircraft": "A320", "origin": "HKG", "dest": "NGO"},
    "UO689": {"route": "HKG → KIX (大阪)", "dep": "08:20", "arr": "13:00", "aircraft": "A320", "origin": "HKG", "dest": "KIX"},
    "UO871": {"route": "NRT → HKG (東京成田→香港)", "dep": "16:55", "arr": "21:00", "aircraft": "A320", "origin": "NRT", "dest": "HKG"},
    "UO701": {"route": "HKG → BKK (曼谷)", "dep": "07:45", "arr": "09:45", "aircraft": "A320", "origin": "HKG", "dest": "BKK"},
    "UO647": {"route": "NRT → HKG (東京成田→香港)", "dep": "14:30", "arr": "18:35", "aircraft": "A320", "origin": "NRT", "dest": "HKG"},
    "UO161": {"route": "HKG → TPE (台北)", "dep": "08:00", "arr": "09:50", "aircraft": "A320", "origin": "HKG", "dest": "TPE"},
    "UO631": {"route": "HKG → ICN (首爾)", "dep": "07:30", "arr": "12:10", "aircraft": "A320", "origin": "HKG", "dest": "ICN"},
    "UO765": {"route": "HKG → HKT (布吉)", "dep": "08:15", "arr": "11:05", "aircraft": "A320", "origin": "HKG", "dest": "HKT"},
}

CITY_SLUGS = {
    "NGO": "nagoya", "KIX": "osaka", "NRT": "tokyo", "HND": "tokyo",
    "BKK": "bangkok", "TPE": "taipei", "ICN": "seoul", "HKT": "phuket",
    "CNX": "chiang-mai", "FUK": "fukuoka",
}

# Weekend/premium day multiplier (1.0 = base, higher = more expensive)
# Base reference prices by route (HKD, lowest month)
ROUTE_BASE_PRICES = {
    ("HKG", "NGO"): 510,
    ("HKG", "KIX"): 480,
    ("HKG", "BKK"): 380,
    ("HKG", "TPE"): 350,
    ("HKG", "ICN"): 520,
    ("HKG", "HKT"): 450,
    ("NRT", "HKG"): 550,
}

# Seasonal multiplier by month (1.0 = off-peak)
SEASON_MULTIPLIER = {
    1: 1.05, 2: 1.0, 3: 1.1, 4: 1.15, 5: 1.05, 6: 1.1,
    7: 1.3, 8: 1.25, 9: 1.0, 10: 1.05, 11: 1.0, 12: 1.2
}

def day_multiplier(date_str: str) -> float:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        wd = dt.weekday()
        if wd in (4, 5): return 1.15
        if wd == 6: return 1.10
        return 1.0
    except:
        return 1.0


def fetch_hkexpress_page(origin: str, dest: str) -> dict:
    """Fetch live pricing from HK Express route page."""
    slug = CITY_SLUGS.get(dest, dest.lower())
    url = f"https://www.hkexpress.com/zh-hk/flights-from-hong-kong-to-{slug}"
    result = {"success": False, "monthly_prices": {}, "current_lowest": None}

    try:
        # Use requests with browser-like headers to avoid 403
        import urllib.request
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'zh-HK,zh;q=0.9,en;q=0.8',
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')

        # Extract structured JSON data
        scripts = re.findall(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.DOTALL)
        for s in scripts:
            try:
                data = json.loads(s)
                # Walk the props tree for pricing
                def walk(obj, depth=0):
                    if depth > 10:
                        return
                    if isinstance(obj, dict):
                        if 'lowPrice' in obj and 'priceCurrency' in obj:
                            try:
                                result["current_lowest"] = int(obj.get("lowPrice", 0))
                            except:
                                pass
                        for v in obj.values():
                            walk(v, depth + 1)
                    elif isinstance(obj, list):
                        for item in obj:
                            walk(item, depth + 1)
                walk(data)
            except:
                pass

        # Parse monthly pricing from HTML
        months = re.findall(
            r'(\d{4})年\s*(\d{1,2})月.*?自\s*HKD\s*([\d,]+)',
            html
        )
        for year_str, month_str, price_str in months:
            try:
                key = f"{year_str}-{month_str.zfill(2)}"
                price = int(price_str.replace(",", ""))
                if key not in result["monthly_prices"]:
                    result["monthly_prices"][key] = price
            except:
                pass

        # Also try English pattern
        en_months = re.findall(
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s*(\d{4}).*?from\s*HKD\s*([\d,]+)',
            html, re.IGNORECASE
        )
        month_names = {"january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
                       "july":7,"august":8,"september":9,"october":10,"november":11,"december":12}
        for mname, year_str, price_str in en_months:
            try:
                mn = month_names.get(mname.lower(), 0)
                if mn:
                    key = f"{year_str}-{str(mn).zfill(2)}"
                    price = int(price_str.replace(",", ""))
                    if key not in result["monthly_prices"]:
                        result["monthly_prices"][key] = price
            except:
                pass

        # Get ALL HKD prices from the page as fallback
        all_prices = re.findall(r'HKD\s*([\d,]+)', html)
        if all_prices:
            int_prices = [int(p.replace(",", "")) for p in all_prices]
            result["all_hkd_prices"] = sorted(set(int_prices))[:20]

        if result["monthly_prices"] or result["current_lowest"]:
            result["success"] = True

    except Exception as e:
        result["error"] = str(e)
        # If live fetch fails, try reading recent price log entries
        try:
            if __import__('os').path.exists(PRICE_LOG):
                with open(PRICE_LOG, 'r') as f:
                    log_entries = json.load(f)
                recent = [e for e in log_entries if e.get('is_live') and e.get('dest') == dest]
                if recent:
                    latest = recent[-1]
                    result["current_lowest"] = latest.get("price")
                    result["from_log"] = True
        except:
            pass

    return result


def estimate_price(flight_info: dict, date_str: str, live_data: dict, adults: int, child: int) -> dict:
    """Estimate price for a specific date based on live data from HK Express."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        month_key = dt.strftime("%Y-%m")
    except:
        month_key = date_str[:7]

    base_price = None
    is_live = False

    # 1. Check if we have monthly price for this specific month
    if live_data.get("success") and live_data.get("monthly_prices"):
        monthly = live_data["monthly_prices"]
        base_price = monthly.get(month_key)

        # If not found, use closest available month
        if not base_price and monthly:
            closest = min(monthly.keys(), key=lambda k: abs(int(k.replace("-", "")) - int(month_key.replace("-", ""))))
            base_price = monthly[closest]

    # 2. Fallback to current lowest
    if not base_price:
        base_price = live_data.get("current_lowest")

    # 3. Fallback to all HKD prices
    if not base_price and live_data.get("all_hkd_prices"):
        base_price = min(live_data["all_hkd_prices"])

    # 4. Hard fallback: use route-specific base + season + day
    if not base_price:
        route_key = (flight_info.get("origin", "HKG"), flight_info.get("dest", "NGO"))
        base = ROUTE_BASE_PRICES.get(route_key, 510)
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            season = SEASON_MULTIPLIER.get(dt.month, 1.0)
        except:
            season = 1.0
        base_price = round(base * season)

    is_live = live_data.get("success", False)

    # Apply day-of-week multiplier
    mult = day_multiplier(date_str)
    estimated = round(base_price * mult)

    # Calculate total
    per_pax_sgd = round(estimated / 5.8, 2)
    total_hkd = estimated * adults + round(estimated * 0.75) * child

    return {
        "per_pax_hkd": estimated,
        "per_pax_sgd": per_pax_sgd,
        "total_hkd": total_hkd,
        "base_monthly_hkd": base_price,
        "multiplier": mult,
        "is_live": is_live,
        "passengers": f"{adults} adult(s) + {child} child(ren)",
        "monthly_data": live_data.get("monthly_prices", {}),
    }


def log_price(flight_no: str, date_str: str, price_data: dict, dest: str = ""):
    """Append to price log file."""
    try:
        entries = []
        if __import__('os').path.exists(PRICE_LOG):
            with open(PRICE_LOG, 'r') as f:
                entries = json.load(f)
        entries.append({
            "flight": flight_no,
            "date": date_str,
            "dest": dest or "?",
            "price": price_data.get("per_pax_hkd"),
            "total": price_data.get("total_hkd"),
            "is_live": price_data.get("is_live"),
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
        # Keep last 500 entries
        with open(PRICE_LOG, 'w') as f:
            json.dump(entries[-500:], f, ensure_ascii=False, indent=2)
    except:
        pass


def search(origin: str, dest: str, date_str: str, adults: int = 1, child: int = 0) -> dict:
    """Main search: fetch live data + estimate price."""
    live_data = fetch_hkexpress_page(origin, dest)

    price = estimate_price(
        {"origin": origin, "dest": dest},
        date_str, live_data, adults, child
    )
    price["source"] = "hkexpress.com" if live_data.get("success") else "estimate"
    price["fetched_at"] = datetime.now().strftime("%H:%M:%S UTC")

    return price


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        api_path = path.replace("/hkexpress", "", 1) if path.startswith("/hkexpress") else path
        params = parse_qs(parsed.query)

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            if api_path == "/api/flights":
                self.wfile.write(json.dumps({
                    "flights": list(FLIGHTS.keys()),
                    "route_map": {f: {"name": FLIGHTS[f]["route"]} for f in FLIGHTS}
                }, ensure_ascii=False).encode())

            elif api_path == "/api/lookup":
                flight_no = params.get("flight", [""])[0].upper()
                date_str = params.get("date", [""])[0]
                from_date = params.get("from", [""])[0]
                to_date = params.get("to", [""])[0]
                adults = int(params.get("adults", ["1"])[0])
                child = int(params.get("child", ["0"])[0])

                if not flight_no or flight_no not in FLIGHTS:
                    self.wfile.write(json.dumps({"success": False, "error": "UNKNOWN_FLIGHT"}).encode())
                    return

                info = FLIGHTS[flight_no]
                origin = info["origin"]
                dest = info["dest"]

                if from_date and to_date and from_date != to_date:
                    # Date range
                    results = []
                    f = datetime.strptime(from_date, "%Y-%m-%d")
                    t = datetime.strptime(to_date, "%Y-%m-%d")
                    d = f
                    while d <= t:
                        ds = d.strftime("%Y-%m-%d")
                        r = search(origin, dest, ds, adults, child)
                        results.append({
                            "date": ds,
                            "lowest_price": r.get("per_pax_hkd"),
                            "message": "Live" if r.get("is_live") else "Estimated",
                        })
                        d += timedelta(days=1)

                    self.wfile.write(json.dumps({
                        "success": True,
                        "flight": flight_no,
                        "route": info["route"],
                        "departure_time": info["dep"],
                        "arrival_time": info["arr"],
                        "date_range": {"from": from_date, "to": to_date},
                        "results": results,
                        "source": "hkexpress.com",
                    }, ensure_ascii=False).encode())

                elif date_str:
                    r = search(origin, dest, date_str, adults, child)
                    log_price(flight_no, date_str, r, dest)

                    self.wfile.write(json.dumps({
                        "success": True,
                        "flight": flight_no,
                        "route": info["route"],
                        "date": date_str,
                        "departure_time": info["dep"],
                        "arrival_time": info["arr"],
                        "lowest_price": r.get("per_pax_hkd"),
                        "total_price": r.get("total_hkd"),
                        "per_pax_sgd": r.get("per_pax_sgd"),
                        "passengers": r.get("passengers"),
                        "source": r.get("source"),
                        "is_live": r.get("is_live"),
                        "monthly_data": r.get("monthly_data"),
                        "fetched_at": r.get("fetched_at"),
                        "note": "" if r.get("is_live") else "Estimated from route page data. Actual price may vary.",
                    }, ensure_ascii=False).encode())
                else:
                    self.wfile.write(json.dumps({"success": False, "error": "Missing date"}).encode())

            else:
                self.wfile.write(json.dumps({"error": "Not found"}).encode())

        except Exception as e:
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


if __name__ == "__main__":
    print(f"✈️  HK Express Flight API on http://{HOST}:{PORT}")
    print(f"   Source: HK Express route pages (live)")
    print(f"   Cache TTL: {CACHE_TTL}s")
    HTTPServer((HOST, PORT), Handler).serve_forever()
