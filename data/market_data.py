"""
============================================================
Liquidity Hunter AI
Market Data Engine V20.6
============================================================

Responsibilities
----------------
• Provider abstraction
• Historical candle loading
• 1000 candle support
• Timeframe management
• Smart cache
• Force refresh
• Live price
• Data normalization
• Provider capability validation
============================================================
"""

from __future__ import annotations

import pandas as pd

from providers.yahoo_provider import YahooProvider


class MarketData:

    # ======================================================
    # Configuration
    # ======================================================

    DEFAULT_TIMEFRAME = "5m"

    MAX_CANDLES = 1000

    # ======================================================
    # INIT
    # ======================================================

    def __init__(
        self,
        symbol,
        provider=None
    ):

        self.symbol = symbol

        # --------------------------------------------------
        # Default provider
        # --------------------------------------------------

        if provider is None:

            provider = YahooProvider()

        self.provider = provider

        # --------------------------------------------------
        # Provider connection
        # --------------------------------------------------

        self.provider.connect()

        # --------------------------------------------------
        # Smart Cache
        #
        # Key:
        #     (symbol, timeframe)
        #
        # Example:
        #     ("B-BTC_USDT", "5m")
        # --------------------------------------------------

        self.cache = {}

        print(
            "Market Data Engine V20.6 Initialized"
        )

        print(
            "Symbol :",
            self.symbol
        )

        print(
            "Max Candles :",
            self.MAX_CANDLES
        )

    # ======================================================
    # Normalize Timeframe
    # ======================================================

    def _normalize_timeframe(
        self,
        timeframe
    ):

        if timeframe is None:

            timeframe = (
                self.DEFAULT_TIMEFRAME
            )

        timeframe = str(
            timeframe
        ).strip()

        # --------------------------------------------------
        # Common aliases
        # --------------------------------------------------

        aliases = {

            "1M": "1m",
            "3M": "3m",
            "5M": "5m",
            "15M": "15m",
            "30M": "30m",

            "1H": "1h",
            "2H": "2h",
            "4H": "4h",
            "6H": "6h",
            "8H": "8h",
            "12H": "12h",

            "1D": "1d",

        }

        timeframe = aliases.get(
            timeframe,
            timeframe
        )

        return timeframe

    # ======================================================
    # Validate Timeframe
    # ======================================================

    def _validate_timeframe(
        self,
        timeframe
    ):

        timeframe = (
            self._normalize_timeframe(
                timeframe
            )
        )

        try:

            if hasattr(
                self.provider,
                "validate_timeframe"
            ):

                valid = (
                    self.provider
                    .validate_timeframe(
                        timeframe
                    )
                )

                if not valid:

                    raise ValueError(
                        f"Unsupported timeframe: "
                        f"{timeframe}"
                    )

            else:

                capabilities = (
                    self.provider
                    .get_capabilities()
                )

                supported = (
                    capabilities.get(
                        "supported_timeframes",
                        []
                    )
                )

                if (
                    timeframe
                    not in supported
                ):

                    raise ValueError(
                        f"Unsupported timeframe: "
                        f"{timeframe}"
                    )

        except Exception:

            raise

        return timeframe

    # ======================================================
    # Provider Timeframe
    # ======================================================

    def _get_api_timeframe(
        self,
        timeframe
    ):

        """
        IMPORTANT

        Old architecture converted:

            5m -> 1m

        That behavior is removed.

        MarketData now passes the requested timeframe
        directly to the provider.

        The provider itself decides whether the timeframe
        is native or needs local aggregation.
        """

        timeframe = (
            self._validate_timeframe(
                timeframe
            )
        )

        return timeframe

    # ======================================================
    # Normalize DataFrame
    # ======================================================

    def _normalize_dataframe(
        self,
        dataframe
    ):

        if dataframe is None:

            return pd.DataFrame()

        if not isinstance(
            dataframe,
            pd.DataFrame
        ):

            return pd.DataFrame()

        if dataframe.empty:

            return dataframe.copy()

        df = dataframe.copy()

        # --------------------------------------------------
        # Datetime Index
        # --------------------------------------------------

        if not isinstance(
            df.index,
            pd.DatetimeIndex
        ):

            df.index = pd.to_datetime(
                df.index,
                utc=True
            )

        else:

            if df.index.tz is None:

                df.index = (
                    df.index
                    .tz_localize("UTC")
                )

            else:

                df.index = (
                    df.index
                    .tz_convert("UTC")
                )

        # --------------------------------------------------
        # Sort
        # --------------------------------------------------

        df = df.sort_index()

        # --------------------------------------------------
        # Duplicate timestamps
        # --------------------------------------------------

        df = (
            df[
                ~df.index.duplicated(
                    keep="last"
                )
            ]
        )

        # --------------------------------------------------
        # Required OHLCV columns
        # --------------------------------------------------

        required_columns = [

            "Open",
            "High",
            "Low",
            "Close",
            "Volume",

        ]

        for column in required_columns:

            if column in df.columns:

                df[column] = pd.to_numeric(
                    df[column],
                    errors="coerce"
                )

        # --------------------------------------------------
        # Remove invalid OHLC rows
        # --------------------------------------------------

        existing_columns = [

            column
            for column
            in required_columns
            if column in df.columns

        ]

        if existing_columns:

            df = df.dropna(
                subset=existing_columns
            )

        return df

    # ======================================================
    # Load Data
    # ======================================================

    def load_data(
        self,
        timeframe="5m",
        force_refresh=False
    ):

        timeframe = (
            self._normalize_timeframe(
                timeframe
            )
        )

        print(
            "\n" + "=" * 60
        )

        print(
            "MarketData.load_data()"
        )

        print(
            "Symbol        :",
            self.symbol
        )

        print(
            "Timeframe     :",
            timeframe
        )

        print(
            "Force Refresh :",
            force_refresh
        )

        print(
            "Requested     :",
            self.MAX_CANDLES
        )

        print(
            "=" * 60
        )

        # ==================================================
        # Cache Key
        # ==================================================

        cache_key = (
            self.symbol,
            timeframe
        )

        # ==================================================
        # Cache
        # ==================================================

        if (

            not force_refresh

            and

            cache_key
            in self.cache

        ):

            print(
                "Using Cached Data"
            )

            cached_data = (
                self.cache[
                    cache_key
                ]
            )

            print(
                "Cached Rows :",
                len(cached_data)
            )

            return cached_data.copy()

        # ==================================================
        # Validate / Get Provider Timeframe
        # ==================================================

        api_timeframe = (
            self._get_api_timeframe(
                timeframe
            )
        )

        print(
            "Provider Timeframe :",
            api_timeframe
        )

        # ==================================================
        # Request Historical Data
        # ==================================================

        try:

            data = (
                self.provider.get_candles(
                    self.symbol,
                    api_timeframe,
                    limit=self.MAX_CANDLES
                )
            )

        except TypeError:

            # ------------------------------------------------
            # Compatibility fallback for older providers
            # which do not accept limit.
            # ------------------------------------------------

            print(
                "Provider does not accept "
                "limit parameter."
            )

            data = (
                self.provider.get_candles(
                    self.symbol,
                    api_timeframe
                )
            )

        except Exception:

            print(
                "MarketData candle request failed."
            )

            raise

        # ==================================================
        # Empty Data
        # ==================================================

        if data is None:

            print(
                "No candle data received: None"
            )

            return pd.DataFrame()

        if data.empty:

            print(
                "No candle data received: Empty"
            )

            return data

        # ==================================================
        # Normalize
        # ==================================================

        data = (
            self._normalize_dataframe(
                data
            )
        )

        # ==================================================
        # Final History Limit
        # ==================================================

        if len(data) > self.MAX_CANDLES:

            data = data.iloc[
                -self.MAX_CANDLES:
            ]

        # ==================================================
        # Cache
        # ==================================================

        self.cache[
            cache_key
        ] = data.copy()

        # ==================================================
        # Debug
        # ==================================================

        print(
            "\n========== MARKET DATA RESULT =========="
        )

        print(
            "Symbol       :",
            self.symbol
        )

        print(
            "Timeframe    :",
            timeframe
        )

        print(
            "Provider TF  :",
            api_timeframe
        )

        print(
            "Rows         :",
            len(data)
        )

        if not data.empty:

            print(
                "First Candle :",
                data.index[0]
            )

            print(
                "Last Candle  :",
                data.index[-1]
            )

        print(
            "=========================================\n"
        )

        print(
            data.tail()
        )

        return data.copy()

    # ======================================================
    # Refresh Cache
    # ======================================================

    def refresh_cache(
        self,
        timeframe
    ):

        print(
            "\nRefreshing cache for:",
            timeframe
        )

        return self.load_data(
            timeframe=timeframe,
            force_refresh=True
        )

    # ======================================================
    # Clear Cache
    # ======================================================

    def clear_cache(self):

        print(
            "Clearing MarketData cache..."
        )

        self.cache.clear()

        print(
            "MarketData cache cleared."
        )

    # ======================================================
    # Clear Specific Timeframe
    # ======================================================

    def clear_timeframe_cache(
        self,
        timeframe
    ):

        timeframe = (
            self._normalize_timeframe(
                timeframe
            )
        )

        cache_key = (
            self.symbol,
            timeframe
        )

        if cache_key in self.cache:

            del self.cache[
                cache_key
            ]

            print(
                "Cache cleared:",
                cache_key
            )

    # ======================================================
    # Change Symbol
    # ======================================================

    def set_symbol(
        self,
        symbol
    ):

        if not symbol:

            return

        if symbol == self.symbol:

            return

        print(
            "\nMarketData Symbol Change:"
        )

        print(
            "Old :",
            self.symbol
        )

        print(
            "New :",
            symbol
        )

        self.symbol = symbol

        # Symbol-specific cache must be removed.
        self.clear_cache()

    # ======================================================
    # Live Price
    # ======================================================

    def get_live_price(self):

        try:

            return (
                self.provider.get_live_price(
                    self.symbol
                )
            )

        except Exception:

            print(
                "Failed to get live price."
            )

            raise

    # ======================================================
    # Provider Capabilities
    # ======================================================

    def get_capabilities(self):

        try:

            return (
                self.provider
                .get_capabilities()
            )

        except Exception:

            return {}

    # ======================================================
    # Provider Health
    # ======================================================

    def health_check(self):

        try:

            if hasattr(
                self.provider,
                "health_check"
            ):

                return (
                    self.provider
                    .health_check()
                )

        except Exception:

            pass

        return {

            "provider":
                type(
                    self.provider
                ).__name__,

            "status":
                "unknown",

        }

    # ======================================================
    # Disconnect
    # ======================================================

    def disconnect(self):

        print(
            "\nDisconnecting MarketData..."
        )

        self.clear_cache()

        try:

            self.provider.disconnect()

        except Exception:

            pass

        print(
            "MarketData disconnected."
        )

    # ======================================================
    # Debug Summary
    # ======================================================

    def debug_summary(self):

        print(
            "\n========== MARKET DATA SUMMARY =========="
        )

        print(
            "Symbol       :",
            self.symbol
        )

        print(
            "Max Candles  :",
            self.MAX_CANDLES
        )

        print(
            "Provider     :",
            type(
                self.provider
            ).__name__
        )

        print(
            "Cache Items  :",
            len(self.cache)
        )

        for key, data in self.cache.items():

            print(
                f"{key} -> "
                f"{len(data)} candles"
            )

        print(
            "=========================================\n"
        )