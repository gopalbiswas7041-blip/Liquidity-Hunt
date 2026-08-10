from indicators.liquidity_sweep_v2 import LiquiditySweepV2
from indicators.atr import ATR
from strategy.smart_entry import SmartEntryEngine


class TradeManager:

    def __init__(self):

        print("Trade Manager Initialized")

        self.swing_engine = LiquiditySweepV2()
        self.atr = ATR()
        self.smart_entry = SmartEntryEngine()

        # -----------------------------------
        # Stop Loss Configuration
        # -----------------------------------

        self.sl_mode = "NORMAL"

        self.sl_buffer = {
            "TIGHT": 0.10,
            "NORMAL": 0.25,
            "SAFE": 0.50
        }

        # -----------------------------------
        # Risk / Reward Configuration
        # -----------------------------------

        self.default_rr = 2.0

        self.minimum_rr = 1.5

        self.preferred_rr = 2.5

        self.max_risk_points = 150

        self.minimum_reward_points = 20

        # -----------------------------------
        # Trade Validation
        # -----------------------------------

        self.enable_rr_filter = True

        # -----------------------------------
        # Smart Target Selection
        # -----------------------------------

        self.use_dynamic_targets = True

        # -----------------------------------
        # AI Trade State
        # -----------------------------------

        self.trade_score = 0

        self.trade_reason = []

        self.trade_status = "WAIT"

    # =========================================================
    # GENERATE TRADE
    # =========================================================

    def generate_trade(self, signal, data):

        print("Generating Trade Plan...")

        # -----------------------------------
        # Signal Status Validation
        # -----------------------------------

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

            # Smart Entry compatibility
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

        # -----------------------------------
        # Market Volatility
        # -----------------------------------

        volatility = self.atr.get_volatility(data)

        print(f"Market Volatility : {volatility}")

        # -----------------------------------
        # Reset AI State
        # -----------------------------------

        self.trade_score = 0
        self.trade_reason = []
        self.trade_status = "WAIT"

        # -----------------------------------
        # Volatility AI Logic
        # -----------------------------------

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

        # -----------------------------------
        # Trade Object
        # -----------------------------------

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

        # -----------------------------------
        # NO TRADE
        # -----------------------------------

        if signal["signal"] == "NO TRADE":

            trade["trade_reason"].append(
                "No Trade Setup"
            )

            return trade

        # =====================================================
        # ENTRY PRICE
        # =====================================================

        trade["entry"] = float(
            data.iloc[-1]["Close"]
        )

        print(
            f"Trade Entry : {trade['entry']}"
        )

        # =====================================================
        # STOP LOSS
        # =====================================================

        trade["stop_loss"] = self.calculate_stop_loss(
            signal["signal"],
            trade["entry"],
            data
        )

        if trade["stop_loss"] is None:

            trade["trade_reason"].append(
                "Stop Loss Not Found"
            )

            return trade

        print(
            f"Trade Stop Loss : {trade['stop_loss']}"
        )

        # -----------------------------------
        # Final SL Direction Safety Check
        # -----------------------------------

        if signal["signal"] == "BUY":

            if trade["stop_loss"] >= trade["entry"]:

                print(
                    "INVALID BUY SL : SL is not below Entry"
                )

                trade["trade_reason"].append(
                    "Invalid BUY Stop Loss"
                )

                trade["trade_status"] = "WAIT"

                return trade

        elif signal["signal"] == "SELL":

            if trade["stop_loss"] <= trade["entry"]:

                print(
                    "INVALID SELL SL : SL is not above Entry"
                )

                trade["trade_reason"].append(
                    "Invalid SELL Stop Loss"
                )

                trade["trade_status"] = "WAIT"

                return trade

        # =====================================================
        # TAKE PROFIT
        # =====================================================

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

        print(
            f"Trade Take Profit : {trade['take_profit']}"
        )

        # -----------------------------------
        # Final TP Direction Safety Check
        # -----------------------------------

        if signal["signal"] == "BUY":

            if trade["take_profit"] <= trade["entry"]:

                print(
                    "INVALID BUY TP : TP is not above Entry"
                )

                trade["trade_reason"].append(
                    "Invalid BUY Take Profit"
                )

                trade["trade_status"] = "WAIT"

                return trade

        elif signal["signal"] == "SELL":

            if trade["take_profit"] >= trade["entry"]:

                print(
                    "INVALID SELL TP : TP is not below Entry"
                )

                trade["trade_reason"].append(
                    "Invalid SELL Take Profit"
                )

                trade["trade_status"] = "WAIT"

                return trade

        # =====================================================
        # RISK
        # =====================================================

        trade["risk"] = abs(
            trade["entry"] -
            trade["stop_loss"]
        )

        # =====================================================
        # REWARD
        # =====================================================

        trade["reward"] = abs(
            trade["take_profit"] -
            trade["entry"]
        )

        # -----------------------------------
        # Basic Validation
        # -----------------------------------

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

        # =====================================================
        # RISK REWARD
        # =====================================================

        trade["risk_reward"] = round(
            trade["reward"] /
            trade["risk"],
            2
        )

        print(
            f"Risk : {trade['risk']}"
        )

        print(
            f"Reward : {trade['reward']}"
        )

        print(
            f"Risk Reward : {trade['risk_reward']}"
        )

        # =====================================================
        # MAXIMUM RISK FILTER
        # =====================================================

        if trade["risk"] > self.max_risk_points:

            trade["trade_reason"].append(
                "Risk Too High"
            )

            trade["trade_status"] = "WAIT"

            return trade

        # =====================================================
        # MINIMUM REWARD FILTER
        # =====================================================

        if trade["reward"] < self.minimum_reward_points:

            trade["trade_reason"].append(
                "Reward Too Small"
            )

            trade["trade_status"] = "WAIT"

            return trade

        # =====================================================
        # RISK REWARD VALIDATION
        # =====================================================

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

        # =====================================================
        # SMART RISK REWARD BONUS
        # =====================================================

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

        # =====================================================
        # CONFIDENCE SCORE
        # =====================================================

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

        # =====================================================
        # QUALITY SCORE
        # =====================================================

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

        # =====================================================
        # TRADE STATUS PREPARATION
        # =====================================================

        if trade["trade_score"] >= 40:

            trade["trade_reason"].append(
                "Trade Passed AI Validation"
            )

        # =====================================================
        # FINAL AI DECISION
        # =====================================================

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

        # =====================================================
        # COPY AI STATUS
        # =====================================================

        self.trade_score = trade["trade_score"]
        self.trade_status = trade["trade_status"]
        self.trade_reason = trade["trade_reason"]

        # =====================================================
        # SMART ENTRY ENGINE
        # =====================================================

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

    # =========================================================
    # CALCULATE STOP LOSS
    # =========================================================

    def calculate_stop_loss(
        self,
        trade_signal,
        entry,
        data
    ):

        buffer = self.sl_buffer[self.sl_mode]

        swing_highs, swing_lows = \
            self.swing_engine.find_swings(data)

        # =====================================================
        # BUY STOP LOSS
        # =====================================================

        if trade_signal == "BUY":

            # Search from newest to oldest
            # for a swing low that is actually
            # below the Entry.
            for swing in reversed(swing_lows):

                swing_price = float(
                    swing["price"]
                )

                if swing_price < entry:

                    stop_loss = (
                        swing_price -
                        buffer
                    )

                    print(
                        f"BUY SL Swing : {swing_price}"
                    )

                    print(
                        f"BUY SL Buffer : {buffer}"
                    )

                    print(
                        f"BUY SL Final : {stop_loss}"
                    )

                    # Final safety check
                    if stop_loss < entry:

                        return float(stop_loss)

            # -------------------------------------------------
            # Fallback
            # -------------------------------------------------

            candle_low = float(
                data.iloc[-1]["Low"]
            )

            stop_loss = (
                candle_low -
                buffer
            )

            print(
                f"BUY SL Fallback : {stop_loss}"
            )

            if stop_loss < entry:

                return float(stop_loss)

            return None

        # =====================================================
        # SELL STOP LOSS
        # =====================================================

        elif trade_signal == "SELL":

            # Search from newest to oldest
            # for a swing high that is actually
            # above the Entry.
            for swing in reversed(swing_highs):

                swing_price = float(
                    swing["price"]
                )

                if swing_price > entry:

                    stop_loss = (
                        swing_price +
                        buffer
                    )

                    print(
                        f"SELL SL Swing : {swing_price}"
                    )

                    print(
                        f"SELL SL Buffer : {buffer}"
                    )

                    print(
                        f"SELL SL Final : {stop_loss}"
                    )

                    # Final safety check
                    if stop_loss > entry:

                        return float(stop_loss)

            # -------------------------------------------------
            # Fallback
            # -------------------------------------------------

            candle_high = float(
                data.iloc[-1]["High"]
            )

            stop_loss = (
                candle_high +
                buffer
            )

            print(
                f"SELL SL Fallback : {stop_loss}"
            )

            if stop_loss > entry:

                return float(stop_loss)

            return None

        return None

    # =========================================================
    # CALCULATE TAKE PROFIT
    # =========================================================

    def calculate_take_profit(
        self,
        signal,
        entry,
        stop_loss,
        data
    ):

        risk = abs(
            entry -
            stop_loss
        )

        if risk <= 0:

            return None

        swing_highs, swing_lows = \
            self.swing_engine.find_swings(data)

        # =====================================================
        # BUY TARGET
        # =====================================================

        if signal == "BUY":

            candidates = []

            for swing in swing_highs:

                price = float(
                    swing["price"]
                )

                # Target must be ABOVE Entry
                if price > entry:

                    rr = (
                        price - entry
                    ) / risk

                    candidates.append(
                        (price, rr)
                    )

            # -------------------------------------------------
            # Select nearest valid target
            # -------------------------------------------------

            valid_targets = [
                item
                for item in candidates
                if item[1] >= self.minimum_rr
            ]

            if valid_targets:

                # Nearest price above Entry
                valid_targets.sort(
                    key=lambda x: x[0]
                )

                return float(
                    valid_targets[0][0]
                )

            # -------------------------------------------------
            # Fallback Preferred RR
            # -------------------------------------------------

            target = (
                entry +
                (
                    risk *
                    self.preferred_rr
                )
            )

            return float(target)

        # =====================================================
        # SELL TARGET
        # =====================================================

        elif signal == "SELL":

            candidates = []

            for swing in swing_lows:

                price = float(
                    swing["price"]
                )

                # Target must be BELOW Entry
                if price < entry:

                    rr = (
                        entry - price
                    ) / risk

                    candidates.append(
                        (price, rr)
                    )

            # -------------------------------------------------
            # Select nearest valid target
            # -------------------------------------------------

            valid_targets = [
                item
                for item in candidates
                if item[1] >= self.minimum_rr
            ]

            if valid_targets:

                # Nearest price below Entry
                valid_targets.sort(
                    key=lambda x: x[0],
                    reverse=True
                )

                return float(
                    valid_targets[0][0]
                )

            # -------------------------------------------------
            # Fallback Preferred RR
            # -------------------------------------------------

            target = (
                entry -
                (
                    risk *
                    self.preferred_rr
                )
            )

            return float(target)

        return None

    # =========================================================
    # FIND RECENT SWING LOW
    # =========================================================

    def find_recent_swing_low(
        self,
        swing_lows
    ):

        if not swing_lows:

            return None

        return swing_lows[-1]

    # =========================================================
    # FIND RECENT SWING HIGH
    # =========================================================

    def find_recent_swing_high(
        self,
        swing_highs
    ):

        if not swing_highs:

            return None

        return swing_highs[-1]

    # =========================================================
    # FIND NEXT SWING HIGH
    # =========================================================

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

            candidates.sort(
                key=lambda x: x["price"]
            )

            return candidates[0]

        return None

    # =========================================================
    # FIND NEXT SWING LOW
    # =========================================================

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

            candidates.sort(
                key=lambda x: x["price"],
                reverse=True
            )

            return candidates[0]

        return None