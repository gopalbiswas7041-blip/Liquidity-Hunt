"""
Liquidity Hunter AI
Live Candle Builder V20.9.3
Futures Live Synchronization Edition
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, Optional


@dataclass(slots=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class LiveCandleBuilder:

    _TIMEFRAME_ALIAS: Dict[str, str] = {
        "1m": "1m", "3m": "3m", "5m": "5m",
        "15m": "15m", "30m": "30m",
        "1h": "1h", "2h": "2h", "4h": "4h",
        "6h": "6h", "8h": "8h", "12h": "12h",
        "1d": "1d", "1w": "1w",
        "1M": "1m", "3M": "3m", "5M": "5m",
        "15M": "15m", "30M": "30m",
        "1H": "1h", "2H": "2h", "4H": "4h",
        "6H": "6h", "8H": "8h", "12H": "12h",
        "1D": "1d", "1W": "1w",
    }

    def __init__(self, timeframe: str = "1m"):
        self.timeframe = self._normalize_timeframe(timeframe)
        self.current_candle: Optional[Candle] = None
        self.last_closed_candle: Optional[Candle] = None
        self.live_update_callback: Optional[Callable[[Candle], None]] = None
        self.candle_close_callback: Optional[Callable[[Candle], None]] = None
        self._paused = False
        print(f"Live Candle Builder Initialized ({self.timeframe})")

    @classmethod
    def _normalize_timeframe(cls, timeframe: str) -> str:
        if timeframe is None:
            return "1m"
        return cls._TIMEFRAME_ALIAS.get(str(timeframe).strip(), str(timeframe).strip().lower())

    @staticmethod
    def _normalize_timestamp(timestamp: datetime) -> datetime:
        if timestamp is None:
            raise ValueError("Timestamp cannot be None")
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)
        return timestamp.astimezone(timezone.utc)

    @property
    def is_paused(self) -> bool:
        return self._paused

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False

    def reset(self):
        self.current_candle = None
        self.last_closed_candle = None

    def set_timeframe(self, timeframe: str):
        tf = self._normalize_timeframe(timeframe)
        if tf == self.timeframe:
            return
        print(f"Live Candle Timeframe Changed : {self.timeframe} -> {tf}")
        self.timeframe = tf
        self.reset()

    def set_live_update_callback(self, callback):
        self.live_update_callback = callback

    def set_candle_close_callback(self, callback):
        self.candle_close_callback = callback

    def get_current_candle(self):
        return self.current_candle

    def get_last_closed_candle(self):
        return self.last_closed_candle

    def seed_current_candle(self, candle: Candle) -> bool:
        if candle is None or self._paused:
            return False
        try:
            ts = self._normalize_timestamp(candle.timestamp)
            self.current_candle = Candle(
                timestamp=ts,
                open=float(candle.open),
                high=float(candle.high),
                low=float(candle.low),
                close=float(candle.close),
                volume=float(candle.volume),
            )
            self.last_closed_candle = None
            return True
        except Exception as exc:
            print("Failed to seed live candle:", exc)
            return False

    @staticmethod
    def _floor_minutes(timestamp: datetime, minutes: int):
        return timestamp.replace(
            minute=(timestamp.minute // minutes) * minutes,
            second=0, microsecond=0,
        )

    @staticmethod
    def _floor_hours(timestamp: datetime, hours: int):
        return timestamp.replace(
            hour=(timestamp.hour // hours) * hours,
            minute=0, second=0, microsecond=0,
        )

    def _get_bucket_time(self, timestamp: datetime):
        ts = self._normalize_timestamp(timestamp)
        tf = self.timeframe
        minute_map = {"1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30}
        hour_map = {"1h": 1, "2h": 2, "4h": 4, "6h": 6, "8h": 8, "12h": 12}
        if tf in minute_map:
            return self._floor_minutes(ts, minute_map[tf])
        if tf in hour_map:
            return self._floor_hours(ts, hour_map[tf])
        if tf == "1d":
            return ts.replace(hour=0, minute=0, second=0, microsecond=0)
        if tf == "1w":
            start = ts.replace(hour=0, minute=0, second=0, microsecond=0)
            return (start.replace(hour=0) - __import__("datetime").timedelta(days=start.weekday()))
        return ts.replace(second=0, microsecond=0)

    def update_tick(self, price: float, volume: float, timestamp: datetime):
        if self._paused:
            return None
        try:
            ts = self._normalize_timestamp(timestamp)
            price = float(price)
            volume = max(0.0, float(volume))
        except (TypeError, ValueError):
            return None
        if price <= 0:
            return None

        bucket = self._get_bucket_time(ts)

        if self.current_candle is None:
            self.current_candle = Candle(bucket, price, price, price, price, volume)
            if self.live_update_callback:
                self.live_update_callback(self.current_candle)
            return None

        if bucket == self.current_candle.timestamp:
            c = self.current_candle
            c.high = max(c.high, price)
            c.low = min(c.low, price)
            c.close = price
            c.volume += volume
            if self.live_update_callback:
                self.live_update_callback(c)
            return None

        if bucket < self.current_candle.timestamp:
            return None

        closed = self.current_candle
        self.last_closed_candle = closed
        if self.candle_close_callback:
            self.candle_close_callback(closed)

        self.current_candle = Candle(bucket, price, price, price, price, volume)
        if self.live_update_callback:
            self.live_update_callback(self.current_candle)
        return closed

    def has_active_candle(self) -> bool:
        return self.current_candle is not None

    def clear_current_candle(self):
        self.current_candle = None

    def clear_last_closed_candle(self):
        self.last_closed_candle = None

    def snapshot(self):
        return {
            "timeframe": self.timeframe,
            "paused": self._paused,
            "has_current_candle": self.current_candle is not None,
            "has_last_closed_candle": self.last_closed_candle is not None,
        }

    def get_status(self):
        return {
            "timeframe": self.timeframe,
            "paused": self._paused,
            "current_candle": self.current_candle,
            "last_closed_candle": self.last_closed_candle,
        }

    def remove_live_update_callback(self):
        self.live_update_callback = None

    def remove_candle_close_callback(self):
        self.candle_close_callback = None

    def __repr__(self):
        return (
            f"LiveCandleBuilder(timeframe='{self.timeframe}', "
            f"paused={self._paused}, current={self.current_candle is not None})"
        )
