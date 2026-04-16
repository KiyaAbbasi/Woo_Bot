"""
Woocommerce Bot

models.py
Minimal data‑models needed for Bale keyboards.

@package    Woocommerce Bot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

from typing import Optional
from pydantic import BaseModel


class BaleUser(BaseModel):
    id:         int
    first_name: Optional[str] = ""
    last_name:  Optional[str] = ""
    username:   Optional[str] = None
    is_bot:     bool = False


class BaleMessage(BaseModel):
    message_id: int
    chat_id:    int
    text:       Optional[str] = None
    date:       Optional[int] = None
    from_user:  Optional[BaleUser] = None


class BaleChannel(BaseModel):
    """مدل Pydantic برای parse اطلاعات کانال از API بله"""
    id:       int           # chat_id کانال
    title:    Optional[str] = ""
    username: Optional[str] = None   # بدون @
    type:     str = "channel"
