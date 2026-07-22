from pathlib import Path
import json

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtWebEngineWidgets import QWebEngineView


class ChartWidget(QWidget):

    def __init__(self):
        super().__init__()

        self.chart_ready = False
        self.pending_candles = None

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

    # ------------------------------------------------

    def _on_chart_loaded(self, ok):

        self.chart_ready = ok

        print("===================================")
        print("Chart Loaded :", ok)
        print("===================================")

        if ok and self.pending_candles is not None:

            print("Sending Pending Candle Data...")

            data = self.pending_candles
            self.pending_candles = None

            self.set_chart_data(data)

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

            candles.append({

                "time": int(index.timestamp()),

                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"])

            })

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

    def update_last_candle(self, dataframe):

        if not self.chart_ready:
            return

        candles = self._convert_dataframe(dataframe)

        if len(candles) == 0:
            return

        js = (
            "window.updateLastCandle("
            + json.dumps(candles[-1])
            + ");"
        )

        self.webview.page().runJavaScript(js)