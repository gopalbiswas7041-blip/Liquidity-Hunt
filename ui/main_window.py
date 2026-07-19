import sys

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt

from ui.dashboard_widgets import DashboardWidget
from ui.controller import Controller
from ui.styles import APP_STYLE


class LiquidityHunterWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Liquidity Hunter AI V13")
        self.resize(500, 700)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.setStyleSheet(APP_STYLE)

        self.controller = Controller()
        self.dashboard = DashboardWidget()

        self.setCentralWidget(self.dashboard)

        self.dashboard.refresh_button.clicked.connect(self.refresh_signal)

        self.refresh_signal()

    def refresh_signal(self):
        data = self.controller.refresh()
        self.dashboard.update_dashboard(data)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = LiquidityHunterWindow()
    window.show()

    sys.exit(app.exec())
