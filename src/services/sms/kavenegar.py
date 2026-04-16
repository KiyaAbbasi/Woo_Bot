"""
Woocommerce Bot

kavenegar.py
SMS provider implementation for Kavenegar panel

@package    Woocommerce Bot
@subpackage Services.SMS
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

import httpx
from config.settings import SMS_API_KEY, SMS_TEMPLATE
from logger import get_logger
from .base import BaseSMSProvider

logger = get_logger("woobot.services.sms.kavenegar")


class KavenegarProvider(BaseSMSProvider):
    """Kavenegar Lookup (template-based) provider."""

    async def send_otp(self, phone: str, code: str) -> bool:
        url = f"https://api.kavenegar.com/v1/{SMS_API_KEY}/verify/lookup.json"
        params = {
            "receptor": phone,
            "token": code,
            "template": SMS_TEMPLATE,
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                success = data.get("return", {}).get("status") == 200
                if not success:
                    logger.warning("Kavenegar rejected: %s", data)
                return success
        except Exception as e:
            logger.error("Kavenegar error: %s", e)
            return False
