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

        status = trade.get("trade_status", "WAIT")

        if status == "AVOID":

            result["entry_type"] = "NO ENTRY"
            result["confirmation"] = "Timeframe Conflict"
            result["entry_quality"] = "D"
            result["reason"] = (
            "Higher timeframe trend conflicts with the lower timeframe signal. "
            "Wait until both timeframes align before entering."
        )
            return result

        elif status == "WAIT":

            result["entry_type"] = "WAIT"
            result["confirmation"] = "Better confirmation required"
            result["entry_quality"] = "B"
            result["reason"] = "Wait for stronger confirmation before entering."
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