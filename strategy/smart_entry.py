# ==========================================
# Liquidity Hunter AI V14.3
# Smart Entry Engine
# ==========================================

class SmartEntryEngine:

    def __init__(self):

        print("Smart Entry Engine Initialized")

    def analyze(self, signal, trade):

        result = {

            "entry_type": "NONE",
            "entry_zone": None,
            "confirmation": "NONE",
            "entry_quality": "C",
            "reason": "No valid setup"

        }

        direction = signal.get("direction", "NONE")

        if trade.get("trade_status") != "READY":
            result["reason"] = "Trade Status = {}".format(
                trade.get("trade_status")
            )
            return result

        entry = trade.get("entry")

        if entry is None:
            result["reason"] = "Entry price unavailable"
            return result

        if direction == "BUY":

            result["entry_type"] = "PULLBACK BUY"

            result["entry_zone"] = (
                round(entry * 0.9995, 2),
                round(entry * 1.0005, 2)
            )

            result["confirmation"] = "Bullish Candle Close"

            result["entry_quality"] = "A"

            result["reason"] = (
                "Wait for retracement into entry zone."
            )

        elif direction == "SELL":

            result["entry_type"] = "PULLBACK SELL"

            result["entry_zone"] = (
                round(entry * 0.9995, 2),
                round(entry * 1.0005, 2)
            )

            result["confirmation"] = "Bearish Candle Close"

            result["entry_quality"] = "A"

            result["reason"] = (
                "Wait for pullback before selling."
            )

        return result