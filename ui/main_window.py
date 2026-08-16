"""
============================================================
Liquidity Hunter AI
Main Window V20.9.9
Live Candle Preservation Edition
============================================================

Responsibilities
----------------
• Main application window
• Dashboard
• Chart
• Watchlist
• Market selector
• Timeframe selector
• 30-second background analysis
• Manual Refresh Signal
• Futures WebSocket live UI
• Non-blocking GUI architecture
• Live candle preservation during analysis

IMPORTANT
---------
30-second analysis is NOT removed.

It is moved away from the Qt GUI thread.

Futures WebSocket remains responsible for:
    • live price
    • forming candle
    • candle wick/body movement
    • live chart updates

30-second background analysis remains responsible for:
    • signal detection
    • trade manager
    • confidence
    • status
    • entry
    • SL
    • TP
    • RR

V20.9.9 FIX
-----------
Previous V20.9.8 temporarily did:

    controller.chart_widget = None

while background analysis was running.

That could suppress live chart updates because the Futures
WebSocket Controller bridge uses controller.chart_widget for
live candle delivery.

V20.9.9 DOES NOT DETACH chart_widget.

Instead, background analysis temporarily disables only the
historical _sync_chart() operation.

Therefore:

    LIVE WS CANDLE
        ↓
    ChartWidget
        ↓
    continues immediately

while:

    30-second analysis
        ↓
    Controller.refresh()
        ↓
    Dashboard
        ↓
    remains background work.
============================================================
"""

import sys
import traceback

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
    QSizePolicy,
)

from PySide6.QtCore import (
    Qt,
    QTimer,
    QThread,
    Signal,
    QObject,
)

from PySide6.QtGui import (
    QFont,
)

from ui.dashboard_widgets import DashboardWidget
from ui.watchlist_widget import WatchlistWidget
from ui.chart_widget import ChartWidget
from ui.controller import Controller
from ui.styles import APP_STYLE


# ============================================================
# BACKGROUND REFRESH WORKER
# ============================================================


class RefreshWorker(QObject):
    """
    Runs Controller.refresh() outside the Qt GUI thread.

    IMPORTANT
    ---------
    The worker does NOT detach controller.chart_widget.

    The Futures WebSocket must remain connected to the live
    ChartWidget while analysis is running.

    Controller._sync_chart() is temporarily disabled so the
    background analysis cannot perform a historical chart
    reload from the worker thread.

    Live Futures WebSocket candle updates are therefore
    preserved.
    """

    finished = Signal(object)

    failed = Signal(str)

    def __init__(
        self,
        controller,
    ):

        super().__init__()

        self.controller = controller

    # ========================================================
    # RUN
    # ========================================================

    def run(self):

        original_sync_chart = None

        try:

            # ------------------------------------------------
            # IMPORTANT V20.9.9
            #
            # DO NOT DO:
            #
            # controller.chart_widget = None
            #
            # because Futures WebSocket live candle callbacks
            # use controller.chart_widget.
            #
            # Instead disable ONLY _sync_chart().
            # ------------------------------------------------

            if hasattr(
                self.controller,
                "_sync_chart",
            ):

                original_sync_chart = (
                    self.controller._sync_chart
                )

                self.controller._sync_chart = (
                    lambda: None
                )

            # ------------------------------------------------
            # Run analysis
            # ------------------------------------------------

            result = (
                self.controller.refresh()
            )

            # ------------------------------------------------
            # Return result to GUI thread.
            # ------------------------------------------------

            self.finished.emit(
                result
            )

        except Exception:

            error_text = (
                traceback.format_exc()
            )

            self.failed.emit(
                error_text
            )

        finally:

            # ------------------------------------------------
            # Restore _sync_chart()
            # ------------------------------------------------

            try:

                if (
                    original_sync_chart is not None
                ):

                    self.controller._sync_chart = (
                        original_sync_chart
                    )

            except Exception:

                traceback.print_exc()


# ============================================================
# LIQUIDITY HUNTER AI
# MAIN WINDOW
# ============================================================


