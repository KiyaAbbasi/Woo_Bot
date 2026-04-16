"""
WooCommerce to Bale Bot (WooBot)
main_menu_handler.py

Handler for displaying the main menu of the bot with inline buttons.

@package    WooBot
@subpackage Handlers/Menu
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

# Import constants for callback data (to be defined in a central place)
# We will define them here temporarily for clarity
CB_STORES = "main_stores"
CB_REPORTS = "main_reports"
CB_PROFILE = "main_profile"
CB_HELP = "main_help"

# Import User Manager to get user info (for greeting)
from src.auth.user_manager import UserManager
from src.database.db_manager import DatabaseManager
from src.logger.log_handler import logger


class MainMenuHandler:
    """
    Handles the display of the main menu for authenticated users.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the handler with database access.

        Args:
            db_manager: Instance of DatabaseManager for DB operations.
        """
        self.db = db_manager
        self.user_manager = UserManager(db_manager)

    async def show_main_menu(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        user_id: int
    ) -> None:
        """
        Display the main menu inline keyboard with user greeting.

        Args:
            update: The update object from Telegram/Bale.
            context: The callback context.
            user_id: The internal user ID of the logged-in user.
        """
        query = update.callback_query
        message = update.effective_message

        # Get user details for personalized greeting
        user_info = await self.user_manager.get_user_by_id(user_id)
        first_name = user_info.get('first_name', 'کاربر') if user_info else 'کاربر'

        # Main menu text
        text = (
            f"👋 سلام {first_name} عزیز!\n"
            f"به ربات WooBot خوش آمدید.\n\n"
            f"لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
        )

        # Build inline keyboard according to new simplified structure
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏬 فروشگاه‌های من", callback_data=CB_STORES)],
            [InlineKeyboardButton("📊 گزارش‌ها", callback_data=CB_REPORTS)],
            [InlineKeyboardButton("👤 پروفایل", callback_data=CB_PROFILE)],
            [InlineKeyboardButton("❓ راهنما", callback_data=CB_HELP)],
        ])

        # Edit the message if it's a callback query, otherwise send new
        if query:
            try:
                await query.edit_message_text(
                    text=text,
                    reply_markup=keyboard
                )
            except Exception as e:
                logger.error(f"Failed to edit main menu message: {e}")
                # Fallback to sending a new message
                await message.reply_text(text=text, reply_markup=keyboard)
        else:
            await message.reply_text(text=text, reply_markup=keyboard)

        logger.info(f"Main menu displayed for user_id: {user_id}")
