// ==========================================
// Liquidity Hunter AI V20.6
// chart.js
// ==========================================

console.log("==========================================");
console.log("Liquidity Hunter AI V20.6 Chart Loaded");
console.log("==========================================");

console.log(
    "LightweightCharts =",
    LightweightCharts
);

console.log(
    "Version =",
    LightweightCharts.version
);

// ==========================================
// JS Candle State
//
// IMPORTANT:
// This variable must exist BEFORE
// setChartData() and updateLastCandle().
// ==========================================

let jsLastCandleTime = null;

// ==========================================
// Create Chart
// ==========================================

const chart = LightweightCharts.createChart(
    document.getElementById("chart"),
    {
        layout: {
            background: {
                color: "#131722"
            },

            textColor: "#D9D9D9"
        },

        grid: {
            vertLines: {
                color: "#2B2B43"
            },

            horzLines: {
                color: "#363C4E"
            }
        },

        crosshair: {
            mode:
                LightweightCharts.CrosshairMode.Normal
        },

        rightPriceScale: {
            borderColor: "#444"
        },

        timeScale: {
            borderColor: "#444",

            timeVisible: true,

            secondsVisible: false
        },

        autoSize: true
    }
);

// ==========================================
// Candlestick Series
// ==========================================

const candleSeries = chart.addSeries(
    LightweightCharts.CandlestickSeries,
    {}
);

// ==========================================
// AI Overlay Series
// ==========================================

const signalSeries = chart.addSeries(
    LightweightCharts.LineSeries,
    {
        color: "#FFD700",

        lineWidth: 0,

        lastValueVisible: false,

        priceLineVisible: false,

        crosshairMarkerVisible: false
    }
);

// ==========================================
// Trade Markers
// ==========================================

const tradeMarkers = [];

const markerPlugin =
    LightweightCharts.createSeriesMarkers(
        candleSeries,
        []
    );

// ==========================================
// HISTORICAL DATA
// ==========================================

window.setChartData = function(candles)
{
    try
    {
        console.log("=================================");
        console.log("setChartData() CALLED");

        // ------------------------------------------
        // Basic validation
        // ------------------------------------------

        if (!Array.isArray(candles))
        {
            console.error(
                "❌ Historical data is not an array"
            );

            return "INVALID_DATA";
        }

        if (candles.length === 0)
        {
            console.warn(
                "⚠️ No historical candles received"
            );

            return "NO_DATA";
        }

        console.log(
            "Received historical candles :",
            candles.length
        );

        // ------------------------------------------
        // Normalize historical candles
        // ------------------------------------------

        const normalizedCandles = [];

        for (const candle of candles)
        {
            const time = Number(
                candle.time
            );

            const open = Number(
                candle.open
            );

            const high = Number(
                candle.high
            );

            const low = Number(
                candle.low
            );

            const close = Number(
                candle.close
            );

            // --------------------------------------
            // Validate
            // --------------------------------------

            if (!Number.isFinite(time))
            {
                console.warn(
                    "Skipping invalid candle time:",
                    candle
                );

                continue;
            }

            if (
                !Number.isFinite(open) ||
                !Number.isFinite(high) ||
                !Number.isFinite(low) ||
                !Number.isFinite(close)
            )
            {
                console.warn(
                    "Skipping invalid OHLC:",
                    candle
                );

                continue;
            }

            normalizedCandles.push({

                time: time,

                open: open,

                high: high,

                low: low,

                close: close

            });
        }

        // ------------------------------------------
        // Validate normalized data
        // ------------------------------------------

        if (
            normalizedCandles.length === 0
        )
        {
            console.error(
                "❌ No valid historical candles"
            );

            return "NO_VALID_DATA";
        }

        // ------------------------------------------
        // Ensure chronological order
        // ------------------------------------------

        normalizedCandles.sort(
            (a, b) =>
                a.time - b.time
        );

        // ------------------------------------------
        // Historical data → Chart
        // ------------------------------------------

        candleSeries.setData(
            normalizedCandles
        );

        // ------------------------------------------
        // IMPORTANT
        //
        // Register latest historical candle.
        //
        // This allows live candle protection
        // to work correctly.
        // ------------------------------------------

        const lastCandle =
            normalizedCandles[
                normalizedCandles.length - 1
            ];

        jsLastCandleTime =
            Number(
                lastCandle.time
            );

        // ------------------------------------------
        // Debug
        // ------------------------------------------

        console.log(
            "First Historical Candle :",
            normalizedCandles[0]
        );

        console.log(
            "Last Historical Candle :",
            lastCandle
        );

        console.log(
            "JS Latest Candle Time :",
            jsLastCandleTime
        );

        console.log(
            "Historical Candle Count :",
            normalizedCandles.length
        );

        // ------------------------------------------
        // IMPORTANT
        //
        // fitContent() is ONLY called here.
        //
        // It is NOT called during live candle
        // updates.
        //
        // Therefore live updates cannot reset
        // user's chart zoom/position.
        // ------------------------------------------

        chart.timeScale().fitContent();

        console.log(
            "Historical chart loaded successfully."
        );

        console.log("=================================");

        return "HISTORICAL_LOADED";

    }
    catch(err)
    {
        console.error(
            "❌ Historical Chart Error"
        );

        console.error(err);

        console.log("=================================");

        return "ERROR";
    }
};

// ==========================================
// LIVE CANDLE UPDATE
// ==========================================

