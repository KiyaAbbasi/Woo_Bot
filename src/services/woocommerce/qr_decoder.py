"""
Woocommerce Bot

qr_decoder.py
Decode WooCommerce REST API QRCode

@package    Woocommerce Bot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

import cv2
from pyzbar.pyzbar import decode


class WooQRCodeDecoder:

    @staticmethod
    def decode(image_path: str) -> str | None:

        img = cv2.imread(image_path)
        decoded = decode(img)

        if not decoded:
            return None

        return decoded[0].data.decode("utf-8")
