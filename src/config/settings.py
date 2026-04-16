"""
Woocommerce Bot

settings.py
Global bot settings and configuration

@package    Woocommerce Bot
@subpackage Config
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

from dataclasses import dataclass
import os
from dotenv import load_dotenv

# --- Base Directory ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, ".env")

# --- Load environment variables ---
if os.path.exists(ENV_PATH):
    load_dotenv(ENV_PATH)
    print("Loaded environment variables from .env file.")
else:
    print(".env file not found. Using system environment variables.")

# --- Bale Bot Configuration ---
BALE_BOT_TOKEN = os.getenv("BALE_BOT_TOKEN", "")
if not BALE_BOT_TOKEN:
    print("WARNING: BALE_BOT_TOKEN is not set. The bot will not be able to connect to Bale.")

# --- SMS Configuration ---
SMS_PANEL = os.getenv("SMS_PANEL", "melipayamak")  # melipayamak | kavenegar | asanpardakht
SMS_USERNAME = os.getenv("SMS_USERNAME", "")
SMS_PASSWORD = os.getenv("SMS_PASSWORD", "")
SMS_API_KEY = os.getenv("SMS_API_KEY", "")       # برای کاوه‌نگار
SMS_SENDER = os.getenv("SMS_SENDER", "")
SMS_TEMPLATE = os.getenv("SMS_TEMPLATE", "کد تأیید شما: {code}")

if not SMS_USERNAME and not SMS_API_KEY:
    print("WARNING: SMS credentials are not set. OTP will be printed to console.")

# --- Logging ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# --- Database Configuration ---
DB_FOLDER = os.path.join(BASE_DIR, "data")
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)
    print(f"Created data directory: {DB_FOLDER}")

DB_PATH = os.path.join(DB_FOLDER, "app.db")

# --- WooCommerce Default Settings ---
WC_TIMEOUT = 15
WC_API_VERSION = "wc/v3"

# --- Other Settings ---
DEFAULT_PAGE_SIZE = 50

# --- Settings Data Class ---
@dataclass
class Settings:
    BALE_BOT_TOKEN: str
    SMS_PANEL: str
    SMS_USERNAME: str
    SMS_PASSWORD: str
    SMS_API_KEY: str
    SMS_SENDER: str
    SMS_TEMPLATE: str
    LOG_LEVEL: str
    DB_PATH: str
    WC_TIMEOUT: int
    WC_API_VERSION: str
    DEFAULT_PAGE_SIZE: int

# --- Initialize Settings Object ---
settings = Settings(
    BALE_BOT_TOKEN=BALE_BOT_TOKEN,
    SMS_PANEL=SMS_PANEL,
    SMS_USERNAME=SMS_USERNAME,
    SMS_PASSWORD=SMS_PASSWORD,
    SMS_API_KEY=SMS_API_KEY,
    SMS_SENDER=SMS_SENDER,
    SMS_TEMPLATE=SMS_TEMPLATE,
    LOG_LEVEL=LOG_LEVEL,
    DB_PATH=DB_PATH,
    WC_TIMEOUT=WC_TIMEOUT,
    WC_API_VERSION=WC_API_VERSION,
    DEFAULT_PAGE_SIZE=DEFAULT_PAGE_SIZE,
)
