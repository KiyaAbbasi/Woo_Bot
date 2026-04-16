"""
Woocommerce Bot

parser.py
Extract WooCommerce keys from QR text

@package    Woocommerce Bot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

class WooKeyParser:

    @staticmethod
    def parse(data: str):

        ck = None
        cs = None

        parts = data.replace("\n", " ").split()

        for p in parts:

            if p.startswith("ck_"):
                ck = p

            if p.startswith("cs_"):
                cs = p

        return ck, cs