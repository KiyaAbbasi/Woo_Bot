"""
Woocommerce Bot

handlers/__init__.py
Exports all handlers and the central router

@package    Woocommerce Bot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

from .router import Router
from .registration_handler import RegistrationHandler

__all__ = ["Router", "RegistrationHandler"]
