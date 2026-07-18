import yfinance as yf


class MarketData:

    def __init__(self, symbol, timeframe="5m"):

        self.symbol = symbol
        self.timeframe = timeframe

        print("Market Data Engine Initialized")

    def load_data(self, timeframe=None, period="5d"):

        if timeframe is None:
            timeframe = self.timeframe

        print(f"Symbol: {self.symbol}")
        print(f"Timeframe: {timeframe}")

        ticker = yf.Ticker(self.symbol)

        data = ticker.history(
            period=period,
            interval=timeframe
        )

        print(data.tail())

        return data