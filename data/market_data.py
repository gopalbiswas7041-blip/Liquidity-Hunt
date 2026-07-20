from providers.yahoo_provider import YahooProvider


class MarketData:

    def __init__(self, symbol, provider=None):

        self.symbol = symbol

        if provider is None:
            provider = YahooProvider()

        self.provider = provider
        self.provider.connect()

        # Smart Cache
        self.cache = {}

        print("Market Data Engine Initialized")

    def _get_api_timeframe(self, timeframe):

        capabilities = self.provider.get_capabilities()

        supported = capabilities.get(
            "supported_timeframes",
            []
        )

        if timeframe in supported:
            return timeframe

        timeframe_map = {
            "5m": "1m"
        }

        return timeframe_map.get(
            timeframe,
            timeframe
        )

    def load_data(self, timeframe="5m", force_refresh=False):

        print(f"Symbol: {self.symbol}")
        print(f"Timeframe: {timeframe}")

        if not force_refresh and timeframe in self.cache:

            print("Using Cached Data")

            return self.cache[timeframe]

        api_timeframe = self._get_api_timeframe(
            timeframe
        )

        data = self.provider.get_candles(
            self.symbol,
            api_timeframe
        )

        self.cache[timeframe] = data

        print(data.tail())

        return data

    def refresh_cache(self, timeframe):

        return self.load_data(
            timeframe,
            force_refresh=True
        )

    def clear_cache(self):

        self.cache.clear()

    def get_live_price(self):

        return self.provider.get_live_price(
            self.symbol
        )

    def disconnect(self):

        self.provider.disconnect()