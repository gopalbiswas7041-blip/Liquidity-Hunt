"""
Liquidity Hunter AI
Version : V20.5 Live Candle Sync
File    : providers/live_candle_builder.py

Production Features
-------------------
- Full timeframe normalization
- Extended timeframe support
- Stable bucket engine
- Live update callback
- Candle close callback
- Safe state management
- Historical current-candle seeding
- Historical + live candle merge support
- UTC timestamp normalization
- Same-candle OHLC continuation
- Future-ready architecture
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, Optional


# ==========================================================
# Candle Model
# ==========================================================

@dataclass(slots=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


# ==========================================================
# Live Candle Builder
# ==========================================================

class LiveCandleBuilder:

    # ======================================================
    # Canonical Timeframe Names
    # ======================================================

    _TIMEFRAME_ALIAS: Dict[str, str] = {

        "1m": "1m",
        "3m": "3m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",

        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "6h": "6h",
        "8h": "8h",
        "12h": "12h",

        "1d": "1d",
        "1w": "1w",

        # Legacy compatibility
        "1H": "1h",
        "2H": "2h",
        "4H": "4h",
        "6H": "6h",
        "8H": "8h",
        "12H": "12h",
        "1D": "1d",
        "1W": "1w",
    }

    # ======================================================
    # Initialization
    # ======================================================

    def __init__(
        self,
        timeframe: str = "1m",
    ):

        self.timeframe = (
            self._normalize_timeframe(
                timeframe
            )
        )

        # ----------------------------------------------
        # Active Candle
        # ----------------------------------------------

        self.current_candle: Optional[Candle] = None

        # ----------------------------------------------
        # Last Closed Candle
        # ----------------------------------------------

        self.last_closed_candle: Optional[Candle] = None

        # ----------------------------------------------
        # Callbacks
        # ----------------------------------------------

        self.live_update_callback: Optional[
            Callable[[Candle], None]
        ] = None

        self.candle_close_callback: Optional[
            Callable[[Candle], None]
        ] = None

        # ----------------------------------------------
        # Runtime State
        # ----------------------------------------------

        self._paused = False

        print(
            f"Live Candle Builder Initialized "
            f"({self.timeframe})"
        )

    # ======================================================
    # Timeframe Normalization
    # ======================================================

    @classmethod
    def _normalize_timeframe(
        cls,
        timeframe: str,
    ) -> str:

        if timeframe is None:
            return "1m"

        return cls._TIMEFRAME_ALIAS.get(
            timeframe,
            timeframe.lower(),
        )

    # ======================================================
    # Timestamp Normalization
    # ======================================================

    @staticmethod
    def _normalize_timestamp(
        timestamp: datetime,
    ) -> datetime:

        if timestamp is None:
            raise ValueError(
                "Timestamp cannot be None"
            )

        # ----------------------------------------------
        # Naive timestamp
        # ----------------------------------------------

        if timestamp.tzinfo is None:

            return timestamp.replace(
                tzinfo=timezone.utc
            )

        # ----------------------------------------------
        # Aware timestamp
        # ----------------------------------------------

        return timestamp.astimezone(
            timezone.utc
        )

    # ======================================================
    # Properties
    # ======================================================

    @property
    def is_paused(self) -> bool:

        return self._paused

    # ======================================================

    def pause(self):

        self._paused = True

    # ======================================================

    def resume(self):

        self._paused = False

    # ======================================================

    def reset(self):

        self.current_candle = None
        self.last_closed_candle = None

    # ======================================================
    # Public API
    # ======================================================

    def set_timeframe(
        self,
        timeframe: str,
    ):

        timeframe = (
            self._normalize_timeframe(
                timeframe
            )
        )

        if timeframe == self.timeframe:
            return

        print(
            f"Live Candle Timeframe Changed : "
            f"{self.timeframe} -> {timeframe}"
        )

        self.timeframe = timeframe

        self.reset()

    # ======================================================

    def set_live_update_callback(
        self,
        callback,
    ):

        self.live_update_callback = callback

    # ======================================================

    def set_candle_close_callback(
        self,
        callback,
    ):

        self.candle_close_callback = callback

    # ======================================================

    def get_current_candle(
        self,
    ):

        return self.current_candle

    # ======================================================

    def get_last_closed_candle(
        self,
    ):

        return self.last_closed_candle

    # ======================================================
    # Historical Candle Seed
    # ======================================================

    def seed_current_candle(
        self,
        candle: Candle,
    ) -> bool:

        """
        Continue an existing historical candle with live ticks.

        The historical candle OHLC is preserved.

        Future live ticks will modify:

            high
            low
            close
            volume

        The original open remains unchanged.
        """

        if candle is None:

            print(
                "Cannot seed current candle: "
                "candle is None"
            )

            return False

        if self._paused:

            print(
                "Cannot seed current candle: "
                "builder is paused"
            )

            return False

        try:

            timestamp = (
                self._normalize_timestamp(
                    candle.timestamp
                )
            )

            self.current_candle = Candle(

                timestamp=timestamp,

                open=float(
                    candle.open
                ),

                high=float(
                    candle.high
                ),

                low=float(
                    candle.low
                ),

                close=float(
                    candle.close
                ),

                volume=float(
                    candle.volume
                ),
            )

            self.last_closed_candle = None

            print(
                "\n========== LIVE CANDLE SEEDED =========="
            )

            print(
                "Timestamp :",
                self.current_candle.timestamp,
            )

            print(
                "Open      :",
                self.current_candle.open,
            )

            print(
                "High      :",
                self.current_candle.high,
            )

            print(
                "Low       :",
                self.current_candle.low,
            )

            print(
                "Close     :",
                self.current_candle.close,
            )

            print(
                "Volume    :",
                self.current_candle.volume,
            )

            print(
                "========================================\n"
            )

            return True

        except Exception as exc:

            print(
                "Failed to seed live candle:",
                exc,
            )

            return False

    # ======================================================
    # Bucket Helpers
    # ======================================================

    @staticmethod
    def _floor_minutes(
        timestamp: datetime,
        minutes: int,
    ):

        minute = (
            timestamp.minute // minutes
        ) * minutes

        return timestamp.replace(

            minute=minute,

            second=0,

            microsecond=0,
        )

    # ======================================================

    @staticmethod
    def _floor_hours(
        timestamp: datetime,
        hours: int,
    ):

        hour = (
            timestamp.hour // hours
        ) * hours

        return timestamp.replace(

            hour=hour,

            minute=0,

            second=0,

            microsecond=0,
        )

    # ======================================================

    def _get_bucket_time(
        self,
        timestamp: datetime,
    ):

        timestamp = (
            self._normalize_timestamp(
                timestamp
            )
        )

        tf = self.timeframe

        # ----------------------------------------------
        # Minute Timeframes
        # ----------------------------------------------

        if tf == "1m":

            return self._floor_minutes(
                timestamp,
                1,
            )

        if tf == "3m":

            return self._floor_minutes(
                timestamp,
                3,
            )

        if tf == "5m":

            return self._floor_minutes(
                timestamp,
                5,
            )

        if tf == "15m":

            return self._floor_minutes(
                timestamp,
                15,
            )

        if tf == "30m":

            return self._floor_minutes(
                timestamp,
                30,
            )

        # ----------------------------------------------
        # Hour Timeframes
        # ----------------------------------------------

        if tf == "1h":

            return self._floor_hours(
                timestamp,
                1,
            )

        if tf == "2h":

            return self._floor_hours(
                timestamp,
                2,
            )

        if tf == "4h":

            return self._floor_hours(
                timestamp,
                4,
            )

        if tf == "6h":

            return self._floor_hours(
                timestamp,
                6,
            )

        if tf == "8h":

            return self._floor_hours(
                timestamp,
                8,
            )

        if tf == "12h":

            return self._floor_hours(
                timestamp,
                12,
            )

        # ----------------------------------------------
        # Daily
        # ----------------------------------------------

        if tf == "1d":

            return timestamp.replace(

                hour=0,

                minute=0,

                second=0,

                microsecond=0,
            )

        # ----------------------------------------------
        # Weekly
        # ----------------------------------------------

        if tf == "1w":

            start = timestamp.replace(

                hour=0,

                minute=0,

                second=0,

                microsecond=0,
            )

            return start.replace(
                day=start.day - start.weekday()
            )

        # ----------------------------------------------
        # Fallback
        # ----------------------------------------------

        return timestamp.replace(

            second=0,

            microsecond=0,
        )

    # ======================================================
    # Live Tick Processing
    # ======================================================

    def update_tick(
        self,
        price: float,
        volume: float,
        timestamp: datetime,
    ):

        """
        Process one live market tick.

        Behaviour
        ---------

        1. No current candle:
           Create a new candle.

        2. Same bucket:
           Update current candle.

        3. New bucket:
           Close old candle and create new candle.
        """

        if self._paused:
            return None

        # ----------------------------------------------
        # Normalize timestamp
        # ----------------------------------------------

        try:

            timestamp = (
                self._normalize_timestamp(
                    timestamp
                )
            )

            price = float(price)

            volume = float(volume)

        except (
            TypeError,
            ValueError,
        ):

            return None

        # ----------------------------------------------
        # Determine bucket
        # ----------------------------------------------

        bucket = self._get_bucket_time(
            timestamp
        )

        # ==================================================
        # First Candle
        # ==================================================

        if self.current_candle is None:

            self.current_candle = Candle(

                timestamp=bucket,

                open=price,

                high=price,

                low=price,

                close=price,

                volume=volume,
            )

            if self.live_update_callback is not None:

                self.live_update_callback(
                    self.current_candle
                )

            return None

        # ==================================================
        # Same Candle
        # ==================================================

        if (
            bucket
            == self.current_candle.timestamp
        ):

            candle = self.current_candle

            candle.high = max(
                candle.high,
                price,
            )

            candle.low = min(
                candle.low,
                price,
            )

            candle.close = price

            candle.volume += volume

            if self.live_update_callback is not None:

                self.live_update_callback(
                    candle
                )

            return None

        # ==================================================
        # Older Tick Protection
        # ==================================================

        if bucket < self.current_candle.timestamp:

            print(
                "⚠️ LIVE TICK IGNORED"
            )

            print(
                "Incoming Bucket :",
                bucket,
            )

            print(
                "Current Bucket  :",
                self.current_candle.timestamp,
            )

            print(
                "Reason : Older than active candle"
            )

            return None

        # ==================================================
        # Candle Closed
        # ==================================================

        closed_candle = (
            self.current_candle
        )

        self.last_closed_candle = (
            closed_candle
        )

        # ----------------------------------------------
        # Closed Candle Callback
        # ----------------------------------------------

        if self.candle_close_callback is not None:

            self.candle_close_callback(
                closed_candle
            )

        # ==================================================
        # Create Next Candle
        # ==================================================

        self.current_candle = Candle(

            timestamp=bucket,

            open=price,

            high=price,

            low=price,

            close=price,

            volume=volume,
        )

        # ----------------------------------------------
        # Live Callback
        # ----------------------------------------------

        if self.live_update_callback is not None:

            self.live_update_callback(
                self.current_candle
            )

        return closed_candle

    # ======================================================
    # State Helpers
    # ======================================================

    def has_active_candle(
        self,
    ) -> bool:

        return (
            self.current_candle
            is not None
        )

    # ======================================================

    def clear_current_candle(
        self,
    ):

        self.current_candle = None

    # ======================================================

    def clear_last_closed_candle(
        self,
    ):

        self.last_closed_candle = None

    # ======================================================
    # Snapshot
    # ======================================================

    def snapshot(
        self,
    ):

        return {

            "timeframe":
                self.timeframe,

            "paused":
                self._paused,

            "has_current_candle":
                self.current_candle is not None,

            "has_last_closed_candle":
                self.last_closed_candle is not None,
        }

    # ======================================================
    # Callback Management
    # ======================================================

    def remove_live_update_callback(
        self,
    ):

        self.live_update_callback = None

    # ======================================================

    def remove_candle_close_callback(
        self,
    ):

        self.candle_close_callback = None

    # ======================================================
    # Public Status
    # ======================================================

    def get_status(
        self,
    ):

        return {

            "timeframe":
                self.timeframe,

            "paused":
                self._paused,

            "current_candle":
                self.current_candle,

            "last_closed_candle":
                self.last_closed_candle,
        }

    # ======================================================
    # String Representation
    # ======================================================

    def __repr__(
        self,
    ):

        return (

            "LiveCandleBuilder("

            f"timeframe='{self.timeframe}', "

            f"paused={self._paused}, "

            f"current="
            f"{self.current_candle is not None}"

            ")"
        )