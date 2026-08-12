"""
============================================================
Liquidity Hunter AI
CoinDCX Socket.IO Engine
Production Edition (V20.5)
============================================================

Provider
--------
CoinDCX Socket.IO

Responsibilities
----------------
• Socket.IO Connection
• Automatic Reconnection
• Market Subscription
• Tick Processing
• Duplicate Tick Protection
• Live Candle Building
• Queue Processing
• Controller Notification
• Live Candle Notification
• Closed Candle Notification
• Health Monitoring
• Runtime Statistics
• Clean Shutdown

V20.5 Update
------------
• Compatible with LiveCandleBuilder V20.5
• Closed Candle Event Separation
• Live Candle Callback Separation
• Timeframe Switching Support
• Safe Callback Execution
• Production Queue Processing
• Strict UTC Tick Timestamp Handling
• Local Time -> UTC Timestamp Bug Fixed
============================================================
"""

from __future__ import annotations

import json
import logging
import queue
import threading
import time

from datetime import datetime, timezone
from typing import Callable, Optional

import socketio

from utils.logger import get_logger
from providers.live_candle_builder import LiveCandleBuilder


# ==========================================================
# CoinDCX WebSocket
# ==========================================================

class CoinDCXWebSocket:

    """
    Production-grade CoinDCX Socket.IO Engine.

    Architecture
    ------------

        CoinDCX Socket.IO
                │
                ▼
        new-trade event
                │
                ▼
        Tick Queue
                │
                ▼
        Queue Worker
                │
                ▼
        Tick Processing
                │
          ┌─────┴─────┐
          ▼           ▼
        Tick      Candle Builder
                      │
               ┌──────┴──────┐
               ▼             ▼
          Live Candle    Closed Candle
               │             │
               ▼             ▼
          Controller      Controller
               │             │
               ▼             ▼
             Chart        AI Pipeline
    """

    # ======================================================
    # Configuration
    # ======================================================

    DEFAULT_SOCKET_URL = (
        "https://stream.coindcx.com"
    )

    DEFAULT_TIMEFRAME = "1m"

    WAIT_TIMEOUT = 20

    RECONNECT_DELAY = 5

    MAX_RECONNECT_DELAY = 60

    HEARTBEAT_TIMEOUT = 30

    QUEUE_SIZE = 5000

    # ======================================================
    # Initialization
    # ======================================================

    def __init__(
        self,
        timeframe: str = DEFAULT_TIMEFRAME,
    ):

        # --------------------------------------------------
        # Logger
        # --------------------------------------------------

        self.logger = get_logger(
            self.__class__.__name__
        )

        if not self.logger.handlers:

            handler = logging.StreamHandler()

            formatter = logging.Formatter(
                "%(asctime)s | "
                "%(levelname)s | "
                "%(name)s | "
                "%(message)s"
            )

            handler.setFormatter(
                formatter
            )

            self.logger.addHandler(
                handler
            )

        self.logger.setLevel(
            logging.INFO
        )

        # --------------------------------------------------
        # Socket.IO Client
        # --------------------------------------------------

        self.sio = socketio.Client(

            reconnection=True,

            reconnection_attempts=0,

            reconnection_delay=(
                self.RECONNECT_DELAY
            ),

            logger=False,

            engineio_logger=False,
        )

        # --------------------------------------------------
        # Synchronization
        # --------------------------------------------------

        self._lock = threading.RLock()

        self._stop_event = (
            threading.Event()
        )

        # --------------------------------------------------
        # Runtime State
        # --------------------------------------------------

        self.running = False

        self.connected = False

        self.symbol = None

        self.socket_url = (
            self.DEFAULT_SOCKET_URL
        )

        self.connection_time = None

        self.last_message_time = None

        self.last_tick_time = None

        self.last_heartbeat = None

        self.last_error = None

        self.reconnect_attempts = 0

        self.reconnect_delay = (
            self.RECONNECT_DELAY
        )

        # --------------------------------------------------
        # Statistics
        # --------------------------------------------------

        self.received_ticks = 0

        self.processed_ticks = 0

        self.dropped_ticks = 0

        self.duplicate_ticks = 0

        # --------------------------------------------------
        # Subscription State
        # --------------------------------------------------

        self.subscriptions = set()

        # --------------------------------------------------
        # Tick Queue
        # --------------------------------------------------

        self.tick_queue = queue.Queue(
            maxsize=self.QUEUE_SIZE
        )

        # --------------------------------------------------
        # Worker Threads
        # --------------------------------------------------

        self.socket_thread = None

        self.queue_thread = None

        self.monitor_thread = None

        # --------------------------------------------------
        # Market Components
        # --------------------------------------------------

        self.candle_builder = (
            LiveCandleBuilder(
                timeframe=timeframe
            )
        )

        self.controller = None

        self.chart_widget = None

        # --------------------------------------------------
        # Duplicate Tick Protection
        # --------------------------------------------------

        self._last_tick_key = {}

        # --------------------------------------------------
        # Callbacks
        # --------------------------------------------------

        self.on_tick: Optional[
            Callable
        ] = None

        self.on_candle: Optional[
            Callable
        ] = None

        self.on_candle_closed: Optional[
            Callable
        ] = None

        self.on_connected: Optional[
            Callable
        ] = None

        self.on_disconnected: Optional[
            Callable
        ] = None

        # --------------------------------------------------
        # Internal Flags
        # --------------------------------------------------

        self._events_registered = False

        # --------------------------------------------------
        # Startup Log
        # --------------------------------------------------

        self.logger.info(
            "=" * 60
        )

        self.logger.info(
            "Liquidity Hunter AI"
        )

        self.logger.info(
            "CoinDCX Socket.IO Engine (V20.5)"
        )

        self.logger.info(
            "Initialization Completed"
        )

        self.logger.info(
            "=" * 60
        )

    # ======================================================
    # Callback Registration
    # ======================================================

    def set_tick_callback(
        self,
        callback: Callable,
    ):

        self.on_tick = callback

    # ======================================================

    def set_candle_callback(
        self,
        callback: Callable,
    ):

        self.on_candle = callback

    # ======================================================

    def set_candle_closed_callback(
        self,
        callback: Callable,
    ):

        self.on_candle_closed = callback

    # ======================================================

    def set_connected_callback(
        self,
        callback: Callable,
    ):

        self.on_connected = callback

    # ======================================================

    def set_disconnected_callback(
        self,
        callback: Callable,
    ):

        self.on_disconnected = callback

    # ======================================================

    def set_controller(
        self,
        controller,
    ):

        self.controller = controller

    # ======================================================

    def set_chart_widget(
        self,
        chart_widget,
    ):

        self.chart_widget = chart_widget

    # ======================================================
    # Timeframe Management
    # ======================================================

    def set_timeframe(
        self,
        timeframe,
    ):

        self.logger.info(
            "Changing Live Candle Timeframe : %s",
            timeframe,
        )

        # --------------------------------------------------
        # Pause Candle Builder
        # --------------------------------------------------

        self.candle_builder.pause()

        try:

            # --------------------------------------------------
            # Change Timeframe
            # --------------------------------------------------

            self.candle_builder.set_timeframe(
                timeframe
            )

        finally:

            # --------------------------------------------------
            # Resume Candle Builder
            # --------------------------------------------------

            self.candle_builder.resume()

        self.logger.info(
            "Live Candle Timeframe Active : %s",
            self.candle_builder.timeframe,
        )

    # ======================================================
    # Status
    # ======================================================

    def is_connected(
        self,
    ) -> bool:

        return self.connected

    # ======================================================

    def is_running(
        self,
    ) -> bool:

        return self.running

    # ======================================================
    # Safe Callback
    # ======================================================

    def _safe_callback(
        self,
        callback: Optional[Callable],
        *args,
        **kwargs,
    ):

        if callback is None:

            return

        try:

            callback(
                *args,
                **kwargs
            )

        except Exception as exc:

            self.logger.exception(
                "Callback execution failed: %s",
                exc,
            )

    # ======================================================
    # Runtime Reset
    # ======================================================

    def _reset_runtime(
        self,
    ):

        self.connected = False

        self.running = False

        self.connection_time = None

        self.last_message_time = None

        self.last_tick_time = None

        self.last_heartbeat = None

        self.last_error = None

        self.received_ticks = 0

        self.processed_ticks = 0

        self.dropped_ticks = 0

        self.duplicate_ticks = 0

        self.subscriptions.clear()

        self._last_tick_key.clear()

        # --------------------------------------------------
        # Clear Queue
        # --------------------------------------------------

        while True:

            try:

                self.tick_queue.get_nowait()

                self.tick_queue.task_done()

            except queue.Empty:

                break

    # ======================================================
    # Heartbeat
    # ======================================================

    def update_heartbeat(
        self,
    ):

        self.last_heartbeat = (
            time.time()
        )

        self.last_message_time = (
            self.last_heartbeat
        )

    # ======================================================

    def heartbeat_age(
        self,
    ):

        if self.last_heartbeat is None:

            return None

        return (
            time.time()
            - self.last_heartbeat
        )

    # ======================================================

    def is_connection_healthy(
        self,
    ):

        if not self.connected:

            return False

        age = self.heartbeat_age()

        if age is None:

            return True

        return (
            age
            <= self.HEARTBEAT_TIMEOUT
        )

    # ======================================================
    # Connection Management
    # ======================================================

    def connect(
        self,
        url: str,
        symbol: str,
    ) -> bool:

        # --------------------------------------------------
        # Prevent Duplicate Start
        # --------------------------------------------------

        if self.running:

            self.logger.warning(
                "WebSocket is already running."
            )

            return False

        # --------------------------------------------------
        # Store Configuration
        # --------------------------------------------------

        self.socket_url = url

        self.symbol = symbol

        # --------------------------------------------------
        # Register Socket Events
        # --------------------------------------------------

        self._register_events()

        # --------------------------------------------------
        # Reset Stop Event
        # --------------------------------------------------

        self._stop_event.clear()

        # --------------------------------------------------
        # Runtime State
        # --------------------------------------------------

        self.running = True

        self.reconnect_attempts = 0

        self.reconnect_delay = (
            self.RECONNECT_DELAY
        )

        # --------------------------------------------------
        # Connection Thread
        # --------------------------------------------------

        self.socket_thread = threading.Thread(

            target=self._connection_worker,

            name="CoinDCXWebSocket",

            daemon=True,
        )

        self.socket_thread.start()

        # --------------------------------------------------
        # Queue Worker
        # --------------------------------------------------

        self.start_workers()

        self.logger.info(
            "Connection thread started."
        )

        return True

    # ======================================================
    # Connection Worker
    # ======================================================

    def _connection_worker(
        self,
    ):

        while not self._stop_event.is_set():

            try:

                self.logger.info(
                    "Connecting to %s",
                    self.socket_url,
                )

                self.logger.info(
                    "Calling sio.connect()..."
                )

                self.sio.connect(

                    self.socket_url,

                    transports=[
                        "websocket"
                    ],

                    wait=True,

                    wait_timeout=(
                        self.WAIT_TIMEOUT
                    ),
                )

                self.logger.info(
                    "sio.connect() returned."
                )

                self.reconnect_attempts = 0

                self.sio.wait()

            except Exception as exc:

                self.last_error = exc

                self.reconnect_attempts += 1

                self.logger.exception(
                    "Connection failed: %s",
                    exc,
                )

            # --------------------------------------------------
            # Stop Requested
            # --------------------------------------------------

            if self._stop_event.is_set():

                break

            # --------------------------------------------------
            # Mark Disconnected
            # --------------------------------------------------

            self.connected = False

            # --------------------------------------------------
            # Reconnect Delay
            # --------------------------------------------------

            self.logger.info(

                "Reconnecting in %.1f seconds...",

                self.reconnect_delay,
            )

            if self._stop_event.wait(
                self.reconnect_delay
            ):

                break

            self.reconnect_delay = min(

                self.reconnect_delay * 2,

                self.MAX_RECONNECT_DELAY,
            )

    # ======================================================
    # Disconnect
    # ======================================================

    def disconnect(
        self,
    ):

        self.logger.info(
            "Stopping CoinDCX WebSocket..."
        )

        self._stop_event.set()

        self.running = False

        self.connected = False

        # --------------------------------------------------
        # Unsubscribe
        # --------------------------------------------------

        try:

            if self.sio.connected:

                self._unsubscribe_market()

        except Exception:

            self.logger.exception(
                "Unsubscribe during disconnect failed."
            )

        # --------------------------------------------------
        # Disconnect Socket
        # --------------------------------------------------

        try:

            if self.sio.connected:

                self.sio.disconnect()

        except Exception as exc:

            self.last_error = exc

            self.logger.exception(
                "Disconnect failed: %s",
                exc,
            )

        # --------------------------------------------------
        # Join Socket Thread
        # --------------------------------------------------

        if (

            self.socket_thread is not None

            and

            self.socket_thread.is_alive()

        ):

            self.socket_thread.join(
                timeout=2
            )

        self.logger.info(
            "WebSocket stopped."
        )

    # ======================================================
    # Socket.IO Event Registration
    # ======================================================

    def _register_events(
        self,
    ):

        if self._events_registered:

            return

        # ==================================================
        # Connected
        # ==================================================

        @self.sio.event
        def connect():

            self.connected = True

            self.connection_time = (
                datetime.now(timezone.utc)
            )

            self.reconnect_delay = (
                self.RECONNECT_DELAY
            )

            self.update_heartbeat()

            self.logger.info(
                "Connected to CoinDCX WebSocket."
            )

            # --------------------------------------------------
            # Subscribe
            # --------------------------------------------------

            self._subscribe_market()

            # --------------------------------------------------
            # Controller Callback
            # --------------------------------------------------

            self._safe_callback(
                self.on_connected
            )

        # ==================================================
        # Disconnected
        # ==================================================

        @self.sio.event
        def disconnect():

            self.connected = False

            self.logger.warning(
                "Disconnected from CoinDCX WebSocket."
            )

            self._safe_callback(
                self.on_disconnected
            )

        # ==================================================
        # Connection Error
        # ==================================================

        @self.sio.event
        def connect_error(
            error,
        ):

            self.last_error = error

            self.logger.error(
                "Connection error: %s",
                error,
            )

        # ==================================================
        # New Trade
        # ==================================================

        @self.sio.on(
            "new-trade"
        )
        def _on_new_trade(
            data,
        ):

            self._handle_market_message(
                data
            )

        self._events_registered = True

        self.logger.info(
            "Socket.IO events registered."
        )

    # ======================================================
    # Market Subscription
    # ======================================================

    def _subscribe_market(
        self,
    ):

        if not self.symbol:

            self.logger.warning(
                "No market symbol configured."
            )

            return

        try:

            payload = {

                "channelName":
                    self.symbol,

            }

            self.sio.emit(

                "join",

                payload,
            )

            self.subscriptions.add(
                self.symbol
            )

            self.logger.info(
                "Subscribed to %s",
                self.symbol,
            )

        except Exception as exc:

            self.last_error = exc

            self.logger.exception(
                "Subscription failed: %s",
                exc,
            )

    # ======================================================
    # Market Unsubscription
    # ======================================================

    def _unsubscribe_market(
        self,
    ):

        if not self.symbol:

            return

        try:

            payload = {

                "channelName":
                    self.symbol,

            }

            self.sio.emit(

                "leave",

                payload,
            )

            self.subscriptions.discard(
                self.symbol
            )

            self.logger.info(
                "Unsubscribed from %s",
                self.symbol,
            )

        except Exception as exc:

            self.logger.exception(
                "Unsubscribe failed: %s",
                exc,
            )

    # ======================================================
    # Market Tick Event
    # ======================================================

    def _handle_market_message(
        self,
        data,
    ):

        self.received_ticks += 1

        self.update_heartbeat()

        if data is None:

            return

        try:

            self.logger.debug(
                "Raw Tick : %s",
                data,
            )

            # --------------------------------------------------
            # CoinDCX Payload Compatibility
            # --------------------------------------------------

            if (

                isinstance(data, dict)

                and

                "data" in data

            ):

                raw_data = data["data"]

                if isinstance(
                    raw_data,
                    str
                ):

                    data = json.loads(
                        raw_data
                    )

                else:

                    data = raw_data

            # --------------------------------------------------
            # Queue
            # --------------------------------------------------

            self.tick_queue.put_nowait(
                data
            )

        except queue.Full:

            self.dropped_ticks += 1

            self.logger.warning(
                "Tick queue is full. "
                "Tick dropped."
            )

        except Exception as exc:

            self.logger.exception(
                "Tick parse failed: %s",
                exc,
            )

    # ======================================================
    # Queue Worker
    # ======================================================

    def _process_tick_queue(
        self,
    ):

        self.logger.info(
            "Tick queue worker active."
        )

        while not self._stop_event.is_set():

            try:

                tick = self.tick_queue.get(
                    timeout=0.5
                )

            except queue.Empty:

                continue

            try:

                self._process_tick(
                    tick
                )

            except Exception:

                self.logger.exception(
                    "Failed to process tick."
                )

            finally:

                self.tick_queue.task_done()

        self.logger.info(
            "Tick queue worker stopped."
        )

    # ======================================================
    # Tick Processing
    # ======================================================

    def _process_tick(
        self,
        tick,
    ):

        self.logger.debug(
            "PROCESSING TICK"
        )

        # --------------------------------------------------
        # Validate Tick
        # --------------------------------------------------

        if not isinstance(
            tick,
            dict
        ):

            return

        # --------------------------------------------------
        # Duplicate Protection
        # --------------------------------------------------

        if self.is_duplicate_tick(
            tick
        ):

            self.duplicate_ticks += 1

            return

        # --------------------------------------------------
        # Price
        # --------------------------------------------------

        price = self.extract_price(
            tick
        )

        if price is None:

            return

        # --------------------------------------------------
        # Volume
        # --------------------------------------------------

        volume = self.extract_volume(
            tick
        )

        # --------------------------------------------------
        # Timestamp
        # --------------------------------------------------

        tick_time = (
            self.extract_timestamp(
                tick
            )
        )

        # --------------------------------------------------
        # Update Candle Builder
        # --------------------------------------------------

        closed_candle = (

            self.candle_builder.update_tick(

                price=price,

                volume=volume,

                timestamp=tick_time,
            )
        )

        self.processed_ticks += 1

        self.last_tick_time = (
            tick_time
        )

        # ==================================================
        # Tick Callback
        # ==================================================

        self._safe_callback(
            self.on_tick,
            tick,
        )

        # ==================================================
        # Live Current Candle
        # ==================================================

        current_candle = (

            self.candle_builder
            .get_current_candle()
        )

        if current_candle is not None:

            self._safe_callback(

                self.on_candle,

                current_candle,
            )

        # ==================================================
        # Closed Candle
        # ==================================================

        if closed_candle is not None:

            self.logger.info(

                "CANDLE CLOSED | "

                "Time=%s | "

                "O=%s | "

                "H=%s | "

                "L=%s | "

                "C=%s | "

                "V=%s",

                closed_candle.timestamp,

                closed_candle.open,

                closed_candle.high,

                closed_candle.low,

                closed_candle.close,

                closed_candle.volume,
            )

            self._safe_callback(

                self.on_candle_closed,

                closed_candle,
            )

    # ======================================================
    # Tick Field Extraction
    # ======================================================

    def extract_price(
        self,
        tick,
    ) -> Optional[float]:

        try:

            value = tick.get(
                "p"
            )

            if value is None:

                value = tick.get(
                    "price"
                )

            if value is None:

                return None

            return float(value)

        except (
            TypeError,
            ValueError,
        ):

            return None

    # ======================================================

    def extract_volume(
        self,
        tick,
    ) -> float:

        try:

            value = tick.get(
                "q",
                tick.get(
                    "quantity",
                    0.0
                )
            )

            if value is None:

                return 0.0

            return float(value)

        except (
            TypeError,
            ValueError,
        ):

            return 0.0

    # ======================================================
    # Tick Timestamp Extraction
    # ======================================================

    def extract_timestamp(
        self,
        tick,
    ) -> datetime:

        """
        Extract CoinDCX trade timestamp.

        IMPORTANT
        ---------
        CoinDCX trade timestamps are Unix timestamps
        expressed in milliseconds.

        datetime.fromtimestamp() without an explicit
        timezone uses the operating system's local timezone.

        That caused:

            22:40 IST

        to become:

            22:40 UTC

        when LiveCandleBuilder later interpreted the
        naive datetime as UTC.

        This method therefore ALWAYS returns a
        timezone-aware UTC datetime.
        """

        try:

            timestamp = tick.get(
                "T"
            )

            if timestamp is None:

                timestamp = tick.get(
                    "timestamp"
                )

            # --------------------------------------------------
            # Millisecond Unix Timestamp
            # --------------------------------------------------

            if timestamp is not None:

                timestamp_ms = int(
                    timestamp
                )

                utc_datetime = (
                    datetime.fromtimestamp(
                        timestamp_ms / 1000,
                        tz=timezone.utc,
                    )
                )

                self.logger.debug(
                    "UTC Tick Timestamp : %s",
                    utc_datetime,
                )

                return utc_datetime

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):

            pass

        # --------------------------------------------------
        # Fallback
        # --------------------------------------------------

        utc_now = datetime.now(
            timezone.utc
        )

        self.logger.warning(
            "Tick timestamp missing/invalid. "
            "Using current UTC time: %s",
            utc_now,
        )

        return utc_now

    # ======================================================
    # Duplicate Tick Filter
    # ======================================================

    def is_duplicate_tick(
        self,
        tick,
    ) -> bool:

        if not isinstance(
            tick,
            dict
        ):

            return False

        key = (

            tick.get("T"),

            tick.get("p"),

            tick.get("q"),

        )

        previous_key = (
            self._last_tick_key.get(
                self.symbol
            )
        )

        if previous_key == key:

            return True

        self._last_tick_key[
            self.symbol
        ] = key

        return False

    # ======================================================
    # Background Workers
    # ======================================================

    def start_workers(
        self,
    ):

        if (

            self.queue_thread is None

            or

            not self.queue_thread.is_alive()

        ):

            self.queue_thread = (
                threading.Thread(

                    target=(
                        self._process_tick_queue
                    ),

                    name=(
                        "CoinDCXTickQueue"
                    ),

                    daemon=True,
                )
            )

            self.queue_thread.start()

            self.logger.info(
                "Tick queue worker started."
            )

    # ======================================================

    def stop_workers(
        self,
    ):

        # --------------------------------------------------
        # Queue Worker exits through stop_event
        # --------------------------------------------------

        if (

            self.queue_thread is not None

            and

            self.queue_thread.is_alive()

        ):

            self.queue_thread.join(
                timeout=2
            )

            self.logger.info(
                "Tick queue worker stopped."
            )

    # ======================================================
    # Statistics
    # ======================================================

    def get_statistics(
        self,
    ):

        return {

            "connected":
                self.connected,

            "running":
                self.running,

            "symbol":
                self.symbol,

            "timeframe":
                self.candle_builder.timeframe,

            "received_ticks":
                self.received_ticks,

            "processed_ticks":
                self.processed_ticks,

            "dropped_ticks":
                self.dropped_ticks,

            "duplicate_ticks":
                self.duplicate_ticks,

            "last_tick_time":
                self.last_tick_time,

            "heartbeat_age":
                self.heartbeat_age(),

            "subscriptions":
                list(
                    self.subscriptions
                ),

            "queue_size":
                self.tick_queue.qsize(),

            "last_error":
                (
                    str(self.last_error)
                    if self.last_error
                    else None
                ),
        }

    # ======================================================
    # Shutdown
    # ======================================================

    def close(
        self,
    ):

        self.logger.info(
            "Closing CoinDCX WebSocket..."
        )

        self.disconnect()

        self.stop_workers()

        self._reset_runtime()

        self.logger.info(
            "CoinDCXWebSocket closed."
        )

    # ======================================================
    # Context Manager
    # ======================================================

    def __enter__(
        self,
    ):

        return self

    # ======================================================

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):

        self.close()

        return False

    # ======================================================
    # Object Representation
    # ======================================================

    def __repr__(
        self,
    ):

        return (

            f"{self.__class__.__name__}("

            f"connected={self.connected}, "

            f"running={self.running}, "

            f"symbol='{self.symbol}', "

            f"timeframe="
            f"'{self.candle_builder.timeframe}'"

            ")"
        )

    # ======================================================
    # Diagnostics
    # ======================================================

    def health_report(
        self,
    ):

        return {

            "connected":
                self.connected,

            "running":
                self.running,

            "connection_healthy":
                self.is_connection_healthy(),

            "symbol":
                self.symbol,

            "timeframe":
                self.candle_builder.timeframe,

            "received_ticks":
                self.received_ticks,

            "processed_ticks":
                self.processed_ticks,

            "dropped_ticks":
                self.dropped_ticks,

            "duplicate_ticks":
                self.duplicate_ticks,

            "queue_size":
                self.tick_queue.qsize(),

            "last_tick_time":
                (
                    self.last_tick_time.isoformat()
                    if self.last_tick_time
                    else None
                ),

            "connection_time":
                (
                    self.connection_time.isoformat()
                    if self.connection_time
                    else None
                ),

            "heartbeat_age":
                self.heartbeat_age(),

            "last_error":
                (
                    str(self.last_error)
                    if self.last_error
                    else None
                ),
        }

    # ======================================================

    def log_health(
        self,
    ):

        report = self.health_report()

        self.logger.info(
            "Health Report: %s",
            report,
        )

    # ======================================================
    # Debug Helpers
    # ======================================================

    def is_alive(
        self,
    ):

        return (

            self.running

            and

            self.connected
        )

    # ======================================================

    def queue_size(
        self,
    ):

        return self.tick_queue.qsize()

    # ======================================================

    def current_candle(
        self,
    ):

        return (

            self.candle_builder
            .get_current_candle()
        )

    # ======================================================

    def last_closed_candle(
        self,
    ):

        return (

            self.candle_builder
            .get_last_closed_candle()
        )

    # ======================================================

    def print_statistics(
        self,
    ):

        self.logger.info(

            "Ticks: "
            "received=%d "
            "processed=%d "
            "duplicate=%d "
            "dropped=%d "
            "queue=%d",

            self.received_ticks,

            self.processed_ticks,

            self.duplicate_ticks,

            self.dropped_ticks,

            self.tick_queue.qsize(),
        )