import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QScrollArea,
    QWidget,
    QHBoxLayout,
    QVBoxLayout
)

from PySide6.QtCore import Qt, QTimer

from ui.dashboard_widgets import DashboardWidget
from ui.watchlist_widget import WatchlistWidget
from ui.chart_widget import ChartWidget
from ui.controller import Controller
from ui.styles import APP_STYLE


class LiquidityHunterWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Liquidity Hunter AI V16")
        self.resize(1400, 900)
        self.setMinimumSize(1200, 700)

        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.setStyleSheet(APP_STYLE)

        self.controller = Controller()

        self.dashboard = DashboardWidget()
        self.chart = ChartWidget()
        self.watchlist = WatchlistWidget()

        # ---------------------------------
        # Dashboard Scroll Area
        # ---------------------------------

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.scroll.setWidget(self.dashboard)

        # ---------------------------------
        # Left Panel (Chart + Dashboard)
        # ---------------------------------

        left_panel = QWidget()

        left_layout = QVBoxLayout(left_panel)

        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(self.chart)
        left_layout.addWidget(self.scroll)

        # ---------------------------------
        # Main Layout
        # ---------------------------------

        container = QWidget()

        layout = QHBoxLayout(container)

        layout.addWidget(left_panel, 3)
        layout.addWidget(self.watchlist, 1)

        self.setCentralWidget(container)

        # ---------------------------------

        self.dashboard.refresh_button.clicked.connect(
            self.refresh_signal
        )

        self.refresh_signal()

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.refresh_signal
        )

        self.timer.start(30000)

    def refresh_signal(self):

        data = self.controller.refresh()

        self.dashboard.update_dashboard(data)


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = LiquidityHunterWindow()

    window.show()

    sys.exit(app.exec())