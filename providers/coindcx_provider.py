import requests
import pandas as pd

from providers.base_provider import BaseProvider


class CoinDCXProvider(BaseProvider):

    BASE_URL = "https://public.coindcx.com"

    def _init_(self):
        self.connected = False

    def connect(self):
        self.connected = True
        print("CoinDCX Provider Connected")

    def disconnect(self):
        self.connected = False
        print("CoinDCX Provider Disconnected")

    def build_candle_url(self, symbol, timeframe, limit=500):
        """
        Build CoinDCX Candle API URL.
        """
        return (
            f"{self.BASE_URL}/market_data/candles"
            f"?pair={symbol}"
            f"&interval={timeframe}"
            f"&limit={limit}"
        )

    def get_live_price(self, symbol):
        """
        Get latest market price from CoinDCX ticker API.
        """

        url = "https://api.coindcx.com/exchange/ticker"

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        tickers = response.json()

        for ticker in tickers:
            market = ticker.get("market", "")

            if market == symbol:
                return float(ticker["last_price"])

        raise ValueError(f"Market '{symbol}' not found.")

    def get_candles(self, symbol, timeframe, limit=500):
        """
        Download candle data from CoinDCX REST API.
        """

        url = self.build_candle_url(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit
        )

        response = requests.get(url, timeout=10)
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
            unit="ms"
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

        df.reset_index(
            drop=True,
            inplace=True
        )

        return df