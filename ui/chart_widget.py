from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class ChartWidget(QWidget):

    def __ini__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("📈 LIVE MARKET CHART")
        title.setAlignment(Qt.AlignCenter)

        title.setStyleSheet("""
            QLabel{
                font-size:18px;
                font-weight:bold;
                color:white;
                padding:10px;
            }
        """)

        chart_placeholder = QLabel()

        chart_placeholder.setAlignment(Qt.AlignCenter)

        chart_placeholder.setMinimumHeight(500)

        chart_placeholder.setStyleSheet("""
            QLabel{
                background:#1c1c1c;
                border:2px solid #444;
                border-radius:10px;
                color:#888;
                font-size:16px;
            }
        """)

        chart_placeholder.setText(
            "Live Chart Loading...\n\n"
            "V16 Phase 1"
        )

        layout.addWidget(title)
        layout.addWidget(chart_placeholder)