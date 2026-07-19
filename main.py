import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import LiquidityHunterWindow
from ui.styles import APP_STYLE


def main():
    app = QApplication(sys.argv)

    app.setStyleSheet(APP_STYLE)

    window = LiquidityHunterWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()