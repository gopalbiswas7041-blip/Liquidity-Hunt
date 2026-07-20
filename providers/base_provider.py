from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """
    Base interface for all market data providers.
    Every provider (Yahoo, CoinDCX, Angel One, etc.)
    must implement these methods.
    """

    @abstractmethod
    def connect(self):
        """Connect to the data source."""
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the data source."""
        pass

    @abstractmethod
    def get_live_price(self, symbol):
        """Return the latest live price."""
        pass

    @abstractmethod
    def get_candles(self, symbol, timeframe):
        """Return OHLC candle data."""
        pass