window.updateLastCandle = function(candle)
{
    console.log("=================================");
    console.log(
        "JS updateLastCandle() CALLED"
    );

    console.log(
        "Incoming candle =",
        candle
    );

    try
    {
        // ------------------------------------------
        // Basic validation
        // ------------------------------------------

        if (
            candle === null ||
            candle === undefined
        )
        {
            console.error(
                "❌ Candle is null"
            );

            return "INVALID_CANDLE";
        }

        // ------------------------------------------
        // Normalize
        // ------------------------------------------

        const incomingTime =
            Number(
                candle.time
            );

        const open =
            Number(
                candle.open
            );

        const high =
            Number(
                candle.high
            );

        const low =
            Number(
                candle.low
            );

        const close =
            Number(
                candle.close
            );

        // ------------------------------------------
        // Validate timestamp
        // ------------------------------------------

        if (
            !Number.isFinite(
                incomingTime
            )
        )
        {
            console.error(
                "❌ INVALID CANDLE TIME"
            );

            return "INVALID_TIME";
        }

        // ------------------------------------------
        // Validate OHLC
        // ------------------------------------------

        if (
            !Number.isFinite(open) ||
            !Number.isFinite(high) ||
            !Number.isFinite(low) ||
            !Number.isFinite(close)
        )
        {
            console.error(
                "❌ INVALID OHLC"
            );

            return "INVALID_OHLC";
        }

        // ------------------------------------------
        // Normalize payload
        // ------------------------------------------

        const normalizedCandle = {

            time:
                incomingTime,

            open:
                open,

            high:
                high,

            low:
                low,

            close:
                close

        };

        console.log(
            "Normalized Candle =",
            normalizedCandle
        );

        console.log(
            "JS Last Candle Time =",
            jsLastCandleTime
        );

        console.log(
            "JS Incoming Time =",
            incomingTime
        );

        // ==========================================
        // STALE CANDLE PROTECTION
        // ==========================================

        if (
            jsLastCandleTime !== null
            &&
            incomingTime <
            jsLastCandleTime
        )
        {
            console.warn(
                "⚠️ JS STALE CANDLE IGNORED"
            );

            console.warn(
                "Incoming =",
                incomingTime
            );

            console.warn(
                "Latest =",
                jsLastCandleTime
            );

            return "STALE";
        }

        // ==========================================
        // SAME CANDLE
        //
        // Existing candle is updated.
        // ==========================================

        if (
            jsLastCandleTime !== null
            &&
            incomingTime ===
            jsLastCandleTime
        )
        {
            console.log(
                "🟡 SAME CANDLE"
            );

            console.log(
                "Updating current candle..."
            );
        }

        // ==========================================
        // NEW CANDLE
        // ==========================================

        if (
            jsLastCandleTime === null
            ||
            incomingTime >
            jsLastCandleTime
        )
        {
            console.log(
                "🟢 NEWER LIVE CANDLE"
            );

            console.log(
                "New candle accepted."
            );
        }

        // ==========================================
        // UPDATE LIGHTWEIGHT CHART
        // ==========================================

        candleSeries.update(
            normalizedCandle
        );

        // ==========================================
        // Register latest timestamp
        // ==========================================

        jsLastCandleTime =
            incomingTime;

        console.log(
            "✅ LIVE CANDLE UPDATE SUCCESS"
        );

        console.log(
            "JS Latest Candle Time =",
            jsLastCandleTime
        );

        console.log(
            "IMPORTANT:"
        );

        console.log(
            "Chart zoom/position NOT reset."
        );

        console.log("=================================");

        return "UPDATED";

    }
    catch(err)
    {
        console.error(
            "❌ LIVE CANDLE UPDATE FAILED"
        );

        console.error(err);

        console.log("=================================");

        return "ERROR";
    }
};

// ==========================================
// AI TRADE SIGNAL OVERLAY
// ==========================================

window.showTradeSignal = function(signal)
{
    try
    {
        console.log(
            "AI SIGNAL RECEIVED"
        );

        console.log(
            signal
        );

        if (
            !signal
        )
        {
            console.warn(
                "No signal data"
            );

            return;
        }

        const signalTime =
            Number(
                signal.time
            );

        if (
            !Number.isFinite(
                signalTime
            )
        )
        {
            console.error(
                "Invalid signal timestamp"
            );

            return;
        }

        // ------------------------------------------
        // Normalize direction
        // ------------------------------------------

        const direction =
            String(
                signal.direction
            ).toUpperCase();

        // ------------------------------------------
        // Add marker
        // ------------------------------------------

        tradeMarkers.push({

            time:
                signalTime,

            position:
                direction === "BUY"
                ? "belowBar"
                : "aboveBar",

            color:
                direction === "BUY"
                ? "#00FF00"
                : "#FF0000",

            shape:
                direction === "BUY"
                ? "arrowUp"
                : "arrowDown",

            text:
                direction

        });

        // ------------------------------------------
        // Update markers
        // ------------------------------------------

        markerPlugin.setMarkers(
            tradeMarkers
        );

        console.log(
            "✅ Signal Marker Added"
        );

    }
    catch(err)
    {
        console.error(
            "❌ Overlay Error"
        );

        console.error(err);
    }
};

// ==========================================
// RESIZE
// ==========================================

window.addEventListener(
    "resize",
    () =>
    {
        try
        {
            chart.applyOptions({
                width:
                    window.innerWidth,

                height:
                    window.innerHeight
            });
        }
        catch(err)
        {
            console.error(
                "Chart resize error:",
                err
            );
        }
    }
);

// ==========================================
// CHART READY
// ==========================================

console.log(
    "================================="
);

console.log(
    "Liquidity Hunter AI Chart Ready"
);

console.log(
    "Historical candles : 1000 supported"
);

console.log(
    "Live candle update : ENABLED"
);

console.log(
    "Chart reset protection : ENABLED"
);

console.log(
    "================================="
);