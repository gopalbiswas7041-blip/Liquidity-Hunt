from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtWebEngineWidgets import QWebEngineView


class ChartWidget(QWidget):

    def __init__(self):
        super().__init__()

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

        # WebEngine View
        self.webview = QWebEngineView()
        self.webview.setMinimumHeight(500)

        # chart.html path
        html_file = (
            Path(__file__).parent
            / "resources"
            / "chart.html"
        )

        # Load HTML
        self.webview.load(
            QUrl.fromLocalFile(str(html_file.resolve()))
        )

        layout.addWidget(title)
        layout.addWidget(self.webview)