"""
============================================================
Liquidity Hunter AI
Controller V19 Production Edition
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
============================================================
"""

from __future__ import annotations

import traceback

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

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

# ==========================================================
# Controller
# ==========================================================

class Controller:

    def __init__(self):

        print("=" * 60)
        print("Liquidity Hunter AI")
        print("Controller V19 Production")
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

        self.live_data_5m = None

        self.live_data_15m = None

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

        self.websocket = CoinDCXWebSocket()

        self.websocket.set_controller(self)

        self.websocket.set_tick_callback(
            self.on_live_tick
        )

        self.websocket.set_candle_callback(
            self.on_live_candle
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

        print(f"Starting WebSocket : {channel}")

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

        print("BUTTON CLICKED :", timeframe)

        if timeframe == self.timeframe:
            return

        print(f"\nChanging Timeframe : {timeframe}")

        self.timeframe = timeframe

        # Change Live Candle Builder Timeframe
        self.websocket.set_timeframe(
            timeframe
        )

        # Clear Historical Data Cache
        self.market.clear_cache()

        # Reload Market Data
        self.refresh()

    # ==================================================
    # Refresh
    # ==================================================

    def refresh(self):

        try:

            print("\nRefreshing Market Data...")

            # ------------------------------------------
            # Historical Data
            # ------------------------------------------

            data_5m = self.market.refresh_cache(
            self.timeframe
            )

            data_15m = self.market.refresh_cache(
            self.higher_timeframe
            )

            self.live_data_5m = data_5m

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

            signal = self.signal_engine.generate_signal(
                data_5m,
                data_15m
            )

            self.latest_signal = signal

            # ------------------------------------------
            # Trade Generation
            # ------------------------------------------

            trade = self.trade_manager.generate_trade(
                signal,
                data_5m
            )

            self.latest_trade = trade

            # ------------------------------------------
            # Final Result
            # ------------------------------------------

            result = {}

            if isinstance(signal, dict):
                result.update(signal)

            if isinstance(trade, dict):
                result.update(trade)

            result["symbol"] = self.symbol
            result["timeframe"] = self.timeframe
            result["live_price"] = self.current_price
            result["data_5m"] = data_5m
            result["data_15m"] = data_15m
            result["last_refresh"] = datetime.now()

            self.latest_result = result
            self.last_refresh = result["last_refresh"]

            if self.chart_widget is not None:

                # Historical Chart
                self.chart_widget.set_chart_data(data_5m)

                # ------------------------------------------
                # AI Trade Signal Overlay
                # ------------------------------------------

                try:

                    if (
                        result.get("trade_status") == "READY"
                        and result.get("trade_direction") in ["BUY", "SELL"]
                    ):

                        print("Sending Trade Signal To JS")

                        signal = {
                            "time": int(data_5m.index[-1].timestamp()),
                            "direction": result["trade_direction"]
                        }

                        self.chart_widget.show_trade_signal(signal)

                except Exception:
                    traceback.print_exc()

            return result

        except Exception:

            traceback.print_exc()

            return {

                "symbol": self.symbol,

                "timeframe": self.timeframe,

                "live_price": None,

                "signal": "ERROR",

                "confidence": 0,

                "trade_status": "ERROR",

                "data_5m": None,

                "data_15m": None

            }

    # ==================================================
    # Live Tick Callback
    # ==================================================

    def on_live_tick(self, tick):

        self.last_tick = tick

        try:

            if isinstance(tick, dict):

                self.current_price = float(
                    tick.get(
                        "price",
                        self.current_price or 0
                    )
                )

        except Exception:

            pass

    # ==================================================
    # Live Candle Callback
    # ==================================================

    def on_live_candle(self, candle):

        self.last_candle = candle

        if self.chart_widget is None:
            return

        try:

            self.chart_widget.update_last_candle(
                candle
            )

        except Exception:

            traceback.print_exc()

    # ==================================================
    # Shutdown
    # ==================================================

    def shutdown(self):

        print("\nShutting Down Controller...")

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

        print("Controller Shutdown Complete")

    # ==================================================
    # Health Report
    # ==================================================

    def health_report(self):

        return {

            "symbol": self.symbol,

            "timeframe": self.timeframe,

            "provider": type(self.provider).__name__,

            "websocket_running": (
                self.websocket.is_running()
                if self.websocket else False
            ),

            "live_price": self.current_price,

            "last_refresh": self.last_refresh,

            "last_tick": self.last_tick,

            "last_candle": self.last_candle

        }

    # ==================================================
    # Log Health
    # ==================================================

    def log_health(self):

        report = self.health_report()

        print("\n========== Controller Health ==========")

        for key, value in report.items():

            print(f"{key} : {value}")

        print("=======================================\n")