class LiquidityHunterWindow(QMainWindow):

    # ========================================================
    # INIT
    # ========================================================

    def __init__(
        self,
    ):

        super().__init__()

        # ====================================================
        # WINDOW SETTINGS
        # ====================================================

        self.setWindowTitle(
            "Liquidity Hunter AI V20.9.9"
        )

        self.resize(
            1700,
            950,
        )

        self.setMinimumSize(
            1400,
            850,
        )

        self.setWindowFlag(
            Qt.WindowStaysOnTopHint,
        )

        self.setStyleSheet(
            APP_STYLE,
        )

        # ====================================================
        # CONTROLLER
        # ====================================================

        self.controller = Controller()

        # ====================================================
        # MAIN WIDGETS
        # ====================================================

        self.dashboard = (
            DashboardWidget()
        )

        self.chart = (
            ChartWidget()
        )

        self.watchlist = (
            WatchlistWidget()
        )

        # ====================================================
        # UI STATE
        # ====================================================

        self.chart_loaded = False

        self.market_buttons = []

        self.active_market_button = None

        # ====================================================
        # BACKGROUND REFRESH STATE
        # ====================================================

        self.refresh_thread = None

        self.refresh_worker = None

        self.refresh_running = False

        # ====================================================
        # LIVE UI STATE
        # ====================================================

        self.last_live_price = None

        self.last_live_candle = None

        self.live_tick_count = 0

        # ====================================================
        # CONTROLLER -> UI
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
        # LEGACY CHART WEBSOCKET BRIDGE
        #
        # Keep compatibility bridge alive.
        #
        # Futures WebSocket remains authoritative through
        # Controller.
        # ====================================================

        try:

            if self.controller.websocket:

                self.controller.websocket.set_chart_widget(
                    self.chart
                )

        except Exception as e:

            print(
                "Chart WebSocket connection error:",
                e,
            )

        # ====================================================
        # DASHBOARD SCROLL AREA
        # ====================================================

        self.dashboard_scroll = (
            QScrollArea()
        )

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
        # MAIN CONTAINER
        # ====================================================

        self.container = QWidget()

        self.main_layout = QVBoxLayout(
            self.container
        )

        self.main_layout.setContentsMargins(
            8,
            8,
            8,
            8,
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
            10,
        )

        self.top_layout.setSpacing(
            15
        )

        # ====================================================
        # APPLICATION TITLE
        # ====================================================

        self.title_label = QLabel(
            "Liquidity Hunter AI"
        )

        self.title_label.setFont(
            QFont(
                "Segoe UI",
                14,
                QFont.Bold,
            )
        )

        self.top_layout.addWidget(
            self.title_label
        )

        # ====================================================
        # MARKET STATUS
        # ====================================================

        self.market_status_label = QLabel(
            "MARKET : GOLD"
        )

        self.market_status_label.setFont(
            QFont(
                "Segoe UI",
                11,
                QFont.Bold,
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
            0,
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
            5,
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
            0,
        )

        self.center_layout.setSpacing(
            5
        )

        self.chart.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
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
            5,
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
            2,
        )

        self.trade_layout.addWidget(
            self.center_panel,
            6,
        )

        self.trade_layout.addWidget(
            self.right_panel,
            2,
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
            6,
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
        # CENTRAL WIDGET
        # ====================================================

        self.setCentralWidget(
            self.container
        )

        # ====================================================
        # DASHBOARD MANUAL REFRESH
        # ====================================================

        try:

            self.dashboard.refresh_button.clicked.connect(
                self.refresh_signal
            )

        except Exception:

            print(
                "Dashboard refresh connection error:"
            )

            traceback.print_exc()

        # ====================================================
        # INITIAL GOLD
        # ====================================================

        self.initialize_gold_market()

        # ====================================================
        # 30 SECOND ANALYSIS TIMER
        #
        # IMPORTANT:
        #
        # This timer is ONLY for AI analysis.
        #
        # It is NOT responsible for live candle movement.
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

        print(
            "30-second background analysis timer started."
        )

        print(
            "Live Futures WebSocket remains "
            "independent from analysis timer."
        )

    # ========================================================
    # MARKET SELECTOR
    # ========================================================

    def create_market_selector(
        self,
    ):

        self.market_frame = QFrame()

        self.market_layout = QVBoxLayout(
            self.market_frame
        )

        self.market_layout.setContentsMargins(
            5,
            5,
            5,
            5,
        )

        self.market_layout.setSpacing(
            6
        )

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
                QFont.Bold,
            )
        )

        self.market_layout.addWidget(
            self.market_title
        )

        self.market_grid = QGridLayout()

        self.market_grid.setSpacing(
            6
        )

        markets = [

            (
                "🥇 GOLD",
                "B-XAU_USDT",
            ),

            (
                "₿ BTC",
                "B-BTC_USDT",
            ),

            (
                "Ξ ETH",
                "B-ETH_USDT",
            ),

            (
                "🥈 SILVER",
                "B-XAG_USDT",
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
                QSizePolicy.Fixed,
            )

            button.setProperty(
                "market_symbol",
                symbol,
            )

            button.clicked.connect(
                lambda checked=False,
                symbol=symbol,
                name=name:
                self.change_market(
                    symbol,
                    name,
                )
            )

            self.market_buttons.append(
                button
            )

            self.market_grid.addWidget(
                button,
                row,
                col,
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
        self,
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

            traceback.print_exc()

    # ========================================================
    # CHANGE MARKET
    # ========================================================

    def change_market(
        self,
        symbol,
        market_name,
    ):

        print(
            "\n" + "=" * 60
        )

        print(
            "MARKET BUTTON CLICKED"
        )

        print(
            "Market :",
            market_name,
        )

        print(
            "Symbol :",
            symbol,
        )

        print(
            "=" * 60
        )

        try:

            if (
                self.controller.symbol
                == symbol
            ):

                print(
                    "Market already active:",
                    symbol,
                )

                return

            self.market_status_label.setText(
                f"MARKET : {market_name}"
            )

            self.status_label.setText(
                f"Socket : Switching   |   "
                f"Market : {market_name}   |   "
                f"AI : Loading"
            )

            self.set_market_buttons_enabled(
                False
            )

            QApplication.processEvents()

            success = (
                self.controller.change_symbol(
                    symbol
                )
            )

            if success:

                print(
                    "\nMARKET SWITCH SUCCESS"
                )

                print(
                    "Active Market :",
                    market_name,
                )

                print(
                    "Active Symbol :",
                    self.controller.symbol,
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

                self.chart_loaded = True

                # ------------------------------------------------
                # Any previous analysis result belongs to the old
                # market. The next background refresh will rebuild
                # it for the new symbol.
                # ------------------------------------------------

                print(
                    "Market changed."
                )

                print(
                    "Live Futures WebSocket will now "
                    "follow the active symbol."
                )

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
        enabled,
    ):

        for button in self.market_buttons:

            button.setEnabled(
                enabled
            )

    # ========================================================

    def set_active_market_button(
        self,
        symbol,
    ):

        self.active_market_button = None

        for button in self.market_buttons:

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
        self,
    ):

        self.timeframe_frame = QFrame()

        self.timeframe_layout = QGridLayout(
            self.timeframe_frame
        )

        self.timeframe_layout.setContentsMargins(
            5,
            5,
            5,
            5,
        )

        self.timeframe_layout.setSpacing(
            6
        )

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
                QFont.Bold,
            )
        )

        self.timeframe_layout.addWidget(
            self.tf_title,
            0,
            0,
            1,
            4,
        )

        self.tf_buttons = []

        timeframes = [

            "1m",
            "3m",
            "5m",
            "15m",
            "30m",
            "1H",
            "4H",
            "1D",

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
                QSizePolicy.Fixed,
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
                col,
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
        timeframe,
    ):

        print(
            "\n" + "=" * 60
        )

        print(
            "TIMEFRAME BUTTON CLICKED :",
            timeframe,
        )

        print(
            "Current Market :",
            self.controller.symbol,
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

            # ------------------------------------------------
            # Controller owns Futures WebSocket timeframe
            # lifecycle.
            # ------------------------------------------------

            self.controller.change_timeframe(
                timeframe
            )

            self.status_label.setText(
                f"Socket : Connected   |   "
                f"Market : {self.controller.symbol}   |   "
                f"AI : Running"
            )

            print(
                "Timeframe switched successfully."
            )

        except Exception:

            traceback.print_exc()

            self.status_label.setText(
                f"Socket : Error   |   "
                f"Market : {self.controller.symbol}   |   "
                f"AI : Error"
            )

    # ========================================================
    # START BACKGROUND REFRESH
    # ========================================================

    def _start_background_refresh(
        self,
    ):

        # ----------------------------------------------------
        # Prevent overlapping analysis jobs.
        # ----------------------------------------------------

        if self.refresh_running:

            print(
                "REFRESH SKIPPED : "
                "previous analysis still running."
            )

            return

        self.refresh_running = True

        print(
            "\n======================================"
        )

        print(
            "BACKGROUND ANALYSIS START"
        )

        print(
            "GUI THREAD : FREE"
        )

        print(
            "LIVE WS    : PRESERVED"
        )

        print(
            "CHART      : LIVE"
        )

        print(
            "======================================"
        )

        # ----------------------------------------------------
        # Worker
        # ----------------------------------------------------

        self.refresh_thread = QThread(
            self
        )

        self.refresh_worker = (
            RefreshWorker(
                self.controller
            )
        )

        self.refresh_worker.moveToThread(
            self.refresh_thread
        )

        # ----------------------------------------------------
        # Thread -> Worker
        # ----------------------------------------------------

        self.refresh_thread.started.connect(
            self.refresh_worker.run
        )

        # ----------------------------------------------------
        # Worker -> GUI
        # ----------------------------------------------------

        self.refresh_worker.finished.connect(
            self._on_background_refresh_finished
        )

        self.refresh_worker.failed.connect(
            self._on_background_refresh_failed
        )

        # ----------------------------------------------------
        # Stop worker thread after result
        # ----------------------------------------------------

        self.refresh_worker.finished.connect(
            self.refresh_thread.quit
        )

        self.refresh_worker.failed.connect(
            self.refresh_thread.quit
        )

        # ----------------------------------------------------
        # Thread cleanup
        # ----------------------------------------------------

        self.refresh_thread.finished.connect(
            self._on_refresh_thread_finished
        )

        # ----------------------------------------------------
        # Start
        # ----------------------------------------------------

        self.refresh_thread.start()

    # ========================================================
    # BACKGROUND REFRESH FINISHED
    # ========================================================

    def _on_background_refresh_finished(
        self,
        data,
    ):

        try:

            if not isinstance(
                data,
                dict,
            ):

                print(
                    "Background refresh returned "
                    "invalid data."
                )

                return

            print(
                "\n======================================"
            )

            print(
                "BACKGROUND ANALYSIS FINISHED"
            )

            print(
                "======================================"
            )

            print(
                "Returned Keys :",
                list(
                    data.keys()
                ),
            )

            # =================================================
            # DASHBOARD UPDATE
            #
            # This executes on the GUI thread.
            # =================================================

            try:

                self.dashboard.update_dashboard(
                    data
                )

            except Exception:

                print(
                    "Dashboard update error:"
                )

                traceback.print_exc()

            # =================================================
            # MARKET STATUS
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
                        current_symbol,
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
            # LIVE PRICE DEBUG
            # =================================================

            try:

                live_price = (
                    data.get(
                        "live_price"
                    )
                )

                if live_price is not None:

                    self.last_live_price = (
                        live_price
                    )

                    print(
                        "Analysis Live Price :",
                        live_price,
                    )

                print(
                    "Live Price Source :",
                    data.get(
                        "live_price_source"
                    ),
                )

                print(
                    "Live Candle Source :",
                    data.get(
                        "live_candle_source"
                    ),
                )

            except Exception:

                pass

            print(
                "Dashboard analysis updated."
            )

            print(
                "Live WebSocket chart remains "
                "independent from this refresh."
            )

        except Exception:

            traceback.print_exc()

    # ========================================================
    # BACKGROUND REFRESH FAILED
    # ========================================================

    def _on_background_refresh_failed(
        self,
        error_text,
    ):

        print(
            "\n======================================"
        )

        print(
            "BACKGROUND ANALYSIS ERROR"
        )

        print(
            "======================================"
        )

        print(
            error_text
        )

        # ----------------------------------------------------
        # Analysis failure is NOT WebSocket failure.
        # ----------------------------------------------------

        self.status_label.setText(
            f"Socket : Connected   |   "
            f"Market : {self.controller.symbol}   |   "
            f"AI : Analysis Error"
        )

    # ========================================================
    # REFRESH THREAD FINISHED
    # ========================================================

    def _on_refresh_thread_finished(
        self,
    ):

        self.refresh_running = False

        worker = (
            self.refresh_worker
        )

        thread = (
            self.refresh_thread
        )

        self.refresh_worker = None

        self.refresh_thread = None

        if worker is not None:

            worker.deleteLater()

        if thread is not None:

            thread.deleteLater()

        print(
            "Background refresh worker cleaned."
        )

        print(
            "Live Futures WebSocket remains active."
        )

    # ========================================================
    # REFRESH SIGNAL
    # ========================================================

    def refresh_signal(
        self,
    ):

        """
        Starts background AI analysis.

        This NEVER controls live candle movement.

        Architecture:

            QTimer 30 sec
                  ↓
            Background QThread
                  ↓
            Controller.refresh()
                  ↓
            Dashboard

        Meanwhile:

            Futures WebSocket
                  ↓
            Controller
                  ↓
            Live Candle
                  ↓
            ChartWidget
                  ↓
            Immediate chart movement
        """

        print(
            "\n=============================="
        )

        print(
            "===== REFRESH REQUEST ====="
        )

        print(
            "=============================="
        )

        self._start_background_refresh()

    # ========================================================
    # LIVE UI HEALTH
    # ========================================================

    def _update_live_ui_state(
        self,
        price=None,
        candle=None,
    ):

        """
        Optional lightweight UI state helper.

        This method does NOT perform analysis.

        It only stores the latest live values that may be
        supplied by future Controller/UI bridge extensions.

        The authoritative live candle path remains inside
        Controller -> ChartWidget.
        """

        try:

            if price is not None:

                self.last_live_price = (
                    float(price)
                )

            if candle is not None:

                self.last_live_candle = (
                    candle
                )

        except Exception:

            pass

    # ========================================================
    # CLOSE EVENT
    # ========================================================

    def closeEvent(
        self,
        event,
    ):

        print(
            "\nClosing Liquidity Hunter AI..."
        )

        # ----------------------------------------------------
        # Stop 30-second analysis timer
        # ----------------------------------------------------

        try:

            if hasattr(
                self,
                "timer",
            ):

                self.timer.stop()

                print(
                    "30-second analysis timer stopped."
                )

        except Exception:

            pass

        # ----------------------------------------------------
        # Stop background analysis thread
        # ----------------------------------------------------

        try:

            if (
                self.refresh_thread is not None
                and self.refresh_thread.isRunning()
            ):

                print(
                    "Waiting for background analysis..."
                )

                self.refresh_thread.quit()

                self.refresh_thread.wait(
                    3000
                )

        except Exception:

            traceback.print_exc()

        # ----------------------------------------------------
        # Controller shutdown
        # ----------------------------------------------------

        try:

            if self.controller:

                self.controller.shutdown()

        except Exception:

            traceback.print_exc()

        print(
            "Liquidity Hunter AI closed."
        )

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