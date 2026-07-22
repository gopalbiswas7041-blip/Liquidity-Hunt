# ==========================================
# Liquidity Hunter AI V17
# ui/controller.py
# ==========================================

from data.market_data import MarketData
from strategy.signal_engine import SignalEngine
from strategy.trade_manager import TradeManager
from indicators.atr import ATR
from providers.coindcx_provider import CoinDCXProvider
from utils.candle_sync import CandleSync


class Controller:

    def __init__(self):

        self.market = MarketData(
            "B-BTC_USDT",
            provider=CoinDCXProvider()
        )

        self.engine = SignalEngine()
        self.trade_manager = TradeManager()
        self.atr = ATR()

        # Smart Candle Sync
        self.candle_sync = CandleSync()

    def refresh(self):
        """
        Load latest market data and return
        all information required by the GUI.
        """

        try:

            # -------------------------
            # Load Market Data
            # -------------------------

            data_5m = self.market.load_data("5m")
            data_15m = self.market.load_data("15m")

            # -------------------------
            # Refresh only if new candle
            # -------------------------

            if self.candle_sync.is_new_candle("5m", data_5m):
                data_5m = self.market.refresh_cache("5m")

            if self.candle_sync.is_new_candle("15m", data_15m):
                data_15m = self.market.refresh_cache("15m")

            # -------------------------
            # ATR
            # -------------------------

            volatility = self.atr.get_volatility(data_5m)

            # -------------------------
            # Signal Engine
            # -------------------------

            signal = self.engine.generate_signal(
                data_5m,
                data_15m
            )

            # -------------------------
            # Trade Manager
            # -------------------------

            trade = self.trade_manager.generate_trade(
                signal,
                data_5m
            )

            # -------------------------
            # Market Context
            # -------------------------

            market_context = {

                "trend": signal.get("trend", "UNKNOWN"),
                "market_phase": signal.get("market_phase", "UNKNOWN"),
                "liquidity_sweep": signal.get("liquidity_sweep", False),
                "choch": signal.get("choch", False),
                "order_block": signal.get("order_block", False),
                "fvg": signal.get("fvg", False)

            }

            # -------------------------
            # GUI Data
            # -------------------------

            result = {

                "symbol": "BTCUSDT",
                "timeframe": "5 Minute",

                "signal": trade.get("signal", "NO TRADE"),
                "confidence": trade.get("confidence", 0),
                "quality": trade.get("quality", "-"),
                "status": trade.get("status", "-"),

                "entry": trade.get("entry", "--"),
                "stop_loss": trade.get("stop_loss", "--"),
                "take_profit": trade.get("take_profit", "--"),

                "risk": trade.get("risk", "--"),
                "reward": trade.get("reward", "--"),
                "risk_reward": trade.get("risk_reward", "--"),

                "volatility": volatility,

                "trade_score": trade.get("trade_score", 0),
                "trade_status": trade.get("trade_status", "WAIT"),

                "entry_type": trade.get("entry_type", "--"),
                "entry_zone": trade.get("entry_zone", "--"),
                "confirmation": trade.get("confirmation", "--"),
                "entry_quality": trade.get("entry_quality", "--"),

                "trend": market_context["trend"],
                "market_phase": market_context["market_phase"],
                "liquidity_sweep": market_context["liquidity_sweep"],
                "choch": market_context["choch"],
                "order_block": market_context["order_block"],
                "fvg": market_context["fvg"],

                "trade_reason": trade.get("trade_reason", []),

                # Chart Data
                "data_5m": data_5m,
                "data_15m": data_15m

            }

            return result

        except Exception as e:

            return {

                "symbol": "BTCUSDT",
                "timeframe": "5 Minute",

                "signal": "ERROR",
                "confidence": 0,
                "quality": "-",
                "status": "ERROR",

                "entry": "--",
                "stop_loss": "--",
                "take_profit": "--",

                "risk": "--",
                "reward": "--",
                "risk_reward": "--",

                "volatility": "UNKNOWN",

                "trade_score": 0,
                "trade_status": "ERROR",

                "entry_type": "--",
                "entry_zone": "--",
                "confirmation": "--",
                "entry_quality": "--",

                "trend": "--",
                "market_phase": "--",
                "liquidity_sweep": "--",
                "choch": "--",
                "order_block": "--",
                "fvg": "--",

                "trade_reason": [str(e)],

                # Empty Chart Data
                "data_5m": None,
                "data_15m": None

            }