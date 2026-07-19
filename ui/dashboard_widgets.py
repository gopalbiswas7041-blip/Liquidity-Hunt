from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QFormLayout, QGroupBox
)


class DashboardWidget(QWidget):
    """
    Liquidity Hunter AI Dashboard Widget
    """

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        group = QGroupBox("Trading Dashboard")
        form = QFormLayout(group)

        self.signal = QLabel("NO TRADE")
        self.confidence = QLabel("0%")
        self.quality = QLabel("-")
        self.status = QLabel("WAIT")
        self.entry = QLabel("--")
        self.stop_loss = QLabel("--")
        self.take_profit = QLabel("--")
        self.risk = QLabel("--")
        self.reward = QLabel("--")
        self.rr = QLabel("--")
        self.volatility = QLabel("NORMAL")
        self.trade_score = QLabel("0")
        self.trade_reason = QLabel("-")

        form.addRow("Signal", self.signal)
        form.addRow("Confidence", self.confidence)
        form.addRow("Quality", self.quality)
        form.addRow("Status", self.status)
        form.addRow("Entry", self.entry)
        form.addRow("Stop Loss", self.stop_loss)
        form.addRow("Take Profit", self.take_profit)
        form.addRow("Risk", self.risk)
        form.addRow("Reward", self.reward)
        form.addRow("Risk : Reward", self.rr)
        form.addRow("Volatility", self.volatility)
        form.addRow("AI Score", self.trade_score)
        form.addRow("Reason", self.trade_reason)

        self.refresh_button = QPushButton("Refresh Signal")

        layout.addWidget(group)
        layout.addWidget(self.refresh_button)

    def update_dashboard(self, data: dict):
        self.signal.setText(str(data.get("signal", "NO TRADE")))
        self.confidence.setText(str(data.get("confidence", "0")))
        self.quality.setText(str(data.get("quality", "-")))
        self.status.setText(str(data.get("status", "-")))
        self.entry.setText(str(data.get("entry", "--")))
        self.stop_loss.setText(str(data.get("stop_loss", "--")))
        self.take_profit.setText(str(data.get("take_profit", "--")))
        self.risk.setText(str(data.get("risk", "--")))
        self.reward.setText(str(data.get("reward", "--")))
        self.rr.setText(str(data.get("risk_reward", "--")))
        self.volatility.setText(str(data.get("volatility", "NORMAL")))
        self.trade_score.setText(str(data.get("trade_score", "0")))

        reasons = data.get("trade_reason", [])
        if isinstance(reasons, list):
            self.trade_reason.setText(", ".join(map(str, reasons)) if reasons else "-")
        else:
            self.trade_reason.setText(str(reasons))
