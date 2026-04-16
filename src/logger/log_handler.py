"""
Woocommerce Bot

log_handler.py
Logging configuration — file + console handlers with rotation

@package    Woocommerce Bot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# ─── Constants ────────────────────────────────────────────────────────────────
LOG_DIR      = "logs"
LOG_FILE     = os.path.join(LOG_DIR, "woobot.log")
MAX_BYTES    = 5 * 1024 * 1024   # 5 MB
BACKUP_COUNT = 3
LOG_FORMAT   = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT  = "%Y-%m-%d %H:%M:%S"

_initialized = False


def setup_logging(level: str = "INFO") -> None:
    """
    Configure root logger with rotating file + console handlers.
    Safe to call multiple times (runs once).

    Args:
        level: Log level string (DEBUG / INFO / WARNING / ERROR).
    """
    global _initialized
    if _initialized:
        return

    os.makedirs(LOG_DIR, exist_ok=True)

    numeric_level = getattr(logging, level.upper(), logging.INFO)
    formatter     = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # ── File handler (rotating) ───────────────────────────────────────────────
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes    = MAX_BYTES,
        backupCount = BACKUP_COUNT,
        encoding    = "utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(numeric_level)

    # ── Console handler ───────────────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)

    # ── Root logger ───────────────────────────────────────────────────────────
    root = logging.getLogger()
    root.setLevel(numeric_level)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    _initialized = True
    root.info("Logging initialized — level=%s file=%s", level, LOG_FILE)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger. setup_logging() must be called first.

    Args:
        name: Dotted logger name (e.g. 'woobot.bale.api').

    Returns:
        logging.Logger instance.
    """
    return logging.getLogger(name)
