"""
Woocommerce Bot

user_manager.py
User authentication and registration logic.

@package    Woocommerce Bot
@subpackage Auth
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

from sqlalchemy.orm import Session
from src.database.models import User, StoreSettings
from src.logger.log_handler import get_logger

logger = get_logger(__name__)


class UserManager:
    def __init__(self, db_session: Session):
        self.db = db_session

    def login(self, phone_number: str) -> User:
        """ورود کاربر با شماره تلفن"""
        user = self.db.query(User).filter(User.phone_number == phone_number).first()
        if not user:
            raise ValueError("کاربری با این شماره یافت نشد")
        if not user.is_active:
            raise ValueError("حساب کاربری غیرفعال است")
        logger.info(f"User {user.id} logged in successfully")
        return user

    def get_or_create_user(self, phone: str, chat_id: str) -> User:
        """
        بررسی می‌کنه کاربر با این شماره وجود داره یا نه.
        اگر وجود داشت، فلگ is_new رو False می‌ذاره.
        اگر وجود نداشت، کاربر جدید ثبت می‌کنه و فلگ is_new رو True می‌ذاره.
        """
        user = self.db.query(User).filter(User.phone_number == phone).first()
        if user:
            # کاربر قبلاً ثبت شده
            user.is_new = False
            # اطمینان از اینکه bale_user_id هم به‌روز شده
            if user.bale_user_id != chat_id:
                user.bale_user_id = chat_id
                self.db.commit()
            return user
        else:
            # کاربر جدید
            new_user = User(
                bale_user_id=chat_id,
                phone_number=phone,
                is_verified=True,
                is_active=True,
            )
            new_user.is_new = True
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            logger.info(f"New user created with phone: {phone}, bale_id: {chat_id}")
            return new_user

    def register(self, phone: str, full_name: str = None, business_name: str = None, 
                website: str = None, email: str = None, category: str = None, 
                bale_user_id: str = None) -> User:
        """ثبت‌نام کامل کاربر جدید با اطلاعات فروشگاه"""
        
        # بررسی وجود کاربر با شماره تلفن
        existing = self.db.query(User).filter(User.phone_number == phone).first()
        if existing:
            raise ValueError("این شماره تلفن قبلاً ثبت شده است")
        
        # ایجاد کاربر
        user = User(
            bale_user_id=bale_user_id or f"temp_{phone}",
            phone_number=phone,
            full_name=full_name,
            is_verified=True,
            is_active=True
        )
        self.db.add(user)
        self.db.flush()  # برای گرفتن user.id
        
        # ایجاد تنظیمات فروشگاه
        store = StoreSettings(
            user_id=user.id,
            store_url=website or "",
            consumer_key="",  # بعداً توسط کاربر پر می‌شه
            consumer_secret="",
            business_name=business_name,
            website=website,
            email=email,
            category=category,
            is_connected=False
        )
        self.db.add(store)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"New user registered with store: {user.id}")
        return user


    def get_user_by_bale_id(self, bale_user_id: str) -> User:
        """دریافت کاربر با bale_user_id"""
        return self.db.query(User).filter(User.bale_user_id == bale_user_id).first()

    def update_user(self, user_id: int, **kwargs) -> User:
        """به‌روزرسانی اطلاعات کاربر"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("کاربر یافت نشد")
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        logger.info(f"User {user_id} updated")
        return user

    def create_store(self, user_id: int, business_name: str = None, 
                    website: str = None, email: str = None, 
                    category: str = None) -> 'StoreSettings':
        """ساخت تنظیمات فروشگاه برای کاربر"""
        
        # چک کنیم فروشگاه قبلاً ساخته نشده باشه
        existing = self.db.query(StoreSettings).filter(
            StoreSettings.user_id == user_id
        ).first()
        if existing:
            raise ValueError("فروشگاه قبلاً برای این کاربر ساخته شده")
        
        store = StoreSettings(
            user_id=user_id,
            store_url=website or "",
            consumer_key="",  # بعداً در منوی ووکامرس پر می‌شه
            consumer_secret="",  # بعداً در منوی ووکامرس پر می‌شه
            business_name=business_name,
            website=website,
            email=email,
            category=category,
            is_connected=False
        )
        self.db.add(store)
        self.db.commit()
        self.db.refresh(store)
        logger.info(f"Store created for user {user_id}")
        return store

    def deactivate_user(self, user_id: int):
        """غیرفعال کردن کاربر"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = False
            self.db.commit()
            logger.info(f"User {user_id} deactivated")
