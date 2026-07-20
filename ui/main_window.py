import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QScrollArea
)

from PySide6.QtCore import Qt, QTimer

from ui.dashboard_widgets import DashboardWidget
from ui.controller import Controller
from ui.styles import APP_STYLE


class LiquidityHunterWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Liquidity Hunter AI V15.1")
        self.resize(650, 900)
        self.setMinimumSize(600, 700)

        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.setStyleSheet(APP_STYLE)

        self.controller = Controller()
        self.dashboard = DashboardWidget()

        # -------------------------------
        # Scroll Area
        # -------------------------------

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.scroll.setWidget(self.dashboard)

        self.setCentralWidget(self.scroll)

        # -------------------------------

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