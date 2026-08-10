"""
============================================================
Liquidity Hunter AI
Controller V20.4 Production Edition
============================================================

Responsibilities
----------------
* Market Data Management
* Live Price Synchronization
* Historical + Live Candle Merge
* Signal Engine Pipeline
* Trade Manager Pipeline
* Dashboard Synchronization
* TradingView Chart Synchronization
* Dynamic Symbol Management
* Dynamic Timeframe Management
* Watchlist Support
* WebSocket Lifecycle Management
* V20.3 Closed Candle Event
* V20.4 Live Closed-Candle AI Pipeline
============================================================
"""

from __future__ import annotations

import traceback

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from data.market_data import MarketData

from strategy.signal_engine import SignalEngine
from strategy.trade_manager import TradeManager

from indicators.atr import ATR

from providers.coindcx_provider import CoinDCXProvider
from providers.coindcx_websocket import CoinDCXWebSocket

from utils.candle_sync import CandleSync
from ui.chart_overlay import ChartOverlay


# ==========================================================
# Controller Configuration
# ==========================================================

@dataclass
class ControllerConfig:

    # Default Trading Pair
    DEFAULT_SYMBOL = "B-BTC_USDT"

    # Timeframes
    DEFAULT_TIMEFRAME = "5m"
    HIGHER_TIMEFRAME = "15m"

    # Refresh
    AUTO_REFRESH_SECONDS = 30

    # Feature Flags
    ENABLE_PRICE_SYNC = True
    ENABLE_DYNAMIC_SYMBOL = True
    ENABLE_DYNAMIC_TIMEFRAME = True
    ENABLE_WATCHLIST = True

    # WebSocket
    SOCKET_URL = "https://stream.coindcx.com"
    SOCKET_CHANNEL_SUFFIX = "@trades"

    # Live AI
    ENABLE_CLOSED_CANDLE_ANALYSIS = True

    # Project market-data timezone
    MARKET_TIMEZONE = "Asia/Kolkata"


# ==========================================================
# Controller
# ==========================================================

