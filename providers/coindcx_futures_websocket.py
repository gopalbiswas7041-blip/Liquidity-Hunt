"""
Liquidity Hunter AI
CoinDCX Futures Socket.IO Engine V20.9.4
Low-Latency Futures Tick Authority

Architecture
------------
Socket ingress
    |
    +--> Controller live price IMMEDIATE
    |
    +--> Tick queue
            |
            +--> Candle Builder
                    |
                    +--> Controller live candle
                    +--> Closed candle analysis
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

from providers.live_candle_builder import (
    LiveCandleBuilder,
)

from utils.logger import get_logger


class CoinDCXFuturesWebSocket:

    PROVIDER_NAME = (
        "CoinDCX Futures WebSocket"
    )

    VERSION = "V20.9.4"

    MARKET_TYPE = "FUTURES"

    EXCHANGE = "CoinDCX"

    DEFAULT_SOCKET_URL = (
        "https://stream.coindcx.com"
    )

    DEFAULT_TIMEFRAME = "1m"

    DEFAULT_SYMBOL = "B-BTC_USDT"

    SOCKET_CHANNEL_SUFFIX = "@trades"

    WAIT_TIMEOUT = 20

    RECONNECT_DELAY = 5

    MAX_RECONNECT_DELAY = 60

    HEARTBEAT_TIMEOUT = 30

    QUEUE_SIZE = 5000

    QUEUE_GET_TIMEOUT = 0.5

    SUPPORTED_SYMBOLS = [
        "B-BTC_USDT",
        "B-ETH_USDT",
        "B-XAU_USDT",
        "B-XAG_USDT",
    ]

    def __init__(
        self,
        timeframe="1m",
        symbol=DEFAULT_SYMBOL,
    ):

        self.logger = get_logger(
            self.__class__.__name__
        )

        if not self.logger.handlers:

            handler = (
                logging.StreamHandler()
            )

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

        # ==================================================
        # LOCK / STOP
        # ==================================================

        self._lock = (
            threading.RLock()
        )

        self._stop_event = (
            threading.Event()
        )

        # ==================================================
        # SYMBOL
        # ==================================================

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
                f"WebSocket symbol: {self.symbol}"
            )

        # ==================================================
        # SOCKET
        # ==================================================

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

        self.reconnect_attempts = 0

        self.reconnect_delay = (
            self.RECONNECT_DELAY
        )

        self.subscriptions = set()

        # ==================================================
        # QUEUE
        # ==================================================

        self.tick_queue = queue.Queue(
            maxsize=self.QUEUE_SIZE
        )

        self.socket_thread = None

        self.queue_thread = None

        # ==================================================
        # CANDLE BUILDER
        # ==================================================

        self.candle_builder = (
            LiveCandleBuilder(
                timeframe=timeframe
            )
        )

        # ==================================================
        # BRIDGES
        # ==================================================

        self.controller = None

        self.chart_widget = None

        # ==================================================
        # CALLBACKS
        # ==================================================

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

        # ==================================================
        # TICK PROTECTION
        # ==================================================

        self._last_tick_key = {}

        self._last_processed_timestamp = None

        self._events_registered = False

        # ==================================================
        # STATISTICS
        # ==================================================

        self.received_ticks = 0

        self.processed_ticks = 0

        self.dropped_ticks = 0

        self.duplicate_ticks = 0

        self.invalid_ticks = 0

        self.callback_errors = 0

        # ==================================================
        # LATENCY
        # ==================================================

        self.last_exchange_latency_ms = None

        self.last_queue_latency_ms = None

        self.last_total_latency_ms = None

        self.max_exchange_latency_ms = 0.0

        self.max_queue_latency_ms = 0.0

        self.max_total_latency_ms = 0.0

        self.latency_samples = 0

    # ======================================================
    # SYMBOL NORMALIZATION
    # ======================================================

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

    @classmethod
    def validate_symbol(
        cls,
        symbol,
    ):

        return (
            cls.normalize_symbol(
                symbol
            )
            in cls.SUPPORTED_SYMBOLS
        )

    # ======================================================
    # SYMBOL
    # ======================================================

    def set_symbol(
        self,
        symbol,
    ):

        symbol = (
            self.normalize_symbol(
                symbol
            )
        )

        if not self.validate_symbol(
            symbol
        ):

            raise ValueError(
                "Unsupported Futures "
                f"WebSocket symbol: {symbol}"
            )

        with self._lock:

            self.symbol = symbol

            self.socket_channel = None

            self._last_tick_key.clear()

            self._last_processed_timestamp = None

            self.subscriptions.clear()

            self._clear_queue()

            self.candle_builder.reset()

        return True

    def get_symbol(self):

        return self.symbol

    def get_trade_channel(
        self,
        symbol=None,
    ):

        return (
            self.normalize_symbol(
                symbol
                or self.symbol
            )
            + self.SOCKET_CHANNEL_SUFFIX
        )

    # ======================================================
    # CONTROLLER
    # ======================================================

    def set_controller(
        self,
        controller,
    ):

        self.controller = controller

        return True

    attach_controller = set_controller

    def set_chart_widget(
        self,
        chart_widget,
    ):

        self.chart_widget = (
            chart_widget
        )

    # ======================================================
    # CALLBACKS
    # ======================================================

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

        self.on_candle_closed = (
            callback
        )

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

    # ======================================================
    # SAFE CALLBACK
    # ======================================================

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

    # ======================================================
    # STATUS
    # ======================================================

    def stop_requested(self):

        return self._stop_event.is_set()

    def is_connected(self):

        return bool(
            self.connected
        )

    def is_running(self):

        return bool(
            self.running
        )

    def is_alive(self):

        return (
            self.running
            and self.connected
        )

    # ======================================================
    # HEARTBEAT
    # ======================================================

    def update_heartbeat(self):

        now = time.time()

        self.last_heartbeat = now

        self.last_message_time = now

    def heartbeat_age(self):

        if self.last_heartbeat is None:

            return None

        return (
            time.time()
            - self.last_heartbeat
        )

    def is_connection_healthy(self):

        age = (
            self.heartbeat_age()
        )

        return bool(
            self.connected
            and (
                age is None
                or age <= self.HEARTBEAT_TIMEOUT
            )
        )

    # ======================================================
    # QUEUE
    # ======================================================

    def queue_size(self):

        return self.tick_queue.qsize()

    # ======================================================
    # CANDLE
    # ======================================================

    def current_candle(self):

        return (
            self.candle_builder
            .get_current_candle()
        )

    def last_closed_candle(self):

        return (
            self.candle_builder
            .get_last_closed_candle()
        )

    # ======================================================
    # TIMESTAMP
    # ======================================================

    @staticmethod
    def _timestamp_to_seconds(
        timestamp,
    ):

        try:

            value = float(
                timestamp
            )

            if (
                value
                > 10_000_000_000
            ):

                value /= 1000.0

            return value

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):

            return None

    # ======================================================
    # LATENCY
    # ======================================================

    def _calculate_exchange_latency(
        self,
        tick,
    ):

        ts = (
            self._timestamp_to_seconds(
                tick.get("T")
                if isinstance(
                    tick,
                    dict,
                )
                else None
            )
        )

        if ts is None:
            return None

        return max(
            0.0,
            (
                time.time()
                - ts
            )
            * 1000.0,
        )

    # ======================================================
    # SOCKET CLIENT
    # ======================================================

    def _initialize_socket_client(
        self,
    ):

        self.sio = socketio.Client(
            reconnection=False,
            logger=False,
            engineio_logger=False,
        )

    # ======================================================
    # CONNECT
    # ======================================================

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

            self.set_symbol(raw)

        self.socket_channel = (
            self.get_trade_channel()
        )

        self._initialize_socket_client()

        if not (
            self._register_all_futures_socket_events()
        ):

            return False

        self._stop_event.clear()

        self.running = True

        self.connected = False

        self.reconnect_attempts = 0

        self.reconnect_delay = (
            self.RECONNECT_DELAY
        )

        self._start_futures_tick_worker()

        self.socket_thread = threading.Thread(
            target=self._connection_worker,
            name="CoinDCXFuturesSocket",
            daemon=True,
        )

        self.socket_thread.start()

        return True

    # ======================================================
    # CONNECTION WORKER
    # ======================================================

    def _connection_worker(self):

        while not self._stop_event.is_set():

            try:

                self.sio.connect(
                    self.socket_url,
                    transports=[
                        "websocket"
                    ],
                    wait=True,
                    wait_timeout=self.WAIT_TIMEOUT,
                )

                self.sio.wait()

            except Exception as exc:

                if self._stop_event.is_set():
                    break

                self.last_error = exc

                self.reconnect_attempts += 1

                self.connected = False

                self.logger.warning(
                    "Futures Socket.IO "
                    "connection failed: %s",
                    exc,
                )

            if self._stop_event.is_set():
                break

            self.connected = False

            if self._stop_event.wait(
                self.reconnect_delay
            ):

                break

            self.reconnect_delay = min(
                self.reconnect_delay * 2,
                self.MAX_RECONNECT_DELAY,
            )

        self.running = False

    # ======================================================
    # SOCKET EVENTS
    # ======================================================

    def _register_socket_events(
        self,
    ):

        if (
            self._events_registered
            or self.sio is None
        ):

            return self.sio is not None

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

            self._subscribe_futures_market()

            self._safe_callback(
                self.on_connected
            )

            self.logger.info(
                "Futures WebSocket connected: %s",
                self.symbol,
            )

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

        @self.sio.event
        def connect_error(error):

            self.connected = False

            self.last_error = error

        self._events_registered = True

        return True

    # ======================================================
    # MARKET EVENTS
    # ======================================================

    def _register_futures_market_events(
        self,
    ):

        @self.sio.on("new-trade")
        def _on_new_trade(data):

            self._on_futures_new_trade(
                data
            )

        return True

    def _register_all_futures_socket_events(
        self,
    ):

        return (
            self._register_socket_events()
            and
            self._register_futures_market_events()
        )

    # ======================================================
    # SUBSCRIBE
    # ======================================================

    def _subscribe_futures_market(
        self,
    ):

        if not self.connected:
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
                }
            )

            print(
                "\n========== FUTURES SUBSCRIPTION =========="
            )

            print(
                "Futures Symbol :",
                self.symbol
            )

            print(
                "Trade Channel  :",
                channel
            )

            print(
                "Subscription   :",
                "JOIN SENT"
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

            return False

    # ======================================================
    # UNSUBSCRIBE
    # ======================================================

    def _unsubscribe_futures_market(
        self,
    ):

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
                        "channelName":
                            channel
                    },
                )

        except Exception:
            pass

        self.subscriptions.discard(
            channel
        )

        return True

    # ======================================================
    # DISCONNECT
    # ======================================================

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

    def close(self):

        self.disconnect()

    # ======================================================
    # INCOMING MARKET MESSAGE
    # ======================================================

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

            if isinstance(
                payload,
                str,
            ):

                payload = json.loads(
                    payload
                )

            if (
                isinstance(
                    payload,
                    dict,
                )
                and "data" in payload
            ):

                payload = payload["data"]

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
                "Futures market "
                "message failed: %s",
                exc,
            )

    # ======================================================
    # NORMALIZE TICK
    # ======================================================

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

        market = tick.get(
            "s",
            tick.get(
                "symbol"
            ),
        )

        if (
            market
            and
            self._normalize_market_identifier(
                market
            )
            !=
            self._normalize_market_identifier(
                self.symbol
            )
        ):

            return None

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

    # ======================================================
    # MARKET IDENTIFIER
    # ======================================================

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

        for separator in (
            "-",
            "_",
            "/",
        ):

            value = value.replace(
                separator,
                "",
            )

        if (
            value.startswith("B")
            and
            value[1:]
            in {
                "BTCUSDT",
                "ETHUSDT",
                "XAUUSDT",
                "XAGUSDT",
            }
        ):

            value = value[1:]

        return value

    # ======================================================
    # DUPLICATE
    # ======================================================

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

        if (
            self._last_tick_key.get(
                self.symbol
            )
            == key
        ):

            return True

        self._last_tick_key[
            self.symbol
        ] = key

        return False

    # ======================================================
    # QUEUE
    # ======================================================

    def _queue_futures_tick(
        self,
        tick,
    ):

        if self._is_duplicate_futures_tick(
            tick
        ):

            self.duplicate_ticks += 1

            return False

        # ==================================================
        # CRITICAL
        #
        # LIVE PRICE FIRST
        #
        # No queue.
        # No candle builder.
        # No AI.
        # ==================================================

        self._notify_controller_tick(
            tick
        )

        try:

            self.tick_queue.put_nowait(
                tick
            )

            return True

        except queue.Full:

            self.dropped_ticks += 1

            return False

    # ======================================================
    # NEW TRADE
    # ======================================================

    def _on_futures_new_trade(self, data):

        # ======================================================
        # FUTURES RAW TRADE DEBUG
        # ======================================================

        print(
            "\n========== FUTURES RAW TRADE =========="
        )

        print(
            "WebSocket Symbol :",
            self.symbol
        )

        print(
            "Channel          :",
            self.socket_channel
        )

        print(
            "Raw Data Type    :",
            type(data)
        )

        print(
            "Raw Data         :",
            data
        )

        print(
            "========================================"
        )

        self._handle_futures_market_message(
            data
        )

    # ======================================================
    # WORKER
    # ======================================================

    def _process_futures_tick_queue(
        self,
    ):

        while not self._stop_event.is_set():

            try:

                tick = (
                    self.tick_queue.get(
                        timeout=self.QUEUE_GET_TIMEOUT
                    )
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

    # ======================================================
    # PROCESS TICK
    # ======================================================

    def _process_futures_tick(
        self,
        tick,
    ):

        timestamp = (
            self._extract_futures_timestamp(
                tick
            )
        )

        if (
            self._last_processed_timestamp
            is not None
            and
            timestamp
            < self._last_processed_timestamp
        ):

            self.invalid_ticks += 1

            return None

        self._last_processed_timestamp = (
            timestamp
        )

        receive = tick.get(
            "_receive_monotonic"
        )

        if receive is not None:

            self.last_queue_latency_ms = max(
                0.0,
                (
                    time.monotonic()
                    - float(receive)
                )
                * 1000.0,
            )

            self.max_queue_latency_ms = max(
                self.max_queue_latency_ms,
                self.last_queue_latency_ms,
            )

        exchange = (
            self._calculate_exchange_latency(
                tick
            )
        )

        if exchange is not None:

            self.last_exchange_latency_ms = (
                exchange
            )

            self.max_exchange_latency_ms = max(
                self.max_exchange_latency_ms,
                exchange,
            )

        if receive is not None:

            self.last_total_latency_ms = max(
                0.0,
                (
                    time.monotonic()
                    - float(receive)
                )
                * 1000.0,
            )

            self.max_total_latency_ms = max(
                self.max_total_latency_ms,
                self.last_total_latency_ms,
            )

            self.latency_samples += 1

        price = self._extract_futures_price(tick)
        if price is None:
            self.invalid_ticks += 1
            return None

        volume = self._extract_futures_volume(tick)

        closed = self.candle_builder.update_tick(
            price,
            volume,
            timestamp
        )

        self.processed_ticks += 1
        self.last_tick_time = timestamp

        tick.pop("_receive_monotonic", None)

        self._safe_callback(
            self.on_tick,
            tick
        )

        # ==================================================
        # DEBUG: FUTURES CANDLE → CONTROLLER
        # ==================================================

        current = (
            self.candle_builder.get_current_candle()
        )

        print(
            "🔥 FUTURES WS CANDLE:",
            self.symbol,
            current
        )

        self._notify_controller_candle(
            current
        )

        print(
            "🔥 FUTURES WS → CONTROLLER DONE:",
            self.symbol
        )

        if current is not None:
            self._safe_callback(
                self.on_candle,
                current
            )

    # ======================================================
    # EXTRACT PRICE
    # ======================================================

    @staticmethod
    def _extract_futures_price(
        tick,
    ):

        try:

            price = float(
                tick.get(
                    "p",
                    tick.get(
                        "price"
                    ),
                )
            )

            return (
                price
                if price > 0
                else None
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    # ======================================================
    # EXTRACT VOLUME
    # ======================================================

    @staticmethod
    def _extract_futures_volume(
        tick,
    ):

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
        ):

            return 0.0

    # ======================================================
    # EXTRACT TIMESTAMP
    # ======================================================

    @staticmethod
    def _extract_futures_timestamp(
        tick,
    ):

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

    # ======================================================
    # CONTROLLER PRICE
    # ======================================================

    def _notify_controller_tick(
        self,
        tick,
    ):

        if self.controller is None:
            return

        callback = getattr(
            self.controller,
            "on_futures_live_tick",
            None,
        )

        if callback:

            self._safe_callback(
                callback,
                tick,
            )

    # ======================================================
    # CONTROLLER CANDLE
    # ======================================================

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

        if callback:

            self._safe_callback(
                callback,
                candle,
            )

    # ======================================================
    # CONTROLLER CLOSED CANDLE
    # ======================================================

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

        if callback:

            self._safe_callback(
                callback,
                candle,
            )

    # ======================================================
    # QUEUE CLEAR
    # ======================================================

    def _clear_queue(self):

        try:

            while True:

                self.tick_queue.get_nowait()

                self.tick_queue.task_done()

        except queue.Empty:

            pass

    # ======================================================
    # WORKER START
    # ======================================================

    def _start_futures_tick_worker(
        self,
    ):

        if (
            self.queue_thread
            and self.queue_thread.is_alive()
        ):

            return

        self.queue_thread = threading.Thread(
            target=self._process_futures_tick_queue,
            name="CoinDCXFuturesTickQueue",
            daemon=True,
        )

        self.queue_thread.start()

    # ======================================================
    # WORKER STATUS
    # ======================================================

    def _stop_futures_tick_worker(
        self,
    ):

        if (
            self.queue_thread
            and self.queue_thread.is_alive()
            and
            threading.current_thread()
            is not self.queue_thread
        ):

            self.queue_thread.join(
                timeout=2
            )

    def futures_worker_running(
        self,
    ):

        return bool(
            self.queue_thread
            and self.queue_thread.is_alive()
        )

    # ======================================================
    # STATUS
    # ======================================================

    def market_subscription_active(
        self,
    ):

        return bool(
            self.socket_channel
            and
            self.socket_channel
            in self.subscriptions
        )

    def controller_attached(
        self,
    ):

        return (
            self.controller is not None
        )

    def get_current_futures_price(
        self,
    ):

        candle = (
            self.candle_builder
            .get_current_candle()
        )

        if candle is None:

            return None

        return float(
            candle.close
        )

    # ======================================================
    # TEST TICK
    # ======================================================

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

        return (
            self._queue_futures_tick(
                normalized
            )
        )

    # ======================================================
    # LATENCY
    # ======================================================

    def get_latency_statistics(
        self,
    ):

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

    # ======================================================
    # SOCKET STATUS
    # ======================================================

    def get_socket_status(
        self,
    ):

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

            "last_tick_time":
                (
                    self.last_tick_time.isoformat()
                    if self.last_tick_time
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
    # HEALTH
    # ======================================================

    def health_report(
        self,
    ):

        return {

            **self.get_socket_status(),

            "timeframe":
                self.candle_builder.timeframe,

            "connection_time":
                (
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

            "latency":
                self.get_latency_statistics(),
        }

    # ======================================================
    # PIPELINE
    # ======================================================

    def pipeline_status(
        self,
    ):

        return {

            **self.get_socket_status(),

            "controller_attached":
                self.controller_attached(),

            "current_price":
                self.get_current_futures_price(),

            "latency":
                self.get_latency_statistics(),
        }

    # ======================================================
    # TIMEFRAME
    # ======================================================

    def set_timeframe(
        self,
        timeframe,
    ):

        try:

            self.candle_builder.set_timeframe(
                timeframe
            )

            self._last_processed_timestamp = (
                None
            )

            self._clear_queue()

            return True

        except Exception as exc:

            self.last_error = exc

            return False

    # ======================================================
    # LOG
    # ======================================================

    def log_socket_status(
        self,
    ):

        self.logger.info(
            "FUTURES SOCKET STATUS: %s",
            self.get_socket_status(),
        )

    def log_pipeline_status(
        self,
    ):

        self.logger.info(
            "FUTURES PIPELINE STATUS: %s",
            self.pipeline_status(),
        )

    # ======================================================
    # REPRESENTATION
    # ======================================================

    def __repr__(self):

        return (
            "CoinDCXFuturesWebSocket("
            f"symbol='{self.symbol}', "
            f"timeframe="
            f"'{self.candle_builder.timeframe}', "
            f"connected={self.connected}, "
            f"running={self.running}"
            ")"
        )