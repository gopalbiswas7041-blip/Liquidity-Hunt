from __future__ import annotations

from typing import Any, Dict, List, Optional


# ==========================================================
# Liquidity Hunter AI
# Liquidity Sweep V2.3
#
# ACTIVE LIQUIDITY ENGINE
#
# Production Logic
# ----------------------------------------------------------
#
# Bearish Sweep:
#
#     High > Swing High
#     AND
#     Close < Swing High
#
# Bullish Sweep:
#
#     Low < Swing Low
#     AND
#     Close > Swing Low
#
#
# ACTIVE LIQUIDITY RULE
# ----------------------------------------------------------
#
# Latest confirmed sweep = ACTIVE
#
# Active liquidity does NOT expire by candle age.
#
# Example:
#
#     Candle 92  -> Bullish Sweep
#     Candle 100 -> No Sweep
#     Candle 120 -> No Sweep
#
#     Candle 92 remains ACTIVE.
#
# If:
#
#     Candle 121 -> Bearish Sweep
#
# Then:
#
#     Candle 92  -> INACTIVE
#     Candle 121 -> ACTIVE
#
#
# V2.3 Improvements
# ----------------------------------------------------------
#
# 1. No fixed 20-candle sweep search window
# 2. No candle-age expiry
# 3. Latest confirmed sweep selection
# 4. Newer sweep replaces older active sweep
# 5. Duplicate sweep cleanup
# 6. Chronological output
# 7. Direction-safe output
# 8. CHoCH compatible
# 9. Confluence compatible
# 10. Signal-safe dictionary structure
# 11. Active liquidity persistence
#
# ==========================================================


