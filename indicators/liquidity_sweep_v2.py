from __future__ import annotations


# ==========================================================
# Liquidity Hunter AI
# Liquidity Sweep V2.2
#
# ACTIVE LIQUIDITY ENGINE
#
# Core Logic:
#
# Bearish Sweep:
#   High > Swing High
#   AND
#   Close < Swing High
#
# Bullish Sweep:
#   Low < Swing Low
#   AND
#   Close > Swing Low
#
# V2.2 Improvements:
#
#   1. No fixed candle expiry
#   2. Latest confirmed sweep remains ACTIVE
#   3. Newer sweep replaces previous active sweep
#   4. Duplicate sweep cleanup
#   5. Chronological output
#   6. Directional latest-sweep selection
#   7. Signal-safe output for CHoCH / Confluence
#
# ACTIVE LIQUIDITY RULE:
#
#   Latest confirmed liquidity sweep = ACTIVE LIQUIDITY
#
# Example:
#
#   Candle 92  -> Bullish Sweep
#   Candle 93  -> No Sweep
#   Candle 94  -> No Sweep
#   ...
#   Candle 120 -> No Sweep
#
#   Candle 92 Bullish Sweep remains ACTIVE.
#
#   If Candle 121 produces a Bearish Sweep:
#
#   Candle 92 -> INACTIVE
#   Candle 121 -> ACTIVE
#
# ==========================================================


