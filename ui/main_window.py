import sys

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt, QTimer

from ui.dashboard_widgets import DashboardWidget
from ui.controller import Controller
from ui.styles import APP_STYLE


class LiquidityHunterWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Liquidity Hunter AI V14.5")
        self.resize(550, 900)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.setStyleSheet(APP_STYLE)

        self.controller = Controller()
        self.dashboard = DashboardWidget()

        self.setCentralWidget(self.dashboard)

        self.dashboard.refresh_button.clicked.connect(self.refresh_signal)

        # First Refresh
        self.refresh_signal()

        # Auto Refresh every 30 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_signal)
        self.timer.start(30000)

    def refresh_signal(self):
        data = self.controller.refresh()
        self.dashboard.update_dashboard(data)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = LiquidityHunterWindow()
    window.show()

    sys.exit(app.exec())
