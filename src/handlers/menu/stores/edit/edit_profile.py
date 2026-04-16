"""
WooCommerce to Bale Bot (WooBot)
edit_profile.py

Handler for editing store profile fields (name, website, category, email, etc.).

@package    WooBot
@subpackage Handlers/Menu/Stores/Edit
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

from typing import Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.database.db_manager import DatabaseManager
from src.utils.state_manager import StateManager
from src.logger.log_handler import logger

# Callback data constants
CB_EDIT_FIELD_PREFIX = "edit_field_"
CB_EDIT_DONE = "edit_done"
CB_BACK_TO_DASHBOARD = "back_to_dashboard"

# Field constants
FIELD_MANAGER_NAME = "manager_name"
FIELD_WEBSITE = "website"
FIELD_CATEGORY = "business_category"
FIELD_EMAIL = "email"

# Predefined business categories (mirroring registration)
BUSINESS_CATEGORIES = [
    "پوشاک", "لوازم الکترونیکی", "مواد غذایی",
    "خدمات", "آموزشی", "زیبایی و سلامت",
    "کتاب و لوازم التحریر", "ورزش و سرگرمی", "سایر"
]


class StoreEditProfileHandler:
    """
    Handles editing of store profile information.
    """

    def __init__(self, db_manager: DatabaseManager, state_manager: StateManager):
        """
        Initialize the handler.

        Args:
            db_manager: Database manager instance.
            state_manager: State manager for conversation handling.
        """
        self.db = db_manager
        self.state_manager = state_manager

    async def get_store_details(self, store_id: int) -> Dict[str, Any]:
        """Fetch current store profile data."""
        query = """
            SELECT manager_name, website, business_category, email
            FROM stores WHERE id = ?
        """
        try:
            row = await self.db.fetch_one(query, (store_id,))
            return {
                "manager_name": row.get("manager_name"),
                "website": row.get("website"),
                "business_category": row.get("business_category"),
                "email": row.get("email"),
            } if row else {}
        except Exception as e:
            logger.error(f"Failed to fetch store details for store {store_id}: {e}")
            return {}

    async def show_edit_menu(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        store_id: int
    ) -> None:
        """
        Display the edit profile menu with current field statuses.
        """
        query = update.callback_query
        message = update.effective_message

        details = await self.get_store_details(store_id)
        if not details:
            text = "❌ خطا در بارگذاری اطلاعات فروشگاه."
            if query:
                await query.edit_message_text(text)
            else:
                await message.reply_text(text)
            return

        # Build status text with checkmarks
        def mark(val): return "✅" if val else "❌"

        text = (
            f"✏️ **ویرایش مشخصات فروشگاه**\n\n"
            f"👤 نام مدیر: {details.get('manager_name') or '—'} {mark(details.get('manager_name'))}\n"
            f"🌐 آدرس سایت: {details.get('website') or '—'} {mark(details.get('website'))}\n"
            f"🏷 دسته‌بندی: {details.get('business_category') or '—'} {mark(details.get('business_category'))}\n"
            f"✉️ ایمیل: {details.get('email') or '—'} {mark(details.get('email'))}\n\n"
            "برای ویرایش هر مورد روی دکمه مربوطه کلیک کنید:"
        )

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                f"👤 ویرایش نام مدیر {mark(details.get('manager_name'))}",
                callback_data=f"{CB_EDIT_FIELD_PREFIX}{FIELD_MANAGER_NAME}_{store_id}"
            )],
            [InlineKeyboardButton(
                f"🌐 ویرایش آدرس سایت {mark(details.get('website'))}",
                callback_data=f"{CB_EDIT_FIELD_PREFIX}{FIELD_WEBSITE}_{store_id}"
            )],
            [InlineKeyboardButton(
                f"🏷 ویرایش دسته‌بندی {mark(details.get('business_category'))}",
                callback_data=f"{CB_EDIT_FIELD_PREFIX}{FIELD_CATEGORY}_{store_id}"
            )],
            [InlineKeyboardButton(
                f"✉️ ویرایش ایمیل {mark(details.get('email'))}",
                callback_data=f"{CB_EDIT_FIELD_PREFIX}{FIELD_EMAIL}_{store_id}"
            )],
            [InlineKeyboardButton(
                "✅ اتمام ویرایش و بازگشت",
                callback_data=f"{CB_EDIT_DONE}_{store_id}"
            )],
            [InlineKeyboardButton(
                "🔙 بازگشت به داشبورد",
                callback_data=f"back_to_dashboard_{store_id}"
            )],
        ])

        if query:
            await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.reply_text(text=text, reply_markup=keyboard, parse_mode="Markdown")

        logger.info(f"Edit profile menu displayed for store {store_id}")

    async def handle_field_selection(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        store_id: int,
        field: str
    ) -> None:
        """
        Start editing a specific field by setting the user's state and prompting for new value.
        """
        query = update.callback_query
        chat_id = update.effective_chat.id

        # Store current editing context in state
        await self.state_manager.set_state(
            chat_id,
            f"edit_store_{field}",
            {"store_id": store_id, "field": field}
        )

        prompts = {
            FIELD_MANAGER_NAME: "👤 لطفاً نام و نام خانوادگی مدیر فروشگاه را وارد کنید:",
            FIELD_WEBSITE: "🌐 لطفاً آدرس وب‌سایت فروشگاه را وارد کنید (مثال: https://example.com):",
            FIELD_EMAIL: "✉️ لطفاً ایمیل فروشگاه را وارد کنید (اختیاری - برای رد کردن /skip را بزنید):",
            FIELD_CATEGORY: "🏷 لطفاً دسته‌بندی کسب‌وکار خود را انتخاب کنید:"
        }

        if field == FIELD_CATEGORY:
            # Show category selection keyboard
            buttons = []
            for cat in BUSINESS_CATEGORIES:
                buttons.append([InlineKeyboardButton(
                    cat,
                    callback_data=f"set_category_{store_id}_{cat}"
                )])
            buttons.append([InlineKeyboardButton("🔙 انصراف", callback_data=f"{CB_EDIT_DONE}_{store_id}")])
            keyboard = InlineKeyboardMarkup(buttons)

            await query.edit_message_text(
                text=prompts[field],
                reply_markup=keyboard
            )
        else:
            await query.edit_message_text(
                text=prompts[field] + "\n\nبرای لغو /cancel را بفرستید."
            )
            # The actual input will be caught by message handler in router

        logger.info(f"User {user_id} started editing field '{field}' for store {store_id}")

    async def process_text_input(
        self,
        chat_id: int,
        text: str,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Process text input when user is in edit state.
        Returns a reply dict if successful, or None to keep state.
        """
        state = await self.state_manager.get_state(chat_id)
        if not state or not state["state"].startswith("edit_store_"):
            return None

        field = state["state"].replace("edit_store_", "")
        store_id = state["data"]["store_id"]

        # Handle cancel command
        if text.strip().lower() in ["/cancel", "انصراف"]:
            await self.state_manager.clear_state(chat_id)
            # We'll return to edit menu via router callback
            return {
                "text": "❌ عملیات لغو شد.",
                "reply_markup": None  # Router will handle navigation
            }

        # Validate and update
        new_value = text.strip()
        if field == FIELD_EMAIL and new_value.lower() == "/skip":
            new_value = None  # Optional field

        # Basic validation
        if field == FIELD_WEBSITE and new_value:
            if not (new_value.startswith("http://") or new_value.startswith("https://")):
                return {"text": "⚠️ آدرس سایت باید با http:// یا https:// شروع شود. دوباره تلاش کنید:"}

        # Update database
        try:
            query = f"UPDATE stores SET {field} = ? WHERE id = ?"
            await self.db.execute(query, (new_value, store_id))
            await self.db.commit()
        except Exception as e:
            logger.error(f"Failed to update field {field} for store {store_id}: {e}")
            return {"text": "❌ خطا در ذخیره‌سازی. لطفاً دوباره تلاش کنید."}

        await self.state_manager.clear_state(chat_id)
        return {
            "text": f"✅ {self._field_label(field)} با موفقیت به‌روزرسانی شد.",
        }

    async def handle_category_selection(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        store_id: int,
        category: str
    ) -> None:
        """Handle category selection from inline keyboard."""
        query = update.callback_query

        try:
            await self.db.execute(
                "UPDATE stores SET business_category = ? WHERE id = ?",
                (category, store_id)
            )
            await self.db.commit()
            await query.answer("✅ دسته‌بندی با موفقیت ثبت شد.")
        except Exception as e:
            logger.error(f"Failed to update category for store {store_id}: {e}")
            await query.answer("❌ خطا در ذخیره‌سازی.", show_alert=True)

        # Return to edit menu
        await self.show_edit_menu(update, context, user_id, store_id)

    def _field_label(self, field: str) -> str:
        """Return Persian label for field."""
        return {
            FIELD_MANAGER_NAME: "نام مدیر",
            FIELD_WEBSITE: "آدرس سایت",
            FIELD_CATEGORY: "دسته‌بندی",
            FIELD_EMAIL: "ایمیل"
        }.get(field, field)

    async def finish_editing(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        store_id: int
    ) -> None:
        """Finish editing and return to dashboard."""
        # The router will handle navigation back to dashboard
        from src.handlers.menu.stores.dashboard.store_dashboard import StoreDashboardHandler
        dashboard = StoreDashboardHandler(self.db)
        await dashboard.show_dashboard(update, context, user_id, store_id)