class LiquiditySweepV2:

    # ======================================================
    # INITIALIZATION
    # ======================================================

    def __init__(self):

        print(
            "Liquidity Sweep V2.2 Engine Initialized"
        )

        # --------------------------------------------------
        # Swing Detection Strength
        # --------------------------------------------------

        self.left_strength = 2
        self.right_strength = 2

        # --------------------------------------------------
        # Active liquidity
        #
        # This stores the latest confirmed sweep.
        #
        # IMPORTANT:
        #
        # There is NO candle-based expiry.
        #
        # The active sweep remains valid until a newer
        # confirmed sweep is detected.
        # --------------------------------------------------

        self.active_liquidity = None

    # ======================================================
    # Find Swing Highs / Swing Lows
    # ======================================================

    def find_swings(self, data):

        if data is None:

            return [], []

        if len(data) < 5:

            return [], []

        highs = data["High"].values
        lows = data["Low"].values

        swing_highs = []
        swing_lows = []

        left = self.left_strength
        right = self.right_strength

        # --------------------------------------------------
        # Confirmed swings only.
        #
        # The last 'right' candles cannot form a confirmed
        # swing until enough candles exist to the right.
        # --------------------------------------------------

        for i in range(
            left,
            len(data) - right
        ):

            # ==================================================
            # Swing High
            # ==================================================

            is_high = True

            for j in range(
                i - left,
                i
            ):

                if highs[j] >= highs[i]:

                    is_high = False

                    break

            if is_high:

                for j in range(
                    i + 1,
                    i + right + 1
                ):

                    if highs[j] > highs[i]:

                        is_high = False

                        break

            if is_high:

                swing_highs.append({

                    "index":
                        i,

                    "price":
                        float(
                            highs[i]
                        )

                })

            # ==================================================
            # Swing Low
            # ==================================================

            is_low = True

            for j in range(
                i - left,
                i
            ):

                if lows[j] <= lows[i]:

                    is_low = False

                    break

            if is_low:

                for j in range(
                    i + 1,
                    i + right + 1
                ):

                    if lows[j] < lows[i]:

                        is_low = False

                        break

            if is_low:

                swing_lows.append({

                    "index":
                        i,

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
    # Detect Raw Liquidity Sweeps
    #
    # Scans the complete dataframe.
    #
    # Historical sweeps are allowed.
    #
    # The latest confirmed sweep will later become
    # ACTIVE LIQUIDITY.
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
        # Bearish Liquidity Sweep
        #
        # Price takes swing high liquidity
        # and closes back below it.
        # ==================================================

        for swing in swing_highs:

            swing_index = int(
                swing["index"]
            )

            swing_price = float(
                swing["price"]
            )

            start = swing_index + 1

            if start >= len(data):

                continue

            # --------------------------------------------------
            # Search until next 20 candles.
            #
            # This is NOT the active-liquidity expiry.
            #
            # It only defines how far we search from a swing
            # level for the first sweep of that level.
            # --------------------------------------------------

            end = min(
                start + 20,
                len(data)
            )

            for i in range(
                start,
                end
            ):

                high_price = float(
                    highs[i]
                )

                close_price = float(
                    closes[i]
                )

                if (
                    high_price > swing_price
                    and
                    close_price < swing_price
                ):

                    raw_signals.append({

                        "type":
                            "Bearish Sweep",

                        "price":
                            swing_price,

                        "index":
                            i,

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
                    # One swing level = one sweep.
                    # --------------------------------------------------

                    break

        # ==================================================
        # Bullish Liquidity Sweep
        #
        # Price takes swing low liquidity
        # and closes back above it.
        # ==================================================

        for swing in swing_lows:

            swing_index = int(
                swing["index"]
            )

            swing_price = float(
                swing["price"]
            )

            start = swing_index + 1

            if start >= len(data):

                continue

            end = min(
                start + 20,
                len(data)
            )

            for i in range(
                start,
                end
            ):

                low_price = float(
                    lows[i]
                )

                close_price = float(
                    closes[i]
                )

                if (
                    low_price < swing_price
                    and
                    close_price > swing_price
                ):

                    raw_signals.append({

                        "type":
                            "Bullish Sweep",

                        "price":
                            swing_price,

                        "index":
                            i,

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
                    # One swing level = one sweep.
                    # --------------------------------------------------

                    break

        return raw_signals

    # ======================================================
    # Remove Duplicate Sweeps
    #
    # If one candle sweeps multiple liquidity levels in
    # the same direction, keep one representative event.
    #
    # Bearish:
    #   Keep highest swept level.
    #
    # Bullish:
    #   Keep lowest swept level.
    # ======================================================

    def _deduplicate_sweeps(
        self,
        signals
    ):

        if not signals:

            return []

        grouped = {}

        for signal in signals:

            key = (
                signal["type"],
                signal["index"]
            )

            if key not in grouped:

                grouped[key] = signal

                continue

            existing = grouped[key]

            # --------------------------------------------------
            # Bearish sweep:
            # higher liquidity level is more meaningful.
            # --------------------------------------------------

            if signal["type"] == "Bearish Sweep":

                if (
                    signal["price"] >
                    existing["price"]
                ):

                    grouped[key] = signal

            # --------------------------------------------------
            # Bullish sweep:
            # lower liquidity level is more meaningful.
            # --------------------------------------------------

            elif signal["type"] == "Bullish Sweep":

                if (
                    signal["price"] <
                    existing["price"]
                ):

                    grouped[key] = signal

        cleaned = list(
            grouped.values()
        )

        # --------------------------------------------------
        # Chronological ordering
        # --------------------------------------------------

        cleaned.sort(
            key=lambda item:
                item["index"]
        )

        return cleaned

    # ======================================================
    # Select Latest Confirmed Sweep
    #
    # IMPORTANT:
    #
    # There is NO age filter.
    #
    # The latest confirmed sweep becomes active regardless
    # of how many candles have passed since it occurred.
    # ======================================================

    def _select_active_liquidity(
        self,
        data,
        signals
    ):

        if not signals:

            return None

        # --------------------------------------------------
        # Always use the latest chronological sweep.
        # --------------------------------------------------

        latest = max(
            signals,
            key=lambda item:
                item.get(
                    "index",
                    -1
                )
        )

        latest_index = len(data) - 1

        sweep_index = int(
            latest.get(
                "index",
                -1
            )
        )

        age = (
            latest_index -
            sweep_index
        )

        # --------------------------------------------------
        # Copy the signal so we do not mutate the original
        # object unexpectedly.
        # --------------------------------------------------

        active = dict(
            latest
        )

        active["age"] = age

        active["status"] = "ACTIVE"

        active["active"] = True

        # --------------------------------------------------
        # Save current active liquidity.
        # --------------------------------------------------

        self.active_liquidity = active

        return active

    # ======================================================
    # Get Active Liquidity
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
    # Public Detection
    # ======================================================

    def detect(
        self,
        data
    ):

        print(
            "Checking Liquidity Sweep V2.2..."
        )

        # --------------------------------------------------
        # Validate
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Swing Detection
        # --------------------------------------------------

        swing_highs, swing_lows = (
            self.find_swings(data)
        )

        print(
            f"Swing Highs : "
            f"{len(swing_highs)}"
        )

        print(
            f"Swing Lows  : "
            f"{len(swing_lows)}"
        )

        # --------------------------------------------------
        # Raw Sweep Detection
        # --------------------------------------------------

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

        # --------------------------------------------------
        # Duplicate Cleanup
        # --------------------------------------------------

        cleaned_signals = (
            self._deduplicate_sweeps(
                raw_signals
            )
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
                    f"{signal['type']} | "

                    f"Index : "
                    f"{signal['index']} | "

                    f"Price : "
                    f"{signal['price']} | "

                    f"Time : "
                    f"{signal['time']}"

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
        #
        # Latest confirmed sweep remains active until a
        # newer confirmed sweep appears.
        # ==================================================

        active_liquidity = (
            self._select_active_liquidity(
                data,
                cleaned_signals
            )
        )

        # --------------------------------------------------
        # Active Liquidity Debug
        # --------------------------------------------------

        print(
            "\n========== "
            "ACTIVE LIQUIDITY DEBUG "
            "=========="
        )

        if active_liquidity:

            print(

                f"Type  : "
                f"{active_liquidity['type']}"

            )

            print(

                f"Index : "
                f"{active_liquidity['index']}"

            )

            print(

                f"Price : "
                f"{active_liquidity['price']}"

            )

            print(

                f"Time  : "
                f"{active_liquidity['time']}"

            )

            print(

                f"Age   : "
                f"{active_liquidity['age']} candles"

            )

            print(
                "Status: ACTIVE"
            )

            print(
                "Rule  : "
                "Active until a newer sweep occurs"
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
        # IMPORTANT:
        #
        # Only the active/latest sweep is returned.
        #
        # Historical sweeps remain available internally
        # through clean detection, but downstream engines
        # receive the current active liquidity event.
        # ==================================================

        if active_liquidity:

            return [
                active_liquidity
            ]

        return []

    # ======================================================
    # Get Latest Sweep
    # ======================================================

    @staticmethod
    def get_latest_sweep(
        signals
    ):

        if not signals:

            return None

        return max(
            signals,
            key=lambda item:
                item.get(
                    "index",
                    -1
                )
        )

    # ======================================================
    # Get Active Sweep
    #
    # Compatibility helper for CHoCH / Confluence.
    # ======================================================

    @staticmethod
    def get_active_sweep(
        signals
    ):

        if not signals:

            return None

        return max(
            signals,
            key=lambda item:
                item.get(
                    "index",
                    -1
                )
        )

    # ======================================================
    # Engine Information
    # ======================================================

    def version(self):

        return {

            "engine":
                "Liquidity Sweep V2",

            "version":
                "V2.2",

            "status":
                "Production",

            "confirmation_zone":
                None,

            "active_liquidity_rule":
                "Latest confirmed sweep remains active until a newer sweep occurs",

            "developer":
                "Liquidity Hunter AI"

        }

    # ======================================================
    # Self Test
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
            "Confirmation Zone :",
            info["confirmation_zone"]
        )

        print(
            "Active Liquidity Rule :",
            info["active_liquidity_rule"]
        )

        print(
            "==========================================\n"
        )

        return True