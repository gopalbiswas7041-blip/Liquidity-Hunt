class CHoCH:

    def __init__(self):
        print("CHoCH Engine Initialized")

    def find_swings(self, data):

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

        print("Checking CHoCH...")

        if data is None:
            return []

        swing_highs, swing_lows = self.find_swings(data)

        print(f"Swing Highs : {len(swing_highs)}")
        print(f"Swing Lows  : {len(swing_lows)}")

        closes = data["Close"].values

        choch_signals = []

        # Bullish CHoCH
        for swing in swing_highs:

            start = swing["index"] + 1

            for i in range(start, len(data)):

                if closes[i] > swing["price"]:

                    choch_signals.append({
                        "type": "Bullish CHoCH",
                        "price": float(swing["price"]),
                        "index": i,
                        "time": str(data.index[i]),
                        "high": float(data.iloc[i]["High"]),
                        "low": float(data.iloc[i]["Low"]),
                        "close": float(data.iloc[i]["Close"])
                    })

                    break

        # Bearish CHoCH
        for swing in swing_lows:

            start = swing["index"] + 1

            for i in range(start, len(data)):

                if closes[i] < swing["price"]:

                    choch_signals.append({
                        "type": "Bearish CHoCH",
                        "price": float(swing["price"]),
                        "index": i,
                        "time": str(data.index[i]),
                        "high": float(data.iloc[i]["High"]),
                        "low": float(data.iloc[i]["Low"]),
                        "close": float(data.iloc[i]["Close"])
                    })

                    break

        print(f"CHoCH Found : {len(choch_signals)}")

        return choch_signals