import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFrame,
)


class LiquidityHunterWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Liquidity Hunter AI")
        self.resize(420, 700)

        # Window always on top
        self.setWindowFlag(Qt.WindowStaysOnTopHint)

        # Dark Theme
        self.setStyleSheet("""
            QMainWindow{
                background-color:#121212;
            }

            QLabel{
                color:white;
            }

            QFrame{
                background:#1d1d1d;
                border:1px solid #333333;
                border-radius:10px;
            }

            QPushButton{
                background:#2d89ef;
                color:white;
                border:none;
                border-radius:8px;
                padding:8px;
                font-size:12pt;
            }

            QPushButton:hover{
                background:#1f6fd1;
            }
        """)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        central.setLayout(layout)

        title = QLabel("LIQUIDITY HUNTER AI")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))

        layout.addWidget(title)

        status = QLabel("🟢 LIVE")
        status.setAlignment(Qt.AlignCenter)
        status.setFont(QFont("Segoe UI", 12))

        layout.addWidget(status)

        card = QFrame()

        card_layout = QVBoxLayout()

        card_layout.addWidget(QLabel("Symbol : NIFTY"))
        card_layout.addWidget(QLabel("Timeframe : 5 Minute"))
        card_layout.addWidget(QLabel("Signal : NO TRADE"))
        card_layout.addWidget(QLabel("Confidence : 0%"))
        card_layout.addWidget(QLabel("Entry : --"))
        card_layout.addWidget(QLabel("Stop Loss : --"))
        card_layout.addWidget(QLabel("Target : --"))

        card.setLayout(card_layout)

        layout.addWidget(card)

        refresh = QPushButton("Refresh Signal")

        layout.addWidget(refresh)

        layout.addStretch()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = LiquidityHunterWindow()
    window.show()

    sys.exit(app.exec())