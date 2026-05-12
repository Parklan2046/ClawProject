"""
HKExpress Price Scanner - Notifications
Sends alerts via Telegram when price drops are detected.
"""
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


class Notifier:
    def __init__(self, config: dict, bot_token: Optional[str] = None):
        self.config = config
        self.bot_token = bot_token

    def send_telegram(self, message: str, chat_id: str) -> bool:
        """Send a message via Telegram Bot API."""
        if not self.bot_token:
            logger.warning("No Telegram bot token configured")
            return False

        try:
            resp = requests.post(
                f"{TELEGRAM_API}/bot{self.bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                },
                timeout=10
            )
            if resp.status_code == 200:
                logger.info(f"Telegram notification sent to {chat_id}")
                return True
            else:
                logger.error(f"Telegram send failed: {resp.status_code} {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Telegram notification error: {e}")
            return False

    def notify_price_drop(
        self, route_name: str, flight_date: str,
        old_price: Optional[float], new_price: float,
        threshold: Optional[float] = None
    ):
        """Notify about a price drop."""
        drop_text = ""
        if old_price:
            pct = ((old_price - new_price) / old_price) * 100
            drop_text = f"was <b>HK${old_price:,.0f}</b> (↓{pct:.0f}%)"
        else:
            drop_text = "first recorded price"

        message = (
            f"✈️ <b>HKExpress Price Drop!</b>\n\n"
            f"<b>{route_name}</b>\n"
            f"🛫 Date: <b>{flight_date}</b>\n"
            f"💰 New price: <b>HK${new_price:,.0f}</b>\n"
        )
        if drop_text:
            message += f"📉 Previous: {drop_text}\n"
        if threshold:
            message += f"🎯 Below threshold: HK${threshold:,.0f}\n"
        message += f"\n🔗 <a href='https://www.hkexpress.com'>Book on HKExpress</a>"

        tg_cfg = self.config.get("notifications", {}).get("telegram", {})
        if tg_cfg.get("enabled"):
            self.send_telegram(message, tg_cfg.get("chat_id", ""))

    def notify_scan_complete(self, route_name: str, prices_found: int,
                             dates_scanned: int):
        """Notify that a scan completed (only if interesting)."""
        if prices_found == 0:
            return  # Don't spam for empty results
        message = (
            f"🔍 <b>Scan Complete: {route_name}</b>\n"
            f"📅 Dates checked: {dates_scanned}\n"
            f"💵 Prices found: {prices_found}"
        )
        tg_cfg = self.config.get("notifications", {}).get("telegram", {})
        if tg_cfg.get("enabled"):
            self.send_telegram(message, tg_cfg.get("chat_id", ""))

    def notify_error(self, route_name: str, error: str):
        """Notify about scanner errors."""
        message = (
            f"⚠️ <b>HKExpress Scanner Error</b>\n"
            f"Route: {route_name}\n"
            f"Error: {error}"
        )
        tg_cfg = self.config.get("notifications", {}).get("telegram", {})
        if tg_cfg.get("enabled"):
            self.send_telegram(message, tg_cfg.get("chat_id", ""))
