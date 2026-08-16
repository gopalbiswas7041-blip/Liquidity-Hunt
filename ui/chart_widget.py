"""
Liquidity Hunter AI
Chart Widget V20.9.6
Futures Live Synchronization Edition
LIVE BRIDGE FIX

Responsibilities
----------------
- Lightweight Charts WebEngine
- Historical candle loading
- GUI-thread-only JavaScript execution
- Thread-safe Futures live candle bridge
- Explicit Qt queued signal connection
- Throttled live candle rendering
- Same timestamp candle update protection
- New timestamp candle creation
- Stale update protection
- No chart reset during live updates
- JavaScript update diagnostics
- Live bridge diagnostics

Architecture
------------

Futures Worker Thread
        |
        | update_last_candle(candle)
        v
Qt Signal.emit(candle)
        |
        | QueuedConnection
        v
GUI Thread
        |
        v
_receive_live_candle_gui()
        |
        v
_pending_live_candle
        |
        v
100ms QTimer
        |
        v
_flush_live_candle()
        |
        v
runJavaScript()
        |
        v
window.updateLastCandle()
        |
        v
candleSeries.update()

IMPORTANT
---------
update_last_candle() MUST NOT touch GUI state.

It only emits the Qt signal.

All QWebEngineView / JavaScript / pending-state
operations happen inside the GUI thread.
"""

from __future__ import annotations

from pathlib import Path
import json
import threading

from PySide6.QtCore import (
    QUrl,
    QTimer,
    Signal,
    Slot,
    Qt,
)

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)

from PySide6.QtWebEngineWidgets import (
    QWebEngineView,
)


