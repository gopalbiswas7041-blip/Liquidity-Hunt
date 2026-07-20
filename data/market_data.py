from providers.yahoo_provider import YahooProvider
from providers.coindcx_provider import CoinDCXProvider


class MarketData:

    def __init__(self, symbol, provider=None):

        self.symbol = symbol

        if provider is None:
            provider = YahooProvider()

        self.provider = provider

        self.provider.connect()

        print("Market Data Engine Initialized")

    def load_data(self, timeframe="5m", period="5d"):

        print(f"Symbol: {self.symbol}")
        print(f"Timeframe: {timeframe}")

        api_timeframe = timeframe

        # CoinDCX workaround
        if isinstance(self.provider, CoinDCXProvider):

            if timeframe == "5m":
                api_timeframe = "1m"

            elif timeframe == "15m":
                api_timeframe = "15m"

        data = self.provider.get_candles(
            self.symbol,
            api_timeframe
        )

        print(data.tail())

        return data

    def get_live_price(self):

        return self.provider.get_live_price(self.symbol)

    def disconnect(self):

        self.provider.disconnect()