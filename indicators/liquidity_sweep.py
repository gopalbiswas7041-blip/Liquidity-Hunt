class LiquiditySweep:

    def _init_(self):
        print("Liquidity Sweep Engine Initialized")

    def detect(self, data):

        print("Checking Liquidity Sweep...")

        if data is None:
            print("No market data found.")
            return []

        if len(data) < 5:
            print("Not enough candles.")
            return []

        print(f"Total Candles: {len(data)}")

        swing_highs = []
        swing_lows = []
        signals = []

        highs = data["High"].values
        lows = data["Low"].values
        closes = data["Close"].values

        # -----------------------------
        # Swing High / Swing Low Detection
        # -----------------------------
        for i in range(2, len(data) - 2):

            # Swing High
            if (
                highs[i] > highs[i - 1]
                and highs[i] > highs[i - 2]
                and highs[i] > highs[i + 1]
                and highs[i] > highs[i + 2]
            ):
                swing_highs.append((i, highs[i]))

            # Swing Low
            if (
                lows[i] < lows[i - 1]
                and lows[i] < lows[i - 2]
                and lows[i] < lows[i + 1]
                and lows[i] < lows[i + 2]
            ):
                swing_lows.append((i, lows[i]))

        print(f"Swing Highs Found : {len(swing_highs)}")
        print(f"Swing Lows Found  : {len(swing_lows)}")

        # -----------------------------
        # Bearish Liquidity Sweep
        # -----------------------------
        for swing_index, swing_price in swing_highs:

            for j in range(swing_index + 1, min(swing_index + 21, len(data))):

                if highs[j] > swing_price and closes[j] < swing_price:

                    signals.append({
                        "type": "Bearish Sweep",
                        "price": float(swing_price),
                        "candle": int(j)
                    })

                    break

        # -----------------------------
        # Bullish Liquidity Sweep
        # -----------------------------
        for swing_index, swing_price in swing_lows:

            for j in range(swing_index + 1, min(swing_index + 21, len(data))):

                if lows[j] < swing_price and closes[j] > swing_price:

                    signals.append({
                        "type": "Bullish Sweep",
                        "price": float(swing_price),
                        "candle": int(j)
                    })

                    break

        print(f"Liquidity Sweeps Found : {len(signals)}")

        return signals