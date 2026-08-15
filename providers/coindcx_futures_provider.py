"""
============================================================
Liquidity Hunter AI
CoinDCX Futures Provider V20.9
FINAL PRODUCTION EDITION
Part 1 / 2
============================================================

Responsibilities
----------------
• CoinDCX Futures REST connection
• Futures instrument validation
• Futures instrument details
• Futures candlestick API
• Futures timeframe normalization
• Futures DataFrame normalization
• Futures live trade price
• Historical pagination foundation
• Derived timeframe foundation
• Safe error handling
• Provider diagnostics

IMPORTANT
---------
This provider is intentionally isolated from the existing
Spot CoinDCXProvider.

Canonical Futures instrument:
    B-BTC_USDT

Futures candle endpoint:
    /market_data/candlesticks

Futures candle parameter:
    pcode = f

============================================================
"""

from __future__ import annotations

import time
import traceback
from typing import Any

import pandas as pd
import requests


# ==========================================================
# CoinDCX Futures Provider
# ==========================================================

class CoinDCXFuturesProvider:

    # ======================================================
    # PROVIDER INFORMATION
    # ======================================================

    PROVIDER_NAME = (
        "CoinDCX Futures"
    )

    VERSION = (
        "V20.9"
    )

    MARKET_TYPE = (
        "FUTURES"
    )

    EXCHANGE = (
        "CoinDCX"
    )

    # ======================================================
    # API CONFIGURATION
    # ======================================================

    API_BASE_URL = (
        "https://api.coindcx.com"
    )

    PUBLIC_BASE_URL = (
        "https://public.coindcx.com"
    )

    # ------------------------------------------------------
    # Futures endpoints
    # ------------------------------------------------------

    ACTIVE_INSTRUMENTS_URL = (
        API_BASE_URL
        + "/exchange/v1/derivatives/"
          "futures/data/active_instruments"
    )

    INSTRUMENT_DETAILS_URL = (
        API_BASE_URL
        + "/exchange/v1/derivatives/"
          "futures/data/instrument"
    )

    FUTURES_TRADES_URL = (
        API_BASE_URL
        + "/exchange/v1/derivatives/"
          "futures/data/trades"
    )

    CANDLE_URL = (
        PUBLIC_BASE_URL
        + "/market_data/candlesticks"
    )

    # ======================================================
    # REQUEST CONFIGURATION
    # ======================================================

    REQUEST_TIMEOUT = 15

    MAX_CANDLES = 1000

    # ======================================================
    # DEFAULT SYMBOL
    # ======================================================

    DEFAULT_SYMBOL = (
        "B-BTC_USDT"
    )

    # ======================================================
    # SUPPORTED FUTURES SYMBOLS
    # ======================================================

    SUPPORTED_SYMBOLS = [

        "B-BTC_USDT",

        "B-ETH_USDT",

        "B-XAU_USDT",

        "B-XAG_USDT",

    ]

    MARKET_NAMES = {

        "B-BTC_USDT":
            "BTC FUTURES",

        "B-ETH_USDT":
            "ETH FUTURES",

        "B-XAU_USDT":
            "GOLD FUTURES",

        "B-XAG_USDT":
            "SILVER FUTURES",

    }

    # ======================================================
    # NATIVE FUTURES TIMEFRAMES
    # ======================================================

    SOURCE_TIMEFRAMES = {

        "1m":
            "1",

        "5m":
            "5",

        "1h":
            "60",

        "1d":
            "1D",

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
    # NATIVE TIMEFRAME DURATION
    # ======================================================

    NATIVE_TIMEFRAME_SECONDS = {

        "1m":
            60,

        "5m":
            5 * 60,

        "1h":
            60 * 60,

        "1d":
            24 * 60 * 60,

    }

    # ======================================================
    # LIVE TIMEFRAME DURATION
    # ======================================================

    LIVE_TIMEFRAME_SECONDS = {

        "1m":
            60,

        "3m":
            3 * 60,

        "5m":
            5 * 60,

        "15m":
            15 * 60,

        "30m":
            30 * 60,

        "1h":
            60 * 60,

        "2h":
            2 * 60 * 60,

        "4h":
            4 * 60 * 60,

        "6h":
            6 * 60 * 60,

        "8h":
            8 * 60 * 60,

        "12h":
            12 * 60 * 60,

        "1d":
            24 * 60 * 60,

    }

    # ======================================================
    # DERIVED TIMEFRAMES
    # ======================================================

    DERIVED_TIMEFRAMES = {

        "3m": {

            "source":
                "1m",

            "rule":
                "3min",

            "multiplier":
                3,

        },

        "15m": {

            "source":
                "5m",

            "rule":
                "15min",

            "multiplier":
                3,

        },

        "30m": {

            "source":
                "5m",

            "rule":
                "30min",

            "multiplier":
                6,

        },

        "2h": {

            "source":
                "1h",

            "rule":
                "2h",

            "multiplier":
                2,

        },

        "4h": {

            "source":
                "1h",

            "rule":
                "4h",

            "multiplier":
                4,

        },

        "6h": {

            "source":
                "1h",

            "rule":
                "6h",

            "multiplier":
                6,

        },

        "8h": {

            "source":
                "1h",

            "rule":
                "8h",

            "multiplier":
                8,

        },

        "12h": {

            "source":
                "1h",

            "rule":
                "12h",

            "multiplier":
                12,

        },

    }

    # ======================================================
    # PAGINATION CONFIGURATION
    # ======================================================

    PAGINATION_OVERLAP_CANDLES = 3

    MAX_PAGINATION_REQUESTS = 20

    # ======================================================
    # INIT
    # ======================================================

    def __init__(
        self,
        symbol: str = DEFAULT_SYMBOL,
    ):

        self.connected = False

        self.last_error = None

        self.symbol = (
            self.normalize_symbol(
                symbol
            )
        )

        self._active_instruments_cache = None

        self._instrument_details_cache = {}

        self._historical_cache = {}

        self._request_session = (
            requests.Session()
        )

        print(
            "=" * 60
        )

        print(
            "Liquidity Hunter AI"
        )

        print(
            "CoinDCX Futures Provider",
            self.VERSION
        )

        print(
            "Market Type :",
            self.MARKET_TYPE
        )

        print(
            "Symbol      :",
            self.symbol
        )

        print(
            "Market      :",
            self.get_market_name(
                self.symbol
            )
        )

        print(
            "=" * 60
        )

    # ======================================================
    # CONNECT
    # ======================================================

    def connect(
        self,
    ):

        self.connected = True

        self.last_error = None

        print(
            "CoinDCX Futures Provider Connected"
        )

        return True

    # ======================================================
    # DISCONNECT
    # ======================================================

    def disconnect(
        self,
    ):

        self.connected = False

        try:

            self._request_session.close()

        except Exception:

            traceback.print_exc()

        print(
            "CoinDCX Futures Provider Disconnected"
        )

    # ======================================================
    # NORMALIZE SYMBOL
    # ======================================================

    @staticmethod
    def normalize_symbol(
        symbol: str | None,
    ) -> str:

        if not symbol:

            return (
                CoinDCXFuturesProvider.DEFAULT_SYMBOL
            )

        value = str(
            symbol
        ).strip().upper()

        mapping = {

            # ------------------------------------------------
            # BTC
            # ------------------------------------------------

            "BTC":
                "B-BTC_USDT",

            "BTCUSDT":
                "B-BTC_USDT",

            "BTC/USDT":
                "B-BTC_USDT",

            "BTC-USDT":
                "B-BTC_USDT",

            "B-BTCUSDT":
                "B-BTC_USDT",

            "B-BTC/USDT":
                "B-BTC_USDT",

            "B-BTC-USDT":
                "B-BTC_USDT",

            # ------------------------------------------------
            # ETH
            # ------------------------------------------------

            "ETH":
                "B-ETH_USDT",

            "ETHUSDT":
                "B-ETH_USDT",

            "ETH/USDT":
                "B-ETH_USDT",

            "ETH-USDT":
                "B-ETH_USDT",

            "B-ETHUSDT":
                "B-ETH_USDT",

            "B-ETH/USDT":
                "B-ETH_USDT",

            "B-ETH-USDT":
                "B-ETH_USDT",

            # ------------------------------------------------
            # GOLD
            # ------------------------------------------------

            "XAU":
                "B-XAU_USDT",

            "XAUUSDT":
                "B-XAU_USDT",

            "XAU/USDT":
                "B-XAU_USDT",

            "XAU-USDT":
                "B-XAU_USDT",

            "GOLD":
                "B-XAU_USDT",

            "GOLDUSDT":
                "B-XAU_USDT",

            "GOLD/USDT":
                "B-XAU_USDT",

            # ------------------------------------------------
            # SILVER
            # ------------------------------------------------

            "XAG":
                "B-XAG_USDT",

            "XAGUSDT":
                "B-XAG_USDT",

            "XAG/USDT":
                "B-XAG_USDT",

            "XAG-USDT":
                "B-XAG_USDT",

            "SILVER":
                "B-XAG_USDT",

            "SILVERUSDT":
                "B-XAG_USDT",

            "SILVER/USDT":
                "B-XAG_USDT",

        }

        normalized = mapping.get(
            value,
            value,
        )

        return normalized

    # ======================================================
    # SET SYMBOL
    # ======================================================

    def set_symbol(
        self,
        symbol: str,
    ):

        normalized = (
            self.normalize_symbol(
                symbol
            )
        )

        if not self.validate_symbol(
            normalized
        ):

            raise ValueError(
                "Unsupported Futures symbol: "
                f"{normalized}"
            )

        self.symbol = normalized

        print(
            "Futures Symbol Active :",
            self.symbol
        )

    # ======================================================
    # GET SYMBOL
    # ======================================================

    def get_symbol(
        self,
    ) -> str:

        return self.symbol

    # ======================================================
    # MARKET NAME
    # ======================================================

    def get_market_name(
        self,
        symbol: str | None = None,
    ) -> str:

        normalized = (
            self.normalize_symbol(
                symbol
                if symbol
                else self.symbol
            )
        )

        return (
            self.MARKET_NAMES.get(
                normalized,
                normalized,
            )
        )

    # ======================================================
    # VALIDATE SYMBOL
    # ======================================================

    def validate_symbol(
        self,
        symbol: str,
    ) -> bool:

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

    # ======================================================
    # NORMALIZE TIMEFRAME
    # ======================================================

    @staticmethod
    def normalize_timeframe(
        timeframe: str,
    ) -> str:

        if timeframe is None:

            raise ValueError(
                "Timeframe cannot be None"
            )

        value = str(
            timeframe
        ).strip()

        aliases = {

            "1M":
                "1m",

            "3M":
                "3m",

            "5M":
                "5m",

            "15M":
                "15m",

            "30M":
                "30m",

            "1H":
                "1h",

            "2H":
                "2h",

            "4H":
                "4h",

            "6H":
                "6h",

            "8H":
                "8h",

            "12H":
                "12h",

            "1D":
                "1d",

        }

        value = aliases.get(
            value,
            value,
        )

        if value not in (
            CoinDCXFuturesProvider.SUPPORTED_TIMEFRAMES
        ):

            raise ValueError(
                "Unsupported Futures timeframe: "
                f"{timeframe}"
            )

        return value

    # ======================================================
    # ACTIVE INSTRUMENTS
    # ======================================================

    def get_active_instruments(
        self,
        force_refresh: bool = False,
    ):

        if (

            self._active_instruments_cache
            is not None

            and

            not force_refresh

        ):

            return list(
                self._active_instruments_cache
            )

        print(
            "\nRequesting active Futures instruments..."
        )

        try:

            response = (
                self._request_session.get(

                    self.ACTIVE_INSTRUMENTS_URL,

                    timeout=
                        self.REQUEST_TIMEOUT,

                )
            )

            response.raise_for_status()

            data = response.json()

            if not isinstance(
                data,
                list,
            ):

                raise ValueError(
                    "Unexpected active Futures "
                    "instrument response."
                )

            self._active_instruments_cache = (
                data
            )

            self.last_error = None

            print(
                "Active Futures Instruments :",
                len(data)
            )

            return list(
                data
            )

        except Exception as exc:

            self.last_error = exc

            print(
                "Futures active instruments error:",
                exc
            )

            raise

    # ======================================================
    # INSTRUMENT DETAILS
    # ======================================================

    def get_instrument_details(
        self,
        symbol: str | None = None,
        force_refresh: bool = False,
    ):

        normalized = (
            self.normalize_symbol(
                symbol
                if symbol
                else self.symbol
            )
        )

        if (

            normalized
            in
            self._instrument_details_cache

            and

            not force_refresh

        ):

            return (
                self._instrument_details_cache[
                    normalized
                ]
            )

        print(
            "\nRequesting Futures instrument details..."
        )

        print(
            "Pair :",
            normalized
        )

        try:

            response = (
                self._request_session.get(

                    self.INSTRUMENT_DETAILS_URL,

                    params={

                        "pair":
                            normalized,

                    },

                    timeout=
                        self.REQUEST_TIMEOUT,

                )
            )

            response.raise_for_status()

            data = response.json()

            if not isinstance(
                data,
                dict,
            ):

                raise ValueError(
                    "Unexpected Futures instrument "
                    "details response."
                )

            self._instrument_details_cache[
                normalized
            ] = data

            self.last_error = None

            return data

        except Exception as exc:

            self.last_error = exc

            print(
                "Futures instrument details error:",
                exc
            )

            raise

    # ======================================================
    # REQUEST FUTURES CANDLES
    # ======================================================

    def _request_candles(
        self,
        symbol: str,
        resolution: str,
        start_time: int,
        end_time: int,
    ):

        normalized = (
            self.normalize_symbol(
                symbol
            )
        )

        if not self.validate_symbol(
            normalized
        ):

            raise ValueError(
                "Unsupported Futures symbol: "
                f"{normalized}"
            )

        params = {

            "pair":
                normalized,

            "from":
                int(start_time),

            "to":
                int(end_time),

            "resolution":
                resolution,

            "pcode":
                "f",

        }

        print(
            "\n------------------------------------------"
        )

        print(
            "CoinDCX FUTURES Candle Request"
        )

        print(
            "Pair       :",
            normalized
        )

        print(
            "Resolution :",
            resolution
        )

        print(
            "From       :",
            start_time
        )

        print(
            "To         :",
            end_time
        )

        print(
            "PCode      : f"
        )

        print(
            "------------------------------------------"
        )

        try:

            response = (
                self._request_session.get(

                    self.CANDLE_URL,

                    params=params,

                    timeout=
                        self.REQUEST_TIMEOUT,

                )
            )

            print(
                "URL    :",
                response.url
            )

            print(
                "Status :",
                response.status_code
            )

            response.raise_for_status()

            payload = response.json()

            if not isinstance(
                payload,
                dict,
            ):

                raise ValueError(
                    "Unexpected Futures candle response."
                )

            if payload.get(
                "s"
            ) != "ok":

                raise ValueError(
                    "CoinDCX Futures candle API "
                    "returned non-ok status: "
                    f"{payload}"
                )

            candles = payload.get(
                "data"
            )

            if not isinstance(
                candles,
                list,
            ):

                raise ValueError(
                    "Futures candle 'data' "
                    "is not a list."
                )

            self.last_error = None

            print(
                "Received Futures Candles :",
                len(candles)
            )

            return candles

        except Exception as exc:

            self.last_error = exc

            print(
                "Futures candle request error:",
                exc
            )

            raise

    # ======================================================
    # CANDLES → DATAFRAME
    # ======================================================

    def _candles_to_dataframe(
        self,
        candles: list[dict[str, Any]] | None,
    ) -> pd.DataFrame:

        if not candles:

            return pd.DataFrame(
                columns=[
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume",
                ]
            )

        df = pd.DataFrame(
            candles
        )

        if df.empty:

            return pd.DataFrame(
                columns=[
                    "Open",
                    "High",
                    "Low",
                    "Close",
                    "Volume",
                ]
            )

        required_columns = [

            "time",

            "open",

            "high",

            "low",

            "close",

            "volume",

        ]

        missing = [

            column

            for column
            in required_columns

            if column not in df.columns

        ]

        if missing:

            raise ValueError(
                "Missing Futures candle columns: "
                + str(missing)
            )

        # --------------------------------------------------
        # Rename
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

            inplace=True,

        )

        # --------------------------------------------------
        # Timestamp
        # --------------------------------------------------

        df["Datetime"] = pd.to_numeric(

            df["Datetime"],

            errors="coerce",

        )

        df.dropna(
            subset=[
                "Datetime"
            ],
            inplace=True,
        )

        # --------------------------------------------------
        # CoinDCX returns milliseconds.
        #
        # Defensive handling also accepts seconds.
        # --------------------------------------------------

        if not df.empty:

            sample_timestamp = float(
                df["Datetime"].iloc[0]
            )

            if sample_timestamp > 10_000_000_000:

                df["Datetime"] = pd.to_datetime(

                    df["Datetime"],

                    unit="ms",

                    utc=True,

                )

            else:

                df["Datetime"] = pd.to_datetime(

                    df["Datetime"],

                    unit="s",

                    utc=True,

                )

        # --------------------------------------------------
        # Numeric columns
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

                errors="coerce",

            )

        # --------------------------------------------------
        # Remove invalid rows
        # --------------------------------------------------

        df.dropna(

            subset=[

                "Datetime",

                "Open",

                "High",

                "Low",

                "Close",

                "Volume",

            ],

            inplace=True,

        )

        # --------------------------------------------------
        # Sort
        # --------------------------------------------------

        df.sort_values(

            "Datetime",

            inplace=True,

        )

        # --------------------------------------------------
        # Duplicate protection
        # --------------------------------------------------

        df = df[
            ~df["Datetime"].duplicated(
                keep="last"
            )
        ]

        # --------------------------------------------------
        # Index
        # --------------------------------------------------

        df.set_index(

            "Datetime",

            inplace=True,

        )

        df.index.name = (
            "Datetime"
        )

        return df

    # ======================================================
    # NATIVE CANDLE REQUEST
    # ======================================================

    def _request_native_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> pd.DataFrame:

        normalized_symbol = (
            self.normalize_symbol(
                symbol
            )
        )

        normalized_timeframe = (
            self.normalize_timeframe(
                timeframe
            )
        )

        if normalized_timeframe not in (
            self.SOURCE_TIMEFRAMES
        ):

            raise ValueError(
                "Not a native Futures timeframe: "
                f"{normalized_timeframe}"
            )

        resolution = (
            self.SOURCE_TIMEFRAMES[
                normalized_timeframe
            ]
        )

        candle_seconds = (
            self.NATIVE_TIMEFRAME_SECONDS[
                normalized_timeframe
            ]
        )

        target_count = max(

            1,

            min(

                int(limit),

                self.MAX_CANDLES,

            ),

        )

        now_seconds = int(
            time.time()
        )

        request_count = (
            target_count
            + self.PAGINATION_OVERLAP_CANDLES
        )

        start_seconds = (

            now_seconds

            - (

                request_count
                * candle_seconds

            )

        )

        candles = (
            self._request_candles(

                symbol=
                    normalized_symbol,

                resolution=
                    resolution,

                start_time=
                    start_seconds,

                end_time=
                    now_seconds,

            )
        )

        dataframe = (
            self._candles_to_dataframe(
                candles
            )
        )

        if dataframe.empty:

            return dataframe

        dataframe.sort_index(
            inplace=True
        )

        dataframe = dataframe[
            ~dataframe.index.duplicated(
                keep="last"
            )
        ]

        if len(dataframe) > target_count:

            dataframe = dataframe.iloc[
                -target_count:
            ].copy()

        return dataframe

    # ======================================================
    # AGGREGATE DATAFRAME
    # ======================================================

    def _aggregate_dataframe(
        self,
        dataframe: pd.DataFrame,
        rule: str,
    ) -> pd.DataFrame:

        if dataframe is None:

            return pd.DataFrame()

        if dataframe.empty:

            return dataframe.copy()

        required_columns = [

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

            if column not in dataframe.columns

        ]

        if missing:

            raise ValueError(
                "Cannot aggregate Futures DataFrame. "
                "Missing columns: "
                f"{missing}"
            )

        df = dataframe.copy()

        if not isinstance(
            df.index,
            pd.DatetimeIndex,
        ):

            df.index = pd.to_datetime(

                df.index,

                utc=True,

            )

        elif df.index.tz is None:

            df.index = (
                df.index.tz_localize(
                    "UTC"
                )
            )

        else:

            df.index = (
                df.index.tz_convert(
                    "UTC"
                )
            )

        df.sort_index(
            inplace=True
        )

        result = (

            df[
                required_columns
            ]

            .resample(

                rule,

                origin="epoch",

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

            .dropna(
                subset=[
                    "Open",
                    "High",
                    "Low",
                    "Close",
                ]
            )

        )

        result.index.name = (
            "Datetime"
        )

        return result

    # ======================================================
    # GET CANDLES
    # ======================================================

    def get_candles(
        self,
        symbol: str | None = None,
        timeframe: str = "5m",
        limit: int = 1000,
    ) -> pd.DataFrame:

        normalized_symbol = (
            self.normalize_symbol(
                symbol
                if symbol
                else self.symbol
            )
        )

        normalized_tf = (
            self.normalize_timeframe(
                timeframe
            )
        )

        target_limit = max(

            1,

            min(

                int(limit),

                self.MAX_CANDLES,

            ),

        )

        print(
            "\n"
            + "=" * 60
        )

        print(
            "CoinDCX FUTURES CANDLES"
        )

        print(
            "Symbol    :",
            normalized_symbol
        )

        print(
            "Market    :",
            self.get_market_name(
                normalized_symbol
            )
        )

        print(
            "Timeframe :",
            normalized_tf
        )

        print(
            "Requested :",
            target_limit
        )

        print(
            "=" * 60
        )

        # --------------------------------------------------
        # Native timeframe
        # --------------------------------------------------

        if normalized_tf in (
            self.SOURCE_TIMEFRAMES
        ):

            dataframe = (
                self._get_native_candles_paginated(

                    symbol=
                        normalized_symbol,

                    timeframe=
                        normalized_tf,

                    limit=
                        target_limit,

                )
            )

        # --------------------------------------------------
        # Derived timeframe
        # --------------------------------------------------

        else:

            config = (
                self.DERIVED_TIMEFRAMES[
                    normalized_tf
                ]
            )

            source_tf = (
                config["source"]
            )

            rule = (
                config["rule"]
            )

            multiplier = int(
                config["multiplier"]
            )

            source_limit = (

                target_limit
                * multiplier
                + 20

            )

            source_df = (
                self.get_candles(

                    symbol=
                        normalized_symbol,

                    timeframe=
                        source_tf,

                    limit=
                        min(

                            source_limit,

                            self.MAX_CANDLES,

                        ),

                )
            )

            dataframe = (
                self._aggregate_dataframe(

                    source_df,

                    rule,

                )
            )

        if dataframe is None:

            return pd.DataFrame()

        if dataframe.empty:

            return dataframe

        dataframe = dataframe.sort_index()

        dataframe = dataframe[
            ~dataframe.index.duplicated(
                keep="last"
            )
        ]

        if len(dataframe) > target_limit:

            dataframe = dataframe.iloc[
                -target_limit:
            ].copy()

        print(
            "\n========== FUTURES RESULT =========="
        )

        print(
            "Symbol  :",
            normalized_symbol
        )

        print(
            "TF      :",
            normalized_tf
        )

        print(
            "Rows    :",
            len(dataframe)
        )

        print(
            "First   :",
            dataframe.index[0]
        )

        print(
            "Last    :",
            dataframe.index[-1]
        )

        print(
            "Close   :",
            dataframe.iloc[-1]["Close"]
        )

        print(
            "===================================="
        )

        return dataframe.copy()

    # ======================================================
    # PART 2
    # FUTURES HISTORICAL PAGINATION ENGINE
    # ======================================================

    # ======================================================
    # CANDLE TIMESTAMP → SECONDS
    # ======================================================

    @staticmethod
    def _candle_timestamp_seconds(
        candle,
    ):

        if not isinstance(
            candle,
            dict,
        ):

            return None

        value = candle.get(
            "time"
        )

        if value is None:

            return None

        try:

            timestamp = int(
                float(
                    value
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

        # --------------------------------------------------
        # Futures candle API normally returns milliseconds.
        # Defensive support for seconds is retained.
        # --------------------------------------------------

        if timestamp > 10_000_000_000:

            return timestamp // 1000

        return timestamp

    # ======================================================
    # REQUEST ONE NATIVE CANDLE PAGE
    # ======================================================

    def _request_native_candle_page(
        self,
        symbol: str,
        timeframe: str,
        end_seconds: int,
        candle_count: int,
    ):

        normalized_symbol = (
            self.normalize_symbol(
                symbol
            )
        )

        normalized_timeframe = (
            self.normalize_timeframe(
                timeframe
            )
        )

        if normalized_timeframe not in (
            self.SOURCE_TIMEFRAMES
        ):

            raise ValueError(
                "Pagination supports only native "
                "Futures timeframes: "
                f"{list(self.SOURCE_TIMEFRAMES.keys())}"
            )

        resolution = (
            self.SOURCE_TIMEFRAMES[
                normalized_timeframe
            ]
        )

        candle_seconds = (
            self.NATIVE_TIMEFRAME_SECONDS[
                normalized_timeframe
            ]
        )

        # --------------------------------------------------
        # Add a small overlap so boundary candles are not
        # accidentally lost.
        # --------------------------------------------------

        request_count = (

            int(candle_count)

            + self.PAGINATION_OVERLAP_CANDLES

        )

        start_seconds = (

            int(end_seconds)

            - (

                request_count
                * candle_seconds

            )

        )

        print(
            "\n------------------------------------------"
        )

        print(
            "Futures Historical Page"
        )

        print(
            "Pair       :",
            normalized_symbol
        )

        print(
            "Timeframe  :",
            normalized_timeframe
        )

        print(
            "Resolution :",
            resolution
        )

        print(
            "From       :",
            start_seconds
        )

        print(
            "To         :",
            end_seconds
        )

        print(
            "Target     :",
            candle_count
        )

        print(
            "------------------------------------------"
        )

        return self._request_candles(

            symbol=
                normalized_symbol,

            resolution=
                resolution,

            start_time=
                start_seconds,

            end_time=
                int(end_seconds),

        )

    # ======================================================
    # PAGINATED NATIVE CANDLE LOADER
    # ======================================================

    def _get_native_candles_paginated(
        self,
        symbol: str,
        timeframe: str,
        limit: int,
    ) -> pd.DataFrame:

        normalized_symbol = (
            self.normalize_symbol(
                symbol
            )
        )

        normalized_timeframe = (
            self.normalize_timeframe(
                timeframe
            )
        )

        if normalized_timeframe not in (
            self.SOURCE_TIMEFRAMES
        ):

            raise ValueError(
                "Pagination supports only native "
                "Futures timeframes."
            )

        candle_seconds = (
            self.NATIVE_TIMEFRAME_SECONDS[
                normalized_timeframe
            ]
        )

        target_count = max(

            1,

            min(

                int(limit),

                self.MAX_CANDLES,

            ),

        )

        print(
            "\n"
            + "=" * 60
        )

        print(
            "FUTURES PAGINATION ENGINE"
        )

        print(
            "Symbol    :",
            normalized_symbol
        )

        print(
            "Timeframe :",
            normalized_timeframe
        )

        print(
            "Target    :",
            target_count
        )

        print(
            "=" * 60
        )

        # --------------------------------------------------
        # Current UTC time in seconds.
        # --------------------------------------------------

        current_end = int(
            time.time()
        )

        all_candles = []

        seen_timestamps = set()

        request_count = 0

        # ==================================================
        # PAGINATION LOOP
        # ==================================================

        while (

            len(seen_timestamps)
            < target_count

            and

            request_count
            < self.MAX_PAGINATION_REQUESTS

        ):

            request_count += 1

            candles = (
                self._request_native_candle_page(

                    symbol=
                        normalized_symbol,

                    timeframe=
                        normalized_timeframe,

                    end_seconds=
                        current_end,

                    candle_count=
                        target_count,

                )
            )

            if not candles:

                print(
                    "Pagination returned no candles."
                )

                break

            new_count = 0

            oldest_timestamp = None

            # --------------------------------------------------
            # Collect unique candles
            # --------------------------------------------------

            for candle in candles:

                timestamp = (
                    self._candle_timestamp_seconds(
                        candle
                    )
                )

                if timestamp is None:

                    continue

                if timestamp not in (
                    seen_timestamps
                ):

                    seen_timestamps.add(
                        timestamp
                    )

                    all_candles.append(
                        candle
                    )

                    new_count += 1

                if (

                    oldest_timestamp is None

                    or

                    timestamp
                    < oldest_timestamp

                ):

                    oldest_timestamp = (
                        timestamp
                    )

            print(
                "Page       :",
                request_count
            )

            print(
                "Page rows  :",
                len(candles)
            )

            print(
                "New rows   :",
                new_count
            )

            print(
                "Total uniq :",
                len(seen_timestamps)
            )

            # --------------------------------------------------
            # API returned no new data.
            # --------------------------------------------------

            if new_count == 0:

                print(
                    "No new unique candles received."
                )

                break

            if oldest_timestamp is None:

                break

            # --------------------------------------------------
            # Move backward.
            #
            # One candle is intentionally skipped from the
            # next endpoint boundary to avoid repeatedly
            # receiving the same page.
            # --------------------------------------------------

            current_end = (

                oldest_timestamp

                - candle_seconds

            )

        # ==================================================
        # EMPTY RESULT
        # ==================================================

        if not all_candles:

            print(
                "Futures pagination produced no candles."
            )

            return pd.DataFrame()

        # ==================================================
        # CONVERT TO DATAFRAME
        # ==================================================

        dataframe = (
            self._candles_to_dataframe(
                all_candles
            )
        )

        if dataframe.empty:

            return dataframe

        # ==================================================
        # FINAL SORT
        # ==================================================

        dataframe.sort_index(
            inplace=True
        )

        # ==================================================
        # FINAL DUPLICATE PROTECTION
        # ==================================================

        dataframe = dataframe[
            ~dataframe.index.duplicated(
                keep="last"
            )
        ]

        # ==================================================
        # FINAL LIMIT
        # ==================================================

        if len(dataframe) > target_count:

            dataframe = dataframe.iloc[
                -target_count:
            ].copy()

        print(
            "\n========== PAGINATION RESULT =========="
        )

        print(
            "Symbol      :",
            normalized_symbol
        )

        print(
            "Timeframe   :",
            normalized_timeframe
        )

        print(
            "API Requests:",
            request_count
        )

        print(
            "Rows        :",
            len(dataframe)
        )

        if not dataframe.empty:

            print(
                "First       :",
                dataframe.index[0]
            )

            print(
                "Last        :",
                dataframe.index[-1]
            )

            print(
                "Last Close  :",
                dataframe.iloc[-1]["Close"]
            )

        print(
            "========================================"
        )

        return dataframe

    # ======================================================
    # COMPATIBILITY NATIVE CANDLE METHOD
    # ======================================================

    def _get_native_candles(
        self,
        symbol,
        timeframe,
        limit,
    ):

        """
        Compatibility wrapper.

        Older Controller / MarketData implementations may
        call _get_native_candles() directly.

        The actual implementation is now handled by the
        pagination engine.
        """

        return (
            self._get_native_candles_paginated(

                symbol=
                    symbol,

                timeframe=
                    timeframe,

                limit=
                    limit,

            )
        )

    # ======================================================
    # TRADE HISTORY
    # ======================================================

    def get_trade_history(
        self,
        symbol: str | None = None,
    ):

        normalized = (
            self.normalize_symbol(
                symbol
                if symbol
                else self.symbol
            )
        )

        if not self.validate_symbol(
            normalized
        ):

            raise ValueError(
                "Unsupported Futures symbol: "
                f"{normalized}"
            )

        print(
            "\nRequesting Futures trade history..."
        )

        try:

            response = (
                self._request_session.get(

                    self.FUTURES_TRADES_URL,

                    params={

                        "pair":
                            normalized,

                    },

                    timeout=
                        self.REQUEST_TIMEOUT,

                )
            )

            response.raise_for_status()

            data = response.json()

            if not isinstance(
                data,
                list,
            ):

                raise ValueError(
                    "Unexpected Futures trade history "
                    "response."
                )

            self.last_error = None

            return data

        except Exception as exc:

            self.last_error = exc

            print(
                "Futures trade history error:",
                exc
            )

            raise

    # ======================================================
    # CURRENT FUTURES PRICE
    # ======================================================

    def get_live_price(
        self,
        symbol: str | None = None,
    ):

        normalized = (
            self.normalize_symbol(
                symbol
                if symbol
                else self.symbol
            )
        )

        trades = (
            self.get_trade_history(
                normalized
            )
        )

        if not trades:

            raise ValueError(
                "No Futures trade data available."
            )

        valid_trades = [

            trade

            for trade
            in trades

            if isinstance(
                trade,
                dict,
            )

            and

            trade.get(
                "price"
            ) is not None

        ]

        if not valid_trades:

            raise ValueError(
                "No valid Futures price found."
            )

        # --------------------------------------------------
        # Prefer latest timestamped trade.
        # --------------------------------------------------

        latest_trade = max(

            valid_trades,

            key=lambda item:
                self._safe_trade_timestamp(
                    item
                ),

        )

        price = float(
            latest_trade["price"]
        )

        print(
            "\nFUTURES LIVE PRICE"
        )

        print(
            "Symbol :",
            normalized
        )

        print(
            "Price  :",
            price
        )

        print(
            "Time   :",
            latest_trade.get(
                "timestamp"
            )
        )

        return price

    # ======================================================
    # SAFE TRADE TIMESTAMP
    # ======================================================

    @staticmethod
    def _safe_trade_timestamp(
        trade,
    ) -> int:

        if not isinstance(
            trade,
            dict,
        ):

            return 0

        value = (
            trade.get(
                "timestamp",
                trade.get(
                    "T",
                    0
                )
            )
        )

        try:

            return int(
                float(
                    value
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            return 0

    # ======================================================
    # CACHE HISTORICAL CANDLES
    # ======================================================

    def cache_historical_candles(
        self,
        dataframe: pd.DataFrame | None,
        timeframe: str = "5m",
    ):

        normalized_tf = (
            self.normalize_timeframe(
                timeframe
            )
        )

        if dataframe is None:

            dataframe = pd.DataFrame()

        if dataframe.empty:

            self._historical_cache[
                normalized_tf
            ] = pd.DataFrame()

            return pd.DataFrame()

        required_columns = [

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

            if column not in dataframe.columns

        ]

        if missing:

            raise ValueError(
                "Historical Futures DataFrame "
                "missing columns: "
                f"{missing}"
            )

        df = dataframe.copy()

        # --------------------------------------------------
        # Normalize index
        # --------------------------------------------------

        if not isinstance(
            df.index,
            pd.DatetimeIndex,
        ):

            df.index = pd.to_datetime(

                df.index,

                utc=True,

            )

        elif df.index.tz is None:

            df.index = (
                df.index.tz_localize(
                    "UTC"
                )
            )

        else:

            df.index = (
                df.index.tz_convert(
                    "UTC"
                )
            )

        # --------------------------------------------------
        # Numeric
        # --------------------------------------------------

        for column in required_columns:

            df[column] = pd.to_numeric(

                df[column],

                errors="coerce",

            )

        df.dropna(

            subset=required_columns,

            inplace=True,

        )

        # --------------------------------------------------
        # Sort
        # --------------------------------------------------

        df.sort_index(
            inplace=True
        )

        # --------------------------------------------------
        # Duplicate protection
        # --------------------------------------------------

        df = df[
            ~df.index.duplicated(
                keep="last"
            )
        ]

        # --------------------------------------------------
        # History limit
        # --------------------------------------------------

        if len(df) > self.MAX_CANDLES:

            df = df.iloc[
                -self.MAX_CANDLES:
            ].copy()

        self._historical_cache[
            normalized_tf
        ] = df.copy()

        print(
            "\nFutures Historical Cache Updated"
        )

        print(
            "Timeframe :",
            normalized_tf
        )

        print(
            "Rows      :",
            len(df)
        )

        if not df.empty:

            print(
                "First     :",
                df.index[0]
            )

            print(
                "Last      :",
                df.index[-1]
            )

        return df.copy()

    # ======================================================
    # GET CACHED HISTORICAL CANDLES
    # ======================================================

    def get_cached_candles(
        self,
        timeframe: str = "5m",
        limit: int | None = None,
    ):

        normalized_tf = (
            self.normalize_timeframe(
                timeframe
            )
        )

        dataframe = (
            self._historical_cache.get(
                normalized_tf
            )
        )

        if dataframe is None:

            return pd.DataFrame()

        dataframe = dataframe.copy()

        dataframe.sort_index(
            inplace=True
        )

        if limit is not None:

            limit = max(
                1,
                int(limit)
            )

            if len(dataframe) > limit:

                dataframe = dataframe.iloc[
                    -limit:
                ].copy()

        return dataframe

    # ======================================================
    # LOAD + CACHE HISTORICAL
    # ======================================================

    def load_and_cache_historical(
        self,
        symbol=None,
        timeframe="5m",
        limit=1000,
    ):

        normalized_tf = (
            self.normalize_timeframe(
                timeframe
            )
        )

        dataframe = (
            self.get_candles(

                symbol=
                    symbol,

                timeframe=
                    normalized_tf,

                limit=
                    limit,

            )
        )

        return (
            self.cache_historical_candles(

                dataframe=
                    dataframe,

                timeframe=
                    normalized_tf,

            )
        )

    # ======================================================
    # CLEAR CACHE
    # ======================================================

    def clear_cache(
        self,
        timeframe=None,
    ):

        if timeframe is None:

            self._historical_cache.clear()

            print(
                "All Futures historical cache cleared."
            )

            return

        normalized_tf = (
            self.normalize_timeframe(
                timeframe
            )
        )

        self._historical_cache.pop(
            normalized_tf,
            None
        )

        print(
            "Futures historical cache cleared:",
            normalized_tf
        )

    # ======================================================
    # GET CAPABILITIES
    # ======================================================

    def get_capabilities(
        self,
    ):

        return {

            "provider":
                self.PROVIDER_NAME,

            "version":
                self.VERSION,

            "exchange":
                self.EXCHANGE,

            "market_type":
                self.MARKET_TYPE,

            "live":
                True,

            "historical":
                True,

            "supports_futures":
                True,

            "supports_websocket":
                True,

            "supported_symbols":
                list(
                    self.SUPPORTED_SYMBOLS
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

            "max_candles":
                self.MAX_CANDLES,

        }

    # ======================================================
    # HEALTH CHECK
    # ======================================================

    def health_check(
        self,
    ):

        return {

            "provider":
                self.PROVIDER_NAME,

            "version":
                self.VERSION,

            "exchange":
                self.EXCHANGE,

            "market_type":
                self.MARKET_TYPE,

            "connected":
                self.connected,

            "symbol":
                self.symbol,

            "market":
                self.get_market_name(
                    self.symbol
                ),

            "last_error":
                (
                    str(
                        self.last_error
                    )
                    if self.last_error
                    else None
                ),

            "timestamp":
                int(
                    time.time()
                    * 1000
                ),

        }

    # ======================================================
    # PROVIDER INFO
    # ======================================================

    def provider_info(
        self,
    ):

        return {

            "name":
                self.PROVIDER_NAME,

            "version":
                self.VERSION,

            "exchange":
                self.EXCHANGE,

            "market_type":
                self.MARKET_TYPE,

            "symbol":
                self.symbol,

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

        }

    # ======================================================
    # DIAGNOSTICS
    # ======================================================

    def diagnostics(
        self,
    ):

        return {

            "provider":
                self.PROVIDER_NAME,

            "version":
                self.VERSION,

            "exchange":
                self.EXCHANGE,

            "market_type":
                self.MARKET_TYPE,

            "symbol":
                self.symbol,

            "market":
                self.get_market_name(
                    self.symbol
                ),

            "connected":
                self.connected,

            "cached_timeframes":
                list(
                    self._historical_cache.keys()
                ),

            "cached_rows":
                {
                    timeframe:
                        len(dataframe)

                    for timeframe, dataframe
                    in self._historical_cache.items()
                },

            "last_error":
                (
                    str(
                        self.last_error
                    )
                    if self.last_error
                    else None
                ),

        }

    # ======================================================
    # REPRESENTATION
    # ======================================================

    def __repr__(
        self,
    ):

        return (

            "CoinDCXFuturesProvider("

            f"symbol='{self.symbol}', "

            f"market_type='{self.MARKET_TYPE}', "

            f"connected={self.connected}"

            ")"

        )