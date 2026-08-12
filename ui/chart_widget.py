"""
Liquidity Hunter AI
Version : V20.5 Live Candle Sync
File    : ui/chart_widget.py

Responsibilities
----------------
- Lightweight Charts WebEngine
- Historical candle loading
- Live candle updates
- Historical/live timestamp protection
- Same-timestamp update ordering
- Stale queued signal protection
- Pending chart data
- Pending AI signal
"""

from __future__ import annotations

from pathlib import Path
import json

from PySide6.QtCore import (
    QUrl,
    Signal,
    Slot,
)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)

from PySide6.QtWebEngineWidgets import (
    QWebEngineView,
)


class ChartWidget(QWidget):

    # ====================================================
    # Signals
    # ====================================================

    live_candle_signal = Signal(dict)

    # ====================================================
    # Initialization
    # ====================================================

    def __init__(self):

        super().__init__()

        # ====================================================
        # Chart State
        # ====================================================

        self.chart_ready = False

        self.pending_candles = None

        self.pending_signal = None

        # ====================================================
        # LIVE CANDLE ORDER PROTECTION
        # ====================================================

        # Latest candle timestamp known by the chart.
        self._last_chart_candle_time = None

        # Latest live candle timestamp.
        self._last_live_candle_time = None

        # ----------------------------------------------------
        # Monotonic live update sequence.
        #
        # IMPORTANT:
        #
        # Timestamp alone cannot detect an old queued update
        # when multiple updates belong to the same candle.
        #
        # Example:
        #
        # seq 101 -> close 63491.72
        # seq 102 -> close 63491.83
        #
        # If seq 101 reaches the GUI after seq 102,
        # it must be rejected.
        # ----------------------------------------------------

        self._live_update_sequence = 0

        self._last_applied_live_sequence = 0

        # ====================================================
        # Layout
        # ====================================================

        layout = QVBoxLayout(self)

        title = QLabel(
            "📈 LIVE MARKET CHART"
        )

        title.setStyleSheet("""
            QLabel{
                font-size:18px;
                font-weight:bold;
                color:white;
                padding:8px;
            }
        """)

        # ====================================================
        # WebEngine
        # ====================================================

        self.webview = QWebEngineView()

        self.webview.setMinimumHeight(500)

        html_file = (
            Path(__file__).parent
            / "resources"
            / "chart.html"
        )

        self.webview.loadFinished.connect(
            self._on_chart_loaded
        )

        self.webview.load(
            QUrl.fromLocalFile(
                str(html_file.resolve())
            )
        )

        layout.addWidget(title)
        layout.addWidget(self.webview)

        # ====================================================
        # Live Candle Signal
        # ====================================================

        self.live_candle_signal.connect(
            self._update_last_candle_gui
        )

        print("CONNECT DONE")
        print(
            self._update_last_candle_gui
        )

    # ========================================================
    # CHART LOADED
    # ========================================================

    def _on_chart_loaded(
        self,
        ok,
    ):

        print(
            ">>> _on_chart_loaded() CALLED <<<"
        )

        self.chart_ready = ok

        print(
            "==================================="
        )

        print(
            "Chart Loaded :",
            ok
        )

        print(
            "==================================="
        )

        # ----------------------------------------------------
        # Pending Historical Candles
        # ----------------------------------------------------

        if (
            ok
            and self.pending_candles is not None
        ):

            print(
                "Sending Pending Candle Data..."
            )

            data = self.pending_candles

            self.pending_candles = None

            self.set_chart_data(data)

        else:

            print(
                "No Pending Candle Data"
            )

        # ----------------------------------------------------
        # Pending AI Signal
        # ----------------------------------------------------

        if (
            ok
            and self.pending_signal is not None
        ):

            print(
                "Sending Pending Trade Signal..."
            )

            signal = self.pending_signal

            self.pending_signal = None

            self.show_trade_signal(
                signal
            )

    # ========================================================
    # DATAFRAME -> CANDLE LIST
    # ========================================================

    def _convert_dataframe(
        self,
        df,
    ):

        if df is None:
            return []

        if df.empty:
            return []

        candles = []

        for index, row in df.iterrows():

            try:

                timestamp = (
                    int(
                        index.timestamp()
                    )
                )

            except Exception as exc:

                print(
                    "HIST TIMESTAMP ERROR:",
                    exc,
                )

                continue

            print(
                "HIST DEBUG:",
                index,
                getattr(
                    index,
                    "tzinfo",
                    None,
                ),
                timestamp,
            )

            candles.append({

                "time": timestamp,

                "open": float(
                    row["Open"]
                ),

                "high": float(
                    row["High"]
                ),

                "low": float(
                    row["Low"]
                ),

                "close": float(
                    row["Close"]
                ),
            })

        if not candles:
            return []

        print(
            "========== FIRST CANDLE =========="
        )

        print(
            candles[0]
        )

        print(
            "========== LAST CANDLE =========="
        )

        print(
            candles[-1]
        )

        print(
            "=================================="
        )

        return candles

    # ========================================================
    # SET HISTORICAL CHART DATA
    # ========================================================

    def set_chart_data(
        self,
        dataframe,
    ):

        print(
            "set_chart_data() called"
        )

        print(
            "Chart Ready :",
            self.chart_ready,
        )

        # ----------------------------------------------------
        # Chart not ready
        # ----------------------------------------------------

        if not self.chart_ready:

            print(
                "Chart not ready. "
                "Saving pending candles."
            )

            self.pending_candles = dataframe

            return

        # ----------------------------------------------------
        # Convert dataframe
        # ----------------------------------------------------

        candles = self._convert_dataframe(
            dataframe
        )

        if not candles:

            print(
                "No candle data available."
            )

            return

        print(
            "Candles Sent :",
            len(candles)
        )

        # ====================================================
        # Register Latest Historical Candle
        # ====================================================

        try:

            latest_time = int(
                candles[-1]["time"]
            )

            self._last_chart_candle_time = (
                latest_time
            )

            self._last_live_candle_time = (
                None
            )

            # ----------------------------------------------
            # Reset live sequence for new dataset
            # ----------------------------------------------

            self._live_update_sequence = 0

            self._last_applied_live_sequence = 0

            print(
                "Chart Latest Candle Time :",
                self._last_chart_candle_time,
            )

        except Exception as exc:

            print(
                "Latest candle time error :",
                exc,
            )

        # ----------------------------------------------------
        # Send historical data to JavaScript
        # ----------------------------------------------------

        js = (
            "window.setChartData("
            + json.dumps(candles)
            + ");"
        )

        self.webview.page().runJavaScript(
            js
        )

    # ========================================================
    # LIVE CANDLE UPDATE
    # ========================================================

    def update_last_candle(
        self,
        candle,
    ):

        print(
            "ChartWidget.update_last_candle() CALLED"
        )

        print(
            candle
        )

        # ----------------------------------------------------
        # Basic validation
        # ----------------------------------------------------

        if not self.chart_ready:

            print(
                "LIVE UPDATE IGNORED: "
                "Chart not ready"
            )

            return

        if candle is None:

            print(
                "LIVE UPDATE IGNORED: "
                "Candle is None"
            )

            return

        # ----------------------------------------------------
        # Timestamp
        # ----------------------------------------------------

        try:

            candle_timestamp = int(
                candle.timestamp.timestamp()
            )

        except Exception as exc:

            print(
                "LIVE UPDATE IGNORED: "
                "Invalid timestamp",
                exc,
            )

            return

        print(
            "LIVE DEBUG:",
            candle.timestamp,
            candle.timestamp.tzinfo,
            candle_timestamp,
        )

        # ====================================================
        # Timestamp Ordering
        # ====================================================

        last_time = (
            self._last_chart_candle_time
        )

        print(
            "Last Chart Candle Time :",
            last_time,
        )

        print(
            "Incoming Candle Time    :",
            candle_timestamp,
        )

        # ----------------------------------------------------
        # Older candle
        # ----------------------------------------------------

        if (
            last_time is not None
            and candle_timestamp < last_time
        ):

            print(
                "⚠️ STALE CANDLE IGNORED"
            )

            print(
                "Incoming :",
                candle_timestamp,
            )

            print(
                "Latest   :",
                last_time,
            )

            return

        # ----------------------------------------------------
        # Same candle
        # ----------------------------------------------------

        if (
            last_time is not None
            and candle_timestamp == last_time
        ):

            print(
                "LIVE CANDLE UPDATE:"
            )

            print(
                "Same timestamp -> "
                "Updating current candle"
            )

        # ----------------------------------------------------
        # New candle
        # ----------------------------------------------------

        elif (
            last_time is None
            or candle_timestamp > last_time
        ):

            print(
                "🟢 NEWER LIVE CANDLE ACCEPTED"
            )

        # ====================================================
        # Generate Monotonic Sequence
        # ====================================================

        self._live_update_sequence += 1

        update_sequence = (
            self._live_update_sequence
        )

        # ====================================================
        # Build Internal Payload
        # ====================================================

        candle_data = {

            "time":
                candle_timestamp,

            "open":
                float(candle.open),

            "high":
                float(candle.high),

            "low":
                float(candle.low),

            "close":
                float(candle.close),

            "_seq":
                update_sequence,
        }

        print(
            "========== LIVE CANDLE =========="
        )

        print(
            candle_data
        )

        print(
            "Sequence :",
            update_sequence,
        )

        print(
            type(
                candle_data["time"]
            )
        )

        print(
            "================================"
        )

        # ----------------------------------------------------
        # WebView safety
        # ----------------------------------------------------

        if self.webview is None:

            print(
                "LIVE UPDATE IGNORED: "
                "WebView missing"
            )

            return

        try:

            page = self.webview.page()

        except RuntimeError:

            return

        if page is None:
            return

        # ====================================================
        # IMPORTANT
        #
        # Update timestamp state immediately.
        # ====================================================

        self._last_chart_candle_time = (
            candle_timestamp
        )

        self._last_live_candle_time = (
            candle_timestamp
        )

        print(
            "Accepted Candle Timestamp :",
            self._last_chart_candle_time,
        )

        print(
            "Accepted Update Sequence  :",
            update_sequence,
        )

        # ----------------------------------------------------
        # Emit
        # ----------------------------------------------------

        self.live_candle_signal.emit(
            candle_data
        )

    # ========================================================
    # GUI SLOT
    # ========================================================

    @Slot(dict)
    def _update_last_candle_gui(
        self,
        candle_data,
    ):

        try:

            print(
                "GUI SLOT CALLED"
            )

            print(
                candle_data
            )

            if not self.chart_ready:
                return

            # =================================================
            # Sequence Validation
            # =================================================

            try:

                incoming_sequence = int(
                    candle_data["_seq"]
                )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):

                print(
                    "⚠️ GUI UPDATE IGNORED: "
                    "Invalid sequence"
                )

                return

            latest_sequence = (
                self._last_applied_live_sequence
            )

            print(
                "Incoming Sequence :",
                incoming_sequence,
            )

            print(
                "Latest Sequence   :",
                latest_sequence,
            )

            # -------------------------------------------------
            # Old queued update
            # -------------------------------------------------

            if (
                incoming_sequence
                < latest_sequence
            ):

                print(
                    "⚠️ GUI STALE UPDATE IGNORED"
                )

                print(
                    "Incoming Sequence :",
                    incoming_sequence,
                )

                print(
                    "Latest Sequence   :",
                    latest_sequence,
                )

                return

            # -------------------------------------------------
            # Mark sequence as applied
            # -------------------------------------------------

            self._last_applied_live_sequence = (
                incoming_sequence
            )

            # =================================================
            # Timestamp Validation
            # =================================================

            incoming_time = int(
                candle_data["time"]
            )

            latest_time = (
                self._last_live_candle_time
            )

            if (
                latest_time is not None
                and incoming_time < latest_time
            ):

                print(
                    "⚠️ GUI STALE CANDLE IGNORED"
                )

                print(
                    "Incoming :",
                    incoming_time,
                )

                print(
                    "Latest   :",
                    latest_time,
                )

                return

            # =================================================
            # Build JS-only payload
            #
            # _seq is NOT sent to JavaScript.
            # =================================================

            js_candle = {

                "time":
                    incoming_time,

                "open":
                    float(
                        candle_data["open"]
                    ),

                "high":
                    float(
                        candle_data["high"]
                    ),

                "low":
                    float(
                        candle_data["low"]
                    ),

                "close":
                    float(
                        candle_data["close"]
                    ),
            }

            # =================================================
            # JavaScript
            # =================================================

            js = (
                "window.updateLastCandle("
                + json.dumps(
                    js_candle
                )
                + ");"
            )

            print(
                js
            )

            self.webview.page().runJavaScript(
                js,
                lambda result: print(
                    "JS Returned:",
                    result,
                ),
            )

        except Exception:

            import traceback

            traceback.print_exc()

    # ========================================================
    # AI TRADE SIGNAL OVERLAY
    # ========================================================

    def show_trade_signal(
        self,
        signal,
    ):

        try:

            # ------------------------------------------------
            # Chart not ready
            # ------------------------------------------------

            if not self.chart_ready:

                print(
                    "Chart Not Ready -> "
                    "Saving Trade Signal"
                )

                self.pending_signal = signal

                return

            # ------------------------------------------------
            # Send signal to JavaScript
            # ------------------------------------------------

            js = (
                "window.showTradeSignal("
                + json.dumps(signal)
                + ");"
            )

            print(
                "Sending Trade Signal To JS"
            )

            print(
                signal
            )

            self.webview.page().runJavaScript(
                js,
                lambda result: print(
                    "Trade Signal JS Returned:",
                    result,
                ),
            )

        except Exception:

            import traceback

            traceback.print_exc()