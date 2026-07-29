import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QSizePolicy
)

from PySide6.QtCore import (
    Qt,
    QTimer
)

from PySide6.QtGui import (
    QFont
)

from ui.dashboard_widgets import DashboardWidget
from ui.watchlist_widget import WatchlistWidget
from ui.chart_widget import ChartWidget
from ui.controller import Controller
from ui.styles import APP_STYLE


class LiquidityHunterWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # ====================================================
        # Window Settings
        # ====================================================

        self.setWindowTitle("Liquidity Hunter AI V18 Professional")

        self.resize(1700, 950)

        self.setMinimumSize(1400, 850)

        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.setStyleSheet(APP_STYLE)

        # ====================================================
        # Controller
        # ====================================================

        self.controller = Controller()

        # ====================================================
        # Main Widgets
        # ====================================================

        self.dashboard = DashboardWidget()

        self.chart = ChartWidget()

        self.chart_loaded = False

        self.watchlist = WatchlistWidget()

        # Connect Live Chart
        self.controller.websocket.set_chart_widget(
            self.chart
        )

        # ====================================================
        # Dashboard Scroll Area
        # ====================================================

        self.dashboard_scroll = QScrollArea()

        self.dashboard_scroll.setWidgetResizable(True)

        self.dashboard_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.dashboard_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.dashboard_scroll.setWidget(
            self.dashboard
        )

        # ====================================================
        # Main Container
        # ====================================================

        self.container = QWidget()

        self.main_layout = QVBoxLayout(self.container)

        self.main_layout.setContentsMargins(8, 8, 8, 8)

        self.main_layout.setSpacing(8)

        # ====================================================
        # Top Toolbar
        # ====================================================

        self.top_bar = QFrame()

        self.top_bar.setFixedHeight(60)

        self.top_layout = QHBoxLayout(self.top_bar)

        self.top_layout.setContentsMargins(15, 10, 15, 10)

        self.top_layout.setSpacing(15)

        self.title_label = QLabel("Liquidity Hunter AI")

        self.title_label.setFont(
            QFont("Segoe UI", 14, QFont.Bold)
        )

        self.top_layout.addWidget(
            self.title_label
        )

        self.top_layout.addStretch()

        self.main_layout.addWidget(
            self.top_bar
        )

        # ====================================================
        # Trading Area
        # ====================================================

        self.trading_area = QWidget()

        self.trade_layout = QHBoxLayout(
            self.trading_area
        )

        self.trade_layout.setContentsMargins(
            0, 0, 0, 0
        )

        self.trade_layout.setSpacing(8)

        # ====================================================
        # LEFT PANEL
        # ====================================================

        self.left_panel = QFrame()

        self.left_panel.setMinimumWidth(330)

        self.left_panel.setMaximumWidth(380)

        self.left_layout = QVBoxLayout(self.left_panel)

        self.left_layout.setContentsMargins(5, 5, 5, 5)

        self.left_layout.setSpacing(8)

        self.left_layout.addWidget(
            self.dashboard_scroll
        )

        # ====================================================
        # CENTER PANEL
        # ====================================================

        self.center_panel = QFrame()

        self.center_layout = QVBoxLayout(self.center_panel)

        self.center_layout.setContentsMargins(
            0, 0, 0, 0
        )

        self.center_layout.setSpacing(5)

        self.chart.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.center_layout.addWidget(
            self.chart
        )

        # ====================================================
        # RIGHT PANEL
        # ====================================================

        self.right_panel = QFrame()

        self.right_panel.setMinimumWidth(270)

        self.right_panel.setMaximumWidth(330)

        self.right_layout = QVBoxLayout(self.right_panel)

        self.right_layout.setContentsMargins(
            5, 5, 5, 5
        )

        self.right_layout.setSpacing(10)

        self.right_layout.addWidget(
            self.watchlist
        )

        # ====================================================
        # ADD PANELS
        # ====================================================

        self.trade_layout.addWidget(
            self.left_panel,
            2
        )

        self.trade_layout.addWidget(
            self.center_panel,
            6
        )

        self.trade_layout.addWidget(
            self.right_panel,
            2
        )

        self.main_layout.addWidget(
            self.trading_area
        )

        # ====================================================
        # TIMEFRAME PANEL
        # ====================================================

        self.timeframe_frame = QFrame()

        self.timeframe_layout = QGridLayout(
            self.timeframe_frame
        )

        self.timeframe_layout.setContentsMargins(
            5, 5, 5, 5
        )

        self.timeframe_layout.setSpacing(6)

        self.tf_title = QLabel("Timeframes")

        self.tf_title.setAlignment(Qt.AlignCenter)

        self.timeframe_layout.addWidget(
            self.tf_title,
            0,
            0,
            1,
            4
        )

        self.tf_buttons = []

        timeframes = [
            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1H",
            "4H",
            "1D"
        ]

        row = 1
        col = 0

        for tf in timeframes:

            btn = QPushButton(tf)

            btn.setMinimumHeight(34)

            btn.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed
            )

            self.tf_buttons.append(btn)

            self.timeframe_layout.addWidget(
                btn,
                row,
                col
            )

            col += 1

            if col == 4:

                col = 0
                row += 1

        self.right_layout.addWidget(
            self.timeframe_frame
        )

        # ====================================================
        # STATUS BAR
        # ====================================================

        self.status_bar = QFrame()

        self.status_layout = QHBoxLayout(
            self.status_bar
        )

        self.status_layout.setContentsMargins(
            10,
            6,
            10,
            6
        )

        self.status_label = QLabel(
            "Socket : Connected   |   Market : Ready   |   AI : Running"
        )

        self.status_layout.addWidget(
            self.status_label
        )

        self.main_layout.addWidget(
            self.status_bar
        )

        # ====================================================
        # SET CENTRAL WIDGET
        # ====================================================

        self.setCentralWidget(
            self.container
        )

        # ====================================================
        # SIGNAL CONNECTIONS
        # ====================================================

        self.dashboard.refresh_button.clicked.connect(
            self.refresh_signal
        )

        # ====================================================
        # FIRST REFRESH
        # ====================================================

        self.refresh_signal()

        # ====================================================
        # AUTO REFRESH TIMER
        # ====================================================

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.refresh_signal
        )

        # Refresh every 30 seconds
        self.timer.start(30000)

    # ====================================================
    # Refresh Signal
    # ====================================================

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

        # ====================================================
        # Dashboard Update
        # ====================================================

        self.dashboard.update_dashboard(data)

        # ====================================================
        # Chart Update
        # ====================================================

        try:

            if (not self.chart_loaded) and (data_5m is not None):

                print("Loading Historical Chart...")

                self.chart.set_chart_data(data_5m)

                self.chart_loaded = True

                print("Historical Chart Loaded")

        except Exception as e:

            print("Chart Update Error :", e)


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = LiquidityHunterWindow()

    window.show()

    sys.exit(app.exec())