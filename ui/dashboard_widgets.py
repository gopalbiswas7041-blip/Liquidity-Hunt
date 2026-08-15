"""
============================================================
Liquidity Hunter AI
Dashboard Widget V20.9.2
Futures Live Price Synchronization Edition
============================================================

Purpose
-------
Professional trading dashboard for Liquidity Hunter AI.

V20.9.2 Responsibilities
------------------------
• Futures symbol display
• Futures timeframe display
• Futures live price display
• Futures WebSocket price authority display
• Signal display
• Confidence display
• Trade status display
• Market context
• AI analysis
• Dynamic dashboard updates

IMPORTANT
---------
Dashboard does NOT generate market data.

Authoritative live price:

    CoinDCX Futures WebSocket
              ↓
          Controller
              ↓
        DashboardWidget

REST is bootstrap/fallback only.

Spot WebSocket must never control the
Futures live price displayed here.
============================================================
"""

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QFrame,
)

from ui.styles import (
    BUY_COLOR,
    SELL_COLOR,
    WAIT_COLOR,
    READY_COLOR,
    AVOID_COLOR,
    TEXT_COLOR,
)


class DashboardWidget(QWidget):
    """
    Liquidity Hunter AI
    Professional Futures Dashboard V20.9.2
    """

    # ======================================================
    # INITIALIZATION
    # ======================================================

    def __init__(self):
        super().__init__()

        self.setObjectName(
            "dashboardWidget"
        )

        # ==================================================
        # MAIN LAYOUT
        # ==================================================

        main_layout = QVBoxLayout(self)

        main_layout.setSpacing(12)

        # ==================================================
        # PROFESSIONAL HEADER CARD
        # ==================================================

        header = QFrame()

        header.setObjectName(
            "headerCard"
        )

        header_layout = QHBoxLayout(
            header
        )

        # --------------------------------------------------
        # Header Left
        # --------------------------------------------------

        left_layout = QVBoxLayout()

        self.title = QLabel(
            "LIQUIDITY HUNTER AI"
        )

        self.title.setObjectName(
            "headerTitle"
        )

        self.subtitle = QLabel(
            "Professional Futures Trading Dashboard"
        )

        self.subtitle.setObjectName(
            "headerSubtitle"
        )

        left_layout.addWidget(
            self.title
        )

        left_layout.addWidget(
            self.subtitle
        )

        # --------------------------------------------------
        # Header Right
        # --------------------------------------------------

        right_layout = QVBoxLayout()

        self.live_status = QLabel(
            "🟢 LIVE"
        )

        self.symbol = QLabel(
            "B-BTC_USDT"
        )

        self.timeframe = QLabel(
            "5m"
        )

        self.live_price = QLabel(
            "--"
        )

        self.price_source = QLabel(
            "Futures WebSocket"
        )

        right_layout.addWidget(
            self.live_status
        )

        right_layout.addWidget(
            self.symbol
        )

        right_layout.addWidget(
            self.timeframe
        )

        right_layout.addWidget(
            self.live_price
        )

        right_layout.addWidget(
            self.price_source
        )

        header_layout.addLayout(
            left_layout
        )

        header_layout.addStretch()

        header_layout.addLayout(
            right_layout
        )

        main_layout.addWidget(
            header
        )

        # ==================================================
        # MARKET CONTEXT
        # ==================================================

        market_group = QGroupBox(
            "Market Context"
        )

        market_form = QFormLayout()

        self.trend = QLabel(
            "--"
        )

        self.market_phase = QLabel(
            "--"
        )

        self.liquidity = QLabel(
            "--"
        )

        self.choch = QLabel(
            "--"
        )

        self.order_block = QLabel(
            "--"
        )

        self.fvg = QLabel(
            "--"
        )

        market_form.addRow(
            "Trend",
            self.trend
        )

        market_form.addRow(
            "Market Phase",
            self.market_phase
        )

        market_form.addRow(
            "Liquidity Sweep",
            self.liquidity
        )

        market_form.addRow(
            "CHoCH",
            self.choch
        )

        market_form.addRow(
            "Order Block",
            self.order_block
        )

        market_form.addRow(
            "Fair Value Gap",
            self.fvg
        )

        market_group.setLayout(
            market_form
        )

        # ==================================================
        # TRADE SETUP
        # ==================================================

        trade_group = QGroupBox(
            "Trade Setup"
        )

        trade_form = QFormLayout()

        self.signal = QLabel(
            "NO TRADE"
        )

        self.confidence = QLabel(
            "0%"
        )

        self.quality = QLabel(
            "-"
        )

        self.status = QLabel(
            "WAIT"
        )

        self.entry = QLabel(
            "--"
        )

        self.stop_loss = QLabel(
            "--"
        )

        self.take_profit = QLabel(
            "--"
        )

        self.risk = QLabel(
            "--"
        )

        self.reward = QLabel(
            "--"
        )

        self.rr = QLabel(
            "--"
        )

        self.volatility = QLabel(
            "NORMAL"
        )

        trade_form.addRow(
            "Signal",
            self.signal
        )

        trade_form.addRow(
            "Confidence",
            self.confidence
        )

        trade_form.addRow(
            "Quality",
            self.quality
        )

        trade_form.addRow(
            "Status",
            self.status
        )

        trade_form.addRow(
            "Entry",
            self.entry
        )

        trade_form.addRow(
            "Stop Loss",
            self.stop_loss
        )

        trade_form.addRow(
            "Take Profit",
            self.take_profit
        )

        trade_form.addRow(
            "Risk",
            self.risk
        )

        trade_form.addRow(
            "Reward",
            self.reward
        )

        trade_form.addRow(
            "Risk : Reward",
            self.rr
        )

        trade_form.addRow(
            "Volatility",
            self.volatility
        )

        trade_group.setLayout(
            trade_form
        )

        # ==================================================
        # AI ANALYSIS
        # ==================================================

        ai_group = QGroupBox(
            "AI Analysis"
        )

        ai_form = QFormLayout()

        self.trade_score = QLabel(
            "0"
        )

        self.entry_type = QLabel(
            "--"
        )

        self.entry_zone = QLabel(
            "--"
        )

        self.confirmation = QLabel(
            "--"
        )

        self.entry_quality = QLabel(
            "--"
        )

        self.trade_reason = QLabel(
            "--"
        )

        self.trade_reason.setWordWrap(
            True
        )

        ai_form.addRow(
            "AI Score",
            self.trade_score
        )

        ai_form.addRow(
            "Entry Type",
            self.entry_type
        )

        ai_form.addRow(
            "Entry Zone",
            self.entry_zone
        )

        ai_form.addRow(
            "Confirmation",
            self.confirmation
        )

        ai_form.addRow(
            "Entry Quality",
            self.entry_quality
        )

        ai_form.addRow(
            "Reason",
            self.trade_reason
        )

        ai_group.setLayout(
            ai_form
        )

        # ==================================================
        # REFRESH BUTTON
        # ==================================================

        self.refresh_button = QPushButton(
            "Refresh Signal"
        )

        self.refresh_button.setMinimumHeight(
            42
        )

        # ==================================================
        # ADD TO MAIN LAYOUT
        # ==================================================

        main_layout.addWidget(
            market_group
        )

        main_layout.addWidget(
            trade_group
        )

        main_layout.addWidget(
            ai_group
        )

        line = QFrame()

        line.setFrameShape(
            QFrame.HLine
        )

        line.setFrameShadow(
            QFrame.Sunken
        )

        main_layout.addWidget(
            line
        )

        main_layout.addWidget(
            self.refresh_button
        )

        # ==================================================
        # INITIAL HEADER STYLE
        # ==================================================

        self._set_live_header_style()

    # ======================================================
    # FUTURES LIVE PRICE
    # ======================================================

    def update_futures_live_price(
        self,
        price,
        source="Futures WebSocket",
    ):
        """
        Update only the Futures live price.

        Intended flow:

            Futures WebSocket
                    ↓
                Controller
                    ↓
            update_futures_live_price()
                    ↓
                Dashboard
        """

        try:

            if price is None:
                return False

            value = float(
                price
            )

            if value <= 0:
                return False

            # --------------------------------------------------
            # Display formatting
            # --------------------------------------------------

            self.live_price.setText(
                self._format_price(
                    value
                )
            )

            # --------------------------------------------------
            # Source
            # --------------------------------------------------

            self.price_source.setText(
                str(
                    source
                )
            )

            # --------------------------------------------------
            # LIVE status
            # --------------------------------------------------

            self.live_status.setText(
                "🟢 LIVE"
            )

            self._set_live_header_style()

            return True

        except Exception:

            return False

    # ======================================================
    # SYMBOL UPDATE
    # ======================================================

    def update_symbol(
        self,
        symbol,
    ):
        """
        Update active Futures symbol.
        """

        if symbol is None:
            return False

        value = str(
            symbol
        ).strip()

        if not value:
            return False

        self.symbol.setText(
            value
        )

        return True

    # ======================================================
    # TIMEFRAME UPDATE
    # ======================================================

    def update_timeframe(
        self,
        timeframe,
    ):
        """
        Update active Futures timeframe.
        """

        if timeframe is None:
            return False

        value = str(
            timeframe
        ).strip()

        if not value:
            return False

        self.timeframe.setText(
            value
        )

        return True

    # ======================================================
    # MARKET TYPE / SOURCE
    # ======================================================

    def update_price_source(
        self,
        source,
    ):
        """
        Update live price source label.
        """

        if source is None:
            return

        self.price_source.setText(
            str(source)
        )

    # ======================================================
    # LIVE STATUS
    # ======================================================

    def set_live_status(
        self,
        connected=True,
    ):
        """
        Update Futures WebSocket status.
        """

        if connected:

            self.live_status.setText(
                "🟢 LIVE"
            )

            self._set_live_header_style()

        else:

            self.live_status.setText(
                "🔴 OFFLINE"
            )

            self.live_status.setStyleSheet(
                f"""
                color:{SELL_COLOR};
                font-weight:bold;
                """
            )

    # ======================================================
    # FORMAT PRICE
    # ======================================================

    @staticmethod
    def _format_price(
        price
    ):
        """
        Professional price formatting.

        Avoids unnecessary trailing zeros.
        """

        try:

            value = float(
                price
            )

            if value >= 1000:

                return f"{value:,.2f}"

            if value >= 1:

                return f"{value:,.4f}"

            return f"{value:.8f}"

        except Exception:

            return str(
                price
            )

    # ======================================================
    # HEADER STYLE
    # ======================================================

    def _set_live_header_style(
        self
    ):

        self.live_status.setStyleSheet(
            f"""
            color:{BUY_COLOR};
            font-weight:bold;
            """
        )

        self.live_price.setStyleSheet(
            f"""
            color:{BUY_COLOR};
            font-size:20px;
            font-weight:bold;
            """
        )

        self.price_source.setStyleSheet(
            f"""
            color:{TEXT_COLOR};
            font-size:10px;
            """
        )

    # ======================================================
    # UPDATE DASHBOARD
    # ======================================================

    def update_dashboard(
        self,
        data: dict,
    ):
        """
        Update complete dashboard from Controller result.

        Expected data may contain:

            symbol
            timeframe
            live_price
            live_price_source

            trend
            market_phase
            liquidity_sweep
            choch
            order_block
            fvg

            signal
            confidence
            quality
            status
            trade_status

            entry
            stop_loss
            take_profit

            risk
            reward
            risk_reward
            volatility

            trade_score
            entry_type
            entry_zone
            confirmation
            entry_quality
            trade_reason
        """

        if not isinstance(
            data,
            dict
        ):

            return

        # ==================================================
        # FUTURES HEADER
        # ==================================================

        symbol = data.get(
            "symbol"
        )

        timeframe = data.get(
            "timeframe"
        )

        live_price = data.get(
            "live_price"
        )

        live_price_source = data.get(
            "live_price_source",
            "Futures WebSocket",
        )

        if symbol is not None:

            self.update_symbol(
                symbol
            )

        if timeframe is not None:

            self.update_timeframe(
                timeframe
            )

        if live_price is not None:

            self.update_futures_live_price(

                live_price,

                source=(
                    live_price_source
                ),

            )

        # ==================================================
        # MARKET CONTEXT
        # ==================================================

        self.trend.setText(
            str(
                data.get(
                    "trend",
                    "--"
                )
            )
        )

        self.market_phase.setText(
            str(
                data.get(
                    "market_phase",
                    "--"
                )
            )
        )

        self.liquidity.setText(
            "YES"
            if data.get(
                "liquidity_sweep",
                False
            )
            else "NO"
        )

        self.choch.setText(
            "YES"
            if data.get(
                "choch",
                False
            )
            else "NO"
        )

        self.order_block.setText(
            "YES"
            if data.get(
                "order_block",
                False
            )
            else "NO"
        )

        self.fvg.setText(
            "YES"
            if data.get(
                "fvg",
                False
            )
            else "NO"
        )

        # ==================================================
        # TRADE SETUP
        # ==================================================

        self.signal.setText(
            str(
                data.get(
                    "signal",
                    "NO TRADE"
                )
            )
        )

        self.confidence.setText(
            str(
                data.get(
                    "confidence",
                    "0"
                )
            )
        )

        self.quality.setText(
            str(
                data.get(
                    "quality",
                    "-"
                )
            )
        )

        self.status.setText(
            str(
                data.get(
                    "status",
                    data.get(
                        "trade_status",
                        "WAIT"
                    )
                )
            )
        )

        self.entry.setText(
            str(
                data.get(
                    "entry",
                    "--"
                )
            )
        )

        self.stop_loss.setText(
            str(
                data.get(
                    "stop_loss",
                    "--"
                )
            )
        )

        self.take_profit.setText(
            str(
                data.get(
                    "take_profit",
                    "--"
                )
            )
        )

        self.risk.setText(
            str(
                data.get(
                    "risk",
                    "--"
                )
            )
        )

        self.reward.setText(
            str(
                data.get(
                    "reward",
                    "--"
                )
            )
        )

        self.rr.setText(
            str(
                data.get(
                    "risk_reward",
                    "--"
                )
            )
        )

        self.volatility.setText(
            str(
                data.get(
                    "volatility",
                    "NORMAL"
                )
            )
        )

        # ==================================================
        # AI ANALYSIS
        # ==================================================

        self.trade_score.setText(
            str(
                data.get(
                    "trade_score",
                    "0"
                )
            )
        )

        self.entry_type.setText(
            str(
                data.get(
                    "entry_type",
                    "--"
                )
            )
        )

        self.entry_zone.setText(
            str(
                data.get(
                    "entry_zone",
                    "--"
                )
            )
        )

        self.confirmation.setText(
            str(
                data.get(
                    "confirmation",
                    "--"
                )
            )
        )

        self.entry_quality.setText(
            str(
                data.get(
                    "entry_quality",
                    "--"
                )
            )
        )

        reasons = data.get(
            "trade_reason",
            []
        )

        if isinstance(
            reasons,
            list
        ):

            self.trade_reason.setText(

                ", ".join(
                    map(
                        str,
                        reasons
                    )
                )

                if reasons

                else "-"

            )

        else:

            self.trade_reason.setText(
                str(
                    reasons
                )
            )

        # ==================================================
        # COLORS
        # ==================================================

        self._update_signal_color()

        self._update_status_color()

        self._update_trend_color()

        self._update_market_context_colors()

        self._update_confidence_color(
            data
        )

        self._update_score_color(
            data
        )

        self._update_entry_quality_color(
            data
        )

        self._update_entry_type_color()

        self._update_reason_style()

    # ======================================================
    # SIGNAL COLOR
    # ======================================================

    def _update_signal_color(
        self
    ):

        signal = str(
            self.signal.text()
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

    # ======================================================
    # STATUS COLOR
    # ======================================================

    def _update_status_color(
        self
    ):

        status = str(
            self.status.text()
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

    # ======================================================
    # TREND COLOR
    # ======================================================

    def _update_trend_color(
        self
    ):

        trend = str(
            self.trend.text()
        ).upper()

        if trend == "BUY":

            self.trend.setStyleSheet(
                f"""
                color:{BUY_COLOR};
                font-weight:bold;
                """
            )

        elif trend == "SELL":

            self.trend.setStyleSheet(
                f"""
                color:{SELL_COLOR};
                font-weight:bold;
                """
            )

        else:

            self.trend.setStyleSheet(
                f"""
                color:{TEXT_COLOR};
                """
            )

    # ======================================================
    # MARKET CONTEXT COLORS
    # ======================================================

    def _update_market_context_colors(
        self
    ):

        yes_style = f"""
        color:{BUY_COLOR};
        font-weight:bold;
        """

        no_style = f"""
        color:{SELL_COLOR};
        font-weight:bold;
        """

        self.liquidity.setStyleSheet(
            yes_style
            if self.liquidity.text() == "YES"
            else no_style
        )

        self.choch.setStyleSheet(
            yes_style
            if self.choch.text() == "YES"
            else no_style
        )

        self.order_block.setStyleSheet(
            yes_style
            if self.order_block.text() == "YES"
            else no_style
        )

        self.fvg.setStyleSheet(
            yes_style
            if self.fvg.text() == "YES"
            else no_style
        )

    # ======================================================
    # CONFIDENCE COLOR
    # ======================================================

    def _update_confidence_color(
        self,
        data
    ):

        try:

            confidence = float(
                str(
                    data.get(
                        "confidence",
                        "0"
                    )
                ).replace(
                    "%",
                    ""
                )
            )

            if confidence >= 80:

                self.confidence.setStyleSheet(
                    f"""
                    color:{BUY_COLOR};
                    font-weight:bold;
                    """
                )

            elif confidence >= 60:

                self.confidence.setStyleSheet(
                    f"""
                    color:{WAIT_COLOR};
                    font-weight:bold;
                    """
                )

            else:

                self.confidence.setStyleSheet(
                    f"""
                    color:{SELL_COLOR};
                    font-weight:bold;
                    """
                )

        except Exception:

            self.confidence.setStyleSheet(
                f"""
                color:{TEXT_COLOR};
                """
            )

    # ======================================================
    # AI SCORE COLOR
    # ======================================================

    def _update_score_color(
        self,
        data
    ):

        try:

            score = int(
                float(
                    data.get(
                        "trade_score",
                        0
                    )
                )
            )

            if score >= 80:

                self.trade_score.setStyleSheet(
                    f"""
                    color:{BUY_COLOR};
                    font-weight:bold;
                    """
                )

            elif score >= 60:

                self.trade_score.setStyleSheet(
                    f"""
                    color:{WAIT_COLOR};
                    font-weight:bold;
                    """
                )

            else:

                self.trade_score.setStyleSheet(
                    f"""
                    color:{SELL_COLOR};
                    font-weight:bold;
                    """
                )

        except Exception:

            self.trade_score.setStyleSheet(
                f"""
                color:{TEXT_COLOR};
                """
            )

    # ======================================================
    # ENTRY QUALITY COLOR
    # ======================================================

    def _update_entry_quality_color(
        self,
        data
    ):

        quality = str(
            data.get(
                "entry_quality",
                "--"
            )
        ).upper()

        if quality == "A":

            self.entry_quality.setStyleSheet(
                f"""
                color:{BUY_COLOR};
                font-weight:bold;
                """
            )

        elif quality == "B":

            self.entry_quality.setStyleSheet(
                f"""
                color:{READY_COLOR};
                font-weight:bold;
                """
            )

        elif quality == "C":

            self.entry_quality.setStyleSheet(
                f"""
                color:{WAIT_COLOR};
                font-weight:bold;
                """
            )

        else:

            self.entry_quality.setStyleSheet(
                f"""
                color:{AVOID_COLOR};
                font-weight:bold;
                """
            )

    # ======================================================
    # ENTRY TYPE COLOR
    # ======================================================

    def _update_entry_type_color(
        self
    ):

        if (
            self.entry_type.text()
            .upper()
            ==
            "NO ENTRY"
        ):

            self.entry_type.setStyleSheet(
                f"""
                color:{AVOID_COLOR};
                font-weight:bold;
                """
            )

        else:

            self.entry_type.setStyleSheet(
                f"""
                color:{BUY_COLOR};
                font-weight:bold;
                """
            )

    # ======================================================
    # REASON STYLE
    # ======================================================

    def _update_reason_style(
        self
    ):

        self.trade_reason.setWordWrap(
            True
        )

        self.trade_reason.setStyleSheet(
            f"""
            color:{TEXT_COLOR};
            font-size:11px;
            """
        )

    # ======================================================
    # RESET DASHBOARD
    # ======================================================

    def reset_dashboard(
        self,
        symbol=None,
        timeframe=None,
    ):
        """
        Reset dashboard when symbol/timeframe changes.
        """

        if symbol is not None:

            self.update_symbol(
                symbol
            )

        if timeframe is not None:

            self.update_timeframe(
                timeframe
            )

        self.live_price.setText(
            "--"
        )

        self.price_source.setText(
            "Waiting for Futures WebSocket"
        )

        self.live_status.setText(
            "🟡 WAITING"
        )

        self.live_status.setStyleSheet(
            f"""
            color:{WAIT_COLOR};
            font-weight:bold;
            """
        )

        self.signal.setText(
            "NO TRADE"
        )

        self.confidence.setText(
            "0%"
        )

        self.quality.setText(
            "-"
        )

        self.status.setText(
            "WAIT"
        )

        self.entry.setText(
            "--"
        )

        self.stop_loss.setText(
            "--"
        )

        self.take_profit.setText(
            "--"
        )

        self.risk.setText(
            "--"
        )

        self.reward.setText(
            "--"
        )

        self.rr.setText(
            "--"
        )

        self.volatility.setText(
            "NORMAL"
        )

        self.trade_score.setText(
            "0"
        )

        self.entry_type.setText(
            "--"
        )

        self.entry_zone.setText(
            "--"
        )

        self.confirmation.setText(
            "--"
        )

        self.entry_quality.setText(
            "--"
        )

        self.trade_reason.setText(
            "--"
        )

        self._update_signal_color()

        self._update_status_color()

        self._update_trend_color()

        self._update_market_context_colors()

        self._update_confidence_color(
            {}
        )

        self._update_score_color(
            {}
        )

        self._update_entry_quality_color(
            {}
        )

        self._update_entry_type_color()

        self._update_reason_style()

    # ======================================================
    # FINISHED
    # ======================================================