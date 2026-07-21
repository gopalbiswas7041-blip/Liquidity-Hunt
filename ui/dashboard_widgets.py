from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QFrame
)

from ui.styles import (
    BUY_COLOR,
    SELL_COLOR,
    WAIT_COLOR,
    READY_COLOR,
    AVOID_COLOR,
    TEXT_COLOR
)


class DashboardWidget(QWidget):
    """
    Liquidity Hunter AI
    Professional Dashboard V15
    """

    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(12)

        # ====================================================
        # PROFESSIONAL HEADER CARD
        # ====================================================

        header = QFrame()
        header.setObjectName("headerCard")

        header_layout = QHBoxLayout(header)

        left_layout = QVBoxLayout()

        self.title = QLabel("LIQUIDITY HUNTER AI")
        self.title.setObjectName("headerTitle")

        self.subtitle = QLabel("Professional Trading Dashboard")
        self.subtitle.setObjectName("headerSubtitle")

        left_layout.addWidget(self.title)
        left_layout.addWidget(self.subtitle)

        right_layout = QVBoxLayout()

        self.live_status = QLabel("🟢 LIVE")
        self.symbol = QLabel("BTC/USDT")
        self.timeframe = QLabel("5m")
        self.live_price = QLabel("--")

        right_layout.addWidget(self.live_status)
        right_layout.addWidget(self.symbol)
        right_layout.addWidget(self.timeframe)
        right_layout.addWidget(self.live_price)

        header_layout.addLayout(left_layout)
        header_layout.addStretch()
        header_layout.addLayout(right_layout)

        main_layout.addWidget(header)

        # ====================================================
        # MARKET CONTEXT
        # ====================================================

        market_group = QGroupBox("Market Context")

        market_form = QFormLayout()

        self.trend = QLabel("--")
        self.market_phase = QLabel("--")
        self.liquidity = QLabel("--")
        self.choch = QLabel("--")
        self.order_block = QLabel("--")
        self.fvg = QLabel("--")

        market_form.addRow("Trend", self.trend)
        market_form.addRow("Market Phase", self.market_phase)
        market_form.addRow("Liquidity Sweep", self.liquidity)
        market_form.addRow("CHoCH", self.choch)
        market_form.addRow("Order Block", self.order_block)
        market_form.addRow("Fair Value Gap", self.fvg)

        market_group.setLayout(market_form)

        # ====================================================
        # TRADE SETUP
        # ====================================================

        trade_group = QGroupBox("Trade Setup")

        trade_form = QFormLayout()

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

        trade_form.addRow("Signal", self.signal)
        trade_form.addRow("Confidence", self.confidence)
        trade_form.addRow("Quality", self.quality)
        trade_form.addRow("Status", self.status)

        trade_form.addRow("Entry", self.entry)
        trade_form.addRow("Stop Loss", self.stop_loss)
        trade_form.addRow("Take Profit", self.take_profit)

        trade_form.addRow("Risk", self.risk)
        trade_form.addRow("Reward", self.reward)
        trade_form.addRow("Risk : Reward", self.rr)

        trade_form.addRow("Volatility", self.volatility)

        trade_group.setLayout(trade_form)

        # ====================================================
        # AI ANALYSIS
        # ====================================================

        ai_group = QGroupBox("AI Analysis")

        ai_form = QFormLayout()

        self.trade_score = QLabel("0")
        self.entry_type = QLabel("--")
        self.entry_zone = QLabel("--")
        self.confirmation = QLabel("--")
        self.entry_quality = QLabel("--")
        self.trade_reason = QLabel("--")

        ai_form.addRow("AI Score", self.trade_score)
        ai_form.addRow("Entry Type", self.entry_type)
        ai_form.addRow("Entry Zone", self.entry_zone)
        ai_form.addRow("Confirmation", self.confirmation)
        ai_form.addRow("Entry Quality", self.entry_quality)
        ai_form.addRow("Reason", self.trade_reason)

        ai_group.setLayout(ai_form)

        # ====================================================
        # REFRESH BUTTON
        # ====================================================

        self.refresh_button = QPushButton("Refresh Signal")

        self.refresh_button.setMinimumHeight(42)

        # ====================================================
        # ADD TO MAIN LAYOUT
        # ====================================================

        main_layout.addWidget(market_group)
        main_layout.addWidget(trade_group)
        main_layout.addWidget(ai_group)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        main_layout.addWidget(line)
        main_layout.addWidget(self.refresh_button)

    # ====================================================
    # UPDATE DASHBOARD
    # ====================================================

    def update_dashboard(self, data: dict):

        # -----------------------
        # Market Context
        # -----------------------

        self.trend.setText(
            str(data.get("trend", "--"))
        )

        self.market_phase.setText(
            str(data.get("market_phase", "--"))
        )

        self.liquidity.setText(
            "YES" if data.get("liquidity_sweep", False) else "NO"
        )

        self.choch.setText(
            "YES" if data.get("choch", False) else "NO"
        )

        self.order_block.setText(
            "YES" if data.get("order_block", False) else "NO"
        )

        self.fvg.setText(
            "YES" if data.get("fvg", False) else "NO"
        )

        # -----------------------
        # Trade Setup
        # -----------------------

        self.signal.setText(
            str(data.get("signal", "NO TRADE"))
        )

        self.confidence.setText(
            str(data.get("confidence", "0"))
        )

        self.quality.setText(
            str(data.get("quality", "-"))
        )

        self.status.setText(
            str(data.get("status", "WAIT"))
        )

        self.entry.setText(
            str(data.get("entry", "--"))
        )

        self.stop_loss.setText(
            str(data.get("stop_loss", "--"))
        )

        self.take_profit.setText(
            str(data.get("take_profit", "--"))
        )

        self.risk.setText(
            str(data.get("risk", "--"))
        )

        self.reward.setText(
            str(data.get("reward", "--"))
        )

        self.rr.setText(
            str(data.get("risk_reward", "--"))
        )

        self.volatility.setText(
            str(data.get("volatility", "NORMAL"))
        )

        # -----------------------
        # AI Analysis
        # -----------------------

        self.trade_score.setText(
            str(data.get("trade_score", "0"))
        )

        self.entry_type.setText(
            str(data.get("entry_type", "--"))
        )

        self.entry_zone.setText(
            str(data.get("entry_zone", "--"))
        )

        self.confirmation.setText(
            str(data.get("confirmation", "--"))
        )

        self.entry_quality.setText(
            str(data.get("entry_quality", "--"))
        )

        reasons = data.get("trade_reason", [])

        if isinstance(reasons, list):
            self.trade_reason.setText(
                ", ".join(map(str, reasons))
                if reasons else "-"
            )
        else:
            self.trade_reason.setText(
                str(reasons)
            )

            # ====================================================
        # SIGNAL COLOR
        # ====================================================

        signal = str(
            data.get("signal", "NO TRADE")
        ).upper()

        if signal == "BUY":

            self.signal.setStyleSheet(
                f"""
                color:{BUY_COLOR};
                font-size:18px;
                font-weight:bold;
                """
            )

        elif signal == "SELL":

            self.signal.setStyleSheet(
                f"""
                color:{SELL_COLOR};
                font-size:18px;
                font-weight:bold;
                """
            )

        else:

            self.signal.setStyleSheet(
                f"""
                color:{WAIT_COLOR};
                font-size:18px;
                font-weight:bold;
                """
            )

        # ====================================================
        # STATUS COLOR
        # ====================================================

        status = str(
            data.get(
                "trade_status",
                data.get("status", "WAIT")
            )
        ).upper()

        if status == "READY":

            self.status.setStyleSheet(
                f"""
                color:{READY_COLOR};
                font-weight:bold;
                """
            )

        elif status == "AVOID":

            self.status.setStyleSheet(
                f"""
                color:{AVOID_COLOR};
                font-weight:bold;
                """
            )

        else:

            self.status.setStyleSheet(
                f"""
                color:{TEXT_COLOR};
                font-weight:bold;
                """
            )

        # ====================================================
        # TREND COLOR
        # ====================================================

        trend = str(
            data.get("trend", "")
        ).upper()

        if trend == "BUY":

            self.trend.setStyleSheet(
                f"color:{BUY_COLOR}; font-weight:bold;"
            )

        elif trend == "SELL":

            self.trend.setStyleSheet(
                f"color:{SELL_COLOR}; font-weight:bold;"
            )

        else:

            self.trend.setStyleSheet(
                f"color:{TEXT_COLOR};"
            )

            # ====================================================
        # MARKET CONTEXT COLOR
        # ====================================================

        yes_style = f"""
        color:{BUY_COLOR};
        font-weight:bold;
        """

        no_style = f"""
        color:{SELL_COLOR};
        font-weight:bold;
        """

        self.liquidity.setStyleSheet(
            yes_style if self.liquidity.text() == "YES" else no_style
        )

        self.choch.setStyleSheet(
            yes_style if self.choch.text() == "YES" else no_style
        )

        self.order_block.setStyleSheet(
            yes_style if self.order_block.text() == "YES" else no_style
        )

        self.fvg.setStyleSheet(
            yes_style if self.fvg.text() == "YES" else no_style
        )

        # ====================================================
        # CONFIDENCE COLOR
        # ====================================================

        try:
            confidence = float(
                str(data.get("confidence", "0")).replace("%", "")
            )

            if confidence >= 80:
                self.confidence.setStyleSheet(
                    f"color:{BUY_COLOR}; font-weight:bold;"
                )

            elif confidence >= 60:
                self.confidence.setStyleSheet(
                    f"color:{WAIT_COLOR}; font-weight:bold;"
                )

            else:
                self.confidence.setStyleSheet(
                    f"color:{SELL_COLOR}; font-weight:bold;"
                )

        except Exception:
            self.confidence.setStyleSheet(
                f"color:{TEXT_COLOR};"
            )

        # ====================================================
        # AI SCORE COLOR
        # ====================================================

        try:

            score = int(data.get("trade_score", 0))

            if score >= 80:
                self.trade_score.setStyleSheet(
                    f"color:{BUY_COLOR}; font-weight:bold;"
                )

            elif score >= 60:
                self.trade_score.setStyleSheet(
                    f"color:{WAIT_COLOR}; font-weight:bold;"
                )

            else:
                self.trade_score.setStyleSheet(
                    f"color:{SELL_COLOR}; font-weight:bold;"
                )

        except Exception:
            self.trade_score.setStyleSheet(
                f"color:{TEXT_COLOR};"
            )

            # ====================================================
        # ENTRY QUALITY COLOR
        # ====================================================

        quality = str(
            data.get("entry_quality", "--")
        ).upper()

        if quality == "A":

            self.entry_quality.setStyleSheet(
                f"color:{BUY_COLOR}; font-weight:bold;"
            )

        elif quality == "B":

            self.entry_quality.setStyleSheet(
                f"color:{READY_COLOR}; font-weight:bold;"
            )

        elif quality == "C":

            self.entry_quality.setStyleSheet(
                f"color:{WAIT_COLOR}; font-weight:bold;"
            )

        else:

            self.entry_quality.setStyleSheet(
                f"color:{AVOID_COLOR}; font-weight:bold;"
            )

        # ====================================================
        # ENTRY TYPE COLOR
        # ====================================================

        if self.entry_type.text().upper() == "NO ENTRY":

            self.entry_type.setStyleSheet(
                f"color:{AVOID_COLOR}; font-weight:bold;"
            )

        else:

            self.entry_type.setStyleSheet(
                f"color:{BUY_COLOR}; font-weight:bold;"
            )

        # ====================================================
        # REASON STYLE
        # ====================================================

        self.trade_reason.setWordWrap(True)

        self.trade_reason.setStyleSheet(
            f"""
            color:{TEXT_COLOR};
            font-size:11px;
            """
        )

        # ====================================================
        # FINISHED
        # ====================================================