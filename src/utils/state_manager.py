"""
Woocommerce Bot

state_manager.py
Simple in-memory state manager for handling user flows

@package    Woocommerce Bot
@subpackage Core
@author     [Kiya Holding] <KiyaHolding@gmail.com>
@copyright  2026 [Kiya Holding / WooBot]
@license    Proprietary
@version    1.0.0
@link       [KiyaHolding.com]
"""


class StateManager:
    """
    Manage temporary user states for multi-step flows.
    """

    def __init__(self):
        self._states = {}

    def set(self, chat_id: int, key: str, value):
        if chat_id not in self._states:
            self._states[chat_id] = {}
        self._states[chat_id][key] = value

    def get(self, chat_id: int, key: str, default=None):
        return self._states.get(chat_id, {}).get(key, default)

    def get_all(self, chat_id: int):
        return self._states.get(chat_id, {})

    def clear(self, chat_id: int):
        if chat_id in self._states:
            del self._states[chat_id]

    def exists(self, chat_id: int) -> bool:
        return chat_id in self._states
