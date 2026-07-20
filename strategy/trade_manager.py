from indicators.liquidity_sweep_v2 import LiquiditySweepV2
from indicators.atr import ATR
from strategy.smart_entry import SmartEntryEngine


class TradeManager:

    def __init__(self):

        print("Trade Manager Initialized")

        self.swing_engine = LiquiditySweepV2()
        self.atr = ATR()
        self.smart_entry = SmartEntryEngine()

        self.sl_mode = "NORMAL"

        self.sl_buffer = {
            "TIGHT": 0.10,
            "NORMAL": 0.25,
            "SAFE": 0.50
        }

        self.default_rr = 2.0

        # Minimum acceptable Risk : Reward
        self.minimum_rr = 1.5

        # Preferred Risk Reward
        self.preferred_rr = 2.5

        # Maximum Risk Allowed
        self.max_risk_points = 150

        # Minimum Reward Required
        self.minimum_reward_points = 20

        # Trade Validation
        self.enable_rr_filter = True

        # Smart Target Selection
        self.use_dynamic_targets = True

        # AI Trade Score
        self.trade_score = 0

        # Trade Reason
        self.trade_reason = []

        # Final Trade Decision
        self.trade_status = "WAIT"

    def generate_trade(self, signal, data):

        print("Generating Trade Plan...")

        # -----------------------------
        # Signal Status Validation
        # -----------------------------

        if signal["status"] != "READY":

            print("Trade Blocked :", signal["status"])

            trade = {

                "signal": signal["signal"],
                "confidence": signal["confidence"],
                "quality": signal["quality"],
                "status": signal["status"],
                "volatility": "UNKNOWN",

                "entry": None,
                "stop_loss": None,
                "take_profit": None,

                "risk": None,
                "reward": None,
                "risk_reward": None,

                "trade_score": 0,
                "trade_status": signal["status"],
                "trade_reason": [
                    f"Signal Status = {signal['status']}"
                ],

                "entry_type": "NONE",
                "entry_zone": None,
                "confirmation": "NONE",
                "entry_quality": "C"
            }

            entry_info = self.smart_entry.analyze(
                signal,
                trade
            )

            trade["entry_type"] = entry_info["entry_type"]
            trade["entry_zone"] = entry_info["entry_zone"]
            trade["confirmation"] = entry_info["confirmation"]
            trade["entry_quality"] = entry_info["entry_quality"]

            trade["trade_reason"].append(
                entry_info["reason"]
            )

            return trade

        # -----------------------------
        # Market Volatility
        # -----------------------------
        volatility = self.atr.get_volatility(data)

        print(f"Market Volatility : {volatility}")

        # -----------------------------
        # Reset AI State
        # -----------------------------
        self.trade_score = 0
        self.trade_reason = []
        self.trade_status = "WAIT"

        # -----------------------------
        # Volatility AI Logic
        # -----------------------------
        if volatility == "LOW":

            self.trade_score -= 5

            self.trade_reason.append(
             "Low Volatility Market"
            )

        elif volatility == "HIGH":

            self.trade_score += 10

            self.trade_reason.append(
                "High Volatility Market"
            )

        else:

            self.trade_reason.append(
                "Normal Volatility"
            )

        trade = {

            "signal": signal["signal"],
            "confidence": signal["confidence"],
            "quality": signal["quality"],
            "status": signal["status"],
            "volatility": volatility,

            "entry": None,
            "stop_loss": None,
            "take_profit": None,

            "risk": None,
            "reward": None,
            "risk_reward": None,

            "trade_score": 0,
            "trade_status": "WAIT",
            "trade_reason": [],

            "entry_type": "NONE",
            "entry_zone": None,
            "confirmation": "NONE",
            "entry_quality": "C",

        }

        # -----------------------------
        # NO TRADE
        # -----------------------------
        if signal["signal"] == "NO TRADE":

            trade["trade_reason"].append(
                "No Trade Setup"
            )

            return trade

        # -----------------------------
        # Entry Price
        # -----------------------------
        trade["entry"] = float(
            data.iloc[-1]["Close"]
        )

        # -----------------------------
        # Stop Loss
        # -----------------------------
        trade["stop_loss"] = self.calculate_stop_loss(
            signal["signal"],
            data
        )

        if trade["stop_loss"] is None:

            trade["trade_reason"].append(
                "Stop Loss Not Found"
            )

            return trade
       
        # -----------------------------
        # Take Profit
        # -----------------------------
        trade["take_profit"] = self.calculate_take_profit(
            signal["signal"],
            trade["entry"],
            trade["stop_loss"],
            data
        )

        if trade["take_profit"] is None:

            trade["trade_reason"].append(
                "Target Not Found"
            )

            return trade

        # -----------------------------
        # Risk
        # -----------------------------
        trade["risk"] = abs(
            trade["entry"] -
            trade["stop_loss"]
        )

        # -----------------------------
        # Reward
        # -----------------------------
        trade["reward"] = abs(
            trade["take_profit"] -
            trade["entry"]
        )

        # -----------------------------
        # Basic Validation
        # -----------------------------
        if trade["risk"] <= 0:

            trade["trade_reason"].append(
                "Invalid Risk"
            )

            return trade

        if trade["reward"] <= 0:

            trade["trade_reason"].append(
                "Invalid Reward"
            )

            return trade

        # -----------------------------
        # Risk Reward
        # -----------------------------
        trade["risk_reward"] = round(
            trade["reward"] /
            trade["risk"],
            2
        )
       
        # -----------------------------
        # Maximum Risk Filter
        # -----------------------------
        if trade["risk"] > self.max_risk_points:

            trade["trade_reason"].append(
                "Risk Too High"
            )

            trade["trade_status"] = "WAIT"

            return trade

        # -----------------------------
        # Minimum Reward Filter
        # -----------------------------
        if trade["reward"] < self.minimum_reward_points:

            trade["trade_reason"].append(
                "Reward Too Small"
            )

            trade["trade_status"] = "WAIT"

            return trade

        # -----------------------------
        # Risk Reward Validation
        # -----------------------------
        if self.enable_rr_filter:

            if trade["risk_reward"] < self.minimum_rr:

                trade["trade_reason"].append(
                    "Risk Reward Too Low"
                )

                trade["trade_status"] = "WAIT"

                return trade

            trade["trade_score"] += 10

            trade["trade_reason"].append(
                "Risk Reward Valid"
            )

        # -----------------------------
        # Smart Risk Reward Bonus
        # -----------------------------
        if trade["risk_reward"] >= self.preferred_rr:

            trade["trade_score"] += 20

            trade["trade_reason"].append(
                "Excellent Risk Reward"
            )

        elif trade["risk_reward"] >= 2.0:

            trade["trade_score"] += 10

            trade["trade_reason"].append(
                "Good Risk Reward"
            )
        
        # -----------------------------
        # Confidence Score
        # -----------------------------
        if signal["confidence"] >= 90:

            trade["trade_score"] += 20

            trade["trade_reason"].append(
                "High Confidence"
            )

        elif signal["confidence"] >= 75:

            trade["trade_score"] += 10

            trade["trade_reason"].append(
                "Good Confidence"
            )

        else:

            trade["trade_reason"].append(
                "Low Confidence"
            )

        # -----------------------------
        # Quality Score
        # -----------------------------
        if signal["quality"] == "A+":

            trade["trade_score"] += 20

            trade["trade_reason"].append(
                "Excellent Setup"
            )

        elif signal["quality"] == "A":

            trade["trade_score"] += 15

            trade["trade_reason"].append(
                "Strong Setup"
            )

        elif signal["quality"] == "B":

            trade["trade_score"] += 5

            trade["trade_reason"].append(
                "Average Setup"
            )

        else:

            trade["trade_reason"].append(
                "Weak Setup"
            )

        # -----------------------------
        # Trade Status Preparation
        # -----------------------------
        if trade["trade_score"] >= 40:

            trade["trade_reason"].append(
                "Trade Passed AI Validation"
            )
       
        # -----------------------------
        # Final AI Decision
        # -----------------------------
        if trade["trade_score"] >= 60:

            trade["trade_status"] = "READY"

            trade["trade_reason"].append(
                "Trade Approved"
            )

        elif trade["trade_score"] >= 40:

            trade["trade_status"] = "WATCH"

            trade["trade_reason"].append(
                "Wait For Better Confirmation"
            )

        else:

            trade["trade_status"] = "WAIT"

            trade["trade_reason"].append(
                "Trade Rejected"
            )

        # -----------------------------
        # Copy AI Status
        # -----------------------------
        self.trade_score = trade["trade_score"]
        self.trade_status = trade["trade_status"]
        self.trade_reason = trade["trade_reason"]

        # -----------------------------
        # Smart Entry Engine
        # -----------------------------
        entry_info = self.smart_entry.analyze(
            signal,
            trade
        )

        trade["entry_type"] = entry_info["entry_type"]
        trade["entry_zone"] = entry_info["entry_zone"]
        trade["confirmation"] = entry_info["confirmation"]
        trade["entry_quality"] = entry_info["entry_quality"]

        trade["trade_reason"].append(
            entry_info["reason"]
        )

        return trade

    def calculate_stop_loss(
        self,
        trade_signal,
        data
    ):

        buffer = self.sl_buffer[self.sl_mode]

        swing_highs, swing_lows = self.swing_engine.find_swings(data)

        if trade_signal == "BUY":

            swing = self.find_recent_swing_low(
                swing_lows
            )

            if swing:
                return swing["price"] - buffer

            return float(
                data.iloc[-1]["Low"] - buffer
            )

        elif trade_signal == "SELL":

            swing = self.find_recent_swing_high(
                swing_highs
            )

            if swing:
                return swing["price"] + buffer

            return float(
                data.iloc[-1]["High"] + buffer
            )

        return None

    def calculate_take_profit(
        self,
        signal,
        entry,
        stop_loss,
        data
    ):

        risk = abs(entry - stop_loss)

        swing_highs, swing_lows = \
            self.swing_engine.find_swings(data)

        # -----------------------------
        # BUY Target
        # -----------------------------
        if signal == "BUY":

            candidates = []

            for swing in swing_highs:

                if swing["price"] > entry:

                    rr = (
                        swing["price"] - entry
                    ) / risk

                    candidates.append(
                        (rr, swing["price"])
                    )

            # Select the first swing
            # that meets the minimum RR
            for rr, price in candidates:

                if rr >= self.minimum_rr:

                    return price

            # Fallback to preferred RR target
            return entry + (
                risk * self.preferred_rr
            )

        # -----------------------------
        # SELL Target
        # -----------------------------
        elif signal == "SELL":

            candidates = []

            for swing in swing_lows:

                if swing["price"] < entry:

                    rr = (
                        entry - swing["price"]
                    ) / risk

                    candidates.append(
                        (rr, swing["price"])
                    )

            # Select the first swing
            # that meets the minimum RR
            for rr, price in candidates:

                if rr >= self.minimum_rr:

                    return price

            # Fallback to preferred RR target
            return entry - (
                risk * self.preferred_rr
            )

        return None

    def find_recent_swing_low(self, swing_lows):

        if not swing_lows:
            return None

        return swing_lows[-1]

    def find_recent_swing_high(self, swing_highs):

        if not swing_highs:
            return None

        return swing_highs[-1]

    # -----------------------------------
    # Dynamic Take Profit
    # -----------------------------------

    def find_next_swing_high(
        self,
        swing_highs,
        entry
    ):

        if not swing_highs:
            return None

        candidates = []

        for swing in swing_highs:

            if swing["price"] > entry:
                candidates.append(swing)

        if candidates:
            return candidates[0]

        return None

    def find_next_swing_low(
        self,
        swing_lows,
        entry
    ):

        if not swing_lows:
            return None

        candidates = []

        for swing in swing_lows:

            if swing["price"] < entry:
                candidates.append(swing)

        if candidates:
            return candidates[-1]

