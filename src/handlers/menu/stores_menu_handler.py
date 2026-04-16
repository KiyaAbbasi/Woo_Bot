"""
Woocommerce Bot

stores_menu_handler.py
Stores menu handler â€” inline keyboard status, edit flows, WooCommerce connect.

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
from sqlalchemy.orm import Session
from src.database.db_manager import SessionLocal
from src.database.models import (
    User,
    StoreSettings,
    BaleChannel,
    SchedulerSettings,
    ContentSettings,
)
from src.utils.helpers import ask_question
from src.logger.log_handler import get_logger

if TYPE_CHECKING:
    from src.bale.api import BaleBot
    from src.auth.user_manager import UserManager

logger = get_logger("woobot.handlers.stores")

try:
    from bale.types import InlineKeyboardButton, InlineKeyboardMarkup  # type: ignore
except Exception:
    class InlineKeyboardButton:
        def __init__(self, text: str, callback_data: str):
            self.text = text
            self.callback_data = callback_data
        def to_dict(self) -> dict:
            return {"text": self.text, "callback_data": self.callback_data}

    class InlineKeyboardMarkup:
        def __init__(self, inline_keyboard: list):
            self.inline_keyboard = inline_keyboard
        def to_dict(self) -> dict:
            return {"inline_keyboard": [[btn.to_dict() for btn in row] for row in self.inline_keyboard]}

try:
    from bale.types import ReplyKeyboardMarkup, KeyboardButton  # type: ignore
except Exception:
    class KeyboardButton:
        def __init__(self, text: str):
            self.text = text
        def to_dict(self) -> dict:
            return {"text": self.text}

    class ReplyKeyboardMarkup:
        def __init__(self, keyboard: list, resize_keyboard: bool = True):
            self.keyboard = keyboard
            self.resize_keyboard = resize_keyboard
        def to_dict(self) -> dict:
            return {"keyboard": [[btn.to_dict() for btn in row] for row in self.keyboard], "resize_keyboard": self.resize_keyboard}


BTN_BACK_MAIN = "â¬…ï¸ Ù…Ù†ÙˆÛŒ Ø§ØµÙ„ÛŒ"
BTN_GO_STORES_MENU = "ðŸ¬ ÙØ±ÙˆØ´Ú¯Ø§Ù‡â€ŒÙ‡Ø§"

CB_STORE_STATUS = "store:status"
CB_EDIT_EMAIL = "store:edit:email"
CB_EDIT_CHANNEL = "store:edit:channel"
CB_EDIT_CATEGORY = "store:edit:category"
CB_EDIT_URL = "store:edit:url"
CB_MANAGER_INFO = "store:manager"

CB_WOOCOM_CONNECT = "store:woocom:connect"
CB_WOOCOM_API = "store:woocom:api"
CB_SEND_SETTINGS = "store:send:settings"


class StoresMenuHandler:
    def __init__(self, user_manager, bot) -> None:
        self._bot = bot
        self._um = user_manager
        self._edit_state: dict[int, str] = {}

    def is_in_flow(self, chat_id: int) -> bool:
        return chat_id in self._edit_state

    def _get_user(self, bale_user_id: str, db: Session):
        return db.query(User).filter(User.bale_user_id == bale_user_id).first()

    def _get_store(self, user_id: int, db: Session):
        return db.query(StoreSettings).filter(StoreSettings.user_id == user_id).first()


    def _get_channels(self, user_id: int, db: Session):
        return db.query(BaleChannel).filter(
            BaleChannel.user_id == user_id,
            BaleChannel.is_active == True,
        ).all()

    def _get_scheduler_settings(self, user_id: int, db: Session):
        return db.query(SchedulerSettings).filter(
            SchedulerSettings.user_id == user_id
        ).first()

    def _get_content_settings(self, user_id: int, db: Session):
        return db.query(ContentSettings).filter(
            ContentSettings.user_id == user_id
        ).first()

    def _mark(self, ok: bool) -> str:
        return "✅" if ok else "❌"

    def _build_send_status(
        self,
        store: StoreSettings | None,
        channels: list[BaleChannel],
        scheduler: SchedulerSettings | None,
        content: ContentSettings | None,
    ) -> dict:
        has_manager = bool(store and store.manager_chat_id)
        has_url = bool(store and store.store_url)
        has_category = bool(store and store.category)
        has_email = bool(store and store.email)
        has_store_connection = bool(
            store
            and store.store_url
            and store.consumer_key
            and store.consumer_secret
            and store.is_connected
        )
        has_channel = len(channels) > 0
        has_content = bool(content)
        has_scheduler = bool(scheduler)
        scheduler_active = bool(scheduler and scheduler.is_active)
        sync_interval_set = bool(scheduler and scheduler.sync_interval)
        daily_limit_set = bool(scheduler and (scheduler.daily_limit or 0) > 0)

        ready = all([
            has_manager,
            has_url,
            has_category,
            has_email,
            has_store_connection,
            has_channel,
            has_content,
            has_scheduler,
            scheduler_active,
            sync_interval_set,
            daily_limit_set,
        ])

        return {
            "has_manager": has_manager,
            "has_url": has_url,
            "has_category": has_category,
            "has_email": has_email,
            "has_store_connection": has_store_connection,
            "has_channel": has_channel,
            "has_content": has_content,
            "has_scheduler": has_scheduler,
            "scheduler_active": scheduler_active,
            "sync_interval_set": sync_interval_set,
            "daily_limit_set": daily_limit_set,
            "ready": ready,
        }

    async def show_store_status(self, chat_id: int) -> dict:
        bale_user_id = str(chat_id)
        db = SessionLocal()

        try:
            user = self._get_user(bale_user_id, db)

            if not user:
                return {"text": "⚠️ کاربر یافت نشد. لطفاً /start بزنید."}

            store = self._get_store(user.id, db)

            # اگر فروشگاه هنوز ساخته نشده، همان‌جا برای کاربر ایجاد می‌شود.
            if not store:
                store = StoreSettings(user_id=user.id, manager_chat_id=chat_id)
                db.add(store)
                db.commit()
                db.refresh(store)

            if not store.manager_chat_id:
                store.manager_chat_id = chat_id
                db.commit()
                db.refresh(store)

            channels = self._get_channels(user.id, db)
            scheduler = self._get_scheduler_settings(user.id, db)
            content = self._get_content_settings(user.id, db)
            send_status = self._build_send_status(store, channels, scheduler, content)

            has_manager = bool(store.manager_chat_id)
            has_url = bool(store.store_url)
            has_category = bool(store.category)
            woocom_ok = bool(store.is_connected)
            has_channel = len(channels) > 0
            has_email = bool(store.email)

            text = (
                "🏬 وضعیت فروشگاه

"
                "وضعیت اتصال‌های فروشگاه شما:

"
                f"{self._mark(has_manager)} مدیر ربات
"
                f"{self._mark(has_url)} آدرس سایت
"
                f"{self._mark(has_category)} دسته‌بندی کسب و کار
"
                f"{self._mark(woocom_ok)} اتصال ووکامرس
"
                f"{self._mark(has_channel)} کانال بله
"
                f"{self._mark(has_email)} ایمیل
"
                f"{self._mark(send_status['ready'])} آمادگی تنظیمات ارسال
"
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(f"👤 آیدی مدیر {self._mark(has_manager)}", CB_MANAGER_INFO)],
                [InlineKeyboardButton(f"🌐 آدرس سایت {self._mark(has_url)}", CB_EDIT_URL)],
                [InlineKeyboardButton(f"🏷 دسته‌بندی کسب و کار {self._mark(has_category)}", CB_EDIT_CATEGORY)],
                [InlineKeyboardButton(f"🛒 اتصال ووکامرس {self._mark(woocom_ok)}", CB_WOOCOM_CONNECT)],
                [InlineKeyboardButton(f"📣 کانال بله {self._mark(has_channel)}", CB_EDIT_CHANNEL)],
                [InlineKeyboardButton(f"✉️ ایمیل {self._mark(has_email)}", CB_EDIT_EMAIL)],
                [InlineKeyboardButton(f"🚀 تنظیمات ارسال فروشگاه {self._mark(send_status['ready'])}", CB_SEND_SETTINGS)],
            ])

            return {
                "text": text,
                "reply_markup": keyboard.to_dict(),
            }

        finally:
            db.close()

    async def handle_callback(self, chat_id: int, data: str) -> dict:
        if data == CB_WOOCOM_CONNECT:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("🔑 وارد کردن API Key", CB_WOOCOM_API)],
            ])

            return {
                "text": "🛒 برای اتصال ووکامرس روش زیر را انتخاب کنید:",
                "reply_markup": keyboard.to_dict(),
            }

        if data == CB_WOOCOM_API:
            self._edit_state[chat_id] = "woocom_key"

            await ask_question(
                self._bot,
                chat_id,
                "🔑 Consumer Key ووکامرس را وارد کنید:",
            )

            return {"text": "منتظر دریافت Consumer Key..."}

        if data == CB_MANAGER_INFO:
            return {
                "text": "👤 مدیر ربات همان کاربری است که ربات را استارت کرده و قابل تغییر نیست."
            }

        if data == CB_SEND_SETTINGS:
            bale_user_id = str(chat_id)
            db = SessionLocal()
            try:
                user = self._get_user(bale_user_id, db)
                if not user:
                    return {"text": "⚠️ کاربر یافت نشد. لطفاً /start بزنید."}

                store = self._get_store(user.id, db)
                channels = self._get_channels(user.id, db)
                scheduler = self._get_scheduler_settings(user.id, db)
                content = self._get_content_settings(user.id, db)
                send_status = self._build_send_status(store, channels, scheduler, content)

                text = (
                    "🚀 وضعیت تنظیمات ارسال فروشگاه

"
                    f"{self._mark(send_status['has_manager'])} مدیر ربات
"
                    f"{self._mark(send_status['has_url'])} آدرس سایت
"
                    f"{self._mark(send_status['has_category'])} دسته‌بندی کسب و کار
"
                    f"{self._mark(send_status['has_email'])} ایمیل
"
                    f"{self._mark(send_status['has_store_connection'])} اتصال کامل ووکامرس
"
                    f"{self._mark(send_status['has_channel'])} حداقل یک کانال فعال
"
                    f"{self._mark(send_status['has_content'])} تنظیمات محتوای ارسال
"
                    f"{self._mark(send_status['has_scheduler'])} تنظیمات زمان‌بندی
"
                    f"{self._mark(send_status['scheduler_active'])} فعال بودن زمان‌بندی
"
                    f"{self._mark(send_status['sync_interval_set'])} بازه Sync مشخص
"
                    f"{self._mark(send_status['daily_limit_set'])} سقف ارسال روزانه
"
                )

                if send_status['ready']:
                    text += (
                        "
✅ همه تیک‌های لازم کامل شده‌اند.
"
                        "ربات آماده ارسال است و ارسال‌ها را بر اساس تنظیمات ذخیره‌شده فروشگاه انجام می‌دهد."
                    )
                else:
                    text += (
                        "
⚠️ تنظیمات ارسال هنوز کامل نشده است.
"
                        "هر موردی که با ❌ مشخص شده باید تکمیل شود تا فروشگاه به وضعیت آماده ارسال برسد."
                    )

                return {"text": text}
            finally:
                db.close()

        edit_map = {
            CB_EDIT_URL: (
                "store_url",
                "🌐 آدرس سایت فروشگاه را وارد کنید:
مثال:
https://site.com",
            ),
            CB_EDIT_EMAIL: (
                "email",
                "✉️ ایمیل فروشگاه را وارد کنید:",
            ),
            CB_EDIT_CHANNEL: (
                "channel",
                "📣 آیدی کانال بله را وارد کنید:
مثال:
@channel",
            ),
            CB_EDIT_CATEGORY: (
                "category",
                "🏷 دسته‌بندی کسب و کار را وارد کنید:",
            ),
        }

        if data in edit_map:
            field, question = edit_map[data]
            self._edit_state[chat_id] = field

            await ask_question(self._bot, chat_id, question)
            return {"text": "✏️ لطفاً مقدار را ارسال کنید."}

        if data == CB_STORE_STATUS:
            return await self.show_store_status(chat_id)

        return {"text": "❓ درخواست نامفهوم."}

    async def handle_message(self, chat_id: int, text: str) -> Union[str, dict]:

        if chat_id in self._edit_state:

            field = self._edit_state.pop(chat_id)

            return await self._save_field(
                chat_id,
                field,
                text
            )

        if text == BTN_GO_STORES_MENU:
            return await self.show_store_status(chat_id)

        return {"text": "Ø§ÛŒÙ† Ø¯Ø³ØªÙˆØ± Ø¯Ø± Ù…Ù†ÙˆÛŒ ÙØ±ÙˆØ´Ú¯Ø§Ù‡â€ŒÙ‡Ø§ Ù¾Ø´ØªÛŒØ¨Ø§Ù†ÛŒ Ù†Ù…ÛŒâ€ŒØ´ÙˆØ¯."}

    async def _save_field(self, chat_id: int, field: str, value: str) -> dict:

        bale_user_id = str(chat_id)

        db = SessionLocal()

        try:

            user = self._get_user(bale_user_id, db)

            if not user:
                return {"text": "âš ï¸ Ú©Ø§Ø±Ø¨Ø± ÛŒØ§ÙØª Ù†Ø´Ø¯."}

            store = self._get_store(user.id, db)

            if not store:
                return {"text": "âš ï¸ ÙØ±ÙˆØ´Ú¯Ø§Ù‡ ÛŒØ§ÙØª Ù†Ø´Ø¯."}

            if field == "woocom_key":

                self._edit_state[chat_id] = "woocom_secret"

                self._edit_state[f"{chat_id}_woocom_key"] = value

                await ask_question(
                    self._bot,
                    chat_id,
                    "ðŸ”‘ Consumer Secret ÙˆÙˆÚ©Ø§Ù…Ø±Ø³ Ø±Ø§ ÙˆØ§Ø±Ø¯ Ú©Ù†ÛŒØ¯:"
                )

                return {}

            if field == "woocom_secret":

                consumer_key = self._edit_state.pop(
                    f"{chat_id}_woocom_key",
                    ""
                )

                store.consumer_key = consumer_key
                store.consumer_secret = value
                store.is_connected = True

                db.commit()

                status = await self.show_store_status(chat_id)

                await self._bot.send_message(
                    chat_id=chat_id,
                    text=status["text"],
                    reply_markup=status["reply_markup"]
                )

                return {"text": "âœ… Ø§ØªØµØ§Ù„ ÙˆÙˆÚ©Ø§Ù…Ø±Ø³ Ø°Ø®ÛŒØ±Ù‡ Ø´Ø¯."}

            if field == "channel":

                channel = BaleChannel(
                    user_id=user.id,
                    channel_id=value,
                    is_active=True
                )

                db.add(channel)
                db.commit()

            else:

                setattr(store, field, value)

                db.commit()

            status = await self.show_store_status(chat_id)

            await self._bot.send_message(
                chat_id=chat_id,
                text=status["text"],
                reply_markup=status["reply_markup"]
            )

            return {"text": "âœ… Ø§Ø·Ù„Ø§Ø¹Ø§Øª Ø°Ø®ÛŒØ±Ù‡ Ø´Ø¯."}

        finally:
            db.close()

    async def start_add_store_flow(self, chat_id: int) -> dict:

        text = "Ø¨Ø±Ø§ÛŒ Ù…Ø¯ÛŒØ±ÛŒØª ÙØ±ÙˆØ´Ú¯Ø§Ù‡ Ø§Ø² Ø¯Ú©Ù…Ù‡ Ø²ÛŒØ± Ø§Ø³ØªÙØ§Ø¯Ù‡ Ú©Ù†ÛŒØ¯."

        keyboard = ReplyKeyboardMarkup(keyboard=[

            [KeyboardButton(text=BTN_GO_STORES_MENU)],
            [KeyboardButton(text=BTN_BACK_MAIN)],

        ])

        await self._bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard.to_dict()
        )

        return {
            "text": text,
            "reply_markup": keyboard.to_dict()
        }


__all__ = [
    "StoresMenuHandler",
    "BTN_BACK_MAIN",
    "BTN_GO_STORES_MENU"
]
