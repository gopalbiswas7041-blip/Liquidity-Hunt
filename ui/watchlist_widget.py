from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QLineEdit
)


class WatchlistWidget(QWidget):
    """
    Liquidity Hunter AI
    Watchlist Manager V15.2
    """

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ==========================================
        # TITLE
        # ==========================================

        self.title = QLabel("WATCHLIST")

        # ==========================================
        # SYMBOL INPUT
        # ==========================================

        self.symbol_input = QLineEdit()

        self.symbol_input.setPlaceholderText(
            "Enter Symbol (Example: B-BTC_USDT)"
        )

        # ==========================================
        # WATCHLIST
        # ==========================================

        self.watchlist = QListWidget()

        # Default Symbols

        self.watchlist.addItem("B-BTC_USDT")
        self.watchlist.addItem("B-ETH_USDT")
        self.watchlist.addItem("B-SOL_USDT")

        # ==========================================
        # BUTTONS
        # ==========================================

        self.add_button = QPushButton("Add")

        self.remove_button = QPushButton("Remove")

        self.scan_button = QPushButton("Scan Watchlist")

        button_layout = QHBoxLayout()

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)

        # ==========================================
        # MAIN LAYOUT
        # ==========================================

        layout.addWidget(self.title)
        layout.addWidget(self.symbol_input)
        layout.addWidget(self.watchlist)
        layout.addLayout(button_layout)
        layout.addWidget(self.scan_button)