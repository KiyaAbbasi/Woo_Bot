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

from src.logger.log_handler import get_logger

if TYPE_CHECKING:
    from src.bale.api import BaleBot
    from src.auth.user_manager import UserManager

logger = get_logger("woobot.handlers.main_menu")


# ───────────────────────────── ثابت‌های متن دکمه‌ها ──────────────────────────────

BTN_STORES      = "🏬 فروشگاه‌ها"
BTN_ADD_STORE   = "➕ فروشگاه"
BTN_NETWORKS    = "🌐 شبکه‌ها"
BTN_CHANNELS    = "📣 کانال‌ها"
BTN_WOOCOM      = "🛒 ووکامرس"
BTN_REPORTS     = "📊 گزارش‌ها"
BTN_PROFILE     = "👤 پروفایل"
BTN_HELP        = "❓ راهنما"

MAIN_MENU_BUTTONS = [
    [BTN_STORES, BTN_ADD_STORE],
    [BTN_NETWORKS, BTN_CHANNELS],
    [BTN_WOOCOM, BTN_REPORTS],
    [BTN_PROFILE, BTN_HELP],
]


# ───────────────────── fallback برای ReplyKeyboardMarkup ────────────────────────
# اگر SDK رسمی بله کلاس‌های زیر را داشته باشد، از آن استفاده می‌شود.
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


# ───────────────────────────────── کلاس MainMenuHandler ─────────────────────────

