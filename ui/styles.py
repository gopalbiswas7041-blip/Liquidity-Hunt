# ==========================================
# Liquidity Hunter AI V13
# styles.py
# ==========================================

APP_STYLE = """
QMainWindow {
    background-color: #121212;
}

QWidget {
    background-color: #121212;
    color: white;
    font-family: Segoe UI;
    font-size: 11pt;
}

QLabel {
    color: white;
}

QGroupBox {
    border: 2px solid #333333;
    border-radius: 8px;
    margin-top: 12px;
    padding: 10px;
    font-weight: bold;
    color: white;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QPushButton {
    background-color: #00C853;
    color: white;
    border-radius: 8px;
    padding: 8px;
    font-size: 11pt;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #00E676;
}

QPushButton:pressed {
    background-color: #00A843;
}
"""

# ------------------------------------------
# Signal Colors
# ------------------------------------------

BUY_COLOR = "#00E676"
SELL_COLOR = "#FF5252"
WAIT_COLOR = "#FFD54F"
TEXT_COLOR = "#FFFFFF"

# ------------------------------------------
# Status Colors
# ------------------------------------------

READY_COLOR = "#00E676"
WATCH_COLOR = "#29B6F6"
AVOID_COLOR = "#FF5252"

# ------------------------------------------
# Dashboard Card Style
# ------------------------------------------

CARD_STYLE = """
QFrame{
    background-color:#1E1E1E;
    border:1px solid #2E2E2E;
    border-radius:10px;
}
"""