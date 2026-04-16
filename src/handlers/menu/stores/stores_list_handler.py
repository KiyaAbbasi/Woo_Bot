"""
WooCommerce to Bale Bot (WooBot)
stores_list_handler.py

Handles displaying the list of user's stores and routing to the selected store dashboard.

@package    WooBot
@subpackage Handlers/Menu/Stores
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

from typing import List, Dict, Any, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.database.db_manager import DatabaseManager
from src.logger.log_handler import logger


# Callback data constants (will be moved to a central file later)
CB_STORE_SELECT_PREFIX = "store_select_"
CB_ADD_STORE = "store_add"


class StoresListHandler:
    """
    Handles the display of the user's stores list and navigation to store dashboard.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the handler with database access.

        Args:
            db_manager: Instance of DatabaseManager for DB operations.
        """
        self.db = db_manager

    async def get_user_stores(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve all stores belonging to a user from the database.

        Args:
            user_id: The internal user ID.

        Returns:
            List of store dictionaries (id, name, website, etc.).
        """
        # Assuming a 'stores' table exists with columns: id, user_id, name, website
        # TODO: Replace with actual DB query using db_manager
        query = """
            SELECT id, name, website, business_category, created_at
            FROM stores
            WHERE user_id = ?
            ORDER BY created_at DESC
        """
        # For MVP, we'll simulate with a direct DB call
        # (In production, use proper async DB methods)
        try:
            # If you have async DB, use await; here we assume synchronous for simplicity
            # You should adapt this to your actual db_manager method.
            stores = await self.db.fetch_all(query, (user_id,))
            return stores if stores else []
        except Exception as e:
            logger.error(f"Failed to fetch stores for user {user_id}: {e}")
            return []

    async def show_stores_list(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int
    ) -> None:
        """
        Display the list of stores or directly open dashboard if only one store exists.

        Args:
            update: The update object from Telegram/Bale.
            context: The callback context.
            user_id: The internal user ID.
        """
        query = update.callback_query
        message = update.effective_message

        stores = await self.get_user_stores(user_id)

        # Case 1: No stores (should not happen in MVP, but we handle gracefully)
        if not stores:
            text = (
                "⚠️ شما هنوز هیچ فروشگاهی ثبت نکرده‌اید.\n"
                "لطفاً از دکمه زیر برای افزودن فروشگاه استفاده کنید."
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ افزودن فروشگاه", callback_data=CB_ADD_STORE)],
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")]
            ])
            if query:
                await query.edit_message_text(text=text, reply_markup=keyboard)
            else:
                await message.reply_text(text=text, reply_markup=keyboard)
            logger.info(f"No stores found for user {user_id}")
            return

        # Case 2: Exactly one store → redirect to its dashboard
        if len(stores) == 1:
            store = stores[0]
            logger.info(f"User {user_id} has one store (ID: {store['id']}). Redirecting to dashboard.")
            # Call the store dashboard handler directly
            # We'll import inside method to avoid circular imports
            from src.handlers.menu.stores.dashboard.store_dashboard import StoreDashboardHandler
            dashboard_handler = StoreDashboardHandler(self.db)
            await dashboard_handler.show_dashboard(update, context, user_id, store['id'])
            return

        # Case 3: Multiple stores → display list for selection
        text = "🏬 **فروشگاه‌های شما:**\n\n"
        text += "لطفاً فروشگاه مورد نظر را انتخاب کنید:"

        # Build inline keyboard with one button per store
        keyboard_buttons = []
        for store in stores:
            store_name = store.get('name', 'بدون نام')
            store_website = store.get('website', '')
            display_text = f"🏷 {store_name}"
            if store_website:
                display_text += f" ({store_website})"
            callback_data = f"{CB_STORE_SELECT_PREFIX}{store['id']}"
            keyboard_buttons.append([InlineKeyboardButton(display_text, callback_data=callback_data)])

        # Add back button
        keyboard_buttons.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="main_menu")])

        keyboard = InlineKeyboardMarkup(keyboard_buttons)

        if query:
            try:
                await query.edit_message_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Failed to edit stores list message: {e}")
                await message.reply_text(text=text, reply_markup=keyboard, parse_mode="Markdown")
        else:
            await message.reply_text(text=text, reply_markup=keyboard, parse_mode="Markdown")

        logger.info(f"Stores list displayed for user {user_id} ({len(stores)} stores)")

    async def handle_store_selection(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int,
        store_id: int
    ) -> None:
        """
        Handle callback when a user selects a store from the list.
        Redirects to the store dashboard.

        Args:
            update: The update object.
            context: The callback context.
            user_id: The internal user ID.
            store_id: The selected store ID.
        """
        logger.info(f"User {user_id} selected store {store_id}")
        from src.handlers.menu.stores.dashboard.store_dashboard import StoreDashboardHandler
        dashboard_handler = StoreDashboardHandler(self.db)
        await dashboard_handler.show_dashboard(update, context, user_id, store_id)
