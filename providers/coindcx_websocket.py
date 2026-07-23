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

        # --------------------------------------------------
        # Thread Safety
        # --------------------------------------------------

        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        # --------------------------------------------------
        # Subscription Management
        # --------------------------------------------------

        # Supports multiple market subscriptions
        self.subscriptions = set()

        # --------------------------------------------------
        # Connection Statistics
        # --------------------------------------------------

        self.reconnect_count = 0
        self.connection_attempts = 0
        self.last_connected_time = None
        self.last_disconnected_time = None

        # --------------------------------------------------
        # Heartbeat
        # --------------------------------------------------

        self.last_ping = None
        self.last_pong = None

        # --------------------------------------------------
        # Tick Cache
        # --------------------------------------------------

        self.last_tick = None

        # --------------------------------------------------
        # Background Thread
        # --------------------------------------------------

        self.thread = None
        self.thread_started = False

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
            "subscriptions": list(self.subscriptions),
            "messages_received": self.messages_received,
            "last_message_time": self.last_message_time,
            "connection_attempts": self.connection_attempts,
            "reconnect_count": self.reconnect_count,
            "last_connected_time": self.last_connected_time,
            "last_disconnected_time": self.last_disconnected_time,
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

    # --------------------------------------------------
    # Connection
    # --------------------------------------------------

    def connect(self, url: str, symbol: str):

        if self.running:
            self.logger.warning("Connection already running.")
            return

        self.symbol = symbol
        self.running = True
        self.connection_attempts += 1
        self._stop_event.clear()

        self.register_events()

        self.thread = threading.Thread(
            target=self._connection_worker,
            args=(url,),
            daemon=True,
        )

        self.thread_started = True

        print(">>> Starting Background Thread <<<")

        self.thread.start()

        print(">>> Thread Started <<<")

    # --------------------------------------------------
    # Background Worker
    # --------------------------------------------------

    def _connection_worker(self, url: str):

        print(">>> Worker Function Entered <<<")

        self.logger.info("Starting Socket.IO worker...")

        while not self._stop_event.is_set():

            try:

                self.logger.info(f"Connecting to {url}")

                self.sio.connect(
                    url,
                    transports=["websocket"],
                    wait=True,
                    wait_timeout=20,
                )

                self.sio.wait()

            except Exception as e:

                self.connected = False
                self.reconnect_count += 1

                self.logger.error(
                    f"Connection error: {e}"
                )

                if self._stop_event.is_set():
                    break

                self.logger.info(
                    "Retrying in 5 seconds..."
                )

                time.sleep(5)

        self.logger.info("Socket worker stopped.")

    # --------------------------------------------------
    # Disconnect
    # --------------------------------------------------

    def disconnect(self):

        self.logger.info("Disconnect requested.")

        self.running = False
        self._stop_event.set()

        try:

            if self.sio.connected:
                self.sio.disconnect()

        except Exception as e:

            self.logger.error(
                f"Disconnect error: {e}"
            )

        if self.thread and self.thread.is_alive():

            self.thread.join(timeout=5)

        self.connected = False
        self.thread_started = False

        self.logger.info("Disconnected successfully.")

    # --------------------------------------------------
    # Socket.IO Event Registration
    # --------------------------------------------------

    def register_events(self):

        @self.sio.event
        def connect():

            self.connected = True
            self.last_connected_time = time.time()

            self.logger.info("Socket.IO connected.")

            if self.symbol:
                self.subscribe(self.symbol)

            if self.on_connected:
                try:
                    self.on_connected()
                except Exception as e:
                    self.logger.error(
                        f"Connected callback error: {e}"
                    )

        @self.sio.event
        def disconnect():

            self.connected = False
            self.last_disconnected_time = time.time()

            self.logger.warning("Socket.IO disconnected.")

            if self.on_disconnected:
                try:
                    self.on_disconnected()
                except Exception as e:
                    self.logger.error(
                        f"Disconnected callback error: {e}"
                    )

        @self.sio.event
        def connect_error(data):

            self.connected = False

            self.logger.error(
                f"Connection failed: {data}"
            )

        @self.sio.event
        def error(data):

            self.logger.error(
                f"Socket error: {data}"
            )

    # --------------------------------------------------
    # Subscribe
    # --------------------------------------------------

    def subscribe(self, channel: str):

        if not self.connected:
            self.logger.warning(
                "Cannot subscribe. Socket not connected."
            )
            return

        try:

            self.sio.emit(
                "join",
                {
                    "channelName": channel
                }
            )

            self.subscriptions.add(channel)

            self.logger.info(
                f"Subscribed: {channel}"
            )

        except Exception as e:

            self.logger.error(
                f"Subscribe error: {e}"
            )

    # --------------------------------------------------
    # Unsubscribe
    # --------------------------------------------------

    def unsubscribe(self, channel: str):

        if not self.connected:
            return

        try:

            self.sio.emit(
                "leave",
                {
                    "channelName": channel
                }
            )

            self.subscriptions.discard(channel)

            self.logger.info(
                f"Unsubscribed: {channel}"
            )

        except Exception as e:

            self.logger.error(
                f"Unsubscribe error: {e}"
            )

    # --------------------------------------------------
    # Tick Handler
    # --------------------------------------------------

    def process_tick(self, tick: dict):

        if not isinstance(tick, dict):
            return

        self.messages_received += 1
        self.last_message_time = time.time()
        self.last_tick = tick

        try:

            if self.on_tick:
                self.on_tick(tick)

        except Exception as e:

            self.logger.error(
                f"Tick callback error: {e}"
            )

    # --------------------------------------------------
    # Register Market Event
    # --------------------------------------------------

    def register_market_handler(self, event_name: str):

        @self.sio.on(event_name)
        def market_message(data):

            try:

                self.process_tick(data)

            except Exception as e:

                self.logger.error(
                    f"Market message error: {e}"
                )