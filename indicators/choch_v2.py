from __future__ import annotations

from typing import Any, Dict, Optional


# ==========================================================
# Liquidity Hunter AI
# CHoCH V2.5
#
# V20.2 Compatible Smart Money Reversal Engine
#
# ACTIVE LIQUIDITY + PROTECTED STRUCTURE VALIDATION
#
# Pipeline:
#
# Liquidity Sweep
#       ↓
# ACTIVE until NEWER sweep
#       ↓
# Protected HL / LH
#       ↓
# Protected Structure Validation
#       ↓
# Protected Level Integrity
#       ↓
# Opposite Body Close
#       ↓
# Directional Displacement
#       ↓
# CHoCH Confirmation
#
# IMPORTANT:
#
# Liquidity does NOT expire by candle age.
#
# Example:
#
# Sweep at candle 89
# Current candle 100
# Age = 11
#
# Still ACTIVE if no newer sweep exists.
#
# When candle 105 creates a new sweep:
#
# Old Sweep → INACTIVE
# New Sweep → ACTIVE
#
# V2.5 PROTECTED STRUCTURE:
#
# BUY:
#
#   LH
#    ↓
#   LL
#    ↓
#   Bearish Sweep
#    ↓
#   Protected LH remains intact
#    ↓
#   Close above Protected LH
#    ↓
#   Bullish CHoCH
#
# SELL:
#
#   HL
#    ↓
#   HH
#    ↓
#   Bullish Sweep
#    ↓
#   Protected HL remains intact
#    ↓
#   Close below Protected HL
#    ↓
#   Bearish CHoCH
#
# Compatibility:
# - MarketStructure V20.2
# - LiquiditySweepV2.2
# - ConfluenceEngine
# - SignalEngine
# ==========================================================


