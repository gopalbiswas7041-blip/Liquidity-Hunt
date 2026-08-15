"""
============================================================
Liquidity Hunter AI
CoinDCX Provider V20.8
============================================================

Responsibilities
----------------
• CoinDCX REST connection
• Live price
• Historical candles
• 1000 final candle support
• CoinDCX runtime-compatible intervals
• Derived timeframe aggregation
• Multi-request historical pagination
• Robust pagination range protection
• DataFrame normalization
• Symbol normalization
• Gold / Silver / BTC / ETH support
• Provider capabilities
• Duplicate protection
• Safe API error reporting

Supported Markets
-----------------
    B-BTC_USDT   -> Bitcoin
    B-ETH_USDT   -> Ethereum
    B-XAU_USDT   -> Gold
    B-XAG_USDT   -> Silver

IMPORTANT
---------
Current CoinDCX candle endpoint observed at runtime
accepts these intervals:

    1m
    15m
    1h
    1d

Therefore all other application timeframes are derived
locally from these source intervals.

Examples:

    3m  <- 1m
    5m  <- 1m
    30m <- 15m
    2h  <- 1h
    4h  <- 1h
    6h  <- 1h
    8h  <- 1h
    12h <- 1h

Final application output:
    Maximum 1000 candles
============================================================
"""

from __future__ import annotations

import time

import pandas as pd
import requests

from providers.base_provider import BaseProvider


