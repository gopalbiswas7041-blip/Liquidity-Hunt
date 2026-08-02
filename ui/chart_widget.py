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

        self.chart_ready = False
        self.pending_candles = None

        # NEW
        self.pending_signal = None

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
            QUrl.fromLocalFile(str(html_file.resolve()))
        )

        layout.addWidget(title)
        layout.addWidget(self.webview)

        self.live_candle_signal.connect(
            self._update_last_candle_gui
        )

        print("CONNECT DONE")
        print(self._update_last_candle_gui)

    # ------------------------------------------------

    def _on_chart_loaded(self, ok):

        print(">>> _on_chart_loaded() CALLED <<<")

        self.chart_ready = ok

        print("===================================")
        print("Chart Loaded :", ok)
        print("===================================")

        if ok and self.pending_candles is not None:

            print("Sending Pending Candle Data...")

            data = self.pending_candles
            self.pending_candles = None

            self.set_chart_data(data)

        # -------------------------------
        # NEW
        # Send pending AI signal
        # -------------------------------
        if ok and self.pending_signal is not None:

            print("Sending Pending Trade Signal...")

            signal = self.pending_signal
            self.pending_signal = None

            self.show_trade_signal(signal)

        else:

            print("No Pending Candle Data")

    # ------------------------------------------------

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

        print("========== FIRST CANDLE ==========")
        print(candles[0])

        print("========== LAST CANDLE ==========")
        print(candles[-1])

        print("==================================")

        return candles

    # ------------------------------------------------

    def set_chart_data(self, dataframe):

        print("set_chart_data() called")
        print("Chart Ready :", self.chart_ready)

        if not self.chart_ready:

            print("Chart not ready. Saving pending candles.")

            self.pending_candles = dataframe

            return

        candles = self._convert_dataframe(dataframe)

        print("Candles Sent :", len(candles))

        js = (
            "window.setChartData("
            + json.dumps(candles)
            + ");"
        )

        self.webview.page().runJavaScript(js)

    # ------------------------------------------------

    def update_last_candle(self, candle):

        print("ChartWidget.update_last_candle() CALLED")
        print(candle)

        if not self.chart_ready:
            return

        if candle is None:
            return

        print(
            "LIVE DEBUG:",
            candle.timestamp,
            candle.timestamp.tzinfo,
            candle.timestamp.timestamp(),
        )

        candle_data = {

            "time": int(candle.timestamp.timestamp()),
            "open": float(candle.open),
            "high": float(candle.high),
            "low": float(candle.low),
            "close": float(candle.close)

        }

        print("========== LIVE CANDLE ==========")
        print(candle_data)
        print(type(candle_data["time"]))
        print("================================")

        print(type(self))
        print(type(self.live_candle_signal))
        print(self.live_candle_signal)

        self.live_candle_signal.emit(candle_data)

    @Slot(dict)
    def _update_last_candle_gui(self, candle_data):

        try:

            print("GUI SLOT CALLED")
            print(candle_data)

            if not self.chart_ready:
                return

            js = (
                "window.updateLastCandle("
                + json.dumps(candle_data)
                + ");"
            )

            print(js)

            self.webview.page().runJavaScript(
                js,
                lambda result: print("JS Returned:", result)
            )

        except Exception as e:

            import traceback
            traceback.print_exc()

    # ------------------------------------------------
    # AI Trade Signal Overlay
    # ------------------------------------------------

    def show_trade_signal(self, signal):

        try:

            # ----------------------------
            # NEW
            # ----------------------------
            if not self.chart_ready:

                print("Chart Not Ready -> Saving Trade Signal")

                self.pending_signal = signal

                return

            js = (
                "window.showTradeSignal("
                + json.dumps(signal)
                + ");"
            )

            print("Sending Trade Signal To JS")
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