"""
Woocommerce Bot

router.py
Central message router â€” dispatches updates to the correct handler
based on user state and message content.

@package    Woocommerce Bot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from src.handlers.main_menu_handler import (
    MainMenuHandler,
    BTN_STORES,
    BTN_ADD_STORE,
    BTN_NETWORKS,
    BTN_CHANNELS,
    BTN_WOOCOM,
    BTN_REPORTS,
    BTN_PROFILE,
    BTN_HELP,
)
from src.handlers.registration_handler import RegistrationHandler, RegState
from src.logger.log_handler import get_logger

if TYPE_CHECKING:
    from src.bale.api import BaleBot
    from src.auth.user_manager import UserManager

logger = get_logger("woobot.router")


class Router:
    """
    Central dispatcher for all incoming Bale updates.
    """

    def __init__(self, user_manager: UserManager, bot: BaleBot) -> None:
        self._bot = bot
        self._reg_handler = RegistrationHandler(user_manager, bot)
        self._menu_handler = MainMenuHandler(user_manager, bot)

        # Ù…Ø¬Ù…ÙˆØ¹Ù‡ Ù…ØªÙ† Ø¯Ú©Ù…Ù‡â€ŒÙ‡Ø§ÛŒ Ù…Ù†ÙˆÛŒ Ø§ØµÙ„ÛŒ Ø¨Ø±Ø§ÛŒ ØªØ´Ø®ÛŒØµ Ø³Ø±ÛŒØ¹
        self._main_menu_buttons = {
            BTN_STORES,
            BTN_ADD_STORE,
            BTN_NETWORKS,
            BTN_CHANNELS,
            BTN_WOOCOM,
            BTN_REPORTS,
            BTN_PROFILE,
            BTN_HELP,
        }

    # â”€â”€â”€ Main entry point â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def route(self, update: dict) -> None:
        """Route one Bale update to the appropriate handler."""
        if "message" in update or "edited_message" in update:
            await self._handle_message(update)
            return
        if "callback_query" in update:
            await self._handle_callback(update)
            return
        logger.debug("Unhandled update type: %s", list(update.keys()))

    # â”€â”€â”€ Message routing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    async def _handle_message(self, update: dict) -> None:
        message = update.get("message") or update.get("edited_message")
        if not message:
            return

        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()
        if not text:
            return

        logger.debug("Message | chat_id=%s text=%r", chat_id, text)

        destination = self._resolve_destination(chat_id, text)

        # â”€â”€ 1) Ø¬Ø±ÛŒØ§Ù† Ø«Ø¨Øªâ€ŒÙ†Ø§Ù…/ÙˆØ±ÙˆØ¯ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if destination == "registration":
            reply = await self._reg_handler.handle(chat_id, text)
            await self._send_reply(chat_id, reply)

            # Ø§Ú¯Ø± Ø¨Ø¹Ø¯ Ø§Ø² Ø§ÛŒÙ† Ù¾ÛŒØ§Ù…ØŒ Ú©Ø§Ø±Ø¨Ø± Ø«Ø¨Øªâ€ŒÙ†Ø§Ù…/ÙˆØ±ÙˆØ¯Ø´ Ú©Ø§Ù…Ù„ Ø´Ø¯Ù‡ Ø¨Ø§Ø´Ø¯ (state=DONE)ØŒ
            # ÛŒÚ©â€ŒØ¨Ø§Ø± Ù…Ù†ÙˆÛŒ Ø§ØµÙ„ÛŒ Ø±Ø§ Ù‡Ù… Ù†Ù…Ø§ÛŒØ´ Ù…ÛŒâ€ŒØ¯Ù‡ÛŒÙ….
            session = self._reg_handler.get_session(chat_id)
            if session["state"] == RegState.DONE:
                await self._menu_handler.show_menu(chat_id)

            return

        # â”€â”€ 2) Ú©Ø§Ø±Ø¨Ø± ÙˆØ§Ø±Ø¯ Ø´Ø¯Ù‡ â†’ Ù…Ù†ÙˆÛŒ Ø§ØµÙ„ÛŒ / Ø²ÛŒØ±Ù…Ù†ÙˆÙ‡Ø§ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        if destination == "main_menu":
            # Ø§Ú¯Ø± /menu Ø²Ø¯Ù‡ØŒ Ù…Ù†ÙˆÛŒ Ø§ØµÙ„ÛŒ Ø±Ø§ Ù†Ø´Ø§Ù† Ù…ÛŒâ€ŒØ¯Ù‡ÛŒÙ…
            if text == "/menu":
                await self._menu_handler.show_menu(chat_id)
                return

            # Ø§Ú¯Ø± Ù…ØªÙ† ÛŒÚ©ÛŒ Ø§Ø² Ø¯Ú©Ù…Ù‡â€ŒÙ‡Ø§ÛŒ Ù…Ù†ÙˆÛŒ Ø§ØµÙ„ÛŒ Ø¨ÙˆØ¯ â†’ Ø¨Ù‡ MainMenuHandler Ø¨Ø¯Ù‡ÛŒÙ…
            if text in self._main_menu_buttons:
                reply = await self._menu_handler.handle_message(chat_id, text)
                await self._send_reply(chat_id, reply)
                return

            # Ø¯Ø± ØºÛŒØ± Ø§ÛŒÙ† ØµÙˆØ±ØªØŒ Ù¾ÛŒØ§Ù… Ø®Ø·Ø§ + Ù†Ù…Ø§ÛŒØ´ Ù…Ø¬Ø¯Ø¯ Ù…Ù†ÙˆÛŒ Ø§ØµÙ„ÛŒ
            await self._send_reply(
                chat_id,
                {
                    "text": "âš ï¸ Ú¯Ø²ÛŒÙ†Ù‡ Ù†Ø§Ù…Ø¹ØªØ¨Ø±. Ù„Ø·ÙØ§Ù‹ Ø§Ø² Ù…Ù†ÙˆÛŒ Ø²ÛŒØ± Ø§Ù†ØªØ®Ø§Ø¨ Ú©Ù†ÛŒØ¯:",
                    "reply_markup": self._menu_handler._build_main_menu_keyboard(),  # type: ignore
                },
            )
            return

        # â”€â”€ fallback (Ø¯Ø± Ø­Ø§Ù„Øª Ø¹Ø§Ø¯ÛŒ Ù†Ø¨Ø§ÛŒØ¯ Ø¨Ø±Ø³ÛŒÙ…) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
        logger.debug(
            "Fallback reached in _handle_message | chat_id=%s text=%r destination=%s",
            chat_id, text, destination
        )
        return

    # â”€â”€â”€ Callback routing â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    async def _handle_callback(self, update: dict) -> None:
        callback = update.get("callback_query")
        if not callback:
            return

        chat_id = callback["message"]["chat"]["id"]
        data = callback.get("data", "")
        session = self._reg_handler.get_session(chat_id)
        just_finished_registration = False

        # بعد از تکمیل ورود/ثبت‌نام، callbackهای منوهای اینلاین باید به
        # هندلر منو برسند؛ در غیر این صورت هنوز متعلق به جریان ثبت‌نام هستند.
        if session["state"] == RegState.DONE:
            if data.startswith("store:"):
                reply = await self._menu_handler.handle_store_callback(chat_id, data)
            else:
                reply = await self._menu_handler.handle_callback(chat_id, data)
        else:
            reply = await self._reg_handler.handle_callback(chat_id, data)
            if self._reg_handler.get_session(chat_id)["state"] == RegState.DONE:
                just_finished_registration = True

        await self._send_reply(chat_id, reply)

        if just_finished_registration:
            await self._menu_handler.show_menu(chat_id)

        await self._bot.answer_callback_query(callback["id"])

