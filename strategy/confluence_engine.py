# ==========================================================
# Liquidity Hunter AI
# Confluence Engine V16 Stable
# ==========================================================

class ConfluenceEngine:

    def __init__(self):

        print("Confluence Engine V16 Initialized")

        # ----------------------------------------
        # Score Weights
        # ----------------------------------------

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

        # ----------------------------------------
        # Engine Settings
        # ----------------------------------------

        self.confirmation_zone = 5
        self.minimum_trade_score = 75
        self.maximum_confidence = 100

    # ======================================================
    # Helper Functions
    # ======================================================

    def add_reason(self, result, text):

        if text not in result["reasons"]:
            result["reasons"].append(text)

    def add_score(
        self,
        direction,
        score,
        bullish_score,
        bearish_score
    ):

        if direction == "Bullish":
            bullish_score += score
        else:
            bearish_score += score

        return bullish_score, bearish_score

    def calculate_quality(self, confidence):

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

        print("Checking Smart Money Confluence...")

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

        # ----------------------------------------
        # No Liquidity
        # ----------------------------------------

        if not liquidity:

            self.add_reason(
                result,
                "No Liquidity Sweep Found"
            )

            return result

        latest_liquidity = liquidity[-1]

        liquidity_index = latest_liquidity["index"]

        if "Bullish" in latest_liquidity["type"]:

            direction = "Bullish"

        else:

            direction = "Bearish"

        bullish_score, bearish_score = self.add_score(

            direction,

            self.score_weights["liquidity"],

            bullish_score,

            bearish_score

        )

        self.add_reason(
            result,
            latest_liquidity["type"]
        )

        # =====================================================
        # Market Structure Confirmation
        # =====================================================

        for item in reversed(structure):

            if abs(item["index"] - liquidity_index) <= self.confirmation_zone:

                if direction in item["type"]:

                    bullish_score, bearish_score = self.add_score(

                        direction,
                        self.score_weights["structure"],
                        bullish_score,
                        bearish_score

                    )

                    self.add_reason(
                        result,
                        item["type"]
                    )

                else:

                    self.add_reason(
                        result,
                        "Structure Conflict"
                    )

                break

        # =====================================================
        # CHoCH Confirmation
        # =====================================================

        for item in reversed(choch):

            if abs(item["index"] - liquidity_index) <= self.confirmation_zone:

                if direction in item["type"]:

                    bullish_score, bearish_score = self.add_score(

                        direction,
                        self.score_weights["choch"],
                        bullish_score,
                        bearish_score

                    )

                    self.add_reason(
                        result,
                        item["type"]
                    )

                else:

                    self.add_reason(
                        result,
                        "CHoCH Conflict"
                    )

                break

        # =====================================================
        # Order Block Confirmation
        # =====================================================

        for item in reversed(order_blocks):

            if abs(item["index"] - liquidity_index) <= self.confirmation_zone:

                if direction in item["type"]:

                    bullish_score, bearish_score = self.add_score(

                        direction,
                        self.score_weights["order_block"],
                        bullish_score,
                        bearish_score

                    )

                    self.add_reason(
                        result,
                        item["type"]
                    )

                else:

                    self.add_reason(
                        result,
                        "Order Block Conflict"
                    )

                break

        # =====================================================
        # Fair Value Gap Confirmation
        # =====================================================

        for item in reversed(fvg):

            if abs(item["index"] - liquidity_index) <= self.confirmation_zone:

                if direction in item["type"]:

                    bullish_score, bearish_score = self.add_score(

                        direction,
                        self.score_weights["fvg"],
                        bullish_score,
                        bearish_score

                    )

                    self.add_reason(
                        result,
                        item["type"]
                    )

                else:

                    self.add_reason(
                        result,
                        "FVG Conflict"
                    )

                break

        # =====================================================
        # Trend Alignment
        # =====================================================

        if trend:

            trend_direction = trend.get(
                "trend",
                "NONE"
            )

            trend_strength = trend.get(
                "strength",
                "WEAK"
            )

            trend_match = (

                direction == "Bullish"
                and trend_direction == "BUY"

            ) or (

                direction == "Bearish"
                and trend_direction == "SELL"

            )

            if trend_match:

                bullish_score, bearish_score = self.add_score(

                    direction,

                    self.score_weights["trend"],

                    bullish_score,

                    bearish_score

                )

                self.add_reason(

                    result,

                    "Trend Alignment"

                )

                if trend_strength == "STRONG":

                    bullish_score, bearish_score = self.add_score(

                        direction,

                        self.score_weights["strong_trend_bonus"],

                        bullish_score,

                        bearish_score

                    )

                    self.add_reason(
                        result,
                        "Strong Trend Bonus"
                    )

                elif trend_strength == "MODERATE":

                    bullish_score, bearish_score = self.add_score(

                        direction,

                        self.score_weights["moderate_trend_bonus"],

                        bullish_score,

                        bearish_score

                    )

                    self.add_reason(
                        result,
                        "Moderate Trend Bonus"
                    )

            else:

                if direction == "Bullish":

                    bullish_score -= self.score_weights["trend_penalty"]

                else:

                    bearish_score -= self.score_weights["trend_penalty"]

                self.add_reason(
                    result,
                    "Trend Conflict"
                )

        # =====================================================
        # Final Scorecard
        # =====================================================

        result["scorecard"] = {

            "bullish_score": bullish_score,
            "bearish_score": bearish_score

        }

        # =====================================================
        # Confidence Calculation
        # =====================================================

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

        result["confidence"] = confidence

        # =====================================================
        # Trade Quality
        # =====================================================

        quality, status = self.calculate_quality(
            confidence
        )

        result["quality"] = quality
        result["status"] = status

        # =====================================================
        # Final Trade Decision
        # =====================================================

        if (

            bullish_score >= self.minimum_trade_score

            and

            bullish_score > bearish_score

        ):

            result["valid"] = True

            result["direction"] = "BUY"

        elif (

            bearish_score >= self.minimum_trade_score

            and

            bearish_score > bullish_score

        ):

            result["valid"] = True

            result["direction"] = "SELL"

        else:

            result["direction"] = "NO TRADE"

        # =====================================================
        # Smart Setup Classification
        # =====================================================

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

        # =====================================================
        # Remove Duplicate Reasons
        # =====================================================

        result["reasons"] = list(
            dict.fromkeys(
                result["reasons"]
            )
        )

        # =====================================================
        # Debug Output
        # =====================================================

        print("\n========== CONFLUENCE REPORT ==========")
        print("Direction :", result["direction"])
        print("Confidence:", result["confidence"])
        print("Quality   :", result["quality"])
        print("Status    :", result["status"])
        print("Bullish   :", bullish_score)
        print("Bearish   :", bearish_score)
        print("Reasons   :", result["reasons"])
        print("=======================================\n")

        return result
        