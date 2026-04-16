"""
Woocommerce Bot

helpers.py
General helper functions

@package    Woocommerce Bot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

from typing import Any
from src.bale.api import BaleBot

async def ask_question(bot: BaleBot, chat_id: int, question: str) -> str:
    """
    یک پیام پرسشی می‌فرستد و منتظر پاسخ کاربر می‌ماند.

    در پروژه واقعی باید از `bot.wait_for('message', ...)` یا متدهای مشابه
    استفاده شود. در این مثال یک placeholder ساده با استفاده از
    `input()` (در محیط pyodide) استفاده می‌کنیم تا بتوانیم تست کنیم.
    """
    # ارسال پیام
    await bot.send_message(chat_id, question)
    # در محیط واقعی: await bot.wait_for('message', ...)
    # در این محیط می‌توانیم به‌سادگی از input() استفاده کنیم
    # تا بتوانید در کنسول تست کنید.
    answer = input(f"User {chat_id} answer to \"{question}\": ")
    return answer