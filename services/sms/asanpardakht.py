"""
Woocommerce Bot

asanpardakht.py
SMS provider implementation for Asanpardakht panel

@package    Woocommerce Bot
@subpackage Services.SMS
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

import httpx
from config.settings import SMS_API_KEY, SMS_SENDER, SMS_TEMPLATE
from logger import get_logger
from .base import BaseSMSProvider

logger = get_logger("woobot.services.sms.asanpardakht")


class AsanpardakhtProvider(BaseSMSProvider):
    """Asanpardakht SMS provider."""

    _URL = "https://api.asanpardakht.ir/sms/send"

    async def send_otp(self, phone: str, code: str) -> bool:
        text = SMS_TEMPLATE.format(code=code)
        headers = {"Authorization": f"Bearer {SMS_API_KEY}"}
        payload = {"from": SMS_SENDER, "to": [phone], "text": text}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(self._URL, json=payload, headers=headers)
                resp.raise_for_status()
                return resp.status_code == 200
        except Exception as e:
            logger.error("Asanpardakht error: %s", e)
            return False
