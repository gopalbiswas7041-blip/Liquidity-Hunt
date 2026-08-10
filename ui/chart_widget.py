from pathlib import Path
import json

from PySide6.QtCore import (
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtWebEngineWidgets import QWebEngineView


class ChartWidget(QWidget):

    live_candle_signal = Signal(dict)

    def __init__(self):
        super().__init__()

        # ====================================================
        # Chart State
        # ====================================================

        self.chart_ready = False

        self.pending_candles = None

        # Pending AI signal
        self.pending_signal = None

        # ====================================================
        # LIVE CANDLE ORDER PROTECTION
        # ====================================================

        # Latest candle timestamp currently known by ChartWidget.
        #
        # This prevents an old/stale candle from being sent
        # to Lightweight Charts after a newer candle arrived.
        #
        # Example:
        #
        # 19:22 -> 1786283520
        # 19:23 -> 1786283580
        #
        # If 19:22 arrives again after 19:23,
        # it will be rejected.
        self._last_chart_candle_time = None

        # Latest live candle timestamp accepted by the
        # live update pipeline.
        self._last_live_candle_time = None

        # ====================================================
        # Layout
        # ====================================================

        layout = QVBoxLayout(self)

        title = QLabel("📈 LIVE MARKET CHART")

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
        print(self._update_last_candle_gui)

    # ========================================================
    # CHART LOADED
    # ========================================================

    def _on_chart_loaded(self, ok):

        print(">>> _on_chart_loaded() CALLED <<<")

        self.chart_ready = ok

        print("===================================")
        print("Chart Loaded :", ok)
        print("===================================")

        # ----------------------------------------------------
        # Pending Historical Candles
        # ----------------------------------------------------

        if ok and self.pending_candles is not None:

            print("Sending Pending Candle Data...")

            data = self.pending_candles

            self.pending_candles = None

            self.set_chart_data(data)

        else:

            print("No Pending Candle Data")

        # ----------------------------------------------------
        # Pending AI Signal
        # ----------------------------------------------------

        if ok and self.pending_signal is not None:

            print("Sending Pending Trade Signal...")

            signal = self.pending_signal

            self.pending_signal = None

            self.show_trade_signal(signal)

    # ========================================================
    # DATAFRAME -> CANDLE LIST
    # ========================================================

    def _convert_dataframe(self, df):

        if df is None:
            return []

        if df.empty:
            return []

        candles = []

        for index, row in df.iterrows():

            print(
                "HIST DEBUG:",
                index,
                index.tzinfo,
                index.timestamp(),
            )

            candles.append({

                "time": int(index.timestamp()),

                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"])

            })

        if not candles:
            return []

        print("========== FIRST CANDLE ==========")
        print(candles[0])

        print("========== LAST CANDLE ==========")
        print(candles[-1])

        print("==================================")

        return candles

    # ========================================================
    # SET HISTORICAL CHART DATA
    # ========================================================

    def set_chart_data(self, dataframe):

        print("set_chart_data() called")

        print(
            "Chart Ready :",
            self.chart_ready
        )

        # ----------------------------------------------------
        # Chart not ready
        # ----------------------------------------------------

        if not self.chart_ready:

            print(
                "Chart not ready. Saving pending candles."
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
        # IMPORTANT:
        # Register latest historical candle timestamp.
        # ====================================================

        try:

            latest_time = int(
                candles[-1]["time"]
            )

            self._last_chart_candle_time = (
                latest_time
            )

            # Reset live timestamp when a completely
            # new historical dataset is loaded.
            self._last_live_candle_time = None

            print(
                "Chart Latest Candle Time :",
                self._last_chart_candle_time
            )

        except Exception as e:

            print(
                "Latest candle time error :",
                e
            )

        # ----------------------------------------------------
        # Send data to JavaScript
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

    def update_last_candle(self, candle):

        print(
            "ChartWidget.update_last_candle() CALLED"
        )

        print(candle)

        # ----------------------------------------------------
        # Basic validation
        # ----------------------------------------------------

        if not self.chart_ready:

            print(
                "LIVE UPDATE IGNORED: Chart not ready"
            )

            return

        if candle is None:

            print(
                "LIVE UPDATE IGNORED: Candle is None"
            )

            return

        # ----------------------------------------------------
        # Timestamp
        # ----------------------------------------------------

        try:

            candle_timestamp = int(
                candle.timestamp.timestamp()
            )

        except Exception as e:

            print(
                "LIVE UPDATE IGNORED: Invalid timestamp",
                e
            )

            return

        print(
            "LIVE DEBUG:",
            candle.timestamp,
            candle.timestamp.tzinfo,
            candle_timestamp,
        )

        # ====================================================
        # LIVE CANDLE ORDER GUARD
        # ====================================================

        last_time = self._last_chart_candle_time

        print(
            "Last Chart Candle Time :",
            last_time
        )

        print(
            "Incoming Candle Time    :",
            candle_timestamp
        )

        # ----------------------------------------------------
        # STALE CANDLE
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
                candle_timestamp
            )

            print(
                "Latest   :",
                last_time
            )

            print(
                "Reason   : Incoming candle is older "
                "than the latest chart candle."
            )

            return

        # ====================================================
        # DUPLICATE / SAME CANDLE
        # ====================================================

        if (
            last_time is not None
            and candle_timestamp == last_time
        ):

            print(
                "LIVE CANDLE UPDATE:"
            )

            print(
                "Same timestamp -> Updating current candle"
            )

        # ====================================================
        # NEWER CANDLE
        # ====================================================

        elif (
            last_time is None
            or candle_timestamp > last_time
        ):

            print(
                "🟢 NEWER LIVE CANDLE ACCEPTED"
            )

        # ----------------------------------------------------
        # Build candle payload
        # ----------------------------------------------------

        candle_data = {

            "time": candle_timestamp,

            "open": float(candle.open),
            "high": float(candle.high),
            "low": float(candle.low),
            "close": float(candle.close)

        }

        print(
            "========== LIVE CANDLE =========="
        )

        print(candle_data)

        print(
            type(candle_data["time"])
        )

        print(
            "================================"
        )

        # ----------------------------------------------------
        # Widget destroyed?
        # ----------------------------------------------------

        if self.webview is None:

            print(
                "LIVE UPDATE IGNORED: WebView missing"
            )

            return

        # ----------------------------------------------------
        # Get page safely
        # ----------------------------------------------------

        try:

            page = self.webview.page()

        except RuntimeError:

            return

        if page is None:

            return

        # ====================================================
        # IMPORTANT:
        # Update Python-side latest timestamp BEFORE emit.
        #
        # This prevents a second stale queued signal from
        # being accepted during candle rollover.
        # ====================================================

        self._last_chart_candle_time = (
            candle_timestamp
        )

        self._last_live_candle_time = (
            candle_timestamp
        )

        print(
            "Accepted Candle Timestamp :",
            self._last_chart_candle_time
        )

        # ----------------------------------------------------
        # Emit to GUI thread
        # ----------------------------------------------------

        print(type(self))

        print(
            type(self.live_candle_signal)
        )

        print(
            self.live_candle_signal
        )

        self.live_candle_signal.emit(
            candle_data
        )

    # ========================================================
    # GUI SLOT
    # ========================================================

    @Slot(dict)
    def _update_last_candle_gui(
        self,
        candle_data
    ):

        try:

            print(
                "GUI SLOT CALLED"
            )

            print(candle_data)

            if not self.chart_ready:

                return

            # ------------------------------------------------
            # SECOND SAFETY CHECK
            # ------------------------------------------------

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
                    incoming_time
                )

                print(
                    "Latest   :",
                    latest_time
                )

                return

            # ------------------------------------------------
            # JavaScript call
            # ------------------------------------------------

            js = (
                "window.updateLastCandle("
                + json.dumps(candle_data)
                + ");"
            )

            print(js)

            self.webview.page().runJavaScript(
                js,
                lambda result: print(
                    "JS Returned:",
                    result
                )
            )

        except Exception:

            import traceback

            traceback.print_exc()

    # ========================================================
    # AI TRADE SIGNAL OVERLAY
    # ========================================================

    def show_trade_signal(self, signal):

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

            print(signal)

            self.webview.page().runJavaScript(
                js,
                lambda result: print(
                    "Trade Signal JS Returned:",
                    result
                )
            )

        except Exception:

            import traceback

            traceback.print_exc()