from __future__ import annotations

from typing import Any, Dict, Optional


# ==========================================================
# Liquidity Hunter AI
# CHoCH V2.5
#
# Production Protected-Structure Reversal Engine
#
# Pipeline
# ----------------------------------------------------------
#
# Active Liquidity
#       ↓
# Protected LH / HL
#       ↓
# Structure Validation
#       ↓
# Protected Level Integrity
#       ↓
# Opposite Body Close
#       ↓
# Directional Displacement
#       ↓
# CHoCH Confirmation
#
# Important
# ----------------------------------------------------------
#
# Liquidity does NOT expire by candle age.
#
# Latest sweep remains ACTIVE until a newer sweep appears.
#
# BUY:
#
#   LH
#    ↓
#   LL
#    ↓
#   Bearish Sweep
#    ↓
#   Protected LH
#    ↓
#   Body Close Above LH
#    ↓
#   Bullish Displacement
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
#   Protected HL
#    ↓
#   Body Close Below HL
#    ↓
#   Bearish Displacement
#    ↓
#   Bearish CHoCH
#
# Compatibility
# ----------------------------------------------------------
#
# MarketStructure V20.3
# LiquiditySweepV2
# ConfluenceEngine
# SignalEngine
# ==========================================================


class CHoCHV2:

    # ======================================================
    # INITIALIZATION
    # ======================================================

    def __init__(self):

        print(
            "CHoCH V2.5 Engine Initialized"
        )

        # --------------------------------------------------
        # Scoring
        # --------------------------------------------------

        self.body_break_score = 30

        self.displacement_score = 25

        self.liquidity_score = 25

        self.trend_confirmation_score = 20

        self.max_score = 100

        # --------------------------------------------------
        # Displacement
        # --------------------------------------------------

        self.displacement_ratio = 0.60

        # --------------------------------------------------
        # Confirmation Threshold
        # --------------------------------------------------

        self.confirmation_threshold = 80

        self.wait_threshold = 60

    # ======================================================
    # DEFAULT RESULT
    # ======================================================

    def create_result(self):

        return {

            # ------------------------------------------------
            # Final
            # ------------------------------------------------

            "choch": False,

            "status": "NONE",

            "direction": None,

            "strength": 0,

            "quality": "NONE",

            "trend_shift": False,

            # ------------------------------------------------
            # Confirmation Components
            # ------------------------------------------------

            "body_break": False,

            "displacement": False,

            "liquidity_confirmed": False,

            # ------------------------------------------------
            # Protected Structure
            # ------------------------------------------------

            "protected_structure": False,

            "protected_structure_valid": False,

            "protected_level_integrity": False,

            "protected_label": None,

            "protected_index": None,

            "protected_level": None,

            "reversal_level": None,

            # ------------------------------------------------
            # Liquidity
            # ------------------------------------------------

            "liquidity_index": None,

            "liquidity_age": None,

            "liquidity_status": None,

            "liquidity_type": None,

            # ------------------------------------------------
            # CHoCH
            # ------------------------------------------------

            "choch_index": None,

            # ------------------------------------------------
            # Reasons
            # ------------------------------------------------

            "reasons": []

        }

    # ======================================================
    # ADD REASON
    # ======================================================

    def add_reason(
        self,
        result: Dict[str, Any],
        reason: str
    ):

        if reason not in result["reasons"]:

            result["reasons"].append(
                reason
            )

    # ======================================================
    # BODY BREAK
    # ======================================================

    def is_body_break(
        self,
        close_price: float,
        level: float,
        direction: str
    ) -> bool:

        try:

            close_price = float(
                close_price
            )

            level = float(
                level
            )

        except (
            TypeError,
            ValueError
        ):

            return False

        if direction == "BUY":

            return close_price > level

        if direction == "SELL":

            return close_price < level

        return False

    # ======================================================
    # DISPLACEMENT
    # ======================================================

    def is_displacement(
        self,
        candle,
        direction: Optional[str] = None
    ) -> bool:

        try:

            open_price = float(
                candle["Open"]
            )

            high_price = float(
                candle["High"]
            )

            low_price = float(
                candle["Low"]
            )

            close_price = float(
                candle["Close"]
            )

        except (
            KeyError,
            TypeError,
            ValueError
        ):

            return False

        candle_range = (
            high_price -
            low_price
        )

        if candle_range <= 0:

            return False

        body = abs(
            close_price -
            open_price
        )

        body_ratio = (
            body /
            candle_range
        )

        if (
            body_ratio <
            self.displacement_ratio
        ):

            return False

        # --------------------------------------------------
        # Directional confirmation
        # --------------------------------------------------

        if direction == "BUY":

            return (
                close_price >
                open_price
            )

        if direction == "SELL":

            return (
                close_price <
                open_price
            )

        return True

    # ======================================================
    # QUALITY
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
    # GET LATEST ACTIVE LIQUIDITY
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

        valid = []

        for item in liquidity_sweeps:

            if not isinstance(
                item,
                dict
            ):

                continue

            if "index" not in item:

                continue

            if "type" not in item:

                continue

            try:

                int(
                    item["index"]
                )

            except (
                TypeError,
                ValueError
            ):

                continue

            valid.append(
                item
            )

        if not valid:

            return None

        return max(
            valid,
            key=lambda item:
                int(item["index"])
        )

    # ======================================================
    # LOAD MARKET STRUCTURE
    # ======================================================

    def _load_structure_engine(
        self,
        df,
        market_structure
    ):

        # --------------------------------------------------
        # Existing engine
        # --------------------------------------------------

        if (
            market_structure is not None
            and
            hasattr(
                market_structure,
                "get_swing_highs"
            )
            and
            hasattr(
                market_structure,
                "get_swing_lows"
            )
        ):

            return market_structure

        # --------------------------------------------------
        # Build automatically
        # --------------------------------------------------

        try:

            from indicators.market_structure import (
                MarketStructure
            )

            ms = MarketStructure()

            ms.detect(
                df
            )

            return ms

        except Exception as error:

            print(
                "CHoCH V2.5: "
                "Market Structure Load Error: "
                f"{error}"
            )

            return None

    # ======================================================
    # FIND PROTECTED LH
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

            and
            getattr(
                swing,
                "index",
                -1
            ) < before_index

        ]

        if not candidates:

            return None

        return max(
            candidates,
            key=lambda swing:
                swing.index
        )

    # ======================================================
    # FIND PROTECTED HL
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

            and
            getattr(
                swing,
                "index",
                -1
            ) < before_index

        ]

        if not candidates:

            return None

        return max(
            candidates,
            key=lambda swing:
                swing.index
        )

    # ======================================================
    # VALIDATE PROTECTED LH
    #
    # BUY:
    #
    # LH → LL → Bearish Sweep
    #
    # The protected LH must have bearish continuation
    # before the liquidity event.
    # ======================================================

    def _validate_protected_lh(
        self,
        market_structure_engine,
        protected_lh,
        liquidity_index: int
    ) -> bool:

        if (
            market_structure_engine is None
            or
            protected_lh is None
        ):

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

        if protected_label != "LH":

            return False

        if protected_index >= liquidity_index:

            return False

        try:

            swing_lows = (
                market_structure_engine
                .get_swing_lows()
            )

        except Exception:

            return False

        for swing in swing_lows:

            label = getattr(
                swing,
                "label",
                ""
            )

            index = getattr(
                swing,
                "index",
                -1
            )

            if (
                label == "LL"
                and
                protected_index <
                index <
                liquidity_index
            ):

                return True

        return False

    # ======================================================
    # VALIDATE PROTECTED HL
    #
    # SELL:
    #
    # HL → HH → Bullish Sweep
    #
    # The protected HL must have bullish continuation
    # before the liquidity event.
    # ======================================================

    def _validate_protected_hl(
        self,
        market_structure_engine,
        protected_hl,
        liquidity_index: int
    ) -> bool:

        if (
            market_structure_engine is None
            or
            protected_hl is None
        ):

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

        if protected_label != "HL":

            return False

        if protected_index >= liquidity_index:

            return False

        try:

            swing_highs = (
                market_structure_engine
                .get_swing_highs()
            )

        except Exception:

            return False

        for swing in swing_highs:

            label = getattr(
                swing,
                "label",
                ""
            )

            index = getattr(
                swing,
                "index",
                -1
            )

            if (
                label == "HH"
                and
                protected_index <
                index <
                liquidity_index
            ):

                return True

        return False

    # ======================================================
    # PROTECTED LEVEL INTEGRITY
    #
    # BUY:
    #
    # No body close above protected LH
    # before or during sweep.
    #
    # SELL:
    #
    # No body close below protected HL
    # before or during sweep.
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

            closes = (
                df["Close"].values
            )

        except Exception:

            return False

        # --------------------------------------------------
        # BUY
        # --------------------------------------------------

        if direction == "BUY":

            for index in range(
                protected_index + 1,
                liquidity_index + 1
            ):

                try:

                    close_price = float(
                        closes[index]
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    return False

                if (
                    close_price >
                    protected_level
                ):

                    return False

            return True

        # --------------------------------------------------
        # SELL
        # --------------------------------------------------

        if direction == "SELL":

            for index in range(
                protected_index + 1,
                liquidity_index + 1
            ):

                try:

                    close_price = float(
                        closes[index]
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    return False

                if (
                    close_price <
                    protected_level
                ):

                    return False

            return True

        return False

    # ======================================================
    # COMPLETE PROTECTED STRUCTURE VALIDATION
    # ======================================================

    def _validate_protected_structure(
        self,
        df,
        market_structure_engine,
        protected,
        liquidity_index: int,
        direction: str
    ) -> Dict[str, bool]:

        validation = {

            "valid": False,

            "structure_valid": False,

            "integrity_valid": False

        }

        if protected is None:

            return validation

        try:

            protected_index = int(
                protected.index
            )

            protected_level = float(
                protected.price
            )

        except (
            AttributeError,
            TypeError,
            ValueError
        ):

            return validation

        # --------------------------------------------------
        # Structural validation
        # --------------------------------------------------

        if direction == "BUY":

            validation[
                "structure_valid"
            ] = self._validate_protected_lh(

                market_structure_engine,

                protected,

                liquidity_index

            )

        elif direction == "SELL":

            validation[
                "structure_valid"
            ] = self._validate_protected_hl(

                market_structure_engine,

                protected,

                liquidity_index

            )

        else:

            return validation

        if not validation[
            "structure_valid"
        ]:

            return validation

        # --------------------------------------------------
        # Level integrity
        # --------------------------------------------------

        validation[
            "integrity_valid"
        ] = (
            self._validate_protected_level_integrity(

                df,

                protected_level,

                protected_index,

                liquidity_index,

                direction

            )
        )

        if not validation[
            "integrity_valid"
        ]:

            return validation

        validation[
            "valid"
        ] = True

        return validation

    # ======================================================
    # LIQUIDITY DIRECTION
    # ======================================================

    def _liquidity_matches_direction(
        self,
        liquidity,
        direction: str
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
    # SCORE
    # ======================================================

    def _calculate_score(
        self,
        result: Dict[str, Any]
    ) -> int:

        score = 0

        if result.get(
            "body_break",
            False
        ):

            score += (
                self.body_break_score
            )

        if result.get(
            "displacement",
            False
        ):

            score += (
                self.displacement_score
            )

        if result.get(
            "liquidity_confirmed",
            False
        ):

            score += (
                self.liquidity_score
            )

        if result.get(
            "trend_shift",
            False
        ):

            score += (
                self.trend_confirmation_score
            )

        return max(
            0,
            min(
                self.max_score,
                score
            )
        )

    # ======================================================
    # FIND CHoCH BODY BREAK
    #
    # Search starts AFTER liquidity sweep.
    #
    # No candle-age expiration.
    # ======================================================

    def _find_choch_body_break(
        self,
        df,
        liquidity_index: int,
        protected_level: float,
        direction: str
    ):

        latest_index = len(df) - 1

        start_index = (
            liquidity_index + 1
        )

        if start_index > latest_index:

            return None

        closes = df["Close"].values

        for candle_index in range(
            start_index,
            latest_index + 1
        ):

            try:

                close_price = float(
                    closes[candle_index]
                )

            except (
                TypeError,
                ValueError
            ):

                continue

            if self.is_body_break(
                close_price,
                protected_level,
                direction
            ):

                return candle_index

        return None

    # ======================================================
    # INTERNAL EVALUATION
    # ======================================================

    def _evaluate(
        self,
        df,
        market_structure,
        liquidity_sweeps
    ):

        result = self.create_result()

        # ==================================================
        # DATA VALIDATION
        # ==================================================

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

        try:

            liquidity_index = int(
                latest_liquidity["index"]
            )

        except (
            KeyError,
            TypeError,
            ValueError
        ):

            self.add_reason(
                result,
                "Invalid Liquidity Index"
            )

            return result

        liquidity_type = str(
            latest_liquidity.get(
                "type",
                ""
            )
        )

        latest_index = len(df) - 1

        # --------------------------------------------------
        # Sweep must exist inside dataset
        # --------------------------------------------------

        if (
            liquidity_index < 0
            or
            liquidity_index > latest_index
        ):

            self.add_reason(
                result,
                "Liquidity Index Outside Data"
            )

            return result

        liquidity_age = (
            latest_index -
            liquidity_index
        )

        result[
            "liquidity_index"
        ] = liquidity_index

        result[
            "liquidity_age"
        ] = liquidity_age

        result[
            "liquidity_status"
        ] = "ACTIVE"

        result[
            "liquidity_type"
        ] = liquidity_type

        self.add_reason(
            result,
            "Active Liquidity"
        )

        self.add_reason(
            result,
            "Active Until Newer Sweep"
        )

        # ==================================================
        # MARKET STRUCTURE
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
        # REVERSAL DIRECTION
        # ==================================================

        if (
            liquidity_type ==
            "Bearish Sweep"
        ):

            direction = "BUY"

        elif (
            liquidity_type ==
            "Bullish Sweep"
        ):

            direction = "SELL"

        else:

            self.add_reason(
                result,
                "Unknown Liquidity Type"
            )

            return result

        result[
            "direction"
        ] = direction

        # ==================================================
        # PROTECTED STRUCTURE
        # ==================================================

        protected = None

        if direction == "BUY":

            protected = (
                self._find_protected_lh(
                    ms_engine,
                    liquidity_index
                )
            )

        elif direction == "SELL":

            protected = (
                self._find_protected_hl(
                    ms_engine,
                    liquidity_index
                )
            )

        if protected is None:

            self.add_reason(
                result,
                "Protected Structure Not Found"
            )

            return result

        try:

            protected_level = float(
                protected.price
            )

            protected_index = int(
                protected.index
            )

            protected_label = str(
                protected.label
            )

        except (
            AttributeError,
            TypeError,
            ValueError
        ):

            self.add_reason(
                result,
                "Invalid Protected Structure"
            )

            return result

        result[
            "protected_structure"
        ] = True

        result[
            "protected_level"
        ] = protected_level

        result[
            "protected_index"
        ] = protected_index

        result[
            "protected_label"
        ] = protected_label

        result[
            "reversal_level"
        ] = protected_level

        self.add_reason(
            result,
            f"Protected {protected_label} Candidate Found"
        )

        # ==================================================
        # PROTECTED STRUCTURE VALIDATION
        # ==================================================

        validation = (
            self._validate_protected_structure(
                df,
                ms_engine,
                protected,
                liquidity_index,
                direction
            )
        )

        # --------------------------------------------------
        # Structure
        # --------------------------------------------------

        if validation[
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
        # Integrity
        # --------------------------------------------------

        if validation[
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

        result[
            "protected_structure_valid"
        ] = True

        # ==================================================
        # LIQUIDITY DIRECTION
        # ==================================================

        if self._liquidity_matches_direction(
            latest_liquidity,
            direction
        ):

            result[
                "liquidity_confirmed"
            ] = True

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
        # BODY-CLOSE CHoCH
        # ==================================================

        choch_index = (
            self._find_choch_body_break(
                df,
                liquidity_index,
                protected_level,
                direction
            )
        )

        if choch_index is None:

            self.add_reason(
                result,
                "Protected Structure Not Broken"
            )

            return result

        result[
            "choch_index"
        ] = choch_index

        result[
            "body_break"
        ] = True

        result[
            "trend_shift"
        ] = True

        self.add_reason(
            result,
            "Protected Structure Body Break"
        )

        self.add_reason(
            result,
            f"{protected_label} Broken"
        )

        # ==================================================
        # DISPLACEMENT
        # ==================================================

        try:

            choch_candle = df.iloc[
                choch_index
            ]

        except Exception:

            self.add_reason(
                result,
                "CHoCH Candle Missing"
            )

            return result

        if self.is_displacement(
            choch_candle,
            direction
        ):

            result[
                "displacement"
            ] = True

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
        # SCORE
        # ==================================================

        score = (
            self._calculate_score(
                result
            )
        )

        result[
            "strength"
        ] = score

        result[
            "quality"
        ] = self.get_quality(
            score
        )

        # ==================================================
        # FINAL STATUS
        # ==================================================

        if (
            score >=
            self.confirmation_threshold
        ):

            result[
                "choch"
            ] = True

            result[
                "status"
            ] = "CONFIRMED"

            self.add_reason(
                result,
                "Confirmed CHoCH"
            )

        elif (
            score >=
            self.wait_threshold
        ):

            result[
                "choch"
            ] = False

            result[
                "status"
            ] = "WAIT"

            self.add_reason(
                result,
                "CHoCH Awaiting Confirmation"
            )

        else:

            result[
                "choch"
            ] = False

            result[
                "status"
            ] = "NONE"

            self.add_reason(
                result,
                "CHoCH Below Threshold"
            )

        return result

    # ======================================================
    # MAIN DETECTION
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

        # ==================================================
        # DATA VALIDATION
        # ==================================================

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
        # AUTO MARKET STRUCTURE
        # ==================================================

        if market_structure is None:

            try:

                from indicators.market_structure import (
                    MarketStructure
                )

                ms = MarketStructure()

                ms.detect(
                    df
                )

                market_structure = ms

            except Exception as error:

                print(
                    "CHoCH V2.5: "
                    "Market Structure Error: "
                    f"{error}"
                )

                market_structure = None

        # ==================================================
        # AUTO LIQUIDITY
        # ==================================================

        if liquidity_sweeps is None:

            try:

                from indicators.liquidity_sweep_v2 import (
                    LiquiditySweepV2
                )

                ls = LiquiditySweepV2()

                liquidity_sweeps = (
                    ls.detect(df)
                )

            except Exception as error:

                print(
                    "CHoCH V2.5: "
                    "Liquidity Error: "
                    f"{error}"
                )

                liquidity_sweeps = []

        # ==================================================
        # EVALUATE
        # ==================================================

        result = self._evaluate(
            df,
            market_structure,
            liquidity_sweeps
        )

        # ==================================================
        # DEBUG
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
            "Liquidity Age :",
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
            "CHoCH Index :",
            result["choch_index"]
        )

        print(
            "Reversal Level :",
            result["reversal_level"]
        )

        print(
            "Reasons :",
            result["reasons"]
        )

        print(
            "================================\n"
        )

        return result

    # ======================================================
    # CONFLUENCE COMPATIBILITY
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

        if not isinstance(
            choch_result,
            dict
        ):

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

        if direction == "BUY":

            event_type = (
                "Bullish CHoCH"
            )

        elif direction == "SELL":

            event_type = (
                "Bearish CHoCH"
            )

        else:

            return []

        # --------------------------------------------------
        # Safety fallback
        # --------------------------------------------------

        if choch_index is None:

            choch_index = len(df) - 1

        if (
            choch_index < 0
            or
            choch_index >= len(df)
        ):

            return []

        candle = df.iloc[
            choch_index
        ]

        return [

            {

                "type":
                    event_type,

                "price":
                    float(
                        candle["Close"]
                    ),

                "index":
                    int(
                        choch_index
                    ),

                "time":
                    candle.name,

                "level":
                    (
                        float(
                            reversal_level
                        )
                        if
                        reversal_level
                        is not None
                        else None
                    ),

                "strength":
                    int(
                        choch_result.get(
                            "strength",
                            0
                        )
                    )

            }

        ]

    # ======================================================
    # ENGINE INFORMATION
    # ======================================================

    @staticmethod
    def version():

        return {

            "engine":
                "CHoCH V2",

            "version":
                "V2.5",

            "status":
                "Production",

            "logic":
                (
                    "Active Liquidity + "
                    "Protected Structure + "
                    "Body Close + "
                    "Displacement"
                ),

            "developer":
                "Liquidity Hunter AI"

        }

    # ======================================================
    # SELF TEST
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
            "Logic   :",
            info["logic"]
        )

        print(
            "========================================\n"
        )

        return True