"""
Woocommerce Bot

main_menu_handler.py
Main menu handler — shows 2‑column main menu and dispatches top‑level
choices to the correct sub‑menus (stores, channels, profile, etc.)

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
from src.handlers.menu.stores_menu_handler import StoresMenuHandler
from src.logger.log_handler import get_logger

if TYPE_CHECKING:
    from src.bale.api import BaleBot
    from src.auth.user_manager import UserManager

logger = get_logger("woobot.handlers.main_menu")


# ───────────────────────────── ثابت‌های متن دکمه‌ها ──────────────────────────────

BTN_STORES      = "🏬 فروشگاه من"
BTN_ADD_STORE   = "➕ افزودن فروشگاه"
BTN_NETWORKS    = "🌐 شبکه‌های اجتماعی"
BTN_CHANNELS    = "📣 کانال‌های من"
BTN_WOOCOM      = "🛒 اتصال به ووکامرس"
BTN_REPORTS     = "📊 گزارش‌های ربات"
BTN_PROFILE     = "👤 پروفایل کاربری"
BTN_HELP        = "❓ راهنما"

MAIN_MENU_BUTTONS = [
    [BTN_STORES, BTN_ADD_STORE],
    [BTN_NETWORKS, BTN_CHANNELS],
    [BTN_WOOCOM, BTN_REPORTS],
    [BTN_PROFILE, BTN_HELP],
]


# ───────────────────── fallback برای ReplyKeyboardMarkup ────────────────────────
try:
    from bale.types import ReplyKeyboardMarkup, KeyboardButton  # type: ignore
except Exception:  # pragma: no cover
    class KeyboardButton:
        def __init__(self, text: str) -> None:
            self.text = text

        def to_dict(self) -> dict:
            return {"text": self.text}

    class ReplyKeyboardMarkup:
        def __init__(self, keyboard: list[list[KeyboardButton]], resize_keyboard: bool = True):
            self.keyboard = keyboard
            self.resize_keyboard = resize_keyboard

        def to_dict(self) -> dict:
            return {
                "keyboard": [
                    [btn.to_dict() for btn in row] for row in self.keyboard
                ],
                "resize_keyboard": self.resize_keyboard,
            }


class MainMenuHandler:
    """
    مدیریت منوی اصلی ربات:
      - ساخت کیبورد دو ستونه (ReplyKeyboard)
      - نمایش منوی اصلی
      - تفسیر انتخاب کاربر و برگرداندن پاسخ اولیه

    منطق زیرمنوها (فروشگاه‌ها، کانال‌ها و ...) در فایل‌های جدا پیاده‌سازی می‌شود.
    """

    def __init__(self, user_manager: UserManager, bot: BaleBot) -> None:
        self._bot = bot
        self._um = user_manager
        self._stores_handler = StoresMenuHandler(user_manager, bot)
        from src.handlers.menu.woocommerce_menu_handler import WoocommerceMenuHandler
        self._woo_handler = WoocommerceMenuHandler(user_manager, bot)

    # ───────────────────────────── کیبورد منوی اصلی ───────────────────────────

    def _build_main_menu_keyboard(self) -> dict:
        """
        ساخت ReplyKeyboard دو ستونه برای منوی اصلی.
        """
        rows: list[list[KeyboardButton]] = []
        for row_def in MAIN_MENU_BUTTONS:
            row: list[KeyboardButton] = [KeyboardButton(label) for label in row_def]
            rows.append(row)

        markup = ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
        return markup.to_dict()

    # ───────────────────────────── نمایش منوی اصلی ─────────────────────────────

    async def show_menu(self, chat_id: int, welcome: bool = False) -> None:
        """
        نمایش منوی اصلی به کاربر.

        اگر welcome=True باشد، متن خوش‌آمدگویی نیز ارسال می‌شود.
        """
        logger.debug("Show main menu | chat_id=%s welcome=%s", chat_id, welcome)

        if welcome:
            text = (
                "🎉 ثبت‌نام/ورود شما انجام شد.\n"
                "از منوی زیر یکی از بخش‌ها را انتخاب کنید:"
            )
        else:
            text = "🏠 منوی اصلی\n\nیکی از گزینه‌ها را انتخاب کنید:"

        markup = self._build_main_menu_keyboard()
        await self._bot.send_message(chat_id, text, reply_markup=markup)

    # ───────────────────────────── هندل پیام‌های منو ───────────────────────────

    async def handle_message(self, chat_id: int, text: str) -> Union[str, dict]:
        text = text.strip()

        # ── فلو ووکامرس ──
        if self._woo_handler.is_in_flow(chat_id):
            return await self._woo_handler.handle_message(chat_id, text)

        # ── فلو stores (ویرایش و زیرمنوها) ──
        if self._stores_handler.is_in_flow(chat_id):
            result = await self._stores_handler.handle_message(chat_id, text)
            if result is None:
                return await self.show_main_menu(chat_id)
            if isinstance(result, dict) and result.get("_action") == "open_woocommerce":
                return await self._woo_handler.start_flow(chat_id)
            return result

        # ── دکمه‌های منوی اصلی ──
        if text == BTN_STORES:
            return await self._stores_handler.show_store_status(chat_id)

        if text == BTN_ADD_STORE:
            return await self._stores_handler.start_add_store_flow(chat_id)

        if text == BTN_WOOCOM:
            return await self._woo_handler.start_flow(chat_id)  # ← این خط عوض شد

        if text == BTN_NETWORKS:
            return "🌐 شبکه‌های اجتماعی\nفعلاً فقط «بله» پشتیبانی می‌شود."

        if text == BTN_CHANNELS:
            return "📣 کانال‌های من\nمدیریت کانال‌های متصل (در حال توسعه)."

        if text == BTN_REPORTS:
            return "📊 گزارش‌های ربات\nگزارش آخرین محصولات ارسال‌شده."

        if text == BTN_PROFILE:
            return "👤 پروفایل کاربری\nتنظیمات پروفایل از این بخش مدیریت می‌شود."

        if text == BTN_HELP:
            return (
                "❓ [راهنما]\n"
                "۱. ابتدا فروشگاه خود را ثبت و به ووکامرس متصل کنید.\n"
                "۲. سپس کانال‌های بله را اضافه کنید.\n"
                "۳. در نهایت زمان‌بندی و تنظیمات ارسال را پیکربندی کنید."
            )

        return {
            "text": "⚠️ گزینه نامعتبر. لطفاً از منوی زیر انتخاب کنید:",
            "reply_markup": self._build_main_menu_keyboard(),
        }


    # ───────────────────────────── هندل callbackها (فعلاً خالی) ────────────────

    async def handle_callback(self, chat_id: int, data: str) -> Union[str, dict]:
        """
        منوی اصلی فعلاً فقط از ReplyKeyboard استفاده می‌کند،
        این متد برای زمانی آماده است که در منوی اصلی از InlineKeyboard استفاده شود.
        """
        logger.debug("MainMenuHandler.handle_callback | chat_id=%s data=%r", chat_id, data)
        return "⚠️ این نوع دکمه در منوی اصلی پشتیبانی نمی‌شود."

    async def handle_store_callback(self, chat_id: int, data: str) -> dict:
        return await self._stores_handler.handle_callback(chat_id, data)
