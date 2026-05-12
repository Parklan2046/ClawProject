#!/usr/bin/env python3
"""
HKExpress Price Scanner - Main Entry Point

Usage:
  python main.py scan          Run a one-time scan of all routes
  python main.py scan --route "HKG-NRT"   Scan a single route
  python main.py serve         Start the scheduler (continuous scanning)
  python main.py history       Show price history for all routes
  python main.py history --route "HKG-NRT"   Show history for one route
"""
import argparse
import asyncio
import logging
import os
import sys
from datetime import date, datetime

import yaml

from database import PriceDatabase
from scraper import HKExpressScraper
from notifier import Notifier
from scheduler import ScanScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("hkexpress")


def load_config(path: str = None) -> dict:
    """Load configuration from YAML file."""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)


async def scan_routes(config: dict, route_filter: str = None):
    """Scan all configured routes for flight prices."""
    scraper = HKExpressScraper(
        headless=config.get("scanner", {}).get("headless", True),
        max_retries=config.get("scanner", {}).get("max_retries", 3),
        delay_sec=config.get("scanner", {}).get("request_delay_sec", 2.0)
    )
    db = PriceDatabase(config.get("database", {}).get("path", "prices.db"))
    notifier = Notifier(config)

    # Get Telegram bot token from environment or file
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        token_file = os.path.expanduser("~/.config/openclaw/telegram_bot_token")
        if os.path.exists(token_file):
            with open(token_file) as f:
                bot_token = f.read().strip()
    notifier.bot_token = bot_token

    routes = config.get("routes", [])
    thresholds = config.get("thresholds", {})
    today = date.today().strftime("%Y-%m-%d")
    days_ahead = config.get("scanner", {}).get("days_ahead", 90)

    try:
        await scraper.start()
        logger.info(f"Scraper started (headless={scraper.headless})")

        for route in routes:
            rkey = f"{route['from']}-{route['to']}"
            if route_filter and rkey != route_filter:
                continue

            logger.info(f"Scanning: {route['name']} ({rkey})")
            results = await scraper.get_price_calendar(
                route["from"], route["to"], today, days_ahead
            )

            prices_found = 0
            for flight_date, price in results.items():
                if price is not None:
                    prices_found += 1
                    prev_price = db.get_previous_price(
                        route["from"], route["to"], flight_date
                    )
                    db.insert_price(
                        route["from"], route["to"], flight_date, price
                    )

                    # Check for price drops
                    threshold = thresholds.get(rkey)
                    if prev_price and price < prev_price:
                        drop_pct = ((prev_price - price) / prev_price) * 100
                        logger.info(
                            f"  📉 PRICE DROP: {route['name']} {flight_date} "
                            f"HK${prev_price:.0f} → HK${price:.0f} "
                            f"({drop_pct:.1f}%)"
                        )
                        notifier.notify_price_drop(
                            route["name"], flight_date, prev_price, price,
                            threshold
                        )
                    elif threshold and price <= threshold:
                        logger.info(
                            f"  🎯 BELOW THRESHOLD: {route['name']} "
                            f"{flight_date} HK${price:.0f} "
                            f"(threshold: HK${threshold:.0f})"
                        )
                        notifier.notify_price_drop(
                            route["name"], flight_date, prev_price, price,
                            threshold
                        )

            logger.info(
                f"  Done: {route['name']} — {prices_found} prices found "
                f"across {len(results)} dates"
            )

            # Brief summary if prices found
            if prices_found > 0:
                notifier.notify_scan_complete(
                    route["name"], prices_found, len(results)
                )

    except Exception as e:
        logger.error(f"Scan failed: {e}", exc_info=True)
        notifier.notify_error("all routes", str(e))
    finally:
        await scraper.stop()
        logger.info("Scraper stopped")


def show_history(config: dict, route_filter: str = None):
    """Display price history from the database."""
    db = PriceDatabase(config.get("database", {}).get("path", "prices.db"))
    routes = config.get("routes", [])

    for route in routes:
        rkey = f"{route['from']}-{route['to']}"
        if route_filter and rkey != route_filter:
            continue

        print(f"\n{'='*60}")
        print(f"  {route['name']} ({rkey})")
        print(f"{'='*60}")

        prices = db.get_latest_prices(route["from"], route["to"])
        if not prices:
            print("  No data yet.")
            continue

        print(f"  {'Date':<12} {'Price (HKD)':>12}")
        print(f"  {'-'*24}")
        for p in prices:
            price_str = f"HK${p['lowest_price']:,.0f}" if p['lowest_price'] else "N/A"
            print(f"  {p['flight_date']:<12} {price_str:>12}")

        if prices:
            valid = [p['lowest_price'] for p in prices if p['lowest_price']]
            if valid:
                print(f"  {'-'*24}")
                print(f"  Min: HK${min(valid):,.0f}  "
                      f"Avg: HK${sum(valid)/len(valid):,.0f}  "
                      f"Max: HK${max(valid):,.0f}")


async def serve(config: dict):
    """Start the continuous scheduler."""
    scheduler = ScanScheduler(
        scan_callback=lambda: scan_routes(config),
        interval_hours=config.get("scheduler", {}).get("interval_hours", 6),
        jitter_minutes=config.get("scheduler", {}).get("jitter_minutes", 15)
    )
    scheduler.start()
    logger.info("Scanner running. Press Ctrl+C to stop.")

    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        scheduler.stop()


def main():
    parser = argparse.ArgumentParser(
        description="HKExpress Flight Price Scanner"
    )
    sub = parser.add_subparsers(dest="command", help="Command to run")

    scan_p = sub.add_parser("scan", help="Run a one-time scan")
    scan_p.add_argument("--route", type=str, help="Filter by route (e.g. HKG-NRT)")
    scan_p.add_argument("--config", type=str, help="Path to config.yaml")

    sub.add_parser("serve", help="Start the scheduler")

    hist_p = sub.add_parser("history", help="Show price history")
    hist_p.add_argument("--route", type=str, help="Filter by route (e.g. HKG-NRT)")
    hist_p.add_argument("--config", type=str, help="Path to config.yaml")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    config = load_config(args.config)
    db_path = config.get("database", {}).get("path", "prices.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    if args.command == "scan":
        asyncio.run(scan_routes(config, args.route))
    elif args.command == "serve":
        asyncio.run(serve(config))
    elif args.command == "history":
        show_history(config, args.route)


if __name__ == "__main__":
    main()
