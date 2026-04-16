"""
Woocommerce Bot

api.py
High‑level Bale Bot API wrapper using BaleHttpClient

@package    Woocommerce Bot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

from typing import Optional, Dict, Any
from .client import BaleHttpClient, BaleClientError
from src.logger.log_handler import get_logger
import asyncio

logger = get_logger("woobot.bale.api")


class BaleBot:
    """
    High‑level wrapper for Bale Bot API.
    اگر شئ `client` داده نشود، به‌صورت خودکار یک
    `BaleHttpClient` با توکن supplied ساخته می‌شود.
    """

    def __init__(self, token: str, client: Optional[BaleHttpClient] = None):
        self.token = token
        # اگر client پاس داده نشده، یک نمونه پیش‌فرض بساز
        self.client: BaleHttpClient = (
            client if client is not None else BaleHttpClient(token)
        )
        self.me: Optional[Dict[str, Any]] = None

    # -----------------------------------------------------------------
    # توابع اولیه‌ی lifecycle (start / stop) – این توابع فقط
    # فراخوانی‌های async client را به‌صورت شفاف در `BaleHttpClient`
    # اجرا می‌کنند.
    # -----------------------------------------------------------------
    async def start(self) -> None:
        """Open the underlying HTTP session."""
        await self.client.start()
        logger.info("BaleBot session opened (client started).")

    async def stop(self) -> None:
        """Close the underlying HTTP session."""
        await self.client.close()
        logger.info("BaleBot session closed (client stopped).")

    # -----------------------------------------------------------------
    # متدهای کاربردی (get_me, get_updates, send_message …)
    # -----------------------------------------------------------------
    async def get_me(self) -> Dict[str, Any]:
        """Get current bot info."""
        if self.me is None:
            self.me = await self.client.get_me()
        return self.me

    async def get_updates(
        self, offset: int = 0, timeout: int = 30
    ) -> Dict[str, Any]:
        """Get incoming updates from Bale API."""
        return await self.client.get_updates(offset=offset, timeout=timeout)

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: Optional[int] = None,
        disable_notification: bool = False,
        disable_web_page_preview: bool = False,
        parse_mode: str = "Markdown",
        reply_markup: Optional[dict] = None,  # <-- جدید: کیبورد اینلاین
    ) -> Dict[str, Any]:
        """
        Forward a message‑send request to the low‑level client.

        پارامتر ``reply_markup`` باید یک دیکشنری باشد که
        مطابق با ساختار **InlineKeyboardMarkup** بله باشد
        (مثلاً خروجی ``InlineKeyboardMarkup(...).to_dict()``).

        سایر پارامترها همانند قبل عمل می‌کنند.
        """
        return await self.client.send_message(
            chat_id=chat_id,
            text=text,
            reply_to_message_id=reply_to_message_id,
            disable_notification=disable_notification,
            disable_web_page_preview=disable_web_page_preview,
            parse_mode=parse_mode,
            reply_markup=reply_markup,  # پاس کردن به لایهٔ پایین
        )

    async def edit_message_reply_markup(
        self,
        chat_id: int,
        message_id: int,
        reply_markup: Optional[dict] = None,
    ) -> dict:
        return await self.client.edit_message_reply_markup(chat_id, message_id, reply_markup)

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False,
    ) -> dict:
        return await self.client.answer_callback_query(callback_query_id, text, show_alert)


    # -----------------------------------------------------------------
    # چند متد کمکی برای پردازش آپدیت‌ها (اختیاری)
    # -----------------------------------------------------------------
    async def process_update(self, update: Dict[str, Any]) -> None:
        logger.debug("Processing update: %s", update)

        if "message" in update:
            message = update["message"]
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text")
            if chat_id and text:
                logger.info("Received message from %d: %s", chat_id, text)
                await self.send_message(chat_id, f"شما گفتید: {text}")

    async def handle_updates(self, offset: int = 0, timeout: int = 30) -> None:
        while True:
            try:
                updates = await self.get_updates(offset=offset, timeout=timeout)
                logger.debug("Received updates: %s", updates)

                if "result" in updates and updates["result"]:
                    for upd in updates["result"]:
                        await self.process_update(upd)
                        offset = upd["update_id"] + 1

                await asyncio.sleep(1)

            except BaleClientError as e:
                logger.error("Bale API error: %s", e)
                await asyncio.sleep(5)
            except Exception as e:
                logger.error("Unexpected error in update handler: %s", e)
                await asyncio.sleep(5)
