"""
Woocommerce Bot

melipayamak.py
SMS provider implementation for Melipayamak panel

@package    Woocommerce Bot
@subpackage Services.SMS
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

import httpx
from config.settings import SMS_USERNAME, SMS_PASSWORD, SMS_SENDER, SMS_TEMPLATE
from logger import get_logger
from .base import BaseSMSProvider

logger = get_logger("woobot.services.sms.melipayamak")


class MelipayamakProvider(BaseSMSProvider):
    """Melipayamak REST API provider."""

    _URL = "https://rest.payamak-panel.com/api/SendSMS/SendSMS"

    async def send_otp(self, phone: str, code: str) -> bool:
        text = SMS_TEMPLATE.format(code=code)
        payload = {
            "username": SMS_USERNAME,
            "password": SMS_PASSWORD,
            "to": phone,
            "from": SMS_SENDER,
            "text": text,
            "isFlash": False,
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(self._URL, json=payload)
                resp.raise_for_status()
                data = resp.json()
                success = str(data.get("RetStatus")) == "1"
                if not success:
                    logger.warning("Melipayamak rejected: %s", data)
                return success
        except Exception as e:
            logger.error("Melipayamak error: %s", e)
            return False
