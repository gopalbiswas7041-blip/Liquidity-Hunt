class ConfluenceEngine:

    def __init__(self):
        print("Confluence Engine Initialized")

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
            "quality": "C",
            "status": "AVOID",
            "reasons": [],
            "scorecard": {}
        }

        bullish_score = 0
        bearish_score = 0

        zone = 5

        # -------------------------
        # Latest Liquidity
        # -------------------------

        if not liquidity:
            return result

        latest_liquidity = liquidity[-1]

        liquidity_index = latest_liquidity["index"]

        if "Bullish" in latest_liquidity["type"]:
            bullish_score += 25
            result["reasons"].append("Bullish Liquidity Sweep")
            direction = "Bullish"

        else:
            bearish_score += 25
            result["reasons"].append("Bearish Liquidity Sweep")
            direction = "Bearish"

        # -------------------------
        # Market Structure
        # -------------------------

        for item in reversed(structure):

            if abs(item["index"] - liquidity_index) <= zone:

                if direction in item["type"]:

                    if direction == "Bullish":
                        bullish_score += 25
                    else:
                        bearish_score += 25

                    result["reasons"].append(item["type"])

                break

        # -------------------------
        # CHoCH
        # -------------------------

        for item in reversed(choch):

            if abs(item["index"] - liquidity_index) <= zone:

                if direction in item["type"]:

                    if direction == "Bullish":
                        bullish_score += 25
                    else:
                        bearish_score += 25

                    result["reasons"].append(item["type"])

                break

        # -------------------------
        # Order Block
        # -------------------------

        for item in reversed(order_blocks):

            if abs(item["index"] - liquidity_index) <= zone:

                if direction in item["type"]:

                    if direction == "Bullish":
                        bullish_score += 15
                    else:
                        bearish_score += 15

                    result["reasons"].append(item["type"])

                break

        # -------------------------
        # Fair Value Gap
        # -------------------------

        for item in reversed(fvg):

            if abs(item["index"] - liquidity_index) <= zone:

                if direction in item["type"]:

                    if direction == "Bullish":
                        bullish_score += 10
                    else:
                        bearish_score += 10

                    result["reasons"].append(item["type"])

                break

        # -------------------------
        # Trend Alignment (V13)
        # -------------------------

        if trend:

            trend_direction = trend.get("trend", "NONE")
            trend_strength = trend.get("strength", "WEAK")

            if (
                direction == "Bullish"
                and trend_direction == "BUY"
            ):

                bullish_score += 15
                result["reasons"].append(
                    "15m Bullish Trend Alignment"
                )

                if trend_strength == "STRONG":
                    bullish_score += 10
                    result["reasons"].append(
                        "Strong Trend Bonus (+10)"
                    )

                elif trend_strength == "MODERATE":
                    bullish_score += 5
                    result["reasons"].append(
                        "Moderate Trend Bonus (+5)" 
                    )

            elif (
                direction == "Bearish"
                and trend_direction == "SELL"
            ):

                bearish_score += 15
                result["reasons"].append(
                    "15m Bearish Trend Alignment"
                )

                if trend_strength == "STRONG":
                    bearish_score += 10
                    result["reasons"].append(
                        "Strong Trend Bonus (+10)"
                    )

                elif trend_strength == "MODERATE":
                    bearish_score += 5
                    result["reasons"].append(
                        "Moderate Trend Bonus (+5)"
                    )

            else:

                if direction == "Bullish":
                    bullish_score -= 20
                else:
                    bearish_score -= 20

                result["reasons"].append(
                    "Trend Conflict (-20)"
                )

        # -------------------------
        # Final Score
        # -------------------------

        result["scorecard"] = {
            "bullish_score": bullish_score,
            "bearish_score": bearish_score
        }

        confidence = min(
            100,
            max(
                0,
                bullish_score,
                bearish_score
            )
        )

        result["confidence"] = confidence

        # -------------------------
        # Trade Quality
        # -------------------------

        if confidence >= 90:
            result["quality"] = "A+"
            result["status"] = "READY"

        elif confidence >= 75:
            result["quality"] = "A"
            result["status"] = "READY"

        elif confidence >= 60:
            result["quality"] = "B"
            result["status"] = "WAIT"

        else:
            result["quality"] = "C"
            result["status"] = "AVOID"

        # -------------------------
        # Final Direction
        # -------------------------

        if bullish_score >= 75 and bullish_score > bearish_score:

            result["valid"] = True
            result["direction"] = "BUY"

        elif bearish_score >= 75 and bearish_score > bullish_score:

            result["valid"] = True
            result["direction"] = "SELL"

        else:

            result["direction"] = "NO TRADE"

        return result