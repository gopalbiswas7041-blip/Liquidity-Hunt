from indicators.liquidity_sweep_v2 import LiquiditySweepV2
from indicators.market_structure import MarketStructure
from indicators.choch_v2 import CHoCHV2
from indicators.order_block import OrderBlock
from indicators.fair_value_gap import FairValueGap

from strategy.confluence_engine import ConfluenceEngine
from strategy.multi_timeframe import MultiTimeframe
from strategy.trend_filter import TrendFilter


class SignalEngine:

    def __init__(self):

        print("Signal Engine Initialized")

        self.liquidity = LiquiditySweepV2()
        self.structure = MarketStructure()
        self.choch = CHoCHV2()
        self.order_block = OrderBlock()
        self.fvg = FairValueGap()

        self.confluence = ConfluenceEngine()
        self.multi_timeframe = MultiTimeframe()
        self.trend_filter = TrendFilter()

    def generate_signal(self, data_5m, data_15m):

        print("Generating Trading Signal...")

        # -------------------------
        # 15 Minute Trend
        # -------------------------

        trend = self.trend_filter.analyze(data_15m)

        # -------------------------
        # 5 Minute Analysis
        # -------------------------

        liquidity = self.liquidity.detect(data_5m)
        structure = self.structure.detect(data_5m)
        
        # Smart CHoCH Result
        choch_result = self.choch.detect(
            data_5m,
            structure,
            liquidity
        )
        
        # Compatibility Output for ConfluenceEngine
        choch = self.choch.detect_for_confluence(
            data_5m,
            choch_result,
            structure,
            liquidity
        )

        order_blocks = self.order_block.detect(data_5m)
        fvg = self.fvg.detect(data_5m)

        confluence = self.confluence.analyze(
            liquidity,
            structure,
            choch,
            order_blocks,
            fvg
        )

        signal = {
            "signal": confluence["direction"],
            "confidence": confluence["confidence"],
            "quality": confluence["quality"],
            "status": confluence["status"],
            "reasons": confluence["reasons"]
        }

        # -------------------------
        # Multi-Timeframe
        # -------------------------

        mtf = self.multi_timeframe.analyze(
            trend["trend"],
            signal["signal"]
        )

        print("\n========== TREND FILTER ==========")
        print("Trend     :", trend["trend"])
        print("Status    :", trend["status"])
        print("Reason    :", trend["reason"])

        print("\n========== MULTI TIMEFRAME ==========")
        print("Status    :", mtf["status"])
        print("Direction :", mtf["direction"])
        print("Reason    :", mtf["reason"])

        # Final Status
        signal["status"] = mtf["status"]

        if mtf["direction"] != "NONE":
            signal["signal"] = mtf["direction"]

        return signal