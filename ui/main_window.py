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

        self.setWindowTitle("Liquidity Hunter AI V17.2")
        self.resize(1400, 900)
        self.setMinimumSize(1200, 700)

        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.setStyleSheet(APP_STYLE)

        self.controller = Controller()

        self.dashboard = DashboardWidget()
        self.chart = ChartWidget()
        self.watchlist = WatchlistWidget()

        self.controller.websocket.set_chart_widget(
            self.chart
        )

        # -----------------------------
        # Dashboard Scroll Area
        # -----------------------------

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setWidget(self.dashboard)

        # -----------------------------
        # Left Panel
        # -----------------------------

        left_panel = QWidget()

        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(self.chart)
        left_layout.addWidget(self.scroll)

        # -----------------------------
        # Main Layout
        # -----------------------------

        container = QWidget()

        layout = QHBoxLayout(container)

        layout.addWidget(left_panel, 3)
        layout.addWidget(self.watchlist, 1)

        self.setCentralWidget(container)

        # -----------------------------

        self.dashboard.refresh_button.clicked.connect(
            self.refresh_signal
        )

        self.refresh_signal()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_signal)
        self.timer.start(30000)

    # =====================================================
    # Refresh Signal
    # =====================================================

    def refresh_signal(self):

        print("\n==============================")
        print("===== REFRESH START =====")
        print("==============================")

        data = self.controller.refresh()

        print("Returned Keys :", list(data.keys()))

        data_5m = data.get("data_5m")

        print("data_5m Type :", type(data_5m))
        print("data_5m None :", data_5m is None)

        if data_5m is not None:
            try:
                print("Rows :", len(data_5m))
                print(data_5m.tail())
            except Exception as e:
                print("DataFrame Error :", e)

        # Dashboard
        self.dashboard.update_dashboard(data)

        # Chart
        try:

            if data_5m is not None:

                print("Calling ChartWidget.set_chart_data()")

                self.chart.set_chart_data(data_5m)

                print("ChartWidget.set_chart_data() Finished")

            else:

                print("No Chart Data Available")

        except Exception as e:

            print("Chart Update Error :", e)

        print("==============================")
        print("===== REFRESH END =====")
        print("==============================\n")


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = LiquidityHunterWindow()

    window.show()

    sys.exit(app.exec())