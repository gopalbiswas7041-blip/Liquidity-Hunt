"""
============================================================
Liquidity Hunter AI
Controller V20.7 Production Edition
============================================================

Responsibilities
----------------
• Market Data Management
• Live Price Synchronization
• Historical + Live Candle Merge
• Historical Current-Candle Seeding
• Same-Candle OHLCV Continuation
• Signal Engine Pipeline
• Trade Manager Pipeline
• Dashboard Synchronization
• TradingView Chart Synchronization
• Dynamic Symbol Management
• Dynamic Timeframe Management
• Watchlist Support
• WebSocket Lifecycle Management
• Closed Candle Event
• Closed-Candle AI Pipeline
• Duplicate Closed-Candle Protection

V20.7 FIXES
-----------
• Historical candle target = 1000
• Historical current candle is seeded into LiveCandleBuilder
• Active live candle is NOT re-seeded on every refresh
• Historical + live OHLCV merge supported
• Same-candle Open is preserved
• Live High / Low / Close / Volume continuously synchronized
• Closed candle merged into working DataFrame
• Live candle update does NOT reload chart history
• Chart historical data is NOT resent on every refresh
• Chart reset / zoom reset protection
• Historical chart reload only on:
      - first load
      - timeframe change
      - symbol change
      - explicit forced reload
• Closed candle AI refresh does NOT reset chart
• Duplicate closed candle protection retained
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

    DEFAULT_SYMBOL = "B-BTC_USDT"

    DEFAULT_TIMEFRAME = "5m"

    HIGHER_TIMEFRAME = "15m"

    AUTO_REFRESH_SECONDS = 30

    ENABLE_PRICE_SYNC = True

    ENABLE_DYNAMIC_SYMBOL = True

    ENABLE_DYNAMIC_TIMEFRAME = True

    ENABLE_WATCHLIST = True

    SOCKET_URL = (
        "https://stream.coindcx.com"
    )

    SOCKET_CHANNEL_SUFFIX = "@trades"

    ENABLE_CLOSED_CANDLE_ANALYSIS = True

    MARKET_TIMEZONE = "Asia/Kolkata"

    # ======================================================
    # Controller working history
    # ======================================================

    MAX_CANDLE_HISTORY = 1000


# ==========================================================
# Controller
# ==========================================================

class Controller:

    def __init__(self):

        print("=" * 60)
        print("Liquidity Hunter AI")
        print("Controller V20.7")
        print("=" * 60)

        # ==================================================
        # Runtime Configuration
        # ==================================================

        self.symbol = (
            ControllerConfig.DEFAULT_SYMBOL
        )

        self.timeframe = (
            ControllerConfig.DEFAULT_TIMEFRAME
        )

        self.higher_timeframe = (
            ControllerConfig.HIGHER_TIMEFRAME
        )

        # ==================================================
        # Runtime State
        # ==================================================

        self.current_price = None

        self.last_refresh = None

        self.last_tick = None

        self.last_candle = None

        self.latest_signal = None

        self.latest_trade = None

        self.latest_result = {}

        # ==================================================
        # Historical + Live Working Data
        # ==================================================

        self.live_data_5m = None

        self.live_data_15m = None

        # ==================================================
        # Closed Candle Protection
        # ==================================================

        self.last_processed_closed_time = None

        # ==================================================
        # Live Candle Seed Protection
        #
        # Prevents refresh() from repeatedly replacing
        # the active live candle with historical REST data.
        # ==================================================

        self._live_candle_seed_timestamp = None

        # ==================================================
        # CHART SYNCHRONIZATION STATE
        # ==================================================

        self._chart_data_loaded = False

        self._chart_loaded_symbol = None

        self._chart_loaded_timeframe = None

        self._chart_loaded_last_timestamp = None

        self._force_chart_reload = True

        # ==================================================
        # Core Components
        # ==================================================

        self.provider = None

        self.market = None

        self.signal_engine = None

        self.trade_manager = None

        self.atr = None

        self.candle_sync = None

        self.websocket = None

        # ==================================================
        # GUI References
        # ==================================================

        self.dashboard = None

        self.chart_widget = None

        self.chart_overlay = None

        self.watchlist = None

        # ==================================================
        # Provider
        # ==================================================

        self.provider = (
            CoinDCXProvider()
        )

        # ==================================================
        # Market Data
        # ==================================================

        self.market = MarketData(
            self.symbol,
            provider=self.provider
        )

        # ==================================================
        # Signal Engine
        # ==================================================

        self.signal_engine = SignalEngine()

        # ==================================================
        # Trade Manager
        # ==================================================

        self.trade_manager = TradeManager()

        # ==================================================
        # ATR
        # ==================================================

        self.atr = ATR()

        # ==================================================
        # Candle Synchronizer
        # ==================================================

        self.candle_sync = CandleSync()

        # ==================================================
        # WebSocket
        # ==================================================

        self.websocket = CoinDCXWebSocket(
            timeframe=self.timeframe
        )

        self.websocket.set_controller(
            self
        )

        # ==================================================
        # Tick Callback
        # ==================================================

        self.websocket.set_tick_callback(
            self.on_live_tick
        )

        # ==================================================
        # Live Candle Callback
        # ==================================================

        self.websocket.set_candle_callback(
            self.on_live_candle
        )

        # ==================================================
        # Closed Candle Callback
        # ==================================================

        self.websocket.set_candle_closed_callback(
            self.on_candle_closed
        )

        print(
            "Core Engine Initialized"
        )

        print(
            "Runtime Initialized"
        )

    # ======================================================
    # WebSocket
    # ======================================================

    def start_websocket(self):

        if self.websocket is None:

            return

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

    # ======================================================

    def stop_websocket(self):

        if self.websocket:

            self.websocket.disconnect()

    # ======================================================

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

    # ======================================================
    # Timeframe
    # ======================================================

    def change_timeframe(
        self,
        timeframe
    ):

        print(
            "BUTTON CLICKED :",
            timeframe
        )

        if not timeframe:

            return

        timeframe = str(
            timeframe
        )

        if timeframe == self.timeframe:

            print(
                "Timeframe already active:",
                timeframe
            )

            return

        print(
            f"\nChanging Timeframe : "
            f"{self.timeframe} -> {timeframe}"
        )

        # --------------------------------------------------
        # Pause Candle Builder
        # --------------------------------------------------

        if self.websocket:

            try:

                self.websocket.candle_builder.pause()

            except Exception:

                traceback.print_exc()

        # --------------------------------------------------
        # Update timeframe
        # --------------------------------------------------

        self.timeframe = timeframe

        # --------------------------------------------------
        # Reset closed candle protection
        # --------------------------------------------------

        self.last_processed_closed_time = None

        # --------------------------------------------------
        # Reset live candle seed state
        # --------------------------------------------------

        self._live_candle_seed_timestamp = None

        # --------------------------------------------------
        # Change Candle Builder
        # --------------------------------------------------

        if self.websocket:

            try:

                self.websocket.set_timeframe(
                    self.timeframe
                )

            except Exception:

                traceback.print_exc()

        # --------------------------------------------------
        # Clear live working data
        # --------------------------------------------------

        self.live_data_5m = None

        # --------------------------------------------------
        # Clear market cache
        # --------------------------------------------------

        if self.market:

            try:

                self.market.clear_cache()

            except Exception:

                traceback.print_exc()

        # ==================================================
        # Chart MUST receive new historical dataset
        # ==================================================

        self._chart_data_loaded = False

        self._chart_loaded_symbol = None

        self._chart_loaded_timeframe = None

        self._chart_loaded_last_timestamp = None

        self._force_chart_reload = True

        # --------------------------------------------------
        # Resume Candle Builder
        # --------------------------------------------------

        if self.websocket:

            try:

                self.websocket.candle_builder.resume()

            except Exception:

                traceback.print_exc()

        # --------------------------------------------------
        # Reload market data
        # --------------------------------------------------

        self.refresh()

    # ======================================================
    # Refresh
    # ======================================================

    def refresh(self):

        try:

            print(
                "\nRefreshing Market Data..."
            )

            # ==================================================
            # Historical Data
            # ==================================================

            data_5m = (
                self.market.refresh_cache(
                    self.timeframe
                )
            )

            data_15m = (
                self.market.refresh_cache(
                    self.higher_timeframe
                )
            )

            # ==================================================
            # Validate
            # ==================================================

            if data_5m is None:

                print(
                    "ERROR: Market Data is None"
                )

                return {
                    "signal": "ERROR",
                    "confidence": 0,
                    "trade_status": "ERROR",
                    "data_5m": None,
                    "data_15m": data_15m,
                }

            # ==================================================
            # Normalize
            # ==================================================

            data_5m = (
                self._normalize_dataframe(
                    data_5m
                )
            )

            if data_15m is not None:

                data_15m = (
                    self._normalize_dataframe(
                        data_15m
                    )
                )

            # ==================================================
            # LIMIT WORKING HISTORY TO 1000
            # ==================================================

            data_5m = (
                self._limit_dataframe_history(
                    data_5m
                )
            )

            if data_15m is not None:

                data_15m = (
                    self._limit_dataframe_history(
                        data_15m
                    )
                )

            # ==================================================
            # Store Working Data
            # ==================================================

            self.live_data_5m = (
                data_5m.copy()
            )

            if data_15m is not None:

                self.live_data_15m = (
                    data_15m.copy()
                )

            else:

                self.live_data_15m = None

            # ==================================================
            # Debug History
            # ==================================================

            print(
                "5m/Current TF Candles :",
                len(self.live_data_5m)
            )

            if self.live_data_15m is not None:

                print(
                    "15m Candles :",
                    len(self.live_data_15m)
                )

            # ==================================================
            # IMPORTANT V20.7
            #
            # Seed the latest historical candle into the
            # LiveCandleBuilder BEFORE live ticks continue.
            #
            # The helper checks whether the same active candle
            # is already running. Therefore refresh() will NOT
            # reset live OHLCV on every refresh.
            # ==================================================

            self._sync_live_candle_seed()

            # ==================================================
            # WebSocket
            # ==================================================

            if self.websocket:

                if not self.websocket.is_running():

                    self.start_websocket()

            # ==================================================
            # Current Price
            # ==================================================

            if ControllerConfig.ENABLE_PRICE_SYNC:

                try:

                    self.current_price = (
                        self.market.get_live_price()
                    )

                except Exception:

                    self.current_price = None

            # ==================================================
            # Signal Engine
            # ==================================================

            signal = (
                self.signal_engine.generate_signal(
                    self.live_data_5m,
                    self.live_data_15m
                )
            )

            self.latest_signal = signal

            # ==================================================
            # Trade Manager
            # ==================================================

            trade = (
                self.trade_manager.generate_trade(
                    signal,
                    self.live_data_5m
                )
            )

            self.latest_trade = trade

            # ==================================================
            # Build Result
            # ==================================================

            result = self._build_result(
                signal=signal,
                trade=trade
            )

            self.latest_result = result

            self.last_refresh = (
                result["last_refresh"]
            )

            # ==================================================
            # Chart
            # ==================================================

            self._sync_chart()

            # ==================================================
            # Debug
            # ==================================================

            self._print_signal_result(
                result
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
                    self.current_price,

                "signal":
                    "ERROR",

                "confidence":
                    0,

                "trade_status":
                    "ERROR",

                "data_5m":
                    self.live_data_5m,

                "data_15m":
                    self.live_data_15m,

            }

    # ======================================================
    # Limit DataFrame History
    # ======================================================

    def _limit_dataframe_history(
        self,
        dataframe
    ):

        if dataframe is None:

            return None

        if dataframe.empty:

            return dataframe

        max_rows = (
            ControllerConfig
            .MAX_CANDLE_HISTORY
        )

        if len(dataframe) <= max_rows:

            return dataframe

        print(
            f"History > {max_rows}. "
            f"Keeping latest {max_rows} candles."
        )

        return dataframe.iloc[
            -max_rows:
        ].copy()

    # ======================================================
    # DataFrame Normalization
    # ======================================================

    def _normalize_dataframe(
        self,
        dataframe
    ):

        df = dataframe.copy()

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

        df = df.sort_index()

        df = (
            df[
                ~df.index.duplicated(
                    keep="last"
                )
            ]
        )

        return df

    # ======================================================
    # Build Result
    # ======================================================

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

        result["symbol"] = (
            self.symbol
        )

        result["timeframe"] = (
            self.timeframe
        )

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

        return result

    # ======================================================
    # Live Candle Seed Synchronization
    # ======================================================

    def _sync_live_candle_seed(
        self
    ):

        """
        Synchronize the latest historical REST candle with
        LiveCandleBuilder.

        IMPORTANT
        ---------
        This method does NOT blindly seed on every refresh.

        If the LiveCandleBuilder is already working on the
        same candle timestamp, the active candle is preserved.

        This prevents:

            historical refresh
                    ↓
            live OHLC reset
                    ↓
            wrong candle values

        Expected flow:

            Historical REST candle
                    ↓
            Seed once
                    ↓
            Live ticks
                    ↓
            Same candle OHLC continuation
        """

        if self.live_data_5m is None:

            print(
                "Live Candle Seed skipped:"
                " live_data_5m is None"
            )

            return False

        if self.live_data_5m.empty:

            print(
                "Live Candle Seed skipped:"
                " live_data_5m is empty"
            )

            return False

        if self.websocket is None:

            print(
                "Live Candle Seed skipped:"
                " WebSocket unavailable"
            )

            return False

        try:

            builder = (
                self.websocket.candle_builder
            )

        except Exception:

            traceback.print_exc()

            return False

        if builder is None:

            print(
                "Live Candle Seed skipped:"
                " CandleBuilder unavailable"
            )

            return False

        try:

            latest_ts = pd.Timestamp(
                self.live_data_5m.index[-1]
            )

            if latest_ts.tzinfo is None:

                latest_ts = (
                    latest_ts.tz_localize(
                        "UTC"
                    )
                )

            else:

                latest_ts = (
                    latest_ts.tz_convert(
                        "UTC"
                    )
                )

            # ==================================================
            # Check current builder candle
            # ==================================================

            current_candle = (
                builder.get_current_candle()
            )

            if current_candle is not None:

                current_ts = pd.Timestamp(
                    current_candle.timestamp
                )

                if current_ts.tzinfo is None:

                    current_ts = (
                        current_ts.tz_localize(
                            "UTC"
                        )
                    )

                else:

                    current_ts = (
                        current_ts.tz_convert(
                            "UTC"
                        )
                    )

                # --------------------------------------------------
                # Same active candle
                # --------------------------------------------------

                if current_ts == latest_ts:

                    self._live_candle_seed_timestamp = (
                        current_ts
                    )

                    print(
                        "\nLive Candle Seed skipped."
                    )

                    print(
                        "Reason : Active candle already synchronized."
                    )

                    print(
                        "Timestamp :",
                        current_ts
                    )

                    return True

                # --------------------------------------------------
                # Builder is newer than historical REST data
                #
                # Never overwrite a newer live candle.
                # --------------------------------------------------

                if current_ts > latest_ts:

                    self._live_candle_seed_timestamp = (
                        current_ts
                    )

                    print(
                        "\nLive Candle Seed skipped."
                    )

                    print(
                        "Reason : Live candle is newer than REST data."
                    )

                    print(
                        "Live Timestamp       :",
                        current_ts
                    )

                    print(
                        "Historical Timestamp :",
                        latest_ts
                    )

                    return True

            # ==================================================
            # Build Candle from latest historical row
            # ==================================================

            row = (
                self.live_data_5m.iloc[-1]
            )

            from providers.live_candle_builder import Candle

            historical_candle = Candle(

                timestamp=latest_ts.to_pydatetime(),

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

            # ==================================================
            # Seed
            # ==================================================

            seeded = (
                builder.seed_current_candle(
                    historical_candle
                )
            )

            if seeded:

                self._live_candle_seed_timestamp = (
                    latest_ts
                )

                print(
                    "\n========== HISTORICAL → LIVE SYNC =========="
                )

                print(
                    "Timeframe :",
                    self.timeframe
                )

                print(
                    "Timestamp :",
                    latest_ts
                )

                print(
                    "Open      :",
                    historical_candle.open
                )

                print(
                    "High      :",
                    historical_candle.high
                )

                print(
                    "Low       :",
                    historical_candle.low
                )

                print(
                    "Close     :",
                    historical_candle.close
                )

                print(
                    "Volume    :",
                    historical_candle.volume
                )

                print(
                    "Status    : SEEDED"
                )

                print(
                    "============================================\n"
                )

                return True

            print(
                "Historical → Live candle seed failed"
            )

            return False

        except Exception:

            traceback.print_exc()

            return False

    # ======================================================
    # Chart Synchronization
    # ======================================================

    def _sync_chart(self):

        if self.chart_widget is None:

            print(
                "Chart Sync skipped: "
                "ChartWidget not attached"
            )

            return

        if self.live_data_5m is None:

            print(
                "Chart Sync skipped: "
                "No live data"
            )

            return

        try:

            if self.live_data_5m.empty:

                return

            # ==================================================
            # Latest historical candle
            # ==================================================

            latest_timestamp = (
                self.live_data_5m.index[-1]
            )

            latest_timestamp = pd.Timestamp(
                latest_timestamp
            )

            # ==================================================
            # Determine whether historical data REALLY needs
            # to be sent to the chart.
            # ==================================================

            timeframe_changed = (

                self._chart_loaded_timeframe
                != self.timeframe

            )

            symbol_changed = (

                self._chart_loaded_symbol
                != self.symbol

            )

            first_chart_load = not (
                self._chart_data_loaded
            )

            should_reload_chart = (

                first_chart_load

                or

                timeframe_changed

                or

                symbol_changed

                or

                self._force_chart_reload

            )

            # ==================================================
            # IMPORTANT
            #
            # Latest candle updates alone do NOT reload the
            # complete chart.
            #
            # Live candle callback handles those updates.
            # ==================================================

            if should_reload_chart:

                print(
                    "\n========== CHART HISTORICAL LOAD =========="
                )

                print(
                    "Reason:"
                )

                if first_chart_load:

                    print(
                        " - First chart load"
                    )

                if timeframe_changed:

                    print(
                        " - Timeframe changed"
                    )

                if symbol_changed:

                    print(
                        " - Symbol changed"
                    )

                if self._force_chart_reload:

                    print(
                        " - Forced chart reload"
                    )

                print(
                    "Symbol    :",
                    self.symbol
                )

                print(
                    "Timeframe :",
                    self.timeframe
                )

                print(
                    "Candles   :",
                    len(
                        self.live_data_5m
                    )
                )

                print(
                    "Latest    :",
                    latest_timestamp
                )

                print(
                    "============================================"
                )

                self.chart_widget.set_chart_data(
                    self.live_data_5m
                )

                # --------------------------------------------------
                # Register chart state
                # --------------------------------------------------

                self._chart_data_loaded = True

                self._chart_loaded_symbol = (
                    self.symbol
                )

                self._chart_loaded_timeframe = (
                    self.timeframe
                )

                self._chart_loaded_last_timestamp = (
                    latest_timestamp
                )

                self._force_chart_reload = False

            else:

                print(
                    "\nChart historical reload skipped."
                )

                print(
                    "Reason : Existing chart dataset is valid."
                )

                print(
                    "Chart remains untouched."
                )

            # ==================================================
            # Trade Overlay
            # ==================================================

            self._sync_trade_overlay()

        except Exception:

            traceback.print_exc()

    # ======================================================
    # Trade Overlay
    # ======================================================

    def _sync_trade_overlay(self):

        if self.chart_widget is None:

            return

        try:

            result = self.latest_result

            if (

                result.get(
                    "trade_status"
                )
                == "READY"

                and

                result.get(
                    "trade_direction"
                )
                in ["BUY", "SELL"]

            ):

                if (
                    self.live_data_5m is None
                    or
                    len(self.live_data_5m) == 0
                ):

                    return

                timestamp = (
                    self.live_data_5m.index[-1]
                )

                signal_overlay = {

                    "time":
                        int(
                            timestamp.timestamp()
                        ),

                    "direction":
                        result[
                            "trade_direction"
                        ],

                }

                self.chart_widget.show_trade_signal(
                    signal_overlay
                )

        except Exception:

            traceback.print_exc()

    # ======================================================
    # Force Chart Reload
    # ======================================================

    def force_chart_reload(self):

        print(
            "\nFORCING CHART HISTORICAL RELOAD"
        )

        self._force_chart_reload = True

        self._chart_data_loaded = False

        self._chart_loaded_symbol = None

        self._chart_loaded_timeframe = None

        self._chart_loaded_last_timestamp = None

        self._sync_chart()

    # ======================================================
    # Live Tick Callback
    # ======================================================

    def on_live_tick(
        self,
        tick
    ):

        self.last_tick = tick

        if not isinstance(
            tick,
            dict
        ):

            return

        try:

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

    # ======================================================
    # Live Candle Callback
    # ======================================================

    def on_live_candle(
        self,
        candle
    ):

        """
        Called by LiveCandleBuilder whenever the active
        candle changes.

        This method performs TWO synchronizations:

        1. Controller working DataFrame
        2. TradingView chart

        It NEVER calls set_chart_data().

        Therefore live ticks cannot reset chart zoom/history.
        """

        self.last_candle = candle

        if candle is None:

            return

        # ==================================================
        # Merge active live candle into working DataFrame
        # ==================================================

        try:

            self._merge_live_candle(
                candle
            )

        except Exception:

            traceback.print_exc()

        # ==================================================
        # Chart Update
        # ==================================================

        if self.chart_widget is None:

            return

        try:

            self.chart_widget.update_last_candle(
                candle
            )

        except Exception:

            traceback.print_exc()

    # ======================================================
    # Merge Active Live Candle
    # ======================================================

    def _merge_live_candle(
        self,
        candle
    ):

        """
        Merge the CURRENT active candle into live_data_5m.

        This is different from _merge_closed_candle().

        Current candle:
            continuously updated

        Closed candle:
            finalized and processed by AI
        """

        if self.live_data_5m is None:

            print(
                "Live Candle Merge skipped:"
                " live_data_5m is None"
            )

            return False

        ts, row = (
            self._candle_to_row(
                candle
            )
        )

        if ts is None or row is None:

            return False

        try:

            df = (
                self._normalize_dataframe(
                    self.live_data_5m
                )
            )

            columns = [
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
            ]

            # ==================================================
            # Existing active candle
            # ==================================================

            if ts in df.index:

                for column in columns:

                    df.loc[
                        ts,
                        column
                    ] = row[column]

                print(
                    "LIVE CANDLE UPDATED :",
                    ts,
                    "| Close :",
                    row["Close"]
                )

            # ==================================================
            # New live candle
            # ==================================================

            else:

                print(
                    "\nNEW LIVE CANDLE APPENDED :",
                    ts
                )

                new_row = pd.DataFrame(
                    [row],
                    index=pd.DatetimeIndex(
                        [ts]
                    )
                )

                new_row.index.name = (
                    df.index.name
                )

                df = pd.concat(
                    [
                        df,
                        new_row
                    ]
                )

            # ==================================================
            # Sort
            # ==================================================

            df = df.sort_index()

            # ==================================================
            # Duplicate protection
            # ==================================================

            df = (
                df[
                    ~df.index.duplicated(
                        keep="last"
                    )
                ]
            )

            # ==================================================
            # History limit
            # ==================================================

            df = (
                self._limit_dataframe_history(
                    df
                )
            )

            self.live_data_5m = df

            return True

        except Exception:

            traceback.print_exc()

            return False

    # ======================================================
    # Normalize Candle Timestamp
    # ======================================================

    def _normalize_candle_timestamp(
        self,
        candle
    ):

        timestamp = getattr(
            candle,
            "timestamp",
            None
        )

        if timestamp is None:

            return None

        try:

            ts = pd.Timestamp(
                timestamp
            )

            # --------------------------------------------------
            # Naive → UTC
            #
            # LiveCandleBuilder already normalizes timestamps
            # to UTC.
            #
            # Using UTC here avoids accidental India/UTC shift.
            # --------------------------------------------------

            if ts.tzinfo is None:

                ts = ts.tz_localize(
                    "UTC"
                )

            # --------------------------------------------------
            # Convert → UTC
            # --------------------------------------------------

            ts = ts.tz_convert(
                "UTC"
            )

            return ts

        except Exception:

            traceback.print_exc()

            return None

    # ======================================================
    # Candle → DataFrame Row
    # ======================================================

    def _candle_to_row(
        self,
        candle
    ):

        ts = (
            self._normalize_candle_timestamp(
                candle
            )
        )

        if ts is None:

            return None, None

        try:

            row = {

                "Open":
                    float(
                        candle.open
                    ),

                "High":
                    float(
                        candle.high
                    ),

                "Low":
                    float(
                        candle.low
                    ),

                "Close":
                    float(
                        candle.close
                    ),

                "Volume":
                    float(
                        candle.volume
                    ),

            }

            return ts, row

        except Exception:

            traceback.print_exc()

            return None, None

    # ======================================================
    # Merge Closed Candle
    # ======================================================

    def _merge_closed_candle(
        self,
        candle
    ):

        if self.live_data_5m is None:

            print(
                "Cannot merge candle:"
                " live_data_5m is None"
            )

            return False

        ts, row = (
            self._candle_to_row(
                candle
            )
        )

        if ts is None or row is None:

            print(
                "Cannot merge candle:"
                " Invalid candle data"
            )

            return False

        try:

            df = (
                self._normalize_dataframe(
                    self.live_data_5m
                )
            )

            columns = [
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
            ]

            # --------------------------------------------------
            # Existing Candle
            # --------------------------------------------------

            if ts in df.index:

                print(
                    "Closed Candle Existing:"
                    " Updating candle"
                )

                for column in columns:

                    df.loc[
                        ts,
                        column
                    ] = row[column]

            # --------------------------------------------------
            # New Candle
            # --------------------------------------------------

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

                new_row.index.name = (
                    df.index.name
                )

                df = pd.concat(
                    [
                        df,
                        new_row
                    ]
                )

            # --------------------------------------------------
            # Sort
            # --------------------------------------------------

            df = df.sort_index()

            # --------------------------------------------------
            # Remove Duplicate Timestamp
            # --------------------------------------------------

            df = (
                df[
                    ~df.index.duplicated(
                        keep="last"
                    )
                ]
            )

            # --------------------------------------------------
            # Limit History
            # --------------------------------------------------

            df = (
                self._limit_dataframe_history(
                    df
                )
            )

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

    # ======================================================
    # Closed Candle AI
    # ======================================================

    def _run_closed_candle_analysis(
        self,
        candle
    ):

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

        try:

            print(
                "\n" + "=" * 60
            )

            print(
                "V20.7 CLOSED CANDLE AI ANALYSIS"
            )

            print(
                "=" * 60
            )

            print(
                "Time      :",
                candle.timestamp
            )

            print(
                "5m Candle :",
                self.live_data_5m.index[-1]
            )

            print(
                "Close     :",
                self.live_data_5m.iloc[-1]["Close"]
            )

            # ==================================================
            # Signal Engine
            # ==================================================

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

            # ==================================================
            # Trade Manager
            # ==================================================

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

            # ==================================================
            # Build Result
            # ==================================================

            result = self._build_result(
                signal=signal,
                trade=trade
            )

            self.latest_result = result

            self.last_refresh = (
                result["last_refresh"]
            )

            # ==================================================
            # Trade Overlay
            # ==================================================

            self._sync_trade_overlay()

            # ==================================================
            # Final Debug
            # ==================================================

            print(
                "\n========== CLOSED CANDLE RESULT =========="
            )

            print(
                "Signal     :",
                result.get(
                    "signal"
                )
            )

            print(
                "Confidence :",
                result.get(
                    "confidence"
                )
            )

            print(
                "Quality    :",
                result.get(
                    "quality"
                )
            )

            print(
                "Status     :",
                result.get(
                    "status"
                )
            )

            print(
                "Trade      :",
                result.get(
                    "trade_status"
                )
            )

            print(
                "Direction  :",
                result.get(
                    "trade_direction"
                )
            )

            print(
                "===========================================\n"
            )

            return result

        except Exception:

            traceback.print_exc()

            return None

    # ======================================================
    # Closed Candle Callback
    # ======================================================

    def on_candle_closed(
        self,
        candle
    ):

        try:

            print(
                "\n" + "=" * 60
            )

            print(
                "V20.7 CANDLE CLOSED"
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

            # ==================================================
            # Store
            # ==================================================

            self.last_candle = candle

            # ==================================================
            # Normalize Timestamp
            # ==================================================

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

            # ==================================================
            # Duplicate Protection
            # ==================================================

            if (

                self.last_processed_closed_time
                is not None

                and

                closed_ts
                <=
                self.last_processed_closed_time

            ):

                print(
                    "CLOSED CANDLE IGNORED:"
                    " Already processed"
                )

                return

            # ==================================================
            # Merge
            # ==================================================

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

            # ==================================================
            # Mark Processed
            # ==================================================

            self.last_processed_closed_time = (
                closed_ts
            )

            # ==================================================
            # Run AI
            # ==================================================

            self._run_closed_candle_analysis(
                candle
            )

        except Exception:

            traceback.print_exc()

    # ======================================================
    # Health Report
    # ======================================================

    def health_report(
        self
    ):

        current_builder_candle = None

        try:

            if self.websocket:

                current_builder_candle = (
                    self.websocket
                    .candle_builder
                    .get_current_candle()
                )

        except Exception:

            current_builder_candle = None

        return {

            "symbol":
                self.symbol,

            "timeframe":
                self.timeframe,

            "higher_timeframe":
                self.higher_timeframe,

            "provider":
                (
                    type(
                        self.provider
                    ).__name__
                    if self.provider
                    else None
                ),

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

            "live_builder_current_candle":
                current_builder_candle,

            "live_candle_seed_timestamp":
                self._live_candle_seed_timestamp,

            "last_processed_closed_time":
                self.last_processed_closed_time,

            "live_data_5m_rows":
                (
                    len(
                        self.live_data_5m
                    )
                    if self.live_data_5m
                    is not None
                    else 0
                ),

            "live_data_15m_rows":
                (
                    len(
                        self.live_data_15m
                    )
                    if self.live_data_15m
                    is not None
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

    # ======================================================
    # Log Health
    # ======================================================

    def log_health(
        self
    ):

        report = (
            self.health_report()
        )

        print(
            "\n========== "
            "Controller Health "
            "=========="
        )

        for key, value in (
            report.items()
        ):

            print(
                f"{key} : {value}"
            )

        print(
            "=======================================\n"
        )

    # ======================================================
    # Signal Debug
    # ======================================================

    def _print_signal_result(
        self,
        result
    ):

        print(
            "\n========== SIGNAL ENGINE REFRESH =========="
        )

        print(
            "Signal     :",
            result.get(
                "signal"
            )
        )

        print(
            "Confidence :",
            result.get(
                "confidence"
            )
        )

        print(
            "Status     :",
            result.get(
                "status"
            )
        )

        print(
            "Trade      :",
            result.get(
                "trade_status"
            )
        )

        print(
            "Direction  :",
            result.get(
                "trade_direction"
            )
        )

        print(
            "============================================\n"
        )

    # ======================================================
    # Shutdown
    # ======================================================

    def shutdown(
        self
    ):

        print(
            "\nShutting Down Controller..."
        )

        # --------------------------------------------------
        # WebSocket
        # --------------------------------------------------

        try:

            if self.websocket:

                self.websocket.close()

        except Exception:

            traceback.print_exc()

        # --------------------------------------------------
        # Market
        # --------------------------------------------------

        try:

            if self.market:

                self.market.disconnect()

        except Exception:

            traceback.print_exc()

        print(
            "Controller Shutdown Complete"
        )

    # ======================================================
    # Representation
    # ======================================================

    def __repr__(
        self
    ):

        return (

            "Controller("

            f"symbol='{self.symbol}', "

            f"timeframe='{self.timeframe}', "

            f"price={self.current_price}, "

            f"websocket="
            f"{self.websocket is not None}"

            ")"
        )