class ChartWidget(QWidget):

    # ======================================================
    # THREAD-SAFE LIVE CANDLE SIGNAL
    # ======================================================
    #
    # Futures WebSocket / worker thread calls:
    #
    #     update_last_candle(candle)
    #
    # That method ONLY emits this signal.
    #
    # Qt QueuedConnection then moves the candle into
    # the GUI thread.
    # ======================================================

    live_candle_signal = Signal(object)

    # ======================================================
    # INIT
    # ======================================================

    def __init__(self):

        super().__init__()

        # ==================================================
        # THREAD DIAGNOSTIC
        # ==================================================

        self._gui_thread_ident = (
            threading.get_ident()
        )

        # ==================================================
        # CHART READY STATE
        # ==================================================

        self.chart_ready = False

        # ==================================================
        # PENDING HISTORICAL DATA
        # ==================================================

        self.pending_candles = None

        # ==================================================
        # PENDING TRADE SIGNAL
        # ==================================================

        self.pending_signal = None

        # ==================================================
        # CHART CANDLE STATE
        # ==================================================

        self._last_chart_candle_time = None

        self._last_live_candle_time = None

        # ==================================================
        # LIVE CANDLE BUFFER
        # ==================================================

        self._pending_live_candle = None

        self._live_update_sequence = 0

        self._last_applied_live_sequence = 0

        # ==================================================
        # DIAGNOSTIC STATE
        # ==================================================

        self._live_updates_received = 0

        self._live_updates_flushed = 0

        self._live_updates_stale = 0

        self._live_updates_invalid = 0

        self._last_live_close = None

        self._last_js_result = None

        self._last_js_error = None

        self._last_live_thread = None

        self._last_gui_thread = None

        # ==================================================
        # LAYOUT
        # ==================================================

        layout = QVBoxLayout(
            self
        )

        title = QLabel(
            "📈 LIVE MARKET CHART"
        )

        title.setStyleSheet(
            """
            QLabel{
                font-size:18px;
                font-weight:bold;
                color:white;
                padding:8px;
            }
            """
        )

        # ==================================================
        # WEBVIEW
        # ==================================================

        self.webview = (
            QWebEngineView()
        )

        self.webview.setMinimumHeight(
            500
        )

        # ==================================================
        # CHART HTML
        # ==================================================

        html_file = (
            Path(__file__).parent
            / "resources"
            / "chart.html"
        )

        self.webview.loadFinished.connect(
            self._on_chart_loaded
        )

        self.webview.load(
            QUrl.fromLocalFile(
                str(
                    html_file.resolve()
                )
            )
        )

        layout.addWidget(
            title
        )

        layout.addWidget(
            self.webview
        )

        # ==================================================
        # SIGNAL -> GUI SLOT
        # ==================================================
        #
        # IMPORTANT:
        #
        # Explicit Qt.QueuedConnection is used.
        #
        # This guarantees that the receiver slot runs
        # through the ChartWidget GUI thread event loop.
        # ==================================================

        self.live_candle_signal.connect(
            self._receive_live_candle_gui,
            Qt.ConnectionType.QueuedConnection,
        )

        # ==================================================
        # GUI LIVE UPDATE TIMER
        # ==================================================
        #
        # 100 ms:
        #
        # maximum 10 visual chart updates / second.
        #
        # This does NOT throttle WebSocket ticks.
        #
        # It only throttles GUI rendering.
        # ==================================================

        self._live_chart_timer = (
            QTimer(self)
        )

        self._live_chart_timer.setInterval(
            100
        )

        self._live_chart_timer.timeout.connect(
            self._flush_live_candle
        )

        self._live_chart_timer.start()

        print(
            "============================================================"
        )
        print(
            "ChartWidget V20.9.6 initialized."
        )
        print(
            "LIVE BRIDGE FIX ACTIVE"
        )
        print(
            "GUI thread:",
            self._gui_thread_ident,
        )
        print(
            "============================================================"
        )

    # ======================================================
    # GUI THREAD CHECK
    # ======================================================

    def _is_gui_thread(self):

        current = threading.get_ident()

        return (
            current
            ==
            self._gui_thread_ident
        )

    # ======================================================
    # CHART LOADED
    # ======================================================

    @Slot(bool)
    def _on_chart_loaded(
        self,
        ok,
    ):

        # ==================================================
        # THREAD DIAGNOSTIC
        # ==================================================

        self._last_gui_thread = (
            threading.get_ident()
        )

        self.chart_ready = bool(
            ok
        )

        print(
            "============================================================"
        )

        print(
            "[CHART LOAD]"
        )

        print(
            "Loaded     :",
            ok,
        )

        print(
            "GUI Thread :",
            self._last_gui_thread,
        )

        print(
            "Expected   :",
            self._gui_thread_ident,
        )

        print(
            "GUI Match  :",
            self._is_gui_thread(),
        )

        print(
            "============================================================"
        )

        if not ok:

            print(
                "❌ Chart HTML failed to load."
            )

            return

        print(
            "✅ Chart HTML loaded successfully."
        )

        print(
            "✅ JavaScript bridge available."
        )

        # ==================================================
        # HISTORICAL DATA
        # ==================================================

        if (
            self.pending_candles
            is not None
        ):

            data = (
                self.pending_candles
            )

            self.pending_candles = None

            print(
                "[CHART LOAD] Applying pending historical data."
            )

            self.set_chart_data(
                data
            )

        # ==================================================
        # PENDING SIGNAL
        # ==================================================

        if (
            self.pending_signal
            is not None
        ):

            signal = (
                self.pending_signal
            )

            self.pending_signal = None

            print(
                "[CHART LOAD] Applying pending trade signal."
            )

            self.show_trade_signal(
                signal
            )

    # ======================================================
    # DATAFRAME -> CANDLES
    # ======================================================

    def _convert_dataframe(
        self,
        df,
    ):

        if df is None:

            return []

        if df.empty:

            return []

        candles = []

        for index, row in df.iterrows():

            try:

                timestamp = int(
                    index.timestamp()
                )

                candles.append(
                    {
                        "time":
                            timestamp,

                        "open":
                            float(
                                row["Open"]
                            ),

                        "high":
                            float(
                                row["High"]
                            ),

                        "low":
                            float(
                                row["Low"]
                            ),

                        "close":
                            float(
                                row["Close"]
                            ),
                    }
                )

            except Exception as exc:

                print(
                    "[CHART HISTORICAL] "
                    "Candle conversion skipped:",
                    exc,
                )

                continue

        candles.sort(
            key=lambda item:
                item["time"]
        )

        return candles

    # ======================================================
    # HISTORICAL DATA
    # ======================================================

    @Slot(object)
    def set_chart_data(
        self,
        dataframe,
    ):

        # ==================================================
        # GUI THREAD ONLY
        # ==================================================

        if not self._is_gui_thread():

            print(
                "⚠️ set_chart_data called outside GUI thread."
            )

            self.pending_candles = (
                dataframe
            )

            return

        # ==================================================
        # CHART NOT READY
        # ==================================================

        if not self.chart_ready:

            print(
                "[CHART HISTORICAL] "
                "Chart not ready. Data queued."
            )

            self.pending_candles = (
                dataframe
            )

            return

        # ==================================================
        # CONVERT
        # ==================================================

        candles = (
            self._convert_dataframe(
                dataframe
            )
        )

        if not candles:

            print(
                "⚠️ [CHART HISTORICAL] No candles."
            )

            return

        # ==================================================
        # RESET CHART STATE
        # ==================================================

        try:

            latest_time = int(
                candles[-1]["time"]
            )

            self._last_chart_candle_time = (
                latest_time
            )

            self._last_live_candle_time = (
                None
            )

            self._pending_live_candle = (
                None
            )

            self._live_update_sequence = 0

            self._last_applied_live_sequence = 0

            self._live_updates_received = 0

            self._live_updates_flushed = 0

            self._live_updates_stale = 0

            self._live_updates_invalid = 0

            self._last_live_close = (
                candles[-1]["close"]
            )

            self._last_js_result = None

            self._last_js_error = None

        except Exception as exc:

            print(
                "❌ Chart historical state error:",
                exc,
            )

            return

        # ==================================================
        # HISTORICAL DEBUG
        # ==================================================

        print(
            "============================================================"
        )

        print(
            "[CHART HISTORICAL]"
        )

        print(
            "Candles       :",
            len(candles),
        )

        print(
            "First time    :",
            candles[0]["time"],
        )

        print(
            "Last time     :",
            candles[-1]["time"],
        )

        print(
            "Last close    :",
            candles[-1]["close"],
        )

        print(
            "Chart ready   :",
            self.chart_ready,
        )

        print(
            "============================================================"
        )

        # ==================================================
        # JAVASCRIPT
        # ==================================================

        js = (
            "window.setChartData("
            + json.dumps(
                candles,
                separators=(
                    ",",
                    ":",
                ),
            )
            + ");"
        )

        try:

            self.webview.page().runJavaScript(
                js,
                self._on_historical_js_result,
            )

        except Exception as exc:

            self._last_js_error = str(
                exc
            )

            print(
                "❌ Historical JavaScript error:",
                exc,
            )

    # ======================================================
    # HISTORICAL JS RESULT
    # ======================================================

    def _on_historical_js_result(
        self,
        result,
    ):

        self._last_js_result = result

        print(
            "[CHART HISTORICAL JS RESULT]",
            result,
        )

    # ======================================================
    # LIVE CANDLE ENTRY POINT
    # ======================================================
    #
    # IMPORTANT:
    #
    # This method may be called by:
    #
    # - Futures WebSocket thread
    # - Futures worker
    # - Controller worker
    #
    # Therefore it MUST NOT:
    #
    # - touch QWebEngineView
    # - call runJavaScript
    # - modify GUI state
    # - modify pending candle state
    #
    # It ONLY emits a Qt signal.
    # ======================================================

    def update_last_candle(
        self,
        candle,
    ):

        if candle is None:

            print(
                "⚠️ [LIVE BRIDGE] Received None candle."
            )

            return

        # ==================================================
        # WORKER THREAD DIAGNOSTIC
        # ==================================================

        current_thread = (
            threading.get_ident()
        )

        self._last_live_thread = (
            current_thread
        )

        # ==================================================
        # SAFE DEBUG
        # ==================================================

        try:

            timestamp = int(
                candle.timestamp.timestamp()
            )

            close = float(
                candle.close
            )

        except Exception as exc:

            print(
                "❌ [LIVE BRIDGE] Invalid candle:",
                exc,
            )

            self._live_updates_invalid += 1

            return

        print(
            "------------------------------------------------------------"
        )

        print(
            "[CONTROLLER → CHART]"
        )

        print(
            "Thread       :",
            current_thread,
        )

        print(
            "GUI Thread   :",
            self._gui_thread_ident,
        )

        print(
            "Candle time  :",
            candle.timestamp,
        )

        print(
            "Close        :",
            close,
        )

        print(
            "Signal emit  : YES",
        )

        print(
            "------------------------------------------------------------"
        )

        # ==================================================
        # CRITICAL FIX
        # ==================================================
        #
        # DO NOT TOUCH:
        #
        # self._pending_live_candle
        #
        # here.
        #
        # DO NOT TOUCH:
        #
        # self._last_chart_candle_time
        #
        # here.
        #
        # ONLY emit.
        # ==================================================

        try:

            self.live_candle_signal.emit(
                candle
            )

        except Exception as exc:

            print(
                "❌ [LIVE BRIDGE] Signal emit failed:",
                exc,
            )

    # ======================================================
    # GUI THREAD RECEIVER
    # ======================================================
    #
    # This is the ONLY place where live candle GUI state
    # is modified.
    # ======================================================

    @Slot(object)
    def _receive_live_candle_gui(
        self,
        candle,
    ):

        # ==================================================
        # GUI THREAD DIAGNOSTIC
        # ==================================================

        gui_thread = (
            threading.get_ident()
        )

        self._last_gui_thread = (
            gui_thread
        )

        print(
            "============================================================"
        )

        print(
            "[CHART GUI RECEIVED]"
        )

        print(
            "Thread       :",
            gui_thread,
        )

        print(
            "Expected GUI :",
            self._gui_thread_ident,
        )

        print(
            "GUI Match    :",
            gui_thread
            ==
            self._gui_thread_ident,
        )

        print(
            "============================================================"
        )

        # ==================================================
        # SAFETY
        # ==================================================

        if not self._is_gui_thread():

            print(
                "❌ CRITICAL: Live candle receiver "
                "is NOT running in GUI thread."
            )

            return

        if candle is None:

            return

        # ==================================================
        # PARSE CANDLE
        # ==================================================

        try:

            timestamp = int(
                candle.timestamp.timestamp()
            )

            candle_data = {

                "time":
                    timestamp,

                "open":
                    float(
                        candle.open
                    ),

                "high":
                    float(
                        candle.high
                    ),

                "low":
                    float(
                        candle.low
                    ),

                "close":
                    float(
                        candle.close
                    ),
            }

        except Exception as exc:

            self._live_updates_invalid += 1

            print(
                "❌ GUI live candle receive error:",
                exc,
            )

            return

        # ==================================================
        # LIVE UPDATE RECEIVED
        # ==================================================

        self._live_updates_received += 1

        self._last_live_close = (
            candle_data["close"]
        )

        # ==================================================
        # STALE PROTECTION
        # ==================================================

        last_time = (
            self._last_chart_candle_time
        )

        if (
            last_time is not None
            and
            timestamp < last_time
        ):

            self._live_updates_stale += 1

            print(
                "[CHART LIVE] STALE RECEIVED:",
                timestamp,
                "<",
                last_time,
            )

            return

        # ==================================================
        # SEQUENCE
        # ==================================================

        self._live_update_sequence += 1

        candle_data[
            "_seq"
        ] = (
            self._live_update_sequence
        )

        # ==================================================
        # LATEST CANDLE WINS
        # ==================================================
        #
        # If 50 ticks arrive within 100ms,
        # only the newest candle state is rendered.
        #
        # Tick processing itself remains untouched.
        # ==================================================

        self._pending_live_candle = (
            candle_data
        )

        print(
            "[CHART GUI BUFFERED]"
            f" seq={self._live_update_sequence}"
            f" time={timestamp}"
            f" close={candle_data['close']}"
        )

    # ======================================================
    # GUI TIMER FLUSH
    # ======================================================

    @Slot()
    def _flush_live_candle(
        self,
    ):

        # ==================================================
        # GUI THREAD CHECK
        # ==================================================

        if not self._is_gui_thread():

            print(
                "❌ CRITICAL: _flush_live_candle "
                "outside GUI thread."
            )

            return

        # ==================================================
        # CHART NOT READY
        # ==================================================

        if not self.chart_ready:

            return

        # ==================================================
        # NO PENDING UPDATE
        # ==================================================

        candle_data = (
            self._pending_live_candle
        )

        if candle_data is None:

            return

        # ==================================================
        # CONSUME
        # ==================================================

        self._pending_live_candle = None

        try:

            sequence = int(
                candle_data[
                    "_seq"
                ]
            )

            if (
                sequence
                <=
                self._last_applied_live_sequence
            ):

                print(
                    "[CHART LIVE] "
                    "Duplicate sequence ignored:",
                    sequence,
                )

                return

            timestamp = int(
                candle_data[
                    "time"
                ]
            )

            # ==================================================
            # TIMESTAMP PROTECTION
            # ==================================================
            #
            # IMPORTANT:
            #
            # timestamp == last timestamp
            # is VALID.
            #
            # It means:
            #
            # existing 5m candle is being updated.
            #
            # Only timestamp < last timestamp is stale.
            # ==================================================

            if (
                self._last_chart_candle_time
                is not None
                and
                timestamp
                <
                self._last_chart_candle_time
            ):

                self._live_updates_stale += 1

                print(
                    "[CHART LIVE] "
                    "FLUSH STALE:",
                    timestamp,
                    "<",
                    self._last_chart_candle_time,
                )

                return

            # ==================================================
            # APPLY INTERNAL STATE
            # ==================================================

            self._last_applied_live_sequence = (
                sequence
            )

            self._last_chart_candle_time = (
                timestamp
            )

            self._last_live_candle_time = (
                timestamp
            )

            self._live_updates_flushed += 1

            # ==================================================
            # JS CANDLE
            # ==================================================

            js_candle = {

                "time":
                    timestamp,

                "open":
                    float(
                        candle_data["open"]
                    ),

                "high":
                    float(
                        candle_data["high"]
                    ),

                "low":
                    float(
                        candle_data["low"]
                    ),

                "close":
                    float(
                        candle_data["close"]
                    ),
            }

            # ==================================================
            # DEBUG
            # ==================================================

            print(
                "============================================================"
            )

            print(
                "[CHART LIVE FLUSH]"
            )

            print(
                "Sequence     :",
                sequence,
            )

            print(
                "Timestamp    :",
                timestamp,
            )

            print(
                "Open         :",
                js_candle["open"],
            )

            print(
                "High         :",
                js_candle["high"],
            )

            print(
                "Low          :",
                js_candle["low"],
            )

            print(
                "Close        :",
                js_candle["close"],
            )

            print(
                "JS Dispatch  : YES",
            )

            print(
                "============================================================"
            )

            # ==================================================
            # JAVASCRIPT
            # ==================================================

            js = (
                "window.updateLastCandle("
                + json.dumps(
                    js_candle,
                    separators=(
                        ",",
                        ":",
                    ),
                )
                + ");"
            )

            # ==================================================
            # GUI THREAD ONLY
            # ==================================================

            self.webview.page().runJavaScript(
                js,
                self._on_live_js_result,
            )

        except Exception as exc:

            self._last_js_error = str(
                exc
            )

            print(
                "❌ Live candle JavaScript dispatch error:",
                exc,
            )

    # ======================================================
    # LIVE JS RESULT
    # ======================================================

    def _on_live_js_result(
        self,
        result,
    ):

        self._last_js_result = result

        print(
            "[CHART LIVE JS RESULT]",
            result,
        )

        if result is None:

            print(
                "⚠️ [CHART LIVE JS RESULT] "
                "JavaScript returned None."
            )

        elif result != "UPDATED":

            print(
                "⚠️ [CHART LIVE JS RESULT] "
                "Unexpected result:",
                result,
            )

    # ======================================================
    # TRADE SIGNAL
    # ======================================================

    @Slot(object)
    def show_trade_signal(
        self,
        signal,
    ):

        # ==================================================
        # GUI THREAD CHECK
        # ==================================================

        if not self._is_gui_thread():

            print(
                "⚠️ show_trade_signal called "
                "outside GUI thread."
            )

            self.pending_signal = (
                signal
            )

            return

        # ==================================================
        # CHART NOT READY
        # ==================================================

        if not self.chart_ready:

            self.pending_signal = (
                signal
            )

            return

        try:

            js = (
                "window.showTradeSignal("
                + json.dumps(
                    signal,
                    separators=(
                        ",",
                        ":",
                    ),
                )
                + ");"
            )

            self.webview.page().runJavaScript(
                js
            )

        except Exception as exc:

            print(
                "❌ Trade signal JavaScript error:",
                exc,
            )

    # ======================================================
    # FORCE RELOAD
    # ======================================================

    @Slot()
    def force_reload(
        self,
    ):

        # ==================================================
        # GUI THREAD CHECK
        # ==================================================

        if not self._is_gui_thread():

            print(
                "⚠️ force_reload requested "
                "outside GUI thread."
            )

            return

        print(
            "============================================================"
        )

        print(
            "[CHART] FORCE RELOAD"
        )

        print(
            "============================================================"
        )

        self.chart_ready = False

        self._pending_live_candle = (
            None
        )

        self._last_chart_candle_time = (
            None
        )

        self._last_live_candle_time = (
            None
        )

        self._live_update_sequence = 0

        self._last_applied_live_sequence = 0

        self._live_updates_received = 0

        self._live_updates_flushed = 0

        self._live_updates_stale = 0

        self._live_updates_invalid = 0

        self._last_live_close = None

        self._last_js_result = None

        self._last_js_error = None

        try:

            self.webview.reload()

        except Exception as exc:

            print(
                "❌ Chart reload error:",
                exc,
            )

    # ======================================================
    # DIAGNOSTICS
    # ======================================================

    @Slot()
    def chart_live_status(
        self,
    ):

        return {

            "chart_ready":
                self.chart_ready,

            "gui_thread":
                self._gui_thread_ident,

            "last_live_thread":
                self._last_live_thread,

            "last_gui_thread":
                self._last_gui_thread,

            "last_chart_candle_time":
                self._last_chart_candle_time,

            "last_live_candle_time":
                self._last_live_candle_time,

            "pending_live_candle":
                self._pending_live_candle
                is not None,

            "live_updates_received":
                self._live_updates_received,

            "live_updates_flushed":
                self._live_updates_flushed,

            "live_updates_stale":
                self._live_updates_stale,

            "live_updates_invalid":
                self._live_updates_invalid,

            "last_live_close":
                self._last_live_close,

            "last_js_result":
                self._last_js_result,

            "last_js_error":
                self._last_js_error,
        }

    # ======================================================
    # CLEANUP
    # ======================================================

    def closeEvent(
        self,
        event,
    ):

        try:

            if (
                hasattr(
                    self,
                    "_live_chart_timer",
                )
            ):

                self._live_chart_timer.stop()

        except Exception:

            pass

        try:

            self.webview.stop()

        except Exception:

            pass

        super().closeEvent(
            event
        )