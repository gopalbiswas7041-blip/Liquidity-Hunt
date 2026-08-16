"""
Liquidity Hunter AI
Controller V20.9.8
Futures Authoritative Live Synchronization Edition

Architecture
------------
Historical Data:
    CoinDCX Futures REST

Live Price:
    CoinDCX Futures WebSocket

Live Candle:
    CoinDCX Futures WebSocket
    -> LiveCandleBuilder

Controller:
    Futures WebSocket is authoritative.
    REST is bootstrap/historical only.

Flow:
    Futures Tick
        ↓
    on_futures_live_tick()
        ↓
    current_price
        ↓
    Dashboard

    Futures Tick
        ↓
    LiveCandleBuilder
        ↓
    on_futures_live_candle()
        ↓
    Chart
        ↓
    live_data_5m
        ↓
    Closed Candle
        ↓
    SignalEngine
        ↓
    TradeManager

V20.9.5 fixes
-------------
1. Closed Futures candle is now explicitly forwarded to Controller.
2. Live candle is no longer delivered twice through Controller paths.
3. Controller no longer relies on a second candle callback registration
   when the Futures WebSocket controller bridge is active.
4. WebSocket remains the sole live-price authority after first valid tick.
5. Chart/Dashboard failures can never break the market-data pipeline.
6. Qt widgets are updated only through queued GUI-thread signals.
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass
from datetime import datetime, timezone

from PySide6.QtCore import QObject, Signal, Slot, Qt

import pandas as pd

from data.market_data import MarketData
from strategy.signal_engine import SignalEngine
from strategy.trade_manager import TradeManager
from indicators.atr import ATR

from providers.coindcx_provider import CoinDCXProvider
from providers.coindcx_futures_provider import CoinDCXFuturesProvider
from providers.coindcx_websocket import CoinDCXWebSocket
from providers.coindcx_futures_websocket import CoinDCXFuturesWebSocket

from utils.candle_sync import CandleSync


# ============================================================
# CONTROLLER CONFIG
# ============================================================

@dataclass
class ControllerConfig:

    DEFAULT_SYMBOL = "B-BTC_USDT"

    DEFAULT_TIMEFRAME = "5m"

    HIGHER_TIMEFRAME = "15m"

    AUTO_REFRESH_SECONDS = 30

    ENABLE_PRICE_SYNC = True

    ENABLE_DYNAMIC_SYMBOL = True

    ENABLE_DYNAMIC_TIMEFRAME = True

    ENABLE_WATCHLIST = True

    SOCKET_URL = "https://stream.coindcx.com"

    SOCKET_CHANNEL_SUFFIX = "@trades"

    ENABLE_CLOSED_CANDLE_ANALYSIS = True

    MARKET_TIMEZONE = "Asia/Kolkata"

    MAX_CANDLE_HISTORY = 1000


# ============================================================
# CONTROLLER
# ============================================================

class Controller(QObject):

    # =========================================================
    # THREAD-SAFE QT SIGNALS
    # =========================================================

    # These signals are emitted from the Socket.IO background
    # thread and delivered to Controller methods on the Qt GUI
    # thread. No Qt widget is touched from the WebSocket thread.
    futures_live_tick_signal = Signal(object)
    futures_live_candle_signal = Signal(object)
    futures_closed_candle_signal = Signal(object)

    def __init__(self):

        super().__init__()

        print("=" * 64)
        print("Liquidity Hunter AI")
        print("Controller V20.9.8")
        print("Futures Authoritative Live Synchronization")
        print("=" * 64)

        self.symbol = ControllerConfig.DEFAULT_SYMBOL
        self.timeframe = ControllerConfig.DEFAULT_TIMEFRAME
        self.higher_timeframe = ControllerConfig.HIGHER_TIMEFRAME

        # ----------------------------------------------------
        # Live market state
        # ----------------------------------------------------

        self.current_price = None
        self.last_refresh = None
        self.last_tick = None
        self.last_candle = None
        self.latest_signal = None
        self.latest_trade = None
        self.latest_result = {}

        # ----------------------------------------------------
        # FUTURES LIVE PRICE AUTHORITY
        # ----------------------------------------------------

        self._futures_live_price_initialized = False
        self._last_futures_tick_timestamp = None
        self._last_futures_ws_price = None

        # ----------------------------------------------------
        # Live DataFrames
        # ----------------------------------------------------

        self.live_data_5m = None
        self.live_data_15m = None

        # ----------------------------------------------------
        # Closed candle state
        # ----------------------------------------------------

        self.last_processed_closed_time = None
        self._live_candle_seed_timestamp = None

        # ----------------------------------------------------
        # Chart state
        # ----------------------------------------------------

        self._chart_data_loaded = False
        self._chart_loaded_symbol = None
        self._chart_loaded_timeframe = None
        self._chart_loaded_last_timestamp = None
        self._force_chart_reload = True

        # ----------------------------------------------------
        # Providers / Engines
        # ----------------------------------------------------

        self.provider = CoinDCXProvider()
        self.futures_provider = None
        self.market = None

        self.signal_engine = SignalEngine()
        self.trade_manager = TradeManager()
        self.atr = ATR()
        self.candle_sync = CandleSync()

        # ----------------------------------------------------
        # WebSockets
        # ----------------------------------------------------

        self.websocket = None
        self.futures_websocket = None

        # ----------------------------------------------------
        # UI references
        # ----------------------------------------------------

        self.dashboard = None
        self.chart_widget = None
        self.chart_overlay = None
        self.watchlist = None

        # ====================================================
        # THREAD-SAFE GUI SIGNAL CONNECTIONS
        # ====================================================

        self.futures_live_tick_signal.connect(
            self._handle_futures_live_tick_gui,
            Qt.QueuedConnection,
        )

        self.futures_live_candle_signal.connect(
            self._handle_futures_live_candle_gui,
            Qt.QueuedConnection,
        )

        self.futures_closed_candle_signal.connect(
            self._handle_futures_closed_candle_gui,
            Qt.QueuedConnection,
        )

        # ====================================================
        # FUTURES REST PROVIDER
        # ====================================================

        try:
            self.futures_provider = CoinDCXFuturesProvider(
                self.symbol
            )
            self.futures_provider.connect()
            print("✅ Futures REST Provider initialized")

        except Exception:
            print("❌ Futures REST Provider initialization failed")
            traceback.print_exc()

        # ====================================================
        # SPOT MARKET COMPATIBILITY
        # ====================================================

        try:
            self.market = MarketData(
                self.symbol,
                provider=self.provider
            )

        except Exception:
            traceback.print_exc()
            self.market = None

        # ====================================================
        # SPOT WEBSOCKET
        #
        # Compatibility only.
        # NEVER authoritative for Futures price.
        # ====================================================

        try:
            self.websocket = CoinDCXWebSocket(
                timeframe=self.timeframe
            )

            self.websocket.set_controller(self)

            self.websocket.set_tick_callback(
                self.on_live_tick
            )

            self.websocket.set_candle_callback(
                self.on_live_candle
            )

            self.websocket.set_candle_closed_callback(
                self.on_candle_closed
            )

        except Exception:
            traceback.print_exc()
            self.websocket = None

        # ====================================================
        # FUTURES WEBSOCKET
        # ====================================================

        try:
            self.futures_websocket = CoinDCXFuturesWebSocket(
                timeframe=self.timeframe,
                symbol=self.symbol,
            )

            self.futures_websocket.set_controller(self)

            self._bind_futures_websocket_callbacks()

        except Exception:
            print("❌ Futures WebSocket initialization failed")
            traceback.print_exc()
            self.futures_websocket = None

        # ====================================================
        # AUTHORITY LOG
        # ====================================================

        print("Historical Data Authority : FUTURES REST")
        print("Live Price Authority       : FUTURES WEBSOCKET")
        print("Live Candle Authority      : FUTURES WEBSOCKET")
        print("REST Live Price            : BOOTSTRAP ONLY")

    # =========================================================
    # FUTURES WEBSOCKET CALLBACK BINDING
    # =========================================================

    def _bind_futures_websocket_callbacks(self):

        """
        Futures WebSocket uses the Controller bridge as the
        authoritative path.

        Live price:
            WS -> Controller.on_futures_live_tick()

        Live candle:
            WS -> Controller.on_futures_live_candle()

        Closed candle:
            WS -> Controller.on_futures_candle_closed()

        We intentionally do NOT register the Controller methods
        again through the optional callback slots. Doing so would
        cause duplicate live-candle delivery because the Futures
        WebSocket already has set_controller(self).
        """

        ws = self.futures_websocket

        if ws is None:
            return False

        bound = []

        # -----------------------------------------------------
        # Controller bridge is the primary path.
        # -----------------------------------------------------

        try:
            ws.set_controller(self)
            bound.append("controller_bridge")
            print("✅ Futures Controller bridge bound")
        except Exception:
            traceback.print_exc()

        # -----------------------------------------------------
        # Optional external tick callback.
        #
        # Do not bind Controller again here.
        # -----------------------------------------------------

        # Intentionally left unbound for Controller.
        # The WS -> controller bridge is authoritative.

        if not bound:
            print("⚠️ Futures WebSocket Controller bridge unavailable.")

        return bool(bound)

    # =========================================================
    # FUTURES REST
    # =========================================================

    def _get_futures_candles(self, timeframe, limit=1000):

        if self.futures_provider is None:
            raise RuntimeError(
                "Futures Provider is not initialized."
            )

        df = self.futures_provider.get_candles(
            symbol=self.symbol,
            timeframe=timeframe,
            limit=limit,
        )

        return self._limit_dataframe_history(
            self._normalize_dataframe(df)
        )

    # =========================================================
    # REST LIVE PRICE
    # IMPORTANT: bootstrap/fallback only
    # =========================================================

    def _get_futures_live_price(self):

        if self.futures_provider is None:
            return None

        try:
            price = float(
                self.futures_provider.get_live_price(
                    self.symbol
                )
            )

            if price > 0:
                return price

        except Exception:
            pass

        return None

    # =========================================================
    # FUTURES WS PRICE STATE
    # =========================================================

    def _has_futures_websocket_price(self):

        return bool(
            self._futures_live_price_initialized
            and self._last_futures_ws_price is not None
            and self._last_futures_ws_price > 0
        )

    # =========================================================
    # AUTHORITATIVE PRICE
    # =========================================================

    def _get_authoritative_futures_price(self):

        if self._has_futures_websocket_price():
            return float(self._last_futures_ws_price)

        if self.current_price is not None and self.current_price > 0:
            return float(self.current_price)

        return self._get_futures_live_price()

    # =========================================================
    # WEBSOCKET LIFECYCLE
    # =========================================================

    def start_futures_websocket(self):

        if self.futures_websocket is None:
            return False

        try:
            self._bind_futures_websocket_callbacks()

            if self.futures_websocket.is_running():
                return False

            result = self.futures_websocket.connect(
                url=ControllerConfig.SOCKET_URL,
                symbol=self.symbol,
            )

            print("🚀 Futures WebSocket start result:", result)
            return result

        except Exception:
            traceback.print_exc()
            return False

    def stop_futures_websocket(self):

        if self.futures_websocket:
            try:
                self.futures_websocket.disconnect()
            except Exception:
                traceback.print_exc()

    def restart_futures_websocket(self):
        self.stop_futures_websocket()
        return self.start_futures_websocket()

    # =========================================================
    # SPOT WEBSOCKET
    # =========================================================

    def start_spot_websocket(self):

        if self.websocket is None:
            return False

        try:
            if self.websocket.is_running():
                return False

            return self.websocket.connect(
                url=ControllerConfig.SOCKET_URL,
                symbol=(
                    f"{self.symbol}"
                    f"{ControllerConfig.SOCKET_CHANNEL_SUFFIX}"
                ),
            )

        except Exception:
            traceback.print_exc()
            return False

    # =========================================================
    # COMPATIBILITY API
    # =========================================================

    def start_websocket(self):
        return self.start_futures_websocket()

    def stop_websocket(self):
        self.stop_futures_websocket()

    def restart_websocket(self):
        return self.restart_futures_websocket()

    # =========================================================
    # SYMBOL
    # =========================================================

    def change_symbol(self, symbol):

        try:
            new_symbol = str(symbol).strip().upper()

            if self.futures_provider:
                new_symbol = self.futures_provider.normalize_symbol(
                    new_symbol
                )
            elif self.futures_websocket:
                new_symbol = self.futures_websocket.normalize_symbol(
                    new_symbol
                )

            if new_symbol == self.symbol:
                return False

            self.stop_futures_websocket()

            if self.futures_websocket:
                try:
                    self.futures_websocket.candle_builder.reset()
                except Exception:
                    pass

            self.symbol = new_symbol

            self._futures_live_price_initialized = False
            self._last_futures_tick_timestamp = None
            self._last_futures_ws_price = None

            if self.futures_provider:
                self.futures_provider.set_symbol(new_symbol)

            if self.futures_websocket:
                self.futures_websocket.set_symbol(new_symbol)
                self._bind_futures_websocket_callbacks()

            if self.market:
                try:
                    self.market.set_symbol(new_symbol)
                    self.market.clear_cache()
                except Exception:
                    pass

            self.live_data_5m = None
            self.live_data_15m = None
            self.current_price = None
            self.last_tick = None
            self.last_candle = None
            self.latest_signal = None
            self.latest_trade = None
            self.latest_result = {}
            self.last_processed_closed_time = None
            self._live_candle_seed_timestamp = None

            self._force_chart_reload = True
            self._chart_data_loaded = False
            self._chart_loaded_symbol = None
            self._chart_loaded_timeframe = None
            self._chart_loaded_last_timestamp = None

            result = self.refresh()

            if (
                isinstance(result, dict)
                and result.get("signal") == "ERROR"
            ):
                return False

            self.start_futures_websocket()
            return True

        except Exception:
            traceback.print_exc()
            return False

    # =========================================================
    # TIMEFRAME
    # =========================================================

    def change_timeframe(self, timeframe):

        if not timeframe:
            return

        tf = str(timeframe).strip()

        if tf == self.timeframe:
            return

        self.stop_futures_websocket()

        self.timeframe = tf

        self.last_processed_closed_time = None
        self._live_candle_seed_timestamp = None

        self._futures_live_price_initialized = False
        self._last_futures_tick_timestamp = None
        self._last_futures_ws_price = None

        if self.futures_websocket:
            self.futures_websocket.set_timeframe(tf)
            self._bind_futures_websocket_callbacks()

        if self.websocket:
            try:
                self.websocket.set_timeframe(tf)
            except Exception:
                pass

        self.live_data_5m = None

        if self.market:
            try:
                self.market.clear_cache()
            except Exception:
                pass

        self._force_chart_reload = True
        self._chart_data_loaded = False
        self._chart_loaded_symbol = None
        self._chart_loaded_timeframe = None
        self._chart_loaded_last_timestamp = None

        self.refresh()
        self.start_futures_websocket()

    # =========================================================
    # REFRESH
    # =========================================================

    def refresh(self):

        try:
            data_5m = self._get_futures_candles(
                self.timeframe,
                ControllerConfig.MAX_CANDLE_HISTORY,
            )

            data_15m = self._get_futures_candles(
                self.higher_timeframe,
                ControllerConfig.MAX_CANDLE_HISTORY,
            )

            self.live_data_5m = data_5m.copy()
            self.live_data_15m = (
                data_15m.copy()
                if data_15m is not None
                else None
            )

            self._sync_live_candle_seed()

            if self.futures_websocket:
                try:
                    candle = (
                        self.futures_websocket
                        .candle_builder
                        .get_current_candle()
                    )

                    if candle is not None:
                        self._merge_live_candle(candle)

                except Exception:
                    traceback.print_exc()

            if (
                self.futures_websocket
                and not self.futures_websocket.is_running()
            ):
                self.start_futures_websocket()

            # -------------------------------------------------
            # PRICE SYNC
            #
            # Once Futures WS has supplied one valid price,
            # REST can NEVER overwrite it.
            # -------------------------------------------------

            if ControllerConfig.ENABLE_PRICE_SYNC:

                if self._has_futures_websocket_price():
                    self.current_price = float(
                        self._last_futures_ws_price
                    )

                elif self.current_price is None:
                    bootstrap = self._get_futures_live_price()

                    if bootstrap is not None:
                        self.current_price = bootstrap

            signal = self.signal_engine.generate_signal(
                self.live_data_5m,
                self.live_data_15m,
            )

            self.latest_signal = signal

            trade = self.trade_manager.generate_trade(
                signal,
                self.live_data_5m,
            )

            self.latest_trade = trade

            result = self._build_result(
                signal,
                trade,
            )

            self.latest_result = result
            self.last_refresh = result["last_refresh"]

            self._sync_chart()

            return result

        except Exception:
            traceback.print_exc()

            return {
                "symbol": self.symbol,
                "timeframe": self.timeframe,
                "live_price": self.current_price,
                "signal": "ERROR",
                "confidence": 0,
                "trade_status": "ERROR",
                "data_5m": self.live_data_5m,
                "data_15m": self.live_data_15m,
            }

    # =========================================================
    # DATAFRAME HELPERS
    # =========================================================

    def _limit_dataframe_history(self, dataframe):

        if dataframe is None or dataframe.empty:
            return dataframe

        return dataframe.iloc[
            -ControllerConfig.MAX_CANDLE_HISTORY:
        ].copy()

    def _normalize_dataframe(self, dataframe):

        if dataframe is None:
            return pd.DataFrame()

        df = dataframe.copy()

        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index, utc=True)

        elif df.index.tz is None:
            df.index = df.index.tz_localize("UTC")

        else:
            df.index = df.index.tz_convert("UTC")

        df = df.sort_index()

        return df[
            ~df.index.duplicated(keep="last")
        ]

    # =========================================================
    # RESULT
    # =========================================================

    def _build_result(self, signal, trade):

        result = {}

        if isinstance(signal, dict):
            result.update(signal)

        if isinstance(trade, dict):
            result.update(trade)

        result.update({
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "live_price": self.current_price,
            "market_type": "FUTURES",
            "price_source": "CoinDCX Futures",
            "live_price_source": (
                "CoinDCX Futures WebSocket"
                if self._has_futures_websocket_price()
                else "CoinDCX Futures REST Bootstrap"
            ),
            "data_5m": self.live_data_5m,
            "data_15m": self.live_data_15m,
            "last_refresh": datetime.now(timezone.utc),
        })

        return result

    # =========================================================
    # HISTORICAL -> LIVE CANDLE SEED
    # =========================================================

    def _sync_live_candle_seed(self):

        if self.live_data_5m is None or self.live_data_5m.empty:
            return False

        if self.futures_websocket is None:
            return False

        builder = self.futures_websocket.candle_builder

        latest_ts = pd.Timestamp(
            self.live_data_5m.index[-1]
        ).tz_convert("UTC")

        current = builder.get_current_candle()

        if current is not None:

            current_ts = pd.Timestamp(
                current.timestamp
            ).tz_convert("UTC")

            if current_ts >= latest_ts:
                self._live_candle_seed_timestamp = current_ts
                return True

        try:
            from providers.live_candle_builder import Candle

            row = self.live_data_5m.iloc[-1]

            seeded = builder.seed_current_candle(
                Candle(
                    timestamp=latest_ts.to_pydatetime(),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row.get("Volume", 0.0)),
                )
            )

            if seeded:
                self._live_candle_seed_timestamp = latest_ts

            return seeded

        except Exception:
            traceback.print_exc()
            return False

    # =========================================================
    # CHART
    # =========================================================

    def _sync_chart(self):

        if (
            self.chart_widget is None
            or self.live_data_5m is None
            or self.live_data_5m.empty
        ):
            return

        try:
            latest = pd.Timestamp(
                self.live_data_5m.index[-1]
            )

            reload_needed = (
                not self._chart_data_loaded
                or self._force_chart_reload
                or self._chart_loaded_symbol != self.symbol
                or self._chart_loaded_timeframe != self.timeframe
            )

            if reload_needed:

                self.chart_widget.set_chart_data(
                    self.live_data_5m
                )

                self._chart_data_loaded = True
                self._chart_loaded_symbol = self.symbol
                self._chart_loaded_timeframe = self.timeframe
                self._chart_loaded_last_timestamp = latest
                self._force_chart_reload = False

            self._sync_trade_overlay()

        except Exception:
            traceback.print_exc()

    # =========================================================
    # TRADE OVERLAY
    # =========================================================

    def _sync_trade_overlay(self):

        if self.chart_widget is None:
            return

        try:
            result = self.latest_result

            if (
                result.get("trade_status") == "READY"
                and result.get("trade_direction") in ("BUY", "SELL")
                and self.live_data_5m is not None
                and not self.live_data_5m.empty
            ):

                ts = self.live_data_5m.index[-1]

                self.chart_widget.show_trade_signal({
                    "time": int(
                        pd.Timestamp(ts).timestamp()
                    ),
                    "direction": result["trade_direction"],
                })

        except Exception:
            traceback.print_exc()

    # =========================================================
    # FORCE CHART RELOAD
    # =========================================================

    def force_chart_reload(self):

        self._force_chart_reload = True
        self._chart_data_loaded = False
        self._sync_chart()

    # =========================================================
    # SPOT COMPATIBILITY CALLBACKS
    # =========================================================

    def on_live_tick(self, tick):
        self.last_tick = tick

    def on_live_candle(self, candle):
        return

    def on_candle_closed(self, candle):
        return

    # =========================================================
    # FUTURES TICK PARSER
    # =========================================================

    def _extract_futures_tick(self, tick):

        if not isinstance(tick, dict):
            return None, None

        price_keys = (
            "p", "price", "last_price", "lastPrice",
            "P", "close", "Close",
        )

        price = None

        for key in price_keys:

            value = tick.get(key)

            if value is not None:
                try:
                    value = float(value)

                    if value > 0:
                        price = value
                        break

                except Exception:
                    continue

        timestamp_keys = (
            "T", "timestamp", "ts", "time", "event_time"
        )

        timestamp = None

        for key in timestamp_keys:

            value = tick.get(key)

            if value is not None:
                try:
                    timestamp = float(value)
                    break
                except Exception:
                    continue

        return price, timestamp

    # =========================================================
    # AUTHORITATIVE FUTURES TICK
    # =========================================================

    def on_futures_live_tick(self, tick):

        """
        LOW-LATENCY FUTURES PRICE AUTHORITY.

        This method is called directly by the Socket.IO
        background thread. It updates ONLY plain Python state.
        It NEVER touches Qt widgets.

        WebSocket tick
            ↓
        validate
            ↓
        current_price
            ↓
        Qt queued signal
            ↓
        GUI thread
        """

        if not isinstance(tick, dict):
            return False

        try:

            price, timestamp = self._extract_futures_tick(tick)

            if price is None:
                return False

            normalized_ts = None

            if timestamp is not None:

                value = float(timestamp)

                if value > 10_000_000_000:
                    value /= 1000.0

                normalized_ts = pd.Timestamp.fromtimestamp(
                    value,
                    tz="UTC",
                )

            if (
                normalized_ts is not None
                and self._last_futures_tick_timestamp is not None
                and normalized_ts < self._last_futures_tick_timestamp
            ):
                return False

            if normalized_ts is not None:
                self._last_futures_tick_timestamp = normalized_ts

            # =================================================
            # AUTHORITATIVE FUTURES PRICE
            # =================================================

            self._last_futures_ws_price = price
            self._futures_live_price_initialized = True
            self.current_price = price
            self.last_tick = tick

            # =================================================
            # THREAD-SAFE GUI BRIDGE
            # =================================================

            try:
                self.futures_live_tick_signal.emit(dict(tick))
            except Exception:
                pass

            return True

        except Exception:
            traceback.print_exc()
            return False

    # =========================================================
    # GUI THREAD — FUTURES LIVE TICK
    # =========================================================

    @Slot(object)
    def _handle_futures_live_tick_gui(self, tick):

        """
        Runs on the Qt GUI thread. All Dashboard widget access
        belongs here, never in the Socket.IO callback thread.
        """

        if not isinstance(tick, dict):
            return

        try:

            price = tick.get(
                "p",
                tick.get("price"),
            )

            if price is None:
                return

            price = float(price)

            if price <= 0:
                return

            if self.dashboard is not None:

                updater = getattr(
                    self.dashboard,
                    "update_futures_live_price",
                    None,
                )

                if callable(updater):
                    updater(
                        price,
                        source="Futures WebSocket",
                    )

                status = getattr(
                    self.dashboard,
                    "set_live_status",
                    None,
                )

                if callable(status):
                    status(True)

        except Exception:
            # A GUI exception must NEVER break market data.
            traceback.print_exc()

    # =========================================================
    # COMPATIBILITY FUTURES PRICE CALLBACK
    # =========================================================

    def on_futures_price(self, price):

        try:

            price = float(price)

            if price <= 0:
                return

            self._last_futures_ws_price = price
            self._futures_live_price_initialized = True
            self.current_price = price

        except Exception:
            pass

    # =========================================================
    # AUTHORITATIVE LIVE CANDLE
    # =========================================================

    def on_futures_live_candle(self, candle):

        """
        Socket.IO thread entry point. No Qt widget access is
        allowed here. The authoritative Candle object is queued
        to the GUI/controller thread.
        """

        if candle is None:
            return False

        try:
            self.futures_live_candle_signal.emit(candle)
            return True
        except Exception:
            traceback.print_exc()
            return False

    # =========================================================
    # GUI THREAD — FUTURES LIVE CANDLE
    # =========================================================

    @Slot(object)
    def _handle_futures_live_candle_gui(self, candle):

        if candle is None:
            return False

        try:

            self.last_candle = candle

            if not self._has_futures_websocket_price():

                try:
                    close_price = float(candle.close)
                    if close_price > 0:
                        self.current_price = close_price
                except Exception:
                    pass

            # Controller mirrors the authoritative Candle; it does
            # not construct OHLC values itself.
            self._merge_live_candle(candle)

            # Chart is now guaranteed to run on the Qt GUI thread.
            if self.chart_widget is not None:

                updater = getattr(
                    self.chart_widget,
                    "update_last_candle",
                    None,
                )

                if callable(updater):
                    updater(candle)

            return True

        except Exception:
            traceback.print_exc()
            return False

    # =========================================================
    # MERGE LIVE CANDLE
    # =========================================================

    def _merge_live_candle(self, candle):

        if self.live_data_5m is None:
            return False

        ts = pd.Timestamp(candle.timestamp)

        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        else:
            ts = ts.tz_convert("UTC")

        row = {
            "Open": float(candle.open),
            "High": float(candle.high),
            "Low": float(candle.low),
            "Close": float(candle.close),
            "Volume": float(candle.volume),
        }

        df = self._normalize_dataframe(
            self.live_data_5m
        )

        if ts in df.index:

            for col, value in row.items():
                df.loc[ts, col] = value

        else:

            new_row = pd.DataFrame(
                [row],
                index=[ts]
            )

            df = pd.concat([df, new_row])

        df = df.sort_index()

        df = df[
            ~df.index.duplicated(keep="last")
        ]

        self.live_data_5m = self._limit_dataframe_history(df)

        return True

    # =========================================================
    # CLOSED FUTURES CANDLE
    # =========================================================

    def on_futures_candle_closed(self, candle):

        """
        Socket.IO thread entry point for a newly closed Futures
        candle. Dispatches exactly once to the Qt GUI thread.
        """

        if candle is None:
            return None

        try:
            self.futures_closed_candle_signal.emit(candle)
            return True
        except Exception:
            traceback.print_exc()
            return None

    # =========================================================
    # GUI THREAD — CLOSED FUTURES CANDLE
    # =========================================================

    @Slot(object)
    def _handle_futures_closed_candle_gui(self, candle):

        if candle is None:
            return None

        try:

            ts = pd.Timestamp(candle.timestamp)

            if ts.tzinfo is None:
                ts = ts.tz_localize("UTC")
            else:
                ts = ts.tz_convert("UTC")

            if (
                self.last_processed_closed_time is not None
                and ts <= self.last_processed_closed_time
            ):
                return None

            if not self._merge_live_candle(candle):
                return None

            self.last_processed_closed_time = ts

            if not self._has_futures_websocket_price():

                try:
                    close_price = float(candle.close)
                    if close_price > 0:
                        self.current_price = close_price
                except Exception:
                    pass

            return self._run_closed_candle_analysis(candle)

        except Exception:
            traceback.print_exc()
            return None

    # =========================================================
    # CLOSED CANDLE ANALYSIS
    # =========================================================

    def _run_closed_candle_analysis(self, candle):

        if not ControllerConfig.ENABLE_CLOSED_CANDLE_ANALYSIS:
            return None

        if (
            self.live_data_5m is None
            or self.live_data_15m is None
        ):
            return None

        try:

            signal = self.signal_engine.generate_signal(
                self.live_data_5m,
                self.live_data_15m,
            )

            self.latest_signal = signal

            trade = self.trade_manager.generate_trade(
                signal,
                self.live_data_5m,
            )

            self.latest_trade = trade

            result = self._build_result(
                signal,
                trade,
            )

            self.latest_result = result
            self.last_refresh = result["last_refresh"]

            self._sync_trade_overlay()

            return result

        except Exception:
            traceback.print_exc()
            return None

    # =========================================================
    # HEALTH REPORT
    # =========================================================

    def health_report(self):

        futures_ws = {}

        if self.futures_websocket:

            try:
                futures_ws = (
                    self.futures_websocket.health_report()
                )
            except Exception:
                pass

        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "higher_timeframe": self.higher_timeframe,

            "futures_provider": (
                type(self.futures_provider).__name__
                if self.futures_provider
                else None
            ),

            "futures_symbol": (
                self.futures_provider.symbol
                if self.futures_provider
                else None
            ),

            "futures_connected": (
                self.futures_provider.connected
                if self.futures_provider
                else False
            ),

            "futures_live_price": self.current_price,

            "futures_live_price_source": (
                "WEBSOCKET"
                if self._has_futures_websocket_price()
                else "REST_BOOTSTRAP_OR_EXISTING_STATE"
            ),

            "futures_ws_live_price": self._last_futures_ws_price,
            "futures_ws_price_initialized": (
                self._futures_live_price_initialized
            ),
            "last_futures_tick_timestamp": (
                self._last_futures_tick_timestamp
            ),

            "futures_websocket_running": (
                self.futures_websocket.is_running()
                if self.futures_websocket
                else False
            ),

            "futures_websocket_connected": (
                self.futures_websocket.is_connected()
                if self.futures_websocket
                else False
            ),

            "futures_websocket_healthy": (
                self.futures_websocket.is_connection_healthy()
                if self.futures_websocket
                else False
            ),

            "futures_websocket_health": futures_ws,

            "live_data_5m_rows": (
                len(self.live_data_5m)
                if self.live_data_5m is not None
                else 0
            ),

            "live_data_15m_rows": (
                len(self.live_data_15m)
                if self.live_data_15m is not None
                else 0
            ),

            "chart_data_loaded": self._chart_data_loaded,
            "chart_loaded_symbol": self._chart_loaded_symbol,
            "chart_loaded_timeframe": self._chart_loaded_timeframe,
            "chart_loaded_last_timestamp": (
                self._chart_loaded_last_timestamp
            ),
            "chart_force_reload": self._force_chart_reload,

            "closed_candle_analysis_enabled": (
                ControllerConfig.ENABLE_CLOSED_CANDLE_ANALYSIS
            ),

            "last_processed_closed_time": (
                self.last_processed_closed_time
            ),
        }

    # =========================================================
    # HEALTH LOG
    # =========================================================

    def log_health(self):

        print("\n========== Controller Health ==========")

        for key, value in self.health_report().items():
            print(f"{key} : {value}")

        print("=======================================\n")

    # =========================================================
    # SHUTDOWN
    # =========================================================

    def shutdown(self):

        try:
            self.stop_futures_websocket()
        except Exception:
            traceback.print_exc()

        try:
            if self.websocket:
                self.websocket.close()
        except Exception:
            traceback.print_exc()

        try:
            if self.market:
                self.market.disconnect()
        except Exception:
            traceback.print_exc()

        try:
            if self.futures_provider:
                self.futures_provider.disconnect()
        except Exception:
            traceback.print_exc()

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(self):

        return (
            f"Controller("
            f"symbol='{self.symbol}', "
            f"timeframe='{self.timeframe}', "
            f"price={self.current_price}, "
            f"market_type='FUTURES', "
            f"futures_provider="
            f"{self.futures_provider is not None}, "
            f"futures_websocket="
            f"{self.futures_websocket is not None}"
            f")"
        )