from indicators.market_structure import MarketStructure
from indicators.choch import CHoCH


class TrendFilter:

    def __init__(self):

        print("Trend Filter Engine Initialized")

        self.structure = MarketStructure()
        self.choch = CHoCH()

        # শুধু সাম্প্রতিক Structure বিশ্লেষণ করব
        self.lookback = 15

    def analyze(self, data):

        result = {
            "trend": "NONE",
            "status": "SIDEWAYS",
            "reason": ""
        }

        if data is None or len(data) < 20:
            result["reason"] = "Not enough candles"
            return result

        structures = self.structure.detect(data)
        chochs = self.choch.detect(data)

        bullish = 0
        bearish = 0

        recent_structures = structures[-self.lookback:]
        recent_chochs = chochs[-self.lookback:]

        # Recent BOS
        for s in recent_structures:

            if s["type"] == "Bullish BOS":
                bullish += 2
            elif s["type"] == "Bearish BOS":
                bearish += 2

        # Recent CHoCH
        for c in recent_chochs:

            if c["type"] == "Bullish CHoCH":
                bullish += 3
            elif c["type"] == "Bearish CHoCH":
                bearish += 3

        score = bullish - bearish

        if score >= 5:

            result["trend"] = "BUY"
            result["status"] = "BULLISH"
            result["reason"] = (
                f"Recent Bullish Score {bullish} vs {bearish}"
            )

        elif score <= -5:

            result["trend"] = "SELL"
            result["status"] = "BEARISH"
            result["reason"] = (
                f"Recent Bearish Score {bearish} vs {bullish}"
            )

        else:

            result["trend"] = "NONE"
            result["status"] = "SIDEWAYS"
            result["reason"] = (
                f"Balanced Score ({bullish}-{bearish})"
            )

        return result