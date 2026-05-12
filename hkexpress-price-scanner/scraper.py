"""
HKExpress Price Scanner - Scraper
Uses Google Flights to find HKExpress prices (bypasses Queue-It anti-bot).
"""
import asyncio
import logging
import re
from datetime import date, datetime, timedelta
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page

logger = logging.getLogger(__name__)


class HKExpressScraper:
    def __init__(self, headless: bool = True, max_retries: int = 2,
                 delay_sec: float = 3.0):
        self.headless = headless
        self.max_retries = max_retries
        self.delay_sec = delay_sec
        self.browser: Optional[Browser] = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-dev-shm-usage",
                  "--disable-blink-features=AutomationControlled"]
        )

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

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

    async def search_flight_price(
        self, route_from: str, route_to: str,
        flight_date_str: str
    ) -> Optional[float]:
        """Search Google Flights for HKExpress price on a route+date."""
        for attempt in range(self.max_retries):
            try:
                price = await self._scrape_google_flights(
                    route_from, route_to, flight_date_str
                )
                if price is not None:
                    return price
            except Exception as e:
                logger.warning(
                    f"Attempt {attempt + 1} failed for "
                    f"{route_from}→{route_to} {flight_date_str}: {e}"
                )
            if attempt < self.max_retries - 1:
                await asyncio.sleep(self.delay_sec)
        return None

    async def _scrape_google_flights(
        self, origin: str, dest: str, dep_date: str
    ) -> Optional[float]:
        """Scrape price from Google Flights."""
        url = (
            f"https://www.google.com/travel/flights"
            f"?q=Flights+to+{dest}+from+{origin}+on+{dep_date}"
            f"&curr=HKD"
        )

        page = await self._new_page()
        lowest_price = None

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(3000)

            # Wait for prices to load
            try:
                await page.wait_for_selector(
                    'span:has-text("HK$"), [aria-label*="HK$"], '
                    '[jsname] span:has-text("$"), '
                    'div[class*="price"], span[class*="price"]',
                    timeout=10000
                )
            except Exception:
                await page.wait_for_timeout(3000)

            # Get all text content and find HK$ prices
            text = await page.text_content("body")

            # Find all HK$ amounts - they look like "HK$1,234" or "$1,234"
            price_pattern = r'(?:HK\$|HKD\s*)\s*([\d,]+(?:\.\d{2})?)'
            matches = re.findall(price_pattern, text)
            
            prices = []
            for m in matches:
                try:
                    p = float(m.replace(",", ""))
                    if 50 < p < 50000:  # reasonable HKExpress price range
                        prices.append(p)
                except ValueError:
                    continue

            if prices:
                lowest_price = min(prices)
                logger.info(
                    f"  Google Flights: {origin}→{dest} {dep_date} = "
                    f"HK${lowest_price:.0f} (from {len(prices)} prices found)"
                )
            else:
                # Try direct selectors for flight prices
                price_els = page.locator(
                    'span[jsname="vKCVfe"], '
                    'span[jsname="V67aGc"], '
                    '[data-gs] span:has-text("$")'
                )
                count = await price_els.count()
                for i in range(min(count, 15)):
                    t = await price_els.nth(i).text_content()
                    p = self._parse_price(t)
                    if p and 50 < p < 50000:
                        if lowest_price is None or p < lowest_price:
                            lowest_price = p

                if lowest_price:
                    logger.info(
                        f"  Google Flights: {origin}→{dest} {dep_date} = "
                        f"HK${lowest_price:.0f}"
                    )

        except Exception as e:
            logger.error(f"Google Flights scrape error: {e}")
        finally:
            await page.close()

        return lowest_price

    def _parse_price(self, text: str) -> Optional[float]:
        """Parse a price string into a float."""
        if not text:
            return None
        cleaned = re.sub(r'[^\d.]', '', text.replace(',', ''))
        try:
            val = float(cleaned)
            return val if 50 < val < 50000 else None
        except ValueError:
            match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', text)
            if match:
                try:
                    val = float(match.group(1).replace(',', ''))
                    return val if 50 < val < 50000 else None
                except ValueError:
                    pass
        return None

    async def get_price_calendar(
        self, route_from: str, route_to: str,
        start_date: str, max_dates: int = 7
    ) -> dict[str, Optional[float]]:
        """Get prices for a range of dates."""
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
                if not price:
                    logger.info(f"  {date_str}: N/A")
            except Exception as e:
                logger.error(f"  {date_str}: error - {e}")
                results[date_str] = None

            if i < max_dates - 1:
                await asyncio.sleep(self.delay_sec)

        return results