class MainMenuHandler:
    """
    مدیریت منوی اصلی ربات:
      - ساخت کیبورد دو ستونه
      - نمایش منوی اصلی
      - تفسیر انتخاب کاربر و هدایت به زیرمنوها

    این کلاس فقط منوی سطح بالا را مدیریت می‌کند و منطق زیرمنوها
    در فایل‌های جدا مانند stores_menu_handler.py و ... پیاده‌سازی می‌شود.
    """

    def __init__(self, user_manager: UserManager, bot: BaleBot) -> None:
        self._bot = bot
        self._um = user_manager

        # در آینده می‌توان اینجا زیرهندلرها را مقداردهی کرد، مثلاً:
        # from src.handlers.menu.stores_menu_handler import StoresMenuHandler
        # self._stores_handler = StoresMenuHandler(user_manager, bot)
        # فعلاً برای اسکلت، آن‌ها را خالی می‌گذاریم.
        self._stores_handler = None
        self._channels_handler = None
        self._woocommerce_handler = None
        self._reports_handler = None
        self._profile_handler = None
        self._networks_handler = None

    # ───────────────────────────────── کیبورد منوی اصلی ─────────────────────────

    def _build_main_menu_keyboard(self) -> dict:
        """
        ساخت ReplyKeyboard دو ستونه برای منوی اصلی.
        خروجی: دیکشنری مناسب برای ارسال به send_message به‌عنوان reply_markup.
        """
        rows: list[list[KeyboardButton]] = []
        for row_def in MAIN_MENU_BUTTONS:
            row: list[KeyboardButton] = [KeyboardButton(text=label) for label in row_def]
            rows.append(row)

        markup = ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
        return markup.to_dict()

    # ───────────────────────────── اینترفیس عمومی: نمایش منو ─────────────────────

    async def show_menu(self, chat_id: int, welcome: bool = False) -> None:
        """
        نمایش منوی اصلی به کاربر.

        پارامترها
        ----------
        chat_id : int
            شناسه چت کاربر در بله.
        welcome : bool, optional
            اگر True باشد متن خوش‌آمدگویی کوتاه نیز ارسال می‌شود.
        """
        logger.debug("Show main menu | chat_id=%s welcome=%s", chat_id, welcome)

        text = "منوی اصلی را انتخاب کنید:" if not welcome else (
            "🎉 ثبت‌نام/ورود شما انجام شد.\n"
            "از منوی زیر یکی از بخش‌ها را انتخاب کنید:"
        )

        markup = self._build_main_menu_keyboard()
        await self._bot.send_message(chat_id, text, reply_markup=markup)

    # ───────────────────────────── هندل پیام‌های منوی اصلی ──────────────────────

    async def handle_message(self, chat_id: int, text: str) -> Union[str, dict]:
        """
        پردازش متن انتخاب‌شده از منوی اصلی.

        در این اسکلت، فعلاً فقط پاسخ‌های ساده یا پیام‌های Placeholder
        برمی‌گرداند. در مراحل بعدی، این متد زیرمنوهای واقعی را صدا می‌زند.
        """
        text = text.strip()
        logger.debug("MainMenuHandler.handle_message | chat_id=%s text=%r", chat_id, text)

        if text == BTN_STORES:
            # در آینده: self._stores_handler.show_list(chat_id)
            return "📋 لیست فروشگاه‌های شما به‌زودی اینجا نمایش داده می‌شود."

        if text == BTN_ADD_STORE:
            # در آینده: self._stores_handler.start_add_flow(chat_id)
            return (
                "➕ افزودن فروشگاه جدید.\n"
                "در نسخهٔ فعلی فقط یک فروشگاه می‌توانید داشته باشید؛ "
                "اگر فروشگاهی ندارید، مراحل افزودن آغاز خواهد شد."
            )

        if text == BTN_NETWORKS:
            # در آینده: self._networks_handler.show_networks(chat_id)
            return "🌐 شبکه‌های شما: فعلاً فقط «بله» پشتیبانی می‌شود."

        if text == BTN_CHANNELS:
            # در آینده: self._channels_handler.show_channels(chat_id)
            return "📣 مدیریت کانال‌ها به‌زودی از این بخش در دسترس خواهد بود."

        if text == BTN_WOOCOM:
            # در آینده: self._woocommerce_handler.show_status(chat_id)
            return "🛒 وضعیت اتصال ووکامرس از این بخش مدیریت خواهد شد."

        if text == BTN_REPORTS:
            # در آینده: self._reports_handler.show_recent_posts(chat_id)
            return "📊 گزارش آخرین محصولات ارسال‌شده از این بخش قابل مشاهده خواهد بود."

        if text == BTN_PROFILE:
            # در آینده: self._profile_handler.show_profile(chat_id)
            return (
                "👤 پروفایل شما به‌زودی از این بخش قابل مدیریت خواهد بود.\n"
                "در این بخش وضعیت تکمیل تنظیمات با ✅ و ❌ نمایش داده می‌شود."
            )

        if text == BTN_HELP:
            return (
                "❓ راهنما:\n"
                "۱. ابتدا فروشگاه خود را ثبت و به ووکامرس متصل کنید.\n"
                "۲. سپس کانال‌های بله را اضافه کنید.\n"
                "۳. در نهایت زمان‌بندی و تنظیمات ارسال را پیکربندی کنید."
            )

        # اگر متن هیچ‌یک از دکمه‌ها نبود، دوباره منو را نشان بده
        return {
            "text": "⚠️ گزینه نامعتبر. لطفاً از منوی زیر انتخاب کنید:",
            "reply_markup": self._build_main_menu_keyboard(),
        }

    # ───────────────────────────── هندل callbackها (فعلاً خالی) ──────────────────

    async def handle_callback(self, chat_id: int, data: str) -> Union[str, dict]:
        """
        در حال حاضر منوی اصلی فقط از ReplyKeyboard استفاده می‌کند،
        اما برای آینده (در صورت نیاز به InlineKeyboard در منوی اصلی)
        این متد آماده شده است.
        """
        logger.debug("MainMenuHandler.handle_callback | chat_id=%s data=%r", chat_id, data)
        # TODO: در صورت استفاده از دکمه‌های اینلاین در منوی اصلی، اینجا پردازش شود.
        return "⚠️ این نوع دکمه در منوی اصلی پشتیبانی نمی‌شود."
