from __future__ import annotations

from dataclasses import dataclass
from typing import List


# ==========================================================
# Swing Point
# ==========================================================

@dataclass(slots=True)
class SwingPoint:
    index: int
    price: float
    kind: str          # HIGH / LOW
    label: str = ""    # HH / HL / LH / LL


# ==========================================================
# Structure Event
# ==========================================================

@dataclass(slots=True)
class StructureEvent:
    index: int
    event: str         # BOS / CHOCH
    direction: str     # BUY / SELL
    level: float


# ==========================================================
# Trend State
# ==========================================================

@dataclass(slots=True)
class TrendState:
    trend: str = "NONE"
    strength: str = "WEAK"

    hh: int = 0
    hl: int = 0
    lh: int = 0
    ll: int = 0


# ==========================================================
# Market Structure Engine V20
# ==========================================================

class MarketStructure:

    def __init__(self):

        print("Market Structure Engine V20 Initialized")

        # Swing Settings
        self.left_strength = 2
        self.right_strength = 2
        self.minimum_distance = 0

        # Runtime Storage
        self.swing_highs: List[SwingPoint] = []
        self.swing_lows: List[SwingPoint] = []

        self.structure_events: List[StructureEvent] = []

        self.trend_state = TrendState()

    # ======================================================
    # Reset Runtime
    # ======================================================

    def reset(self):

        self.swing_highs.clear()
        self.swing_lows.clear()
        self.structure_events.clear()

        self.trend_state = TrendState()

    # ======================================================
    # Validate Data
    # ======================================================

    def validate(self, data):

        if data is None:
            return False

        if len(data) < 10:
            return False

        required = [
            "Open",
            "High",
            "Low",
            "Close"
        ]

        for col in required:

            if col not in data.columns:
                return False

        return True

    # ======================================================
    # Swing High
    # ======================================================

    def is_swing_high(
        self,
        highs,
        index
    ):

        left = self.left_strength
        right = self.right_strength

        price = highs[index]

        for i in range(index - left, index):

            if highs[i] >= price:
                return False

        for i in range(index + 1, index + right + 1):

            if highs[i] > price:
                return False

        return True

    # ======================================================
    # Swing Low
    # ======================================================

    def is_swing_low(
        self,
        lows,
        index
    ):

        left = self.left_strength
        right = self.right_strength

        price = lows[index]

        for i in range(index - left, index):

            if lows[i] <= price:
                return False

        for i in range(index + 1, index + right + 1):

            if lows[i] < price:
                return False

        return True

    # ======================================================
    # Detect Swings
    # ======================================================

    def detect_swings(self, data):

        highs = data["High"].values
        lows = data["Low"].values

        left = self.left_strength
        right = self.right_strength

        for i in range(left, len(data) - right):

            if self.is_swing_high(highs, i):

                self.swing_highs.append(

                    SwingPoint(
                        index=i,
                        price=float(highs[i]),
                        kind="HIGH"
                    )

                )

            if self.is_swing_low(lows, i):

                self.swing_lows.append(

                    SwingPoint(
                        index=i,
                        price=float(lows[i]),
                        kind="LOW"
                    )

                )

        print(f"Swing Highs : {len(self.swing_highs)}")
        print(f"Swing Lows  : {len(self.swing_lows)}")

    # ======================================================
    # Classify Swing Highs
    # ======================================================

    def classify_highs(self):

        previous_high = None

        for swing in self.swing_highs:

            if previous_high is None:
                swing.label = "HH"

            elif swing.price > previous_high:
                swing.label = "HH"

            else:
                swing.label = "LH"

            previous_high = swing.price

    # ======================================================
    # Classify Swing Lows
    # ======================================================

    def classify_lows(self):

        previous_low = None

        for swing in self.swing_lows:

            if previous_low is None:
                swing.label = "HL"

            elif swing.price > previous_low:
                swing.label = "HL"

            else:
                swing.label = "LL"

            previous_low = swing.price

    # ======================================================
    # Update Trend Counters
    # ======================================================

    def update_trend_state(self):

        self.trend_state.hh = sum(
            1 for s in self.swing_highs
            if s.label == "HH"
        )

        self.trend_state.lh = sum(
            1 for s in self.swing_highs
            if s.label == "LH"
        )

        self.trend_state.hl = sum(
            1 for s in self.swing_lows
            if s.label == "HL"
        )

        self.trend_state.ll = sum(
            1 for s in self.swing_lows
            if s.label == "LL"
        )

        print("\n========== MARKET STRUCTURE ==========")
        print(f"HH : {self.trend_state.hh}")
        print(f"LH : {self.trend_state.lh}")
        print(f"HL : {self.trend_state.hl}")
        print(f"LL : {self.trend_state.ll}")
        print("======================================\n")

    # ======================================================
    # Detect Trend
    # ======================================================

    def detect_trend(self):

        hh = self.trend_state.hh
        hl = self.trend_state.hl
        lh = self.trend_state.lh
        ll = self.trend_state.ll

        # Bullish Trend
        if hh > lh and hl > ll:

            self.trend_state.trend = "BULLISH"

        # Bearish Trend
        elif ll > hl and lh > hh:

            self.trend_state.trend = "BEARISH"

        # Sideways
        else:

            self.trend_state.trend = "SIDEWAYS"

        # Trend Strength
        score = abs((hh + hl) - (lh + ll))

        if score >= 6:
            self.trend_state.strength = "STRONG"

        elif score >= 3:
            self.trend_state.strength = "MEDIUM"

        else:
            self.trend_state.strength = "WEAK"

        print("\n========== TREND ==========")
        print(f"Trend    : {self.trend_state.trend}")
        print(f"Strength : {self.trend_state.strength}")
        print("===========================\n")

    # ======================================================
    # Detect Break Of Structure (BOS)
    # ======================================================

    def detect_bos(self):

        self.structure_events.clear()

        # --------------------------------------------------
        # Bullish BOS
        # --------------------------------------------------

        for i in range(1, len(self.swing_highs)):

            previous = self.swing_highs[i - 1]
            current = self.swing_highs[i]

            if current.label != "HH":
                continue

            if current.price <= previous.price:
                continue

            self.structure_events.append(

                StructureEvent(

                    index=current.index,

                    event="BOS",

                    direction="BUY",

                    level=current.price

                )

            )

        # --------------------------------------------------
        # Bearish BOS
        # --------------------------------------------------

        for i in range(1, len(self.swing_lows)):

            previous = self.swing_lows[i - 1]
            current = self.swing_lows[i]

            if current.label != "LL":
                continue

            if current.price >= previous.price:
                continue

            self.structure_events.append(

                StructureEvent(

                    index=current.index,

                    event="BOS",

                    direction="SELL",

                    level=current.price

                )

            )

        # --------------------------------------------------
        # Debug Output
        # --------------------------------------------------

        print("\n========== BOS EVENTS ==========")

        if not self.structure_events:

            print("No BOS Detected")

        else:

            for event in self.structure_events:

                print(
                    f"{event.direction} BOS | "
                    f"Index : {event.index} | "
                    f"Level : {event.level}"
                )

        print("================================\n")

    # ======================================================
    # Export Structure Events
    # ======================================================

    def export_structure(self):

        result = []

        for event in self.structure_events:

            result.append(

                {
                    "type": (
                        "Bullish BOS"
                        if event.direction == "BUY"
                        else "Bearish BOS"
                    ),

                    "price": event.level,

                    "index": event.index,

                    "time": None
                }

            )

        return result

    # ======================================================
    # Public Detection API
    # ======================================================

    def detect(self, data):

        self.reset()

        if not self.validate(data):
            return []

        # ---------------------------------------------
        # Market Structure Pipeline
        # ---------------------------------------------

        self.detect_swings(data)

        self.classify_highs()

        self.classify_lows()

        self.update_trend_state()

        self.detect_trend()

        self.detect_bos()

        # ---------------------------------------------
        # Compatibility Output
        # ---------------------------------------------

        return self.export_structure()

    # ======================================================
    # Public Helper APIs
    # ======================================================

    def get_trend(self):

        return {
            "trend": self.trend_state.trend,
            "strength": self.trend_state.strength,
            "hh": self.trend_state.hh,
            "hl": self.trend_state.hl,
            "lh": self.trend_state.lh,
            "ll": self.trend_state.ll
        }

    def get_structure_events(self):

        return self.structure_events.copy()

    def get_swing_highs(self):

        return self.swing_highs.copy()

    def get_swing_lows(self):

        return self.swing_lows.copy()

    # ======================================================
    # Debug Summary
    # ======================================================

    def debug_summary(self):

        print("\n========== MARKET STRUCTURE SUMMARY ==========")

        print(f"Trend      : {self.trend_state.trend}")
        print(f"Strength   : {self.trend_state.strength}")

        print(f"HH Count   : {self.trend_state.hh}")
        print(f"HL Count   : {self.trend_state.hl}")
        print(f"LH Count   : {self.trend_state.lh}")
        print(f"LL Count   : {self.trend_state.ll}")

        print(f"Swing Highs: {len(self.swing_highs)}")
        print(f"Swing Lows : {len(self.swing_lows)}")

        print(f"BOS Events : {len(self.structure_events)}")

        print("==============================================\n")

    # ======================================================
    # Engine Information
    # ======================================================

    @staticmethod
    def version():

        return {
            "engine": "Market Structure Engine",
            "version": "V20",
            "status": "Production",
            "developer": "Liquidity Hunter AI"
        }

    # ======================================================
    # Self Test
    # ======================================================

    def self_test(self):

        print("\n========== ENGINE TEST ==========")

        info = self.version()

        print(f"Engine  : {info['engine']}")
        print(f"Version : {info['version']}")
        print(f"Status  : {info['status']}")

        print("=================================\n")

        return True