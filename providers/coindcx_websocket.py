"""
Liquidity Hunter AI
CoinDCX WebSocket Engine
Production Version V1
Part 1
"""

import json
import time
import threading
import logging
from typing import Callable, Optional

import websocket


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s"
)


class CoinDCXWebSocket:
    """
    Production WebSocket Engine
    """

    def __init__(self):

        # --------------------------------------------------
        # Connection
        # --------------------------------------------------

        # Replace with official CoinDCX websocket URL
        self.ws_url = ""

        self.ws = None

        self.connected = False
        self.running = False

        # --------------------------------------------------
        # Thread
        # --------------------------------------------------

        self.thread = None

        self.reconnect_thread = None

        self.auto_reconnect = True

        self.reconnect_delay = 5

        # --------------------------------------------------
        # Callback
        # --------------------------------------------------

        self.on_tick: Optional[Callable] = None

        self.on_connected: Optional[Callable] = None

        self.on_disconnected: Optional[Callable] = None

        # --------------------------------------------------
        # Symbol
        # --------------------------------------------------

        self.symbol = None

        # --------------------------------------------------
        # Statistics
        # --------------------------------------------------

        self.messages_received = 0

        self.last_message_time = None

        # --------------------------------------------------
        # Logger
        # --------------------------------------------------

        self.logger = logging.getLogger("CoinDCXWebSocket")

        self.logger.info("=" * 60)
        self.logger.info("CoinDCX WebSocket Engine Initialized")
        self.logger.info("=" * 60)

        # ==================================================
        # Callback Registration
        # ==================================================

        def set_tick_callback(self, callback: Callable):
            self.on_tick = callback

        def set_connected_callback(self, callback: Callable):
            self.on_connected = callback

        def set_disconnected_callback(self, callback: Callable):
            self.on_disconnected = callback

        # ==================================================
        # Status
        # ==================================================

        def is_connected(self):

            return self.connected

        def is_running(self):

            return self.running

        # ==================================================
        # Connect
        # ==================================================

        def connect(self, symbol: str):

            self.symbol = symbol

            self.running = True

            self.logger.info(f"Connecting to CoinDCX WebSocket ({symbol})")

            self.thread = threading.Thread(
                target=self._run,
                daemon=True
            )

            self.thread.start()

            if self.auto_reconnect:

                self.reconnect_thread = threading.Thread(
                    target=self._reconnect_loop,
                    daemon=True
                )

                self.reconnect_thread.start()

        # ==================================================
        # Disconnect
        # ==================================================

        def disconnect(self):

            self.logger.info("Disconnect requested.")

            self.running = False

            self.connected = False

            try:

                if self.ws is not None:

                    self.ws.close()

            except Exception as e:

                self.logger.error(e)

        # ==================================================
        # Background Runner
        # ==================================================

        def _run(self):

            self.logger.info("Starting WebSocket Engine...")

            try:

                self.ws = websocket.WebSocketApp(

                    self.ws_url,

                    on_open=self._on_open,

                    on_message=self._on_message,

                    on_error=self._on_error,

                    on_close=self._on_close

                )

                self.ws.run_forever()

            except Exception as e:

                self.logger.exception(e)

        # ==================================================
        # Auto Reconnect
        # ==================================================

        def _reconnect_loop(self):

            while self.running:

                if not self.connected:

                    self.logger.warning(
                        "Connection Lost. Reconnecting..."
                    )

                    try:

                        self._run()

                except Exception as e:

                    self.logger.error(e)

                time.sleep(self.reconnect_delay)

            else:

                time.sleep(1)

        # ==================================================
        # WebSocket Events
        # ==================================================

        def _on_open(self, ws):

            self.connected = True

            self.logger.info("WebSocket Connected Successfully")

            if self.on_connected is not None:
                try:
                    self.on_connected()
                except Exception as e:
                    self.logger.error(e)

            # -------------------------------------------------
            # Subscription
            # -------------------------------------------------
            # TODO:
            # এখানে CoinDCX-এর অফিসিয়াল subscribe payload যোগ করা হবে।
            # এখন ইচ্ছাকৃতভাবে ফাঁকা রাখা হয়েছে যতক্ষণ না
            # অফিসিয়াল WebSocket subscription format যুক্ত করা হচ্ছে।
            # -------------------------------------------------

        def _on_message(self, ws, message):

            self.messages_received += 1

            self.last_message_time = time.time()

            try:

                data = json.loads(message)

            except Exception as e:

                self.logger.error(
                    f"JSON Parse Error : {e}"
                )

                return

            try:

                self._dispatch_tick(data)

            except Exception as e:

                self.logger.exception(e)

        def _on_error(self, ws, error):

            self.connected = False

            self.logger.error(
                f"WebSocket Error : {error}"
            )

        def _on_close(self, ws, status_code, message):

            self.connected = False

            self.logger.warning(
                f"WebSocket Closed ({status_code})"
            )

            if self.on_disconnected is not None:

                try:

                    self.on_disconnected()

                except Exception as e:

                    self.logger.error(e)

        # ==================================================
        # Tick Processing
        # ==================================================

        def _process_tick(self, data):

            """
            Generic Tick Processor

            NOTE:
            CoinDCX-এর অফিসিয়াল WebSocket message format
            যুক্ত হলে এই ফাংশন আপডেট করা হবে।
            """

            if not isinstance(data, dict):
                return

            tick = {}

            tick["symbol"] = data.get("symbol")
            tick["price"] = data.get("price")
            tick["volume"] = data.get("volume")
            tick["timestamp"] = data.get("timestamp", time.time())

            return tick

        # ==================================================
        # Tick Dispatcher
        # ==================================================

        def _dispatch_tick(self, data):

            tick = self._process_tick(data)

            if tick is None:
                return

            if self.on_tick is not None:

                try:
                    self.on_tick(tick)

                except Exception as e:
                    self.logger.exception(e)

        # ==================================================
        # Statistics
        # ==================================================

        def get_statistics(self):

            return {

                "connected": self.connected,

                "running": self.running,

                "messages_received": self.messages_received,

                "last_message_time": self.last_message_time,

                "symbol": self.symbol

            }

        # ==================================================
        # Reset Statistics
        # ==================================================

        def reset_statistics(self):

            self.messages_received = 0

            self.last_message_time = None

        # ==================================================
        # Shutdown
        # ==================================================

        def shutdown(self):

            self.logger.info("Shutting down CoinDCX WebSocket Engine...")

            self.disconnect()