"""
Liquidity Hunter AI
Controller V20.9.4
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
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass
from datetime import datetime, timezone

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

class Controller:

    def __init__(self):

        print("=" * 64)
        print("Liquidity Hunter AI")
        print("Controller V20.9.4")
        print("Futures Authoritative Live Synchronization")
        print("=" * 64)

        # ----------------------------------------------------
        # Basic state
        # ----------------------------------------------------

        self.symbol = ControllerConfig.DEFAULT_SYMBOL

        self.timeframe = ControllerConfig.DEFAULT_TIMEFRAME

        self.higher_timeframe = (
            ControllerConfig.HIGHER_TIMEFRAME
        )

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
        # FUTURES REST PROVIDER
        # ====================================================

        try:

            self.futures_provider = (
                CoinDCXFuturesProvider(
                    self.symbol
                )
            )

            self.futures_provider.connect()

            print(
                "✅ Futures REST Provider initialized"
            )

        except Exception:

            print(
                "❌ Futures REST Provider initialization failed"
            )

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
        #
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

            self.futures_websocket = (
                CoinDCXFuturesWebSocket(
                    timeframe=self.timeframe,
                    symbol=self.symbol,
                )
            )

            # Controller reference
            self.futures_websocket.set_controller(
                self
            )

            # IMPORTANT:
            # Explicit callback binding.
            #
            # This is one of the main changes in V20.9.4.
            # =================================================

            self._bind_futures_websocket_callbacks()

        except Exception:

            print(
                "❌ Futures WebSocket initialization failed"
            )

            traceback.print_exc()

            self.futures_websocket = None

        # ====================================================
        # AUTHORITY LOG
        # ====================================================

        print(
            "Historical Data Authority : FUTURES REST"
        )

        print(
            "Live Price Authority       : FUTURES WEBSOCKET"
        )

        print(
            "Live Candle Authority      : FUTURES WEBSOCKET"
        )

        print(
            "REST Live Price            : BOOTSTRAP ONLY"
        )

    # =========================================================
    # FUTURES WEBSOCKET CALLBACK BINDING
    # =========================================================

    def _bind_futures_websocket_callbacks(self):

        """
        Explicitly connect Futures WebSocket events to
        Controller authoritative handlers.

        This prevents a situation where the WebSocket is
        connected and receiving ticks but Controller never
        receives the live price.
        """

        ws = self.futures_websocket

        if ws is None:
            return False

        bound = []

        # -----------------------------------------------------
        # Live tick
        # -----------------------------------------------------

        tick_methods = (
            "set_tick_callback",
            "set_trade_callback",
            "set_price_callback",
            "set_live_tick_callback",
        )

        for method_name in tick_methods:

            method = getattr(
                ws,
                method_name,
                None
            )

            if callable(method):

                try:

                    method(
                        self.on_futures_live_tick
                    )

                    bound.append(method_name)

                    print(
                        f"✅ Futures tick callback bound: "
                        f"{method_name}"
                    )

                    # One successful tick callback
                    # registration is enough.
                    break

                except Exception:

                    continue

        # -----------------------------------------------------
        # Live candle
        # -----------------------------------------------------

        candle_methods = (
            "set_candle_callback",
            "set_live_candle_callback",
        )

        for method_name in candle_methods:

            method = getattr(
                ws,
                method_name,
                None
            )

            if callable(method):

                try:

                    method(
                        self.on_futures_live_candle
                    )

                    bound.append(method_name)

                    print(
                        f"✅ Futures candle callback bound: "
                        f"{method_name}"
                    )

                    break

                except Exception:

                    continue

        # -----------------------------------------------------
        # Closed candle
        # -----------------------------------------------------

        closed_methods = (
            "set_candle_closed_callback",
            "set_closed_candle_callback",
            "set_live_candle_closed_callback",
        )

        for method_name in closed_methods:

            method = getattr(
                ws,
                method_name,
                None
            )

            if callable(method):

                try:

                    method(
                        self.on_futures_candle_closed
                    )

                    bound.append(method_name)

                    print(
                        f"✅ Futures closed-candle callback bound: "
                        f"{method_name}"
                    )

                    break

                except Exception:

                    continue

        if not bound:

            print(
                "⚠️ Futures WebSocket callback methods "
                "were not found."
            )

            print(
                "⚠️ set_controller(self) remains active "
                "as compatibility path."
            )

        return bool(bound)

    # =========================================================
    # FUTURES REST
    # =========================================================

    def _get_futures_candles(
        self,
        timeframe,
        limit=1000
    ):

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
    #
    # IMPORTANT:
    # This function is ONLY bootstrap/fallback.
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
            and
            self._last_futures_ws_price is not None
            and
            self._last_futures_ws_price > 0
        )

    # =========================================================
    # AUTHORITATIVE PRICE
    # =========================================================

    def _get_authoritative_futures_price(self):

        # -----------------------------------------------------
        # 1. Futures WebSocket
        # -----------------------------------------------------

        if self._has_futures_websocket_price():

            return float(
                self._last_futures_ws_price
            )

        # -----------------------------------------------------
        # 2. Existing controller state
        # -----------------------------------------------------

        if (
            self.current_price is not None
            and
            self.current_price > 0
        ):

            return float(
                self.current_price
            )

        # -----------------------------------------------------
        # 3. REST bootstrap
        # -----------------------------------------------------

        return self._get_futures_live_price()

    # =========================================================
    # WEBSOCKET LIFECYCLE
    # =========================================================

    def start_futures_websocket(self):

        if self.futures_websocket is None:
            return False

        try:

            # Make absolutely sure callbacks are present
            # before every connection.

            self._bind_futures_websocket_callbacks()

            if self.futures_websocket.is_running():

                return False

            result = self.futures_websocket.connect(
                url=ControllerConfig.SOCKET_URL,
                symbol=self.symbol,
            )

            print(
                "🚀 Futures WebSocket start result:",
                result
            )

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

            new_symbol = str(
                symbol
            ).strip().upper()

            if self.futures_provider:

                new_symbol = (
                    self.futures_provider
                    .normalize_symbol(
                        new_symbol
                    )
                )

            elif self.futures_websocket:

                new_symbol = (
                    self.futures_websocket
                    .normalize_symbol(
                        new_symbol
                    )
                )

            if new_symbol == self.symbol:

                return False

            # -------------------------------------------------
            # Stop old Futures stream
            # -------------------------------------------------

            self.stop_futures_websocket()

            # -------------------------------------------------
            # Reset builder
            # -------------------------------------------------

            if self.futures_websocket:

                try:

                    self.futures_websocket.candle_builder.reset()

                except Exception:

                    pass

            # -------------------------------------------------
            # Change symbol
            # -------------------------------------------------

            self.symbol = new_symbol

            # -------------------------------------------------
            # Reset authoritative price
            # -------------------------------------------------

            self._futures_live_price_initialized = False

            self._last_futures_tick_timestamp = None

            self._last_futures_ws_price = None

            # -------------------------------------------------
            # Update Futures REST
            # -------------------------------------------------

            if self.futures_provider:

                self.futures_provider.set_symbol(
                    new_symbol
                )

            # -------------------------------------------------
            # Update Futures WebSocket
            # -------------------------------------------------

            if self.futures_websocket:

                self.futures_websocket.set_symbol(
                    new_symbol
                )

                # Re-bind after symbol change.
                self._bind_futures_websocket_callbacks()

            # -------------------------------------------------
            # Spot compatibility
            # -------------------------------------------------

            if self.market:

                try:

                    self.market.set_symbol(
                        new_symbol
                    )

                    self.market.clear_cache()

                except Exception:

                    pass

            # -------------------------------------------------
            # Reset data
            # -------------------------------------------------

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

            # -------------------------------------------------
            # Reset chart
            # -------------------------------------------------

            self._force_chart_reload = True

            self._chart_data_loaded = False

            self._chart_loaded_symbol = None

            self._chart_loaded_timeframe = None

            self._chart_loaded_last_timestamp = None

            # -------------------------------------------------
            # Bootstrap historical data
            # -------------------------------------------------

            result = self.refresh()

            if (
                isinstance(result, dict)
                and
                result.get("signal") == "ERROR"
            ):

                return False

            # -------------------------------------------------
            # Start new Futures stream
            # -------------------------------------------------

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

        tf = str(
            timeframe
        ).strip()

        if tf == self.timeframe:
            return

        # -----------------------------------------------------
        # Stop Futures stream
        # -----------------------------------------------------

        self.stop_futures_websocket()

        # -----------------------------------------------------
        # Update timeframe
        # -----------------------------------------------------

        self.timeframe = tf

        # -----------------------------------------------------
        # Reset candle state
        # -----------------------------------------------------

        self.last_processed_closed_time = None

        self._live_candle_seed_timestamp = None

        # -----------------------------------------------------
        # Reset Futures live price state
        # -----------------------------------------------------

        self._futures_live_price_initialized = False

        self._last_futures_tick_timestamp = None

        self._last_futures_ws_price = None

        # -----------------------------------------------------
        # Update Futures WebSocket
        # -----------------------------------------------------

        if self.futures_websocket:

            self.futures_websocket.set_timeframe(
                tf
            )

            self._bind_futures_websocket_callbacks()

        # -----------------------------------------------------
        # Spot compatibility
        # -----------------------------------------------------

        if self.websocket:

            try:

                self.websocket.set_timeframe(
                    tf
                )

            except Exception:

                pass

        # -----------------------------------------------------
        # Reset live data
        # -----------------------------------------------------

        self.live_data_5m = None

        # -----------------------------------------------------
        # Clear REST cache
        # -----------------------------------------------------

        if self.market:

            try:

                self.market.clear_cache()

            except Exception:

                pass

        # -----------------------------------------------------
        # Reset chart
        # -----------------------------------------------------

        self._force_chart_reload = True

        self._chart_data_loaded = False

        self._chart_loaded_symbol = None

        self._chart_loaded_timeframe = None

        self._chart_loaded_last_timestamp = None

        # -----------------------------------------------------
        # Refresh bootstrap data
        # -----------------------------------------------------

        self.refresh()

        # -----------------------------------------------------
        # Restart Futures stream
        # -----------------------------------------------------

        self.start_futures_websocket()

    # =========================================================
    # REFRESH
    # =========================================================

    def refresh(self):

        try:

            # =================================================
            # 1. FUTURES REST HISTORICAL DATA
            # =================================================

            data_5m = self._get_futures_candles(
                self.timeframe,
                ControllerConfig.MAX_CANDLE_HISTORY,
            )

            data_15m = self._get_futures_candles(
                self.higher_timeframe,
                ControllerConfig.MAX_CANDLE_HISTORY,
            )

            # =================================================
            # 2. COPY INTO LIVE DATA
            # =================================================

            self.live_data_5m = (
                data_5m.copy()
            )

            self.live_data_15m = (
                data_15m.copy()
                if data_15m is not None
                else None
            )

            # =================================================
            # 3. SEED LIVE CANDLE
            # =================================================

            self._sync_live_candle_seed()

            # =================================================
            # 4. IF BUILDER ALREADY HAS A LIVE CANDLE,
            #    MERGE IT.
            # =================================================

            if self.futures_websocket:

                try:

                    candle = (
                        self.futures_websocket
                        .candle_builder
                        .get_current_candle()
                    )

                    if candle is not None:

                        self._merge_live_candle(
                            candle
                        )

                except Exception:

                    traceback.print_exc()

            # =================================================
            # 5. ENSURE FUTURES WS IS RUNNING
            # =================================================

            if (
                self.futures_websocket
                and
                not self.futures_websocket.is_running()
            ):

                self.start_futures_websocket()

            # =================================================
            # 6. PRICE SYNC
            #
            # IMPORTANT:
            #
            # Once Futures WS has supplied one valid price,
            # REST is NEVER allowed to overwrite it.
            # =================================================

            if ControllerConfig.ENABLE_PRICE_SYNC:

                if self._has_futures_websocket_price():

                    self.current_price = float(
                        self._last_futures_ws_price
                    )

                elif self.current_price is None:

                    bootstrap = (
                        self._get_futures_live_price()
                    )

                    if bootstrap is not None:

                        self.current_price = bootstrap

            # =================================================
            # 7. AI ANALYSIS
            # =================================================

            signal = (
                self.signal_engine.generate_signal(
                    self.live_data_5m,
                    self.live_data_15m,
                )
            )

            self.latest_signal = signal

            # =================================================
            # 8. TRADE MANAGER
            # =================================================

            trade = (
                self.trade_manager.generate_trade(
                    signal,
                    self.live_data_5m,
                )
            )

            self.latest_trade = trade

            # =================================================
            # 9. RESULT
            # =================================================

            result = self._build_result(
                signal,
                trade,
            )

            self.latest_result = result

            self.last_refresh = (
                result["last_refresh"]
            )

            # =================================================
            # 10. CHART
            # =================================================

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

    def _limit_dataframe_history(
        self,
        dataframe
    ):

        if (
            dataframe is None
            or
            dataframe.empty
        ):

            return dataframe

        return dataframe.iloc[
            -ControllerConfig.MAX_CANDLE_HISTORY:
        ].copy()

    def _normalize_dataframe(
        self,
        dataframe
    ):

        if dataframe is None:

            return pd.DataFrame()

        df = dataframe.copy()

        if not isinstance(
            df.index,
            pd.DatetimeIndex
        ):

            df.index = pd.to_datetime(
                df.index,
                utc=True,
            )

        elif df.index.tz is None:

            df.index = df.index.tz_localize(
                "UTC"
            )

        else:

            df.index = df.index.tz_convert(
                "UTC"
            )

        df = df.sort_index()

        return df[
            ~df.index.duplicated(
                keep="last"
            )
        ]

    # =========================================================
    # RESULT
    # =========================================================

    def _build_result(
        self,
        signal,
        trade
    ):

        result = {}

        if isinstance(
            signal,
            dict
        ):

            result.update(
                signal
            )

        if isinstance(
            trade,
            dict
        ):

            result.update(
                trade
            )

        result.update({

            "symbol":
                self.symbol,

            "timeframe":
                self.timeframe,

            "live_price":
                self.current_price,

            "market_type":
                "FUTURES",

            "price_source":
                "CoinDCX Futures",

            "live_price_source":
                (
                    "CoinDCX Futures WebSocket"
                    if
                    self._has_futures_websocket_price()
                    else
                    "CoinDCX Futures REST Bootstrap"
                ),

            "data_5m":
                self.live_data_5m,

            "data_15m":
                self.live_data_15m,

            "last_refresh":
                datetime.now(
                    timezone.utc
                ),
        })

        return result

    # =========================================================
    # HISTORICAL -> LIVE CANDLE SEED
    # =========================================================

    def _sync_live_candle_seed(self):

        if (
            self.live_data_5m is None
            or
            self.live_data_5m.empty
        ):

            return False

        if self.futures_websocket is None:

            return False

        builder = (
            self.futures_websocket
            .candle_builder
        )

        latest_ts = pd.Timestamp(
            self.live_data_5m.index[-1]
        ).tz_convert(
            "UTC"
        )

        # -----------------------------------------------------
        # Builder already has a newer/equal candle
        # -----------------------------------------------------

        current = (
            builder.get_current_candle()
        )

        if current is not None:

            current_ts = pd.Timestamp(
                current.timestamp
            ).tz_convert(
                "UTC"
            )

            if current_ts >= latest_ts:

                self._live_candle_seed_timestamp = (
                    current_ts
                )

                return True

        # -----------------------------------------------------
        # Seed builder from REST candle
        # -----------------------------------------------------

        try:

            from providers.live_candle_builder import Candle

            row = self.live_data_5m.iloc[-1]

            seeded = (
                builder.seed_current_candle(
                    Candle(
                        timestamp=(
                            latest_ts
                            .to_pydatetime()
                        ),
                        open=float(
                            row["Open"]
                        ),
                        high=float(
                            row["High"]
                        ),
                        low=float(
                            row["Low"]
                        ),
                        close=float(
                            row["Close"]
                        ),
                        volume=float(
                            row.get(
                                "Volume",
                                0.0
                            )
                        ),
                    )
                )
            )

            if seeded:

                self._live_candle_seed_timestamp = (
                    latest_ts
                )

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
            or
            self.live_data_5m is None
            or
            self.live_data_5m.empty
        ):

            return

        try:

            latest = pd.Timestamp(
                self.live_data_5m.index[-1]
            )

            reload_needed = (

                not self._chart_data_loaded

                or

                self._force_chart_reload

                or

                self._chart_loaded_symbol
                != self.symbol

                or

                self._chart_loaded_timeframe
                != self.timeframe
            )

            if reload_needed:

                self.chart_widget.set_chart_data(
                    self.live_data_5m
                )

                self._chart_data_loaded = True

                self._chart_loaded_symbol = (
                    self.symbol
                )

                self._chart_loaded_timeframe = (
                    self.timeframe
                )

                self._chart_loaded_last_timestamp = (
                    latest
                )

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
                result.get(
                    "trade_status"
                ) == "READY"

                and

                result.get(
                    "trade_direction"
                ) in (
                    "BUY",
                    "SELL",
                )

                and

                self.live_data_5m is not None

                and

                not self.live_data_5m.empty
            ):

                ts = (
                    self.live_data_5m.index[-1]
                )

                self.chart_widget.show_trade_signal({

                    "time":
                        int(
                            pd.Timestamp(
                                ts
                            ).timestamp()
                        ),

                    "direction":
                        result[
                            "trade_direction"
                        ],
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

    def on_live_tick(
        self,
        tick
    ):

        # Spot is compatibility-only.
        # NEVER change current_price here.

        self.last_tick = tick

    def on_live_candle(
        self,
        candle
    ):

        return

    def on_candle_closed(
        self,
        candle
    ):

        return

    # =========================================================
    # FUTURES TICK PARSER
    # =========================================================

    def _extract_futures_tick(
        self,
        tick
    ):

        if not isinstance(
            tick,
            dict
        ):

            return None, None

        # -----------------------------------------------------
        # Price candidates
        # -----------------------------------------------------

        price_keys = (
            "p",
            "price",
            "last_price",
            "lastPrice",
            "P",
            "close",
            "Close",
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

        # -----------------------------------------------------
        # Timestamp candidates
        # -----------------------------------------------------

        timestamp_keys = (
            "T",
            "timestamp",
            "ts",
            "time",
            "event_time",
        )

        timestamp = None

        for key in timestamp_keys:

            value = tick.get(key)

            if value is not None:

                try:

                    timestamp = float(
                        value
                    )

                    break

                except Exception:

                    continue

        return price, timestamp

    # =========================================================
    # AUTHORITATIVE FUTURES TICK
    # =========================================================

    def on_futures_live_tick(
        self,
        tick
    ):

        """
        LOW-LATENCY FUTURES PRICE AUTHORITY.

        This function intentionally does NOT perform:

            REST
            AI analysis
            DataFrame merge
            chart rendering
            heavy logging

        Its job is:

            WebSocket tick
                ↓
            validate
                ↓
            current_price
        """

        if not isinstance(
            tick,
            dict
        ):

            return

        try:

            price, timestamp = (
                self._extract_futures_tick(
                    tick
                )
            )

            if price is None:

                return

            # -------------------------------------------------
            # Timestamp normalization
            # -------------------------------------------------

            normalized_ts = None

            if timestamp is not None:

                value = float(
                    timestamp
                )

                # Milliseconds -> seconds
                if value > 10_000_000_000:

                    value /= 1000.0

                normalized_ts = (
                    pd.Timestamp.fromtimestamp(
                        value,
                        tz="UTC"
                    )
                )

            # -------------------------------------------------
            # OLD TICK PROTECTION
            #
            # Only reject when timestamp exists.
            # -------------------------------------------------

            if (
                normalized_ts is not None
                and
                self._last_futures_tick_timestamp
                is not None
                and
                normalized_ts
                <
                self._last_futures_tick_timestamp
            ):

                return

            if normalized_ts is not None:

                self._last_futures_tick_timestamp = (
                    normalized_ts
                )

            # =================================================
            # AUTHORITATIVE FUTURES PRICE
            # =================================================

            self._last_futures_ws_price = (
                price
            )

            self._futures_live_price_initialized = (
                True
            )

            self.current_price = (
                price
            )

            self.last_tick = (
                tick
            )

            # =================================================
            # LIGHTWEIGHT DASHBOARD UPDATE
            # =================================================

            if self.dashboard is not None:

                try:

                    updater = getattr(
                        self.dashboard,
                        "update_futures_live_price",
                        None
                    )

                    if callable(updater):

                        updater(
                            price,
                            source="Futures WebSocket",
                        )

                except Exception:

                    # UI failure must NEVER kill
                    # the Futures price path.

                    pass

        except Exception:

            # Absolute rule:
            # live price callback must never crash
            # the WebSocket worker.

            pass

    # =========================================================
    # COMPATIBILITY FUTURES PRICE CALLBACK
    # =========================================================

    def on_futures_price(
        self,
        price
    ):

        try:

            price = float(
                price
            )

            if price <= 0:
                return

            self._last_futures_ws_price = (
                price
            )

            self._futures_live_price_initialized = (
                True
            )

            self.current_price = (
                price
            )

        except Exception:

            pass

    # =========================================================
    # AUTHORITATIVE LIVE CANDLE
    # =========================================================

    def on_futures_live_candle(
        self,
        candle
    ):

        if candle is None:
            return

        # -----------------------------------------------------
        # Save latest candle
        # -----------------------------------------------------

        self.last_candle = candle

        # =====================================================
        # 1. PRICE FALLBACK
        #
        # Only use candle close if no Futures tick has ever
        # arrived.
        # =====================================================

        if not self._has_futures_websocket_price():

            try:

                close_price = float(
                    candle.close
                )

                if close_price > 0:

                    self.current_price = (
                        close_price
                    )

            except Exception:

                pass

        # =====================================================
        # 2. CHART LIVE UPDATE
        #
        # Chart gets the candle immediately.
        #
        # Do NOT wait for AI analysis.
        # =====================================================

        if self.chart_widget is not None:

            try:

                self.chart_widget.update_last_candle(
                    candle
                )

            except Exception:

                # Chart failure must not stop
                # candle/data processing.

                traceback.print_exc()

        # =====================================================
        # 3. MERGE INTO LIVE DATA
        # =====================================================

        try:

            self._merge_live_candle(
                candle
            )

        except Exception:

            traceback.print_exc()

    # =========================================================
    # MERGE LIVE CANDLE
    # =========================================================

    def _merge_live_candle(
        self,
        candle
    ):

        if self.live_data_5m is None:

            return False

        # -----------------------------------------------------
        # Normalize timestamp
        # -----------------------------------------------------

        ts = pd.Timestamp(
            candle.timestamp
        )

        if ts.tzinfo is None:

            ts = ts.tz_localize(
                "UTC"
            )

        else:

            ts = ts.tz_convert(
                "UTC"
            )

        # -----------------------------------------------------
        # Candle row
        # -----------------------------------------------------

        row = {

            "Open":
                float(candle.open),

            "High":
                float(candle.high),

            "Low":
                float(candle.low),

            "Close":
                float(candle.close),

            "Volume":
                float(candle.volume),
        }

        # -----------------------------------------------------
        # Normalize existing data
        # -----------------------------------------------------

        df = self._normalize_dataframe(
            self.live_data_5m
        )

        # -----------------------------------------------------
        # Update existing candle
        # -----------------------------------------------------

        if ts in df.index:

            for col, value in row.items():

                df.loc[
                    ts,
                    col
                ] = value

        # -----------------------------------------------------
        # Add new candle
        # -----------------------------------------------------

        else:

            new_row = pd.DataFrame(
                [row],
                index=[ts]
            )

            df = pd.concat(
                [
                    df,
                    new_row,
                ]
            )

        # -----------------------------------------------------
        # Sort
        # -----------------------------------------------------

        df = df.sort_index()

        # -----------------------------------------------------
        # Remove duplicate timestamps
        # -----------------------------------------------------

        df = df[
            ~df.index.duplicated(
                keep="last"
            )
        ]

        # -----------------------------------------------------
        # History limit
        # -----------------------------------------------------

        self.live_data_5m = (
            self._limit_dataframe_history(
                df
            )
        )

        return True

    # =========================================================
    # CLOSED FUTURES CANDLE
    # =========================================================

    def on_futures_candle_closed(
        self,
        candle
    ):

        if candle is None:
            return

        try:

            # -------------------------------------------------
            # Normalize timestamp
            # -------------------------------------------------

            ts = pd.Timestamp(
                candle.timestamp
            )

            if ts.tzinfo is None:

                ts = ts.tz_localize(
                    "UTC"
                )

            else:

                ts = ts.tz_convert(
                    "UTC"
                )

            # -------------------------------------------------
            # Duplicate closed candle protection
            # -------------------------------------------------

            if (
                self.last_processed_closed_time
                is not None
                and
                ts
                <=
                self.last_processed_closed_time
            ):

                return

            # -------------------------------------------------
            # Merge final candle
            # -------------------------------------------------

            if not self._merge_live_candle(
                candle
            ):

                return

            # -------------------------------------------------
            # Mark processed
            # -------------------------------------------------

            self.last_processed_closed_time = (
                ts
            )

            # -------------------------------------------------
            # Price fallback
            # -------------------------------------------------

            if not self._has_futures_websocket_price():

                try:

                    self.current_price = float(
                        candle.close
                    )

                except Exception:

                    pass

            # -------------------------------------------------
            # CLOSED CANDLE ANALYSIS
            # -------------------------------------------------

            self._run_closed_candle_analysis(
                candle
            )

        except Exception:

            traceback.print_exc()

    # =========================================================
    # CLOSED CANDLE ANALYSIS
    # =========================================================

    def _run_closed_candle_analysis(
        self,
        candle
    ):

        if not ControllerConfig.ENABLE_CLOSED_CANDLE_ANALYSIS:

            return None

        if (
            self.live_data_5m is None
            or
            self.live_data_15m is None
        ):

            return None

        try:

            # -------------------------------------------------
            # Signal
            # -------------------------------------------------

            signal = (
                self.signal_engine.generate_signal(
                    self.live_data_5m,
                    self.live_data_15m,
                )
            )

            self.latest_signal = (
                signal
            )

            # -------------------------------------------------
            # Trade
            # -------------------------------------------------

            trade = (
                self.trade_manager.generate_trade(
                    signal,
                    self.live_data_5m,
                )
            )

            self.latest_trade = (
                trade
            )

            # -------------------------------------------------
            # Result
            # -------------------------------------------------

            result = (
                self._build_result(
                    signal,
                    trade,
                )
            )

            self.latest_result = (
                result
            )

            self.last_refresh = (
                result[
                    "last_refresh"
                ]
            )

            # -------------------------------------------------
            # Overlay
            # -------------------------------------------------

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
                    self.futures_websocket
                    .health_report()
                )

            except Exception:

                pass

        return {

            "symbol":
                self.symbol,

            "timeframe":
                self.timeframe,

            "higher_timeframe":
                self.higher_timeframe,

            "futures_provider":
                (
                    type(
                        self.futures_provider
                    ).__name__
                    if self.futures_provider
                    else None
                ),

            "futures_symbol":
                (
                    self.futures_provider.symbol
                    if self.futures_provider
                    else None
                ),

            "futures_connected":
                (
                    self.futures_provider.connected
                    if self.futures_provider
                    else False
                ),

            "futures_live_price":
                self.current_price,

            "futures_live_price_source":
                (
                    "WEBSOCKET"
                    if
                    self._has_futures_websocket_price()
                    else
                    "REST_BOOTSTRAP_OR_EXISTING_STATE"
                ),

            "futures_ws_live_price":
                self._last_futures_ws_price,

            "futures_ws_price_initialized":
                self._futures_live_price_initialized,

            "last_futures_tick_timestamp":
                self._last_futures_tick_timestamp,

            "futures_websocket_running":
                (
                    self.futures_websocket.is_running()
                    if self.futures_websocket
                    else False
                ),

            "futures_websocket_connected":
                (
                    self.futures_websocket.is_connected()
                    if self.futures_websocket
                    else False
                ),

            "futures_websocket_healthy":
                (
                    self.futures_websocket.is_connection_healthy()
                    if self.futures_websocket
                    else False
                ),

            "futures_websocket_health":
                futures_ws,

            "live_data_5m_rows":
                (
                    len(
                        self.live_data_5m
                    )
                    if self.live_data_5m is not None
                    else 0
                ),

            "live_data_15m_rows":
                (
                    len(
                        self.live_data_15m
                    )
                    if self.live_data_15m is not None
                    else 0
                ),

            "chart_data_loaded":
                self._chart_data_loaded,

            "chart_loaded_symbol":
                self._chart_loaded_symbol,

            "chart_loaded_timeframe":
                self._chart_loaded_timeframe,

            "chart_loaded_last_timestamp":
                self._chart_loaded_last_timestamp,

            "chart_force_reload":
                self._force_chart_reload,
        }

    # =========================================================
    # HEALTH LOG
    # =========================================================

    def log_health(self):

        print(
            "\n========== Controller Health =========="
        )

        for key, value in (
            self.health_report().items()
        ):

            print(
                f"{key} : {value}"
            )

        print(
            "=======================================\n"
        )

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