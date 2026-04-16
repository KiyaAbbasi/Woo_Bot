"""
Woocommerce Bot

models.py
Database models for User, StoreSettings, ErrorLog, etc.

@package    Woocommerce Bot
@subpackage Database
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, JSON
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True)
    bale_user_id    = Column(String(50), unique=True, index=True, nullable=False)
    phone_number    = Column(String(20), unique=True, nullable=True)
    full_name       = Column(String(100), nullable=True)
    is_active       = Column(Boolean, default=True)
    is_verified     = Column(Boolean, default=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    store_settings      = relationship("StoreSettings",     back_populates="user", uselist=False, cascade="all, delete-orphan")
    scheduler_settings  = relationship("SchedulerSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    content_settings    = relationship("ContentSettings",   back_populates="user", uselist=False, cascade="all, delete-orphan")
    channels            = relationship("BaleChannel",       back_populates="user", cascade="all, delete-orphan")
    send_history        = relationship("ProductSendHistory",back_populates="user", cascade="all, delete-orphan")
    error_logs          = relationship("ErrorLog",          back_populates="user", cascade="all, delete-orphan")


class StoreSettings(Base):
    __tablename__ = "store_settings"

    id              = Column(Integer, primary_key=True)
    user_id         = Column(Integer, ForeignKey("users.id"), unique=True, index=True)

    manager_chat_id = Column(String(50), nullable=True)

    store_url       = Column(String(500), nullable=True)
    consumer_key    = Column(String(200), nullable=True)
    consumer_secret = Column(String(200), nullable=True)
    
    is_connected    = Column(Boolean, default=False)
    last_sync_at    = Column(DateTime(timezone=True), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    
    # فیلدهای جدید برای ثبت‌نام اولیه (SaaS)
    business_name   = Column(String(255), nullable=True)
    website         = Column(String(500), nullable=True)
    email           = Column(String(255), nullable=True)
    category        = Column(String(100), nullable=True)

    user = relationship("User", back_populates="store_settings")


class SchedulerSettings(Base):
    __tablename__ = "scheduler_settings"

    id              = Column(Integer, primary_key=True)
    user_id         = Column(Integer, ForeignKey("users.id"), unique=True, index=True)

    # بازه sync محصولات از ووکامرس: '6h', '12h', '24h', '3d'
    sync_interval   = Column(String(10), default="24h")

    # محدودیت ارسال روزانه
    daily_limit     = Column(Integer, default=20)

    # بازه مجاز ارسال (HH:MM)
    send_start_time = Column(String(5), nullable=True)   # e.g. "09:00"
    send_end_time   = Column(String(5), nullable=True)   # e.g. "21:00"

    # ساعات خاموشی (HH:MM)
    quiet_hours_start = Column(String(5), nullable=True)
    quiet_hours_end   = Column(String(5), nullable=True)

    # ترتیب ارسال: 'sequential' | 'random'
    send_order      = Column(String(15), default="sequential")

    # حالت ارسال: 'automatic' | 'manual' | 'semi_automatic'
    send_mode       = Column(String(20), default="manual")

    is_active       = Column(Boolean, default=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="scheduler_settings")


class ContentSettings(Base):
    __tablename__ = "content_settings"

    id              = Column(Integer, primary_key=True)
    user_id         = Column(Integer, ForeignKey("users.id"), unique=True, index=True)

    # فیلدهای نمایشی
    show_title          = Column(Boolean, default=True)
    show_price          = Column(Boolean, default=True)
    show_stock          = Column(Boolean, default=True)
    show_description    = Column(Boolean, default=True)
    show_image          = Column(Boolean, default=True)
    show_sku            = Column(Boolean, default=False)
    show_link           = Column(Boolean, default=True)
    show_categories     = Column(Boolean, default=False)
    show_attributes     = Column(Boolean, default=False)

    # قالب قیمت: مثلاً "تومان" یا "ریال"
    price_format        = Column(String(20), default="تومان")

    # امضای انتهای پست
    footer_text         = Column(String(500), nullable=True)

    # حالت محصول متغیر: 'per_variation' | 'parent_with_list' | 'single_selected'
    variable_product_mode   = Column(String(30), default="parent_with_list")

    # فیلدهای نمایشی برای variation ها (JSON list)
    # e.g. ["price", "image", "attributes", "stock", "sku"]
    variable_product_fields = Column(JSON, default=["price", "attributes", "stock"])

    # فیلتر دسته‌بندی (JSON list of category IDs)
    filter_categories       = Column(JSON, default=[])

    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="content_settings")


class BaleChannel(Base):
    __tablename__ = "bale_channels"

    id              = Column(Integer, primary_key=True)
    user_id         = Column(Integer, ForeignKey("users.id"), index=True)
    channel_id      = Column(String(100), nullable=False)   # chat_id از بله
    username        = Column(String(100), nullable=True)    # @username (اختیاری)
    title           = Column(String(200), nullable=True)
    is_default      = Column(Boolean, default=False)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="channels")


class ProductSendHistory(Base):
    __tablename__ = "product_send_history"

    id          = Column(Integer, primary_key=True)
    user_id     = Column(Integer, ForeignKey("users.id"), index=True)
    product_id  = Column(Integer, index=True)               # WooCommerce Product ID
    variation_id= Column(Integer, nullable=True)            # در صورت variable product
    channel_id  = Column(String(100), nullable=True)        # Bale channel_id
    sent_at     = Column(DateTime(timezone=True), server_default=func.now())
    # 'sent' | 'failed' | 'skipped'
    status      = Column(String(20), default="sent")
    error_msg   = Column(Text, nullable=True)

    user = relationship("User", back_populates="send_history")


class ErrorLog(Base):
    __tablename__ = "error_logs"

    id          = Column(Integer, primary_key=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    module      = Column(String(100), nullable=True)        # مثلاً 'scheduler', 'woocommerce'
    message     = Column(Text, nullable=False)
    traceback   = Column(Text, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="error_logs")