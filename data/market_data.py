import yfinance as yf

class MarketData:
    def __init__(self, symbol, timeframe):
        self.symbol = symbol
        self.timeframe = timeframe
        print("Market Data Engine Initialized")

    def load_data(self):
        print(f"Symbol: {self.symbol}")
        print(f"Timeframe: {self.timeframe}")

        ticker = yf.Ticker(self.symbol)
        data = ticker.history(period="5d", interval=self.timeframe)

        print(data.tail())

        return data