"""
WooCommerce to Bale Bot (WooBot)
router.py

Central message router — dispatches updates to the correct handler
based on user state and callback data prefix (modular menu architecture).

@package    WooBot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    2.0.0
@link       [KiyaHolding.com]
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from src.database.db_manager import DatabaseManager
from src.auth.user_manager import UserManager
from src.handlers.registration_handler import RegistrationHandler, RegState
from src.logger.log_handler import get_logger

# New modular menu handlers
from src.handlers.menu.main_menu.main_menu_handler import MainMenuHandler, CB_STORES, CB_REPORTS, CB_PROFILE, CB_HELP
from src.handlers.menu.stores.stores_list_handler import (
    StoresListHandler,
    CB_STORE_SELECT_PREFIX,
    CB_ADD_STORE,
)
from src.handlers.menu.stores.dashboard.store_dashboard import (
    StoreDashboardHandler,
    CB_STORE_EDIT,
    CB_STORE_WOOCOMMERCE,
    CB_STORE_CHANNELS,
    CB_STORE_SCHEDULING,
    CB_STORE_MANUAL_POST,
    CB_BACK_TO_STORES,
)

if TYPE_CHECKING:
    from src.bale.api import BaleBot

logger = get_logger("woobot.router")


class Router:
    """
    Central dispatcher for all incoming Bale updates.
    Routes based on registration state and callback data prefixes.
    """

    def __init__(self, db_manager: DatabaseManager, bot: BaleBot) -> None:
        """
        Initialize the router with all required handlers.

        Args:
            db_manager: Database manager instance.
            bot: BaleBot API client instance.
        """
        self.db = db_manager
        self.bot = bot
        self.user_manager = UserManager(db_manager)

        # Handlers
        self.reg_handler = RegistrationHandler(self.user_manager, bot)
        self.main_menu_handler = MainMenuHandler(db_manager)
        self.stores_list_handler = StoresListHandler(db_manager)
        self.store_dashboard_handler = StoreDashboardHandler(db_manager)

        # Cache for user_id lookups (avoid repeated DB hits)
        self._user_id_cache: dict[int, Optional[int]] = {}

    # ─── Main entry point ─────────────────────────────────────────────────

    async def route(self, update: dict) -> None:
        """Route one Bale update to the appropriate handler."""
        if "message" in update or "edited_message" in update:
            await self._handle_message(update)
            return
        if "callback_query" in update:
            await self._handle_callback(update)
            return
        logger.debug("Unhandled update type: %s", list(update.keys()))

    # ─── Message routing ───────────────────────────────────────────────────

    async def _handle_message(self, update: dict) -> None:
        message = update.get("message") or update.get("edited_message")
        if not message:
            return

        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()

        # If user sends "/start" or any text while not registered, go to registration
        session = self.reg_handler.get_session(chat_id)
        if session["state"] != RegState.DONE:
            reply = await self.reg_handler.handle(chat_id, text)
            await self._send_reply(chat_id, reply)

            # After registration completed, show main menu automatically
            if self.reg_handler.get_session(chat_id)["state"] == RegState.DONE:
                await self._show_main_menu(chat_id)
            return

        # User is logged in.
        # Any text message (except commands) is ignored or prompts main menu.
        if text == "/start" or text == "/menu":
            await self._show_main_menu(chat_id)
            return

        # For any other text, show a helpful message with main menu
        await self._send_reply(
            chat_id,
            {
                "text": "⚠️ لطفاً از منوی زیر گزینه مورد نظر را انتخاب کنید:",
                "reply_markup": await self._build_main_menu_keyboard(chat_id),
            },
        )

    # ─── Callback routing ──────────────────────────────────────────────────

    async def _handle_callback(self, update: dict) -> None:
        callback = update.get("callback_query")
        if not callback:
            return

        chat_id = callback["message"]["chat"]["id"]
        data = callback.get("data", "")

        # Answer callback query to remove loading state
        await self.bot.answer_callback_query(callback["id"])

        # Check if user is in registration flow
        session = self.reg_handler.get_session(chat_id)
        if session["state"] != RegState.DONE:
            reply = await self.reg_handler.handle_callback(chat_id, data)
            await self._send_reply(chat_id, reply)

            if self.reg_handler.get_session(chat_id)["state"] == RegState.DONE:
                await self._show_main_menu(chat_id)
            return

        # User is logged in – get internal user_id
        user_id = await self._get_user_id(chat_id)
        if user_id is None:
            logger.error(f"Logged-in user with chat_id {chat_id} not found in DB.")
            await self._send_reply(chat_id, {"text": "❌ خطای احراز هویت. لطفاً /start را بزنید."})
            return

        # Build a pseudo-update object for handlers that expect Update (from PTB)
        # We'll simulate a minimal Update object using simple namespace.
        class FakeUpdate:
            def __init__(self, callback_query, effective_message):
                self.callback_query = callback_query
                self.effective_message = effective_message

        fake_update = FakeUpdate(callback, callback["message"])

        # Route based on callback data prefix
        if data == "main_menu":
            await self.main_menu_handler.show_main_menu(fake_update, None, user_id)

        elif data == CB_STORES:
            await self.stores_list_handler.show_stores_list(fake_update, None, user_id)

        elif data == CB_REPORTS:
            await self._show_reports(fake_update, user_id)

        elif data == CB_PROFILE:
            await self._show_profile(fake_update, user_id)

        elif data == CB_HELP:
            await self._show_help(fake_update, user_id)

        elif data.startswith(CB_STORE_SELECT_PREFIX):
            store_id = int(data.split(CB_STORE_SELECT_PREFIX)[1])
            await self.stores_list_handler.handle_store_selection(fake_update, None, user_id, store_id)

        elif data == CB_ADD_STORE:
            await self._handle_add_store(fake_update, user_id)

        elif data == CB_BACK_TO_STORES:
            await self.stores_list_handler.show_stores_list(fake_update, None, user_id)

        # Store dashboard actions
        elif data.startswith(CB_STORE_EDIT):
            store_id = int(data.split("_")[-1])
            await self._handle_store_edit(fake_update, user_id, store_id)

        elif data.startswith(CB_STORE_WOOCOMMERCE):
            store_id = int(data.split("_")[-1])
            await self._handle_woocommerce(fake_update, user_id, store_id)

        elif data.startswith(CB_STORE_CHANNELS):
            store_id = int(data.split("_")[-1])
            await self._handle_channels(fake_update, user_id, store_id)

        elif data.startswith(CB_STORE_SCHEDULING):
            store_id = int(data.split("_")[-1])
            await self._handle_scheduling(fake_update, user_id, store_id)

        elif data.startswith(CB_STORE_MANUAL_POST):
            store_id = int(data.split("_")[-1])
            await self._handle_manual_post(fake_update, user_id, store_id)

        else:
            logger.warning(f"Unhandled callback data: {data}")
            await self._send_reply(
                chat_id,
                {"text": "⚠️ این بخش در حال توسعه است. به زودی تکمیل می‌شود."}
            )

    # ─── Helper methods ────────────────────────────────────────────────────

    async def _get_user_id(self, chat_id: int) -> Optional[int]:
        """Retrieve internal user_id from chat_id (Bale user ID)."""
        if chat_id in self._user_id_cache:
            return self._user_id_cache[chat_id]
        user = await self.user_manager.get_user_by_chat_id(chat_id)
        uid = user["id"] if user else None
        self._user_id_cache[chat_id] = uid
        return uid

    async def _show_main_menu(self, chat_id: int) -> None:
        """Send the main menu as a new message (used after registration)."""
        user_id = await self._get_user_id(chat_id)
        if user_id is None:
            return
        # Create a fake update for sending message
        class FakeMessage:
            def __init__(self, chat_id):
                self.chat_id = chat_id
        fake_update = type('obj', (object,), {
            'callback_query': None,
            'effective_message': FakeMessage(chat_id)
        })
        await self.main_menu_handler.show_main_menu(fake_update, None, user_id)

    async def _build_main_menu_keyboard(self, chat_id: int) -> dict:
        """Build inline keyboard markup for main menu (used in fallback)."""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏬 فروشگاه‌های من", callback_data=CB_STORES)],
            [InlineKeyboardButton("📊 گزارش‌ها", callback_data=CB_REPORTS)],
            [InlineKeyboardButton("👤 پروفایل", callback_data=CB_PROFILE)],
            [InlineKeyboardButton("❓ راهنما", callback_data=CB_HELP)],
        ])
        return keyboard.to_dict()

    async def _send_reply(self, chat_id: int, reply: dict) -> None:
        """Send a message using the bot API."""
        if "text" in reply:
            await self.bot.send_message(
                chat_id,
                reply["text"],
                reply_markup=reply.get("reply_markup")
            )

    # ─── Temporary placeholders for unimplemented sections ─────────────────

    async def _show_reports(self, update, user_id: int) -> None:
        await self._send_placeholder(update, "📊 گزارش‌ها")

    async def _show_profile(self, update, user_id: int) -> None:
        await self._send_placeholder(update, "👤 پروفایل")

    async def _show_help(self, update, user_id: int) -> None:
        await self._send_placeholder(update, "❓ راهنما")

    async def _handle_add_store(self, update, user_id: int) -> None:
        await self._send_placeholder(update, "➕ افزودن فروشگاه")

    async def _handle_store_edit(self, update, user_id: int, store_id: int) -> None:
        await self._send_placeholder(update, f"✏️ ویرایش فروشگاه {store_id}")

    async def _handle_woocommerce(self, update, user_id: int, store_id: int) -> None:
        await self._send_placeholder(update, f"🔌 مدیریت ووکامرس فروشگاه {store_id}")

    async def _handle_channels(self, update, user_id: int, store_id: int) -> None:
        await self._send_placeholder(update, f"📣 مدیریت کانال‌های فروشگاه {store_id}")

    async def _handle_scheduling(self, update, user_id: int, store_id: int) -> None:
        await self._send_placeholder(update, f"⚙️ تنظیمات ارسال فروشگاه {store_id}")

    async def _handle_manual_post(self, update, user_id: int, store_id: int) -> None:
        await self._send_placeholder(update, f"📋 ارسال دستی فروشگاه {store_id}")

    async def _send_placeholder(self, update, text: str) -> None:
        """Send a temporary 'under construction' message."""
        if update.callback_query:
            await update.callback_query.edit_message_text(
                f"🚧 {text}\n\nاین بخش به زودی تکمیل خواهد شد."
            )
        else:
            await self.bot.send_message(update.effective_message.chat_id, f"🚧 {text}")
