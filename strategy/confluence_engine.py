# ==========================================================
# Liquidity Hunter AI
# Confluence Engine V20.4
#
# Direction-Aware Smart Money Confluence Engine
#
# Logic:
#
# Liquidity Sweep
#       ↓
# Reversal Direction
#       ↓
# Confirmed CHoCH
#       ↓
# Structure BOS
#       ↓
# Order Block
#       ↓
# FVG
#       ↓
# HTF Trend
#       ↓
# Final Confluence
#
# Important:
#
# Bullish Sweep  != BUY
# Bullish Sweep  -> potential SELL
#
# Bearish Sweep  != SELL
# Bearish Sweep  -> potential BUY
#
# Confirmed CHoCH has highest directional priority.
# ==========================================================


class ConfluenceEngine:

    def __init__(self):

        print(
            "Confluence Engine V20.4 Initialized"
        )

        # --------------------------------------------------
        # Score Weights
        # --------------------------------------------------

        self.score_weights = {

            "liquidity": 25,

            "structure": 25,

            "choch": 25,

            "order_block": 15,

            "fvg": 10,

            "trend": 15,

            "strong_trend_bonus": 10,

            "moderate_trend_bonus": 5,

            "trend_penalty": 20

        }

        # --------------------------------------------------
        # Engine Settings
        # --------------------------------------------------

        self.confirmation_zone = 5

        self.minimum_trade_score = 75

        self.maximum_confidence = 100

    # ======================================================
    # Helper: Add Reason
    # ======================================================

    def add_reason(
        self,
        result,
        text
    ):

        if text not in result["reasons"]:

            result["reasons"].append(text)

    # ======================================================
    # Helper: Add Score
    # ======================================================

    def add_score(
        self,
        direction,
        score,
        bullish_score,
        bearish_score
    ):

        if direction == "BUY":

            bullish_score += score

        elif direction == "SELL":

            bearish_score += score

        return (
            bullish_score,
            bearish_score
        )

    # ======================================================
    # Quality
    # ======================================================

    def calculate_quality(
        self,
        confidence
    ):

        if confidence >= 90:

            return "A+", "READY"

        elif confidence >= 75:

            return "A", "READY"

        elif confidence >= 60:

            return "B", "WAIT"

        elif confidence >= 40:

            return "C", "WAIT"

        return "D", "AVOID"

    # ======================================================
    # Liquidity Direction
    #
    # IMPORTANT:
    #
    # Bullish Sweep
    #     ↓
    # Sell-side liquidity was taken
    #     ↓
    # Potential bearish reversal
    #     ↓
    # SELL
    #
    # Bearish Sweep
    #     ↓
    # Buy-side liquidity was taken
    #     ↓
    # Potential bullish reversal
    #     ↓
    # BUY
    # ======================================================

    def get_liquidity_direction(
        self,
        liquidity
    ):

        if not isinstance(
            liquidity,
            dict
        ):

            return None

        liquidity_type = str(
            liquidity.get(
                "type",
                ""
            )
        )

        if liquidity_type == "Bullish Sweep":

            return "SELL"

        if liquidity_type == "Bearish Sweep":

            return "BUY"

        return None

    # ======================================================
    # CHoCH Direction
    # ======================================================

    def get_choch_direction(
        self,
        choch
    ):

        if not isinstance(
            choch,
            list
        ):

            return None

        if not choch:

            return None

        # ----------------------------------------------
        # Search latest valid CHoCH
        # ----------------------------------------------

        for item in reversed(choch):

            if not isinstance(
                item,
                dict
            ):

                continue

            event_type = str(
                item.get(
                    "type",
                    ""
                )
            )

            if "Bullish CHoCH" in event_type:

                return "BUY"

            if "Bearish CHoCH" in event_type:

                return "SELL"

        return None

    # ======================================================
    # Structure Direction
    # ======================================================

    def get_structure_direction(
        self,
        item
    ):

        if not isinstance(
            item,
            dict
        ):

            return None

        event_type = str(
            item.get(
                "type",
                ""
            )
        )

        if "Bullish BOS" in event_type:

            return "BUY"

        if "Bearish BOS" in event_type:

            return "SELL"

        if "Bullish CHoCH" in event_type:

            return "BUY"

        if "Bearish CHoCH" in event_type:

            return "SELL"

        return None

    # ======================================================
    # Generic Direction
    #
    # Used for:
    # Order Blocks
    # FVG
    # ======================================================

    def get_component_direction(
        self,
        item
    ):

        if not isinstance(
            item,
            dict
        ):

            return None

        event_type = str(
            item.get(
                "type",
                ""
            )
        )

        if "Bullish" in event_type:

            return "BUY"

        if "Bearish" in event_type:

            return "SELL"

        return None

    # ======================================================
    # Find Nearest Component
    #
    # Searches backward from anchor index.
    #
    # This prevents old historical components from
    # influencing the current setup.
    # ======================================================

    def find_nearest_component(
        self,
        components,
        anchor_index
    ):

        if not isinstance(
            components,
            list
        ):

            return None

        candidates = []

        for item in components:

            if not isinstance(
                item,
                dict
            ):

                continue

            index = item.get(
                "index"
            )

            if index is None:

                continue

            try:

                index = int(index)

            except Exception:

                continue

            distance = abs(
                index - anchor_index
            )

            if distance <= self.confirmation_zone:

                candidates.append(
                    (
                        distance,
                        index,
                        item
                    )
                )

        if not candidates:

            return None

        # ----------------------------------------------
        # Nearest first.
        # If same distance, latest index wins.
        # ----------------------------------------------

        candidates.sort(
            key=lambda x: (
                x[0],
                -x[1]
            )
        )

        return candidates[0][2]

    # ======================================================
    # Main Analysis
    # ======================================================

    def analyze(
        self,
        liquidity,
        structure,
        choch,
        order_blocks,
        fvg,
        trend
    ):

        print(
            "Checking Smart Money Confluence..."
        )

        # ==================================================
        # Default Result
        # ==================================================

        result = {

            "valid": False,

            "direction": "NO TRADE",

            "confidence": 0,

            "quality": "D",

            "status": "AVOID",

            "reasons": [],

            "scorecard": {

                "bullish_score": 0,

                "bearish_score": 0

            }

        }

        bullish_score = 0

        bearish_score = 0

        # ==================================================
        # Validate Liquidity
        # ==================================================

        if not isinstance(
            liquidity,
            list
        ) or not liquidity:

            self.add_reason(
                result,
                "No Liquidity Sweep Found"
            )

            print(
                "\n========== CONFLUENCE REPORT =========="
            )

            print(
                "Direction : NO TRADE"
            )

            print(
                "Confidence: 0"
            )

            print(
                "Quality   : D"
            )

            print(
                "Status    : AVOID"
            )

            print(
                "Reasons   :",
                result["reasons"]
            )

            print(
                "=======================================\n"
            )

            return result

        # ==================================================
        # Latest Liquidity
        # ==================================================

        latest_liquidity = None

        valid_liquidity = []

        for item in liquidity:

            if not isinstance(
                item,
                dict
            ):

                continue

            if "index" not in item:

                continue

            if "type" not in item:

                continue

            valid_liquidity.append(
                item
            )

        if not valid_liquidity:

            self.add_reason(
                result,
                "No Valid Liquidity Sweep"
            )

            return result

        latest_liquidity = max(
            valid_liquidity,
            key=lambda item: int(
                item["index"]
            )
        )

        liquidity_index = int(
            latest_liquidity["index"]
        )

        liquidity_type = str(
            latest_liquidity["type"]
        )

        # ==================================================
        # Liquidity Direction
        # ==================================================

        liquidity_direction = (
            self.get_liquidity_direction(
                latest_liquidity
            )
        )

        if liquidity_direction is None:

            self.add_reason(
                result,
                "Unknown Liquidity Direction"
            )

            return result

        # --------------------------------------------------
        # Liquidity itself gives setup direction.
        # It is NOT final direction until CHoCH confirms.
        # --------------------------------------------------

        setup_direction = (
            liquidity_direction
        )

        bullish_score, bearish_score = (
            self.add_score(
                setup_direction,
                self.score_weights["liquidity"],
                bullish_score,
                bearish_score
            )
        )

        self.add_reason(
            result,
            liquidity_type
        )

        # ==================================================
        # CHoCH Direction
        #
        # Confirmed CHoCH gets priority over liquidity.
        # ==================================================

        choch_direction = (
            self.get_choch_direction(
                choch
            )
        )

        if choch_direction is not None:

            final_direction = (
                choch_direction
            )

            # ----------------------------------------------
            # Check whether CHoCH agrees with liquidity.
            # ----------------------------------------------

            if choch_direction == setup_direction:

                self.add_reason(
                    result,
                    "CHoCH Direction Confirmed"
                )

            else:

                self.add_reason(
                    result,
                    "Liquidity Reversal Confirmed By CHoCH"
                )

            # ----------------------------------------------
            # CHoCH score
            # ----------------------------------------------

            bullish_score, bearish_score = (
                self.add_score(
                    choch_direction,
                    self.score_weights["choch"],
                    bullish_score,
                    bearish_score
                )
            )

        else:

            # ------------------------------------------------
            # No confirmed CHoCH.
            #
            # We keep liquidity direction as a setup bias,
            # but do not treat it as fully confirmed.
            # ------------------------------------------------

            final_direction = (
                setup_direction
            )

            self.add_reason(
                result,
                "CHoCH Not Confirmed"
            )

        # ==================================================
        # Anchor Index
        #
        # If CHoCH exists, use CHoCH candle as the main
        # confluence anchor.
        #
        # Otherwise use liquidity candle.
        # ==================================================

        anchor_index = liquidity_index

        if isinstance(
            choch,
            list
        ) and choch:

            latest_choch = None

            for item in reversed(choch):

                if isinstance(
                    item,
                    dict
                ):

                    if "index" in item:

                        latest_choch = item

                        break

            if latest_choch is not None:

                try:

                    anchor_index = int(
                        latest_choch["index"]
                    )

                except Exception:

                    anchor_index = liquidity_index

        # ==================================================
        # Structure Confirmation
        # ==================================================

        structure_component = (
            self.find_nearest_component(
                structure,
                anchor_index
            )
        )

        if structure_component is not None:

            structure_direction = (
                self.get_structure_direction(
                    structure_component
                )
            )

            if (
                structure_direction ==
                final_direction
            ):

                bullish_score, bearish_score = (
                    self.add_score(
                        final_direction,
                        self.score_weights["structure"],
                        bullish_score,
                        bearish_score
                    )
                )

                self.add_reason(
                    result,
                    structure_component.get(
                        "type",
                        "Structure Confirmed"
                    )
                )

            elif structure_direction is not None:

                self.add_reason(
                    result,
                    "Structure Conflict"
                )

        else:

            self.add_reason(
                result,
                "Structure Confirmation Missing"
            )

        # ==================================================
        # Order Block Confirmation
        # ==================================================

        order_block_component = (
            self.find_nearest_component(
                order_blocks,
                anchor_index
            )
        )

        if order_block_component is not None:

            ob_direction = (
                self.get_component_direction(
                    order_block_component
                )
            )

            if ob_direction == final_direction:

                bullish_score, bearish_score = (
                    self.add_score(
                        final_direction,
                        self.score_weights["order_block"],
                        bullish_score,
                        bearish_score
                    )
                )

                self.add_reason(
                    result,
                    order_block_component.get(
                        "type",
                        "Order Block Confirmed"
                    )
                )

            elif ob_direction is not None:

                self.add_reason(
                    result,
                    "Order Block Conflict"
                )

        else:

            self.add_reason(
                result,
                "Order Block Confirmation Missing"
            )

        # ==================================================
        # Fair Value Gap Confirmation
        # ==================================================

        fvg_component = (
            self.find_nearest_component(
                fvg,
                anchor_index
            )
        )

        if fvg_component is not None:

            fvg_direction = (
                self.get_component_direction(
                    fvg_component
                )
            )

            if fvg_direction == final_direction:

                bullish_score, bearish_score = (
                    self.add_score(
                        final_direction,
                        self.score_weights["fvg"],
                        bullish_score,
                        bearish_score
                    )
                )

                self.add_reason(
                    result,
                    fvg_component.get(
                        "type",
                        "FVG Confirmed"
                    )
                )

            elif fvg_direction is not None:

                self.add_reason(
                    result,
                    "FVG Conflict"
                )

        else:

            self.add_reason(
                result,
                "FVG Confirmation Missing"
            )

        # ==================================================
        # Trend Alignment
        # ==================================================

        if isinstance(
            trend,
            dict
        ):

            trend_direction = str(
                trend.get(
                    "trend",
                    "NONE"
                )
            ).upper()

            trend_strength = str(
                trend.get(
                    "strength",
                    "WEAK"
                )
            ).upper()

            trend_match = (

                final_direction == "BUY"

                and

                trend_direction == "BUY"

            ) or (

                final_direction == "SELL"

                and

                trend_direction == "SELL"

            )

            if trend_match:

                bullish_score, bearish_score = (
                    self.add_score(
                        final_direction,
                        self.score_weights["trend"],
                        bullish_score,
                        bearish_score
                    )
                )

                self.add_reason(
                    result,
                    "Trend Alignment"
                )

                # ------------------------------------------
                # Strong Trend Bonus
                # ------------------------------------------

                if trend_strength == "STRONG":

                    bullish_score, bearish_score = (
                        self.add_score(
                            final_direction,
                            self.score_weights[
                                "strong_trend_bonus"
                            ],
                            bullish_score,
                            bearish_score
                        )
                    )

                    self.add_reason(
                        result,
                        "Strong Trend Bonus"
                    )

                # ------------------------------------------
                # Moderate Trend Bonus
                # ------------------------------------------

                elif trend_strength == "MODERATE":

                    bullish_score, bearish_score = (
                        self.add_score(
                            final_direction,
                            self.score_weights[
                                "moderate_trend_bonus"
                            ],
                            bullish_score,
                            bearish_score
                        )
                    )

                    self.add_reason(
                        result,
                        "Moderate Trend Bonus"
                    )

            else:

                # ------------------------------------------
                # Trend conflict
                # ------------------------------------------

                if final_direction == "BUY":

                    bullish_score -= (
                        self.score_weights[
                            "trend_penalty"
                        ]
                    )

                elif final_direction == "SELL":

                    bearish_score -= (
                        self.score_weights[
                            "trend_penalty"
                        ]
                    )

                self.add_reason(
                    result,
                    "Trend Conflict"
                )

        else:

            self.add_reason(
                result,
                "Trend Data Missing"
            )

        # ==================================================
        # Prevent Negative Scores
        # ==================================================

        bullish_score = max(
            0,
            bullish_score
        )

        bearish_score = max(
            0,
            bearish_score
        )

        # ==================================================
        # Final Scorecard
        # ==================================================

        result["scorecard"] = {

            "bullish_score":
                bullish_score,

            "bearish_score":
                bearish_score

        }

        # ==================================================
        # Confidence
        # ==================================================

        highest_score = max(
            bullish_score,
            bearish_score
        )

        confidence = max(
            0,
            min(
                self.maximum_confidence,
                highest_score
            )
        )

        result["confidence"] = (
            confidence
        )

        # ==================================================
        # Quality
        # ==================================================

        quality, status = (
            self.calculate_quality(
                confidence
            )
        )

        result["quality"] = quality

        result["status"] = status

        # ==================================================
        # Final Direction
        #
        # Only allow the direction with the highest score.
        # ==================================================

        if final_direction == "BUY":

            if (
                bullish_score >=
                self.minimum_trade_score
                and
                bullish_score >
                bearish_score
            ):

                result["valid"] = True

                result["direction"] = "BUY"

            else:

                result["direction"] = "NO TRADE"

        elif final_direction == "SELL":

            if (
                bearish_score >=
                self.minimum_trade_score
                and
                bearish_score >
                bullish_score
            ):

                result["valid"] = True

                result["direction"] = "SELL"

            else:

                result["direction"] = "NO TRADE"

        else:

            result["direction"] = "NO TRADE"

        # ==================================================
        # Smart Setup Classification
        # ==================================================

        if result["valid"]:

            if confidence >= 90:

                self.add_reason(
                    result,
                    "High Probability Setup"
                )

            elif confidence >= 75:

                self.add_reason(
                    result,
                    "Good Confluence Setup"
                )

            else:

                self.add_reason(
                    result,
                    "Average Quality Setup"
                )

        else:

            self.add_reason(
                result,
                "Confluence Below Threshold"
            )

        # ==================================================
        # Remove Duplicate Reasons
        # ==================================================

        result["reasons"] = list(
            dict.fromkeys(
                result["reasons"]
            )
        )

        # ==================================================
        # Debug Output
        # ==================================================

        print(
            "\n========== CONFLUENCE REPORT =========="
        )

        print(
            "Direction :",
            result["direction"]
        )

        print(
            "Confidence:",
            result["confidence"]
        )

        print(
            "Quality   :",
            result["quality"]
        )

        print(
            "Status    :",
            result["status"]
        )

        print(
            "Bullish   :",
            bullish_score
        )

        print(
            "Bearish   :",
            bearish_score
        )

        print(
            "Reasons   :",
            result["reasons"]
        )

        print(
            "=======================================\n"
        )

        return result