class CHoCHV2:

    def __init__(self):

        print("CHoCH V2.5 Engine Initialized")

        # --------------------------------------------------
        # Scoring Weights
        # --------------------------------------------------

        self.body_break_score = 30
        self.displacement_score = 25
        self.liquidity_score = 25
        self.trend_confirmation_score = 20

        self.max_score = 100

        # --------------------------------------------------
        # Displacement Settings
        # --------------------------------------------------

        self.displacement_ratio = 0.60

    # ======================================================
    # Default Result
    # ======================================================

    def create_result(self):

        return {

            "choch": False,

            "status": "NONE",

            "direction": None,

            "strength": 0,

            "quality": "NONE",

            "trend_shift": False,

            "body_break": False,

            "displacement": False,

            "liquidity_confirmed": False,

            # --------------------------------------------------
            # V2.5 Protected Structure
            # --------------------------------------------------

            "protected_structure": False,

            "protected_structure_valid": False,

            "protected_level_integrity": False,

            "protected_label": None,

            "protected_index": None,

            "protected_level": None,

            "reversal_level": None,

            # --------------------------------------------------
            # Liquidity
            # --------------------------------------------------

            "liquidity_index": None,

            "liquidity_age": None,

            "liquidity_status": None,

            "liquidity_type": None,

            # --------------------------------------------------
            # CHoCH
            # --------------------------------------------------

            "choch_index": None,

            # --------------------------------------------------
            # Reasons
            # --------------------------------------------------

            "reasons": []

        }

    # ======================================================
    # Add Reason
    # ======================================================

    def add_reason(
        self,
        result: Dict[str, Any],
        reason: str
    ):

        if reason not in result["reasons"]:

            result["reasons"].append(reason)

    # ======================================================
    # Body Break
    # ======================================================

    def is_body_break(
        self,
        close_price: float,
        level: float,
        direction: str
    ) -> bool:

        if direction == "BUY":

            return close_price > level

        if direction == "SELL":

            return close_price < level

        return False

    # ======================================================
    # Displacement
    # ======================================================

    def is_displacement(
        self,
        candle,
        direction: Optional[str] = None
    ) -> bool:

        body = abs(
            float(candle["Close"]) -
            float(candle["Open"])
        )

        candle_range = (
            float(candle["High"]) -
            float(candle["Low"])
        )

        if candle_range <= 0:

            return False

        body_ratio = (
            body / candle_range
        )

        if body_ratio < self.displacement_ratio:

            return False

        # --------------------------------------------------
        # Directional validation
        # --------------------------------------------------

        if direction == "BUY":

            return (
                float(candle["Close"]) >
                float(candle["Open"])
            )

        if direction == "SELL":

            return (
                float(candle["Close"]) <
                float(candle["Open"])
            )

        return True

    # ======================================================
    # Quality
    # ======================================================

    def get_quality(
        self,
        score: int
    ) -> str:

        if score >= 90:

            return "A+"

        if score >= 80:

            return "A"

        if score >= 70:

            return "B"

        if score >= 60:

            return "C"

        return "D"

    # ======================================================
    # Get Latest ACTIVE Liquidity
    #
    # IMPORTANT:
    #
    # There is NO candle-age expiration.
    #
    # The latest sweep remains ACTIVE until a newer
    # liquidity sweep appears.
    # ======================================================

    def _get_latest_liquidity(
        self,
        liquidity_sweeps
    ):

        if not isinstance(
            liquidity_sweeps,
            list
        ):

            return None

        if not liquidity_sweeps:

            return None

        # --------------------------------------------------
        # Keep only valid liquidity events
        # --------------------------------------------------

        valid = [

            item

            for item in liquidity_sweeps

            if isinstance(item, dict)

            and "index" in item

            and "type" in item

        ]

        if not valid:

            return None

        # --------------------------------------------------
        # Latest chronological sweep is ACTIVE
        # --------------------------------------------------

        return max(
            valid,
            key=lambda item: int(
                item["index"]
            )
        )

    # ======================================================
    # Load Market Structure Engine
    # ======================================================

    def _load_structure_engine(
        self,
        df,
        market_structure
    ):

        # --------------------------------------------------
        # If actual MarketStructure object is supplied,
        # use it directly.
        # --------------------------------------------------

        if hasattr(
            market_structure,
            "get_swing_highs"
        ) and hasattr(
            market_structure,
            "get_swing_lows"
        ):

            return market_structure

        # --------------------------------------------------
        # Otherwise rebuild V20.2 structure internally.
        # --------------------------------------------------

        try:

            from indicators.market_structure import (
                MarketStructure
            )

            ms = MarketStructure()

            ms.detect(df)

            return ms

        except Exception as error:

            print(
                "CHoCH V2.5: "
                f"Market Structure Load Error: {error}"
            )

            return None

    # ======================================================
    # Find Protected Bullish Structure
    #
    # BUY reversal:
    #
    # Bearish Sweep
    #       ↓
    # Latest LH before sweep
    #       ↓
    # Protected LH
    #
    # The LH is only a CANDIDATE here.
    #
    # V2.5 validation happens separately.
    # ======================================================

    def _find_protected_lh(
        self,
        market_structure_engine,
        before_index: int
    ):

        if market_structure_engine is None:

            return None

        try:

            swing_highs = (
                market_structure_engine
                .get_swing_highs()
            )

        except Exception:

            return None

        candidates = [

            swing

            for swing in swing_highs

            if getattr(
                swing,
                "label",
                ""
            ) == "LH"

            and getattr(
                swing,
                "index",
                -1
            ) < before_index

        ]

        if not candidates:

            return None

        return max(
            candidates,
            key=lambda swing: swing.index
        )

    # ======================================================
    # Find Protected Bearish Structure
    #
    # SELL reversal:
    #
    # Bullish Sweep
    #       ↓
    # Latest HL before sweep
    #       ↓
    # Protected HL
    #
    # The HL is only a CANDIDATE here.
    #
    # V2.5 validation happens separately.
    # ======================================================

    def _find_protected_hl(
        self,
        market_structure_engine,
        before_index: int
    ):

        if market_structure_engine is None:

            return None

        try:

            swing_lows = (
                market_structure_engine
                .get_swing_lows()
            )

        except Exception:

            return None

        candidates = [

            swing

            for swing in swing_lows

            if getattr(
                swing,
                "label",
                ""
            ) == "HL"

            and getattr(
                swing,
                "index",
                -1
            ) < before_index

        ]

        if not candidates:

            return None

        return max(
            candidates,
            key=lambda swing: swing.index
        )

    # ======================================================
    # CHoCH V2.5
    #
    # Validate Protected LH
    #
    # BUY CHoCH:
    #
    #   LH
    #    ↓
    #   LL
    #    ↓
    #   Bearish Sweep
    #
    # The candidate LH must:
    #
    # 1. Actually be labelled LH
    # 2. Exist before liquidity sweep
    # 3. Have bearish continuation through an LL
    #    before the sweep
    #
    # Candle-level integrity is validated separately.
    # ======================================================

    def _validate_protected_lh(
        self,
        market_structure_engine,
        protected_lh,
        liquidity_index: int
    ) -> bool:

        if market_structure_engine is None:

            return False

        if protected_lh is None:

            return False

        try:

            protected_index = int(
                protected_lh.index
            )

            protected_label = str(
                protected_lh.label
            )

        except Exception:

            return False

        # --------------------------------------------------
        # Candidate must actually be LH
        # --------------------------------------------------

        if protected_label != "LH":

            return False

        # --------------------------------------------------
        # LH must exist before active sweep
        # --------------------------------------------------

        if protected_index >= liquidity_index:

            return False

        # --------------------------------------------------
        # Get swing lows
        # --------------------------------------------------

        try:

            swing_lows = (
                market_structure_engine
                .get_swing_lows()
            )

        except Exception:

            return False

        # ==================================================
        # Bearish continuation validation
        #
        # There must be at least one LL between the
        # protected LH and the liquidity sweep.
        # ==================================================

        continuation_ll = [

            swing

            for swing in swing_lows

            if getattr(
                swing,
                "label",
                ""
            ) == "LL"

            and getattr(
                swing,
                "index",
                -1
            ) > protected_index

            and getattr(
                swing,
                "index",
                -1
            ) < liquidity_index

        ]

        if not continuation_ll:

            return False

        return True

    # ======================================================
    # CHoCH V2.5
    #
    # Validate Protected HL
    #
    # SELL CHoCH:
    #
    #   HL
    #    ↓
    #   HH
    #    ↓
    #   Bullish Sweep
    #
    # The candidate HL must:
    #
    # 1. Actually be labelled HL
    # 2. Exist before liquidity sweep
    # 3. Have bullish continuation through an HH
    #    before the sweep
    #
    # Candle-level integrity is validated separately.
    # ======================================================

    def _validate_protected_hl(
        self,
        market_structure_engine,
        protected_hl,
        liquidity_index: int
    ) -> bool:

        if market_structure_engine is None:

            return False

        if protected_hl is None:

            return False

        try:

            protected_index = int(
                protected_hl.index
            )

            protected_label = str(
                protected_hl.label
            )

        except Exception:

            return False

        # --------------------------------------------------
        # Candidate must actually be HL
        # --------------------------------------------------

        if protected_label != "HL":

            return False

        # --------------------------------------------------
        # HL must exist before active sweep
        # --------------------------------------------------

        if protected_index >= liquidity_index:

            return False

        # --------------------------------------------------
        # Get swing highs
        # --------------------------------------------------

        try:

            swing_highs = (
                market_structure_engine
                .get_swing_highs()
            )

        except Exception:

            return False

        # ==================================================
        # Bullish continuation validation
        #
        # There must be at least one HH between the
        # protected HL and the liquidity sweep.
        # ==================================================

        continuation_hh = [

            swing

            for swing in swing_highs

            if getattr(
                swing,
                "label",
                ""
            ) == "HH"

            and getattr(
                swing,
                "index",
                -1
            ) > protected_index

            and getattr(
                swing,
                "index",
                -1
            ) < liquidity_index

        ]

        if not continuation_hh:

            return False

        return True

    # ======================================================
    # CHoCH V2.5
    #
    # Protected Level Integrity
    #
    # BUY:
    #
    # Protected LH
    #       ↓
    # No body close ABOVE LH
    #       ↓
    # Bearish Sweep
    #
    # SELL:
    #
    # Protected HL
    #       ↓
    # No body close BELOW HL
    #       ↓
    # Bullish Sweep
    #
    # IMPORTANT:
    #
    # The sweep candle itself is included.
    #
    # This makes sure that the protected level was still
    # intact when the active liquidity event happened.
    # ======================================================

    def _validate_protected_level_integrity(
        self,
        df,
        protected_level: float,
        protected_index: int,
        liquidity_index: int,
        direction: str
    ) -> bool:

        if df is None:

            return False

        if protected_level is None:

            return False

        if protected_index < 0:

            return False

        if liquidity_index <= protected_index:

            return False

        if liquidity_index >= len(df):

            return False

        try:

            closes = df["Close"].values

        except Exception:

            return False

        # ==================================================
        # BUY
        #
        # Protected LH must not have been broken above
        # before or on the liquidity sweep.
        # ==================================================

        if direction == "BUY":

            for candle_index in range(
                protected_index + 1,
                liquidity_index + 1
            ):

                close_price = float(
                    closes[candle_index]
                )

                if close_price > protected_level:

                    return False

            return True

        # ==================================================
        # SELL
        #
        # Protected HL must not have been broken below
        # before or on the liquidity sweep.
        # ==================================================

        if direction == "SELL":

            for candle_index in range(
                protected_index + 1,
                liquidity_index + 1
            ):

                close_price = float(
                    closes[candle_index]
                )

                if close_price < protected_level:

                    return False

            return True

        return False

    # ======================================================
    # Validate Complete Protected Structure
    #
    # V2.5 combines:
    #
    # 1. Structure validation
    # 2. Level integrity validation
    #
    # Returns:
    #
    # {
    #     "valid": bool,
    #     "structure_valid": bool,
    #     "integrity_valid": bool
    # }
    # ======================================================

    def _validate_protected_structure(
        self,
        df,
        market_structure_engine,
        protected,
        liquidity_index: int,
        direction: str
    ) -> Dict[str, bool]:

        result = {

            "valid": False,

            "structure_valid": False,

            "integrity_valid": False

        }

        if protected is None:

            return result

        protected_index = getattr(
            protected,
            "index",
            -1
        )

        protected_level = getattr(
            protected,
            "price",
            None
        )

        if protected_index is None:

            return result

        if protected_level is None:

            return result

        try:

            protected_index = int(
                protected_index
            )

            protected_level = float(
                protected_level
            )

        except Exception:

            return result

        # ==================================================
        # Structural validation
        # ==================================================

        if direction == "BUY":

            result["structure_valid"] = (
                self._validate_protected_lh(
                    market_structure_engine,
                    protected,
                    liquidity_index
                )
            )

        elif direction == "SELL":

            result["structure_valid"] = (
                self._validate_protected_hl(
                    market_structure_engine,
                    protected,
                    liquidity_index
                )
            )

        else:

            return result

        if not result["structure_valid"]:

            return result

        # ==================================================
        # Candle integrity validation
        # ==================================================

        result["integrity_valid"] = (
            self._validate_protected_level_integrity(
                df,
                protected_level,
                protected_index,
                liquidity_index,
                direction
            )
        )

        if not result["integrity_valid"]:

            return result

        # ==================================================
        # Final protected structure validation
        # ==================================================

        result["valid"] = True

        return result

    # ======================================================
    # Validate Liquidity Direction
    #
    # Bearish Sweep → Bullish CHoCH
    #
    # Bullish Sweep → Bearish CHoCH
    # ======================================================

    def _liquidity_matches_direction(
        self,
        liquidity,
        direction
    ) -> bool:

        if liquidity is None:

            return False

        liquidity_type = str(
            liquidity.get(
                "type",
                ""
            )
        )

        if direction == "BUY":

            return (
                liquidity_type ==
                "Bearish Sweep"
            )

        if direction == "SELL":

            return (
                liquidity_type ==
                "Bullish Sweep"
            )

        return False

    # ======================================================
    # Internal Evaluation
    # ======================================================

    def _evaluate(
        self,
        df,
        market_structure,
        liquidity_sweeps
    ):

        result = self.create_result()

        # --------------------------------------------------
        # Basic Validation
        # --------------------------------------------------

        if df is None:

            self.add_reason(
                result,
                "Market Data Missing"
            )

            return result

        if len(df) < 10:

            self.add_reason(
                result,
                "Not Enough Candles"
            )

            return result

        # ==================================================
        # ACTIVE LIQUIDITY
        # ==================================================

        latest_liquidity = (
            self._get_latest_liquidity(
                liquidity_sweeps
            )
        )

        if latest_liquidity is None:

            self.add_reason(
                result,
                "No Liquidity Sweep Found"
            )

            return result

        liquidity_index = int(
            latest_liquidity["index"]
        )

        liquidity_type = str(
            latest_liquidity["type"]
        )

        latest_index = len(df) - 1

        liquidity_age = (
            latest_index -
            liquidity_index
        )

        result["liquidity_index"] = (
            liquidity_index
        )

        result["liquidity_age"] = (
            liquidity_age
        )

        result["liquidity_status"] = (
            "ACTIVE"
        )

        result["liquidity_type"] = (
            liquidity_type
        )

        # --------------------------------------------------
        # IMPORTANT:
        #
        # DO NOT reject old liquidity.
        #
        # Liquidity remains ACTIVE until a newer sweep
        # replaces it.
        # --------------------------------------------------

        self.add_reason(
            result,
            "Active Liquidity"
        )

        self.add_reason(
            result,
            "Active Until Newer Sweep"
        )

        # ==================================================
        # Load V20.2 Market Structure
        # ==================================================

        ms_engine = (
            self._load_structure_engine(
                df,
                market_structure
            )
        )

        if ms_engine is None:

            self.add_reason(
                result,
                "Market Structure Missing"
            )

            return result

        # ==================================================
        # Determine Sweep → Reversal Direction
        #
        # Bearish Sweep = potential BUY reversal
        # Bullish Sweep = potential SELL reversal
        # ==================================================

        if liquidity_type == "Bearish Sweep":

            direction = "BUY"

        elif liquidity_type == "Bullish Sweep":

            direction = "SELL"

        else:

            self.add_reason(
                result,
                "Unknown Liquidity Type"
            )

            return result

        result["direction"] = direction

        # ==================================================
        # Find Protected Structure Candidate
        # ==================================================

        protected_level = None
        protected_index = None
        protected_label = None

        protected = None

        if direction == "BUY":

            protected = (
                self._find_protected_lh(
                    ms_engine,
                    liquidity_index
                )
            )

            if protected is not None:

                protected_level = float(
                    protected.price
                )

                protected_index = int(
                    protected.index
                )

                protected_label = "LH"

        elif direction == "SELL":

            protected = (
                self._find_protected_hl(
                    ms_engine,
                    liquidity_index
                )
            )

            if protected is not None:

                protected_level = float(
                    protected.price
                )

                protected_index = int(
                    protected.index
                )

                protected_label = "HL"

        # --------------------------------------------------
        # Protected Structure Candidate Missing
        # --------------------------------------------------

        if protected_level is None:

            self.add_reason(
                result,
                "Protected Structure Not Found"
            )

            return result

        result["reversal_level"] = (
            protected_level
        )

        result["protected_level"] = (
            protected_level
        )

        result["protected_index"] = (
            protected_index
        )

        result["protected_label"] = (
            protected_label
        )

        result["protected_structure"] = True

        self.add_reason(
            result,
            f"Protected {protected_label} Candidate Found"
        )

        # ==================================================
        # CHoCH V2.5
        #
        # Validate Protected Structure
        # ==================================================

        protected_validation = (
            self._validate_protected_structure(
                df,
                ms_engine,
                protected,
                liquidity_index,
                direction
            )
        )

        # --------------------------------------------------
        # Structural validation
        # --------------------------------------------------

        if protected_validation[
            "structure_valid"
        ]:

            self.add_reason(
                result,
                "Protected Structure Validated"
            )

        else:

            self.add_reason(
                result,
                "Protected Structure Validation Failed"
            )

            return result

        # --------------------------------------------------
        # Level integrity
        # --------------------------------------------------

        if protected_validation[
            "integrity_valid"
        ]:

            result[
                "protected_level_integrity"
            ] = True

            self.add_reason(
                result,
                "Protected Level Integrity Confirmed"
            )

        else:

            self.add_reason(
                result,
                "Protected Level Already Broken"
            )

            return result

        # --------------------------------------------------
        # Complete protected structure
        # --------------------------------------------------

        result[
            "protected_structure_valid"
        ] = True

        # ==================================================
        # Search For Opposite Body Close
        #
        # IMPORTANT V2.5:
        #
        # Search continues until CURRENT candle.
        #
        # There is NO 5-candle CHoCH expiration.
        #
        # Liquidity remains active until a newer sweep.
        # ==================================================

        closes = df["Close"].values

        choch_index = None

        search_start = (
            liquidity_index + 1
        )

        if search_start > latest_index:

            self.add_reason(
                result,
                "Waiting For Post-Sweep Candle"
            )

            return result

        for candle_index in range(
            search_start,
            latest_index + 1
        ):

            close_price = float(
                closes[candle_index]
            )

            if self.is_body_break(
                close_price,
                protected_level,
                direction
            ):

                choch_index = candle_index

                break

        # --------------------------------------------------
        # No Body Break
        # --------------------------------------------------

        if choch_index is None:

            self.add_reason(
                result,
                "Protected Structure Not Broken"
            )

            return result

        result["choch_index"] = (
            choch_index
        )

        # ==================================================
        # Body Break Confirmation
        # ==================================================

        result["body_break"] = True

        result["trend_shift"] = True

        self.add_reason(
            result,
            "Protected Structure Body Break"
        )

        self.add_reason(
            result,
            f"{protected_label} Broken"
        )

        # ==================================================
        # Liquidity Direction Confirmation
        # ==================================================

        if self._liquidity_matches_direction(
            latest_liquidity,
            direction
        ):

            result["liquidity_confirmed"] = True

            self.add_reason(
                result,
                f"{liquidity_type} Confirmed"
            )

        else:

            self.add_reason(
                result,
                "Liquidity Direction Conflict"
            )

            return result

        # ==================================================
        # Displacement Confirmation
        # ==================================================

        choch_candle = df.iloc[
            choch_index
        ]

        if self.is_displacement(
            choch_candle,
            direction
        ):

            result["displacement"] = True

            self.add_reason(
                result,
                "Directional Displacement Confirmed"
            )

        else:

            self.add_reason(
                result,
                "Weak Displacement"
            )

        # ==================================================
        # Score
        # ==================================================

        score = 0

        # --------------------------------------------------
        # Body Break
        # --------------------------------------------------

        if result["body_break"]:

            score += (
                self.body_break_score
            )

        # --------------------------------------------------
        # Displacement
        # --------------------------------------------------

        if result["displacement"]:

            score += (
                self.displacement_score
            )

        # --------------------------------------------------
        # Liquidity
        # --------------------------------------------------

        if result["liquidity_confirmed"]:

            score += (
                self.liquidity_score
            )

        # --------------------------------------------------
        # Trend Shift
        # --------------------------------------------------

        if result["trend_shift"]:

            score += (
                self.trend_confirmation_score
            )

        # --------------------------------------------------
        # Clamp
        # --------------------------------------------------

        score = max(
            0,
            min(
                self.max_score,
                score
            )
        )

        result["strength"] = score

        result["quality"] = (
            self.get_quality(score)
        )

        # ==================================================
        # Final CHoCH Status
        # ==================================================

        if score >= 80:

            result["choch"] = True

            result["status"] = "CONFIRMED"

            self.add_reason(
                result,
                "Confirmed CHoCH"
            )

        elif score >= 60:

            result["choch"] = False

            result["status"] = "WAIT"

            self.add_reason(
                result,
                "CHoCH Awaiting Confirmation"
            )

        else:

            result["choch"] = False

            result["status"] = "NONE"

            self.add_reason(
                result,
                "CHoCH Below Threshold"
            )

        return result

    # ======================================================
    # Main Detection
    # ======================================================

    def detect(
        self,
        df,
        market_structure=None,
        liquidity_sweeps=None
    ):

        print(
            "Checking CHoCH V2.5..."
        )

        result = self.create_result()

        # --------------------------------------------------
        # Validate Data
        # --------------------------------------------------

        if df is None:

            self.add_reason(
                result,
                "Market Data Missing"
            )

            return result

        if len(df) < 10:

            self.add_reason(
                result,
                "Not Enough Candles"
            )

            return result

        # --------------------------------------------------
        # Auto-load Market Structure
        # --------------------------------------------------

        if market_structure is None:

            try:

                from indicators.market_structure import (
                    MarketStructure
                )

                ms = MarketStructure()

                ms.detect(df)

                market_structure = ms

            except Exception as error:

                print(
                    "CHoCH V2.5: "
                    f"Market Structure Error: {error}"
                )

                market_structure = None

        # --------------------------------------------------
        # Auto-load Liquidity
        # --------------------------------------------------

        if liquidity_sweeps is None:

            try:

                from indicators.liquidity_sweep_v2 import (
                    LiquiditySweepV2
                )

                ls = LiquiditySweepV2()

                liquidity_sweeps = ls.detect(
                    df
                )

            except Exception as error:

                print(
                    "CHoCH V2.5: "
                    f"Liquidity Error: {error}"
                )

                liquidity_sweeps = []

        # --------------------------------------------------
        # Evaluate
        # --------------------------------------------------

        result = self._evaluate(
            df,
            market_structure,
            liquidity_sweeps
        )

        # ==================================================
        # Debug Output
        # ==================================================

        print(
            "\n========== CHoCH V2.5 =========="
        )

        print(
            "Direction :",
            result["direction"]
        )

        print(
            "Status    :",
            result["status"]
        )

        print(
            "Strength  :",
            result["strength"]
        )

        print(
            "Quality   :",
            result["quality"]
        )

        print(
            "Liquidity :",
            result["liquidity_index"]
        )

        print(
            "Liquidity Type :",
            result["liquidity_type"]
        )

        print(
            "Age       :",
            result["liquidity_age"]
        )

        print(
            "Liquidity Status :",
            result["liquidity_status"]
        )

        print(
            "Protected Structure :",
            result["protected_structure"]
        )

        print(
            "Protected Valid :",
            result["protected_structure_valid"]
        )

        print(
            "Protected Label :",
            result["protected_label"]
        )

        print(
            "Protected Index :",
            result["protected_index"]
        )

        print(
            "Protected Level :",
            result["protected_level"]
        )

        print(
            "Level Integrity :",
            result["protected_level_integrity"]
        )

        print(
            "CHoCH     :",
            result["choch_index"]
        )

        print(
            "Level     :",
            result["reversal_level"]
        )

        print(
            "Reasons   :",
            result["reasons"]
        )

        print(
            "================================\n"
        )

        return result

    # ======================================================
    # Compatibility Output
    #
    # ConfluenceEngine expects:
    #
    # [
    #   {
    #       "type": "Bullish CHoCH",
    #       "price": ...,
    #       "index": ...,
    #       "time": ...
    #   }
    # ]
    # ======================================================

    def detect_for_confluence(
        self,
        df,
        choch_result=None,
        market_structure=None,
        liquidity_sweeps=None
    ):

        if choch_result is None:

            choch_result = self.detect(
                df,
                market_structure,
                liquidity_sweeps
            )

        if not choch_result:

            return []

        if not choch_result.get(
            "choch",
            False
        ):

            return []

        direction = (
            choch_result.get(
                "direction"
            )
        )

        choch_index = (
            choch_result.get(
                "choch_index"
            )
        )

        reversal_level = (
            choch_result.get(
                "reversal_level"
            )
        )

        # --------------------------------------------------
        # Safety fallback
        # --------------------------------------------------

        if choch_index is None:

            choch_index = len(df) - 1

        # --------------------------------------------------
        # Direction
        # --------------------------------------------------

        if direction == "BUY":

            event_type = "Bullish CHoCH"

        elif direction == "SELL":

            event_type = "Bearish CHoCH"

        else:

            return []

        # --------------------------------------------------
        # Candle information
        # --------------------------------------------------

        candle = df.iloc[
            choch_index
        ]

        return [

            {

                "type": event_type,

                "price": float(
                    candle["Close"]
                ),

                "index": int(
                    choch_index
                ),

                "time": candle.name,

                "level": (
                    float(reversal_level)
                    if reversal_level is not None
                    else None
                ),

                "strength": int(
                    choch_result.get(
                        "strength",
                        0
                    )
                )

            }

        ]

    # ======================================================
    # Engine Information
    # ======================================================

    @staticmethod
    def version():

        return {

            "engine":
                "CHoCH V2",

            "version":
                "V2.5",

            "status":
                "Development",

            "developer":
                "Liquidity Hunter AI"

        }

    # ======================================================
    # Self Test
    # ======================================================

    def self_test(self):

        print(
            "\n========== CHoCH ENGINE TEST =========="
        )

        info = self.version()

        print(
            "Engine  :",
            info["engine"]
        )

        print(
            "Version :",
            info["version"]
        )

        print(
            "Status  :",
            info["status"]
        )

        print(
            "========================================\n"
        )

        return True