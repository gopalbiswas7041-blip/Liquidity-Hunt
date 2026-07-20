# ==========================================
# Liquidity Hunter AI V14.2.2
# controller.py
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

            # Load cached data
            data_5m = self.market.load_data("5m")
            data_15m = self.market.load_data("15m")

            # Check for new candles
            if self.candle_sync.is_new_candle("5m", data_5m):
                data_5m = self.market.refresh_cache("5m")

            if self.candle_sync.is_new_candle("15m", data_15m):
                data_15m = self.market.refresh_cache("15m")

            # ATR
            volatility = self.atr.get_volatility(data_5m)

            # Signal
            signal = self.engine.generate_signal(
                data_5m,
                data_15m
            )

            # Trade
            trade = self.trade_manager.generate_trade(
                signal,
                data_5m
            )

            return {

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

                "trade_reason": trade.get("trade_reason", [])

            }

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

                "trade_reason": [str(e)]

            }