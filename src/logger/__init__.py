"""
Woocommerce Bot

__init__.py
Logger package exports

@package    Woocommerce Bot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

from .log_handler import setup_logging, get_logger

__all__ = ["setup_logging", "get_logger"]