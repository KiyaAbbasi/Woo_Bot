"""
Woocommerce Bot

woocommerce_menu_handler.py
Handler for WooCommerce connection flow (store_url, consumer_key, consumer_secret)

@package    Woocommerce Bot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

import requests
from urllib.parse import urlparse

from src.database.db_manager import SessionLocal
from src.database.models import User, StoreSettings
from src.logger.log_handler import get_logger

try:
    from bale.types import ReplyKeyboardMarkup, KeyboardButton  # type: ignore
except ImportError:
    class KeyboardButton:
        def __init__(self, text: str): self.text = text
        def to_dict(self): return {"text": self.text}

    class ReplyKeyboardMarkup:
        def __init__(self, keyboard, resize_keyboard=True):
            self.keyboard = keyboard
            self.resize_keyboard = resize_keyboard

        def to_dict(self):
            return {
                "keyboard": [[b.to_dict() for b in row] for row in self.keyboard],
                "resize_keyboard": self.resize_keyboard
            }


logger = get_logger(__name__)

BTN_BACK_MAIN = "⬅️ منوی اصلی"

_STATE_STEP = "woo_step"
_STATE_URL  = "woo_url"
_STATE_KEY  = "woo_key"


class WoocommerceMenuHandler:

    def __init__(self, user_manager, bot):
        self._states = {}
        self._um = user_manager
        self._bot = bot

    async def start_flow(self, chat_id: int) -> dict:
        self._states[chat_id] = {_STATE_STEP: "url"}

        return self._ask(
            chat_id,
            "🛒 اتصال به ووکامرس\n\n"
            "مرحله ۱/۳ — آدرس فروشگاه ووکامرس خود را وارد کنید:\n"
            "مثال:\n"
            "https://myshop.com"
        )

    async def handle_message(self, chat_id: int, text: str) -> dict:

        if text == BTN_BACK_MAIN:
            self._clear(chat_id)
            return None

        step = self._states.get(chat_id, {}).get(_STATE_STEP)

        if step == "url":
            return await self._handle_url(chat_id, text)

        elif step == "key":
            return await self._handle_key(chat_id, text)

        elif step == "secret":
            return await self._handle_secret(chat_id, text)

        return self._ask(chat_id, "❌ خطا رخ داد. لطفاً دوباره تلاش کنید.")

    async def _handle_url(self, chat_id: int, text: str) -> dict:

        url = text.strip().rstrip("/")

        if not self._is_valid_url(url):
            return self._ask(
                chat_id,
                "⚠️ آدرس معتبر نیست.\n"
                "لطفاً آدرس را با http یا https وارد کنید.\n\n"
                "مثال:\n"
                "https://myshop.com"
            )

        self._states[chat_id][_STATE_URL] = url
        self._states[chat_id][_STATE_STEP] = "key"

        return self._ask(
            chat_id,
            "مرحله ۲/۳ — Consumer Key را وارد کنید:\n\n"
            "از مسیر زیر در ووکامرس دریافت کنید:\n"
            "WooCommerce → Settings → Advanced → REST API"
        )

    async def _handle_key(self, chat_id: int, text: str) -> dict:

        key = text.strip()

        if not key.startswith("ck_"):
            return self._ask(
                chat_id,
                "⚠️ Consumer Key معتبر نیست.\n"
                "کلید باید با ck_ شروع شود."
            )

        self._states[chat_id][_STATE_KEY] = key
        self._states[chat_id][_STATE_STEP] = "secret"

        return self._ask(
            chat_id,
            "مرحله ۳/۳ — Consumer Secret را وارد کنید:"
        )

    async def _handle_secret(self, chat_id: int, text: str) -> dict:

        secret = text.strip()

        if not secret.startswith("cs_"):
            return self._ask(
                chat_id,
                "⚠️ Consumer Secret معتبر نیست.\n"
                "کلید باید با cs_ شروع شود."
            )

        state = self._states.get(chat_id, {})

        url = state.get(_STATE_URL, "")
        key = state.get(_STATE_KEY, "")

        if not await self._test_connection(url, key, secret):
            logger.warning(f"WooCommerce connection failed for chat_id={chat_id}")

            return self._ask(
                chat_id,
                "❌ اتصال به ووکامرس برقرار نشد.\n\n"
                "موارد زیر را بررسی کنید:\n"
                "• آدرس سایت درست باشد\n"
                "• Consumer Key صحیح باشد\n"
                "• Consumer Secret صحیح باشد\n"
                "• REST API در ووکامرس فعال باشد"
            )

        try:

            with SessionLocal() as db:

                user = db.query(User).filter(
                    User.bale_user_id == str(chat_id)
                ).first()

                store = db.query(StoreSettings).filter(
                    StoreSettings.user_id == user.id
                ).first() if user else None

                if not store:
                    self._clear(chat_id)
                    return self._ask(chat_id, "❌ فروشگاهی یافت نشد.")

                store.store_url = url
                store.consumer_key = key
                store.consumer_secret = secret
                store.is_connected = True

                db.commit()

        except Exception as e:

            logger.error(f"Database error while saving WooCommerce keys: {e}")

            self._clear(chat_id)

            return self._ask(
                chat_id,
                "❌ خطا در ذخیره اطلاعات.\n"
                "لطفاً دوباره تلاش کنید."
            )

        self._clear(chat_id)

        logger.info(f"WooCommerce connected successfully for chat_id={chat_id}")

        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(BTN_BACK_MAIN)]],
            resize_keyboard=True,
        )

        return {
            "chat_id": chat_id,
            "text": "✅ اتصال به ووکامرس با موفقیت انجام شد!",
            "reply_markup": keyboard.to_dict(),
        }

    async def _test_connection(self, url: str, key: str, secret: str) -> bool:

        endpoint = f"{url}/wp-json/wc/v3/products"

        try:

            r = requests.get(
                endpoint,
                auth=(key, secret),
                timeout=10
            )

            if r.status_code == 200:
                return True

            logger.warning(
                f"WooCommerce API returned status {r.status_code}"
            )

            return False

        except requests.RequestException as e:

            logger.error(f"WooCommerce connection error: {e}")

            return False

    def _is_valid_url(self, url: str) -> bool:

        try:

            result = urlparse(url)

            return all([result.scheme in ("http", "https"), result.netloc])

        except Exception:

            return False

    def _clear(self, chat_id: int):

        self._states.pop(chat_id, None)

    def _ask(self, chat_id: int, text: str) -> dict:

        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(BTN_BACK_MAIN)]],
            resize_keyboard=True,
        )

        return {
            "chat_id": chat_id,
            "text": text,
            "reply_markup": keyboard.to_dict()
        }

    def is_in_flow(self, chat_id: int) -> bool:
        return chat_id in self._states
