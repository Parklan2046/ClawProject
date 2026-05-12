"""
HKExpress Price Scanner - API-Based Scraper
Uses direct API calls where possible, falls back to Playwright.
Discovered endpoints from api.hkexpress.com
"""
import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Optional

import requests
from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger(__name__)

API_BASE = "https://api.hkexpress.com"
SITE_URL = "https://www.hkexpress.com"


class HKExpressScraper:
    def __init__(self, headless: bool = True, max_retries: int = 3,
                 delay_sec: float = 2.0):
        self.headless = headless
        self.max_retries = max_retries
        self.delay_sec = delay_sec
        self.browser: Optional[Browser] = None
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36",
            "Accept": "application/json",
        })

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def _get_api_headers(self):
        return {
            "Content-Type": "application/json",
            "Origin": SITE_URL,
            "Referer": f"{SITE_URL}/en-hk",
            "Accept": "application/json, text/plain, */*",
        }

    async def search_flight_price(
        self, route_from: str, route_to: str,
        flight_date_str: str
    ) -> Optional[float]:
        """Search for a one-way flight price."""
        # Strategy 1: Try API directly
        price = self._try_api_search(route_from, route_to, flight_date_str)
        if price is not None:
            return price

        # Strategy 2: Fall back to Playwright browser
        for attempt in range(self.max_retries):
            try:
                price = await self._scrape_via_browser(
                    route_from, route_to, flight_date_str
                )
                if price is not None:
                    return price
            except Exception as e:
                logger.error(f"Browser attempt {attempt + 1}: {e}")
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.delay_sec * (attempt + 1))

        return None

    def _try_api_search(self, origin: str, dest: str,
                        dep_date: str) -> Optional[float]:
        """Try the HKExpress internal API for availability."""
        formats = [
            {
                "url": f"{API_BASE}/flt-booking-query/public/v1/availability",
                "body": {
                    "origin": origin, "destination": dest,
                    "departureDate": dep_date,
                    "currency": "HKD", "adultCount": 1,
                    "childCount": 0, "infantCount": 0
                }
            },
            {
                "url": f"{API_BASE}/flt-booking-query/public/v1/fares",
                "body": {
                    "originCode": origin, "destinationCode": dest,
                    "departDate": dep_date,
                    "currencyCode": "HKD", "pax": {"adult": 1}
                }
            },
        ]

        for fmt in formats:
            try:
                resp = self._session.post(
                    fmt["url"], json=fmt["body"],
                    headers=self._get_api_headers(),
                    timeout=15
                )
                if resp.status_code == 200:
                    data = resp.json()
                    price = self._extract_price_from_response(data)
                    if price:
                        return price
            except Exception:
                continue

        return None

    def _extract_price_from_response(self, data: dict) -> Optional[float]:
        """Extract the lowest price from API response."""
        # Try common keys
        for key in ["lowestPrice", "lowestFare", "fromPrice",
                     "price", "fare", "totalFare",
                     "totalPrice", "amount"]:
            if key in data and isinstance(data[key], (int, float)):
                return float(data[key])

        # Try nested: data.flights[0].price
        if "flights" in data and data["flights"]:
            for flight in data["flights"][:5]:
                for key in ["price", "fare", "totalPrice", "totalFare"]:
                    if key in flight and isinstance(flight[key], (int, float)):
                        return float(flight[key])
                    if isinstance(flight.get(key), dict):
                        if "amount" in flight[key]:
                            return float(flight[key]["amount"])

        # Try data.availability or data.calendar
        for section in ["availability", "calendar", "fares", "data"]:
            if section in data and isinstance(data[section], list):
                prices = []
                for item in data[section]:
                    for key in ["price", "fare", "amount", "total"]:
                        if key in item and isinstance(item[key], (int, float)):
                            prices.append(float(item[key]))
                if prices:
                    return min(prices)

        return None

    async def _scrape_via_browser(
        self, route_from: str, route_to: str, flight_date_str: str
    ) -> Optional[float]:
        """Scrape using Playwright with robust selectors."""
        page = await self._new_page()
        prices = None
        api_price = None

        try:
            # Intercept API responses to capture prices
            async def handle_response(response):
                nonlocal api_price
                if 'api.hkexpress.com' not in response.url:
                    return
                if api_price is not None:
                    return
                try:
                    body = await response.json()
                    extracted = self._extract_price_from_response(body)
                    if extracted:
                        api_price = extracted
                        logger.info(f"Captured API price: {extracted}")
                except Exception:
                    pass

            page.on('response', handle_response)

            # Navigate and search
            await page.goto(
                f"{SITE_URL}/en-hk/book-a-flight/select-your-flight",
                wait_until="networkidle", timeout=30000
            )
            await page.wait_for_timeout(2000)

            # Close any modals/popups
            await self._dismiss_modals(page)

            # Build URL params for direct search (if site supports it)
            search_url = (
                f"{SITE_URL}/en-hk/book-a-flight/select-your-flight"
                f"?origin={route_from}&destination={route_to}"
                f"&departureDate={flight_date_str}"
                f"&adults=1&children=0&infants=0"
            )
            try:
                await page.goto(search_url, wait_until="networkidle",
                                timeout=30000)
                await page.wait_for_timeout(5000)
            except Exception:
                pass

            # If API price was captured, use it
            if api_price:
                return api_price

            # Fall back to DOM extraction
            prices = await self._extract_prices_from_page(page)

        except Exception as e:
            logger.error(f"Browser scrape error: {e}")
        finally:
            await page.close()

        if prices and isinstance(prices, list) and len(prices) > 0:
            return min(prices)
        return api_price

    async def _dismiss_modals(self, page: Page):
        """Dismiss cookie banners, modals, etc."""
        dismiss_selectors = [
            'button:has-text("Accept All")',
            'button:has-text("Accept")',
            'button:has-text("OK")',
            '[aria-label="Close"]',
            '.close-button',
            '.modal-close',
        ]
        for sel in dismiss_selectors:
            try:
                el = page.locator(sel).first
                if await el.count() > 0 and await el.is_visible():
                    await el.click(timeout=2000)
                    await page.wait_for_timeout(500)
            except Exception:
                continue

    async def _new_page(self) -> Page:
        ctx = await self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            locale="en-HK",
            viewport={"width": 1280, "height": 800}
        )
        return await ctx.new_page()

    async def _extract_prices_from_page(self, page: Page) -> list[float]:
        """Extract all price values from the DOM."""
        prices = []
        selectors = [
            '[class*="price"]',
            '[class*="Price"]',
            '[class*="fare"]',
            '[class*="Fare"]',
            '[class*="amount"]',
            '[class*="Amount"]',
            '[data-testid*="price"]',
            'span:has-text("HK$")',
            'span:has-text("$")',
        ]

        for selector in selectors:
            try:
                elements = page.locator(selector)
                count = await elements.count()
                for i in range(min(count, 30)):
                    text = await elements.nth(i).text_content()
                    if text:
                        price = self._parse_price(text)
                        if price and 10 < price < 50000:
                            prices.append(price)
            except Exception:
                continue

        return prices

    def _parse_price(self, text: str) -> Optional[float]:
        """Parse a price string into a float."""
        import re
        cleaned = re.sub(r'[^\d.]', '', text.replace(',', ''))
        try:
            val = float(cleaned)
            return val if 10 < val < 50000 else None
        except ValueError:
            match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
            if match:
                try:
                    val = float(match.group(1).replace(',', ''))
                    return val if 10 < val < 50000 else None
                except ValueError:
                    pass
        return None

    async def get_price_calendar(
        self, route_from: str, route_to: str,
        start_date: str, max_dates: int = 7
    ) -> dict[str, Optional[float]]:
        """Get prices for a range of dates (practical limit to avoid detection)."""
        results = {}
        start = datetime.strptime(start_date, "%Y-%m-%d").date()

        for i in range(max_dates):
            d = start + timedelta(days=i)
            date_str = d.strftime("%Y-%m-%d")
            try:
                price = await self.search_flight_price(
                    route_from, route_to, date_str
                )
                results[date_str] = price
                logger.info(f"  {date_str}: HK${price:.0f}" if price else f"  {date_str}: N/A")
            except Exception as e:
                logger.error(f"  {date_str}: error - {e}")
                results[date_str] = None

            if i < max_dates - 1:
                await asyncio.sleep(self.delay_sec)

        return results
