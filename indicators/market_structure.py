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
# Market Structure Engine V20.3
#
# V20.3 UPDATE
#
# Major change:
#
# Trend is NO LONGER calculated from the complete historical
# HH / HL / LH / LL count.
#
# Trend now uses the MOST RECENT CONFIRMED STRUCTURES.
#
# Default:
#
#     Recent structure lookback = 12
#
# These are structure points, NOT candles.
#
# Example:
#
#     HH
#     HL
#     HH
#     HL
#     LH
#     LL
#     ...
#
# Only the latest 12 labelled structure points are used for
# the current trend decision.
#
# This prevents old historical structure from dominating
# the current 15m HTF trend.
# ==========================================================


class MarketStructure:

    # ======================================================
    # INITIALIZATION
    # ======================================================

    def __init__(self):

        print(
            "Market Structure Engine V20.3 Initialized"
        )

        # --------------------------------------------------
        # Swing Settings
        # --------------------------------------------------

        self.left_strength = 2
        self.right_strength = 2

        # --------------------------------------------------
        # Trend Settings
        #
        # IMPORTANT:
        #
        # This is the number of RECENT CONFIRMED STRUCTURE
        # POINTS used for trend detection.
        #
        # It is NOT the number of candles.
        # --------------------------------------------------

        self.trend_structure_lookback = 12

        # --------------------------------------------------
        # Minimum price distance between consecutive
        # same-type swing points.
        #
        # 0 = disabled
        # --------------------------------------------------

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

        for i in range(
            index - left,
            index
        ):

            if highs[i] >= price:

                return False

        # --------------------------------------------------
        # Right side
        # --------------------------------------------------

        for i in range(
            index + 1,
            index + right + 1
        ):

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

        for i in range(
            index - left,
            index
        ):

            if lows[i] <= price:

                return False

        # --------------------------------------------------
        # Right side
        # --------------------------------------------------

        for i in range(
            index + 1,
            index + right + 1
        ):

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

        return (
            distance >=
            self.minimum_distance
        )

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

            # ==================================================
            # Swing High
            # ==================================================

            if self.is_swing_high(
                highs,
                i
            ):

                price = float(
                    highs[i]
                )

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

            # ==================================================
            # Swing Low
            # ==================================================

            if self.is_swing_low(
                lows,
                i
            ):

                price = float(
                    lows[i]
                )

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
            key=lambda item:
                item[0]
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
    #
    # IMPORTANT:
    #
    # These counters still represent the COMPLETE detected
    # dataset for compatibility/debugging.
    #
    # Trend itself does NOT use these complete counts anymore.
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
    # Get Recent Structures
    #
    # Returns only the latest confirmed labelled structure
    # points used by the Trend Engine.
    # ======================================================

    def get_recent_structures(self):

        recent = []

        # --------------------------------------------------
        # High structures
        # --------------------------------------------------

        for swing in self.swing_highs:

            if swing.label:

                recent.append(

                    {
                        "index":
                            swing.index,

                        "price":
                            swing.price,

                        "kind":
                            swing.kind,

                        "label":
                            swing.label
                    }

                )

        # --------------------------------------------------
        # Low structures
        # --------------------------------------------------

        for swing in self.swing_lows:

            if swing.label:

                recent.append(

                    {
                        "index":
                            swing.index,

                        "price":
                            swing.price,

                        "kind":
                            swing.kind,

                        "label":
                            swing.label
                    }

                )

        # --------------------------------------------------
        # Chronological order
        # --------------------------------------------------

        recent.sort(
            key=lambda item:
                item["index"]
        )

        # --------------------------------------------------
        # Keep latest N structures
        # --------------------------------------------------

        return recent[
            -self.trend_structure_lookback:
        ]

    # ======================================================
    # Detect Trend V20.3
    #
    # NEW TREND LOGIC
    #
    # Only recent confirmed structures are considered.
    #
    # Bullish evidence:
    #
    #     HH
    #     HL
    #
    # Bearish evidence:
    #
    #     LH
    #     LL
    #
    # Recent structures receive more importance.
    # ======================================================

    def detect_trend(self):

        recent_structures = (
            self.get_recent_structures()
        )

        # --------------------------------------------------
        # No recent structure
        # --------------------------------------------------

        if not recent_structures:

            self.trend_state.trend = "NONE"

            self.trend_state.strength = "WEAK"

            print(
                "\n========== TREND =========="
            )

            print(
                "Trend    : NONE"
            )

            print(
                "Strength : WEAK"
            )

            print(
                "Recent Structures : 0"
            )

            print(
                "===========================\n"
            )

            return

        # --------------------------------------------------
        # Recent structure counts
        # --------------------------------------------------

        recent_hh = sum(

            1

            for item in recent_structures

            if item["label"] == "HH"

        )

        recent_hl = sum(

            1

            for item in recent_structures

            if item["label"] == "HL"

        )

        recent_lh = sum(

            1

            for item in recent_structures

            if item["label"] == "LH"

        )

        recent_ll = sum(

            1

            for item in recent_structures

            if item["label"] == "LL"

        )

        # --------------------------------------------------
        # Weighted score
        #
        # Older recent structures get lower weight.
        #
        # Latest structure gets highest weight.
        #
        # Example with 12 structures:
        #
        # Oldest -> weight 1
        # ...
        # Latest -> weight 12
        # --------------------------------------------------

        bullish_score = 0

        bearish_score = 0

        total_weight = len(
            recent_structures
        )

        for position, structure in enumerate(
            recent_structures,
            start=1
        ):

            label = structure["label"]

            weight = position

            if label in (
                "HH",
                "HL"
            ):

                bullish_score += weight

            elif label in (
                "LH",
                "LL"
            ):

                bearish_score += weight

        # --------------------------------------------------
        # Difference
        # --------------------------------------------------

        score_difference = abs(

            bullish_score -
            bearish_score

        )

        # --------------------------------------------------
        # Dominance ratio
        #
        # This tells us how strongly one side dominates.
        # --------------------------------------------------

        total_score = (

            bullish_score +
            bearish_score

        )

        if total_score > 0:

            dominance = (
                score_difference /
                total_score
            )

        else:

            dominance = 0.0

        # --------------------------------------------------
        # Latest structure
        # --------------------------------------------------

        latest_label = (
            recent_structures[-1]["label"]
        )

        # --------------------------------------------------
        # Trend Decision
        #
        # We require both:
        #
        # 1. Directional score dominance
        # 2. Latest structure should not strongly oppose
        #    the direction.
        # --------------------------------------------------

        if (

            bullish_score >
            bearish_score

            and

            latest_label in (
                "HH",
                "HL"
            )

        ):

            self.trend_state.trend = (
                "BULLISH"
            )

        elif (

            bearish_score >
            bullish_score

            and

            latest_label in (
                "LH",
                "LL"
            )

        ):

            self.trend_state.trend = (
                "BEARISH"
            )

        else:

            self.trend_state.trend = (
                "SIDEWAYS"
            )

        # --------------------------------------------------
        # Strength
        #
        # Strong:
        #     dominance >= 0.35
        #
        # Medium:
        #     dominance >= 0.20
        #
        # Weak:
        #     below 0.20
        # --------------------------------------------------

        if dominance >= 0.35:

            self.trend_state.strength = (
                "STRONG"
            )

        elif dominance >= 0.20:

            self.trend_state.strength = (
                "MEDIUM"
            )

        else:

            self.trend_state.strength = (
                "WEAK"
            )

        # --------------------------------------------------
        # Debug
        # --------------------------------------------------

        print(
            "\n========== "
            "TREND V20.3 "
            "=========="
        )

        print(
            f"Recent Structures Used : "
            f"{len(recent_structures)}"
        )

        print(
            f"Recent HH : "
            f"{recent_hh}"
        )

        print(
            f"Recent HL : "
            f"{recent_hl}"
        )

        print(
            f"Recent LH : "
            f"{recent_lh}"
        )

        print(
            f"Recent LL : "
            f"{recent_ll}"
        )

        print(
            f"Bullish Score : "
            f"{bullish_score}"
        )

        print(
            f"Bearish Score : "
            f"{bearish_score}"
        )

        print(
            f"Dominance : "
            f"{dominance:.2f}"
        )

        print(
            f"Latest Structure : "
            f"{latest_label}"
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
            "================================\n"
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

            level = float(
                swing.price
            )

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
                    # One structure level = one BOS.
                    # --------------------------------------

                    break

        # --------------------------------------------------
        # Bearish BOS
        # --------------------------------------------------

        bearish_events = []

        for swing in self.swing_lows:

            level = float(
                swing.price
            )

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

            key=lambda event:
                event.index

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

                    "price":
                        event.level,

                    "index":
                        event.index,

                    "time":
                        None,

                    "close":
                        event.close,

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
        # Trend V20.3
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
                self.trend_state.latest_low_label,

            # --------------------------------------------------
            # V20.3 information
            # --------------------------------------------------

            "trend_structure_lookback":
                self.trend_structure_lookback,

            "recent_structures":
                self.get_recent_structures()
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

        recent_structures = (
            self.get_recent_structures()
        )

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
            f"Recent Structures Used: "
            f"{len(recent_structures)}"
        )

        print(
            f"Trend Lookback: "
            f"{self.trend_structure_lookback}"
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
                "V20.3",

            "status":
                "Production",

            "trend_logic":
                "Recent confirmed structure with weighted recency",

            "trend_structure_lookback":
                12,

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
            f"Trend Logic : "
            f"{info['trend_logic']}"
        )

        print(
            f"Trend Lookback : "
            f"{info['trend_structure_lookback']}"
        )

        print(
            "=================================\n"
        )

        return True