import requests
import pandas as pd
import time

from providers.base_provider import BaseProvider


class CoinDCXProvider(BaseProvider):

    BASE_URL = "https://public.coindcx.com"

    TIMEFRAME_MAP = {
        "1m": "1m",
        "3m": "3m",
        "5m": "1m",
        "15m": "15m",
        "30m": "30m",
        "1H": "1h",
        "1h": "1h",
        "2H": "2h",
        "2h": "2h",
        "4H": "4h",
        "4h": "4h",
        "6H": "6h",
        "6h": "6h",
        "8H": "8h",
        "8h": "8h",
        "12H": "12h",
        "12h": "12h",
        "1D": "1d",
        "1d": "1d",
    }

    def __init__(self):
        self.connected = False
        self.websocket = None

    def normalize_timeframe(self, timeframe: str) -> str:
        """
        Normalize timeframe names before sending to CoinDCX.
        """

        tf = str(timeframe).strip()

        if tf not in self.TIMEFRAME_MAP:
            raise ValueError(f"Unsupported timeframe: {tf}")

        return self.TIMEFRAME_MAP[tf]

    def connect(self):
        self.connected = True
        print("CoinDCX Provider Connected")

    def disconnect(self):
        self.connected = False
        print("CoinDCX Provider Disconnected")

    def get_live_price(self, symbol):
        """
        Get latest market price from CoinDCX ticker API.
        """

        url = "https://api.coindcx.com/exchange/ticker"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        tickers = response.json()

        for ticker in tickers:
            if ticker.get("market") == symbol:
                return float(ticker["last_price"])

        raise ValueError(f"Market '{symbol}' not found.")

    def get_candles(self, symbol, timeframe, limit=500):
        """
        Download candle data from CoinDCX REST API.
        """

        # User যে timeframe চেয়েছে সেটা সংরক্ষণ
        original_timeframe = timeframe

        symbol = self.normalize_symbol(symbol)
        timeframe = self.normalize_timeframe(timeframe)

        url = f"{self.BASE_URL}/market_data/candles"

        params = {
            "pair": symbol,
            "interval": timeframe,
            "limit": limit
        }

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        print("URL :", response.url)
        print("Status Code :", response.status_code)
        print("Response :", response.text)

        response.raise_for_status()

        candles = response.json()

        df = pd.DataFrame(candles)

        if df.empty:
            return df

        df.rename(
            columns={
                "time": "Datetime",
                "open": "Open",
                "high": "High",
                "low": "Low",
                "close": "Close",
                "volume": "Volume"
            },
            inplace=True
        )

        df["Datetime"] = pd.to_datetime(
            df["Datetime"],
            unit="ms",
            utc=True
        )

        numeric_columns = [
            "Open",
            "High",
            "Low",
            "Close",
            "Volume"
        ]

        for column in numeric_columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        df.sort_values(
            "Datetime",
            inplace=True
        )

        df.set_index(
            "Datetime",
            inplace=True
        )

        # -------- Aggregate Timeframes --------

        if original_timeframe == "3m":

            df = df.resample("3min").agg({
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum",
            }).dropna()

        elif original_timeframe == "5m":

            df = df.resample("5min").agg({
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum",
            }).dropna()

        elif original_timeframe == "30m":

            df = df.resample("30min").agg({
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum",
            }).dropna()

        return df

    def get_capabilities(self):
        """
        Return CoinDCX provider capabilities.
        """

        return {
            "provider": "CoinDCX",
            "live": True,
            "historical": True,
            "supported_timeframes": [
                "1m",
                "3m",
                "5m",
                "15m",
                "30m",
                "1h",
                "2h",
                "4h",
                "6h",
                "8h",
                "12h",
                "1d",
            ],
            "max_candles": 500,
            "supports_websocket": True
        }

    def validate_timeframe(self, timeframe: str) -> bool:
        """
        Validate whether a timeframe is supported.
        """

        return timeframe in self.get_capabilities()["supported_timeframes"]

    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize trading pair symbol.
        """

        if not symbol:
            return "B-BTC_USDT"

        symbol = symbol.strip().upper()

        mapping = {
            "BTCUSDT": "B-BTC_USDT",
            "BTC/USDT": "B-BTC_USDT",
            "ETHUSDT": "B-ETH_USDT",
            "ETH/USDT": "B-ETH_USDT",
        }

        return mapping.get(symbol, symbol)

    def get_server_time(self):
        """
        Return current server timestamp.
        """

        return int(time.time() * 1000)

    def health_check(self):
        """
        Provider health status.
        """

        return {
            "provider": "CoinDCX",
            "status": "healthy",
            "websocket": self.websocket is not None,
            "historical": True,
            "live": True,
            "timestamp": self.get_server_time(),
        }

    def provider_info(self):
        """
        Return provider information.
        """

        return {
            "name": "CoinDCX Provider",
            "version": "V19.3",
            "exchange": "CoinDCX",
            "supports_live_data": True,
            "supports_historical_data": True,
            "supports_websocket": True,
            "max_candles": 500,
            "timeframes": self.get_capabilities()["supported_timeframes"],
        }