from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """
    Base interface for all market data providers.
    Every provider (Yahoo, CoinDCX, Angel One, Binance, etc.)
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

    @abstractmethod
    def get_capabilities(self):
        """
        Return provider capabilities.

        Example:
        {
            "provider": "CoinDCX",
            "live": True,
            "historical": True,
            "supported_timeframes": [
                "1m",
                "5m",
                "15m",
                "1h"
            ],
            "max_candles": 1000,
            "supports_websocket": False
        }
        """
        pass