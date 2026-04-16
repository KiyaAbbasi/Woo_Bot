"""
Woocommerce Bot

sms_service.py
SMS facade — selects the correct provider based on settings

@package    Woocommerce Bot
@subpackage Services
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

from config.settings import SMS_PANEL, SMS_TEMPLATE
from logger import get_logger
from services.sms.base import BaseSMSProvider

logger = get_logger("woobot.services.sms")


def _load_provider() -> BaseSMSProvider:
    panel = SMS_PANEL.lower()
    if panel == "melipayamak":
        from services.sms.melipayamak import MelipayamakProvider
        return MelipayamakProvider()
    elif panel == "kavenegar":
        from services.sms.kavenegar import KavenegarProvider
        return KavenegarProvider()
    elif panel == "asanpardakht":
        from services.sms.asanpardakht import AsanpardakhtProvider
        return AsanpardakhtProvider()
    else:
        logger.warning("Unknown SMS_PANEL '%s' — using console fallback", panel)
        return _ConsoleFallback()


class _ConsoleFallback(BaseSMSProvider):
    """Fallback provider that just prints to console (dev/test mode)."""
    async def send_otp(self, phone: str, code: str) -> bool:
        print(f"[SMS FALLBACK] {phone} → {SMS_TEMPLATE.format(code=code)}")
        return True


class SMSService:
    def __init__(self):
        self._provider: BaseSMSProvider = _load_provider()
        logger.info("SMS provider loaded: %s", type(self._provider).__name__)

    async def send_otp(self, phone: str, code: str) -> bool:
        return await self._provider.send_otp(phone, code)
