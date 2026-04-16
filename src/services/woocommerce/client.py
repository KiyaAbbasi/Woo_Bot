"""
Woocommerce Bot

client.py
WooCommerce REST API client

@package    Woocommerce Bot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""

import requests


class WooClient:

    def __init__(self, url, ck, cs):

        self.url = url.rstrip("/")
        self.ck = ck
        self.cs = cs

    def test_connection(self):

        endpoint = f"{self.url}/wp-json/wc/v3/products"

        r = requests.get(
            endpoint,
            auth=(self.ck, self.cs),
            timeout=10
        )

        return r.status_code == 200