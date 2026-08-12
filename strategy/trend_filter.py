from __future__ import annotations

from typing import Any, Dict, Optional


# ==========================================================
# Liquidity Hunter AI
# Trend Filter V20.5
#
# Purpose
# -------
# Higher Timeframe Trend Filter
#
# Default:
#     15m HTF
#
# Pipeline:
#
# Market Data
#      ↓
# MarketStructure V20.3
#      ↓
# Recent Confirmed Structures
#      ↓
# Weighted Trend
#      ↓
# BUY / SELL / NONE
#
# Optional:
# CHoCH V2.5 can be supplied as additional confirmation.
#
# IMPORTANT:
#
# MarketStructure V20.3 already contains the primary trend
# engine.
#
# TrendFilter must NOT calculate a second conflicting trend
# using old BOS/CHoCH counting logic.
# ==========================================================


class TrendFilter:

    # ======================================================
    # INITIALIZATION
    # ======================================================

    def __init__(self):

        print(
            "Trend Filter Engine V20.5 Initialized"
        )

        # --------------------------------------------------
        # Market Structure Engine
        # --------------------------------------------------

        from indicators.market_structure import (
            MarketStructure
        )

        self.structure = MarketStructure()

        # --------------------------------------------------
        # Optional CHoCH Engine
        # --------------------------------------------------

        from indicators.choch_v2 import (
            CHoCHV2
        )

        self.choch = CHoCHV2()

        # --------------------------------------------------
        # Recent structure information
        #
        # IMPORTANT:
        #
        # This should remain aligned with
        # MarketStructure V20.3.
        # --------------------------------------------------

        self.lookback = (
            self.structure.trend_structure_lookback
        )

    # ======================================================
    # Default Result
    # ======================================================

    def _create_result(self):

        return {

            "trend":
                "NONE",

            "status":
                "SIDEWAYS",

            "strength":
                "WEAK",

            "score":
                0,

            "bullish":
                0,

            "bearish":
                0,

            "reason":
                "",

            # --------------------------------------------------
            # Structure Information
            # --------------------------------------------------

            "latest_structure":
                "",

            "latest_high_label":
                "",

            "latest_low_label":
                "",

            "recent_structures":
                [],

            "structure_lookback":
                self.lookback,

            # --------------------------------------------------
            # Optional CHoCH Information
            # --------------------------------------------------

            "choch_confirmed":
                False,

            "choch_direction":
                None,

            "choch_strength":
                0

        }

    # ======================================================
    # Normalize Market Structure Trend
    #
    # MarketStructure V20.3 returns:
    #
    #     BULLISH
    #     BEARISH
    #     SIDEWAYS
    #     NONE
    #
    # TrendFilter exposes:
    #
    #     BUY
    #     SELL
    #     NONE
    # ======================================================

    @staticmethod
    def _normalize_trend(
        trend: Any
    ) -> str:

        if trend is None:

            return "NONE"

        value = str(
            trend
        ).upper().strip()

        if value in (
            "BULLISH",
            "BUY"
        ):

            return "BUY"

        if value in (
            "BEARISH",
            "SELL"
        ):

            return "SELL"

        return "NONE"

    # ======================================================
    # Calculate Compatibility Score
    #
    # MarketStructure V20.3 is the actual trend engine.
    #
    # This score is only an informational score for
    # downstream compatibility/debugging.
    #
    # It does NOT replace MarketStructure's trend logic.
    # ======================================================

    @staticmethod
    def _calculate_score(
        trend: str,
        strength: str
    ):

        if trend == "BUY":

            if strength == "STRONG":
                return 10, 0

            if strength == "MEDIUM":
                return 7, 0

            return 5, 0

        if trend == "SELL":

            if strength == "STRONG":
                return 0, 10

            if strength == "MEDIUM":
                return 0, 7

            return 0, 5

        return 0, 0

    # ======================================================
    # Extract CHoCH Information
    #
    # CHoCH is optional.
    #
    # IMPORTANT:
    #
    # HTF trend remains controlled by MarketStructure.
    #
    # CHoCH is only additional information.
    # ======================================================

    def _extract_choch(
        self,
        choch_result
    ):

        result = {

            "confirmed":
                False,

            "direction":
                None,

            "strength":
                0

        }

        if not isinstance(
            choch_result,
            dict
        ):

            return result

        if not choch_result.get(
            "choch",
            False
        ):

            return result

        direction = (
            choch_result.get(
                "direction"
            )
        )

        if direction not in (
            "BUY",
            "SELL"
        ):

            return result

        result["confirmed"] = True

        result["direction"] = (
            direction
        )

        try:

            result["strength"] = int(
                choch_result.get(
                    "strength",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            result["strength"] = 0

        return result

    # ======================================================
    # Analyze
    # ======================================================

    def analyze(
        self,
        data,
        choch_result=None
    ):

        result = (
            self._create_result()
        )

        # ==================================================
        # Validate Data
        # ==================================================

        if data is None:

            result["reason"] = (
                "Market Data Missing"
            )

            return result

        if len(data) < 20:

            result["reason"] = (
                "Not Enough Candles"
            )

            return result

        # ==================================================
        # Run Market Structure V20.3
        # ==================================================

        try:

            self.structure.detect(
                data
            )

        except Exception as error:

            result["reason"] = (
                "Market Structure Error: "
                f"{error}"
            )

            print(
                result["reason"]
            )

            return result

        # ==================================================
        # Get V20.3 Trend
        # ==================================================

        structure_trend = (
            self.structure.get_trend()
        )

        if not isinstance(
            structure_trend,
            dict
        ):

            result["reason"] = (
                "Invalid Market Structure Trend"
            )

            return result

        # ==================================================
        # Primary Trend
        # ==================================================

        raw_trend = (
            structure_trend.get(
                "trend",
                "NONE"
            )
        )

        trend = (
            self._normalize_trend(
                raw_trend
            )
        )

        # ==================================================
        # Strength
        # ==================================================

        strength = str(
            structure_trend.get(
                "strength",
                "WEAK"
            )
        ).upper()

        if strength == "MEDIUM":

            strength = "MODERATE"

        elif strength not in (
            "STRONG",
            "MODERATE",
            "WEAK"
        ):

            strength = "WEAK"

        # ==================================================
        # Structure Counters
        # ==================================================

        hh = int(
            structure_trend.get(
                "hh",
                0
            )
        )

        hl = int(
            structure_trend.get(
                "hl",
                0
            )
        )

        lh = int(
            structure_trend.get(
                "lh",
                0
            )
        )

        ll = int(
            structure_trend.get(
                "ll",
                0
            )
        )

        # ==================================================
        # Informational Score
        # ==================================================

        bullish, bearish = (
            self._calculate_score(
                trend,
                strength
            )
        )

        if trend == "BUY":

            score = bullish

        elif trend == "SELL":

            score = -bearish

        else:

            score = 0

        # ==================================================
        # Recent Structures
        # ==================================================

        recent_structures = (
            structure_trend.get(
                "recent_structures",
                []
            )
        )

        if not isinstance(
            recent_structures,
            list
        ):

            recent_structures = []

        # ==================================================
        # Latest Structure
        # ==================================================

        latest_structure = str(
            structure_trend.get(
                "latest_structure",
                ""
            )
        )

        latest_high_label = str(
            structure_trend.get(
                "latest_high_label",
                ""
            )
        )

        latest_low_label = str(
            structure_trend.get(
                "latest_low_label",
                ""
            )
        )

        # ==================================================
        # Store Structure Information
        # ==================================================

        result["trend"] = trend

        result["strength"] = strength

        result["score"] = score

        result["bullish"] = bullish

        result["bearish"] = bearish

        result["latest_structure"] = (
            latest_structure
        )

        result["latest_high_label"] = (
            latest_high_label
        )

        result["latest_low_label"] = (
            latest_low_label
        )

        result["recent_structures"] = (
            recent_structures
        )

        result["structure_lookback"] = (
            structure_trend.get(
                "trend_structure_lookback",
                self.lookback
            )
        )

        # ==================================================
        # Optional CHoCH
        # ==================================================

        choch_info = (
            self._extract_choch(
                choch_result
            )
        )

        result["choch_confirmed"] = (
            choch_info["confirmed"]
        )

        result["choch_direction"] = (
            choch_info["direction"]
        )

        result["choch_strength"] = (
            choch_info["strength"]
        )

        # ==================================================
        # Status
        # ==================================================

        if trend == "BUY":

            result["status"] = (
                "BULLISH"
            )

            result["reason"] = (
                f"Recent Structure Trend "
                f"BULLISH | "
                f"Strength {strength}"
            )

        elif trend == "SELL":

            result["status"] = (
                "BEARISH"
            )

            result["reason"] = (
                f"Recent Structure Trend "
                f"BEARISH | "
                f"Strength {strength}"
            )

        elif str(
            raw_trend
        ).upper() == "SIDEWAYS":

            result["trend"] = "NONE"

            result["status"] = (
                "SIDEWAYS"
            )

            result["reason"] = (
                "Recent Structures are balanced"
            )

        else:

            result["trend"] = "NONE"

            result["status"] = (
                "SIDEWAYS"
            )

            result["reason"] = (
                "Insufficient directional structure"
            )

        # ==================================================
        # Add CHoCH Context To Reason
        # ==================================================

        if choch_info["confirmed"]:

            result["reason"] += (
                " | Confirmed CHoCH: "
                f"{choch_info['direction']}"
            )

        # ==================================================
        # Debug
        # ==================================================

        print(
            "\n========== TREND FILTER V20.5 =========="
        )

        print(
            "Trend       :",
            result["trend"]
        )

        print(
            "Status      :",
            result["status"]
        )

        print(
            "Strength    :",
            result["strength"]
        )

        print(
            "Score       :",
            result["score"]
        )

        print(
            "Bullish     :",
            result["bullish"]
        )

        print(
            "Bearish     :",
            result["bearish"]
        )

        print(
            "HH          :",
            hh
        )

        print(
            "HL          :",
            hl
        )

        print(
            "LH          :",
            lh
        )

        print(
            "LL          :",
            ll
        )

        print(
            "Latest High :",
            latest_high_label
        )

        print(
            "Latest Low  :",
            latest_low_label
        )

        print(
            "Latest Structure :",
            latest_structure
        )

        print(
            "Recent Structures :",
            len(recent_structures)
        )

        print(
            "CHoCH Confirmed :",
            result["choch_confirmed"]
        )

        print(
            "CHoCH Direction :",
            result["choch_direction"]
        )

        print(
            "Reason      :",
            result["reason"]
        )

        print(
            "==========================================\n"
        )

        return result

    # ======================================================
    # Get Current Trend
    # ======================================================

    def get_trend(self):

        try:

            structure_trend = (
                self.structure.get_trend()
            )

        except Exception:

            return {

                "trend": "NONE",

                "status": "SIDEWAYS",

                "strength": "WEAK"

            }

        trend = self._normalize_trend(
            structure_trend.get(
                "trend",
                "NONE"
            )
        )

        strength = str(
            structure_trend.get(
                "strength",
                "WEAK"
            )
        ).upper()

        if strength == "MEDIUM":

            strength = "MODERATE"

        return {

            "trend":
                trend,

            "status":
                (
                    "BULLISH"
                    if trend == "BUY"
                    else
                    "BEARISH"
                    if trend == "SELL"
                    else
                    "SIDEWAYS"
                ),

            "strength":
                strength,

            "latest_structure":
                structure_trend.get(
                    "latest_structure",
                    ""
                ),

            "recent_structures":
                structure_trend.get(
                    "recent_structures",
                    []
                )

        }

    # ======================================================
    # Engine Information
    # ======================================================

    @staticmethod
    def version():

        return {

            "engine":
                "Trend Filter",

            "version":
                "V20.5",

            "status":
                "Production",

            "primary_engine":
                "MarketStructure V20.3",

            "logic":
                "Recent confirmed structure weighted trend",

            "developer":
                "Liquidity Hunter AI"

        }

    # ======================================================
    # Self Test
    # ======================================================

    def self_test(self):

        print(
            "\n========== "
            "TREND FILTER TEST "
            "=========="
        )

        info = self.version()

        print(
            "Engine :",
            info["engine"]
        )

        print(
            "Version:",
            info["version"]
        )

        print(
            "Status :",
            info["status"]
        )

        print(
            "Primary:",
            info["primary_engine"]
        )

        print(
            "Logic  :",
            info["logic"]
        )

        print(
            "====================================\n"
        )

        return True