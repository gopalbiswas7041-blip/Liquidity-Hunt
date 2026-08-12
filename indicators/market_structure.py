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
# Market Structure Engine V20.4
#
# ==========================================================
#
# V20.4 MAJOR TREND UPDATE
#
# V20.3 used:
#
#     Recent HH / HL / LH / LL
#             +
#     Weighted structure recency
#
# Problem:
#
# A market could have a strong current bearish move while
# old HH / HL structures inside the recent structure window
# still dominate the score.
#
# Example:
#
#     Old bullish structures
#             +
#     Recent SELL BOS
#     Recent SELL BOS
#     Recent SELL BOS
#
# V20.3 could incorrectly produce:
#
#     SIDEWAYS
#
# V20.4 fixes this by using:
#
#     1. Recent confirmed structures
#     2. Recent BODY-CLOSE BOS
#     3. BOS recency weighting
#     4. Current BOS direction
#     5. Latest structure direction
#
# Priority:
#
#     CURRENT CONFIRMED BOS
#             >
#     RECENT STRUCTURE
#             >
#     OLD STRUCTURE
#
#
# IMPORTANT:
#
# Red candles alone do NOT create trend.
#
# Trend requires confirmed structure/BOS evidence.
#
# ==========================================================


class MarketStructure:

    # ======================================================
    # INITIALIZATION
    # ======================================================

    def __init__(self):

        print(
            "Market Structure Engine V20.4 Initialized"
        )

        # --------------------------------------------------
        # Swing Settings
        # --------------------------------------------------

        self.left_strength = 2
        self.right_strength = 2

        # --------------------------------------------------
        # Structure Trend Settings
        #
        # Number of recent labelled structure points.
        #
        # These are STRUCTURES, not candles.
        # --------------------------------------------------

        self.trend_structure_lookback = 12

        # --------------------------------------------------
        # BOS Trend Settings
        #
        # Number of latest confirmed BOS events used for
        # current directional trend.
        # --------------------------------------------------

        self.trend_bos_lookback = 8

        # --------------------------------------------------
        # Minimum number of same-direction recent BOS events
        # required to activate the current BOS leg.
        #
        # Example:
        #
        #     SELL
        #     SELL
        #     SELL
        #
        # = bearish current leg
        # --------------------------------------------------

        self.minimum_bos_confirmation = 2

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

        # --------------------------------------------------
        # Runtime Trend Diagnostics
        # --------------------------------------------------

        self.recent_bos_direction = "NONE"

        self.recent_bos_count = 0

        self.bullish_bos_score = 0

        self.bearish_bos_score = 0

        self.bos_dominance = 0.0

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

        self.recent_bos_direction = "NONE"

        self.recent_bos_count = 0

        self.bullish_bos_score = 0

        self.bearish_bos_score = 0

        self.bos_dominance = 0.0

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
    # These counters remain COMPLETE DATASET counters.
    #
    # They are NOT used directly as the primary trend.
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
    # Detect Body-Close BOS
    #
    # V20.2 CORE LOGIC
    #
    # Bullish:
    #
    #     Close > confirmed swing high
    #
    # Bearish:
    #
    #     Close < confirmed swing low
    #
    # Wick-only break is NOT BOS.
    #
    # IMPORTANT:
    #
    # This function is intentionally kept compatible with
    # the previous V20.3 BOS output.
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
    # Get Recent BOS Events
    #
    # Only latest confirmed BOS events are used by V20.4
    # trend logic.
    # ======================================================

    def get_recent_bos_events(self):

        bos_events = [

            event

            for event in self.structure_events

            if event.event == "BOS"

        ]

        bos_events.sort(
            key=lambda event:
                event.index
        )

        return bos_events[
            -self.trend_bos_lookback:
        ]

    # ======================================================
    # Analyze Recent BOS
    #
    # V20.4 CURRENT LEG ENGINE
    #
    # Recent BOS receives higher importance than old
    # structure labels.
    # ======================================================

    def _analyze_recent_bos(self):

        recent_bos = (
            self.get_recent_bos_events()
        )

        # --------------------------------------------------
        # Reset diagnostics
        # --------------------------------------------------

        self.recent_bos_direction = "NONE"

        self.recent_bos_count = len(
            recent_bos
        )

        self.bullish_bos_score = 0

        self.bearish_bos_score = 0

        self.bos_dominance = 0.0

        # --------------------------------------------------
        # No BOS
        # --------------------------------------------------

        if not recent_bos:

            return {

                "direction": "NONE",

                "count": 0,

                "bullish_score": 0,

                "bearish_score": 0,

                "dominance": 0.0,

                "latest_direction": "NONE",

                "latest_index": -1,

                "same_direction_count": 0

            }

        # --------------------------------------------------
        # Weighted BOS
        #
        # Oldest recent BOS -> weight 1
        # Latest BOS       -> highest weight
        # --------------------------------------------------

        for position, event in enumerate(
            recent_bos,
            start=1
        ):

            weight = position

            if event.direction == "BUY":

                self.bullish_bos_score += weight

            elif event.direction == "SELL":

                self.bearish_bos_score += weight

        # --------------------------------------------------
        # Latest BOS
        # --------------------------------------------------

        latest_event = recent_bos[-1]

        latest_direction = (
            latest_event.direction
        )

        # --------------------------------------------------
        # Consecutive same-direction BOS
        #
        # Starting from the latest BOS and moving backward.
        # --------------------------------------------------

        same_direction_count = 0

        for event in reversed(
            recent_bos
        ):

            if event.direction == latest_direction:

                same_direction_count += 1

            else:

                break

        # --------------------------------------------------
        # Weighted dominance
        # --------------------------------------------------

        total_score = (

            self.bullish_bos_score +
            self.bearish_bos_score

        )

        if total_score > 0:

            score_difference = abs(

                self.bullish_bos_score -
                self.bearish_bos_score

            )

            self.bos_dominance = (

                score_difference /
                total_score

            )

        else:

            self.bos_dominance = 0.0

        # --------------------------------------------------
        # Current BOS direction
        #
        # Strong current leg:
        #
        #     At least 2 consecutive BOS
        #
        # Otherwise weighted recent BOS direction.
        # --------------------------------------------------

        if same_direction_count >= (
            self.minimum_bos_confirmation
        ):

            self.recent_bos_direction = (
                latest_direction
            )

        elif (
            self.bullish_bos_score >
            self.bearish_bos_score
        ):

            self.recent_bos_direction = "BUY"

        elif (
            self.bearish_bos_score >
            self.bullish_bos_score
        ):

            self.recent_bos_direction = "SELL"

        else:

            self.recent_bos_direction = "NONE"

        return {

            "direction":
                self.recent_bos_direction,

            "count":
                len(recent_bos),

            "bullish_score":
                self.bullish_bos_score,

            "bearish_score":
                self.bearish_bos_score,

            "dominance":
                self.bos_dominance,

            "latest_direction":
                latest_direction,

            "latest_index":
                latest_event.index,

            "latest_level":
                latest_event.level,

            "latest_close":
                latest_event.close,

            "same_direction_count":
                same_direction_count

        }

    # ======================================================
    # Detect Trend V20.4
    #
    # PRIMARY TREND LOGIC
    #
    # Priority:
    #
    #     1. Current confirmed BOS leg
    #     2. Recent structure
    #     3. Weighted structure score
    #
    # This prevents old bullish structures from masking a
    # fresh bearish market leg.
    # ======================================================

    def detect_trend(self):

        recent_structures = (
            self.get_recent_structures()
        )

        # --------------------------------------------------
        # Structure score
        # --------------------------------------------------

        bullish_structure_score = 0

        bearish_structure_score = 0

        recent_hh = 0
        recent_hl = 0
        recent_lh = 0
        recent_ll = 0

        for position, structure in enumerate(
            recent_structures,
            start=1
        ):

            label = structure["label"]

            weight = position

            if label == "HH":

                recent_hh += 1

                bullish_structure_score += weight

            elif label == "HL":

                recent_hl += 1

                bullish_structure_score += weight

            elif label == "LH":

                recent_lh += 1

                bearish_structure_score += weight

            elif label == "LL":

                recent_ll += 1

                bearish_structure_score += weight

        # --------------------------------------------------
        # Structure dominance
        # --------------------------------------------------

        structure_total = (

            bullish_structure_score +
            bearish_structure_score

        )

        if structure_total > 0:

            structure_difference = abs(

                bullish_structure_score -
                bearish_structure_score

            )

            structure_dominance = (

                structure_difference /
                structure_total

            )

        else:

            structure_dominance = 0.0

        # --------------------------------------------------
        # Latest structure
        # --------------------------------------------------

        if recent_structures:

            latest_label = (
                recent_structures[-1]["label"]
            )

        else:

            latest_label = ""

        # --------------------------------------------------
        # Recent BOS analysis
        # --------------------------------------------------

        bos_info = (
            self._analyze_recent_bos()
        )

        bos_direction = (
            bos_info["direction"]
        )

        bos_same_direction_count = (
            bos_info["same_direction_count"]
        )

        bos_dominance = (
            bos_info["dominance"]
        )

        # --------------------------------------------------
        # DEBUG: Recent Structure Sequence
        # --------------------------------------------------

        print(
            "Recent Structure Sequence :",
            [
                item["label"]
                for item in recent_structures
            ]
        )

        # --------------------------------------------------
        # TREND DECISION
        #
        # Rule 1:
        #
        # Multiple recent same-direction BOS events have
        # priority over historical structure imbalance.
        #
        # Example:
        #
        #     SELL BOS
        #     SELL BOS
        #     SELL BOS
        #
        # => BEARISH
        #
        # Rule 2:
        #
        # A strong BOS direction plus matching structure
        # gives STRONG trend.
        #
        # Rule 3:
        #
        # If BOS is mixed and structure is also mixed,
        # remain SIDEWAYS.
        # --------------------------------------------------

        trend = "SIDEWAYS"

        strength = "WEAK"

        # ==================================================
        # STRONG CURRENT BEARISH LEG
        # ==================================================

        if (

            bos_direction == "SELL"

            and

            bos_same_direction_count >=
            self.minimum_bos_confirmation

        ):

            trend = "BEARISH"

            # ----------------------------------------------
            # Strong if:
            #
            # 3+ consecutive bearish BOS
            #
            # OR
            #
            # BOS dominance >= 0.35
            # AND latest structure bearish
            # ----------------------------------------------

            if (

                bos_same_direction_count >= 3

                or

                (
                    bos_dominance >= 0.35
                    and
                    latest_label in (
                        "LH",
                        "LL"
                    )
                )

            ):

                strength = "STRONG"

            else:

                strength = "MEDIUM"

        # ==================================================
        # STRONG CURRENT BULLISH LEG
        # ==================================================

        elif (

            bos_direction == "BUY"

            and

            bos_same_direction_count >=
            self.minimum_bos_confirmation

        ):

            trend = "BULLISH"

            if (

                bos_same_direction_count >= 3

                or

                (
                    bos_dominance >= 0.35
                    and
                    latest_label in (
                        "HH",
                        "HL"
                    )
                )

            ):

                strength = "STRONG"

            else:

                strength = "MEDIUM"

        # ==================================================
        # NO STRONG CURRENT BOS LEG
        # ==================================================

        else:

            # ------------------------------------------------
            # Use structure trend
            # ------------------------------------------------

            if (

                bullish_structure_score >
                bearish_structure_score

                and

                latest_label in (
                    "HH",
                    "HL"
                )

            ):

                trend = "BULLISH"

                if structure_dominance >= 0.35:

                    strength = "STRONG"

                elif structure_dominance >= 0.20:

                    strength = "MEDIUM"

                else:

                    strength = "WEAK"

            elif (

                bearish_structure_score >
                bullish_structure_score

                and

                latest_label in (
                    "LH",
                    "LL"
                )

            ):

                trend = "BEARISH"

                if structure_dominance >= 0.35:

                    strength = "STRONG"

                elif structure_dominance >= 0.20:

                    strength = "MEDIUM"

                else:

                    strength = "WEAK"

            else:

                trend = "SIDEWAYS"

                strength = "WEAK"

        # ==================================================
        # BOS / STRUCTURE CONFLICT PROTECTION
        #
        # If the latest BOS is strongly against the current
        # structure trend, do NOT blindly call strong trend
        # unless multiple BOS confirm it.
        #
        # Multiple consecutive BOS already have priority.
        # ==================================================

        if trend == "BEARISH":

            if (

                bos_direction == "BUY"

                and

                bos_same_direction_count <
                self.minimum_bos_confirmation

            ):

                if (

                    latest_label in (
                        "HH",
                        "HL"
                    )

                ):

                    trend = "SIDEWAYS"

                    strength = "WEAK"

        elif trend == "BULLISH":

            if (

                bos_direction == "SELL"

                and

                bos_same_direction_count <
                self.minimum_bos_confirmation

            ):

                if (

                    latest_label in (
                        "LH",
                        "LL"
                    )

                ):

                    trend = "SIDEWAYS"

                    strength = "WEAK"

        # ==================================================
        # Store Trend
        # ==================================================

        self.trend_state.trend = trend

        self.trend_state.strength = strength

        # ==================================================
        # Debug
        # ==================================================

        print(
            "\n========== "
            "TREND V20.4 "
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
            f"Structure Bullish Score : "
            f"{bullish_structure_score}"
        )

        print(
            f"Structure Bearish Score : "
            f"{bearish_structure_score}"
        )

        print(
            f"Structure Dominance : "
            f"{structure_dominance:.2f}"
        )

        print(
            f"Recent BOS Used : "
            f"{bos_info['count']}"
        )

        print(
            f"BOS Bullish Score : "
            f"{bos_info['bullish_score']}"
        )

        print(
            f"BOS Bearish Score : "
            f"{bos_info['bearish_score']}"
        )

        print(
            f"BOS Dominance : "
            f"{bos_info['dominance']:.2f}"
        )

        print(
            f"Latest BOS Direction : "
            f"{bos_info['latest_direction']}"
        )

        print(
            f"Latest BOS Index : "
            f"{bos_info['latest_index']}"
        )

        print(
            f"Consecutive Same BOS : "
            f"{bos_info['same_direction_count']}"
        )

        print(
            f"Current BOS Direction : "
            f"{bos_direction}"
        )

        print(
            f"Latest Structure : "
            f"{latest_label}"
        )

        print(
            f"Trend    : "
            f"{trend}"
        )

        print(
            f"Strength : "
            f"{strength}"
        )

        print(
            "================================\n"
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
        # Body-Close BOS
        #
        # IMPORTANT:
        #
        # BOS must be detected BEFORE trend because V20.4
        # trend uses recent BOS information.
        # --------------------------------------------------

        self.detect_bos(data)

        # --------------------------------------------------
        # Trend V20.4
        # --------------------------------------------------

        self.detect_trend()

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
            # V20.3 compatibility
            # --------------------------------------------------

            "trend_structure_lookback":
                self.trend_structure_lookback,

            "recent_structures":
                self.get_recent_structures(),

            # --------------------------------------------------
            # V20.4 Trend Diagnostics
            # --------------------------------------------------

            "trend_bos_lookback":
                self.trend_bos_lookback,

            "recent_bos_direction":
                self.recent_bos_direction,

            "recent_bos_count":
                self.recent_bos_count,

            "bullish_bos_score":
                self.bullish_bos_score,

            "bearish_bos_score":
                self.bearish_bos_score,

            "bos_dominance":
                self.bos_dominance

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
    # Get Recent BOS
    # ======================================================

    def get_recent_bos(self):

        return self.get_recent_bos_events()

    # ======================================================
    # Debug Summary
    # ======================================================

    def debug_summary(self):

        recent_structures = (
            self.get_recent_structures()
        )

        recent_bos = (
            self.get_recent_bos_events()
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
            f"Trend Structure Lookback: "
            f"{self.trend_structure_lookback}"
        )

        print(
            f"Recent BOS Used: "
            f"{len(recent_bos)}"
        )

        print(
            f"Trend BOS Lookback: "
            f"{self.trend_bos_lookback}"
        )

        print(
            f"Recent BOS Direction: "
            f"{self.recent_bos_direction}"
        )

        print(
            f"Consecutive Same BOS: "
            f"{self._get_consecutive_bos_count()}"
        )

        print(
            f"BOS Bullish Score: "
            f"{self.bullish_bos_score}"
        )

        print(
            f"BOS Bearish Score: "
            f"{self.bearish_bos_score}"
        )

        print(
            f"BOS Dominance: "
            f"{self.bos_dominance:.2f}"
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
    # Consecutive BOS Helper
    # ======================================================

    def _get_consecutive_bos_count(self):

        recent_bos = (
            self.get_recent_bos_events()
        )

        if not recent_bos:

            return 0

        latest_direction = (
            recent_bos[-1].direction
        )

        count = 0

        for event in reversed(
            recent_bos
        ):

            if event.direction == latest_direction:

                count += 1

            else:

                break

        return count

    # ======================================================
    # Engine Information
    # ======================================================

    @staticmethod
    def version():

        return {

            "engine":
                "Market Structure Engine",

            "version":
                "V20.4",

            "status":
                "Production",

            "trend_logic":
                (
                    "Recent structure + "
                    "confirmed body-close BOS "
                    "with BOS recency priority"
                ),

            "trend_structure_lookback":
                12,

            "trend_bos_lookback":
                8,

            "minimum_bos_confirmation":
                2,

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
            f"Trend Structure Lookback : "
            f"{info['trend_structure_lookback']}"
        )

        print(
            f"Trend BOS Lookback : "
            f"{info['trend_bos_lookback']}"
        )

        print(
            f"Minimum BOS Confirmation : "
            f"{info['minimum_bos_confirmation']}"
        )

        print(
            "=================================\n"
        )

        return True