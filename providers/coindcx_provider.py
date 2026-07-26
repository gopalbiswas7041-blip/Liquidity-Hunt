import requests
import pandas as pd

from providers.base_provider import BaseProvider


class CoinDCXProvider(BaseProvider):

    BASE_URL = "https://public.coindcx.com"

    def __init__(self):
        self.connected = False

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

        df["Datetime"] = (
            pd.to_datetime(
                df["Datetime"],
                unit="ms",
                utc=True
            )
            .dt.tz_convert("Asia/Kolkata")
            .dt.tz_localize(None)
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

        # Datetime কে Index হিসেবে ব্যবহার করা হবে
        df.set_index(
            "Datetime",
            inplace=True
        )

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
                "15m"
            ],
            "max_candles": 500,
            "supports_websocket": False
        }