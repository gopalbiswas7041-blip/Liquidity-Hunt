"""
===========================================================
Liquidity Hunter AI
Official CoinDCX Socket.IO Engine
Version : V17.3
Part 1 - Foundation
===========================================================
"""

import logging
import socketio
import threading
import time

from typing import Callable, Optional


class CoinDCXWebSocket:
    """
    Liquidity Hunter AI

    Official CoinDCX Socket.IO Client
    Production Foundation
    """

    # --------------------------------------------------
    # Constructor
    # --------------------------------------------------

    def __init__(self):

        # Logger
        self.logger = logging.getLogger("CoinDCXWebSocket")
        self.logger.setLevel(logging.INFO)

        # Socket.IO Client
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=0,
            reconnection_delay=5,
            logger=False,
            engineio_logger=False,
        )

        # Connection State
        self.connected = False
        self.running = False

        # Market
        self.symbol = None

        # Statistics
        self.messages_received = 0
        self.last_message_time = None

        # Callbacks
        self.on_tick: Optional[Callable] = None
        self.on_connected: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None

        # Thread
        self.thread = None

        self.logger.info("=" * 60)
        self.logger.info("Liquidity Hunter AI")
        self.logger.info("CoinDCX Socket.IO Engine Initialized")
        self.logger.info("=" * 60)

    # --------------------------------------------------
    # Callback Registration
    # --------------------------------------------------

    def set_tick_callback(self, callback: Callable):
        self.on_tick = callback

    def set_connected_callback(self, callback: Callable):
        self.on_connected = callback

    def set_disconnected_callback(self, callback: Callable):
        self.on_disconnected = callback

    # --------------------------------------------------
    # Status
    # --------------------------------------------------

    def is_connected(self):
        return self.connected

    def is_running(self):
        return self.running

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def get_statistics(self):

        return {
            "connected": self.connected,
            "running": self.running,
            "symbol": self.symbol,
            "messages_received": self.messages_received,
            "last_message_time": self.last_message_time,
        }

    # --------------------------------------------------
    # Object Representation
    # --------------------------------------------------

    def __repr__(self):

        return (
            f"<CoinDCXWebSocket "
            f"connected={self.connected}, "
            f"running={self.running}, "
            f"symbol={self.symbol}>"
        )