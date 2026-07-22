"""
Liquidity Hunter AI
CoinDCX WebSocket Engine
Production Version V17.2
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

    def _init_(self):

        # ==================================================
        # Connection
        # ==================================================

        # TODO:
        # অফিসিয়াল CoinDCX WebSocket URL
        self.ws_url = ""

        self.ws = None

        self.connected = False
        self.running = False

        # ==================================================
        # Thread Management
        # ==================================================

        self.thread = None
        self.reconnect_thread = None

        self.auto_reconnect = True
        self.reconnect_delay = 5

        # ==================================================
        # Callback
        # ==================================================

        self.on_tick: Optional[Callable] = None
        self.on_connected: Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None

        # ==================================================
        # Symbol
        # ==================================================

        self.symbol = None

        # ==================================================
        # Statistics
        # ==================================================

        self.messages_received = 0
        self.last_message_time = None

        # ==================================================
        # Logger
        # ==================================================

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

        if self.running:
            self.logger.warning("WebSocket already running.")
            return

        self.symbol = symbol

        self.running = True

        self.logger.info(
            f"Connecting to CoinDCX WebSocket ({symbol})"
        )

        self.thread = threading.Thread(
            target=self._run,
            daemon=True,
            name="CoinDCX-WebSocket"
        )

        self.thread.start()

        if self.auto_reconnect:

            self.reconnect_thread = threading.Thread(
                target=self._reconnect_loop,
                daemon=True,
                name="CoinDCX-Reconnect"
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

            self.logger.exception(e)

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

            self.ws.run_forever(
                ping_interval=20,
                ping_timeout=10
            )

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

                    self.logger.exception(e)

            time.sleep(self.reconnect_delay)

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
                self.logger.exception(e)

        # --------------------------------------------------
        # TODO:
        # CoinDCX Official Subscription Payload
        # --------------------------------------------------
        #
        # Example:
        #
        # payload = {
        #     "event": "...",
        #     "channel": "...",
        #     "pair": self.symbol
        # }
        #
        # ws.send(json.dumps(payload))
        #
        # Official CoinDCX WebSocket specification
        # অনুযায়ী এটি পরে যুক্ত করা হবে।
        # --------------------------------------------------

    # ==================================================

    def _on_message(self, ws, message):

        self.messages_received += 1

        self.last_message_time = time.time()

        try:

            data = json.loads(message)

        except json.JSONDecodeError as e:

            self.logger.error(
                f"JSON Decode Error : {e}"
            )

            return

        except Exception as e:

            self.logger.exception(e)

            return

        try:

            self._dispatch_tick(data)

        except Exception as e:

            self.logger.exception(e)

    # ==================================================

    def _on_error(self, ws, error):

        self.connected = False

        self.logger.error(
            f"WebSocket Error : {error}"
        )

    # ==================================================

    def _on_close(
        self,
        ws,
        close_status_code,
        close_msg
    ):

        self.connected = False

        self.logger.warning(

            f"WebSocket Closed "

            f"(Status={close_status_code}, "

            f"Message={close_msg})"

        )

        if self.on_disconnected is not None:

            try:

                self.on_disconnected()

            except Exception as e:

                self.logger.exception(e)

    # ==================================================
    # Send Raw Message
    # ==================================================

    def send(self, payload):

        if not self.connected:

            self.logger.warning(
                "Cannot send. WebSocket not connected."
            )

            return False

        try:

            if isinstance(payload, dict):

                payload = json.dumps(payload)

            self.ws.send(payload)

            return True

        except Exception as e:

            self.logger.exception(e)

            return False

    # ==================================================
    # Tick Processing
    # ==================================================

    def _process_tick(self, data):
        """
        Convert raw WebSocket message into a normalized tick.

        NOTE:
        CoinDCX-এর অফিসিয়াল WebSocket message format
        যুক্ত হলে এই ফাংশন আপডেট করা হবে।
        """

        if data is None:
            return None

        if not isinstance(data, dict):
            return None

        tick = {}

        tick["symbol"] = (
            data.get("symbol")
            or data.get("market")
            or self.symbol
        )

        tick["price"] = float(
            data.get("price")
            or data.get("last_price")
            or 0
        )

        tick["volume"] = float(
            data.get("volume")
            or data.get("qty")
            or 0
        )

        tick["timestamp"] = data.get(
            "timestamp",
            time.time()
        )

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

            "symbol": self.symbol,

            "messages_received": self.messages_received,

            "last_message_time": self.last_message_time

        }

    # ==================================================
    # Reset Statistics
    # ==================================================

    def reset_statistics(self):

        self.messages_received = 0

        self.last_message_time = None

        self.logger.info(
            "WebSocket statistics reset."
        )

    # ==================================================
    # Heartbeat
    # ==================================================

    def heartbeat(self):

        return {

            "connected": self.connected,

            "running": self.running,

            "last_message": self.last_message_time,

            "messages": self.messages_received

        }

        # ==================================================
    # Wait Until Connected
    # ==================================================

    def wait_until_connected(self, timeout=15):

        """
        Wait until the websocket is connected.

        Returns True if connected within timeout,
        otherwise False.
        """

        start = time.time()

        while time.time() - start < timeout:

            if self.connected:
                return True

            time.sleep(0.25)

        return False

    # ==================================================
    # Connection Information
    # ==================================================

    def connection_info(self):

        return {

            "url": self.ws_url,

            "symbol": self.symbol,

            "connected": self.connected,

            "running": self.running,

            "auto_reconnect": self.auto_reconnect,

            "reconnect_delay": self.reconnect_delay,

            "messages_received": self.messages_received,

            "last_message_time": self.last_message_time

        }

    # ==================================================
    # Shutdown
    # ==================================================

    def shutdown(self):

        self.logger.info(
            "Shutting down CoinDCX WebSocket Engine..."
        )

        self.running = False

        self.connected = False

        try:

            if self.ws is not None:

                self.ws.close()

        except Exception as e:

            self.logger.exception(e)

        if self.thread is not None:

            self.thread.join(timeout=2)

        if self.reconnect_thread is not None:

            self.reconnect_thread.join(timeout=2)

        self.logger.info(
            "CoinDCX WebSocket Engine Stopped."
        )

    # ==================================================
    # Object Representation
    # ==================================================

    def _repr_(self):

        return (

            f"<CoinDCXWebSocket "

            f"connected={self.connected}, "

            f"running={self.running}, "

            f"symbol={self.symbol}>"

        )