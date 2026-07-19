import pandas as pd


class CHoCHV2:
    """
    Change of Character V2
    Smart Money Reversal Engine
    """

    def __init__(self):

        print("CHoCH V2 Engine Initialized")

        # Scoring Weights
        self.body_break_score = 30
        self.displacement_score = 25
        self.liquidity_score = 25
        self.trend_confirmation_score = 20

        self.max_score = 100

    # --------------------------------------------------
    # Create Default Result
    # --------------------------------------------------

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
            "reasons": []
        }

    # --------------------------------------------------
    # Candle Body Break
    # --------------------------------------------------

    def is_body_break(self, close_price, level, direction):

        if direction == "BUY":
            return close_price > level

        if direction == "SELL":
            return close_price < level

        return False

    # --------------------------------------------------
    # Strong Displacement Candle
    # --------------------------------------------------

    def is_displacement(self, candle):

        body = abs(candle["Close"] - candle["Open"])
        candle_range = candle["High"] - candle["Low"]

        if candle_range == 0:
            return False

        body_ratio = body / candle_range

        return body_ratio >= 0.60

    # --------------------------------------------------
    # Convert Score to Quality
    # --------------------------------------------------

    def get_quality(self, score):

        if score >= 90:
            return "A+"

        if score >= 80:
            return "A"

        if score >= 70:
            return "B"

        if score >= 60:
            return "C"

        return "D"

    # --------------------------------------------------
    # Internal CHoCH Evaluation
    # --------------------------------------------------

    def _evaluate(
        self,
        df,
        market_structure,
        liquidity_sweeps
    ):
        """
        Internal evaluation method.
        This will become the single source of truth
        for both detect() and detect_legacy().
        """

    # --------------------------------------------------
    # Main Detection Method
    # --------------------------------------------------

    def detect(
        self,
        df,
        market_structure=None,
        liquidity_sweeps=None
    ):

        result = self.create_result()

        # Auto-load Market Structure if not provided
        if market_structure is None:
            from indicators.market_structure import MarketStructure
            ms = MarketStructure()
            market_structure = ms.detect(df)

        # Auto-load Liquidity Sweeps if not provided
        if liquidity_sweeps is None:
            from indicators.liquidity_sweep_v2 import LiquiditySweepV2
            ls = LiquiditySweepV2()
            liquidity_sweeps = ls.detect(df)

        # Detection logic will be added in Part 2

        print("Checking CHoCH V2...")

        if df is None or len(df) < 10:
            result["reasons"].append("Not enough candles")
            return result

        if market_structure is None:
            result["reasons"].append("Market Structure missing")
            return result

        latest = df.iloc[-1]

        bullish_break = False
        bearish_break = False

        # -----------------------------
        # Market Structure Validation
        # -----------------------------

        structures = market_structure

        if isinstance(structures, list) and len(structures) > 0:

            last_structure = structures[-1]

            structure_type = last_structure.get("type", "")

            level = last_structure.get("price", latest["Close"])

            if structure_type == "Bullish BOS":

                if self.is_body_break(
                    latest["Close"],
                    level,
                    "BUY"
                ):

                    bullish_break = True

            elif structure_type == "Bearish BOS":

                if self.is_body_break(
                    latest["Close"],
                    level,
                    "SELL"
                ):

                    bearish_break = True

        # -----------------------------
        # Displacement Check
        # -----------------------------

        if self.is_displacement(latest):

            result["displacement"] = True

        # -----------------------------
        # Liquidity Sweep Validation
        # -----------------------------

        if liquidity_sweeps is not None:

            if isinstance(liquidity_sweeps, list):

                if len(liquidity_sweeps) > 0:

                    result["liquidity_confirmed"] = True

        # -----------------------------
        # Temporary Flags
        # -----------------------------

        if bullish_break:

            result["trend_shift"] = True
            result["direction"] = "BUY"
            result["body_break"] = True

        elif bearish_break:

            result["trend_shift"] = True
            result["direction"] = "SELL"
            result["body_break"] = True

        # -----------------------------
        # Strength Scoring
        # -----------------------------

        score = 0

        if result["body_break"]:
            score += self.body_break_score
            result["reasons"].append("Body Break Confirmed")

        if result["displacement"]:
            score += self.displacement_score
            result["reasons"].append("Strong Displacement")

        if result["liquidity_confirmed"]:
            score += self.liquidity_score
            result["reasons"].append("Liquidity Sweep Confirmed")

        if result["trend_shift"]:
            score += self.trend_confirmation_score
            result["reasons"].append("Trend Shift Confirmed")

        if score > self.max_score:
            score = self.max_score

        result["strength"] = score
        result["quality"] = self.get_quality(score)

        # -----------------------------
        # Final Status
        # -----------------------------

        if score >= 80:

            result["choch"] = True
            result["status"] = "CONFIRMED"

        elif score >= 60:

            result["choch"] = False
            result["status"] = "WAIT"

        else:

            result["choch"] = False
            result["status"] = "NONE"
        
        # -----------------------------
        # Final Output Validation
        # -----------------------------

        if result["status"] == "CONFIRMED":

            print("========== CHoCH V2 ==========")
            print(f"Direction : {result['direction']}")
            print(f"Status    : {result['status']}")
            print(f"Strength  : {result['strength']}")
            print(f"Quality   : {result['quality']}")

            if len(result["reasons"]) > 0:

                print("\nReasons:")

                for reason in result["reasons"]:
                    print(f"  ✔️ {reason}")

        else:

            print("========== CHoCH V2 ==========")
            print("No Confirmed CHoCH Found")

        return result

    # --------------------------------------------------
    # Compatibility Method for Confluence / TrendFilter
    # --------------------------------------------------

    def detect_for_confluence(
        self,
        df,
        choch_result=None,
        market_structure=None,
        liquidity_sweeps=None
    ):
        """
        Returns legacy-style CHoCH list for compatibility
        with ConfluenceEngine and TrendFilter.
        """

        if choch_result is None:
            result = self.detect(
                df,
                market_structure,
                liquidity_sweeps
            )
        else:

            result = choch_result

        if not result["choch"]:
            return []

        latest = df.iloc[-1]

        direction = (
            "Bullish CHoCH"
            if result["direction"] == "BUY"
            else "Bearish CHoCH"
        )

        return [{
            "type": direction,
            "price": latest["Close"],
            "index": len(df) - 1,
            "time": latest.name
        }]