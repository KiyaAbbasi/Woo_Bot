"""
Woocommerce Bot

client.py
Low‑level async HTTP client for Bale Bot API with retry and timeout support

@package    Woocommerce Bot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

import asyncio
import aiohttp
from typing import Any, Optional, Dict, List
from src.logger.log_handler import get_logger

# ─── Constants ────────────────────────────────────────────────────────────────
DEFAULT_TIMEOUT = 30        # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2             # seconds between retries
RETRY_MULTIPLIER = 2        # exponential backoff multiplier

logger = get_logger("woobot.bale.client")


class BaleClientError(Exception):
    """Base exception for Bale HTTP client errors."""
    pass


class BaleNetworkError(BaleClientError):
    """Raised on connection/timeout failures."""
    pass


class BaleAPIError(BaleClientError):
    """Raised when Bale API returns an error response."""

    def __init__(self, status_code: int, description: str):
        self.status_code = status_code
        self.description = description
        super().__init__(f"[{status_code}] {description}")


# ─── Client ───────────────────────────────────────────────────────────────────
class BaleHttpClient:
    """
    Async HTTP client for communicating with Bale Bot API.
    Supports retry with exponential backoff and configurable timeout.
    """

    def __init__(
        self,
        token: str,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        self.base_url = f"https://tapi.bale.ai/bot{token}"
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self._session: Optional[aiohttp.ClientSession] = None

    # ─── Session lifecycle ────────────────────────────────────────────────────
    async def start(self) -> None:
        """Open the HTTP session. Call once before making requests."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
            logger.info("BaleHttpClient session started.")

    async def close(self) -> None:
        """Close the HTTP session gracefully."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("BaleHttpClient session closed.")

    async def __aenter__(self) -> "BaleHttpClient":
        await self.start()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    # ─── Core request ─────────────────────────────────────────────────────────
    async def post(self, method: str, payload: dict) -> dict:
        """
        Send a POST request to a Bale API method with retry logic.
        """
        url = f"{self.base_url}/{method}"
        delay = RETRY_DELAY

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    "POST %s | attempt %d/%d | payload=%s",
                    method, attempt, self.max_retries, payload,
                )
                async with self._session.post(url, json=payload) as resp:
                    try:
                        data = await resp.json(content_type=None)
                    except Exception as e:
                        logger.error("Failed to parse JSON response: %s", e)
                        logger.error("Raw response content: %s", await resp.text())
                        raise

                    if not resp.ok:
                        raise BaleAPIError(
                            resp.status,
                            data.get("description", "Unknown API error"),
                        )

                    if not data.get("ok", True):
                        raise BaleAPIError(
                            data.get("error_code", 0),
                            data.get("description", "ok=false"),
                        )

                    logger.debug("POST %s succeeded on attempt %d.", method, attempt)
                    return data

            except BaleAPIError:
                raise  # Don't retry API‑level errors

            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                logger.warning(
                    "Network error on attempt %d/%d for %s: %s",
                    attempt, self.max_retries, method, exc,
                )
                if attempt == self.max_retries:
                    raise BaleNetworkError(
                        f"Failed after {self.max_retries} retries: {exc}"
                    ) from exc

                logger.info("Retrying in %ds...", delay)
                await asyncio.sleep(delay)
                delay *= RETRY_MULTIPLIER

    async def get(self, method: str, params: Optional[dict] = None) -> dict:
        """
        Send a GET request to a Bale API method.
        """
        url = f"{self.base_url}/{method}"
        delay = RETRY_DELAY

        for attempt in range(1, self.max_retries + 1):
            try:
                async with self._session.get(url, params=params) as resp:
                    try:
                        data = await resp.json(content_type=None)
                    except Exception as e:
                        logger.error("Failed to parse JSON response: %s", e)
                        logger.error("Raw response content: %s", await resp.text())
                        raise

                    if not resp.ok:
                        raise BaleAPIError(
                            resp.status,
                            data.get("description", "Unknown API error"),
                        )

                    return data

            except BaleAPIError:
                raise

            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                logger.warning(
                    "GET %s attempt %d/%d failed: %s",
                    method, attempt, self.max_retries, exc,
                )
                if attempt == self.max_retries:
                    raise BaleNetworkError(
                        f"GET failed after {self.max_retries} retries: {exc}"
                    ) from exc

                await asyncio.sleep(delay)
                delay *= RETRY_MULTIPLIER

    # ─── API Methods ──────────────────────────────────────────────────────────
    async def get_me(self) -> dict:
        """Get current bot info."""
        return await self.get("getMe")

    async def get_updates(self, offset: int = 0, timeout: int = 30) -> dict:
        """Get incoming updates."""
        return await self.get(
            "getUpdates", params={"offset": offset, "timeout": timeout}
        )

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_to_message_id: Optional[int] = None,
        disable_notification: bool = False,
        disable_web_page_preview: bool = False,
        parse_mode: str = "Markdown",
        reply_markup: Optional[dict] = None,          # <-- جدید
    ) -> dict:
        """
        Send text message to a chat.

        `reply_markup` must be a dict that follows Bale’s
        InlineKeyboardMarkup schema (e.g. the dict returned by
        ``InlineKeyboardMarkup(...).to_dict()``).
        """
        payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_notification": disable_notification,
            "disable_web_page_preview": disable_web_page_preview,
            "parse_mode": parse_mode,
        }

        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id

        if reply_markup:
            payload["reply_markup"] = reply_markup   # <<‑ اضافه شد

        return await self.post("sendMessage", payload)

    async def edit_message_reply_markup(
        self,
        chat_id: int,
        message_id: int,
        reply_markup: Optional[dict] = None,
    ) -> dict:
        payload = {"chat_id": chat_id, "message_id": message_id}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return await self.post("editMessageReplyMarkup", payload)

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False,
    ) -> dict:
        payload = {"callback_query_id": callback_query_id, "show_alert": show_alert}
        if text:
            payload["text"] = text
        return await self.post("answerCallbackQuery", payload)
