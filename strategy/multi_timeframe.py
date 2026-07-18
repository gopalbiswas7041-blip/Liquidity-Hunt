class MultiTimeframe:

    def __init__(self):
        print("Multi-Timeframe Engine Initialized")

    def analyze(self, htf_signal, ltf_signal):

        result = {
            "valid": False,
            "status": "WAIT",
            "direction": "NONE",
            "reason": ""
        }

        # -----------------------------
        # BUY Confirmation
        # -----------------------------
        if htf_signal == "BUY" and ltf_signal == "BUY":

            result["valid"] = True
            result["status"] = "READY"
            result["direction"] = "BUY"
            result["reason"] = "15m and 5m Bullish"

        # -----------------------------
        # SELL Confirmation
        # -----------------------------
        elif htf_signal == "SELL" and ltf_signal == "SELL":

            result["valid"] = True
            result["status"] = "READY"
            result["direction"] = "SELL"
            result["reason"] = "15m and 5m Bearish"

        # -----------------------------
        # Trend Conflict
        # -----------------------------
        else:

            result["valid"] = False
            result["status"] = "WAIT"
            result["direction"] = "NONE"
            result["reason"] = "Timeframe Conflict"

        return result