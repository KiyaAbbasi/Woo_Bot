"""
Woocommerce Bot

base.py
Abstract base class for SMS panel providers

@package    Woocommerce Bot
@subpackage Services.SMS
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

from abc import ABC, abstractmethod


class BaseSMSProvider(ABC):
    """Abstract base for all SMS providers. Each panel must implement send_otp."""

    @abstractmethod
    async def send_otp(self, phone: str, code: str) -> bool:
        """
        Send OTP code to the given phone number.
        Returns True on success, False on failure.
        """
        ...
