class OrderBlock:

    def __init__(self):
        print("Order Block Engine Initialized")

    def find_order_blocks(self, data):

        if data is None or len(data) < 5:
            return []

        opens = data["Open"].values
        highs = data["High"].values
        lows = data["Low"].values
        closes = data["Close"].values

        order_blocks = []

        for i in range(1, len(data)):

            # Bullish Order Block
            if closes[i] > opens[i] and closes[i - 1] < opens[i - 1]:

                order_blocks.append({
                    "type": "Bullish Order Block",
                    "index": i - 1,
                    "time": str(data.index[i - 1]),
                    "high": float(highs[i - 1]),
                    "low": float(lows[i - 1]),
                    "open": float(opens[i - 1]),
                    "close": float(closes[i - 1])
                })

            # Bearish Order Block
            elif closes[i] < opens[i] and closes[i - 1] > opens[i - 1]:

                order_blocks.append({
                    "type": "Bearish Order Block",
                    "index": i - 1,
                    "time": str(data.index[i - 1]),
                    "high": float(highs[i - 1]),
                    "low": float(lows[i - 1]),
                    "open": float(opens[i - 1]),
                    "close": float(closes[i - 1])
                })

        return order_blocks

    def detect(self, data):

        print("Checking Order Blocks...")

        if data is None:
            return []

        order_blocks = self.find_order_blocks(data)

        print(f"Order Blocks Found : {len(order_blocks)}")

        return order_blocks