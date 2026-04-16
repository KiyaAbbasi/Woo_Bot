"""
Woocommerce Bot

registration_handler.py
Stepâ€‘byâ€‘step registration flow handler (FSMâ€‘based)

@package    Woocommerce Bot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

import time
import asyncio
from typing import List

# â”€â”€ Ø§ÛŒÙ…Ù¾ÙˆØ±Øªâ€ŒÙ‡Ø§ÛŒ Ù¾Ø±ÙˆÚ˜Ù‡ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
from src.auth.user_manager import UserManager
from src.logger.log_handler import get_logger
from src.auth.otp_service import OTPService

logger = get_logger("woobot.handlers.registration")

# â”€â”€ fallback Ø¨Ø±Ø§ÛŒ InlineKeyboardButton / InlineKeyboardMarkup (Ø¯Ø± ØµÙˆØ±Øª Ø¹Ø¯Ù… ÙˆØ¬ÙˆØ¯ SDK) â”€â”€
# Ø§Ú¯Ø± Ø¨Ø³ØªÙ‡Ù” Ø±Ø³Ù…ÛŒ Bale Ù†ØµØ¨ Ø¨Ø§Ø´Ø¯ØŒ Ø§ÛŒÙ† Ø¨Ù„ÙˆÚ© Ø§Ø¬Ø±Ø§ Ù†Ù…ÛŒâ€ŒØ´ÙˆØ¯.
try:
    from bale.types import InlineKeyboardButton, InlineKeyboardMarkup   # type: ignore
except Exception:  # pragma: no cover
    class InlineKeyboardButton:
        def __init__(self, text: str, callback_data: str):
            self.text = text
            self.callback_data = callback_data

        def to_dict(self) -> dict:
            return {"text": self.text, "callback_data": self.callback_data}

    class InlineKeyboardMarkup:
        def __init__(self, inline_keyboard: list[list[InlineKeyboardButton]]):
            self.inline_keyboard = inline_keyboard

        def to_dict(self) -> dict:
            return {
                "inline_keyboard": [
                    [btn.to_dict() for btn in row] for row in self.inline_keyboard
                ]
            }

# â”€â”€ ÙˆØ¶Ø¹ÛŒØªâ€ŒÙ‡Ø§ÛŒ Ø«Ø¨Øªâ€ŒÙ†Ø§Ù… (Ø¨Ù‡â€ŒØ±ÙˆØ² Ø´Ø¯Ù‡) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class RegState:
    IDLE              = "idle"
    WAIT_PHONE        = "wait_phone"      # Ø¯Ø±ÛŒØ§ÙØª Ø´Ù…Ø§Ø±Ù‡ Ù…ÙˆØ¨Ø§ÛŒÙ„
    WAIT_OTP          = "wait_otp"        # ÙˆØ§Ø±Ø¯ Ú©Ø±Ø¯Ù† Ú©Ø¯ OTP
    WAIT_NAME         = "wait_name"       # ÙÙ‚Ø· Ø¨Ø±Ø§ÛŒ Ú©Ø§Ø±Ø¨Ø± Ø¬Ø¯ÛŒØ¯
    WAIT_BUSINESS     = "wait_business"
    WAIT_WEBSITE      = "wait_website"
    WAIT_EMAIL        = "wait_email"
    WAIT_CATEGORY     = "wait_category"
    DONE              = "done"

# â”€â”€ Ø¯Ø³ØªÙ‡â€‘Ø¨Ù†Ø¯ÛŒâ€ŒÙ‡Ø§ÛŒ Ø­Ø¯Ø§Ù‚Ù„ Û³Û° ØªØ§ÛŒÛŒ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
CATEGORIES = [
    "Ù¾ÙˆØ´Ø§Ú©", "Ù„ÙˆØ§Ø²Ù… Ø§Ù„Ú©ØªØ±ÙˆÙ†ÛŒÚ©ÛŒ", "Ù…ÙˆØ§Ø¯ ØºØ°Ø§ÛŒÛŒ", "Ø®Ø¯Ù…Ø§Øª", "Ø¢Ù…ÙˆØ²Ø´ÛŒ", "Ø³Ø§ÛŒØ±",
    "Ú©ØªØ§Ø¨â€ŒÙ‡Ø§", "Ù†Ø±Ù…â€ŒØ§ÙØ²Ø§Ø±Ù‡Ø§", "ÙˆØ±Ø²Ø´ Ùˆ ØªÙ†Ø§Ø³Ø¨â€ŒØ¨Ø¯Ù†", "Ø¯Ú©ÙˆØ±Ø§Ø³ÛŒÙˆÙ† Ø¯Ø§Ø®Ù„ÛŒ",
    "Ø§Ø¨Ø²Ø§Ø±Ø¢Ù„Ø§Øª ØµÙ†Ø¹ØªÛŒ", "Ù…Ø­ØµÙˆÙ„Ø§Øª Ø¢Ø±Ø§ÛŒØ´ÛŒ", "ØµÙ†Ø§ÛŒØ¹ Ú†ÙˆØ¨", "Ø³Ø¨Ø²ÛŒØ¬Ø§Øª ØªØ§Ø²Ù‡",
    "Ø­Ø±ÙÙ‡â€ŒØ§ÛŒâ€ŒÙ‡Ø§", "Ù…Ø­ØµÙˆÙ„Ø§Øª Ø®Ø§Ù†Ú¯ÛŒ", "Ù…Ø­ØµÙˆÙ„Ø§Øª Ø¨Ú†Ù‡â€ŒÚ¯Ø§Ù†Ù‡", "Ù…Ø­ØµÙˆÙ„Ø§Øª ÙˆØ±Ø²Ø´ÛŒ",
    "Ù…Ø­ØµÙˆÙ„Ø§Øª Ø¯ÛŒØ¬ÛŒØªØ§Ù„", "Ù„ÙˆØ§Ø²Ù… Ø®Ø§Ù†Ú¯ÛŒ", "Ù„ÙˆØ§Ø²Ù… Ø§Ø¯Ø§Ø±ÛŒ", "Ø­ÛŒÙˆØ§Ù†Ø§Øª Ø®Ø§Ù†Ú¯ÛŒ",
    "Ù…Ø­ØµÙˆÙ„Ø§Øª Ú©Ø´Ø§ÙˆØ±Ø²ÛŒ", "Ù…Ø­ØµÙˆÙ„Ø§Øª Ø¨Ù‡Ø¯Ø§Ø´ØªÛŒ", "Ù…Ø­ØµÙˆÙ„Ø§Øª Ø¨Ø§Ø²ÛŒ Ùˆ Ø³Ø±Ú¯Ø±Ù…ÛŒ",
    "Ø¢Ù„Ø§Øª Ù…ÙˆØ³ÛŒÙ‚ÛŒ", "Ù…Ø­ØµÙˆÙ„Ø§Øª Ú†Ø§Ù¾ÛŒ", "Ø§Ø¨Ø²Ø§Ø±Ù‡Ø§ÛŒ Ø¨Ø§ØºØ¨Ø§Ù†ÛŒ", "Ù…Ø­ØµÙˆÙ„Ø§Øª Ø¨Ø³ØªÙ‡â€ŒØ¨Ù†Ø¯ÛŒ",
    "Ø´Ù†Ø§Ø³ÛŒ Ø¯Ø§Ø¯Ù‡â€ŒÙ‡Ø§"
]   # Ø¯Ù‚ÛŒÙ‚Ø§Ù‹ 30 Ø¢ÛŒØªÙ…

# â”€â”€ Ù¾ÛŒØ§Ù…â€ŒÙ‡Ø§ÛŒ Ø±Ø¨Ø§Øª â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
MSG = {
    "welcome":          "ðŸ‘‹ Ø³Ù„Ø§Ù…! Ø¨Ù‡ Ø±Ø¨Ø§Øª ÙˆÙˆÚ©Ø§Ù…Ø±Ø³ Ø®ÙˆØ´ Ø¢Ù…Ø¯ÛŒØ¯.\nØ§Ø¨ØªØ¯Ø§ Ø´Ù…Ø§Ø±Ù‡ Ù…ÙˆØ¨Ø§ÛŒÙ„ Ø®ÙˆØ¯ Ø±Ø§ Ø¨ÙØ±Ø³ØªÛŒØ¯:",
    "ask_name":         "ðŸ§‘â€ðŸ’¼ Ù„Ø·ÙØ§Ù‹ Ù†Ø§Ù… Ùˆ Ù†Ø§Ù… Ø®Ø§Ù†ÙˆØ§Ø¯Ú¯ÛŒâ€ŒØªØ§Ù† Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯:",
    "ask_phone":        "ðŸ‘‹ Ø³Ù„Ø§Ù…! Ø¨Ù‡ Ø±Ø¨Ø§Øª ÙˆÙˆÚ©Ø§Ù…Ø±Ø³ Ø®ÙˆØ´ Ø¢Ù…Ø¯ÛŒØ¯.\n\nðŸ“± Ø§Ø¨ØªØ¯Ø§ Ø´Ù…Ø§Ø±Ù‡ Ù…ÙˆØ¨Ø§ÛŒÙ„ Ø®ÙˆØ¯ Ø±Ø§ Ø¨ÙØ±Ø³ØªÛŒØ¯:",
    "otp_sent":         "âœ… Ú©Ø¯ ØªØ£ÛŒÛŒØ¯ Ø§Ø±Ø³Ø§Ù„ Ø´Ø¯. Ù„Ø·ÙØ§Ù‹ Ú©Ø¯ Û¶ Ø±Ù‚Ù…ÛŒ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯:",
    "resent_otp":       "ðŸ”„ Ú©Ø¯ Ø¬Ø¯ÛŒØ¯ Ø§Ø±Ø³Ø§Ù„ Ø´Ø¯. Ù„Ø·ÙØ§Ù‹ Ú©Ø¯ Û¶ Ø±Ù‚Ù…ÛŒ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯:",
    "otp_error":        "âŒ›ï¸ Ø²Ù…Ø§Ù† Ø§Ø¹ØªØ¨Ø§Ø± Ú©Ø¯ ØªÙ…Ø§Ù… Ø´Ø¯. Ù…ÛŒâ€ŒØªÙˆØ§Ù†ÛŒØ¯ Ø¯Ø±Ø®ÙˆØ§Ø³Øª Ú©Ø¯ Ø¬Ø¯ÛŒØ¯ Ø¨Ø¯Ù‡ÛŒØ¯.",
    "otp_fail":         "âŒ Ú©Ø¯ Ø§Ø´ØªØ¨Ø§Ù‡ ÛŒØ§ Ù…Ù†Ù‚Ø¶ÛŒ Ø´Ø¯Ù‡. Ø¯ÙˆØ¨Ø§Ø±Ù‡ ØªÙ„Ø§Ø´ Ú©Ù†ÛŒØ¯:",
    "ask_biz":          "ðŸª Ù†Ø§Ù… Ú©Ø³Ø¨â€ŒÙˆÚ©Ø§Ø±ØªØ§Ù† Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯:",
    "ask_site":         "ðŸŒ Ø¢Ø¯Ø±Ø³ ÙˆØ¨â€ŒØ³Ø§ÛŒØª ÙØ±ÙˆØ´Ú¯Ø§Ù‡â€ŒØªØ§Ù† Ø±Ø§ Ø¨Ù†ÙˆÛŒØ³ÛŒØ¯: \n (Ù…Ø«Ø§Ù„: myshop.ir)",
    "ask_email":        "ðŸ“§ Ø§ÛŒÙ…ÛŒÙ„ØªØ§Ù† Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯ (Ø§Ø®ØªÛŒØ§Ø±ÛŒ):",
    "skip_email_btn":   "âŽ Ø±Ø¯ Ú©Ø±Ø¯Ù† Ø§ÛŒÙ…ÛŒÙ„",
    "email_skip":       "âœ… Ø§ÛŒÙ…ÛŒÙ„ Ø±Ø¯ Ø´Ø¯.",
    "ask_cat":          "ðŸ“‚ Ø¯Ø³ØªÙ‡â€ŒØ¨Ù†Ø¯ÛŒ Ú©Ø³Ø¨â€ŒÙˆÚ©Ø§Ø±ØªØ§Ù† Ø±Ø§ Ø§Ù†ØªØ®Ø§Ø¨ Ú©Ù†ÛŒØ¯:",
    "search_btn":       "ðŸ” Ø¬Ø³ØªØ¬Ùˆ",
    "prev_page":        "â—€ï¸ Ù‚Ø¨Ù„ÛŒ",
    "next_page":        "Ø¨Ø¹Ø¯ÛŒ â–¶ï¸",
    "resend_btn":       "ðŸ”„ Ø§Ø±Ø³Ø§Ù„ Ù…Ø¬Ø¯Ø¯ Ú©Ø¯",
    "timer_btn":        "â³ {seconds}s",
    "done":             "ðŸŽ‰ Ø«Ø¨Øªâ€ŒÙ†Ø§Ù… Ø´Ù…Ø§ Ø¨Ø§ Ù…ÙˆÙÙ‚ÛŒØª Ø§Ù†Ø¬Ø§Ù… Ø´Ø¯.\n\nØ¨Ù‡ Ù¾Ù†Ù„ Ù…Ø¯ÛŒØ±ÛŒØª Ø®ÙˆØ´ Ø¢Ù…Ø¯ÛŒØ¯.",
    "login_done":       "âœ… Ø®ÙˆØ´ Ø¨Ø±Ú¯Ø´ØªÛŒØ¯ ðŸ˜Š\n\nÙˆØ±ÙˆØ¯ Ø´Ù…Ø§ Ø¨Ø§ Ù…ÙˆÙÙ‚ÛŒØª Ø§Ù†Ø¬Ø§Ù… Ø´Ø¯.",
    "invalid":          "âš ï¸ Ù…Ù‚Ø¯Ø§Ø± ÙˆØ§Ø±Ø¯â€ŒØ´Ø¯Ù‡ Ù…Ø¹ØªØ¨Ø± Ù†ÛŒØ³Øª. Ù„Ø·ÙØ§Ù‹ Ø¯ÙˆØ¨Ø§Ø±Ù‡ Ø§Ù…ØªØ­Ø§Ù† Ú©Ù†ÛŒØ¯.",
    "unknown_callback": "â“ Ø¯Ø±Ø®ÙˆØ§Ø³Øª Ù†Ø§Ù…ÙÙ‡ÙˆÙ…."
}

# â”€â”€ Ú©Ù„Ø§Ø³ Ø§ØµÙ„ÛŒ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
class RegistrationHandler:
    """
    Ù…Ø¯ÛŒØ±ÛŒØª Ø¬Ø±ÛŒØ§Ù† Ø«Ø¨Øªâ€ŒÙ†Ø§Ù…/ÙˆØ±ÙˆØ¯ Ø¨Ù‡â€ŒØµÙˆØ±Øª Ù…Ø±Ø­Ù„Ù‡â€‘Ø¨Ù‡â€‘Ù…Ø±Ø­Ù„Ù‡ (FSM).
    ØªÙ…Ø§Ù… ÙˆØ¶Ø¹ÛŒØªâ€ŒÙ‡Ø§ Ø¯Ø± ÛŒÚ© Ø¯ÛŒÚ©Ø´Ù†Ø±ÛŒ inâ€‘memory Ù†Ú¯Ù‡Ø¯Ø§Ø±ÛŒ Ù…ÛŒâ€ŒØ´ÙˆÙ†Ø¯.
    """

    CATS_PER_PAGE = 10  # ØªØ¹Ø¯Ø§Ø¯ Ø¯Ø³ØªÙ‡â€ŒØ¨Ù†Ø¯ÛŒ Ø¯Ø± Ù‡Ø± ØµÙØ­Ù‡

    def __init__(self, user_manager: UserManager, bot) -> None:
        """
        Ù¾Ø§Ø±Ø§Ù…ØªØ±Ù‡Ø§
        ----------
        user_manager : UserManager
            Ù„Ø§ÛŒÙ‡Ù” Ø¯Ø³ØªØ±Ø³ÛŒ Ø¨Ù‡ Ø¯ÛŒØªØ§Ø¨ÛŒØ³ (login ØŒ register ØŒ OTP â€¦)
        bot : BaleBot
            Ø´ÛŒØ¡ Ø±Ø¨Ø§Øª Ø¨Ø±Ø§ÛŒ Ø§Ø±Ø³Ø§Ù„ Ù¾ÛŒØ§Ù… Ùˆ ÙˆÛŒØ±Ø§ÛŒØ´ Ú©ÛŒØ¨ÙˆØ±Ø¯Ù‡Ø§.
        """
        self._um = user_manager
        self._bot = bot
        self._otp_service = OTPService()
        self._otp_expiry = self._otp_service.expiry
        # Ø³Ø§Ø®ØªØ§Ø± Ø³Ø´Ù†: chat_id â†’ {"state": RegState.*, "data": {...}}
        self._sessions: dict[int, dict] = {}

    # -------------------------------------------------------------------------
    # Helper â€“ Ø³Ø´Ù† Ùˆ ÙˆØ¶Ø¹ÛŒØª
    # -------------------------------------------------------------------------
    def _get_session(self, chat_id: int) -> dict:
        """
        Ú¯Ø±ÙØªÙ† ÛŒØ§ Ø³Ø§Ø®ØªÙ† Ø³Ø´Ù† Ù…Ø±Ø¨ÙˆØ· Ø¨Ù‡ ÛŒÚ© chat_id.
        """
        if chat_id not in self._sessions:
            self._sessions[chat_id] = {
                "state": RegState.IDLE,
                "data": {
                    "phone": None,
                    "full_name": None,  # ØªØºÛŒÛŒØ± Ø§Ø² "name"
                    "business_name": None,  # ØªØºÛŒÛŒØ± Ø§Ø² "business"
                    "website": None,
                    "email": None,
                    "category": None,
                    "otp": {
                        "code": None,
                        "expires_at": 0,
                        "retry": 0,
                    },
                    "otp_sent_at": 0,
                    "search_results": [],
                },
            }
        return self._sessions[chat_id]

    def get_session(self, chat_id: int) -> dict:
        """Public wrapper Ø¨Ø±Ø§ÛŒ Ø¯Ø³ØªØ±Ø³ÛŒ Ø¨Ù‡ Ø³Ø´Ù† Ú©Ø§Ø±Ø¨Ø± Ø§Ø² Ø®Ø§Ø±Ø¬ Ú©Ù„Ø§Ø³."""
        return self._get_session(chat_id)

    def _set_state(self, chat_id: int, state: str) -> None:
        """Ø¨Ù‡â€ŒØ±ÙˆØ²Ø±Ø³Ø§Ù†ÛŒ ÙˆØ¶Ø¹ÛŒØª Ø³Ø´Ù†."""
        self._sessions[chat_id]["state"] = state
        logger.debug("State â†’ %s for chat_id=%s", state, chat_id)

    @staticmethod
    def _valid_phone(phone: str) -> bool:
        """Ø§Ø¹ØªØ¨Ø§Ø±Ø³Ù†Ø¬ÛŒ Ø³Ø§Ø¯Ù‡ Ø´Ù…Ø§Ø±Ù‡ Ù…ÙˆØ¨Ø§ÛŒÙ„ Ø§ÛŒØ±Ø§Ù†ÛŒ."""
        return phone.startswith("09") and len(phone) == 11 and phone.isdigit()

    # -------------------------------------------------------------------------
    # Helper â€“ Ú©ÛŒØ¨ÙˆØ±Ø¯Ù‡Ø§ÛŒ OTP Ø¨Ø§ Ø´Ù…Ø§Ø±Ø´ Ù…Ø¹Ú©ÙˆØ³
    # -------------------------------------------------------------------------
    def _otp_resend_markup(self, remaining: int) -> dict:
        """
        Ø§Ú¯Ø± `remaining` > 0 â†’ Ø¯Ú©Ù…Ù‡Ù” ØºÛŒØ±ÙØ¹Ø§Ù„ Ø¨Ø§ Ù…ØªÙ† Ø´Ù…Ø§Ø±Ø´ Ù…Ø¹Ú©ÙˆØ³.
        Ø§Ú¯Ø± `remaining` == 0 â†’ Ø¯Ú©Ù…Ù‡Ù” ÙØ¹Ø§Ù„ Â«Ø§Ø±Ø³Ø§Ù„ Ù…Ø¬Ø¯Ø¯Â».
        """
        if remaining > 0:
            minutes = remaining // 60
            seconds = remaining % 60
            btn = InlineKeyboardButton(
                text=f"â³ {minutes:02d}:{seconds:02d}",
                callback_data="noop"
            )
        else:
            btn = InlineKeyboardButton(text=MSG["resend_btn"], callback_data="resend_otp")
        markup = InlineKeyboardMarkup(inline_keyboard=[[btn]])
        return markup.to_dict()

    async def _otp_sent_with_keyboard(
        self, chat_id: int, phone: str, new: bool = False
    ) -> None:
        """
        Ø§Ø±Ø³Ø§Ù„ Ù¾ÛŒØ§Ù… OTP (Ø§ÙˆÙ„ÛŒÙ† ÛŒØ§ Ø¨Ø¹Ø¯ Ø§Ø² `resend`) Ø¨Ù‡ Ú©Ø§Ø±Ø¨Ø±
        Ùˆ Ø±Ø§Ù‡â€ŒØ§Ù†Ø¯Ø§Ø²ÛŒ ØªØ³Ú© Ù¾Ø³â€ŒØ²Ù…ÛŒÙ†Ù‡ Ø¨Ø±Ø§ÛŒ Ø´Ù…Ø§Ø±Ø´ Ù…Ø¹Ú©ÙˆØ³.
        Ø§ÛŒÙ† Ù…ØªØ¯ Ø®ÙˆØ¯Ø´ Ù¾ÛŒØ§Ù… Ø±Ø§ Ù…ÛŒâ€ŒÙØ±Ø³ØªØ¯ Ùˆ Ú†ÛŒØ²ÛŒ Ø¨Ø±Ø§ÛŒ Router Ø¨Ø±Ù†Ù…ÛŒâ€ŒÚ¯Ø±Ø¯Ø§Ù†Ø¯.
        """
        txt = MSG["resent_otp"] if new else MSG["otp_sent"]
        markup = self._otp_resend_markup(remaining=300)

        sent_msg = await self._bot.send_message(chat_id, txt, reply_markup=markup)

        msg_id = sent_msg.get("result", {}).get("message_id") or sent_msg.get("message_id")
        asyncio.create_task(self._countdown_otp(chat_id, msg_id, phone))

        # Ù‡ÛŒÚ† Ú†ÛŒØ² Ø¨Ø±Ù†Ù…ÛŒâ€ŒÚ¯Ø±Ø¯Ø§Ù†ÛŒÙ… â†’ Router Ù†Ø¨Ø§ÛŒØ¯ Ø¯ÙˆØ¨Ø§Ø±Ù‡ Ú†ÛŒØ²ÛŒ Ø¨ÙØ±Ø³ØªØ¯
        return None

    async def _otp_error_with_keyboard(self, chat_id: int) -> dict:
        """
        ÙˆÙ‚ØªÛŒ Ø²Ù…Ø§Ù† OTP ØªÙ…Ø§Ù… Ù…ÛŒâ€ŒØ´ÙˆØ¯ØŒ Ø¯Ú©Ù…Ù‡ Â«Ø§Ø±Ø³Ø§Ù„ Ù…Ø¬Ø¯Ø¯Â» Ø±Ø§ ÙØ¹Ø§Ù„ Ù…ÛŒâ€ŒÚ©Ù†Ø¯.
        """
        markup = self._otp_resend_markup(remaining=0)
        return {"text": MSG["otp_error"], "reply_markup": markup}

    async def _countdown_otp(self, chat_id: int, message_id: int, phone: str) -> None:
        """
        Ø­Ù„Ù‚Ù‡Ù” async Ú©Ù‡ Ù‡Ø± Ø«Ø§Ù†ÛŒÙ‡ Ú©ÛŒØ¨ÙˆØ±Ø¯ Ø±Ø§ Ø¨Ù‡â€ŒØ±ÙˆØ² Ù…ÛŒâ€ŒÚ©Ù†Ø¯.
        Ù¾Ø³ Ø§Ø² Ø§ØªÙ…Ø§Ù… 300 Ø«Ø§Ù†ÛŒÙ‡ØŒ Ø¯Ú©Ù…Ù‡ Â«Ø§Ø±Ø³Ø§Ù„ Ù…Ø¬Ø¯Ø¯Â» ÙØ¹Ø§Ù„ Ù…ÛŒâ€ŒØ´ÙˆØ¯.
        """
        for remaining in range(300, 0, -1):
            await asyncio.sleep(1)
            markup = self._otp_resend_markup(remaining)
            try:
                await self._bot.edit_message_reply_markup(
                    chat_id, message_id, reply_markup=markup
                )
            except Exception:
                # Ù…Ù…Ú©Ù† Ø§Ø³Øª Ù¾ÛŒØ§Ù… Ø­Ø°Ù Ø´Ø¯Ù‡ Ø¨Ø§Ø´Ø¯ ÛŒØ§ Ø¯Ø³ØªØ±Ø³ÛŒ Ù†Ø¯Ø§Ø´ØªÙ‡ Ø¨Ø§Ø´ÛŒÙ…
                return

        # Ø²Ù…Ø§Ù† ØªÙ…Ø§Ù… Ø´Ø¯ â†’ Ø¯Ú©Ù…Ù‡ Â«Ø§Ø±Ø³Ø§Ù„ Ù…Ø¬Ø¯Ø¯Â» ÙØ¹Ø§Ù„ Ù…ÛŒâ€ŒØ´ÙˆØ¯
        markup = self._otp_resend_markup(remaining=0)
        try:
            await self._bot.edit_message_reply_markup(
                chat_id, message_id, reply_markup=markup
            )
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Helper â€“ Ø¯Ø³ØªÙ‡â€ŒØ¨Ù†Ø¯ÛŒâ€ŒÙ‡Ø§
    # -------------------------------------------------------------------------
    def _build_category_keyboard(
        self, items: List[tuple], page: int, total_pages: int, prefix: str
    ) -> dict:
        """
        Ø³Ø§Ø®Øª Ú©ÛŒØ¨ÙˆØ±Ø¯ Ø¯Ø³ØªÙ‡â€ŒØ¨Ù†Ø¯ÛŒ Ø¨Ø§ 5 Ø±Ø¯ÛŒÙ Ã— 2 Ø³ØªÙˆÙ† + Ø¯Ú©Ù…Ù‡ Ø¬Ø³ØªØ¬Ùˆ + Ù†Ø§ÙˆØ¨Ø±ÛŒ
        """
        buttons = []
        
        # 5 Ø±Ø¯ÛŒÙ Ã— 2 Ø³ØªÙˆÙ† (10 Ø¯Ø³ØªÙ‡â€ŒØ¨Ù†Ø¯ÛŒ)
        for i in range(0, len(items), 2):
            row = []
            idx, cat = items[i]
            row.append(InlineKeyboardButton(text=cat, callback_data=f"cat_{idx}"))
            if i + 1 < len(items):
                idx2, cat2 = items[i + 1]
                row.append(InlineKeyboardButton(text=cat2, callback_data=f"cat_{idx2}"))
            buttons.append(row)

        # Ø¯Ú©Ù…Ù‡ Ø¬Ø³ØªØ¬Ùˆ (ÙÙ‚Ø· Ø¯Ø± Ù„ÛŒØ³Øª Ø§ØµÙ„ÛŒØŒ Ù†Ù‡ Ø¯Ø± Ù†ØªØ§ÛŒØ¬ Ø¬Ø³ØªØ¬Ùˆ)
        if prefix == "cat_page":
            buttons.append([InlineKeyboardButton(text=MSG["search_btn"], callback_data="start_search")])

        # Ø¯Ú©Ù…Ù‡â€ŒÙ‡Ø§ÛŒ Ù†Ø§ÙˆØ¨Ø±ÛŒ
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton(text=MSG["prev_page"], callback_data=f"{prefix}_{page - 1}"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text=MSG["next_page"], callback_data=f"{prefix}_{page + 1}"))
        
        if nav_row:
            buttons.append(nav_row)

        return InlineKeyboardMarkup(inline_keyboard=buttons).to_dict()

    def _show_category_page(
        self, items: List[tuple], page: int, prefix: str, title: str
    ) -> dict:
        """
        Ù†Ù…Ø§ÛŒØ´ ØµÙØ­Ù‡â€ŒØ¨Ù†Ø¯ÛŒ Ø¯Ø³ØªÙ‡â€ŒØ¨Ù†Ø¯ÛŒâ€ŒÙ‡Ø§
        """
        total_pages = max(1, (len(items) + self.CATS_PER_PAGE - 1) // self.CATS_PER_PAGE)
        page = max(0, min(page, total_pages - 1))
        start = page * self.CATS_PER_PAGE
        page_items = items[start: start + self.CATS_PER_PAGE]
        markup = self._build_category_keyboard(page_items, page, total_pages, prefix)
        return {"text": title, "reply_markup": markup}

    # -------------------------------------------------------------------------
    # Public entry point
    # -------------------------------------------------------------------------
    async def handle(self, chat_id: int, text: str) -> str | dict:
        """
        Ø¯Ø±ÛŒØ§ÙØª ÛŒÚ© Ù¾ÛŒØ§Ù… Ù…ØªÙ†ÛŒØŒ Ù¾Ø±Ø¯Ø§Ø²Ø´ Ø¨Ø± Ù¾Ø§ÛŒÙ‡ ÙˆØ¶Ø¹ÛŒØª ÙØ¹Ù„ÛŒ Ú©Ø§Ø±Ø¨Ø± (FSM)
        Ùˆ Ø¨Ø±Ú¯Ø±Ø¯Ø§Ù†Ø¯Ù† Ù¾Ø§Ø³Ø® â€“ Ù…ÛŒâ€ŒØªÙˆØ§Ù†Ø¯ Ø±Ø´ØªÙ‡ Ø³Ø§Ø¯Ù‡ ÛŒØ§ Ø¯ÛŒÚ©Ø´Ù†Ø±ÛŒ Ø´Ø§Ù…Ù„
        ``text`` Ùˆ ``reply_markup`` Ø¨Ø§Ø´Ø¯.
        """
        session = self._get_session(chat_id)
        state   = session["state"]
        logger.debug("handle | chat_id=%s state=%s text=%r", chat_id, state, text)

        # â”€â”€ ÙØ±Ù…Ø§Ù† /start â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if text.strip() == "/start":
            # Ø¨Ø§ /start Ù…Ø³ØªÙ‚ÛŒÙ…Ø§Ù‹ Ø¨Ù‡ Ù…Ø±Ø­Ù„Ù‡Ù” Ø¯Ø±ÛŒØ§ÙØª Ø´Ù…Ø§Ø±Ù‡ Ù…ÙˆØ¨Ø§ÛŒÙ„ Ù…ÛŒâ€ŒØ±ÙˆÛŒÙ…
            return await self._start(chat_id)

        # â”€â”€ ØªÙˆØ²ÛŒØ¹ Ø¨Ù‡ ØªÙˆØ§Ø¨Ø¹ Ù…Ø±Ø¨ÙˆØ· Ø¨Ù‡ ÙˆØ¶Ø¹ÛŒØª ÙØ¹Ù„ÛŒ (FSM) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        handlers = {
            RegState.WAIT_PHONE:    self._step_phone,
            RegState.WAIT_OTP:      self._step_otp,
            RegState.WAIT_NAME:     self._step_name,
            RegState.WAIT_BUSINESS: self._step_business,
            RegState.WAIT_WEBSITE:  self._step_website,
            RegState.WAIT_EMAIL:    self._step_email,
            RegState.WAIT_CATEGORY: self._step_category,
        }

        fn = handlers.get(state)
        if fn:
            return await fn(chat_id, text.strip())

        # Ø§Ú¯Ø± Ú©Ø§Ø±Ø¨Ø± Ù‚Ø¨Ù„Ø§Ù‹ Ø«Ø¨Øªâ€ŒÙ†Ø§Ù… ÛŒØ§ ÙˆØ±ÙˆØ¯ ØªÚ©Ù…ÛŒÙ„ Ú©Ø±Ø¯Ù‡ Ø¨Ø§Ø´Ø¯
        if state == RegState.DONE:
            return "âœ… Ø´Ù…Ø§ Ù‚Ø¨Ù„Ø§Ù‹ ÙˆØ§Ø±Ø¯ Ø´Ø¯ÛŒØ¯. Ø§Ø² Ù…Ù†ÙˆÛŒ Ø§ØµÙ„ÛŒ Ø§Ø³ØªÙØ§Ø¯Ù‡ Ú©Ù†ÛŒØ¯."

        # fallback â†’ Ø±Ø§Ù‡â€ŒØ§Ù†Ø¯Ø§Ø²ÛŒ Ù…Ø¬Ø¯Ø¯ ÙØ±Ø¢ÛŒÙ†Ø¯
        return await self._start(chat_id)

    # -------------------------------------------------------------------------
    # Steps â€“ ØªÙˆØ§Ù„ÛŒ Ù…Ø±Ø§Ø­Ù„ Ø«Ø¨Øªâ€ŒÙ†Ø§Ù… / ÙˆØ±ÙˆØ¯
    # -------------------------------------------------------------------------
    async def _start(self, chat_id: int) -> str:
        """
        Ù…Ù‚Ø¯Ø§Ø±Ø¯Ù‡ÛŒ Ø§ÙˆÙ„ÛŒÙ‡ Ø³Ø´Ù†Ø› Ø¯Ø± Ø§ÛŒÙ† Ù†Ø³Ø®Ù‡ Ø¨Ù„Ø§ÙØ§ØµÙ„Ù‡ Ø´Ù…Ø§Ø±Ù‡ Ù…ÙˆØ¨Ø§ÛŒÙ„
        Ø§Ø² Ú©Ø§Ø±Ø¨Ø± Ø¯Ø±Ø®ÙˆØ§Ø³Øª Ù…ÛŒâ€ŒØ´ÙˆØ¯ (Ø¨Ø¯ÙˆÙ† Ù¾Ø±Ø³Ø´ Ø§Ø³Ù… Ø¨Ø±Ø§ÛŒ Ú©Ø§Ø±Ø¨Ø±Ù‡Ø§ÛŒ Ù…ÙˆØ¬ÙˆØ¯).
        """
        self._sessions[chat_id] = {"state": RegState.WAIT_PHONE, "data": {}}
        logger.info("Registration / login started for chat_id=%s", chat_id)
        return MSG["ask_phone"]

    async def _step_phone(self, chat_id: int, text: str) -> str | dict:
        """
        Ø¯Ø±ÛŒØ§ÙØª Ø´Ù…Ø§Ø±Ù‡ Ù…ÙˆØ¨Ø§ÛŒÙ„ØŒ Ø¨Ø±Ø±Ø³ÛŒ ÙˆØ¬ÙˆØ¯ Ú©Ø§Ø±Ø¨Ø± (login) ÛŒØ§ Ø«Ø¨Øªâ€ŒÙ†Ø§Ù… Ø¬Ø¯ÛŒØ¯ØŒ
        Ø§Ø±Ø³Ø§Ù„ OTPØŒ Ø°Ø®ÛŒØ±Ù‡ Ø²Ù…Ø§Ù† Ø§Ø±Ø³Ø§Ù„ Ø¨Ø±Ø§ÛŒ Ø´Ù…Ø§Ø±Ø´ Ù…Ø¹Ú©ÙˆØ³ØŒ Ùˆ Ø¨Ø§Ø²Ú¯Ø±Ø¯Ø§Ù†Ø¯Ù†
        Ù¾ÛŒØ§Ù… OTP Ù‡Ù…Ø±Ø§Ù‡ Ú©ÛŒØ¨ÙˆØ±Ø¯ Ø´Ù…Ø§Ø±Ø´ Ù…Ø¹Ú©ÙˆØ³.
        """
        if not self._valid_phone(text):
            return MSG["invalid"]

        # Ø¨Ø±Ø±Ø³ÛŒ Ú©Ø§Ø±Ø¨Ø± Ø¯Ø± Ø¯ÛŒØªØ§Ø¨ÛŒØ³
        from src.database.db_manager import SessionLocal

        db = SessionLocal()

        try:
            user = self._um.login(text)   # Ø§Ú¯Ø± Ú©Ø§Ø±Ø¨Ø± ÙˆØ¬ÙˆØ¯ Ø¯Ø§Ø´ØªÙ‡ Ø¨Ø§Ø´Ø¯
        except ValueError:
            user = None                   # Ú©Ø§Ø±Ø¨Ø± ÙˆØ¬ÙˆØ¯ Ù†Ø¯Ø§Ø±Ø¯ â†’ Ø«Ø¨Øªâ€ŒÙ†Ø§Ù…
        finally:
            db.close()

        # Ø°Ø®ÛŒØ±Ù‡ Ø§Ø·Ù„Ø§Ø¹Ø§Øª Ù¾Ø§ÛŒÙ‡ Ø¯Ø± Ø³Ø´Ù†
        self._sessions[chat_id]["data"]["phone"] = text
        self._sessions[chat_id]["data"]["is_login"] = bool(user)

        # Ø§Ø±Ø³Ø§Ù„ OTP
        sent = await self._otp_service.send(text)
        if not sent:
            logger.error("OTP send failed | chat_id=%s phone=%s", chat_id, text)
            # Ø´Ù…Ø§Ø±Ù‡ Ø±Ùˆ Ø¯Ø± Ø³Ø´Ù† Ø°Ø®ÛŒØ±Ù‡ Ú©Ù† ØªØ§ Ø¯Ú©Ù…Ù‡ Ø§Ø±Ø³Ø§Ù„ Ù…Ø¬Ø¯Ø¯ Ú©Ø§Ø± Ú©Ù†Ù‡
            self._sessions[chat_id]["data"]["phone"] = text
            markup = self._otp_resend_markup(remaining=0)
            return {
                "text": "âŒ Ø§Ø±Ø³Ø§Ù„ Ú©Ø¯ ØªØ£ÛŒÛŒØ¯ Ø¨Ø§ Ø®Ø·Ø§ Ù…ÙˆØ§Ø¬Ù‡ Ø´Ø¯. Ù„Ø·ÙØ§Ù‹ Ù…Ø¬Ø¯Ø¯ Ø§Ù…ØªØ­Ø§Ù† Ú©Ù†ÛŒØ¯.",
                "reply_markup": markup
            }

        # Ø²Ù…Ø§Ù†â€ŒØ³Ù†Ø¬ 5 Ø¯Ù‚ÛŒÙ‚Ù‡ (300 Ø«Ø§Ù†ÛŒÙ‡)
        self._sessions[chat_id]["data"]["otp_sent_at"] = time.time()
        self._set_state(chat_id, RegState.WAIT_OTP)

        # Ù¾ÛŒØ§Ù… OTP Ù‡Ù…Ø±Ø§Ù‡ Ú©ÛŒØ¨ÙˆØ±Ø¯ Ø´Ù…Ø§Ø±Ø´ Ù…Ø¹Ú©ÙˆØ³ (ÙˆØ¸ÛŒÙÙ‡Ù” Ø´Ù…Ø§Ø±Ø´ Ù…Ø¹Ú©ÙˆØ³ Ø¯Ø± Ù…ØªØ¯ _otp_sent_with_keyboard)
        await self._otp_sent_with_keyboard(chat_id, text, new=False)
        return "" 

    async def _step_otp(self, chat_id: int, text: str) -> str | dict:
        """
        Ø¨Ø±Ø±Ø³ÛŒ Ø²Ù…Ø§Ù†â€ŒØ³Ù†Ø¬ (Ø¨Ù‡â€ŒØ§Ø²Ø§ÛŒ 300 Ø«Ø§Ù†ÛŒÙ‡) Ùˆ Ø§Ø¹ØªØ¨Ø§Ø±Ø³Ù†Ø¬ÛŒ Ú©Ø¯ OTP.
        Ø§Ú¯Ø± Ú©Ø§Ø±Ø¨Ø± Ù‚Ø¨Ù„Ø§Ù‹ Ø«Ø¨Øªâ€ŒÙ†Ø§Ù… Ú©Ø±Ø¯Ù‡ Ø¨Ø§Ø´Ø¯ â†’ ÙˆØ±ÙˆØ¯ (login) Ù…ÙˆÙÙ‚.
        Ø¯Ø± ØºÛŒØ± Ø§ÛŒÙ†â€ŒØµÙˆØ±Øª Ø¨Ù‡ Ù…Ø±Ø­Ù„Ù‡Ù” Ø¯Ø±ÛŒØ§ÙØª Ù†Ø§Ù… (WAIT_NAME) Ù…ÛŒâ€ŒØ±ÙˆÛŒÙ….
        """
        session = self._get_session(chat_id)
        phone   = session["data"]["phone"]

        sent_at = session["data"].get("otp_sent_at")
        if not sent_at:
            # ÛŒØ¹Ù†ÛŒ ØªØ§ Ø§Ù„Ø§Ù† Ú©Ø¯ÛŒ Ø¨Ø§ Ù…ÙˆÙÙ‚ÛŒØª Ø§Ø±Ø³Ø§Ù„ Ù†Ø´Ø¯Ù‡ ÛŒØ§ Ø³Ø´Ù† Ù…Ø´Ú©Ù„ Ø¯Ø§Ø±Ø¯
            logger.warning("OTP used before sent | chat_id=%s phone=%s", chat_id, phone)
            return "âš ï¸ Ù‡Ù†ÙˆØ² Ú©Ø¯ ØªØ£ÛŒÛŒØ¯ Ø¨Ø±Ø§ÛŒ Ø´Ù…Ø§ Ø§Ø±Ø³Ø§Ù„ Ù†Ø´Ø¯Ù‡ ÛŒØ§ Ø¨Ø§ Ø®Ø·Ø§ Ù…ÙˆØ§Ø¬Ù‡ Ø´Ø¯Ù‡ Ø§Ø³Øª. Ù„Ø·ÙØ§Ù‹ Ø§Ø¨ØªØ¯Ø§ Ø§Ø² Ø¯Ú©Ù…Ù‡ Â«Ø§Ø±Ø³Ø§Ù„ Ù…Ø¬Ø¯Ø¯ Ú©Ø¯Â» Ø§Ø³ØªÙØ§Ø¯Ù‡ Ú©Ù†ÛŒØ¯."

        elapsed = time.time() - sent_at
        if elapsed > self._otp_expiry:
            logger.warning(
                "OTP expired | chat_id=%s phone=%s elapsed=%.1f",
                chat_id, phone, elapsed
            )
            return await self._otp_error_with_keyboard(chat_id)

        # ---------- ØªØ§ÛŒÙ…Ø± 5 Ø¯Ù‚ÛŒÙ‚Ù‡ ----------
        elapsed = time.time() - session["data"].get("otp_sent_at", 0)
        if elapsed > self._otp_expiry:
            logger.warning(
                "OTP expired | chat_id=%s phone=%s elapsed=%.1f",
                chat_id, phone, elapsed
            )
            return await self._otp_error_with_keyboard(chat_id)

        # ---------- Ø§Ø¹ØªØ¨Ø§Ø±Ø³Ù†Ø¬ÛŒ Ú©Ø¯ OTP ----------
        if not self._otp_service.verify(phone, text):
            logger.warning("OTP verification failed | chat_id=%s phone=%s", chat_id, phone)
            return MSG["otp_fail"]

        # ---------- Ø§Ú¯Ø± Ú©Ø§Ø±Ø¨Ø± Ù‚Ø¨Ù„Ø§Ù‹ Ø«Ø¨Øªâ€ŒÙ†Ø§Ù… Ú©Ø±Ø¯Ù‡ Ø¨Ø§Ø´Ø¯ (login) ----------
        if session["data"].get("is_login"):
            self._set_state(chat_id, RegState.DONE)
            logger.info("Login success | chat_id=%s phone=%s", chat_id, phone)
            return MSG["login_done"]

        # ---------- Ú©Ø§Ø±Ø¨Ø± Ø¬Ø¯ÛŒØ¯ â†’ Ø§Ø¯Ø§Ù…Ù‡ Ø«Ø¨Øªâ€ŒÙ†Ø§Ù… ----------
        self._set_state(chat_id, RegState.WAIT_NAME)
        return MSG["ask_name"]

    async def _step_name(self, chat_id: int, text: str) -> str:
        """Ø°Ø®ÛŒØ±Ù‡ Ù†Ø§Ù… Ùˆ Ù†Ø§Ù… Ø®Ø§Ù†ÙˆØ§Ø¯Ú¯ÛŒ Ùˆ Ø±ÙØªÙ† Ø¨Ù‡ Ù…Ø±Ø­Ù„Ù‡Ù” Ù†Ø§Ù… Ú©Ø³Ø¨â€ŒÙˆÚ©Ø§Ø±."""
        if len(text) < 3:
            return MSG["invalid"]
        self._sessions[chat_id]["data"]["full_name"] = text
        self._set_state(chat_id, RegState.WAIT_BUSINESS)
        return MSG["ask_biz"]

    async def _step_business(self, chat_id: int, text: str) -> str:
        """Ø°Ø®ÛŒØ±Ù‡ Ù†Ø§Ù… Ú©Ø³Ø¨â€ŒÙˆÚ©Ø§Ø± Ùˆ Ø±ÙØªÙ† Ø¨Ù‡ Ù…Ø±Ø­Ù„Ù‡Ù” ÙˆØ¨â€ŒØ³Ø§ÛŒØª."""
        if len(text) < 2:
            return MSG["invalid"]
        self._sessions[chat_id]["data"]["business_name"] = text
        self._set_state(chat_id, RegState.WAIT_WEBSITE)
        return MSG["ask_site"]

    async def _step_website(self, chat_id: int, text: str) -> str | dict:
        """Ø°Ø®ÛŒØ±Ù‡ Ø¢Ø¯Ø±Ø³ ÙˆØ¨â€ŒØ³Ø§ÛŒØª Ø¨Ø¯ÙˆÙ† Ù‡ÛŒÚ† Ù†ÙˆØ¹ ÙˆÙ„ÛŒØ¯ÛŒØ´Ù†."""
        url = text.strip()

        # Ú©Ø§Ø±Ø¨Ø± ÙÙ‚Ø· Ø¯Ø§Ù…Ù†Ù‡ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ù…ÛŒâ€ŒÚ©Ù†Ø¯
        if not url.startswith("http"):
            url = "https://" + url

        self._sessions[chat_id]["data"]["website"] = url
        self._set_state(chat_id, RegState.WAIT_EMAIL)

        # Ø¯Ú©Ù…Ù‡ Ø±Ø¯ Ø§ÛŒÙ…ÛŒÙ„
        btn_skip = InlineKeyboardButton(
            text=MSG["skip_email_btn"], callback_data="skip_email"
        )
        markup = InlineKeyboardMarkup(inline_keyboard=[[btn_skip]])

        return {"text": MSG["ask_email"], "reply_markup": markup.to_dict()}

    async def _step_email(self, chat_id: int, text: str) -> str | dict:
        """
        Ø°Ø®ÛŒØ±Ù‡ Ø§ÛŒÙ…ÛŒÙ„ (ÛŒØ§ Ø®Ø§Ù„ÛŒ Ú©Ø±Ø¯Ù† Ø¢Ù† Ø¯Ø± ØµÙˆØ±Øª ÙØ´Ø§Ø± Ø¯Ø§Ø¯Ù† Ø¯Ú©Ù…Ù‡ Â«Ø±Ø¯ Ø§ÛŒÙ…ÛŒÙ„Â»
        Ú©Ù‡ Ø¯Ø± `handle_callback` Ù…Ø¯ÛŒØ±ÛŒØª Ù…ÛŒâ€ŒØ´ÙˆØ¯) Ùˆ Ù†Ù…Ø§ÛŒØ´ ØµÙØ­Ù‡Ù” Ø§ÙˆÙ„
        Ø¨Ø±Ø§ÛŒ Ø§Ù†ØªØ®Ø§Ø¨ Ø¯Ø³ØªÙ‡â€ŒØ¨Ù†Ø¯ÛŒ.
        """
        self._sessions[chat_id]["data"]["email"] = text
        self._set_state(chat_id, RegState.WAIT_CATEGORY)

        # Ù†Ù…Ø§ÛŒØ´ Ù„ÛŒØ³Øª Ø¯Ø³ØªÙ‡â€ŒØ¨Ù†Ø¯ÛŒâ€ŒÙ‡Ø§
        items = [(i, cat) for i, cat in enumerate(CATEGORIES)]
        return self._show_category_page(items, page=0, prefix="cat_page", title=MSG["ask_cat"])

    async def _step_category(self, chat_id: int, text: str) -> str | dict:
        """
        Ù¾Ø±Ø¯Ø§Ø²Ø´ Ø¬Ø³ØªØ¬ÙˆÛŒ Ø¯Ø³ØªÙ‡â€ŒØ¨Ù†Ø¯ÛŒ
        """
        query = text.strip()
        if not query:
            return "Ù„Ø·ÙØ§Ù‹ Ø¹Ø¨Ø§Ø±Øª Ø¬Ø³ØªØ¬Ùˆ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯."

        results = [(i, cat) for i, cat in enumerate(CATEGORIES) if query.lower() in cat.lower()]

        if not results:
            return "âŒ Ù†ØªÛŒØ¬Ù‡â€ŒØ§ÛŒ ÛŒØ§ÙØª Ù†Ø´Ø¯. Ù„Ø·ÙØ§Ù‹ Ø¹Ø¨Ø§Ø±Øª Ø¯ÛŒÚ¯Ø±ÛŒ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯."

        session = self._get_session(chat_id)
        session["data"]["search_results"] = results
        return self._show_category_page(results, page=0, prefix="search_page", title=f"ðŸ” Ù†ØªØ§ÛŒØ¬ Ø¬Ø³ØªØ¬Ùˆ ({len(results)} Ù…ÙˆØ±Ø¯)")

    # -------------------------------------------------------------------------
    # Callback Handler â€“ Ù…Ø¯ÛŒØ±ÛŒØª Ú©Ù„ÛŒÚ© Ø±ÙˆÛŒ Ø¯Ú©Ù…Ù‡â€ŒÙ‡Ø§
    # -------------------------------------------------------------------------
    async def handle_callback(self, chat_id: int, data: str) -> str | dict:
        """
        Ù¾Ø±Ø¯Ø§Ø²Ø´ Ø¯Ú©Ù…Ù‡â€ŒÙ‡Ø§ÛŒ Ø§ÛŒÙ†Ù„Ø§ÛŒÙ†:
        - Ø§Ø±Ø³Ø§Ù„ Ù…Ø¬Ø¯Ø¯ OTP
        - Ø±Ø¯ Ø§ÛŒÙ…ÛŒÙ„
        - Ù†Ø§ÙˆØ¨Ø±ÛŒ Ù„ÛŒØ³Øª Ø¯Ø³ØªÙ‡â€ŒÙ‡Ø§
        - Ø§Ù†ØªØ®Ø§Ø¨ Ø¯Ø³ØªÙ‡
        - Ø¬Ø³ØªØ¬Ùˆ
        """
        session = self._get_session(chat_id)
        logger.debug("callback | chat_id=%s data=%r state=%s", chat_id, data, session["state"])

        # --------------------------------------------------------------
        # Ø§Ø±Ø³Ø§Ù„ Ù…Ø¬Ø¯Ø¯ OTP
        # --------------------------------------------------------------
        if data == "resend_otp":
            phone = session["data"].get("phone")
            if not phone:
                return "Ø´Ù…Ø§Ø±Ù‡ Ù…ÙˆØ¨Ø§ÛŒÙ„ Ø¯Ø± Ø³Ø´Ù† Ù…ÙˆØ¬ÙˆØ¯ Ù†ÛŒØ³Øª. Ù„Ø·ÙØ§Ù‹ Ø¯ÙˆØ¨Ø§Ø±Ù‡ /start Ø¨Ø²Ù†ÛŒØ¯."

            sent = await self._otp_service.send(phone)
            if not sent:
                logger.error("OTP resend failed | chat_id=%s phone=%s", chat_id, phone)
                markup = self._otp_resend_markup(remaining=0)
                return {"text": "âŒ Ø§Ø±Ø³Ø§Ù„ Ù…Ø¬Ø¯Ø¯ Ø¨Ø§ Ø®Ø·Ø§ Ù…ÙˆØ§Ø¬Ù‡ Ø´Ø¯.", "reply_markup": markup}

            # Ø¨Ø±ÙˆØ²Ø±Ø³Ø§Ù†ÛŒ Ø²Ù…Ø§Ù† Ø§Ø±Ø³Ø§Ù„
            session["data"]["otp_sent_at"] = time.time()
            return await self._otp_sent_with_keyboard(chat_id, phone, new=True)

        # --------------------------------------------------------------
        # Ø±Ø¯ Ø§ÛŒÙ…ÛŒÙ„
        # --------------------------------------------------------------
        if data == "skip_email":
            session["data"]["email"] = None
            self._set_state(chat_id, RegState.WAIT_CATEGORY)

            items = [(i, c) for i, c in enumerate(CATEGORIES)]
            return self._show_category_page(items, 0, "cat_page", MSG["ask_cat"])

        # --------------------------------------------------------------
        # Ù†Ø§ÙˆØ¨Ø±ÛŒ ØµÙØ­Ù‡â€ŒÙ‡Ø§ÛŒ Ø¯Ø³ØªÙ‡â€ŒØ¨Ù†Ø¯ÛŒ (Ù„ÛŒØ³Øª Ø§ØµÙ„ÛŒ)
        # --------------------------------------------------------------
        if data.startswith("cat_page_"):
            page = int(data.split("_")[-1])
            items = [(i, c) for i, c in enumerate(CATEGORIES)]
            return self._show_category_page(items, page, "cat_page", MSG["ask_cat"])

        # --------------------------------------------------------------
        # Ù†Ø§ÙˆØ¨Ø±ÛŒ ØµÙØ­Ù‡â€ŒÙ‡Ø§ÛŒ Ø¯Ø³ØªÙ‡â€ŒØ¨Ù†Ø¯ÛŒ (Ù†ØªØ§ÛŒØ¬ Ø¬Ø³ØªØ¬Ùˆ)
        # --------------------------------------------------------------
        if data.startswith("search_page_"):
            page = int(data.split("_")[-1])
            results = session["data"].get("search_results", [])
            return self._show_category_page(results, page, "search_page", "ðŸ” Ù†ØªØ§ÛŒØ¬ Ø¬Ø³ØªØ¬Ùˆ")

        # --------------------------------------------------------------
        # Ø´Ø±ÙˆØ¹ Ø¬Ø³ØªØ¬Ùˆ (Ú©Ø§Ø±Ø¨Ø± Ø¨Ø§ÛŒØ¯ Ù…ØªÙ† Ø¨ÙØ±Ø³ØªØ¯)
        # --------------------------------------------------------------
        if data == "start_search":
            return "ðŸ”Ž Ù„Ø·ÙØ§Ù‹ Ø¹Ø¨Ø§Ø±Øª Ù…ÙˆØ±Ø¯Ù†Ø¸Ø± Ø±Ø§ Ø§Ø±Ø³Ø§Ù„ Ú©Ù†ÛŒØ¯."

        # --------------------------------------------------------------
        # Ø§Ù†ØªØ®Ø§Ø¨ Ø¯Ø³ØªÙ‡
        # --------------------------------------------------------------
        if data.startswith("cat_"):
            idx = int(data.split("_")[1])
            if 0 <= idx < len(CATEGORIES):
                category = CATEGORIES[idx]
                session["data"]["category"] = category
                self._set_state(chat_id, RegState.DONE)
                return await self._finalize_registration(chat_id)

            return "âŒ Ø¯Ø³ØªÙ‡ Ù†Ø§Ù…Ø¹ØªØ¨Ø± Ø§Ø³Øª."

        # --------------------------------------------------------------
        # fallback
        # --------------------------------------------------------------
        return "Ø¯Ø³ØªÙˆØ± Ù†Ø§Ù…Ø¹ØªØ¨Ø±."

    # -------------------------------------------------------------------------
    # Registration finalizer
    # -------------------------------------------------------------------------
    async def _finalize_registration(self, chat_id: int) -> str:
        data = self._sessions[chat_id]["data"]
        try:
            user = self._um.register(
                phone=data.get("phone"),
                full_name=data.get("full_name"),
                business_name=data.get("business_name"),
                website=data.get("website"),
                email=data.get("email"),
                category=data.get("category"),
                bale_user_id=str(chat_id)
            )
            logger.info(f"User {user.id} registered successfully")
        except Exception as e:
            logger.exception("Registration DB error")
            # state Ø±Ùˆ Ø¨Ø±Ú¯Ø±Ø¯ÙˆÙ† ØªØ§ Router Ù…Ù†Ùˆ Ù†Ø´ÙˆÙ† Ù†Ø¯Ù‡
            self._set_state(chat_id, RegState.IDLE)
            return f"âŒ Ø®Ø·Ø§ Ø¯Ø± Ø«Ø¨Øª Ø§Ø·Ù„Ø§Ø¹Ø§Øª: {e}"
        return MSG["done"]

