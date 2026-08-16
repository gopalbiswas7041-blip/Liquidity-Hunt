"""
Liquidity Hunter AI
Live Candle Builder V20.9.5
Futures Live Synchronization Edition

Responsibilities
----------------
- Build live OHLC candles from Futures ticks
- Correct UTC bucket handling
- Seed historical active candle
- Emit live candle updates
- Detect candle close exactly once
- Provide last closed candle safely
- Protect against duplicate/out-of-order ticks
- No GUI dependency

Architecture
------------
Futures WebSocket Tick
        |
        v
LiveCandleBuilder.update_tick()
        |
        +--> Current Live Candle
        |
        +--> Closed Candle
                 |
                 v
          Futures WebSocket
                 |
                 v
             Controller

Important
---------
The builder itself does NOT know about Controller,
Dashboard, ChartWidget, Qt or GUI objects.

The builder only manages candle state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Callable, Dict, Optional


# ============================================================
# CANDLE MODEL
# ============================================================

@dataclass(slots=True)
class Candle:

    timestamp: datetime

    open: float
    high: float
    low: float
    close: float

    volume: float = 0.0


# ============================================================
# LIVE CANDLE BUILDER
# ============================================================

class LiveCandleBuilder:

    """
    Builds OHLC candles from live Futures ticks.

    Design goals
    ------------
    1. UTC is the internal time standard.
    2. Each tick belongs to exactly one candle bucket.
    3. A candle can only move forward in time.
    4. A closed candle is emitted exactly once.
    5. Historical active candle can be seeded.
    6. No GUI dependency.
    """

    # ========================================================
    # TIMEFRAME ALIASES
    # ========================================================

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

        # ----------------------------------------------------
        # Upper-case compatibility
        # ----------------------------------------------------

        "1M": "1m",
        "3M": "3m",
        "5M": "5m",
        "15M": "15m",
        "30M": "30m",

        "1H": "1h",
        "2H": "2h",
        "4H": "4h",
        "6H": "6h",
        "8H": "8h",
        "12H": "12h",

        "1D": "1d",
        "1W": "1w",
    }

    # ========================================================
    # TIMEFRAME MAPS
    # ========================================================

    MINUTE_MAP = {

        "1m": 1,
        "3m": 3,
        "5m": 5,
        "15m": 15,
        "30m": 30,
    }

    HOUR_MAP = {

        "1h": 1,
        "2h": 2,
        "4h": 4,
        "6h": 6,
        "8h": 8,
        "12h": 12,
    }

    # ========================================================
    # INIT
    # ========================================================

    def __init__(
        self,
        timeframe: str = "1m",
    ):

        self.timeframe = (
            self._normalize_timeframe(
                timeframe
            )
        )

        # ----------------------------------------------------
        # Current forming candle
        # ----------------------------------------------------

        self.current_candle: Optional[Candle] = None

        # ----------------------------------------------------
        # Most recently closed candle
        # ----------------------------------------------------

        self.last_closed_candle: Optional[Candle] = None

        # ----------------------------------------------------
        # Closed candle delivery protection
        #
        # Timestamp of the last candle that was emitted
        # as closed through update_tick().
        # ----------------------------------------------------

        self._last_emitted_closed_timestamp: Optional[
            datetime
        ] = None

        # ----------------------------------------------------
        # Tick ordering protection
        # ----------------------------------------------------

        self._last_tick_timestamp: Optional[
            datetime
        ] = None

        # ----------------------------------------------------
        # State
        # ----------------------------------------------------

        self._paused = False

        # ====================================================
        # CALLBACKS
        # ====================================================

        self.live_update_callback: Optional[
            Callable[[Candle], None]
        ] = None

        self.candle_close_callback: Optional[
            Callable[[Candle], None]
        ] = None

        print(
            "Live Candle Builder Initialized "
            f"({self.timeframe})"
        )

    # ========================================================
    # TIMEFRAME NORMALIZATION
    # ========================================================

    @classmethod
    def _normalize_timeframe(
        cls,
        timeframe: str,
    ) -> str:

        if timeframe is None:
            return "1m"

        value = str(
            timeframe
        ).strip()

        normalized = cls._TIMEFRAME_ALIAS.get(
            value
        )

        if normalized is not None:
            return normalized

        normalized = value.lower()

        return normalized

    # ========================================================
    # PAUSE STATE
    # ========================================================

    @property
    def is_paused(self) -> bool:

        return self._paused

    # ========================================================
    # PAUSE
    # ========================================================

    def pause(self):

        self._paused = True

    # ========================================================
    # RESUME
    # ========================================================

    def resume(self):

        self._paused = False

    # ========================================================
    # RESET
    # ========================================================

    def reset(self):

        """
        Completely reset live candle state.

        Used when:
        - Symbol changes
        - Timeframe changes
        - WebSocket state is intentionally rebuilt
        """

        self.current_candle = None

        self.last_closed_candle = None

        self._last_emitted_closed_timestamp = None

        self._last_tick_timestamp = None

    # ========================================================
    # TIMEFRAME CHANGE
    # ========================================================

    def set_timeframe(
        self,
        timeframe: str,
    ):

        new_timeframe = (
            self._normalize_timeframe(
                timeframe
            )
        )

        if new_timeframe == self.timeframe:
            return

        print(
            "Live Candle Timeframe Changed : "
            f"{self.timeframe} -> "
            f"{new_timeframe}"
        )

        self.timeframe = new_timeframe

        self.reset()

    # ========================================================
    # CALLBACK REGISTRATION
    # ========================================================

    def set_live_update_callback(
        self,
        callback: Optional[
            Callable[[Candle], None]
        ],
    ):

        self.live_update_callback = callback

    # ========================================================

    def set_candle_close_callback(
        self,
        callback: Optional[
            Callable[[Candle], None]
        ],
    ):

        self.candle_close_callback = callback

    # ========================================================
    # CALLBACK REMOVAL
    # ========================================================

    def remove_live_update_callback(self):

        self.live_update_callback = None

    # ========================================================

    def remove_candle_close_callback(self):

        self.candle_close_callback = None

    # ========================================================
    # GET CURRENT CANDLE
    # ========================================================

    def get_current_candle(self) -> Optional[Candle]:

        return self.current_candle

    # ========================================================
    # GET LAST CLOSED CANDLE
    # ========================================================

    def get_last_closed_candle(
        self,
    ) -> Optional[Candle]:

        return self.last_closed_candle

    # ========================================================
    # ACTIVE CANDLE CHECK
    # ========================================================

    def has_active_candle(self) -> bool:

        return (
            self.current_candle
            is not None
        )

    # ========================================================
    # CLOSED CANDLE CHECK
    # ========================================================

    def has_closed_candle(self) -> bool:

        return (
            self.last_closed_candle
            is not None
        )

    # ========================================================
    # TIMESTAMP NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_timestamp(
        timestamp: datetime,
    ) -> datetime:

        """
        Convert every timestamp to timezone-aware UTC.
        """

        if timestamp is None:

            raise ValueError(
                "Timestamp cannot be None."
            )

        if not isinstance(
            timestamp,
            datetime,
        ):

            raise TypeError(
                "Timestamp must be datetime."
            )

        if timestamp.tzinfo is None:

            return timestamp.replace(
                tzinfo=timezone.utc
            )

        return timestamp.astimezone(
            timezone.utc
        )

    # ========================================================
    # SEED CURRENT CANDLE
    # ========================================================

    def seed_current_candle(
        self,
        candle: Candle,
    ) -> bool:

        """
        Seed the builder using a historical active candle.

        This does NOT emit a closed-candle event.

        The seeded candle becomes the current forming candle.
        """

        if candle is None:
            return False

        if self._paused:
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

            # ------------------------------------------------
            # Seed is a fresh live-state boundary.
            # ------------------------------------------------

            self.last_closed_candle = None

            self._last_emitted_closed_timestamp = None

            self._last_tick_timestamp = timestamp

            return True

        except Exception as exc:

            print(
                "Failed to seed live candle:",
                exc,
            )

            return False

    # ========================================================
    # FLOOR MINUTES
    # ========================================================

    @staticmethod
    def _floor_minutes(
        timestamp: datetime,
        minutes: int,
    ) -> datetime:

        return timestamp.replace(

            minute=(
                timestamp.minute
                // minutes
            ) * minutes,

            second=0,

            microsecond=0,
        )

    # ========================================================
    # FLOOR HOURS
    # ========================================================

    @staticmethod
    def _floor_hours(
        timestamp: datetime,
        hours: int,
    ) -> datetime:

        return timestamp.replace(

            hour=(
                timestamp.hour
                // hours
            ) * hours,

            minute=0,

            second=0,

            microsecond=0,
        )

    # ========================================================
    # CANDLE BUCKET
    # ========================================================

    def _get_bucket_time(
        self,
        timestamp: datetime,
    ) -> datetime:

        ts = (
            self._normalize_timestamp(
                timestamp
            )
        )

        timeframe = self.timeframe

        # ----------------------------------------------------
        # Minute timeframe
        # ----------------------------------------------------

        if timeframe in self.MINUTE_MAP:

            return self._floor_minutes(

                ts,

                self.MINUTE_MAP[
                    timeframe
                ],
            )

        # ----------------------------------------------------
        # Hour timeframe
        # ----------------------------------------------------

        if timeframe in self.HOUR_MAP:

            return self._floor_hours(

                ts,

                self.HOUR_MAP[
                    timeframe
                ],
            )

        # ----------------------------------------------------
        # Daily
        # ----------------------------------------------------

        if timeframe == "1d":

            return ts.replace(

                hour=0,

                minute=0,

                second=0,

                microsecond=0,
            )

        # ----------------------------------------------------
        # Weekly
        # ----------------------------------------------------

        if timeframe == "1w":

            start = ts.replace(

                hour=0,

                minute=0,

                second=0,

                microsecond=0,
            )

            return (
                start
                - timedelta(
                    days=start.weekday()
                )
            )

        # ----------------------------------------------------
        # Defensive fallback
        # ----------------------------------------------------

        return ts.replace(

            second=0,

            microsecond=0,
        )

    # ========================================================
    # VALIDATE OHLC
    # ========================================================

    @staticmethod
    def _validate_ohlc(
        open_price: float,
        high: float,
        low: float,
        close: float,
    ) -> bool:

        try:

            values = (
                float(open_price),
                float(high),
                float(low),
                float(close),
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):

            return False

        if any(
            value <= 0
            for value in values
        ):

            return False

        return (
            high >= open_price
            and high >= close
            and high >= low
            and low <= open_price
            and low <= close
        )

    # ========================================================
    # SAFE FLOAT
    # ========================================================

    @staticmethod
    def _safe_float(
        value,
        default: float = 0.0,
    ) -> float:

        try:

            result = float(value)

            if result != result:
                return default

            return result

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):

            return default

    # ========================================================
    # UPDATE TICK
    # ========================================================

    def update_tick(
        self,
        price: float,
        volume: float,
        timestamp: datetime,
    ) -> Optional[Candle]:

        """
        Process one Futures market tick.

        Returns
        -------
        Candle | None

        Returns the candle that has just closed when the
        incoming tick belongs to a newer candle bucket.

        Otherwise returns None.

        Flow
        ----
        Tick
          ↓
        Normalize timestamp
          ↓
        Validate price
          ↓
        Reject old tick
          ↓
        Calculate bucket
          ↓
        Same bucket?
          ├── YES → update current candle
          │
          └── NO
               ↓
          close current candle
               ↓
          start new candle
               ↓
          return closed candle

        Important
        ---------
        A closed candle is returned ONLY at the exact moment
        when the candle transitions to a newer bucket.

        We do NOT repeatedly return last_closed_candle on
        subsequent ticks.

        This is the key V20.9.5 exactly-once behavior.
        """

        # ----------------------------------------------------
        # PAUSED
        # ----------------------------------------------------

        if self._paused:
            return None

        # ----------------------------------------------------
        # NORMALIZE INPUT
        # ----------------------------------------------------

        try:

            ts = (
                self._normalize_timestamp(
                    timestamp
                )
            )

            price = float(price)

            volume = max(
                0.0,
                float(volume),
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):

            return None

        # ----------------------------------------------------
        # VALIDATE PRICE
        # ----------------------------------------------------

        if price <= 0:
            return None

        # ----------------------------------------------------
        # CALCULATE CURRENT TICK BUCKET
        # ----------------------------------------------------

        bucket = (
            self._get_bucket_time(
                ts
            )
        )

        # ====================================================
        # TICK ORDER PROTECTION
        # ====================================================

        if (
            self._last_tick_timestamp
            is not None
            and ts < self._last_tick_timestamp
        ):

            return None

        # ----------------------------------------------------
        # Accept timestamp as the newest processed tick.
        # ----------------------------------------------------

        self._last_tick_timestamp = ts

        # ====================================================
        # FIRST LIVE CANDLE
        # ====================================================

        if self.current_candle is None:

            self.current_candle = Candle(

                timestamp=bucket,

                open=price,

                high=price,

                low=price,

                close=price,

                volume=volume,
            )

            # ------------------------------------------------
            # First candle is live immediately.
            # ------------------------------------------------

            self._emit_live_update(
                self.current_candle
            )

            return None

        # ====================================================
        # SAME CANDLE
        # ====================================================

        if (
            bucket
            == self.current_candle.timestamp
        ):

            candle = (
                self.current_candle
            )

            # ------------------------------------------------
            # OHLC UPDATE
            # ------------------------------------------------

            candle.high = max(
                candle.high,
                price,
            )

            candle.low = min(
                candle.low,
                price,
            )

            candle.close = price

            # ------------------------------------------------
            # Volume accumulation
            # ------------------------------------------------

            candle.volume += volume

            # ------------------------------------------------
            # Live candle notification
            # ------------------------------------------------

            self._emit_live_update(
                candle
            )

            # ------------------------------------------------
            # IMPORTANT:
            #
            # No closed candle is returned here.
            #
            # This prevents the same last_closed_candle from
            # being rediscovered on every tick.
            # ------------------------------------------------

            return None

        # ====================================================
        # OLD CANDLE / OUT-OF-ORDER BUCKET
        # ====================================================

        if (
            bucket
            < self.current_candle.timestamp
        ):

            return None

        # ====================================================
        # NEW BUCKET DETECTED
        # ====================================================

        # ----------------------------------------------------
        # The current candle is now closed.
        # ----------------------------------------------------

        closed = self.current_candle

        closed_timestamp = (
            self._normalize_timestamp(
                closed.timestamp
            )
        )

        # ----------------------------------------------------
        # EXACTLY-ONCE PROTECTION
        #
        # This guard protects against an accidental repeated
        # transition with the same candle timestamp.
        # ----------------------------------------------------

        if (
            self._last_emitted_closed_timestamp
            is not None
            and closed_timestamp
            <= self._last_emitted_closed_timestamp
        ):

            closed = None

        else:

            self.last_closed_candle = (
                closed
            )

            self._last_emitted_closed_timestamp = (
                closed_timestamp
            )

            # ------------------------------------------------
            # Notify registered closed-candle consumer.
            # ------------------------------------------------

            self._emit_closed(
                closed
            )

        # ====================================================
        # START NEW LIVE CANDLE
        # ====================================================

        self.current_candle = Candle(

            timestamp=bucket,

            open=price,

            high=price,

            low=price,

            close=price,

            volume=volume,
        )

        # ----------------------------------------------------
        # New candle is immediately live.
        # ----------------------------------------------------

        self._emit_live_update(
            self.current_candle
        )

        # ----------------------------------------------------
        # Return ONLY the candle that was actually closed.
        #
        # If the exactly-once guard rejected the candle,
        # return None.
        # ----------------------------------------------------

        return closed

    # ========================================================
    # EMIT LIVE UPDATE
    # ========================================================

    def _emit_live_update(
        self,
        candle: Candle,
    ):

        """
        Emit current forming candle.

        This callback is optional.

        The builder itself never requires a callback in order
        to maintain candle state.
        """

        if candle is None:
            return

        callback = (
            self.live_update_callback
        )

        if callback is None:
            return

        try:

            callback(candle)

        except Exception as exc:

            # ------------------------------------------------
            # Callback errors must NEVER break candle
            # construction.
            # ------------------------------------------------

            print(
                "Live candle callback error:",
                exc,
            )

    # ========================================================
    # EMIT CLOSED CANDLE
    # ========================================================

    def _emit_closed(
        self,
        candle: Candle,
    ):

        """
        Emit a candle exactly when it transitions from
        forming -> closed.

        Candle construction is independent of this callback.
        """

        if candle is None:
            return

        callback = (
            self.candle_close_callback
        )

        if callback is None:
            return

        try:

            callback(candle)

        except Exception as exc:

            # ------------------------------------------------
            # Callback failure must not interrupt the market
            # data pipeline.
            # ------------------------------------------------

            print(
                "Candle close callback error:",
                exc,
            )

    # ========================================================
    # FORCE CLOSE CURRENT CANDLE
    # ========================================================

    def force_close_current_candle(
        self,
    ) -> Optional[Candle]:

        """
        Explicitly close the current candle.

        This is useful for controlled shutdown/reset
        scenarios or external lifecycle management.

        It does NOT create a new candle.

        Returns
        -------
        Candle | None
        """

        if self.current_candle is None:
            return None

        closed = self.current_candle

        timestamp = (
            self._normalize_timestamp(
                closed.timestamp
            )
        )

        # ----------------------------------------------------
        # Exactly-once protection
        # ----------------------------------------------------

        if (
            self._last_emitted_closed_timestamp
            is not None
            and timestamp
            <= self._last_emitted_closed_timestamp
        ):

            return None

        self.last_closed_candle = closed

        self._last_emitted_closed_timestamp = timestamp

        self._emit_closed(
            closed
        )

        self.current_candle = None

        return closed

    # ========================================================
    # CLEAR CURRENT CANDLE
    # ========================================================

    def clear_current_candle(
        self,
    ):

        """
        Remove the current forming candle.

        This does NOT emit a close event.
        """

        self.current_candle = None

    # ========================================================
    # CLEAR LAST CLOSED CANDLE
    # ========================================================

    def clear_last_closed_candle(
        self,
    ):

        """
        Remove stored last-closed candle reference.

        This is only state cleanup.

        It does NOT emit another close event.
        """

        self.last_closed_candle = None

    # ========================================================
    # CLEAR CLOSED-CANDLE DELIVERY STATE
    # ========================================================

    def clear_closed_delivery_state(
        self,
    ):

        """
        Reset the exactly-once closed-candle delivery marker.

        Normally this should NOT be required during normal
        tick processing.

        It is provided for controlled lifecycle operations.
        """

        self._last_emitted_closed_timestamp = None

    # ========================================================
    # LAST TICK TIMESTAMP
    # ========================================================

    def get_last_tick_timestamp(
        self,
    ) -> Optional[datetime]:

        return self._last_tick_timestamp

    # ========================================================
    # LAST EMITTED CLOSED TIMESTAMP
    # ========================================================

    def get_last_emitted_closed_timestamp(
        self,
    ) -> Optional[datetime]:

        return (
            self._last_emitted_closed_timestamp
        )

    # ========================================================
    # CANDLE TIMESTAMP
    # ========================================================

    def get_current_candle_timestamp(
        self,
    ) -> Optional[datetime]:

        if self.current_candle is None:
            return None

        return self.current_candle.timestamp

    # ========================================================
    # CANDLE AGE
    # ========================================================

    def get_current_candle_age_seconds(
        self,
        now: Optional[datetime] = None,
    ) -> Optional[float]:

        if self.current_candle is None:
            return None

        try:

            current_time = (
                self._normalize_timestamp(
                    now
                    if now is not None
                    else datetime.now(
                        timezone.utc
                    )
                )
            )

            candle_time = (
                self._normalize_timestamp(
                    self.current_candle.timestamp
                )
            )

            age = (
                current_time
                - candle_time
            ).total_seconds()

            return max(
                0.0,
                age,
            )

        except Exception:

            return None

    # ========================================================
    # CANDLE COPY
    # ========================================================

    @staticmethod
    def _copy_candle(
        candle: Optional[Candle],
    ) -> Optional[Candle]:

        if candle is None:
            return None

        return Candle(

            timestamp=candle.timestamp,

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

    # ========================================================
    # SAFE CURRENT CANDLE COPY
    # ========================================================

    def get_current_candle_copy(
        self,
    ) -> Optional[Candle]:

        return self._copy_candle(
            self.current_candle
        )

    # ========================================================
    # SAFE LAST CLOSED CANDLE COPY
    # ========================================================

    def get_last_closed_candle_copy(
        self,
    ) -> Optional[Candle]:

        return self._copy_candle(
            self.last_closed_candle
        )

    # ========================================================
    # SNAPSHOT
    # ========================================================

    def snapshot(self):

        current = self.current_candle
        closed = self.last_closed_candle

        return {
            "timeframe":
                self.timeframe,

            "paused":
                self._paused,

            "has_current_candle":
                current is not None,

            "has_last_closed_candle":
                closed is not None,

            "current_timestamp": (
                current.timestamp.isoformat()
                if current is not None
                else None
            ),

            "last_closed_timestamp": (
                closed.timestamp.isoformat()
                if closed is not None
                else None
            ),

            "last_tick_timestamp": (
                self._last_tick_timestamp.isoformat()
                if self._last_tick_timestamp is not None
                else None
            ),

            "last_emitted_closed_timestamp": (
                self._last_emitted_closed_timestamp.isoformat()
                if (
                    self._last_emitted_closed_timestamp
                    is not None
                )
                else None
            ),
        }

    # ========================================================
    # STATUS
    # ========================================================

    def get_status(self):

        return {
            "timeframe":
                self.timeframe,

            "paused":
                self._paused,

            "current_candle":
                self._copy_candle(
                    self.current_candle
                ),

            "last_closed_candle":
                self._copy_candle(
                    self.last_closed_candle
                ),

            "last_tick_timestamp":
                self._last_tick_timestamp,

            "last_emitted_closed_timestamp":
                self._last_emitted_closed_timestamp,
        }

    # ========================================================
    # CANDLE VALIDATION
    # ========================================================

    @staticmethod
    def validate_candle(
        candle: Optional[Candle],
    ) -> bool:

        if candle is None:
            return False

        try:

            if candle.timestamp is None:
                return False

            timestamp = (
                LiveCandleBuilder
                ._normalize_timestamp(
                    candle.timestamp
                )
            )

            if timestamp is None:
                return False

            open_price = float(
                candle.open
            )

            high_price = float(
                candle.high
            )

            low_price = float(
                candle.low
            )

            close_price = float(
                candle.close
            )

            volume = float(
                candle.volume
            )

            if (
                open_price <= 0
                or high_price <= 0
                or low_price <= 0
                or close_price <= 0
            ):
                return False

            if volume < 0:
                return False

            # ------------------------------------------------
            # OHLC structural validation
            # ------------------------------------------------

            if high_price < low_price:
                return False

            if high_price < open_price:
                return False

            if high_price < close_price:
                return False

            if low_price > open_price:
                return False

            if low_price > close_price:
                return False

            return True

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):

            return False

    # ========================================================
    # TIMEFRAME DURATION
    # ========================================================

    def timeframe_duration(
        self,
    ) -> Optional[timedelta]:

        tf = self.timeframe

        if tf in self.MINUTE_MAP:

            return timedelta(
                minutes=self.MINUTE_MAP[tf]
            )

        if tf in self.HOUR_MAP:

            return timedelta(
                hours=self.HOUR_MAP[tf]
            )

        if tf == "1d":

            return timedelta(
                days=1
            )

        if tf == "1w":

            return timedelta(
                weeks=1
            )

        return None

    # ========================================================
    # NEXT BUCKET
    # ========================================================

    def get_next_bucket_time(
        self,
        timestamp: datetime,
    ) -> Optional[datetime]:

        try:

            bucket = (
                self._get_bucket_time(
                    timestamp
                )
            )

            duration = (
                self.timeframe_duration()
            )

            if duration is None:
                return None

            return bucket + duration

        except Exception:

            return None

    # ========================================================
    # CURRENT CANDLE COMPLETE CHECK
    # ========================================================

    def is_candle_expired(
        self,
        now: Optional[datetime] = None,
    ) -> bool:

        if self.current_candle is None:
            return False

        try:

            current_time = (
                self._normalize_timestamp(
                    now
                    if now is not None
                    else datetime.now(
                        timezone.utc
                    )
                )
            )

            next_bucket = (
                self.get_next_bucket_time(
                    self.current_candle.timestamp
                )
            )

            if next_bucket is None:
                return False

            return current_time >= next_bucket

        except Exception:

            return False

    # ========================================================
    # ACTIVE CANDLE DATA
    # ========================================================

    def current_ohlcv(self):

        candle = self.current_candle

        if candle is None:
            return None

        return {
            "timestamp":
                candle.timestamp,

            "open":
                float(candle.open),

            "high":
                float(candle.high),

            "low":
                float(candle.low),

            "close":
                float(candle.close),

            "volume":
                float(candle.volume),
        }

    # ========================================================
    # LAST CLOSED OHLCV
    # ========================================================

    def last_closed_ohlcv(self):

        candle = self.last_closed_candle

        if candle is None:
            return None

        return {
            "timestamp":
                candle.timestamp,

            "open":
                float(candle.open),

            "high":
                float(candle.high),

            "low":
                float(candle.low),

            "close":
                float(candle.close),

            "volume":
                float(candle.volume),
        }

    # ========================================================
    # RESET
    # ========================================================

    def reset(self):

        """
        Complete live candle state reset.

        Used when:
            - Symbol changes
            - Timeframe changes
            - Futures WebSocket reconnects
            - Controller starts a new live session

        No callbacks are emitted during reset.
        """

        self.current_candle = None

        self.last_closed_candle = None

        self._last_tick_timestamp = None

        self._last_emitted_closed_timestamp = None

    # ========================================================
    # PAUSE
    # ========================================================

    def pause(self):

        self._paused = True

    # ========================================================
    # RESUME
    # ========================================================

    def resume(self):

        self._paused = False

    # ========================================================
    # CALLBACK REGISTRATION
    # ========================================================

    def set_live_update_callback(
        self,
        callback: Optional[
            Callable[[Candle], None]
        ],
    ):

        if callback is not None and not callable(
            callback
        ):
            raise TypeError(
                "live_update_callback "
                "must be callable or None."
            )

        self.live_update_callback = callback

    # ========================================================

    def set_candle_close_callback(
        self,
        callback: Optional[
            Callable[[Candle], None]
        ],
    ):

        if callback is not None and not callable(
            callback
        ):
            raise TypeError(
                "candle_close_callback "
                "must be callable or None."
            )

        self.candle_close_callback = callback

    # ========================================================
    # REMOVE CALLBACKS
    # ========================================================

    def remove_live_update_callback(self):

        self.live_update_callback = None

    def remove_candle_close_callback(self):

        self.candle_close_callback = None

    # ========================================================
    # CALLBACK STATUS
    # ========================================================

    def callbacks_status(self):

        return {
            "live_update_callback":
                self.live_update_callback
                is not None,

            "candle_close_callback":
                self.candle_close_callback
                is not None,
        }

    # ========================================================
    # CURRENT CANDLE EXISTENCE
    # ========================================================

    def has_active_candle(self) -> bool:

        return (
            self.current_candle
            is not None
        )

    # ========================================================
    # LAST CLOSED CANDLE EXISTENCE
    # ========================================================

    def has_last_closed_candle(self) -> bool:

        return (
            self.last_closed_candle
            is not None
        )

    # ========================================================
    # DEBUG SUMMARY
    # ========================================================

    def debug_summary(self):

        current = self.current_candle
        closed = self.last_closed_candle

        return {
            "class":
                self.__class__.__name__,

            "timeframe":
                self.timeframe,

            "paused":
                self._paused,

            "current_candle": (
                {
                    "timestamp":
                        current.timestamp,

                    "open":
                        current.open,

                    "high":
                        current.high,

                    "low":
                        current.low,

                    "close":
                        current.close,

                    "volume":
                        current.volume,
                }
                if current is not None
                else None
            ),

            "last_closed_candle": (
                {
                    "timestamp":
                        closed.timestamp,

                    "open":
                        closed.open,

                    "high":
                        closed.high,

                    "low":
                        closed.low,

                    "close":
                        closed.close,

                    "volume":
                        closed.volume,
                }
                if closed is not None
                else None
            ),

            "last_tick_timestamp":
                self._last_tick_timestamp,

            "last_emitted_closed_timestamp":
                self._last_emitted_closed_timestamp,

            "callbacks":
                self.callbacks_status(),
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self):

        return (
            "LiveCandleBuilder("
            f"timeframe='{self.timeframe}', "
            f"paused={self._paused}, "
            f"current="
            f"{self.current_candle is not None}, "
            f"last_closed="
            f"{self.last_closed_candle is not None}"
            ")"
        )