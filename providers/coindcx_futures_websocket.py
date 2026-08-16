"""
Liquidity Hunter AI
CoinDCX Futures WebSocket V20.9.6

FUTURES AUTHORITATIVE LIVE MARKET ENGINE

Architecture
------------

CoinDCX Futures Socket.IO
        |
        v
    new-trade
        |
        v
  Normalize Tick
        |
        +----------------------+
        |                      |
        v                      v
Controller Price        Tick Queue
IMMEDIATE PATH               |
                             v
                       Candle Builder
                             |
                    +--------+--------+
                    |                 |
                    v                 v
              Live Candle       Closed Candle
                    |                 |
                    v                 v
               Controller        Controller
                    |
                    v
              Signal Analysis


Authority Rules
---------------

Historical:
    Futures REST

Live Price:
    Futures WebSocket

Live Candle:
    Futures WebSocket
    + LiveCandleBuilder

Closed Candle:
    Futures WebSocket
    + LiveCandleBuilder

Spot WebSocket:
    NEVER used by this engine.

Important
---------

The Controller receives a valid Futures tick immediately
before the tick enters the processing queue.

This guarantees:

    WebSocket Tick
        ->
    Controller current_price

does NOT wait for candle processing.

V20.9.6 goals
-------------

1. Futures WebSocket remains the only live-price authority.
2. Controller receives each accepted tick immediately.
3. Tick processing remains asynchronous.
4. Candle building happens only inside the worker.
5. Closed candle is forwarded exactly once.
6. Duplicate ticks are rejected.
7. Old/out-of-order ticks are rejected.
8. Symbol changes reset live state safely.
9. Timeframe changes reset candle state safely.
10. Reconnection does not create duplicate callbacks.
11. Controller/UI failures cannot kill the WebSocket worker.
"""

from __future__ import annotations

import json
import logging
import queue
import threading
import time

from datetime import datetime, timezone
from typing import Callable, Optional, Any

import socketio

from providers.live_candle_builder import (
    LiveCandleBuilder,
)

from utils.logger import get_logger


# ============================================================
# FUTURES WEBSOCKET
# ============================================================

