import yfinance as yf

from providers.base_provider import BaseProvider


class YahooProvider(BaseProvider):

    def __init__(self):
        self.connected = False

    def connect(self):
        self.connected = True
        print("Yahoo Provider Connected")

    def disconnect(self):
        self.connected = False
        print("Yahoo Provider Disconnected")

    def get_live_price(self, symbol):
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m")

        if data.empty:
            return None

        return float(data["Close"].iloc[-1])

    def get_candles(self, symbol, timeframe):
        ticker = yf.Ticker(symbol)

        data = ticker.history(
            period="5d",
            interval=timeframe
        )

        return data