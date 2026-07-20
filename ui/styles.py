# ==========================================
# Liquidity Hunter AI V15.1
# Professional Dark Theme
# ==========================================

APP_STYLE = """
QMainWindow{
    background-color:#0E1117;
}

QWidget{
    background-color:#0E1117;
    color:#E6EDF3;
    font-family:'Segoe UI';
    font-size:11pt;
}

QLabel{
    color:#E6EDF3;
    background:transparent;
}

QGroupBox{
    background-color:#161B22;
    border:1px solid #30363D;
    border-radius:14px;
    margin-top:16px;
    padding:16px;
    font-size:12pt;
    font-weight:700;
    color:#58A6FF;
}

QGroupBox::title{
    subcontrol-origin:margin;
    left:14px;
    padding:0 8px;
}

QFrame{
    background-color:#161B22;
    border:1px solid #30363D;
    border-radius:12px;
}

QPushButton{
    background-color:#238636;
    color:white;
    border:none;
    border-radius:10px;
    padding:10px;
    font-size:11pt;
    font-weight:bold;
}

QPushButton:hover{
    background-color:#2EA043;
}

QPushButton:pressed{
    background-color:#1F6F2C;
}

QLineEdit,
QTextEdit,
QPlainTextEdit{
    background:#0D1117;
    color:#E6EDF3;
    border:1px solid #30363D;
    border-radius:8px;
    padding:6px;
}

QScrollArea{
    border:none;
    background:#0E1117;
}

QScrollBar:vertical{
    background:#161B22;
    width:10px;
    border:none;
}

QScrollBar::handle:vertical{
    background:#30363D;
    border-radius:5px;
}

QScrollBar::handle:vertical:hover{
    background:#484F58;
}
"""

# ------------------------------------------
# Signal Colors
# ------------------------------------------

BUY_COLOR = "#00E676"
SELL_COLOR = "#FF5252"
WAIT_COLOR = "#FFD54F"

TEXT_COLOR = "#E6EDF3"

# ------------------------------------------
# Status Colors
# ------------------------------------------

READY_COLOR = "#00E676"
WATCH_COLOR = "#29B6F6"
AVOID_COLOR = "#FF5252"

# ------------------------------------------
# Dashboard Cards
# ------------------------------------------

CARD_STYLE = """
QFrame{
    background-color:#161B22;
    border:1px solid #30363D;
    border-radius:14px;
}
"""

# ------------------------------------------
# Accent Colors
# ------------------------------------------

PRIMARY_COLOR = "#58A6FF"
SUCCESS_COLOR = "#00E676"
WARNING_COLOR = "#FFD54F"
DANGER_COLOR = "#FF5252"
BACKGROUND_COLOR = "#0E1117"
CARD_COLOR = "#161B22"
BORDER_COLOR = "#30363D"