"""
WooCommerce to Bale Bot (WooBot)
store_dashboard.py

Displays the store dashboard with status overview and main action buttons.

@package    WooBot
@subpackage Handlers/Menu/Stores/Dashboard
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
from src.logger.log_handler import logger


# Callback data constants for dashboard buttons
CB_STORE_EDIT = "store_edit"
CB_STORE_WOOCOMMERCE = "store_woocommerce"
CB_STORE_CHANNELS = "store_channels"
CB_STORE_SCHEDULING = "store_scheduling"
CB_STORE_MANUAL_POST = "store_manual_post"
CB_BACK_TO_STORES = "back_to_stores"


class StoreDashboardHandler:
    """
    Handles displaying the store dashboard and routing to sub-menus.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the handler with database access.

        Args:
            db_manager: Instance of DatabaseManager for DB operations.
        """
        self.db = db_manager

    async def get_store_summary(self, store_id: int) -> Dict[str, Any]:
        """
        Fetch store details and connection statuses for dashboard display.

        Args:
            store_id: The store ID.

        Returns:
            Dictionary containing store info and status flags.
        """
        # TODO: Replace with actual DB queries
        # For MVP, we'll build a summary from multiple tables
        try:
            # 1. Basic store info
            store_query = """
                SELECT name, website, business_category, email, manager_name,
                       woo_consumer_key, woo_consumer_secret, woo_connected_at
                FROM stores WHERE id = ?
            """
            store = await self.db.fetch_one(store_query, (store_id,))

            if not store:
                logger.error(f"Store {store_id} not found")
                return {}

            # 2. Check if any Bale channel is connected
            channel_query = """
                SELECT COUNT(*) as count FROM channels
                WHERE store_id = ? AND platform = 'bale' AND is_active = 1
            """
            channel_count = await self.db.fetch_val(channel_query, (store_id,))

            # 3. Check scheduling settings (simplified: exists in store_settings table)
            schedule_query = """
                SELECT post_interval_minutes, daily_limit, active_hours_start, active_hours_end
                FROM store_scheduling WHERE store_id = ?
            """
            schedule = await self.db.fetch_one(schedule_query, (store_id,))

            # Build summary
            summary = {
                "id": store_id,
                "name": store.get("name", "بدون نام"),
                "website": store.get("website", ""),
                "category": store.get("business_category", "نامشخص"),
                "email": store.get("email"),
                "manager": store.get("manager_name"),
                # Statuses
                "woocommerce_connected": bool(store.get("woo_consumer_key") and store.get("woo_consumer_secret")),
                "woocommerce_last_sync": store.get("woo_connected_at"),
                "has_channel": (channel_count or 0) > 0,
                "scheduling_configured": schedule is not None,
            }
            return summary

        except Exception as e:
            logger.error(f"Failed to get store summary for store {store_id}: {e}")
            return {}

    async def show_dashboard(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        store_id: int
    ) -> None:
        """
        Display the store dashboard with current status and action buttons.

        Args:
            update: The update object from Telegram/Bale.
            context: The callback context.
            user_id: The internal user ID (for logging/permission checks).
            store_id: The ID of the store to display.
        """
        query = update.callback_query
        message = update.effective_message

        # Get store summary
        summary = await self.get_store_summary(store_id)
        if not summary:
            text = "❌ خطا در بارگذاری اطلاعات فروشگاه. لطفاً دوباره تلاش کنید."
            if query:
                await query.edit_message_text(text=text)
            else:
                await message.reply_text(text=text)
            return

        # Build status text with emojis
        woo_status = "✅ متصل" if summary["woocommerce_connected"] else "❌ قطع"
        channel_status = "✅ فعال" if summary["has_channel"] else "❌ بدون کانال"
        schedule_status = "✅ تنظیم شده" if summary["scheduling_configured"] else "⚠️ ناقص"

        text = (
            f"🏬 **داشبورد فروشگاه**\n\n"
            f"📌 **{summary['name']}**\n"
            f"🌐 {summary['website']}\n"
            f"🏷 {summary['category']}\n\n"
            f"🔌 **وضعیت اتصال‌ها:**\n"
            f"• ووکامرس: {woo_status}\n"
            f"• کانال بله: {channel_status}\n"
            f"• تنظیمات ارسال: {schedule_status}\n\n"
            f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
        )

        # Build action buttons
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ ویرایش مشخصات فروشگاه", callback_data=f"{CB_STORE_EDIT}_{store_id}")],
            [InlineKeyboardButton("🔌 مدیریت اتصال ووکامرس", callback_data=f"{CB_STORE_WOOCOMMERCE}_{store_id}")],
            [InlineKeyboardButton("📣 مدیریت کانال‌های بله", callback_data=f"{CB_STORE_CHANNELS}_{store_id}")],
            [InlineKeyboardButton("⚙️ تنظیمات ارسال خودکار", callback_data=f"{CB_STORE_SCHEDULING}_{store_id}")],
            [InlineKeyboardButton("📋 ارسال دستی محصول", callback_data=f"{CB_STORE_MANUAL_POST}_{store_id}")],
            [InlineKeyboardButton("🔙 بازگشت به فروشگاه‌های من", callback_data=CB_BACK_TO_STORES)],
        ])

        if query:
            try:
                await query.edit_message_text(
                    text=text,
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to edit store dashboard message: {e}")
                await message.reply_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.reply_text(text=text, reply_markup=keyboard, parse_mode="Markdown")

        logger.info(f"Store dashboard displayed for user {user_id}, store {store_id}")