class Controller:

    def __init__(self):

        print("=" * 60)
        print("Liquidity Hunter AI")
        print("Controller V20.4")
        print("=" * 60)

        # ------------------------------------------
        # Runtime Configuration
        # ------------------------------------------

        self.symbol = ControllerConfig.DEFAULT_SYMBOL

        self.timeframe = (
            ControllerConfig.DEFAULT_TIMEFRAME
        )

        self.higher_timeframe = (
            ControllerConfig.HIGHER_TIMEFRAME
        )

        # ------------------------------------------
        # Runtime State
        # ------------------------------------------

        self.current_price = None

        self.last_refresh = None

        self.last_tick = None

        self.last_candle = None

        self.latest_signal = None

        self.latest_trade = None

        self.latest_result = {}

        # Historical + live working data
        self.live_data_5m = None
        self.live_data_15m = None

        # Last closed candle processed by AI
        self.last_processed_closed_time = None

        # ------------------------------------------
        # Core Components
        # ------------------------------------------

        self.provider = None

        self.market = None

        self.signal_engine = None

        self.trade_manager = None

        self.atr = None

        self.candle_sync = None

        self.websocket = None

        # ------------------------------------------
        # GUI References
        # ------------------------------------------

        self.dashboard = None

        self.chart_widget = None

        self.chart_overlay = None

        self.watchlist = None

        # ------------------------------------------
        # Provider
        # ------------------------------------------

        self.provider = CoinDCXProvider()

        # ------------------------------------------
        # Market Data
        # ------------------------------------------

        self.market = MarketData(
            self.symbol,
            provider=self.provider
        )

        # ------------------------------------------
        # Signal Engine
        # ------------------------------------------

        self.signal_engine = SignalEngine()

        # ------------------------------------------
        # Trade Manager
        # ------------------------------------------

        self.trade_manager = TradeManager()

        # ------------------------------------------
        # ATR
        # ------------------------------------------

        self.atr = ATR()

        # ------------------------------------------
        # Candle Synchronizer
        # ------------------------------------------

        self.candle_sync = CandleSync()

        # ------------------------------------------
        # WebSocket
        # ------------------------------------------

        self.websocket = CoinDCXWebSocket(
            timeframe=self.timeframe
        )

        self.websocket.set_controller(self)

        # ------------------------------------------
        # Live Tick Callback
        # ------------------------------------------

        self.websocket.set_tick_callback(
            self.on_live_tick
        )

        # ------------------------------------------
        # Live Candle Callback
        # ------------------------------------------

        self.websocket.set_candle_callback(
            self.on_live_candle
        )

        # ------------------------------------------
        # Closed Candle Callback
        # ------------------------------------------

        self.websocket.set_candle_closed_callback(
            self.on_candle_closed
        )

        print("Core Engine Initialized")
        print("Runtime Initialized")

    # ==================================================
    # WebSocket
    # ==================================================

    def start_websocket(self):

        if self.websocket.is_running():
            return

        channel = (
            f"{self.symbol}"
            f"{ControllerConfig.SOCKET_CHANNEL_SUFFIX}"
        )

        print(
            f"Starting WebSocket : {channel}"
        )

        self.websocket.connect(
            url=ControllerConfig.SOCKET_URL,
            symbol=channel
        )

    # ==================================================

    def stop_websocket(self):

        if self.websocket:

            self.websocket.disconnect()

    # ==================================================

    def restart_websocket(self):

        if not self.websocket:
            return

        self.websocket.disconnect()

        channel = (
            f"{self.symbol}"
            f"{ControllerConfig.SOCKET_CHANNEL_SUFFIX}"
        )

        self.websocket.connect(
            url=ControllerConfig.SOCKET_URL,
            symbol=channel
        )

    # ==================================================
    # Change Timeframe
    # ==================================================

    def change_timeframe(self, timeframe):

        print(
            "BUTTON CLICKED :",
            timeframe
        )

        if timeframe == self.timeframe:
            return

        print(
            f"\nChanging Timeframe : "
            f"{self.timeframe} -> {timeframe}"
        )

        # ------------------------------------------
        # Update Controller Timeframe
        # ------------------------------------------

        self.timeframe = timeframe

        # ------------------------------------------
        # Reset Closed Candle Protection
        # ------------------------------------------

        self.last_processed_closed_time = None

        # ------------------------------------------
        # Change Live Candle Builder Timeframe
        # ------------------------------------------

        if self.websocket:

            self.websocket.set_timeframe(
                timeframe
            )

        # ------------------------------------------
        # Clear Historical Cache
        # ------------------------------------------

        if self.market:

            self.market.clear_cache()

        # ------------------------------------------
        # Reload Market Data
        # ------------------------------------------

        self.refresh()

    # ==================================================
    # Refresh
    # ==================================================

    def refresh(self):

        try:

            print(
                "\nRefreshing Market Data..."
            )

            # ------------------------------------------
            # Historical Data
            # ------------------------------------------

            data_5m = self.market.refresh_cache(
                self.timeframe
            )

            data_15m = self.market.refresh_cache(
                self.higher_timeframe
            )

            # ------------------------------------------
            # Validate Data
            # ------------------------------------------

            if data_5m is None:

                print(
                    "ERROR: 5m Market Data is None"
                )

                return {
                    "signal": "ERROR",
                    "confidence": 0,
                    "trade_status": "ERROR",
                    "data_5m": None,
                    "data_15m": data_15m
                }

            # ------------------------------------------
            # Store Working Data
            # ------------------------------------------

            self.live_data_5m = data_5m.copy()

            if data_15m is not None:

                self.live_data_15m = (
                    data_15m.copy()
                )

            else:

                self.live_data_15m = data_15m

            # ------------------------------------------
            # Ensure WebSocket Running
            # ------------------------------------------

            if not self.websocket.is_running():

                self.start_websocket()

            # ------------------------------------------
            # Current Price
            # ------------------------------------------

            try:

                self.current_price = (
                    self.market.get_live_price()
                )

            except Exception:

                self.current_price = None

            # ------------------------------------------
            # Signal Generation
            # ------------------------------------------

            signal = (
                self.signal_engine.generate_signal(
                    self.live_data_5m,
                    self.live_data_15m
                )
            )

            self.latest_signal = signal

            # ------------------------------------------
            # Trade Generation
            # ------------------------------------------

            trade = (
                self.trade_manager.generate_trade(
                    signal,
                    self.live_data_5m
                )
            )

            self.latest_trade = trade

            # ------------------------------------------
            # Build Final Result
            # ------------------------------------------

            result = {}

            if isinstance(signal, dict):

                result.update(signal)

            if isinstance(trade, dict):

                result.update(trade)

            result["symbol"] = self.symbol

            result["timeframe"] = self.timeframe

            result["live_price"] = (
                self.current_price
            )

            result["data_5m"] = (
                self.live_data_5m
            )

            result["data_15m"] = (
                self.live_data_15m
            )

            result["last_refresh"] = (
                datetime.now()
            )

            self.latest_result = result

            self.last_refresh = (
                result["last_refresh"]
            )

            # ------------------------------------------
            # Chart Synchronization
            # ------------------------------------------

            if self.chart_widget is not None:

                self.chart_widget.set_chart_data(
                    self.live_data_5m
                )

                # --------------------------------------
                # AI Trade Signal Overlay
                # --------------------------------------

                try:

                    if (
                        result.get("trade_status")
                        == "READY"
                        and
                        result.get("trade_direction")
                        in ["BUY", "SELL"]
                    ):

                        print(
                            "Sending Trade Signal To JS"
                        )

                        signal_overlay = {

                            "time": int(
                                self.live_data_5m.index[-1]
                                .timestamp()
                            ),

                            "direction":
                                result[
                                    "trade_direction"
                                ]
                        }

                        self.chart_widget.show_trade_signal(
                            signal_overlay
                        )

                except Exception:

                    traceback.print_exc()

            print(
                "\n========== SIGNAL ENGINE REFRESH =========="
            )

            print(
                "Signal     :",
                result.get("signal")
            )

            print(
                "Confidence :",
                result.get("confidence")
            )

            print(
                "Status     :",
                result.get("status")
            )

            print(
                "Trade      :",
                result.get("trade_status")
            )

            print(
                "============================================\n"
            )

            return result

        except Exception:

            traceback.print_exc()

            return {

                "symbol":
                    self.symbol,

                "timeframe":
                    self.timeframe,

                "live_price":
                    None,

                "signal":
                    "ERROR",

                "confidence":
                    0,

                "trade_status":
                    "ERROR",

                "data_5m":
                    None,

                "data_15m":
                    None

            }

    # ==================================================
    # Live Tick Callback
    # ==================================================

    def on_live_tick(self, tick):

        self.last_tick = tick

        try:

            if isinstance(tick, dict):

                # CoinDCX normally uses "p"
                # but keep "price" compatibility.

                price = tick.get(
                    "price",
                    tick.get("p")
                )

                if price is not None:

                    self.current_price = float(
                        price
                    )

        except Exception:

            traceback.print_exc()

    # ==================================================
    # Live Candle Callback
    # ==================================================

    def on_live_candle(self, candle):

        self.last_candle = candle

        # ------------------------------------------
        # Chart Update
        # ------------------------------------------

        if self.chart_widget is None:

            return

        try:

            self.chart_widget.update_last_candle(
                candle
            )

        except Exception:

            traceback.print_exc()

    # ==================================================
    # Normalize Candle Timestamp
    # ==================================================

    def _normalize_candle_timestamp(self, candle):

        """
        Convert Live Candle timestamp into
        UTC-aware pandas Timestamp.

        Historical MarketData uses UTC timestamps.

        CoinDCX Live Candle may arrive as a naive
        datetime representing Asia/Kolkata local time.
        """

        timestamp = getattr(
            candle,
            "timestamp",
            None
        )

        if timestamp is None:

            return None

        try:

            ts = pd.Timestamp(timestamp)

            # --------------------------------------
            # Naive timestamp
            # --------------------------------------

            if ts.tzinfo is None:

                ts = ts.tz_localize(
                    ControllerConfig.MARKET_TIMEZONE
                )

            # --------------------------------------
            # Convert to UTC
            # --------------------------------------

            ts = ts.tz_convert("UTC")

            return ts

        except Exception:

            traceback.print_exc()

            return None

    # ==================================================
    # Convert Candle To DataFrame Row
    # ==================================================

    def _candle_to_row(self, candle):

        ts = self._normalize_candle_timestamp(
            candle
        )

        if ts is None:

            return None, None

        try:

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
                    float(candle.volume)

            }

            return ts, row

        except Exception:

            traceback.print_exc()

            return None, None

    # ==================================================
    # Merge Closed Candle Into 5m Data
    # ==================================================

    def _merge_closed_candle(
        self,
        candle
    ):

        """
        Merge one CLOSED candle into the
        working 5m DataFrame.

        Existing timestamp:
            Replace candle.

        New timestamp:
            Append candle.

        Result:
            Sorted UTC DataFrame.
        """

        if self.live_data_5m is None:

            print(
                "Cannot merge candle: "
                "live_data_5m is None"
            )

            return False

        ts, row = self._candle_to_row(
            candle
        )

        if ts is None or row is None:

            print(
                "Cannot merge candle: "
                "Invalid candle data"
            )

            return False

        try:

            df = self.live_data_5m.copy()

            # --------------------------------------
            # Normalize DataFrame Index
            # --------------------------------------

            if not isinstance(
                df.index,
                pd.DatetimeIndex
            ):

                df.index = pd.to_datetime(
                    df.index,
                    utc=True
                )

            else:

                if df.index.tz is None:

                    df.index = (
                        df.index
                        .tz_localize("UTC")
                    )

                else:

                    df.index = (
                        df.index
                        .tz_convert("UTC")
                    )

            # --------------------------------------
            # Update / Append
            # --------------------------------------

            if ts in df.index:

                print(
                    "Closed Candle Existing:"
                    " Updating historical candle"
                )

                df.loc[ts, [
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume"
                ]] = [

                    row["Open"],
                    row["High"],
                    row["Low"],
                    row["Close"],
                    row["Volume"]

                ]

            else:

                print(
                    "Closed Candle New:"
                    " Appending candle"
                )

                new_row = pd.DataFrame(
                    [row],
                    index=pd.DatetimeIndex(
                        [ts]
                    )
                )

                df = pd.concat(
                    [
                        df,
                        new_row
                    ]
                )

            # --------------------------------------
            # Sort
            # --------------------------------------

            df = df.sort_index()

            # --------------------------------------
            # Remove Duplicate Index
            # --------------------------------------

            df = (
                df[
                    ~df.index.duplicated(
                        keep="last"
                    )
                ]
            )

            # --------------------------------------
            # Keep Reasonable History
            # --------------------------------------

            if len(df) > 500:

                df = df.iloc[-500:]

            self.live_data_5m = df

            print(
                "\n========== LIVE DATA MERGE =========="
            )

            print(
                "Merged Candle UTC :",
                ts
            )

            print(
                "Rows              :",
                len(df)
            )

            print(
                "Latest Close      :",
                df.iloc[-1]["Close"]
            )

            print(
                "Latest Timestamp  :",
                df.index[-1]
            )

            print(
                "======================================\n"
            )

            return True

        except Exception:

            traceback.print_exc()

            return False

    # ==================================================
    # Run AI On Closed Candle
    # ==================================================

    def _run_closed_candle_analysis(
        self,
        candle
    ):

        """
        Run the complete AI pipeline after a
        CLOSED candle has been merged.

        Pipeline:

        Closed Candle
             ↓
        data_5m update
             ↓
        SignalEngine
             ↓
        TradeManager
             ↓
        latest_result
             ↓
        Chart Overlay
        """

        try:

            if not ControllerConfig.ENABLE_CLOSED_CANDLE_ANALYSIS:

                print(
                    "Closed Candle AI Analysis Disabled"
                )

                return None

            if self.live_data_5m is None:

                print(
                    "AI Analysis skipped:"
                    " live_data_5m is None"
                )

                return None

            if self.live_data_15m is None:

                print(
                    "AI Analysis skipped:"
                    " live_data_15m is None"
                )

                return None

            # --------------------------------------
            # Generate Signal
            # --------------------------------------

            print(
                "\n" + "=" * 60
            )

            print(
                "V20.4 CLOSED CANDLE AI ANALYSIS"
            )

            print(
                "=" * 60
            )

            print(
                "5m Candle :",
                self.live_data_5m.index[-1]
            )

            print(
                "Close     :",
                self.live_data_5m.iloc[-1]["Close"]
            )

            print(
                "Running SignalEngine..."
            )

            signal = (
                self.signal_engine.generate_signal(
                    self.live_data_5m,
                    self.live_data_15m
                )
            )

            self.latest_signal = signal

            # --------------------------------------
            # Generate Trade
            # --------------------------------------

            print(
                "Running TradeManager..."
            )

            trade = (
                self.trade_manager.generate_trade(
                    signal,
                    self.live_data_5m
                )
            )

            self.latest_trade = trade

            # --------------------------------------
            # Final Result
            # --------------------------------------

            result = {}

            if isinstance(signal, dict):

                result.update(signal)

            if isinstance(trade, dict):

                result.update(trade)

            result["symbol"] = self.symbol

            result["timeframe"] = self.timeframe

            result["live_price"] = (
                self.current_price
            )

            result["data_5m"] = (
                self.live_data_5m
            )

            result["data_15m"] = (
                self.live_data_15m
            )

            result["last_refresh"] = (
                datetime.now()
            )

            self.latest_result = result

            self.last_refresh = (
                result["last_refresh"]
            )

            # --------------------------------------
            # Chart Trade Signal
            # --------------------------------------

            if self.chart_widget is not None:

                try:

                    if (
                        result.get("trade_status")
                        == "READY"
                        and
                        result.get("trade_direction")
                        in ["BUY", "SELL"]
                    ):

                        print(
                            "Sending Closed-Candle "
                            "Trade Signal To JS"
                        )

                        signal_overlay = {

                            "time": int(
                                self.live_data_5m.index[-1]
                                .timestamp()
                            ),

                            "direction":
                                result[
                                    "trade_direction"
                                ]

                        }

                        self.chart_widget.show_trade_signal(
                            signal_overlay
                        )

                except Exception:

                    traceback.print_exc()

            # --------------------------------------
            # Final Debug
            # --------------------------------------

            print(
                "\n========== CLOSED CANDLE RESULT =========="
            )

            print(
                "Signal     :",
                result.get("signal")
            )

            print(
                "Confidence :",
                result.get("confidence")
            )

            print(
                "Quality    :",
                result.get("quality")
            )

            print(
                "Status     :",
                result.get("status")
            )

            print(
                "Trade      :",
                result.get("trade_status")
            )

            print(
                "Direction  :",
                result.get("trade_direction")
            )

            print(
                "===========================================\n"
            )

            return result

        except Exception:

            traceback.print_exc()

            return None

    # ==================================================
    # V20.4 Closed Candle Callback
    # ==================================================

    def on_candle_closed(self, candle):

        try:

            print(
                "\n" + "=" * 60
            )

            print(
                "V20.4 CANDLE CLOSED"
            )

            print(
                "=" * 60
            )

            print(
                "Time   :",
                candle.timestamp
            )

            print(
                "Open   :",
                candle.open
            )

            print(
                "High   :",
                candle.high
            )

            print(
                "Low    :",
                candle.low
            )

            print(
                "Close  :",
                candle.close
            )

            print(
                "Volume :",
                candle.volume
            )

            print(
                "=" * 60
            )

            # ------------------------------------------
            # Store Latest Closed Candle
            # ------------------------------------------

            self.last_candle = candle

            # ------------------------------------------
            # Normalize Timestamp
            # ------------------------------------------

            closed_ts = (
                self._normalize_candle_timestamp(
                    candle
                )
            )

            if closed_ts is None:

                print(
                    "Closed Candle rejected:"
                    " Invalid timestamp"
                )

                return

            print(
                "Normalized Closed Time :",
                closed_ts
            )

            # ------------------------------------------
            # Duplicate Protection
            # ------------------------------------------

            if (
                self.last_processed_closed_time
                is not None
                and
                closed_ts
                <= self.last_processed_closed_time
            ):

                print(
                    "CLOSED CANDLE IGNORED:"
                    " Already processed"
                )

                return

            # ------------------------------------------
            # Merge Candle
            # ------------------------------------------

            merged = (
                self._merge_closed_candle(
                    candle
                )
            )

            if not merged:

                print(
                    "Closed Candle merge failed"
                )

                return

            # ------------------------------------------
            # Mark Processed
            # ------------------------------------------

            self.last_processed_closed_time = (
                closed_ts
            )

            # ------------------------------------------
            # Run AI
            # ------------------------------------------

            self._run_closed_candle_analysis(
                candle
            )

        except Exception:

            traceback.print_exc()

    # ==================================================
    # Shutdown
    # ==================================================

    def shutdown(self):

        print(
            "\nShutting Down Controller..."
        )

        try:

            if self.websocket:

                self.websocket.disconnect()

        except Exception:

            traceback.print_exc()

        try:

            if self.market:

                self.market.disconnect()

        except Exception:

            traceback.print_exc()

        print(
            "Controller Shutdown Complete"
        )

    # ==================================================
    # Health Report
    # ==================================================

    def health_report(self):

        return {

            "symbol":
                self.symbol,

            "timeframe":
                self.timeframe,

            "provider":
                type(
                    self.provider
                ).__name__,

            "websocket_running":
                (
                    self.websocket.is_running()
                    if self.websocket
                    else False
                ),

            "websocket_connected":
                (
                    self.websocket.is_connected()
                    if self.websocket
                    else False
                ),

            "live_price":
                self.current_price,

            "last_refresh":
                self.last_refresh,

            "last_tick":
                self.last_tick,

            "last_candle":
                self.last_candle,

            "last_processed_closed_time":
                self.last_processed_closed_time,

            "live_data_5m_rows":
                (
                    len(self.live_data_5m)
                    if self.live_data_5m is not None
                    else 0
                )

        }

    # ==================================================
    # Log Health
    # ==================================================

    def log_health(self):

        report = self.health_report()

        print(
            "\n========== "
            "Controller Health "
            "=========="
        )

        for key, value in report.items():

            print(
                f"{key} : {value}"
            )

        print(
            "=======================================\n"
        )