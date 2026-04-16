"""
Woocommerce Bot

main.py
Application entry point — initializes components and starts polling loop

@package    Woocommerce Bot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import settings
from src.database.db_manager import init_db, SessionLocal
from src.auth.user_manager import UserManager
from src.bale.api import BaleBot
from src.handlers.router import Router
from src.logger.log_handler import setup_logging, get_logger

setup_logging(settings.LOG_LEVEL)
logger = get_logger("woobot.main")

POLL_TIMEOUT = 20


async def polling_loop(bot: BaleBot, router: Router) -> None:
    """حلقه دریافت آپدیت‌ها"""
    offset: int = 0
    logger.info("Polling loop started.")

    while True:
        try:
            response = await bot.get_updates(offset=offset, timeout=POLL_TIMEOUT)
            updates = response.get("result", [])

            for update in updates:
                offset = update["update_id"] + 1
                await router.route(update)

        except asyncio.CancelledError:
            logger.info("Polling cancelled.")
            break
        except Exception as exc:
            logger.error("Polling error: %s", exc, exc_info=True)
            await asyncio.sleep(3)


async def main() -> None:
    """نقطه ورود برنامه"""
    logger.info("WooBot starting...")

    init_db()
    logger.info("Database ready.")

    bot = BaleBot(token=settings.BALE_BOT_TOKEN)
    db_session = SessionLocal()
    user_manager = UserManager(db_session=db_session)
    router = Router(user_manager=user_manager, bot=bot)

    await bot.start()
    logger.info("BaleBot session opened.")

    try:
        await polling_loop(bot, router)
    finally:
        await bot.stop()
        db_session.close()
        logger.info("WooBot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