class CoinDCXProvider(BaseProvider):

    # ======================================================
    # Configuration
    # ======================================================

    BASE_URL = (
        "https://public.coindcx.com"
    )

    TICKER_URL = (
        "https://api.coindcx.com/exchange/ticker"
    )

    CANDLE_ENDPOINT = (
        "/market_data/candles"
    )

    # ------------------------------------------------------
    # Maximum candles returned by CoinDCX per request.
    # ------------------------------------------------------

    MAX_API_CANDLES = 1000

    # ------------------------------------------------------
    # Maximum candles returned to Liquidity Hunter AI.
    # ------------------------------------------------------

    MAX_CANDLES = 1000

    # ------------------------------------------------------
    # HTTP timeout
    # ------------------------------------------------------

    REQUEST_TIMEOUT = 15

    # ------------------------------------------------------
    # Small delay between pagination requests.
    # ------------------------------------------------------

    REQUEST_DELAY = 0.10

    # ------------------------------------------------------
    # Maximum pagination requests.
    # ------------------------------------------------------

    MAX_PAGINATION_REQUESTS = 20

    # ======================================================
    # SUPPORTED MARKET SYMBOLS
    # ======================================================
    #
    # These are the canonical CoinDCX symbols used internally.
    #
    # IMPORTANT:
    # BTC is NOT removed.
    #
    # GOLD / SILVER / ETH / BTC are all supported.
    # ======================================================

    SUPPORTED_SYMBOLS = [

        "B-XAU_USDT",     # GOLD

        "B-BTC_USDT",     # BITCOIN

        "B-ETH_USDT",     # ETHEREUM

        "B-XAG_USDT",     # SILVER

    ]

    # ======================================================
    # MARKET NAMES
    # ======================================================

    MARKET_NAMES = {

        "B-XAU_USDT":
            "GOLD",

        "B-BTC_USDT":
            "BTC",

        "B-ETH_USDT":
            "ETH",

        "B-XAG_USDT":
            "SILVER",

    }

    # ======================================================
    # ACTUAL COINDCX RUNTIME SOURCE TIMEFRAMES
    # ======================================================

    SOURCE_TIMEFRAMES = {

        "1m": "1m",

        "15m": "15m",

        "1h": "1h",

        "1d": "1d",

    }

    # ======================================================
    # APPLICATION TIMEFRAMES
    # ======================================================

    SUPPORTED_TIMEFRAMES = [

        "1m",
        "3m",
        "5m",
        "15m",
        "30m",
        "1h",
        "2h",
        "4h",
        "6h",
        "8h",
        "12h",
        "1d",

    ]

    # ======================================================
    # DERIVED TIMEFRAME CONFIGURATION
    # ======================================================

    DERIVED_TIMEFRAMES = {

        # ----------------------------------------------
        # 1m -> 3m
        # ----------------------------------------------

        "3m": {

            "source": "1m",

            "rule": "3min",

            "multiplier": 3,

        },

        # ----------------------------------------------
        # 1m -> 5m
        # ----------------------------------------------

        "5m": {

            "source": "1m",

            "rule": "5min",

            "multiplier": 5,

        },

        # ----------------------------------------------
        # 15m -> 30m
        # ----------------------------------------------

        "30m": {

            "source": "15m",

            "rule": "30min",

            "multiplier": 2,

        },

        # ----------------------------------------------
        # 1h -> 2h
        # ----------------------------------------------

        "2h": {

            "source": "1h",

            "rule": "2h",

            "multiplier": 2,

        },

        # ----------------------------------------------
        # 1h -> 4h
        # ----------------------------------------------

        "4h": {

            "source": "1h",

            "rule": "4h",

            "multiplier": 4,

        },

        # ----------------------------------------------
        # 1h -> 6h
        # ----------------------------------------------

        "6h": {

            "source": "1h",

            "rule": "6h",

            "multiplier": 6,

        },

        # ----------------------------------------------
        # 1h -> 8h
        # ----------------------------------------------

        "8h": {

            "source": "1h",

            "rule": "8h",

            "multiplier": 8,

        },

        # ----------------------------------------------
        # 1h -> 12h
        # ----------------------------------------------

        "12h": {

            "source": "1h",

            "rule": "12h",

            "multiplier": 12,

        },

    }

    # ======================================================
    # INIT
    # ======================================================

    def __init__(self):

        self.connected = False

        self.websocket = None

        print(
            "CoinDCX Provider V20.8 Initialized"
        )

        print(
            "Supported Markets :",
            self.SUPPORTED_SYMBOLS
        )

        print(
            "Market Names      :",
            self.MARKET_NAMES
        )

        print(
            "Supported API source TF :",
            list(
                self.SOURCE_TIMEFRAMES.keys()
            )
        )

        print(
            "Application TF count :",
            len(
                self.SUPPORTED_TIMEFRAMES
            )
        )

    # ======================================================
    # CONNECT
    # ======================================================

    def connect(self):

        self.connected = True

        print(
            "CoinDCX Provider Connected"
        )

        return True

    # ======================================================
    # DISCONNECT
    # ======================================================

    def disconnect(self):

        self.connected = False

        print(
            "CoinDCX Provider Disconnected"
        )

    # ======================================================
    # NORMALIZE TIMEFRAME
    # ======================================================

    def normalize_timeframe(
        self,
        timeframe: str
    ) -> str:

        if timeframe is None:

            raise ValueError(
                "Timeframe cannot be None"
            )

        tf = str(
            timeframe
        ).strip()

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

        tf = aliases.get(
            tf,
            tf
        )

        if tf not in (
            self.SUPPORTED_TIMEFRAMES
        ):

            raise ValueError(
                f"Unsupported timeframe: {timeframe}"
            )

        return tf

    # ======================================================
    # NORMALIZE SYMBOL
    # ======================================================

    def normalize_symbol(
        self,
        symbol: str
    ) -> str:

        # --------------------------------------------------
        # Empty symbol
        #
        # Keep BTC as provider-level fallback for backward
        # compatibility.
        #
        # Controller V20.8 explicitly selects GOLD first.
        # --------------------------------------------------

        if not symbol:

            return "B-BTC_USDT"

        symbol = str(
            symbol
        ).strip().upper()

        # ==================================================
        # Canonical symbols
        # ==================================================

        mapping = {

            # ==================================================
            # BITCOIN
            # ==================================================

            "BTCUSDT":
                "B-BTC_USDT",

            "BTC/USDT":
                "B-BTC_USDT",

            "BTC-USDT":
                "B-BTC_USDT",

            "BTC":
                "B-BTC_USDT",

            "B-BTCUSDT":
                "B-BTC_USDT",

            "B-BTC/USDT":
                "B-BTC_USDT",

            "B-BTC-USDT":
                "B-BTC_USDT",

            # ==================================================
            # ETHEREUM
            # ==================================================

            "ETHUSDT":
                "B-ETH_USDT",

            "ETH/USDT":
                "B-ETH_USDT",

            "ETH-USDT":
                "B-ETH_USDT",

            "ETH":
                "B-ETH_USDT",

            "B-ETHUSDT":
                "B-ETH_USDT",

            "B-ETH/USDT":
                "B-ETH_USDT",

            "B-ETH-USDT":
                "B-ETH_USDT",

            # ==================================================
            # GOLD
            # ==================================================

            "XAUUSDT":
                "B-XAU_USDT",

            "XAU/USDT":
                "B-XAU_USDT",

            "XAU-USDT":
                "B-XAU_USDT",

            "XAU":
                "B-XAU_USDT",

            "GOLD":
                "B-XAU_USDT",

            "GOLDUSDT":
                "B-XAU_USDT",

            "GOLD/USDT":
                "B-XAU_USDT",

            "GOLD-USDT":
                "B-XAU_USDT",

            "B-XAUUSDT":
                "B-XAU_USDT",

            "B-XAU/USDT":
                "B-XAU_USDT",

            "B-XAU-USDT":
                "B-XAU_USDT",

            # ==================================================
            # SILVER
            # ==================================================

            "XAGUSDT":
                "B-XAG_USDT",

            "XAG/USDT":
                "B-XAG_USDT",

            "XAG-USDT":
                "B-XAG_USDT",

            "XAG":
                "B-XAG_USDT",

            "SILVER":
                "B-XAG_USDT",

            "SILVERUSDT":
                "B-XAG_USDT",

            "SILVER/USDT":
                "B-XAG_USDT",

            "SILVER-USDT":
                "B-XAG_USDT",

            "B-XAGUSDT":
                "B-XAG_USDT",

            "B-XAG/USDT":
                "B-XAG_USDT",

            "B-XAG-USDT":
                "B-XAG_USDT",

        }

        normalized = mapping.get(
            symbol,
            symbol
        )

        # ==================================================
        # Debug
        # ==================================================

        print(
            "Symbol Normalize :",
            symbol,
            "->",
            normalized
        )

        return normalized

    # ======================================================
    # MARKET NAME
    # ======================================================

    def get_market_name(
        self,
        symbol: str
    ) -> str:

        normalized = (
            self.normalize_symbol(
                symbol
            )
        )

        return self.MARKET_NAMES.get(
            normalized,
            normalized
        )

    # ======================================================
    # VALIDATE SYMBOL
    # ======================================================

    def validate_symbol(
        self,
        symbol: str
    ) -> bool:

        try:

            normalized = (
                self.normalize_symbol(
                    symbol
                )
            )

            return (
                normalized
                in
                self.SUPPORTED_SYMBOLS
            )

        except Exception:

            return False

    # ======================================================
    # LIVE PRICE
    # ======================================================

    def get_live_price(
        self,
        symbol
    ):

        symbol = (
            self.normalize_symbol(
                symbol
            )
        )

        print(
            "\nCoinDCX Live Price Request"
        )

        print(
            "Symbol :",
            symbol
        )

        response = requests.get(
            self.TICKER_URL,
            timeout=self.REQUEST_TIMEOUT
        )

        response.raise_for_status()

        tickers = response.json()

        if not isinstance(
            tickers,
            list
        ):

            raise ValueError(
                "Unexpected CoinDCX ticker response."
            )

        for ticker in tickers:

            if (
                ticker.get("market")
                == symbol
            ):

                return float(
                    ticker["last_price"]
                )

        raise ValueError(
            f"Market '{symbol}' not found."
        )

    # ======================================================
    # RAW CANDLE REQUEST
    # ======================================================

    def _request_candles(
        self,
        symbol: str,
        interval: str,
        limit: int = 1000,
        start_time: int | None = None,
        end_time: int | None = None,
    ):

        symbol = (
            self.normalize_symbol(
                symbol
            )
        )

        # --------------------------------------------------
        # Safety
        # --------------------------------------------------

        limit = max(
            1,
            min(
                int(limit),
                self.MAX_API_CANDLES
            )
        )

        # --------------------------------------------------
        # Validate source interval
        # --------------------------------------------------

        if interval not in (
            self.SOURCE_TIMEFRAMES
        ):

            raise ValueError(
                "Invalid CoinDCX source interval: "
                f"{interval}"
            )

        # --------------------------------------------------
        # Validate market
        # --------------------------------------------------

        if not self.validate_symbol(
            symbol
        ):

            print(
                "WARNING:"
                " Symbol is not in provider"
                " supported symbol registry:",
                symbol
            )

        url = (
            f"{self.BASE_URL}"
            f"{self.CANDLE_ENDPOINT}"
        )

        params = {

            "pair":
                symbol,

            "interval":
                interval,

            "limit":
                limit,

        }

        if start_time is not None:

            params["startTime"] = int(
                start_time
            )

        if end_time is not None:

            params["endTime"] = int(
                end_time
            )

        print(
            "\n------------------------------------------"
        )

        print(
            "CoinDCX Candle Request"
        )

        print(
            "Pair     :",
            symbol
        )

        print(
            "Market   :",
            self.get_market_name(
                symbol
            )
        )

        print(
            "Interval :",
            interval
        )

        print(
            "Limit    :",
            limit
        )

        if start_time is not None:

            print(
                "Start    :",
                start_time
            )

        if end_time is not None:

            print(
                "End      :",
                end_time
            )

        print(
            "------------------------------------------"
        )

        response = requests.get(
            url,
            params=params,
            timeout=self.REQUEST_TIMEOUT
        )

        print(
            "URL      :",
            response.url
        )

        print(
            "Status   :",
            response.status_code
        )

        if response.status_code != 200:

            print(
                "Response Body :",
                response.text
            )

        response.raise_for_status()

        candles = response.json()

        if not isinstance(
            candles,
            list
        ):

            raise ValueError(
                "Unexpected CoinDCX candle response."
            )

        print(
            "Received Candles :",
            len(candles)
        )

        return candles

    # ======================================================
    # CANDLES -> DATAFRAME
    # ======================================================

    def _candles_to_dataframe(
        self,
        candles
    ):

        if not candles:

            return pd.DataFrame()

        df = pd.DataFrame(
            candles
        )

        if df.empty:

            return df

        # --------------------------------------------------
        # Rename CoinDCX columns
        # --------------------------------------------------

        df.rename(
            columns={

                "time":
                    "Datetime",

                "open":
                    "Open",

                "high":
                    "High",

                "low":
                    "Low",

                "close":
                    "Close",

                "volume":
                    "Volume",

            },
            inplace=True
        )

        required_columns = [

            "Datetime",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",

        ]

        missing = [

            column

            for column
            in required_columns

            if column
            not in df.columns

        ]

        if missing:

            raise ValueError(
                "Missing candle columns: "
                + str(missing)
            )

        # --------------------------------------------------
        # Timestamp
        # --------------------------------------------------

        df["Datetime"] = pd.to_datetime(
            df["Datetime"],
            unit="ms",
            utc=True
        )

        # --------------------------------------------------
        # Numeric
        # --------------------------------------------------

        numeric_columns = [

            "Open",
            "High",
            "Low",
            "Close",
            "Volume",

        ]

        for column in numeric_columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )

        # --------------------------------------------------
        # Remove invalid rows
        # --------------------------------------------------

        df.dropna(
            subset=required_columns,
            inplace=True
        )

        # --------------------------------------------------
        # Sort ascending
        # --------------------------------------------------

        df.sort_values(
            "Datetime",
            inplace=True
        )

        # --------------------------------------------------
        # Index
        # --------------------------------------------------

        df.set_index(
            "Datetime",
            inplace=True
        )

        df.index.name = "Datetime"

        # --------------------------------------------------
        # Duplicate protection
        # --------------------------------------------------

        df = (
            df[
                ~df.index.duplicated(
                    keep="last"
                )
            ]
        )

        return df

    # ======================================================
    # AGGREGATE DATAFRAME
    # ======================================================

    def _aggregate_dataframe(
        self,
        df,
        rule: str
    ):

        if df is None:

            return pd.DataFrame()

        if df.empty:

            return df

        result = (
            df[
                [
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume",
                ]
            ]
            .resample(
                rule,
                origin="epoch"
            )
            .agg({

                "Open":
                    "first",

                "High":
                    "max",

                "Low":
                    "min",

                "Close":
                    "last",

                "Volume":
                    "sum",

            })
            .dropna()
        )

        result = (
            result.sort_index()
        )

        result = (
            result[
                ~result.index.duplicated(
                    keep="last"
                )
            ]
        )

        return result

    # ======================================================
    # PAGINATED SOURCE CANDLES
    # ======================================================

    def _get_source_candles(
        self,
        symbol,
        source_timeframe,
        required_count
    ):

        if source_timeframe not in (
            self.SOURCE_TIMEFRAMES
        ):

            raise ValueError(
                "Unsupported source timeframe: "
                f"{source_timeframe}"
            )

        required_count = max(
            1,
            int(required_count)
        )

        chunks = []

        remaining = required_count

        # --------------------------------------------------
        # None = latest available candles.
        # --------------------------------------------------

        end_time = None

        total_received = 0

        request_number = 0

        # --------------------------------------------------
        # Global set of timestamps.
        # --------------------------------------------------

        collected_timestamps = set()

        # ==================================================
        # PAGINATION LOOP
        # ==================================================

        while remaining > 0:

            request_number += 1

            # --------------------------------------------------
            # Safety protection
            # --------------------------------------------------

            if (
                request_number
                > self.MAX_PAGINATION_REQUESTS
            ):

                print(
                    "\n⚠️ MAX PAGINATION REQUEST LIMIT REACHED"
                )

                print(
                    "Requests :",
                    request_number - 1
                )

                print(
                    "Collected:",
                    len(
                        collected_timestamps
                    )
                )

                break

            request_limit = min(
                remaining,
                self.MAX_API_CANDLES
            )

            print(
                "\n=========================================="
            )

            print(
                "Historical Chunk Request #",
                request_number
            )

            print(
                "Source TF :",
                source_timeframe
            )

            print(
                "Need     :",
                remaining
            )

            print(
                "Request  :",
                request_limit
            )

            print(
                "Current End Time :",
                end_time
            )

            print(
                "=========================================="
            )

            # ==================================================
            # REQUEST
            # ==================================================

            candles = (
                self._request_candles(
                    symbol=symbol,
                    interval=source_timeframe,
                    limit=request_limit,
                    end_time=end_time
                )
            )

            if not candles:

                print(
                    "No more candles returned."
                )

                break

            # ==================================================
            # CONVERT CHUNK
            # ==================================================

            chunk = (
                self._candles_to_dataframe(
                    candles
                )
            )

            if chunk.empty:

                print(
                    "Empty chunk received."
                )

                break

            # ==================================================
            # CHUNK RANGE DEBUG
            # ==================================================

            chunk_first = (
                chunk.index.min()
            )

            chunk_last = (
                chunk.index.max()
            )

            print(
                "\n---------- CHUNK RANGE ----------"
            )

            print(
                "Chunk #     :",
                request_number
            )

            print(
                "Rows        :",
                len(chunk)
            )

            print(
                "Oldest      :",
                chunk_first
            )

            print(
                "Newest      :",
                chunk_last
            )

            print(
                "=================================\n"
            )

            # ==================================================
            # CHECK FOR DUPLICATE CHUNK
            # ==================================================

            chunk_timestamps = set(
                chunk.index
            )

            new_timestamps = (
                chunk_timestamps
                - collected_timestamps
            )

            if not new_timestamps:

                print(
                    "\n⚠️ DUPLICATE HISTORICAL CHUNK"
                )

                print(
                    "CoinDCX returned a range "
                    "already collected."
                )

                print(
                    "Chunk # :",
                    request_number
                )

                print(
                    "Range   :",
                    chunk_first,
                    "->",
                    chunk_last
                )

                print(
                    "Pagination stopped safely."
                )

                break

            # ==================================================
            # FILTER ONLY NEW CANDLES
            # ==================================================

            new_chunk = (
                chunk[
                    chunk.index.isin(
                        new_timestamps
                    )
                ]
                .copy()
            )

            # --------------------------------------------------
            # Extra safety
            # --------------------------------------------------

            if new_chunk.empty:

                print(
                    "No new candles found."
                )

                break

            # ==================================================
            # STORE
            # ==================================================

            chunks.append(
                new_chunk
            )

            # --------------------------------------------------
            # Update global timestamp registry
            # --------------------------------------------------

            collected_timestamps.update(
                new_timestamps
            )

            received = len(
                new_chunk
            )

            total_received += (
                received
            )

            remaining -= (
                received
            )

            print(
                "New Candles      :",
                received
            )

            print(
                "Total Unique     :",
                total_received
            )

            print(
                "Remaining        :",
                max(
                    0,
                    remaining
                )
            )

            # ==================================================
            # PAGINATION CURSOR
            # ==================================================

            oldest_timestamp = (
                new_chunk.index.min()
            )

            oldest_ms = int(
                oldest_timestamp.timestamp()
                * 1000
            )

            next_end_time = (
                oldest_ms - 1
            )

            # --------------------------------------------------
            # Cursor protection
            # --------------------------------------------------

            if (
                end_time is not None
                and next_end_time >= end_time
            ):

                print(
                    "\n⚠️ PAGINATION CURSOR DID NOT MOVE"
                )

                print(
                    "Previous End :",
                    end_time
                )

                print(
                    "Next End     :",
                    next_end_time
                )

                print(
                    "Pagination stopped safely."
                )

                break

            # --------------------------------------------------
            # Set next cursor
            # --------------------------------------------------

            end_time = (
                next_end_time
            )

            print(
                "\nNext Historical End Time :",
                end_time
            )

            print(
                "Next request will search "
                "OLDER candles."
            )

            # ==================================================
            # API returned fewer candles
            # ==================================================

            if received < request_limit:

                print(
                    "\nAPI returned fewer NEW candles "
                    "than requested."
                )

                print(
                    "This may indicate the available "
                    "historical range has been exhausted."
                )

                break

            # ==================================================
            # DELAY
            # ==================================================

            if remaining > 0:

                time.sleep(
                    self.REQUEST_DELAY
                )

        # ==================================================
        # NO CHUNKS
        # ==================================================

        if not chunks:

            print(
                "\n⚠️ No historical chunks collected."
            )

            return pd.DataFrame()

        # ==================================================
        # MERGE
        # ==================================================

        df = pd.concat(
            chunks
        )

        # ==================================================
        # SORT
        # ==================================================

        df = (
            df.sort_index()
        )

        # ==================================================
        # DUPLICATE PROTECTION
        # ==================================================

        df = (
            df[
                ~df.index.duplicated(
                    keep="last"
                )
            ]
        )

        # ==================================================
        # FINAL UNIQUE COUNT
        # ==================================================

        unique_count = len(
            df
        )

        print(
            "\n=========================================="
        )

        print(
            "SOURCE COLLECTION COMPLETE"
        )

        print(
            "Source TF        :",
            source_timeframe
        )

        print(
            "Required         :",
            required_count
        )

        print(
            "Unique Collected :",
            unique_count
        )

        print(
            "Shortfall        :",
            max(
                0,
                required_count
                - unique_count
            )
        )

        if not df.empty:

            print(
                "First            :",
                df.index[0]
            )

            print(
                "Last             :",
                df.index[-1]
            )

        print(
            "=========================================="
        )

        # ==================================================
        # IMPORTANT VALIDATION
        # ==================================================

        if (
            unique_count
            < required_count
        ):

            print(
                "\n⚠️ WARNING:"
            )

            print(
                "Requested source candles were not "
                "fully collected."
            )

            print(
                "This is NOT an aggregation error."
            )

            print(
                "Available unique source candles :",
                unique_count
            )

            print(
                "Required source candles          :",
                required_count
            )

        else:

            print(
                "\n✅ REQUIRED SOURCE CANDLE COUNT REACHED"
            )

        print(
            "=================================\n"
        )

        return df

    # ======================================================
    # NATIVE CANDLES
    # ======================================================

    def _get_native_candles(
        self,
        symbol,
        timeframe,
        limit
    ):

        print(
            "\nNative timeframe:",
            timeframe
        )

        return self._get_source_candles(
            symbol=symbol,
            source_timeframe=timeframe,
            required_count=limit
        )

    # ======================================================
    # DERIVED CANDLES
    # ======================================================

    def _get_derived_candles(
        self,
        symbol,
        timeframe,
        limit
    ):

        config = (
            self.DERIVED_TIMEFRAMES[
                timeframe
            ]
        )

        source_timeframe = (
            config["source"]
        )

        rule = (
            config["rule"]
        )

        multiplier = int(
            config["multiplier"]
        )

        # ==================================================
        # SOURCE CANDLE REQUIREMENT
        # ==================================================

        safety_margin = (
            multiplier * 2
        )

        source_required = (
            limit * multiplier
            + safety_margin
        )

        print(
            "\n=========================================="
        )

        print(
            "Derived Timeframe Request"
        )

        print(
            "Target TF       :",
            timeframe
        )

        print(
            "Source TF       :",
            source_timeframe
        )

        print(
            "Aggregation     :",
            rule
        )

        print(
            "Target Candles  :",
            limit
        )

        print(
            "Source Required :",
            source_required
        )

        print(
            "=========================================="
        )

        # ==================================================
        # DOWNLOAD SOURCE CANDLES
        # ==================================================

        source_df = (
            self._get_source_candles(
                symbol=symbol,
                source_timeframe=source_timeframe,
                required_count=source_required
            )
        )

        if source_df.empty:

            print(
                "No source candles available."
            )

            return pd.DataFrame()

        # ==================================================
        # SOURCE COUNT DEBUG
        # ==================================================

        print(
            "\n=========================================="
        )

        print(
            "DERIVED SOURCE VALIDATION"
        )

        print(
            "Source TF      :",
            source_timeframe
        )

        print(
            "Required       :",
            source_required
        )

        print(
            "Received       :",
            len(source_df)
        )

        if len(source_df) >= source_required:

            print(
                "Status         : ✅ READY"
            )

        else:

            print(
                "Status         : ⚠️ SHORT SOURCE DATA"
            )

        print(
            "=========================================="
        )

        # ==================================================
        # AGGREGATE
        # ==================================================

        result = (
            self._aggregate_dataframe(
                source_df,
                rule
            )
        )

        if result.empty:

            return result

        # ==================================================
        # FINAL DUPLICATE PROTECTION
        # ==================================================

        result = (
            result[
                ~result.index.duplicated(
                    keep="last"
                )
            ]
        )

        # ==================================================
        # SORT
        # ==================================================

        result = (
            result.sort_index()
        )

        # ==================================================
        # FINAL 1000 CANDLE LIMIT
        # ==================================================

        if len(result) > limit:

            result = result.iloc[
                -limit:
            ].copy()

        # ==================================================
        # DERIVED RESULT
        # ==================================================

        print(
            "\n========== DERIVED RESULT =========="
        )

        print(
            "Target TF :",
            timeframe
        )

        print(
            "Returned  :",
            len(result)
        )

        if not result.empty:

            print(
                "First     :",
                result.index[0]
            )

            print(
                "Last      :",
                result.index[-1]
            )

        print(
            "====================================\n"
        )

        return result

    # ======================================================
    # PUBLIC: GET CANDLES
    # ======================================================

    def get_candles(
        self,
        symbol,
        timeframe,
        limit=1000
    ):

        # ==================================================
        # NORMALIZE TIMEFRAME
        # ==================================================

        original_timeframe = (
            self.normalize_timeframe(
                timeframe
            )
        )

        # ==================================================
        # LIMIT
        # ==================================================

        limit = max(
            1,
            min(
                int(limit),
                self.MAX_CANDLES
            )
        )

        # ==================================================
        # NORMALIZE SYMBOL
        # ==================================================

        symbol = (
            self.normalize_symbol(
                symbol
            )
        )

        print(
            "\n"
            + "=" * 60
        )

        print(
            "CoinDCX Historical Candles V20.8"
        )

        print(
            "Symbol    :",
            symbol
        )

        print(
            "Market    :",
            self.get_market_name(
                symbol
            )
        )

        print(
            "Timeframe :",
            original_timeframe
        )

        print(
            "Requested :",
            limit
        )

        print(
            "=" * 60
        )

        # ==================================================
        # NATIVE SOURCE TIMEFRAME
        # ==================================================

        if (
            original_timeframe
            in self.SOURCE_TIMEFRAMES
        ):

            df = (
                self._get_native_candles(
                    symbol=symbol,
                    timeframe=original_timeframe,
                    limit=limit
                )
            )

        # ==================================================
        # DERIVED TIMEFRAME
        # ==================================================

        else:

            df = (
                self._get_derived_candles(
                    symbol=symbol,
                    timeframe=original_timeframe,
                    limit=limit
                )
            )

        # ==================================================
        # EMPTY
        # ==================================================

        if df is None:

            print(
                "No candle data received: None"
            )

            return pd.DataFrame()

        if df.empty:

            print(
                "No candle data received: Empty"
            )

            return df

        # ==================================================
        # FINAL NORMALIZATION
        # ==================================================

        df = (
            df.sort_index()
        )

        df = (
            df[
                ~df.index.duplicated(
                    keep="last"
                )
            ]
        )

        # ==================================================
        # FINAL 1000 SAFETY LIMIT
        # ==================================================

        if len(df) > limit:

            df = df.iloc[
                -limit:
            ].copy()

        # ==================================================
        # FINAL RESULT
        # ==================================================

        print(
            "\n"
            + "=" * 60
        )

        print(
            "FINAL CANDLE RESULT"
        )

        print(
            "Symbol    :",
            symbol
        )

        print(
            "Market    :",
            self.get_market_name(
                symbol
            )
        )

        print(
            "Timeframe :",
            original_timeframe
        )

        print(
            "Requested :",
            limit
        )

        print(
            "Returned  :",
            len(df)
        )

        print(
            "First     :",
            df.index[0]
        )

        print(
            "Last      :",
            df.index[-1]
        )

        print(
            "=" * 60
        )

        return df.copy()

    # ======================================================
    # CAPABILITIES
    # ======================================================

    def get_capabilities(
        self
    ):

        return {

            "provider":
                "CoinDCX",

            "live":
                True,

            "historical":
                True,

            "supported_symbols":
                list(
                    self.SUPPORTED_SYMBOLS
                ),

            "supported_markets":
                dict(
                    self.MARKET_NAMES
                ),

            "supported_timeframes":
                list(
                    self.SUPPORTED_TIMEFRAMES
                ),

            "native_timeframes":
                list(
                    self.SOURCE_TIMEFRAMES.keys()
                ),

            "derived_timeframes":
                list(
                    self.DERIVED_TIMEFRAMES.keys()
                ),

            "api_source_intervals":
                list(
                    self.SOURCE_TIMEFRAMES.keys()
                ),

            "max_candles":
                self.MAX_CANDLES,

            "max_api_candles":
                self.MAX_API_CANDLES,

            "supports_websocket":
                True,

        }

    # ======================================================
    # VALIDATE TIMEFRAME
    # ======================================================

    def validate_timeframe(
        self,
        timeframe: str
    ) -> bool:

        try:

            tf = (
                self.normalize_timeframe(
                    timeframe
                )
            )

            return (
                tf in
                self.SUPPORTED_TIMEFRAMES
            )

        except Exception:

            return False

    # ======================================================
    # SERVER TIME
    # ======================================================

    def get_server_time(
        self
    ):

        return int(
            time.time() * 1000
        )

    # ======================================================
    # HEALTH CHECK
    # ======================================================

    def health_check(
        self
    ):

        return {

            "provider":
                "CoinDCX",

            "status":
                "healthy"
                if self.connected
                else "disconnected",

            "connected":
                self.connected,

            "websocket":
                self.websocket is not None,

            "historical":
                True,

            "live":
                True,

            "supported_symbols":
                list(
                    self.SUPPORTED_SYMBOLS
                ),

            "timestamp":
                self.get_server_time(),

        }

    # ======================================================
    # PROVIDER INFO
    # ======================================================

    def provider_info(
        self
    ):

        return {

            "name":
                "CoinDCX Provider",

            "version":
                "V20.8",

            "exchange":
                "CoinDCX",

            "supports_live_data":
                True,

            "supports_historical_data":
                True,

            "supports_websocket":
                True,

            "supported_symbols":
                list(
                    self.SUPPORTED_SYMBOLS
                ),

            "markets":
                dict(
                    self.MARKET_NAMES
                ),

            "max_candles":
                self.MAX_CANDLES,

            "max_api_candles":
                self.MAX_API_CANDLES,

            "source_intervals":
                list(
                    self.SOURCE_TIMEFRAMES.keys()
                ),

            "timeframes":
                list(
                    self.SUPPORTED_TIMEFRAMES
                ),

        }