class CoinDCXFuturesWebSocket:

    # ========================================================
    # IDENTITY
    # ========================================================

    PROVIDER_NAME = (
        "CoinDCX Futures WebSocket"
    )

    VERSION = "V20.9.6"

    MARKET_TYPE = "FUTURES"

    EXCHANGE = "CoinDCX"

    # ========================================================
    # SOCKET CONFIG
    # ========================================================

    DEFAULT_SOCKET_URL = (
        "https://stream.coindcx.com"
    )

    SOCKET_CHANNEL_SUFFIX = "@trades-futures"

    DEFAULT_TIMEFRAME = "1m"

    DEFAULT_SYMBOL = "B-BTC_USDT"

    # ========================================================
    # CONNECTION CONFIG
    # ========================================================

    WAIT_TIMEOUT = 20

    RECONNECT_DELAY = 5

    MAX_RECONNECT_DELAY = 60

    HEARTBEAT_TIMEOUT = 30

    # ========================================================
    # QUEUE CONFIG
    # ========================================================

    QUEUE_SIZE = 5000

    QUEUE_GET_TIMEOUT = 0.5

    # ========================================================
    # SUPPORTED FUTURES
    # ========================================================

    SUPPORTED_SYMBOLS = (
        "B-BTC_USDT",
        "B-ETH_USDT",
        "B-XAU_USDT",
        "B-XAG_USDT",
    )

    # ========================================================
    # INIT
    # ========================================================

    def __init__(
        self,
        timeframe: str = DEFAULT_TIMEFRAME,
        symbol: str = DEFAULT_SYMBOL,
    ):

        # ----------------------------------------------------
        # LOGGER
        # ----------------------------------------------------

        self.logger = get_logger(
            self.__class__.__name__
        )

        if not self.logger.handlers:

            handler = logging.StreamHandler()

            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | "
                    "%(levelname)s | "
                    "%(name)s | "
                    "%(message)s"
                )
            )

            self.logger.addHandler(
                handler
            )

        self.logger.setLevel(
            logging.INFO
        )

        # ----------------------------------------------------
        # THREAD SAFETY
        # ----------------------------------------------------

        self._lock = threading.RLock()

        self._stop_event = (
            threading.Event()
        )

        # ----------------------------------------------------
        # SYMBOL
        # ----------------------------------------------------

        self.symbol = (
            self.normalize_symbol(
                symbol
            )
        )

        if not self.validate_symbol(
            self.symbol
        ):
            raise ValueError(
                "Unsupported Futures "
                f"WebSocket symbol: "
                f"{self.symbol}"
            )

        # ----------------------------------------------------
        # TIMEFRAME
        # ----------------------------------------------------

        self.timeframe = (
            str(timeframe).strip()
            if timeframe
            else self.DEFAULT_TIMEFRAME
        )

        # ----------------------------------------------------
        # SOCKET STATE
        # ----------------------------------------------------

        self.socket_url = (
            self.DEFAULT_SOCKET_URL
        )

        self.socket_channel = None

        self.sio = None

        self.running = False

        self.connected = False

        self.connection_time = None

        self.last_message_time = None

        self.last_tick_time = None

        self.last_heartbeat = None

        self.last_error = None

        # ----------------------------------------------------
        # RECONNECT STATE
        # ----------------------------------------------------

        self.reconnect_attempts = 0

        self.reconnect_delay = (
            self.RECONNECT_DELAY
        )

        self.subscriptions = set()

        # ----------------------------------------------------
        # THREADS
        # ----------------------------------------------------

        self.socket_thread = None

        self.queue_thread = None

        # ----------------------------------------------------
        # TICK QUEUE
        # ----------------------------------------------------

        self.tick_queue = queue.Queue(
            maxsize=self.QUEUE_SIZE
        )

        # ----------------------------------------------------
        # CANDLE BUILDER
        # ----------------------------------------------------

        self.candle_builder = (
            LiveCandleBuilder(
                timeframe=self.timeframe
            )
        )

        # ----------------------------------------------------
        # CONTROLLER BRIDGE
        # ----------------------------------------------------

        self.controller = None

        self.chart_widget = None

        # ----------------------------------------------------
        # OPTIONAL CALLBACKS
        # ----------------------------------------------------

        self.on_tick: Optional[
            Callable[[dict], None]
        ] = None

        self.on_candle: Optional[
            Callable[[Any], None]
        ] = None

        self.on_candle_closed: Optional[
            Callable[[Any], None]
        ] = None

        self.on_connected: Optional[
            Callable[[], None]
        ] = None

        self.on_disconnected: Optional[
            Callable[[], None]
        ] = None

        # ----------------------------------------------------
        # TICK PROTECTION
        # ----------------------------------------------------

        self._last_tick_key = {}

        self._last_processed_timestamp = None

        self._events_registered = False

        # ----------------------------------------------------
        # STATISTICS
        # ----------------------------------------------------

        self.received_ticks = 0

        self.processed_ticks = 0

        self.dropped_ticks = 0

        self.duplicate_ticks = 0

        self.invalid_ticks = 0

        self.callback_errors = 0

        # ----------------------------------------------------
        # LATENCY
        # ----------------------------------------------------

        self.last_exchange_latency_ms = None

        self.last_queue_latency_ms = None

        self.last_total_latency_ms = None

        self.max_exchange_latency_ms = 0.0

        self.max_queue_latency_ms = 0.0

        self.max_total_latency_ms = 0.0

        self.latency_samples = 0

    # ========================================================
    # SYMBOL NORMALIZATION
    # ========================================================

    @classmethod
    def normalize_symbol(
        cls,
        symbol,
    ):

        if not symbol:
            return cls.DEFAULT_SYMBOL

        value = (
            str(symbol)
            .strip()
            .upper()
        )

        mapping = {

            # ------------------------------------------------
            # BTC
            # ------------------------------------------------

            "BTC":
                "B-BTC_USDT",

            "BTCUSDT":
                "B-BTC_USDT",

            "BTC/USDT":
                "B-BTC_USDT",

            "BTC-USDT":
                "B-BTC_USDT",

            "B-BTCUSDT":
                "B-BTC_USDT",

            "B-BTC/USDT":
                "B-BTC_USDT",

            "B-BTC-USDT":
                "B-BTC_USDT",

            # ------------------------------------------------
            # ETH
            # ------------------------------------------------

            "ETH":
                "B-ETH_USDT",

            "ETHUSDT":
                "B-ETH_USDT",

            "ETH/USDT":
                "B-ETH_USDT",

            "ETH-USDT":
                "B-ETH_USDT",

            "B-ETHUSDT":
                "B-ETH_USDT",

            "B-ETH/USDT":
                "B-ETH_USDT",

            "B-ETH-USDT":
                "B-ETH_USDT",

            # ------------------------------------------------
            # GOLD
            # ------------------------------------------------

            "XAU":
                "B-XAU_USDT",

            "XAUUSDT":
                "B-XAU_USDT",

            "XAU/USDT":
                "B-XAU_USDT",

            "XAU-USDT":
                "B-XAU_USDT",

            "GOLD":
                "B-XAU_USDT",

            "GOLDUSDT":
                "B-XAU_USDT",

            "GOLD/USDT":
                "B-XAU_USDT",

            # ------------------------------------------------
            # SILVER
            # ------------------------------------------------

            "XAG":
                "B-XAG_USDT",

            "XAGUSDT":
                "B-XAG_USDT",

            "XAG/USDT":
                "B-XAG_USDT",

            "XAG-USDT":
                "B-XAG_USDT",

            "SILVER":
                "B-XAG_USDT",

            "SILVERUSDT":
                "B-XAG_USDT",

            "SILVER/USDT":
                "B-XAG_USDT",
        }

        return mapping.get(
            value,
            value,
        )

    # ========================================================
    # SYMBOL VALIDATION
    # ========================================================

    @classmethod
    def validate_symbol(
        cls,
        symbol,
    ):

        normalized = (
            cls.normalize_symbol(
                symbol
            )
        )

        return (
            normalized
            in cls.SUPPORTED_SYMBOLS
        )

    # ========================================================
    # SYMBOL SETTER
    # ========================================================

    def set_symbol(
        self,
        symbol,
    ):

        normalized = (
            self.normalize_symbol(
                symbol
            )
        )

        if not self.validate_symbol(
            normalized
        ):
            raise ValueError(
                "Unsupported Futures "
                f"WebSocket symbol: "
                f"{normalized}"
            )

        with self._lock:

            self.symbol = normalized

            self.socket_channel = None

            self._last_tick_key.clear()

            self._last_processed_timestamp = None

            self.subscriptions.clear()

            self._clear_queue()

            self.candle_builder.reset()

        self.logger.info(
            "Futures symbol changed: %s",
            normalized,
        )

        return True

    # ========================================================
    # GET SYMBOL
    # ========================================================

    def get_symbol(self):

        return self.symbol

    # ========================================================
    # TRADE CHANNEL
    # ========================================================

    def get_trade_channel(
        self,
        symbol=None,
    ):

        normalized = (
            self.normalize_symbol(
                symbol or self.symbol
            )
        )

        return (
            normalized
            + self.SOCKET_CHANNEL_SUFFIX
        )

    # ========================================================
    # CONTROLLER
    # ========================================================

    def set_controller(
        self,
        controller,
    ):

        with self._lock:
            self.controller = controller

        return True

    attach_controller = set_controller

    # ========================================================
    # CHART
    # ========================================================

    def set_chart_widget(
        self,
        chart_widget,
    ):

        self.chart_widget = chart_widget

    # ========================================================
    # CALLBACKS
    # ========================================================

    def set_tick_callback(
        self,
        callback,
    ):

        self.on_tick = callback

    def set_candle_callback(
        self,
        callback,
    ):

        self.on_candle = callback

    def set_candle_closed_callback(
        self,
        callback,
    ):

        self.on_candle_closed = callback

    def set_connected_callback(
        self,
        callback,
    ):

        self.on_connected = callback

    def set_disconnected_callback(
        self,
        callback,
    ):

        self.on_disconnected = callback

    # ========================================================
    # SAFE CALLBACK
    # ========================================================

    def _safe_callback(
        self,
        callback,
        *args,
    ):

        if callback is None:
            return

        try:

            callback(*args)

        except Exception as exc:

            self.callback_errors += 1

            self.last_error = exc

            self.logger.exception(
                "Futures callback failed: %s",
                exc,
            )

    # ========================================================
    # STATUS
    # ========================================================

    def stop_requested(self):

        return (
            self._stop_event.is_set()
        )

    def is_connected(self):

        return bool(
            self.connected
        )

    def is_running(self):

        return bool(
            self.running
        )

    def is_alive(self):

        return bool(
            self.running
            and self.connected
        )

    # ========================================================
    # HEARTBEAT
    # ========================================================

    def update_heartbeat(self):

        now = time.time()

        self.last_heartbeat = now

        self.last_message_time = now

    # ========================================================
    # HEARTBEAT AGE
    # ========================================================

    def heartbeat_age(self):

        if self.last_heartbeat is None:
            return None

        return (
            time.time()
            - self.last_heartbeat
        )

    # ========================================================
    # CONNECTION HEALTH
    # ========================================================

    def is_connection_healthy(self):

        age = self.heartbeat_age()

        return bool(
            self.connected
            and (
                age is None
                or age <= self.HEARTBEAT_TIMEOUT
            )
        )

    # ========================================================
    # QUEUE SIZE
    # ========================================================

    def queue_size(self):

        return self.tick_queue.qsize()

    # ========================================================
    # CURRENT CANDLE
    # ========================================================

    def current_candle(self):

        return (
            self.candle_builder
            .get_current_candle()
        )

    # ========================================================
    # LAST CLOSED CANDLE
    # ========================================================

    def last_closed_candle(self):

        return (
            self.candle_builder
            .get_last_closed_candle()
        )

    # ========================================================
    # TIMESTAMP CONVERSION
    # ========================================================

    @staticmethod
    def _timestamp_to_seconds(
        timestamp,
    ):

        try:

            value = float(
                timestamp
            )

            if value > 10_000_000_000:
                value /= 1000.0

            return value

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):

            return None

    # ========================================================
    # EXCHANGE LATENCY
    # ========================================================

    def _calculate_exchange_latency(
        self,
        tick,
    ):

        if not isinstance(
            tick,
            dict,
        ):
            return None

        timestamp = (
            tick.get(
                "T",
                tick.get(
                    "timestamp"
                ),
            )
        )

        ts = (
            self._timestamp_to_seconds(
                timestamp
            )
        )

        if ts is None:
            return None

        return max(
            0.0,
            (
                time.time()
                - ts
            ) * 1000.0,
        )

    # ========================================================
    # SOCKET CLIENT
    # ========================================================

    def _initialize_socket_client(
        self,
    ):

        self.sio = socketio.Client(
            reconnection=False,
            logger=False,
            engineio_logger=False,
        )

        self._events_registered = False

    # ========================================================
    # CONNECT
    # ========================================================

    def connect(
        self,
        url=None,
        symbol=None,
    ):

        if self.running:
            return False

        self.socket_url = (
            str(url).strip()
            if url
            else self.DEFAULT_SOCKET_URL
        )

        if symbol:

            raw = (
                str(symbol)
                .strip()
                .upper()
            )

            if raw.endswith(
                self.SOCKET_CHANNEL_SUFFIX
            ):

                raw = raw[
                    :-
                    len(
                        self.SOCKET_CHANNEL_SUFFIX
                    )
                ]

            self.set_symbol(
                raw
            )

        self.socket_channel = (
            self.get_trade_channel()
        )

        self._initialize_socket_client()

        if not self._register_all_socket_events():

            self.logger.error(
                "Failed to register "
                "Futures Socket.IO events."
            )

            return False

        self._stop_event.clear()

        self.running = True

        self.connected = False

        self.reconnect_attempts = 0

        self.reconnect_delay = (
            self.RECONNECT_DELAY
        )

        self._start_tick_worker()

        self.socket_thread = (
            threading.Thread(
                target=self._connection_worker,
                name=(
                    "CoinDCXFuturesSocket"
                ),
                daemon=True,
            )
        )

        self.socket_thread.start()

        return True

    # ========================================================
    # END OF PART 1
    # ========================================================

    # ========================================================
    # CONNECTION WORKER
    # ========================================================

    def _connection_worker(self):

        while not self._stop_event.is_set():

            try:

                self.sio.connect(
                    self.socket_url,
                    transports=["websocket"],
                    wait=True,
                    wait_timeout=self.WAIT_TIMEOUT,
                )

                # ------------------------------------------------
                # Socket.IO remains active until disconnect.
                # ------------------------------------------------

                self.sio.wait()

            except Exception as exc:

                if self._stop_event.is_set():
                    break

                self.last_error = exc

                self.reconnect_attempts += 1

                self.connected = False

                self.logger.warning(
                    "Futures Socket.IO connection failed: %s",
                    exc,
                )

            if self._stop_event.is_set():
                break

            self.connected = False

            # ------------------------------------------------
            # Reconnect delay
            # ------------------------------------------------

            if self._stop_event.wait(
                self.reconnect_delay
            ):
                break

            self.reconnect_delay = min(
                self.reconnect_delay * 2,
                self.MAX_RECONNECT_DELAY,
            )

        self.running = False

        self.connected = False

    # ========================================================
    # SOCKET EVENT REGISTRATION
    # ========================================================

    def _register_socket_events(self):

        if self.sio is None:
            return False

        if self._events_registered:
            return True

        # ----------------------------------------------------
        # CONNECT
        # ----------------------------------------------------

        @self.sio.event
        def connect():

            self.connected = True

            self.connection_time = (
                datetime.now(
                    timezone.utc
                )
            )

            self.last_error = None

            self.reconnect_attempts = 0

            self.reconnect_delay = (
                self.RECONNECT_DELAY
            )

            self.update_heartbeat()

            # -----------------------------------------------
            # Subscribe immediately after connection.
            # -----------------------------------------------

            self._subscribe_futures_market()

            self._safe_callback(
                self.on_connected
            )

            self.logger.info(
                "Futures WebSocket connected: %s",
                self.symbol,
            )

        # ----------------------------------------------------
        # DISCONNECT
        # ----------------------------------------------------

        @self.sio.event
        def disconnect():

            self.connected = False

            self.last_message_time = (
                time.time()
            )

            self._safe_callback(
                self.on_disconnected
            )

            self.logger.warning(
                "Futures WebSocket disconnected."
            )

        # ----------------------------------------------------
        # CONNECTION ERROR
        # ----------------------------------------------------

        @self.sio.event
        def connect_error(error):

            self.connected = False

            self.last_error = error

            self.logger.warning(
                "Futures Socket.IO connect error: %s",
                error,
            )

        self._events_registered = True

        return True

    # ========================================================
    # FUTURES MARKET EVENTS
    # ========================================================

    def _register_futures_market_events(self):

        if self.sio is None:
            return False

        # ----------------------------------------------------
        # CoinDCX Futures trade event
        # ----------------------------------------------------

        @self.sio.on("new-trade")
        def _on_new_trade(data):

            self._on_futures_new_trade(
                data
            )

        return True

    # ========================================================
    # ALL SOCKET EVENTS
    # ========================================================

    def _register_all_socket_events(self):

        if self.sio is None:
            return False

        socket_events = (
            self._register_socket_events()
        )

        market_events = (
            self._register_futures_market_events()
        )

        return bool(
            socket_events
            and market_events
        )

    # ========================================================
    # SUBSCRIBE FUTURES MARKET
    # ========================================================

    def _subscribe_futures_market(self):

        if not self.connected:
            return False

        if self.sio is None:
            return False

        channel = (
            self.get_trade_channel()
        )

        self.socket_channel = channel

        try:

            self.sio.emit(
                "join",
                {
                    "channelName": channel
                },
            )

            print(
                "\n"
                "========== FUTURES SUBSCRIPTION "
                "=========="
            )

            print(
                "Futures Symbol :",
                self.symbol,
            )

            print(
                "Trade Channel  :",
                channel,
            )

            print(
                "Subscription   :",
                "JOIN SENT",
            )

            print(
                "=========================================="
            )

            self.subscriptions.add(
                channel
            )

            self.update_heartbeat()

            return True

        except Exception as exc:

            self.last_error = exc

            self.logger.exception(
                "Futures subscription failed: %s",
                exc,
            )

            return False

    # ========================================================
    # UNSUBSCRIBE
    # ========================================================

    def _unsubscribe_futures_market(self):

        channel = (
            self.socket_channel
        )

        if not channel:
            return True

        try:

            if (
                self.sio is not None
                and self.sio.connected
            ):

                self.sio.emit(
                    "leave",
                    {
                        "channelName": channel
                    },
                )

        except Exception:

            pass

        self.subscriptions.discard(
            channel
        )

        return True

    # ========================================================
    # DISCONNECT
    # ========================================================

    def disconnect(self):

        self._stop_event.set()

        self.running = False

        self._unsubscribe_futures_market()

        try:

            if (
                self.sio is not None
                and self.sio.connected
            ):

                self.sio.disconnect()

        except Exception:

            pass

        self.connected = False

        self.subscriptions.clear()

        self._clear_queue()

        # ----------------------------------------------------
        # Do not join ourselves.
        # ----------------------------------------------------

        if (
            self.queue_thread
            and self.queue_thread.is_alive()
            and threading.current_thread()
            is not self.queue_thread
        ):

            self.queue_thread.join(
                timeout=2
            )

        if (
            self.socket_thread
            and self.socket_thread.is_alive()
            and threading.current_thread()
            is not self.socket_thread
        ):

            self.socket_thread.join(
                timeout=2
            )

        self.socket_thread = None

        self.queue_thread = None

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        self.disconnect()

    # ========================================================
    # INCOMING FUTURES MESSAGE
    # ========================================================

    def _handle_futures_market_message(
        self,
        data,
    ):

        self.received_ticks += 1

        receive_monotonic = (
            time.monotonic()
        )

        self.update_heartbeat()

        try:

            payload = data

            # ------------------------------------------------
            # JSON string payload
            # ------------------------------------------------

            if isinstance(
                payload,
                str,
            ):

                payload = json.loads(
                    payload
                )

            # ------------------------------------------------
            # Wrapped payload
            #
            # CoinDCX Futures may send:
            #
            # {
            #     "event": "new-trade",
            #     "data": "{\"T\":...,\"p\":\"4384.42\",...}"
            # }
            #
            # Therefore "data" may itself be a JSON string.
            # ------------------------------------------------

            if (
                isinstance(payload, dict)
                and "data" in payload
            ):

                payload = payload["data"]

            # ------------------------------------------------
            # Decode nested JSON string
            # ------------------------------------------------

            if isinstance(payload, str):

                try:

                    payload = json.loads(
                        payload
                    )

                except json.JSONDecodeError:

                    self.invalid_ticks += 1

                    self.logger.warning(
                        "Invalid nested Futures JSON payload: %s",
                        payload,
                    )

                    return

            # ------------------------------------------------
            # Normalize single/list payload
            # ------------------------------------------------

            items = (
                payload
                if isinstance(
                    payload,
                    list,
                )
                else [payload]
            )

            for item in items:

                tick = (
                    self._normalize_futures_tick(
                        item
                    )
                )

                if tick is None:

                    self.invalid_ticks += 1

                    continue

                # ------------------------------------------------
                # Internal latency marker.
                # Removed before external callback.
                # ------------------------------------------------

                tick[
                    "_receive_monotonic"
                ] = receive_monotonic

                self._queue_futures_tick(
                    tick
                )

        except Exception as exc:

            self.invalid_ticks += 1

            self.last_error = exc

            self.logger.exception(
                "Futures market message failed: %s",
                exc,
            )

    # ========================================================
    # NORMALIZE FUTURES TICK
    # ========================================================

    def _normalize_futures_tick(
        self,
        tick,
    ):

        if not isinstance(
            tick,
            dict,
        ):
            return None

        try:

            price = float(
                tick.get(
                    "p",
                    tick.get(
                        "price"
                    ),
                )
            )

            quantity = max(
                0.0,
                float(
                    tick.get(
                        "q",
                        tick.get(
                            "quantity",
                            0.0,
                        ),
                    )
                ),
            )

            timestamp = int(
                float(
                    tick.get(
                        "T",
                        tick.get(
                            "timestamp"
                        ),
                    )
                )
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):

            return None

        if price <= 0:
            return None

        # ----------------------------------------------------
        # Market identifier
        # ----------------------------------------------------

        market = tick.get(
            "s",
            tick.get(
                "symbol"
            ),
        )

        if market:

            incoming_market = (
                self._normalize_market_identifier(
                    market
                )
            )

            current_market = (
                self._normalize_market_identifier(
                    self.symbol
                )
            )

            if (
                incoming_market
                != current_market
            ):

                return None

        # ----------------------------------------------------
        # Canonical Futures tick
        # ----------------------------------------------------

        result = dict(
            tick
        )

        result.update({

            "p":
                price,

            "q":
                quantity,

            "T":
                timestamp,

            "symbol":
                self.symbol,

            "market_type":
                self.MARKET_TYPE,

            "exchange":
                self.EXCHANGE,
        })

        return result

    # ========================================================
    # MARKET IDENTIFIER NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_market_identifier(
        market,
    ):

        value = (
            str(
                market or ""
            )
            .strip()
            .upper()
        )

        # ----------------------------------------------------
        # Remove common separators
        # ----------------------------------------------------

        for separator in (
            "-",
            "_",
            "/",
        ):

            value = (
                value.replace(
                    separator,
                    "",
                )
            )

        # ----------------------------------------------------
        # Convert B-BTCUSDT style identifier
        # ----------------------------------------------------

        if (
            value.startswith("B")
            and value[1:]
            in {
                "BTCUSDT",
                "ETHUSDT",
                "XAUUSDT",
                "XAGUSDT",
            }
        ):

            value = value[1:]

        return value

    # ========================================================
    # DUPLICATE TICK PROTECTION
    # ========================================================

    def _is_duplicate_futures_tick(
        self,
        tick,
    ):

        key = (
            self.symbol,
            tick.get("T"),
            tick.get("p"),
            tick.get("q"),
        )

        previous = (
            self._last_tick_key.get(
                self.symbol
            )
        )

        if previous == key:

            return True

        self._last_tick_key[
            self.symbol
        ] = key

        return False

    # ========================================================
    # QUEUE FUTURES TICK
    # ========================================================

    def _queue_futures_tick(
        self,
        tick,
    ):

        # ----------------------------------------------------
        # Duplicate protection BEFORE controller delivery.
        # ----------------------------------------------------

        if self._is_duplicate_futures_tick(
            tick
        ):

            self.duplicate_ticks += 1

            return False

        # ====================================================
        # CRITICAL AUTHORITY PATH
        #
        # WebSocket tick
        #       ↓
        # Controller
        #
        # This happens BEFORE queue processing.
        #
        # Therefore:
        #
        # Live price latency does NOT depend on:
        #     - candle building
        #     - SignalEngine
        #     - chart
        #     - queue worker
        # ====================================================

        self._notify_controller_tick(
            tick
        )

        # ----------------------------------------------------
        # Queue for candle processing.
        # ----------------------------------------------------

        try:

            self.tick_queue.put_nowait(
                tick
            )

            return True

        except queue.Full:

            self.dropped_ticks += 1

            self.logger.warning(
                "Futures tick queue full. "
                "Tick dropped."
            )

            return False

    # ========================================================
    # RAW FUTURES TRADE EVENT
    # ========================================================

    def _on_futures_new_trade(
        self,
        data,
    ):

        print(
            "\n"
            "========== FUTURES RAW TRADE "
            "=========="
        )

        print(
            "WebSocket Symbol :",
            self.symbol,
        )

        print(
            "Channel          :",
            self.socket_channel,
        )

        print(
            "Raw Data Type    :",
            type(data),
        )

        print(
            "Raw Data         :",
            data,
        )

        print(
            "========================================"
        )

        self._handle_futures_market_message(
            data
        )

    # ========================================================
    # END OF PART 2
    # ========================================================

    # ========================================================
    # TICK WORKER
    # ========================================================

    def _process_futures_tick_queue(self):

        while not self._stop_event.is_set():

            try:

                tick = self.tick_queue.get(
                    timeout=self.QUEUE_GET_TIMEOUT
                )

            except queue.Empty:

                continue

            try:

                self._process_futures_tick(
                    tick
                )

            except Exception as exc:

                self.last_error = exc

                self.logger.exception(
                    "Futures tick processing failed: %s",
                    exc,
                )

            finally:

                self.tick_queue.task_done()

    # ========================================================
    # PROCESS FUTURES TICK
    # ========================================================

    def _process_futures_tick(
        self,
        tick,
    ):

        if not isinstance(
            tick,
            dict,
        ):
            self.invalid_ticks += 1
            return None

        # ----------------------------------------------------
        # Timestamp
        # ----------------------------------------------------

        try:

            timestamp = (
                self._extract_futures_timestamp(
                    tick
                )
            )

        except Exception:

            self.invalid_ticks += 1

            return None

        # ----------------------------------------------------
        # Out-of-order protection
        # ----------------------------------------------------

        if (
            self._last_processed_timestamp
            is not None
            and timestamp
            < self._last_processed_timestamp
        ):

            self.invalid_ticks += 1

            return None

        self._last_processed_timestamp = (
            timestamp
        )

        # ----------------------------------------------------
        # Queue latency
        # ----------------------------------------------------

        receive_monotonic = (
            tick.get(
                "_receive_monotonic"
            )
        )

        if receive_monotonic is not None:

            try:

                queue_latency = max(
                    0.0,
                    (
                        time.monotonic()
                        - float(
                            receive_monotonic
                        )
                    )
                    * 1000.0,
                )

                self.last_queue_latency_ms = (
                    queue_latency
                )

                self.max_queue_latency_ms = max(
                    self.max_queue_latency_ms,
                    queue_latency,
                )

            except Exception:

                pass

        # ----------------------------------------------------
        # Exchange latency
        # ----------------------------------------------------

        exchange_latency = (
            self._calculate_exchange_latency(
                tick
            )
        )

        if exchange_latency is not None:

            self.last_exchange_latency_ms = (
                exchange_latency
            )

            self.max_exchange_latency_ms = max(
                self.max_exchange_latency_ms,
                exchange_latency,
            )

        # ----------------------------------------------------
        # Total latency
        # ----------------------------------------------------

        if receive_monotonic is not None:

            try:

                total_latency = max(
                    0.0,
                    (
                        time.monotonic()
                        - float(
                            receive_monotonic
                        )
                    )
                    * 1000.0,
                )

                self.last_total_latency_ms = (
                    total_latency
                )

                self.max_total_latency_ms = max(
                    self.max_total_latency_ms,
                    total_latency,
                )

                self.latency_samples += 1

            except Exception:

                pass

        # ----------------------------------------------------
        # Price
        # ----------------------------------------------------

        price = (
            self._extract_futures_price(
                tick
            )
        )

        if price is None:

            self.invalid_ticks += 1

            return None

        # ----------------------------------------------------
        # Volume
        # ----------------------------------------------------

        volume = (
            self._extract_futures_volume(
                tick
            )
        )

        # ====================================================
        # LIVE CANDLE BUILDER
        # ====================================================

        closed = (
            self.candle_builder.update_tick(
                price,
                volume,
                timestamp,
            )
        )

        self.processed_ticks += 1

        self.last_tick_time = (
            timestamp
        )

        # ----------------------------------------------------
        # Remove internal transport field
        # before external callbacks.
        # ----------------------------------------------------

        tick.pop(
            "_receive_monotonic",
            None,
        )

        # ====================================================
        # OPTIONAL EXTERNAL TICK CALLBACK
        #
        # IMPORTANT:
        #
        # Controller does NOT depend on this callback
        # for live price.
        #
        # Controller already received the tick inside:
        #
        #     _queue_futures_tick()
        #
        # ====================================================

        self._safe_callback(
            self.on_tick,
            tick,
        )

        # ====================================================
        # CURRENT LIVE CANDLE
        # ====================================================

        current = (
            self.candle_builder
            .get_current_candle()
        )

        if current is not None:

            # ------------------------------------------------
            # Controller live candle bridge
            # ------------------------------------------------

            self._notify_controller_candle(
                current
            )

            # ------------------------------------------------
            # Optional external callback
            # ------------------------------------------------

            self._safe_callback(
                self.on_candle,
                current,
            )

        # ====================================================
        # CLOSED CANDLE
        # ====================================================

        closed_candle = (
            self._resolve_closed_candle(
                closed
            )
        )

        if closed_candle is not None:

            # ------------------------------------------------
            # Controller closed-candle bridge
            #
            # EXACTLY ONCE from this processing path.
            # ------------------------------------------------

            self._notify_controller_closed_candle(
                closed_candle
            )

            # ------------------------------------------------
            # Optional external callback
            # ------------------------------------------------

            self._safe_callback(
                self.on_candle_closed,
                closed_candle,
            )

        return closed_candle

    # ========================================================
    # RESOLVE CLOSED CANDLE
    # ========================================================

    def _resolve_closed_candle(
        self,
        closed,
    ):

        """
        Supports two LiveCandleBuilder contracts:

        1. update_tick() returns Candle
        2. update_tick() returns True/False while the builder
           exposes get_last_closed_candle()

        A defensive fallback is also used.
        """

        # ----------------------------------------------------
        # Direct Candle return
        # ----------------------------------------------------

        if closed is not None:

            if (
                hasattr(
                    closed,
                    "timestamp",
                )
                and hasattr(
                    closed,
                    "close",
                )
            ):

                return closed

            # ------------------------------------------------
            # Boolean close notification
            # ------------------------------------------------

            if closed is True:

                try:

                    return (
                        self.candle_builder
                        .get_last_closed_candle()
                    )

                except Exception:

                    return None

        # ----------------------------------------------------
        # Defensive fallback
        # ----------------------------------------------------

        try:

            candidate = (
                self.candle_builder
                .get_last_closed_candle()
            )

            if candidate is None:
                return None

            current = (
                self.candle_builder
                .get_current_candle()
            )

            # ------------------------------------------------
            # Do not return current candle as closed candle.
            # ------------------------------------------------

            if (
                current is not None
                and hasattr(
                    current,
                    "timestamp",
                )
                and hasattr(
                    candidate,
                    "timestamp",
                )
                and current.timestamp
                == candidate.timestamp
            ):

                return None

            return candidate

        except Exception:

            return None

    # ========================================================
    # EXTRACT PRICE
    # ========================================================

    @staticmethod
    def _extract_futures_price(
        tick,
    ):

        if not isinstance(
            tick,
            dict,
        ):
            return None

        try:

            price = float(
                tick.get(
                    "p",
                    tick.get(
                        "price"
                    ),
                )
            )

            if price <= 0:
                return None

            return price

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):

            return None

    # ========================================================
    # EXTRACT VOLUME
    # ========================================================

    @staticmethod
    def _extract_futures_volume(
        tick,
    ):

        if not isinstance(
            tick,
            dict,
        ):
            return 0.0

        try:

            return max(
                0.0,
                float(
                    tick.get(
                        "q",
                        tick.get(
                            "quantity",
                            0.0,
                        ),
                    )
                ),
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):

            return 0.0

    # ========================================================
    # EXTRACT TIMESTAMP
    # ========================================================

    @staticmethod
    def _extract_futures_timestamp(
        tick,
    ):

        if not isinstance(
            tick,
            dict,
        ):
            raise ValueError(
                "Invalid Futures tick."
            )

        value = float(
            tick.get(
                "T",
                tick.get(
                    "timestamp"
                ),
            )
        )

        if value > 10_000_000_000:

            value /= 1000.0

        return datetime.fromtimestamp(
            value,
            tz=timezone.utc,
        )

    # ========================================================
    # CONTROLLER LIVE PRICE BRIDGE
    # ========================================================

    def _notify_controller_tick(
        self,
        tick,
    ):

        controller = self.controller

        if controller is None:
            return

        callback = getattr(
            controller,
            "on_futures_live_tick",
            None,
        )

        if not callable(callback):
            return

        # ----------------------------------------------------
        # Controller callback is protected.
        #
        # A UI/controller exception must NEVER kill
        # the WebSocket receive path.
        # ----------------------------------------------------

        self._safe_callback(
            callback,
            tick,
        )

    # ========================================================
    # CONTROLLER LIVE CANDLE BRIDGE
    # ========================================================

    def _notify_controller_candle(
        self,
        candle,
    ):

        if (
            self.controller is None
            or candle is None
        ):
            return

        callback = getattr(
            self.controller,
            "on_futures_live_candle",
            None,
        )

        if not callable(callback):
            return

        self._safe_callback(
            callback,
            candle,
        )

    # ========================================================
    # CONTROLLER CLOSED CANDLE BRIDGE
    # ========================================================

    def _notify_controller_closed_candle(
        self,
        candle,
    ):

        if (
            self.controller is None
            or candle is None
        ):
            return

        callback = getattr(
            self.controller,
            "on_futures_candle_closed",
            None,
        )

        if not callable(callback):
            return

        self._safe_callback(
            callback,
            candle,
        )

    # ========================================================
    # QUEUE CLEAR
    # ========================================================

    def _clear_queue(self):

        try:

            while True:

                self.tick_queue.get_nowait()

                self.tick_queue.task_done()

        except queue.Empty:

            pass

    # ========================================================
    # START TICK WORKER
    # ========================================================

    def _start_tick_worker(self):

        if (
            self.queue_thread
            and self.queue_thread.is_alive()
        ):

            return

        self.queue_thread = (
            threading.Thread(
                target=(
                    self._process_futures_tick_queue
                ),
                name=(
                    "CoinDCXFuturesTickQueue"
                ),
                daemon=True,
            )
        )

        self.queue_thread.start()

    # ========================================================
    # STOP TICK WORKER
    # ========================================================

    def _stop_tick_worker(self):

        if (
            self.queue_thread
            and self.queue_thread.is_alive()
            and threading.current_thread()
            is not self.queue_thread
        ):

            self.queue_thread.join(
                timeout=2
            )

    # ========================================================
    # WORKER STATUS
    # ========================================================

    def futures_worker_running(self):

        return bool(
            self.queue_thread
            and self.queue_thread.is_alive()
        )

    # ========================================================
    # MARKET SUBSCRIPTION STATUS
    # ========================================================

    def market_subscription_active(self):

        return bool(
            self.socket_channel
            and self.socket_channel
            in self.subscriptions
        )

    # ========================================================
    # CONTROLLER STATUS
    # ========================================================

    def controller_attached(self):

        return (
            self.controller is not None
        )

    # ========================================================
    # CURRENT FUTURES CANDLE PRICE
    # ========================================================

    def get_current_futures_price(self):

        candle = (
            self.candle_builder
            .get_current_candle()
        )

        if candle is None:
            return None

        try:

            return float(
                candle.close
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    # ========================================================
    # TEST TICK INJECTION
    # ========================================================

    def inject_test_futures_tick(
        self,
        tick,
    ):

        normalized = (
            self._normalize_futures_tick(
                tick
            )
        )

        if normalized is None:

            self.invalid_ticks += 1

            return False

        normalized[
            "_receive_monotonic"
        ] = time.monotonic()

        return self._queue_futures_tick(
            normalized
        )

    # ========================================================
    # LATENCY STATISTICS
    # ========================================================

    def get_latency_statistics(self):

        return {

            "last_exchange_latency_ms":
                self.last_exchange_latency_ms,

            "last_queue_latency_ms":
                self.last_queue_latency_ms,

            "last_total_latency_ms":
                self.last_total_latency_ms,

            "max_exchange_latency_ms":
                self.max_exchange_latency_ms,

            "max_queue_latency_ms":
                self.max_queue_latency_ms,

            "max_total_latency_ms":
                self.max_total_latency_ms,

            "latency_samples":
                self.latency_samples,
        }

    # ========================================================
    # SOCKET STATUS
    # ========================================================

    def get_socket_status(self):

        sio_connected = bool(
            self.sio
            and getattr(
                self.sio,
                "connected",
                False,
            )
        )

        return {

            "provider":
                self.PROVIDER_NAME,

            "version":
                self.VERSION,

            "market_type":
                self.MARKET_TYPE,

            "symbol":
                self.symbol,

            "timeframe":
                self.timeframe,

            "channel":
                self.socket_channel,

            "running":
                self.running,

            "connected":
                self.connected,

            "sio_connected":
                sio_connected,

            "connection_healthy":
                self.is_connection_healthy(),

            "subscription_active":
                self.market_subscription_active(),

            "controller_attached":
                self.controller_attached(),

            "worker_running":
                self.futures_worker_running(),

            "queue_size":
                self.queue_size(),

            "received_ticks":
                self.received_ticks,

            "processed_ticks":
                self.processed_ticks,

            "duplicate_ticks":
                self.duplicate_ticks,

            "dropped_ticks":
                self.dropped_ticks,

            "invalid_ticks":
                self.invalid_ticks,

            "callback_errors":
                self.callback_errors,

            "last_tick_time": (
                self.last_tick_time.isoformat()
                if self.last_tick_time
                else None
            ),

            "heartbeat_age":
                self.heartbeat_age(),

            "last_error": (
                str(self.last_error)
                if self.last_error
                else None
            ),
        }

    # ========================================================
    # HEALTH REPORT
    # ========================================================

    def health_report(self):

        return {

            **self.get_socket_status(),

            "connection_time": (
                self.connection_time.isoformat()
                if self.connection_time
                else None
            ),

            "last_message_time":
                self.last_message_time,

            "subscriptions":
                list(
                    self.subscriptions
                ),

            "reconnect_attempts":
                self.reconnect_attempts,

            "reconnect_delay":
                self.reconnect_delay,

            "candle_builder":
                self.candle_builder.snapshot(),

            "latency":
                self.get_latency_statistics(),
        }

    # ========================================================
    # PIPELINE STATUS
    # ========================================================

    def pipeline_status(self):

        current_candle = (
            self.candle_builder
            .get_current_candle()
        )

        closed_candle = (
            self.candle_builder
            .get_last_closed_candle()
        )

        return {

            **self.get_socket_status(),

            "controller_attached":
                self.controller_attached(),

            "current_price":
                self.get_current_futures_price(),

            "current_candle":
                current_candle,

            "last_closed_candle":
                closed_candle,

            "latency":
                self.get_latency_statistics(),
        }

    # ========================================================
    # TIMEFRAME
    # ========================================================

    def set_timeframe(
        self,
        timeframe,
    ):

        try:

            tf = (
                str(timeframe)
                .strip()
            )

            if not tf:
                return False

            if tf == self.timeframe:
                return True

            self.timeframe = tf

            self.candle_builder.set_timeframe(
                tf
            )

            self._last_processed_timestamp = (
                None
            )

            self._clear_queue()

            self.logger.info(
                "Futures WebSocket timeframe "
                "changed to %s",
                tf,
            )

            return True

        except Exception as exc:

            self.last_error = exc

            self.logger.exception(
                "Failed to change Futures "
                "WebSocket timeframe: %s",
                exc,
            )

            return False

    # ========================================================
    # LOG SOCKET STATUS
    # ========================================================

    def log_socket_status(self):

        self.logger.info(
            "FUTURES SOCKET STATUS: %s",
            self.get_socket_status(),
        )

    # ========================================================
    # LOG PIPELINE STATUS
    # ========================================================

    def log_pipeline_status(self):

        self.logger.info(
            "FUTURES PIPELINE STATUS: %s",
            self.pipeline_status(),
        )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self):

        return (
            "CoinDCXFuturesWebSocket("
            f"symbol='{self.symbol}', "
            f"timeframe='{self.timeframe}', "
            f"connected={self.connected}, "
            f"running={self.running}"
            ")"
        )