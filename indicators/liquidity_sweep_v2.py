class LiquiditySweepV2:

    def __init__(self):
        print("Liquidity Sweep V2 Engine Initialized")

    def find_swings(self, data):
        """
        Detect Swing Highs and Swing Lows
        """

        if data is None or len(data) < 5:
            return [], []

        highs = data["High"].values
        lows = data["Low"].values

        swing_highs = []
        swing_lows = []

        for i in range(2, len(data) - 2):

            # Swing High
            if (
                highs[i] > highs[i - 1]
                and highs[i] > highs[i - 2]
                and highs[i] > highs[i + 1]
                and highs[i] > highs[i + 2]
            ):
                swing_highs.append({
                    "index": i,
                    "price": float(highs[i])
                })

            # Swing Low
            if (
                lows[i] < lows[i - 1]
                and lows[i] < lows[i - 2]
                and lows[i] < lows[i + 1]
                and lows[i] < lows[i + 2]
            ):
                swing_lows.append({
                    "index": i,
                    "price": float(lows[i])
                })

        return swing_highs, swing_lows

    def detect(self, data):

        print("Checking Liquidity Sweep V2...")

        if data is None:
            print("No Market Data")
            return []

        swing_highs, swing_lows = self.find_swings(data)

        print(f"Swing Highs : {len(swing_highs)}")
        print(f"Swing Lows  : {len(swing_lows)}")

        highs = data["High"].values
        lows = data["Low"].values
        closes = data["Close"].values

        signals = []

        # Bearish Sweep
        for swing in swing_highs:

            start = swing["index"] + 1
            end = min(start + 20, len(data))

            for i in range(start, end):

                if highs[i] > swing["price"] and closes[i] < swing["price"]:

                    signals.append({
                        "type": "Bearish Sweep",
                        "price": float(swing["price"]),
                        "index": i,
                        "time": str(data.index[i]),
                        "high": float(data.iloc[i]["High"]),
                        "low": float(data.iloc[i]["Low"]),
                        "close": float(data.iloc[i]["Close"])
                    })

                    break

        # Bullish Sweep
        for swing in swing_lows:

            start = swing["index"] + 1
            end = min(start + 20, len(data))

            for i in range(start, end):

                if lows[i] < swing["price"] and closes[i] > swing["price"]:

                    signals.append({
                        "type": "Bullish Sweep",
                        "price": float(swing["price"]),
                        "index": i,
                        "time": str(data.index[i]),
                        "high": float(data.iloc[i]["High"]),
                        "low": float(data.iloc[i]["Low"]),
                        "close": float(data.iloc[i]["Close"])
                    })

                    break

        print(f"Liquidity Sweeps Found : {len(signals)}")

        return signals