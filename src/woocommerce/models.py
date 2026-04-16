"""
Woocommerce Bot

models.py
Data models for Woocommerce products

@package    Woocommerce Bot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

from typing import List, Optional
from pydantic import BaseModel


class WooCategory(BaseModel):
    id:   int
    name: str
    slug: str


class WooImage(BaseModel):
    id:  int
    src: str
    alt: Optional[str] = ""


class WooAttribute(BaseModel):
    id:      int
    name:    str
    options: List[str] = []


class WooVariation(BaseModel):
    id:           int
    sku:          Optional[str] = ""
    price:        Optional[str] = ""
    sale_price:   Optional[str] = ""
    stock_status: Optional[str] = "instock"    # 'instock' | 'outofstock'
    stock_quantity: Optional[int] = None
    image:        Optional[WooImage] = None
    attributes:   List[WooAttribute] = []


class WooProduct(BaseModel):
    id:             int
    name:           str
    slug:           str
    permalink:      Optional[str] = ""
    type:           str = "simple"             # 'simple' | 'variable'
    status:         str = "publish"
    description:    Optional[str] = ""
    short_description: Optional[str] = ""
    sku:            Optional[str] = ""
    price:          Optional[str] = ""
    regular_price:  Optional[str] = ""
    sale_price:     Optional[str] = ""
    stock_status:   Optional[str] = "instock"
    stock_quantity: Optional[int] = None
    categories:     List[WooCategory] = []
    images:         List[WooImage] = []
    attributes:     List[WooAttribute] = []
    variations:     List[int] = []             # لیست ID متغیرها (برای type=variable)