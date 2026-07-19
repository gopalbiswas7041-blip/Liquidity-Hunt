from strategy.signal_engine import SignalEngine
from strategy.trade_manager import TradeManager


class BacktestEngine:

    def __init__(self):

        print("Backtest Engine Initialized")

        self.signal_engine = SignalEngine()
        self.trade_manager = TradeManager()

    def run(
        self,
        data_5m,
        data_15m
    ):

        print("Starting Backtest...")

        results = []

        signal = self.signal_engine.generate_signal(
            data_5m,
            data_15m
        )

        trade = self.trade_manager.generate_trade(
            signal,
            data_5m
        )

        results.append(trade)

        print(f"Trades Processed : {len(results)}")

        return results