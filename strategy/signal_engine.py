from indicators.liquidity_sweep_v2 import LiquiditySweepV2
from indicators.market_structure import MarketStructure
from indicators.choch import CHoCH
from indicators.order_block import OrderBlock
from indicators.fair_value_gap import FairValueGap

from strategy.confluence_engine import ConfluenceEngine


class SignalEngine:

    def __init__(self):

        print("Signal Engine Initialized")

        self.liquidity = LiquiditySweepV2()
        self.structure = MarketStructure()
        self.choch = CHoCH()
        self.order_block = OrderBlock()
        self.fvg = FairValueGap()
        self.confluence = ConfluenceEngine()

    def generate_signal(self, data):

        print("Generating Trading Signal...")

        liquidity = self.liquidity.detect(data)
        structure = self.structure.detect(data)
        choch = self.choch.detect(data)
        order_blocks = self.order_block.detect(data)
        fvg = self.fvg.detect(data)

        confluence = self.confluence.analyze(
            liquidity,
            structure,
            choch,
            order_blocks,
            fvg
        )

        return {
            "signal": confluence["direction"],
            "confidence": confluence["confidence"],
            "quality": confluence["quality"],
            "status": confluence["status"],
            "reasons": confluence["reasons"]
        }