import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QSizePolicy
)

from PySide6.QtCore import (
    Qt,
    QTimer
)

from PySide6.QtGui import (
    QFont
)

from ui.dashboard_widgets import DashboardWidget
from ui.watchlist_widget import WatchlistWidget
from ui.chart_widget import ChartWidget
from ui.controller import Controller
from ui.styles import APP_STYLE


# ============================================================
# Liquidity Hunter AI
# Main Window V20.8
# ============================================================
#
# V20.8 FEATURES
# ----------------
# • Gold-first market selection
# • Dynamic market switching
# • BTC / ETH / GOLD / SILVER
# • Controller.change_symbol() integration
# • Dynamic timeframe selection
# • Controller V20.7 chart synchronization preserved
# • No duplicate historical chart reload from UI
# • Live candle updates remain Controller controlled
# • Auto refresh
# ============================================================


class LiquidityHunterWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        # ====================================================
        # Window Settings
        # ====================================================

        self.setWindowTitle(
            "Liquidity Hunter AI V20.8"
        )

        self.resize(
            1700,
            950
        )

        self.setMinimumSize(
            1400,
            850
        )

        self.setWindowFlag(
            Qt.WindowStaysOnTopHint
        )

        self.setStyleSheet(
            APP_STYLE
        )

        # ====================================================
        # Controller
        # ====================================================

        self.controller = Controller()

        # ====================================================
        # Main Widgets
        # ====================================================

        self.dashboard = DashboardWidget()

        self.chart = ChartWidget()

        self.watchlist = WatchlistWidget()

        # ====================================================
        # UI State
        # ====================================================

        self.chart_loaded = False

        self.market_buttons = []

        self.active_market_button = None

        # ====================================================
        # Connect Controller -> UI
        # ====================================================

        self.controller.chart_widget = (
            self.chart
        )

        self.controller.dashboard = (
            self.dashboard
        )

        self.controller.watchlist = (
            self.watchlist
        )

        # ====================================================
        # Connect Live Chart
        # ====================================================

        try:

            self.controller.websocket.set_chart_widget(
                self.chart
            )

        except Exception as e:

            print(
                "Chart WebSocket connection error:",
                e
            )

        # ====================================================
        # Dashboard Scroll Area
        # ====================================================

        self.dashboard_scroll = QScrollArea()

        self.dashboard_scroll.setWidgetResizable(
            True
        )

        self.dashboard_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff
        )

        self.dashboard_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded
        )

        self.dashboard_scroll.setWidget(
            self.dashboard
        )

        # ====================================================
        # Main Container
        # ====================================================

        self.container = QWidget()

        self.main_layout = QVBoxLayout(
            self.container
        )

        self.main_layout.setContentsMargins(
            8,
            8,
            8,
            8
        )

        self.main_layout.setSpacing(
            8
        )

        # ====================================================
        # TOP TOOLBAR
        # ====================================================

        self.top_bar = QFrame()

        self.top_bar.setFixedHeight(
            60
        )

        self.top_layout = QHBoxLayout(
            self.top_bar
        )

        self.top_layout.setContentsMargins(
            15,
            10,
            15,
            10
        )

        self.top_layout.setSpacing(
            15
        )

        # ====================================================
        # Application Title
        # ====================================================

        self.title_label = QLabel(
            "Liquidity Hunter AI"
        )

        self.title_label.setFont(
            QFont(
                "Segoe UI",
                14,
                QFont.Bold
            )
        )

        self.top_layout.addWidget(
            self.title_label
        )

        # ====================================================
        # Active Market Display
        # ====================================================

        self.market_status_label = QLabel(
            "MARKET : GOLD"
        )

        self.market_status_label.setFont(
            QFont(
                "Segoe UI",
                11,
                QFont.Bold
            )
        )

        self.top_layout.addWidget(
            self.market_status_label
        )

        self.top_layout.addStretch()

        self.main_layout.addWidget(
            self.top_bar
        )

        # ====================================================
        # TRADING AREA
        # ====================================================

        self.trading_area = QWidget()

        self.trade_layout = QHBoxLayout(
            self.trading_area
        )

        self.trade_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.trade_layout.setSpacing(
            8
        )

        # ====================================================
        # LEFT PANEL
        # ====================================================

        self.left_panel = QFrame()

        self.left_panel.setMinimumWidth(
            330
        )

        self.left_panel.setMaximumWidth(
            380
        )

        self.left_layout = QVBoxLayout(
            self.left_panel
        )

        self.left_layout.setContentsMargins(
            5,
            5,
            5,
            5
        )

        self.left_layout.setSpacing(
            8
        )

        self.left_layout.addWidget(
            self.dashboard_scroll
        )

        # ====================================================
        # CENTER PANEL
        # ====================================================

        self.center_panel = QFrame()

        self.center_layout = QVBoxLayout(
            self.center_panel
        )

        self.center_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.center_layout.setSpacing(
            5
        )

        self.chart.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.center_layout.addWidget(
            self.chart
        )

        # ====================================================
        # RIGHT PANEL
        # ====================================================

        self.right_panel = QFrame()

        self.right_panel.setMinimumWidth(
            270
        )

        self.right_panel.setMaximumWidth(
            330
        )

        self.right_layout = QVBoxLayout(
            self.right_panel
        )

        self.right_layout.setContentsMargins(
            5,
            5,
            5,
            5
        )

        self.right_layout.setSpacing(
            10
        )

        # ====================================================
        # MARKET SELECTOR
        # ====================================================

        self.create_market_selector()

        # ====================================================
        # WATCHLIST
        # ====================================================

        self.right_layout.addWidget(
            self.watchlist
        )

        # ====================================================
        # TIMEFRAME SELECTOR
        # ====================================================

        self.create_timeframe_selector()

        # ====================================================
        # ADD PANELS
        # ====================================================

        self.trade_layout.addWidget(
            self.left_panel,
            2
        )

        self.trade_layout.addWidget(
            self.center_panel,
            6
        )

        self.trade_layout.addWidget(
            self.right_panel,
            2
        )

        self.main_layout.addWidget(
            self.trading_area
        )

        # ====================================================
        # STATUS BAR
        # ====================================================

        self.status_bar = QFrame()

        self.status_layout = QHBoxLayout(
            self.status_bar
        )

        self.status_layout.setContentsMargins(
            10,
            6,
            10,
            6
        )

        self.status_label = QLabel(
            "Socket : Starting   |   "
            "Market : GOLD   |   "
            "AI : Starting"
        )

        self.status_layout.addWidget(
            self.status_label
        )

        self.main_layout.addWidget(
            self.status_bar
        )

        # ====================================================
        # SET CENTRAL WIDGET
        # ====================================================

        self.setCentralWidget(
            self.container
        )

        # ====================================================
        # SIGNAL CONNECTIONS
        # ====================================================

        try:

            self.dashboard.refresh_button.clicked.connect(
                self.refresh_signal
            )

        except Exception as e:

            print(
                "Dashboard refresh connection error:",
                e
            )

        # ====================================================
        # INITIAL MARKET
        #
        # IMPORTANT:
        # Controller V20.7 currently defaults to BTC.
        #
        # We explicitly switch to GOLD here.
        # ====================================================

        self.initialize_gold_market()

        # ====================================================
        # AUTO REFRESH TIMER
        # ====================================================

        self.timer = QTimer(
            self
        )

        self.timer.timeout.connect(
            self.refresh_signal
        )

        self.timer.start(
            30000
        )

    # ========================================================
    # MARKET SELECTOR
    # ========================================================

    def create_market_selector(
        self
    ):

        self.market_frame = QFrame()

        self.market_layout = QVBoxLayout(
            self.market_frame
        )

        self.market_layout.setContentsMargins(
            5,
            5,
            5,
            5
        )

        self.market_layout.setSpacing(
            6
        )

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        self.market_title = QLabel(
            "Markets"
        )

        self.market_title.setAlignment(
            Qt.AlignCenter
        )

        self.market_title.setFont(
            QFont(
                "Segoe UI",
                11,
                QFont.Bold
            )
        )

        self.market_layout.addWidget(
            self.market_title
        )

        # ----------------------------------------------------
        # Market Grid
        # ----------------------------------------------------

        self.market_grid = QGridLayout()

        self.market_grid.setSpacing(
            6
        )

        # ====================================================
        # Supported Markets
        # ====================================================
        #
        # Gold:
        # B-XAU_USDT
        #
        # BTC:
        # B-BTC_USDT
        #
        # ETH:
        # B-ETH_USDT
        #
        # Silver:
        # B-XAG_USDT
        #
        # These are CoinDCX-style pair identifiers.
        # ====================================================

        markets = [

            (
                "🥇 GOLD",
                "B-XAU_USDT"
            ),

            (
                "₿ BTC",
                "B-BTC_USDT"
            ),

            (
                "Ξ ETH",
                "B-ETH_USDT"
            ),

            (
                "🥈 SILVER",
                "B-XAG_USDT"
            ),

        ]

        row = 0

        col = 0

        for name, symbol in markets:

            button = QPushButton(
                name
            )

            button.setMinimumHeight(
                38
            )

            button.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed
            )

            button.setProperty(
                "market_symbol",
                symbol
            )

            button.clicked.connect(
                lambda checked=False,
                symbol=symbol,
                name=name:
                self.change_market(
                    symbol,
                    name
                )
            )

            self.market_buttons.append(
                button
            )

            self.market_grid.addWidget(
                button,
                row,
                col
            )

            col += 1

            if col == 2:

                col = 0

                row += 1

        self.market_layout.addLayout(
            self.market_grid
        )

        self.right_layout.addWidget(
            self.market_frame
        )

    # ========================================================
    # INITIAL GOLD
    # ========================================================

    def initialize_gold_market(
        self
    ):

        print(
            "\n" + "=" * 60
        )

        print(
            "INITIAL MARKET : GOLD"
        )

        print(
            "Symbol         : B-XAU_USDT"
        )

        print(
            "=" * 60
        )

        try:

            success = (
                self.controller.change_symbol(
                    "B-XAU_USDT"
                )
            )

            if success:

                self.market_status_label.setText(
                    "MARKET : GOLD"
                )

                self.status_label.setText(
                    "Socket : Connected   |   "
                    "Market : GOLD   |   "
                    "AI : Running"
                )

                self.set_active_market_button(
                    "B-XAU_USDT"
                )

                print(
                    "Initial GOLD market loaded."
                )

            else:

                print(
                    "Initial GOLD market switch failed."
                )

                self.status_label.setText(
                    "Socket : Error   |   "
                    "Market : GOLD   |   "
                    "AI : Error"
                )

        except Exception:

            print(
                "Initial GOLD market exception."
            )

            import traceback

            traceback.print_exc()

    # ========================================================
    # CHANGE MARKET
    # ========================================================

    def change_market(
        self,
        symbol,
        market_name
    ):

        print(
            "\n" + "=" * 60
        )

        print(
            "MARKET BUTTON CLICKED"
        )

        print(
            "Market :",
            market_name
        )

        print(
            "Symbol :",
            symbol
        )

        print(
            "=" * 60
        )

        try:

            # ------------------------------------------------
            # Prevent duplicate switch
            # ------------------------------------------------

            if (
                self.controller.symbol
                == symbol
            ):

                print(
                    "Market already active:",
                    symbol
                )

                return

            # ------------------------------------------------
            # UI status
            # ------------------------------------------------

            self.market_status_label.setText(
                f"MARKET : {market_name}"
            )

            self.status_label.setText(
                f"Socket : Switching   |   "
                f"Market : {market_name}   |   "
                f"AI : Loading"
            )

            # ------------------------------------------------
            # Disable market buttons during switch
            # ------------------------------------------------

            self.set_market_buttons_enabled(
                False
            )

            QApplication.processEvents()

            # ------------------------------------------------
            # Controller handles complete lifecycle
            # ------------------------------------------------

            success = (
                self.controller.change_symbol(
                    symbol
                )
            )

            # ------------------------------------------------
            # Success
            # ------------------------------------------------

            if success:

                print(
                    "\nMARKET SWITCH SUCCESS"
                )

                print(
                    "Active Market :",
                    market_name
                )

                print(
                    "Active Symbol :",
                    self.controller.symbol
                )

                self.market_status_label.setText(
                    f"MARKET : {market_name}"
                )

                self.status_label.setText(
                    f"Socket : Connected   |   "
                    f"Market : {market_name}   |   "
                    f"AI : Running"
                )

                self.set_active_market_button(
                    symbol
                )

                # --------------------------------------------
                # Reset UI chart flag
                #
                # Controller itself controls chart reload.
                # This flag only prevents old UI code from
                # sending the chart dataset again.
                # --------------------------------------------

                self.chart_loaded = True

            # ------------------------------------------------
            # Failure
            # ------------------------------------------------

            else:

                print(
                    "\nMARKET SWITCH FAILED"
                )

                self.status_label.setText(
                    f"Socket : Error   |   "
                    f"Market : {market_name}   |   "
                    f"AI : Error"
                )

        except Exception:

            import traceback

            traceback.print_exc()

            self.status_label.setText(
                f"Socket : Error   |   "
                f"Market : {market_name}   |   "
                f"AI : Error"
            )

        finally:

            self.set_market_buttons_enabled(
                True
            )

            print(
                "=" * 60
            )

    # ========================================================
    # MARKET BUTTON STATE
    # ========================================================

    def set_market_buttons_enabled(
        self,
        enabled
    ):

        for button in (
            self.market_buttons
        ):

            button.setEnabled(
                enabled
            )

    # ========================================================

    def set_active_market_button(
        self,
        symbol
    ):

        self.active_market_button = None

        for button in (
            self.market_buttons
        ):

            button_symbol = (
                button.property(
                    "market_symbol"
                )
            )

            if button_symbol == symbol:

                self.active_market_button = (
                    button
                )

                break

    # ========================================================
    # TIMEFRAME SELECTOR
    # ========================================================

    def create_timeframe_selector(
        self
    ):

        self.timeframe_frame = QFrame()

        self.timeframe_layout = QGridLayout(
            self.timeframe_frame
        )

        self.timeframe_layout.setContentsMargins(
            5,
            5,
            5,
            5
        )

        self.timeframe_layout.setSpacing(
            6
        )

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        self.tf_title = QLabel(
            "Timeframes"
        )

        self.tf_title.setAlignment(
            Qt.AlignCenter
        )

        self.tf_title.setFont(
            QFont(
                "Segoe UI",
                11,
                QFont.Bold
            )
        )

        self.timeframe_layout.addWidget(
            self.tf_title,
            0,
            0,
            1,
            4
        )

        # ----------------------------------------------------
        # Timeframes
        # ----------------------------------------------------

        self.tf_buttons = []

        timeframes = [

            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1H",
            "4H",
            "1D"

        ]

        row = 1

        col = 0

        for tf in timeframes:

            btn = QPushButton(
                tf
            )

            btn.setMinimumHeight(
                34
            )

            btn.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed
            )

            btn.clicked.connect(
                lambda checked=False,
                tf=tf:
                self.change_timeframe(
                    tf
                )
            )

            self.tf_buttons.append(
                btn
            )

            self.timeframe_layout.addWidget(
                btn,
                row,
                col
            )

            col += 1

            if col == 4:

                col = 0

                row += 1

        self.right_layout.addWidget(
            self.timeframe_frame
        )

    # ========================================================
    # TIMEFRAME CHANGE
    # ========================================================

    def change_timeframe(
        self,
        timeframe
    ):

        print(
            "\n" + "=" * 60
        )

        print(
            "TIMEFRAME BUTTON CLICKED :",
            timeframe
        )

        print(
            "Current Market :",
            self.controller.symbol
        )

        print(
            "=" * 60
        )

        try:

            self.status_label.setText(
                f"Socket : Switching   |   "
                f"Market : {self.controller.symbol}   |   "
                f"Timeframe : {timeframe}"
            )

            QApplication.processEvents()

            self.controller.change_timeframe(
                timeframe
            )

            self.status_label.setText(
                f"Socket : Connected   |   "
                f"Market : {self.controller.symbol}   |   "
                f"AI : Running"
            )

        except Exception:

            import traceback

            traceback.print_exc()

            self.status_label.setText(
                f"Socket : Error   |   "
                f"Market : {self.controller.symbol}   |   "
                f"AI : Error"
            )

    # ========================================================
    # REFRESH SIGNAL
    # ========================================================

    def refresh_signal(
        self
    ):

        print(
            "\n=============================="
        )

        print(
            "===== REFRESH START ====="
        )

        print(
            "=============================="
        )

        try:

            # =================================================
            # Controller refresh
            #
            # IMPORTANT:
            # Controller V20.7 handles chart synchronization.
            #
            # Therefore this UI DOES NOT call:
            #
            # self.chart.set_chart_data(...)
            #
            # on every refresh.
            # =================================================

            data = (
                self.controller.refresh()
            )

            if not isinstance(
                data,
                dict
            ):

                print(
                    "Controller returned invalid data."
                )

                return

            print(
                "Returned Keys :",
                list(
                    data.keys()
                )
            )

            # =================================================
            # Current timeframe data
            # =================================================

            data_5m = data.get(
                f"data_{self.controller.timeframe}"
            )

            if data_5m is None:

                data_5m = data.get(
                    "data_5m"
                )

            print(
                "data_5m Type :",
                type(
                    data_5m
                )
            )

            print(
                "data_5m None :",
                data_5m is None
            )

            if data_5m is not None:

                try:

                    print(
                        "Rows :",
                        len(
                            data_5m
                        )
                    )

                    print(
                        data_5m.tail()
                    )

                except Exception as e:

                    print(
                        "DataFrame Error :",
                        e
                    )

            # =================================================
            # Dashboard Update
            # =================================================

            try:

                self.dashboard.update_dashboard(
                    data
                )

            except Exception:

                import traceback

                traceback.print_exc()

            # =================================================
            # Market Status
            # =================================================

            try:

                current_symbol = (
                    self.controller.symbol
                )

                market_names = {

                    "B-XAU_USDT":
                        "GOLD",

                    "B-BTC_USDT":
                        "BTC",

                    "B-ETH_USDT":
                        "ETH",

                    "B-XAG_USDT":
                        "SILVER",

                }

                market_name = (
                    market_names.get(
                        current_symbol,
                        current_symbol
                    )
                )

                self.market_status_label.setText(
                    f"MARKET : {market_name}"
                )

                self.status_label.setText(
                    f"Socket : Connected   |   "
                    f"Market : {market_name}   |   "
                    f"AI : Running"
                )

            except Exception:

                pass

            # =================================================
            # DO NOT RELOAD CHART HERE
            # =================================================
            #
            # Controller V20.7 already does:
            #
            # _sync_chart()
            #
            # and live candle updates use:
            #
            # update_last_candle()
            #
            # So historical chart data is not resent every
            # 30-second refresh.
            # =================================================

            print(
                "UI Chart reload skipped."
            )

            print(
                "Reason : Controller V20.7 owns chart sync."
            )

        except Exception:

            import traceback

            traceback.print_exc()

            self.status_label.setText(
                "Socket : Error   |   "
                "Market : Error   |   "
                "AI : Error"
            )

    # ========================================================
    # CLOSE EVENT
    # ========================================================

    def closeEvent(
        self,
        event
    ):

        print(
            "\nClosing Liquidity Hunter AI..."
        )

        try:

            if hasattr(
                self,
                "timer"
            ):

                self.timer.stop()

        except Exception:

            pass

        try:

            if self.controller:

                self.controller.shutdown()

        except Exception:

            import traceback

            traceback.print_exc()

        event.accept()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    window = (
        LiquidityHunterWindow()
    )

    window.show()

    sys.exit(
        app.exec()
    )