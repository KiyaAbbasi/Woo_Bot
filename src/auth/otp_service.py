"""
Woocommerce Bot

otp_service.py
Service for generating and verifying One-Time Passwords (OTP)

@package    Woocommerce Bot
@subpackage Auth
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

import random
import time
import httpx
from src.config.settings import (
    SMS_PANEL, SMS_USERNAME, SMS_PASSWORD,
    SMS_API_KEY, SMS_SENDER, SMS_TEMPLATE
)
from src.logger.log_handler import get_logger

logger = get_logger("woobot.auth.otp_service")


class OTPService:
    """
    Ù…Ø¯ÛŒØ±ÛŒØª OTP:
    * ØªÙˆÙ„ÛŒØ¯ Ú©Ø¯ ØªØµØ§Ø¯ÙÛŒ Û¶ Ø±Ù‚Ù…ÛŒ
    * Ø°Ø®ÛŒØ±Ù‡ Ù…ÙˆÙ‚Øª Ø¯Ø± Ø­Ø§ÙØ¸Ù‡â€Œcache Ø¨Ø§ Ø²Ù…Ø§Ù† Ø§Ù†Ù‚Ø¶Ø§
    * Ø§Ø±Ø³Ø§Ù„ Ø¨Ù‡ Ø³Ø±ÙˆÛŒØ³ Ù¾ÛŒØ§Ù…Ú© (Ø¨Ù‡â€ŒØµÙˆØ±Øª async)
    * Ø§Ø¹ØªØ¨Ø§Ø±Ø³Ù†Ø¬ÛŒ Ú©Ø¯ ÙˆØ§Ø±Ø¯â€‘Ø´Ø¯Ù‡
    * Ù‚Ø§Ø¨Ù„ÛŒØª **Ø§Ø±Ø³Ø§Ù„ Ù…Ø¬Ø¯Ø¯** (Ø¯ÙˆØ¨Ø§Ø±Ù‡â€ŒØ³Ø§Ø®ØªÙ† Ú©Ø¯ Ùˆ Ø±ÛŒØ³Øª Ø²Ù…Ø§Ù† Ø§Ù†Ù‚Ø¶Ø§)
    """

    def __init__(self, expiry_seconds: int = 300):
        """
        Ù¾Ø§Ø±Ø§Ù…ØªØ± `expiry_seconds` Ø²Ù…Ø§Ù† Ø§Ø¹ØªØ¨Ø§Ø± Ú©Ø¯ Ø±Ø§ Ø¨Ø±Ø«Ø§Ù†ÛŒÙ‡ ØªØ¹ÛŒÛŒÙ† Ù…ÛŒâ€ŒÚ©Ù†Ø¯.
        Ù…Ù‚Ø¯Ø§Ø± Ù¾ÛŒØ´â€ŒÙØ±Ø¶ Ø¨Ù‡â€¯Û² Ø¯Ù‚ÛŒÙ‚Ù‡ (â€¯120â€¯Ø«) ØªØºÛŒÛŒØ± Ø¯Ø§Ø¯Ù‡ Ø´Ø¯ ØªØ§ Ú©Ø¯ Ø²ÙˆØ¯ Ù…Ù†Ù‚Ø¶ÛŒ Ù†Ø´ÙˆØ¯Ø›
        Ø§Ú¯Ø± Ù…ÛŒâ€ŒØ®ÙˆØ§Ù‡ÛŒØ¯ Ø²Ù…Ø§Ù† Ø¯ÛŒÚ¯Ø±ÛŒ Ø¯Ø§Ø´ØªÙ‡ Ø¨Ø§Ø´ÛŒØ¯ØŒ Ù‡Ù†Ú¯Ø§Ù… Ø³Ø§Ø®Øª `OTPService`
        Ù…Ù‚Ø¯Ø§Ø± Ø¯Ù„Ø®ÙˆØ§Ù‡ Ø±Ø§ Ø¨Ø¯Ù‡ÛŒØ¯ (Ù…Ø«Ù„Ø§Ù‹ 300â€¯Ø« â†’ Ûµâ€¯Ø¯Ù‚ÛŒÙ‚Ù‡).
        """
        self.cache: dict[str, dict] = {}          # phone â†’ {"code": str, "time": float}
        self.expiry = expiry_seconds

    # -----------------------------------------------------------------
    # ØªÙˆÙ„ÛŒØ¯ Ú©Ø¯ Ø¬Ø¯ÛŒØ¯ (Ù‡Ù…Ø±Ø§Ù‡ Ø¨Ø§ Ø¨Ø§Ø²Ù†ÙˆÛŒØ³ÛŒ Ø²Ù…Ø§Ù† ØªÙˆÙ„ÛŒØ¯)
    # -----------------------------------------------------------------
    def _store_code(self, phone: str, code: str) -> None:
        """Ø«Ø¨Øª Ú©Ø¯ Ø¨Ø§ Ø²Ù…Ø§Ù† Ø¬Ø§Ø±ÛŒØ› Ø§Ú¯Ø± Ù‚Ø¨Ù„Ø§Ù‹ Ú©Ø¯ÛŒ Ù…ÙˆØ¬ÙˆØ¯ Ø¨Ø§Ø´Ø¯ Ø¢Ù† Ø±Ø§ Ø¨Ø§Ø²Ù†ÙˆÛŒØ³ÛŒ Ù…ÛŒâ€ŒÚ©Ù†Ø¯."""
        self.cache[phone] = {"code": code, "time": time.time()}
        logger.debug("OTP stored for %s (code=%s)", phone, code)

    def generate(self, phone: str) -> str:
        """ÛŒÚ© Ú©Ø¯ Û¶ Ø±Ù‚Ù…ÛŒ ØªØµØ§Ø¯ÙÛŒ Ù…ÛŒâ€ŒØ³Ø§Ø²Ø¯ Ùˆ Ø¯Ø± cache Ø°Ø®ÛŒØ±Ù‡ Ù…ÛŒâ€ŒÚ©Ù†Ø¯."""
        code = f"{random.randint(100000, 999999)}"
        self._store_code(phone, code)
        return code

    # -----------------------------------------------------------------
    # Ø§Ø±Ø³Ø§Ù„ Ù¾ÛŒØ§Ù…Ú© (async) â€“ Ø¨Ø§ Ù„Ø§Ú¯â€ŒØ²Ù…Ø§Ù† Ùˆ retry Ø³Ø§Ø¯Ù‡
    # -----------------------------------------------------------------
    async def send(self, phone: str) -> bool:
        """
        ØªÙˆÙ„ÛŒØ¯ Ú©Ø¯ Ø¬Ø¯ÛŒØ¯ØŒ Ø°Ø®ÛŒØ±Ù‡ Ø¢Ù† Ùˆ Ø§Ø±Ø³Ø§Ù„ Ø¨Ù‡ Ø³Ø±ÙˆÛŒØ³ Ù¾ÛŒØ§Ù…Ú©.
        Ø§Ú¯Ø± ØªÙ†Ø¸ÛŒÙ…Ø§Øª Ù¾ÛŒØ§Ù…Ú© Ø®Ø§Ù„ÛŒ Ø¨Ø§Ø´Ø¯ ØªÙ†Ù‡Ø§ Ø¯Ø± Ù„Ø§Ú¯Ø± Ú†Ø§Ù¾ Ù…ÛŒâ€ŒØ´ÙˆØ¯
        (Ù…Ù†Ø§Ø³Ø¨ Ø¨Ø±Ø§ÛŒ Ù…Ø­ÛŒØ· ØªÙˆØ³Ø¹Ù‡).
        """
        start_ts = time.time()
        code = self.generate(phone)

        # Ø¯Ø± Ø­Ø§Ù„Øª ØªÙˆØ³Ø¹Ù‡ ÛŒØ§ ÙˆÙ‚ØªÛŒ ØªÙ†Ø¸ÛŒÙ…Ø§Øª Ù¾ÛŒØ§Ù…Ú© Ø®Ø§Ù„ÛŒ Ø§Ø³Øª ÙÙ‚Ø· Ù„Ø§Ú¯ Ù…ÛŒâ€ŒÚ©Ù†ÛŒÙ…
        if not SMS_USERNAME and not SMS_API_KEY:
            logger.warning(
                "OTP for %s: %s (SMS not configured) â€“ generated in %.2fâ€¯s",
                phone, code, time.time() - start_ts
            )
            return True

        try:
            if SMS_PANEL == "kavenegar":
                result = await self._send_kavenadar(phone, code)
            else:
                result = await self._send_melipayamak(phone, code)
            elapsed = time.time() - start_ts
            logger.info(
                "OTP sent to %s (code=%s) â€“ success=%s â€“ %.2fâ€¯s",
                phone, code, result, elapsed
            )
            return result
        except Exception as exc:                     # pragma: no cover
            logger.error("SMS send failed for %s: %s", phone, exc)
            return False

    async def _send_melipayamak(self, phone: str, code: str) -> bool:
        """Ø§Ø±Ø³Ø§Ù„ Ø§Ø² Ø·Ø±ÛŒÙ‚ Ø³Ø±ÙˆÛŒØ³â€¯Melipayamak (async)."""
        text = SMS_TEMPLATE.format(code=code)
        url = "https://rest.payamak-panel.com/api/SendSMS/SendSMS"
        payload = {
            "username": SMS_USERNAME,
            "password": SMS_PASSWORD,
            "to": phone,
            "from": SMS_SENDER,
            "text": text,
            "isflash": False,
        }

        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, json=payload)
            data = r.json()
            logger.debug("Melipayamak response: %s", data)

        # Ø³Ø±ÙˆÛŒØ³ Melipayamak Ù…Ù‚Ø¯Ø§Ø± Â«ValueÂ» Ø¹Ø¯Ø¯ÛŒ Ø¨Ø±Ù…ÛŒâ€ŒÚ¯Ø±Ø¯Ø§Ù†Ø¯Ø› Ø¹Ø¯Ø¯ Ø¨Ø²Ø±Ú¯â€¯Û° = Ù…ÙˆÙÙ‚ÛŒØª
        success = str(data.get("Value", "")).isdigit() and int(data.get("Value", 0)) > 0
        return success

    async def _send_kavenadar(self, phone: str, code: str) -> bool:
        """Ø§Ø±Ø³Ø§Ù„ Ø§Ø² Ø·Ø±ÛŒÙ‚ Ø³Ø±ÙˆÛŒØ³â€¯Kavenadar (async)."""
        url = f"https://api.kavenegar.com/v1/{SMS_API_KEY}/sms/send.json"
        params = {
            "receptor": phone,
            "sender": SMS_SENDER,
            "message": SMS_TEMPLATE.format(code=code),
        }

        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url, params=params)
            data = r.json()
            logger.debug("Kavenadar response: %s", data)

        # ÙˆØ¶Ø¹ÛŒØª 200 â†’ Ù…ÙˆÙÙ‚
        return data.get("return", {}).get("status") == 200

    # -----------------------------------------------------------------
    # Ø§Ø¹ØªØ¨Ø§Ø±Ø³Ù†Ø¬ÛŒ Ú©Ø¯
    # -----------------------------------------------------------------
    def verify(self, phone: str, code: str) -> bool:
        """
        Ø¨Ø±Ø±Ø³ÛŒ Ø§ÛŒÙ†Ú©Ù‡ Ø¢ÛŒØ§ Ú©Ø¯ Ø§Ø±Ø§Ø¦Ù‡â€¯Ø´Ø¯Ù‡ Ø¨Ø§ Ú©Ø¯ÛŒ Ú©Ù‡ Ø¯Ø± cache Ø¯Ø§Ø±ÛŒÙ… Ø¨Ø±Ø§Ø¨Ø± Ø§Ø³Øª
        Ùˆ Ø¢ÛŒØ§ Ù‡Ù†ÙˆØ² Ù…Ù†Ù‚Ø¶ÛŒ Ù†Ø´Ø¯Ù‡ Ø§Ø³Øª.
        Ø¯Ø± Ù‡Ø± Ø¯Ùˆ Ø­Ø§Ù„Øª (Ù…ÙˆÙÙ‚/Ù†Ø§Ù…ÙˆÙÙ‚) ÙˆØ±ÙˆØ¯ÛŒ Ù…Ø±Ø¨ÙˆØ· Ø¨Ù‡ Ø¢Ù† phone Ø­Ø°Ù Ù…ÛŒâ€ŒØ´ÙˆØ¯
        ØªØ§ Ø§Ø² Ø§Ø³ØªÙØ§Ø¯Ù‡Ù” Ù…Ø¬Ø¯Ø¯ Ø¬Ù„ÙˆÚ¯ÛŒØ±ÛŒ Ø´ÙˆØ¯.
        """
        entry = self.cache.get(phone)
        if not entry:
            logger.debug("OTP verify failed â€“ no entry for %s", phone)
            return False

        # Ø²Ù…Ø§Ù† Ø§Ù†Ù‚Ø¶Ø§
        if time.time() - entry["time"] > self.expiry:
            logger.warning("OTP for %s expired (%.0fâ€¯s passed)", phone,
                           time.time() - entry["time"])
            self.cache.pop(phone, None)
            return False

        if entry["code"] == code:
            logger.info("OTP verified successfully for %s", phone)
            self.cache.pop(phone, None)
            return True

        logger.warning("OTP verify failed â€“ wrong code for %s", phone)
        return False

    # -----------------------------------------------------------------
    # Ù…ØªØ¯ Â«Ø¯ÙˆØ¨Ø§Ø±Ù‡ Ø§Ø±Ø³Ø§Ù„Â» (Resend) â€“ ÙÙ‚Ø· ÛŒÚ© Ø¨Ø§Ø± Ø¬Ø¯ÛŒØ¯ ØªÙˆÙ„ÛŒØ¯ Ù…ÛŒâ€ŒÚ©Ù†Ø¯
    # -----------------------------------------------------------------
    async def resend(self, phone: str) -> bool:
        """
        ÙˆÙ‚ØªÛŒ Ú©Ø§Ø±Ø¨Ø± Ø±ÙˆÛŒ Ø¯Ú©Ù…Ù‡ Â«ðŸ”„ Ø§Ø±Ø³Ø§Ù„ Ù…Ø¬Ø¯Ø¯ Ú©Ø¯Â» Ù…ÛŒâ€ŒÚ©Ø´Ø¯ Ø§ÛŒÙ† Ù…ØªØ¯ ÙØ±Ø§Ø®ÙˆØ§Ù†ÛŒ Ù…ÛŒâ€ŒØ´ÙˆØ¯.
        * ÛŒÚ© Ú©Ø¯ ØªØ§Ø²Ù‡ ØªÙˆÙ„ÛŒØ¯ Ù…ÛŒâ€ŒÚ©Ù†Ø¯ (Ø¨Ù‡â€ŒÚ¯ÙˆÙ†Ù‡â€ŒØ§ÛŒ Ú©Ù‡ Ø²Ù…Ø§Ù† Ø§Ù†Ù‚Ø¶Ø§ Ø§Ø² Ù†Ùˆ Ø´Ø±ÙˆØ¹ Ù…ÛŒâ€ŒØ´ÙˆØ¯)
        * Ù‡Ù…Ø§Ù† Ù…Ø³ÛŒØ± Ø§Ø±Ø³Ø§Ù„ Ù¾ÛŒØ§Ù…Ú© async Ø±Ø§ Ø§Ø¬Ø±Ø§ Ù…ÛŒâ€ŒÚ©Ù†Ø¯
        """
        logger.info("Resending OTP for %s", phone)
        # Ø­Ø°Ù Ù‡Ø± Ú©Ø¯ Ù‚Ø¯ÛŒÙ…ÛŒ (Ø§Ú¯Ø± Ù‡Ù†ÙˆØ² Ø¯Ø± cache Ø¨Ø§Ø´Ø¯) Ùˆ Ø³Ø§Ø®Øª Ú©Ø¯ Ø¬Ø¯ÛŒØ¯
        if phone in self.cache:
            self.cache.pop(phone, None)
        return await self.send(phone)
