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

    # V20.2 confirmation information
    close: float = 0.0
    structure_index: int = -1


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

    latest_structure: str = ""
    latest_high_label: str = ""
    latest_low_label: str = ""


# ==========================================================
# Market Structure Engine V20.2
# Body-Close BOS Engine
# ==========================================================

class MarketStructure:

    def __init__(self):

        print("Market Structure Engine V20.2 Initialized")

        # --------------------------------------------------
        # Swing Settings
        # --------------------------------------------------

        self.left_strength = 2
        self.right_strength = 2

        # Minimum price distance between consecutive
        # same-type swing points.
        #
        # 0 = disabled
        #
        self.minimum_distance = 0.0

        # --------------------------------------------------
        # Runtime Storage
        # --------------------------------------------------

        self.swing_highs: List[SwingPoint] = []
        self.swing_lows: List[SwingPoint] = []

        self.structure_events: List[StructureEvent] = []

        self.trend_state = TrendState()

        # Chronological structure sequence
        self.structure_sequence: List[str] = []

        # Latest confirmed structure
        self.latest_structure: str = ""

    # ======================================================
    # Reset Runtime
    # ======================================================

    def reset(self):

        self.swing_highs.clear()
        self.swing_lows.clear()

        self.structure_events.clear()

        self.structure_sequence.clear()

        self.latest_structure = ""

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

        # --------------------------------------------------
        # Left side
        # --------------------------------------------------

        for i in range(index - left, index):

            if highs[i] >= price:
                return False

        # --------------------------------------------------
        # Right side
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Left side
        # --------------------------------------------------

        for i in range(index - left, index):

            if lows[i] <= price:
                return False

        # --------------------------------------------------
        # Right side
        # --------------------------------------------------

        for i in range(index + 1, index + right + 1):

            if lows[i] < price:
                return False

        return True

    # ======================================================
    # Minimum Swing Distance
    # ======================================================

    def _passes_minimum_distance(
        self,
        new_price: float,
        previous_price: float
    ) -> bool:

        distance = abs(
            new_price - previous_price
        )

        return distance >= self.minimum_distance

    # ======================================================
    # Detect Swings
    # ======================================================

    def detect_swings(self, data):

        highs = data["High"].values
        lows = data["Low"].values

        left = self.left_strength
        right = self.right_strength

        for i in range(
            left,
            len(data) - right
        ):

            # ------------------------------------------------
            # Swing High
            # ------------------------------------------------

            if self.is_swing_high(highs, i):

                price = float(highs[i])

                if self.swing_highs:

                    previous_price = (
                        self.swing_highs[-1].price
                    )

                    if not self._passes_minimum_distance(
                        price,
                        previous_price
                    ):
                        continue

                self.swing_highs.append(

                    SwingPoint(
                        index=i,
                        price=price,
                        kind="HIGH"
                    )

                )

            # ------------------------------------------------
            # Swing Low
            # ------------------------------------------------

            if self.is_swing_low(lows, i):

                price = float(lows[i])

                if self.swing_lows:

                    previous_price = (
                        self.swing_lows[-1].price
                    )

                    if not self._passes_minimum_distance(
                        price,
                        previous_price
                    ):
                        continue

                self.swing_lows.append(

                    SwingPoint(
                        index=i,
                        price=price,
                        kind="LOW"
                    )

                )

        print(
            f"Swing Highs : "
            f"{len(self.swing_highs)}"
        )

        print(
            f"Swing Lows  : "
            f"{len(self.swing_lows)}"
        )

    # ======================================================
    # Classify Swing Highs
    # ======================================================

    def classify_highs(self):

        previous_high = None

        for swing in self.swing_highs:

            # ------------------------------------------------
            # First confirmed high
            # ------------------------------------------------

            if previous_high is None:

                swing.label = ""

            # ------------------------------------------------
            # Higher High
            # ------------------------------------------------

            elif swing.price > previous_high:

                swing.label = "HH"

            # ------------------------------------------------
            # Lower High
            # ------------------------------------------------

            elif swing.price < previous_high:

                swing.label = "LH"

            # ------------------------------------------------
            # Equal High
            # ------------------------------------------------

            else:

                swing.label = ""

            previous_high = swing.price

    # ======================================================
    # Classify Swing Lows
    # ======================================================

    def classify_lows(self):

        previous_low = None

        for swing in self.swing_lows:

            # ------------------------------------------------
            # First confirmed low
            # ------------------------------------------------

            if previous_low is None:

                swing.label = ""

            # ------------------------------------------------
            # Higher Low
            # ------------------------------------------------

            elif swing.price > previous_low:

                swing.label = "HL"

            # ------------------------------------------------
            # Lower Low
            # ------------------------------------------------

            elif swing.price < previous_low:

                swing.label = "LL"

            # ------------------------------------------------
            # Equal Low
            # ------------------------------------------------

            else:

                swing.label = ""

            previous_low = swing.price

    # ======================================================
    # Build Structure Sequence
    # ======================================================

    def build_structure_sequence(self):

        points = []

        # --------------------------------------------------
        # High structures
        # --------------------------------------------------

        for swing in self.swing_highs:

            if swing.label:

                points.append(
                    (
                        swing.index,
                        swing.label
                    )
                )

        # --------------------------------------------------
        # Low structures
        # --------------------------------------------------

        for swing in self.swing_lows:

            if swing.label:

                points.append(
                    (
                        swing.index,
                        swing.label
                    )
                )

        # --------------------------------------------------
        # Chronological order
        # --------------------------------------------------

        points.sort(
            key=lambda item: item[0]
        )

        self.structure_sequence = [
            label
            for _, label in points
        ]

        # --------------------------------------------------
        # Latest structure
        # --------------------------------------------------

        if self.structure_sequence:

            self.latest_structure = (
                self.structure_sequence[-1]
            )

        else:

            self.latest_structure = ""

    # ======================================================
    # Update Trend Counters
    # ======================================================

    def update_trend_state(self):

        self.trend_state.hh = sum(
            1
            for s in self.swing_highs
            if s.label == "HH"
        )

        self.trend_state.hl = sum(
            1
            for s in self.swing_lows
            if s.label == "HL"
        )

        self.trend_state.lh = sum(
            1
            for s in self.swing_highs
            if s.label == "LH"
        )

        self.trend_state.ll = sum(
            1
            for s in self.swing_lows
            if s.label == "LL"
        )

        # --------------------------------------------------
        # Latest High
        # --------------------------------------------------

        labelled_highs = [
            s.label
            for s in self.swing_highs
            if s.label
        ]

        if labelled_highs:

            self.trend_state.latest_high_label = (
                labelled_highs[-1]
            )

        else:

            self.trend_state.latest_high_label = ""

        # --------------------------------------------------
        # Latest Low
        # --------------------------------------------------

        labelled_lows = [
            s.label
            for s in self.swing_lows
            if s.label
        ]

        if labelled_lows:

            self.trend_state.latest_low_label = (
                labelled_lows[-1]
            )

        else:

            self.trend_state.latest_low_label = ""

        # --------------------------------------------------
        # Latest Structure
        # --------------------------------------------------

        self.trend_state.latest_structure = (
            self.latest_structure
        )

        print(
            "\n========== "
            "MARKET STRUCTURE "
            "=========="
        )

        print(
            f"HH : "
            f"{self.trend_state.hh}"
        )

        print(
            f"HL : "
            f"{self.trend_state.hl}"
        )

        print(
            f"LH : "
            f"{self.trend_state.lh}"
        )

        print(
            f"LL : "
            f"{self.trend_state.ll}"
        )

        print(
            f"Latest High : "
            f"{self.trend_state.latest_high_label}"
        )

        print(
            f"Latest Low  : "
            f"{self.trend_state.latest_low_label}"
        )

        print(
            f"Latest Structure : "
            f"{self.trend_state.latest_structure}"
        )

        print(
            "======================================\n"
        )

    # ======================================================
    # Detect Trend
    #
    # V20.2 keeps the V20.1 trend calculation for
    # compatibility.
    #
    # Dedicated structure-state trend logic will be
    # upgraded in V20.3.
    # ======================================================

    def detect_trend(self):

        hh = self.trend_state.hh
        hl = self.trend_state.hl
        lh = self.trend_state.lh
        ll = self.trend_state.ll

        total_structure = (
            hh + hl + lh + ll
        )

        # --------------------------------------------------
        # No structure
        # --------------------------------------------------

        if total_structure == 0:

            self.trend_state.trend = "NONE"

            self.trend_state.strength = "WEAK"

            return

        # --------------------------------------------------
        # Bullish
        # --------------------------------------------------

        if hh > lh and hl > ll:

            self.trend_state.trend = "BULLISH"

        # --------------------------------------------------
        # Bearish
        # --------------------------------------------------

        elif ll > hl and lh > hh:

            self.trend_state.trend = "BEARISH"

        # --------------------------------------------------
        # Mixed / Sideways
        # --------------------------------------------------

        else:

            self.trend_state.trend = "SIDEWAYS"

        # --------------------------------------------------
        # Strength
        # --------------------------------------------------

        score = abs(
            (hh + hl) - (lh + ll)
        )

        if score >= 6:

            self.trend_state.strength = "STRONG"

        elif score >= 3:

            self.trend_state.strength = "MEDIUM"

        else:

            self.trend_state.strength = "WEAK"

        print(
            "\n========== TREND =========="
        )

        print(
            f"Trend    : "
            f"{self.trend_state.trend}"
        )

        print(
            f"Strength : "
            f"{self.trend_state.strength}"
        )

        print(
            "===========================\n"
        )

    # ======================================================
    # Detect Body-Close BOS
    #
    # V20.2 CORE LOGIC
    #
    # Bullish:
    # Close > confirmed swing high
    #
    # Bearish:
    # Close < confirmed swing low
    #
    # Wick-only break is NOT BOS.
    # ======================================================

    def detect_bos(self, data):

        self.structure_events.clear()

        closes = data["Close"].values

        # --------------------------------------------------
        # Bullish BOS
        # --------------------------------------------------

        bullish_events = []

        for swing in self.swing_highs:

            level = float(swing.price)

            swing_index = swing.index

            # ----------------------------------------------
            # Start checking AFTER the swing candle.
            #
            # The swing itself cannot break itself.
            # ----------------------------------------------

            start_index = (
                swing_index + 1
            )

            if start_index >= len(data):

                continue

            for candle_index in range(
                start_index,
                len(data)
            ):

                close_price = float(
                    closes[candle_index]
                )

                # ------------------------------------------
                # BODY CLOSE CONFIRMATION
                # ------------------------------------------

                if close_price > level:

                    bullish_events.append(

                        StructureEvent(

                            index=candle_index,

                            event="BOS",

                            direction="BUY",

                            level=level,

                            close=close_price,

                            structure_index=swing_index

                        )

                    )

                    # --------------------------------------
                    # IMPORTANT:
                    #
                    # One structure level can generate
                    # only ONE BOS.
                    # --------------------------------------

                    break

        # --------------------------------------------------
        # Bearish BOS
        # --------------------------------------------------

        bearish_events = []

        for swing in self.swing_lows:

            level = float(swing.price)

            swing_index = swing.index

            start_index = (
                swing_index + 1
            )

            if start_index >= len(data):

                continue

            for candle_index in range(
                start_index,
                len(data)
            ):

                close_price = float(
                    closes[candle_index]
                )

                # ------------------------------------------
                # BODY CLOSE CONFIRMATION
                # ------------------------------------------

                if close_price < level:

                    bearish_events.append(

                        StructureEvent(

                            index=candle_index,

                            event="BOS",

                            direction="SELL",

                            level=level,

                            close=close_price,

                            structure_index=swing_index

                        )

                    )

                    break

        # --------------------------------------------------
        # Merge
        # --------------------------------------------------

        self.structure_events = (
            bullish_events +
            bearish_events
        )

        # --------------------------------------------------
        # Chronological order
        # --------------------------------------------------

        self.structure_events.sort(
            key=lambda event: event.index
        )

        # --------------------------------------------------
        # Debug Output
        # --------------------------------------------------

        print(
            "\n========== "
            "BODY-CLOSE BOS EVENTS "
            "=========="
        )

        if not self.structure_events:

            print(
                "No Confirmed BOS Detected"
            )

        else:

            for event in self.structure_events:

                print(
                    f"{event.direction} BOS | "
                    f"Candle Index : "
                    f"{event.index} | "
                    f"Structure Index : "
                    f"{event.structure_index} | "
                    f"Level : "
                    f"{event.level} | "
                    f"Close : "
                    f"{event.close}"
                )

        print(
            "==========================================\n"
        )

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

                    "time": None,

                    # V20.2 information
                    "close": event.close,

                    "structure_index":
                        event.structure_index
                }

            )

        return result

    # ======================================================
    # Public Detection API
    # ======================================================

    def detect(self, data):

        # --------------------------------------------------
        # Reset
        # --------------------------------------------------

        self.reset()

        # --------------------------------------------------
        # Validate
        # --------------------------------------------------

        if not self.validate(data):

            return []

        # --------------------------------------------------
        # Swing Detection
        # --------------------------------------------------

        self.detect_swings(data)

        # --------------------------------------------------
        # Structure Classification
        # --------------------------------------------------

        self.classify_highs()

        self.classify_lows()

        # --------------------------------------------------
        # Structure Sequence
        # --------------------------------------------------

        self.build_structure_sequence()

        # --------------------------------------------------
        # State
        # --------------------------------------------------

        self.update_trend_state()

        # --------------------------------------------------
        # Trend
        # --------------------------------------------------

        self.detect_trend()

        # --------------------------------------------------
        # V20.2 Body-Close BOS
        # --------------------------------------------------

        self.detect_bos(data)

        # --------------------------------------------------
        # Compatibility Output
        # --------------------------------------------------

        return self.export_structure()

    # ======================================================
    # Public Helper APIs
    # ======================================================

    def get_trend(self):

        return {

            "trend":
                self.trend_state.trend,

            "strength":
                self.trend_state.strength,

            "hh":
                self.trend_state.hh,

            "hl":
                self.trend_state.hl,

            "lh":
                self.trend_state.lh,

            "ll":
                self.trend_state.ll,

            "latest_structure":
                self.trend_state.latest_structure,

            "latest_high_label":
                self.trend_state.latest_high_label,

            "latest_low_label":
                self.trend_state.latest_low_label
        }

    # ======================================================
    # Get Structure Events
    # ======================================================

    def get_structure_events(self):

        return self.structure_events.copy()

    # ======================================================
    # Get Swing Highs
    # ======================================================

    def get_swing_highs(self):

        return self.swing_highs.copy()

    # ======================================================
    # Get Swing Lows
    # ======================================================

    def get_swing_lows(self):

        return self.swing_lows.copy()

    # ======================================================
    # Get Structure Sequence
    # ======================================================

    def get_structure_sequence(self):

        return self.structure_sequence.copy()

    # ======================================================
    # Get Latest Structure
    # ======================================================

    def get_latest_structure(self):

        return self.latest_structure

    # ======================================================
    # Get BOS Events
    # ======================================================

    def get_bos_events(self):

        return [
            event
            for event in self.structure_events
            if event.event == "BOS"
        ]

    # ======================================================
    # Debug Summary
    # ======================================================

    def debug_summary(self):

        print(
            "\n========== "
            "MARKET STRUCTURE SUMMARY "
            "=========="
        )

        print(
            f"Trend      : "
            f"{self.trend_state.trend}"
        )

        print(
            f"Strength   : "
            f"{self.trend_state.strength}"
        )

        print(
            f"HH Count   : "
            f"{self.trend_state.hh}"
        )

        print(
            f"HL Count   : "
            f"{self.trend_state.hl}"
        )

        print(
            f"LH Count   : "
            f"{self.trend_state.lh}"
        )

        print(
            f"LL Count   : "
            f"{self.trend_state.ll}"
        )

        print(
            f"Latest High: "
            f"{self.trend_state.latest_high_label}"
        )

        print(
            f"Latest Low : "
            f"{self.trend_state.latest_low_label}"
        )

        print(
            f"Latest Structure: "
            f"{self.trend_state.latest_structure}"
        )

        print(
            f"Structure Sequence: "
            f"{self.structure_sequence}"
        )

        print(
            f"Swing Highs: "
            f"{len(self.swing_highs)}"
        )

        print(
            f"Swing Lows : "
            f"{len(self.swing_lows)}"
        )

        print(
            f"Confirmed BOS Events: "
            f"{len(self.structure_events)}"
        )

        print(
            "==============================================\n"
        )

    # ======================================================
    # Engine Information
    # ======================================================

    @staticmethod
    def version():

        return {

            "engine":
                "Market Structure Engine",

            "version":
                "V20.2",

            "status":
                "Production",

            "developer":
                "Liquidity Hunter AI"
        }

    # ======================================================
    # Self Test
    # ======================================================

    def self_test(self):

        print(
            "\n========== ENGINE TEST =========="
        )

        info = self.version()

        print(
            f"Engine  : "
            f"{info['engine']}"
        )

        print(
            f"Version : "
            f"{info['version']}"
        )

        print(
            f"Status  : "
            f"{info['status']}"
        )

        print(
            "=================================\n"
        )

        return True