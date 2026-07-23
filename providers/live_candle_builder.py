from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class LiveCandleBuilder:

    def __init__(self, timeframe="1m"):

        self.timeframe = timeframe

        self.current_candle: Optional[Candle] = None

        self.last_closed_candle: Optional[Candle] = None

        print(f"Live Candle Builder Initialized ({timeframe})")

    def reset(self):

        self.current_candle = None
        self.last_closed_candle = None

    def get_current_candle(self):

        return self.current_candle

    def get_last_closed_candle(self):

        return self.last_closed_candle

    def _get_bucket_time(self, timestamp: datetime):

        if self.timeframe == "1m":
            return timestamp.replace(second=0, microsecond=0)

        elif self.timeframe == "5m":
            minute = (timestamp.minute // 5) * 5
            return timestamp.replace(
                minute=minute,
                second=0,
                microsecond=0
            )

        elif self.timeframe == "15m":
            minute = (timestamp.minute // 15) * 15
            return timestamp.replace(
                minute=minute,
                second=0,
                microsecond=0
            )

        return timestamp.replace(second=0, microsecond=0)

    def update_tick(
        self,
        price: float,
        volume: float,
        timestamp: datetime
    ):

        bucket = self._get_bucket_time(timestamp)

        if self.current_candle is None:

            self.current_candle = Candle(
                timestamp=bucket,
                open=price,
                high=price,
                low=price,
                close=price,
                volume=volume
            )

            return None

        if bucket == self.current_candle.timestamp:

            self.current_candle.high = max(
                self.current_candle.high,
                price
            )

            self.current_candle.low = min(
                self.current_candle.low,
                price
            )

            self.current_candle.close = price
            self.current_candle.volume += volume

            return None

        closed = self.current_candle

        self.last_closed_candle = closed

        self.current_candle = Candle(
            timestamp=bucket,
            open=price,
            high=price,
            low=price,
            close=price,
            volume=volume
        )

        return closed