from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView


class ChartView(QWebEngineView):
    def __init__(self):
        super().__init__()

        html_path = (
            Path(_file_).parent
            / "resources"
            / "chart.html"
        )

        self.load(QUrl.fromLocalFile(str(html_path.resolve())))