class LiquiditySweepV2:

    # ======================================================
    # INITIALIZATION
    # ======================================================

    def __init__(self):

        print(
            "Liquidity Sweep V2.3 Engine Initialized"
        )

        # --------------------------------------------------
        # Swing Detection
        # --------------------------------------------------

        self.left_strength = 2

        self.right_strength = 2

        # --------------------------------------------------
        # Active Liquidity
        # --------------------------------------------------

        self.active_liquidity: Optional[
            Dict[str, Any]
        ] = None

        # --------------------------------------------------
        # Latest Detection Cache
        # --------------------------------------------------

        self.last_clean_signals: List[
            Dict[str, Any]
        ] = []

        self.last_detection_index = None

    # ======================================================
    # FIND SWINGS
    # ======================================================

    def find_swings(self, data):

        if data is None:

            return [], []

        if len(data) < 5:

            return [], []

        required_columns = [
            "High",
            "Low"
        ]

        for column in required_columns:

            if column not in data.columns:

                return [], []

        highs = data["High"].values

        lows = data["Low"].values

        swing_highs = []

        swing_lows = []

        left = self.left_strength

        right = self.right_strength

        # --------------------------------------------------
        # Only confirmed swings
        # --------------------------------------------------

        for i in range(
            left,
            len(data) - right
        ):

            # ==================================================
            # SWING HIGH
            # ==================================================

            is_high = True

            # --------------------------------------------------
            # Left side
            # --------------------------------------------------

            for j in range(
                i - left,
                i
            ):

                if highs[j] >= highs[i]:

                    is_high = False

                    break

            # --------------------------------------------------
            # Right side
            # --------------------------------------------------

            if is_high:

                for j in range(
                    i + 1,
                    i + right + 1
                ):

                    if highs[j] > highs[i]:

                        is_high = False

                        break

            # --------------------------------------------------
            # Save confirmed swing high
            # --------------------------------------------------

            if is_high:

                swing_highs.append({

                    "index":
                        int(i),

                    "price":
                        float(
                            highs[i]
                        )

                })

            # ==================================================
            # SWING LOW
            # ==================================================

            is_low = True

            # --------------------------------------------------
            # Left side
            # --------------------------------------------------

            for j in range(
                i - left,
                i
            ):

                if lows[j] <= lows[i]:

                    is_low = False

                    break

            # --------------------------------------------------
            # Right side
            # --------------------------------------------------

            if is_low:

                for j in range(
                    i + 1,
                    i + right + 1
                ):

                    if lows[j] < lows[i]:

                        is_low = False

                        break

            # --------------------------------------------------
            # Save confirmed swing low
            # --------------------------------------------------

            if is_low:

                swing_lows.append({

                    "index":
                        int(i),

                    "price":
                        float(
                            lows[i]
                        )

                })

        return (
            swing_highs,
            swing_lows
        )

    # ======================================================
    # DETECT RAW SWEEPS
    #
    # IMPORTANT V2.3
    #
    # There is NO 20-candle search limit.
    #
    # A swing level is searched until the end of the
    # available dataset.
    #
    # This is necessary because:
    #
    # Active liquidity has NO age expiry.
    # ======================================================

    def _detect_raw_sweeps(
        self,
        data,
        swing_highs,
        swing_lows
    ):

        highs = data["High"].values

        lows = data["Low"].values

        closes = data["Close"].values

        raw_signals = []

        # ==================================================
        # BEARISH SWEEPS
        #
        # High > Swing High
        # Close < Swing High
        # ==================================================

        for swing in swing_highs:

            try:

                swing_index = int(
                    swing["index"]
                )

                swing_price = float(
                    swing["price"]
                )

            except (
                KeyError,
                TypeError,
                ValueError
            ):

                continue

            start = (
                swing_index + 1
            )

            if start >= len(data):

                continue

            # --------------------------------------------------
            # Search ALL remaining candles.
            #
            # No 20 candle restriction.
            # --------------------------------------------------

            for i in range(
                start,
                len(data)
            ):

                try:

                    high_price = float(
                        highs[i]
                    )

                    close_price = float(
                        closes[i]
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    continue

                # --------------------------------------------------
                # Bearish liquidity sweep
                # --------------------------------------------------

                if (
                    high_price >
                    swing_price
                    and
                    close_price <
                    swing_price
                ):

                    raw_signals.append({

                        "type":
                            "Bearish Sweep",

                        "price":
                            swing_price,

                        "index":
                            int(i),

                        "time":
                            str(
                                data.index[i]
                            ),

                        "high":
                            float(
                                data.iloc[i]["High"]
                            ),

                        "low":
                            float(
                                data.iloc[i]["Low"]
                            ),

                        "close":
                            close_price,

                        "swing_index":
                            swing_index

                    })

                    # --------------------------------------------------
                    # One swing level = first confirmed sweep.
                    # --------------------------------------------------

                    break

        # ==================================================
        # BULLISH SWEEPS
        #
        # Low < Swing Low
        # Close > Swing Low
        # ==================================================

        for swing in swing_lows:

            try:

                swing_index = int(
                    swing["index"]
                )

                swing_price = float(
                    swing["price"]
                )

            except (
                KeyError,
                TypeError,
                ValueError
            ):

                continue

            start = (
                swing_index + 1
            )

            if start >= len(data):

                continue

            # --------------------------------------------------
            # Search ALL remaining candles.
            # --------------------------------------------------

            for i in range(
                start,
                len(data)
            ):

                try:

                    low_price = float(
                        lows[i]
                    )

                    close_price = float(
                        closes[i]
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    continue

                # --------------------------------------------------
                # Bullish liquidity sweep
                # --------------------------------------------------

                if (
                    low_price <
                    swing_price
                    and
                    close_price >
                    swing_price
                ):

                    raw_signals.append({

                        "type":
                            "Bullish Sweep",

                        "price":
                            swing_price,

                        "index":
                            int(i),

                        "time":
                            str(
                                data.index[i]
                            ),

                        "high":
                            float(
                                data.iloc[i]["High"]
                            ),

                        "low":
                            float(
                                data.iloc[i]["Low"]
                            ),

                        "close":
                            close_price,

                        "swing_index":
                            swing_index

                    })

                    # --------------------------------------------------
                    # One swing level = first confirmed sweep.
                    # --------------------------------------------------

                    break

        return raw_signals

    # ======================================================
    # DEDUPLICATE SWEEPS
    #
    # Same candle can sweep multiple levels.
    #
    # Bearish:
    #     Keep highest swept level.
    #
    # Bullish:
    #     Keep lowest swept level.
    # ======================================================

    def _deduplicate_sweeps(
        self,
        signals
    ):

        if not signals:

            return []

        grouped = {}

        for signal in signals:

            try:

                signal_type = str(
                    signal["type"]
                )

                signal_index = int(
                    signal["index"]
                )

            except (
                KeyError,
                TypeError,
                ValueError
            ):

                continue

            key = (
                signal_type,
                signal_index
            )

            if key not in grouped:

                grouped[key] = signal

                continue

            existing = grouped[key]

            # --------------------------------------------------
            # Bearish Sweep
            # --------------------------------------------------

            if (
                signal_type ==
                "Bearish Sweep"
            ):

                if (
                    float(
                        signal["price"]
                    )
                    >
                    float(
                        existing["price"]
                    )
                ):

                    grouped[key] = signal

            # --------------------------------------------------
            # Bullish Sweep
            # --------------------------------------------------

            elif (
                signal_type ==
                "Bullish Sweep"
            ):

                if (
                    float(
                        signal["price"]
                    )
                    <
                    float(
                        existing["price"]
                    )
                ):

                    grouped[key] = signal

        cleaned = list(
            grouped.values()
        )

        cleaned.sort(
            key=lambda item:
                int(
                    item.get(
                        "index",
                        -1
                    )
                )
        )

        return cleaned

    # ======================================================
    # SELECT ACTIVE LIQUIDITY
    #
    # Latest confirmed sweep becomes ACTIVE.
    #
    # There is NO age expiry.
    # ======================================================

    def _select_active_liquidity(
        self,
        data,
        signals
    ):

        # --------------------------------------------------
        # No new signal found
        #
        # If previous active liquidity exists, keep it.
        #
        # This protects the "no expiry" rule.
        # --------------------------------------------------

        if not signals:

            if self.active_liquidity is not None:

                active = dict(
                    self.active_liquidity
                )

                try:

                    latest_index = (
                        len(data) - 1
                    )

                    sweep_index = int(
                        active.get(
                            "index",
                            -1
                        )
                    )

                    active["age"] = (
                        latest_index -
                        sweep_index
                    )

                    active["status"] = (
                        "ACTIVE"
                    )

                    active["active"] = True

                    self.active_liquidity = (
                        active
                    )

                    return active

                except Exception:

                    return None

            return None

        # --------------------------------------------------
        # Latest chronological sweep
        # --------------------------------------------------

        latest = max(
            signals,
            key=lambda item:
                int(
                    item.get(
                        "index",
                        -1
                    )
                )
        )

        try:

            latest_index = (
                len(data) - 1
            )

            sweep_index = int(
                latest.get(
                    "index",
                    -1
                )
            )

        except (
            TypeError,
            ValueError
        ):

            return None

        active = dict(
            latest
        )

        active["age"] = (
            latest_index -
            sweep_index
        )

        active["status"] = (
            "ACTIVE"
        )

        active["active"] = True

        # --------------------------------------------------
        # Save latest sweep.
        #
        # This automatically replaces older liquidity.
        # --------------------------------------------------

        self.active_liquidity = (
            active
        )

        return active

    # ======================================================
    # GET ACTIVE LIQUIDITY
    # ======================================================

    def get_active_liquidity(
        self
    ):

        if self.active_liquidity is None:

            return None

        return dict(
            self.active_liquidity
        )

    # ======================================================
    # CLEAR ACTIVE LIQUIDITY
    #
    # Manual reset only.
    #
    # This should NOT be called because of candle age.
    # ======================================================

    def clear_active_liquidity(
        self
    ):

        self.active_liquidity = None

    # ======================================================
    # PUBLIC DETECTION
    # ======================================================

    def detect(
        self,
        data
    ):

        print(
            "Checking Liquidity Sweep V2.3..."
        )

        # ==================================================
        # VALIDATION
        # ==================================================

        if data is None:

            print(
                "No Market Data"
            )

            return []

        if len(data) < 10:

            print(
                "Not Enough Market Data"
            )

            return []

        required_columns = [
            "High",
            "Low",
            "Close"
        ]

        for column in required_columns:

            if column not in data.columns:

                print(
                    f"Missing Column : {column}"
                )

                return []

        # ==================================================
        # SWING DETECTION
        # ==================================================

        swing_highs, swing_lows = (
            self.find_swings(
                data
            )
        )

        print(
            f"Swing Highs : "
            f"{len(swing_highs)}"
        )

        print(
            f"Swing Lows  : "
            f"{len(swing_lows)}"
        )

        # ==================================================
        # RAW SWEEP DETECTION
        # ==================================================

        raw_signals = (
            self._detect_raw_sweeps(
                data,
                swing_highs,
                swing_lows
            )
        )

        print(
            f"Raw Liquidity Sweeps : "
            f"{len(raw_signals)}"
        )

        # ==================================================
        # DEDUPLICATION
        # ==================================================

        cleaned_signals = (
            self._deduplicate_sweeps(
                raw_signals
            )
        )

        self.last_clean_signals = [
            dict(signal)
            for signal in cleaned_signals
        ]

        self.last_detection_index = (
            len(data) - 1
        )

        print(
            f"Clean Liquidity Sweeps : "
            f"{len(cleaned_signals)}"
        )

        # ==================================================
        # ALL CLEAN LIQUIDITY DEBUG
        # ==================================================

        if cleaned_signals:

            print(
                "\n========== "
                "ALL CLEAN LIQUIDITY "
                "=========="
            )

            for signal in cleaned_signals:

                print(

                    f"Type : "
                    f"{signal.get('type')} | "

                    f"Index : "
                    f"{signal.get('index')} | "

                    f"Price : "
                    f"{signal.get('price')} | "

                    f"Time : "
                    f"{signal.get('time')}"

                )

            print(
                "=========================================="
            )

        else:

            print(
                "\nNo Clean Liquidity Sweeps Found"
            )

        # ==================================================
        # ACTIVE LIQUIDITY
        # ==================================================

        active_liquidity = (
            self._select_active_liquidity(
                data,
                cleaned_signals
            )
        )

        # ==================================================
        # ACTIVE DEBUG
        # ==================================================

        print(
            "\n========== "
            "ACTIVE LIQUIDITY DEBUG "
            "=========="
        )

        if active_liquidity is not None:

            print(
                "Type   :",
                active_liquidity.get(
                    "type"
                )
            )

            print(
                "Index  :",
                active_liquidity.get(
                    "index"
                )
            )

            print(
                "Price  :",
                active_liquidity.get(
                    "price"
                )
            )

            print(
                "Time   :",
                active_liquidity.get(
                    "time"
                )
            )

            print(
                "Age    :",
                active_liquidity.get(
                    "age"
                ),
                "candles"
            )

            print(
                "Status :",
                active_liquidity.get(
                    "status"
                )
            )

            print(
                "Active :",
                active_liquidity.get(
                    "active"
                )
            )

            print(
                "Rule   : "
                "Active until newer sweep"
            )

        else:

            print(
                "No Active Liquidity"
            )

        print(
            "=========================================="
        )

        # ==================================================
        # SIGNAL-SAFE OUTPUT
        #
        # Downstream engines receive ONLY active liquidity.
        # ==================================================

        if active_liquidity is not None:

            return [
                dict(
                    active_liquidity
                )
            ]

        return []

    # ======================================================
    # GET LATEST SWEEP
    # ======================================================

    @staticmethod
    def get_latest_sweep(
        signals
    ):

        if not signals:

            return None

        valid = [

            signal

            for signal in signals

            if isinstance(
                signal,
                dict
            )

            and
            signal.get(
                "index"
            ) is not None

        ]

        if not valid:

            return None

        return max(
            valid,
            key=lambda item:
                int(
                    item.get(
                        "index",
                        -1
                    )
                )
        )

    # ======================================================
    # GET ACTIVE SWEEP
    #
    # Compatibility helper.
    # ======================================================

    @staticmethod
    def get_active_sweep(
        signals
    ):

        return (
            LiquiditySweepV2
            .get_latest_sweep(
                signals
            )
        )

    # ======================================================
    # GET ALL CLEAN SIGNALS
    #
    # Debug / analysis helper.
    # ======================================================

    def get_all_clean_signals(
        self
    ):

        return [
            dict(signal)
            for signal in
            self.last_clean_signals
        ]

    # ======================================================
    # ENGINE INFORMATION
    # ======================================================

    def version(self):

        return {

            "engine":
                "Liquidity Sweep V2",

            "version":
                "V2.3",

            "status":
                "Production",

            "active_liquidity_rule":
                (
                    "Latest confirmed sweep remains "
                    "active until a newer sweep occurs"
                ),

            "sweep_search_expiry":
                None,

            "candle_age_expiry":
                None,

            "developer":
                "Liquidity Hunter AI"

        }

    # ======================================================
    # SELF TEST
    # ======================================================

    def self_test(self):

        print(
            "\n========== "
            "LIQUIDITY SWEEP ENGINE TEST "
            "=========="
        )

        info = self.version()

        print(
            "Engine :",
            info["engine"]
        )

        print(
            "Version :",
            info["version"]
        )

        print(
            "Status :",
            info["status"]
        )

        print(
            "Active Liquidity Rule :",
            info[
                "active_liquidity_rule"
            ]
        )

        print(
            "Sweep Search Expiry :",
            info[
                "sweep_search_expiry"
            ]
        )

        print(
            "Candle Age Expiry :",
            info[
                "candle_age_expiry"
            ]
        )

        print(
            "==========================================\n"
        )

        return True