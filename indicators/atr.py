import pandas as pd


class ATR:
    def __init__(self, period=14):
        self.period = period
        print("ATR Engine Initialized")

    def calculate(self, data):
        """
        Calculate Average True Range (ATR)
        """

        df = data.copy()

        # Previous Close
        df["prev_close"] = df["Close"].shift(1)

        # True Range Components
        df["high_low"] = df["High"] - df["Low"]
        df["high_close"] = (df["High"] - df["prev_close"]).abs()
        df["low_close"] = (df["Low"] - df["prev_close"]).abs()

        # True Range
        df["TR"] = df[
            ["high_low", "high_close", "low_close"]
        ].max(axis=1)

        # ATR
        df["ATR"] = df["TR"].rolling(self.period).mean()

        return df

    def get_volatility(self, data):
        """
        Detect Market Volatility
        """

        df = self.calculate(data)

        current_atr = df["ATR"].iloc[-1]
        average_atr = df["ATR"].tail(20).mean()

        if current_atr > average_atr * 1.20:
            return "HIGH"

        elif current_atr < average_atr * 0.80:
            return "LOW"

        return "NORMAL"