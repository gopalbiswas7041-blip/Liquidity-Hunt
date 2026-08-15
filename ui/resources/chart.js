// ==========================================
// Liquidity Hunter AI
// Chart JS V20.9.4
// Futures Live Synchronization Edition
// ==========================================

console.log(
    "Liquidity Hunter AI V20.9.4 Chart Loaded"
);

// ==========================================
// STATE
// ==========================================

let jsLastCandleTime = null;

// ==========================================
// CHART
// ==========================================

const chart =
    LightweightCharts.createChart(
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
                    LightweightCharts
                        .CrosshairMode
                        .Normal
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
// CANDLE SERIES
// ==========================================

const candleSeries =
    chart.addSeries(
        LightweightCharts.CandlestickSeries,
        {}
    );

// ==========================================
// SIGNAL SERIES
// ==========================================

const signalSeries =
    chart.addSeries(
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
// TRADE MARKERS
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
        if (!Array.isArray(candles))
        {
            return "INVALID_DATA";
        }

        if (candles.length === 0)
        {
            return "NO_DATA";
        }

        const normalizedCandles = [];

        for (
            const candle of candles
        )
        {
            const time =
                Number(candle.time);

            const open =
                Number(candle.open);

            const high =
                Number(candle.high);

            const low =
                Number(candle.low);

            const close =
                Number(candle.close);

            if (
                !Number.isFinite(time) ||
                !Number.isFinite(open) ||
                !Number.isFinite(high) ||
                !Number.isFinite(low) ||
                !Number.isFinite(close)
            )
            {
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

        if (
            normalizedCandles.length === 0
        )
        {
            return "NO_VALID_DATA";
        }

        normalizedCandles.sort(
            (a, b) =>
                a.time - b.time
        );

        // ------------------------------------------
        // Remove duplicate timestamps
        // ------------------------------------------

        const uniqueCandles = [];

        let previousTime = null;

        for (
            const candle of normalizedCandles
        )
        {
            if (
                previousTime !== null &&
                candle.time === previousTime
            )
            {
                uniqueCandles[
                    uniqueCandles.length - 1
                ] = candle;

                continue;
            }

            uniqueCandles.push(candle);

            previousTime =
                candle.time;
        }

        // ------------------------------------------
        // Set data
        // ------------------------------------------

        candleSeries.setData(
            uniqueCandles
        );

        // ------------------------------------------
        // Register latest candle
        // ------------------------------------------

        const lastCandle =
            uniqueCandles[
                uniqueCandles.length - 1
            ];

        jsLastCandleTime =
            Number(lastCandle.time);

        // ------------------------------------------
        // Fit ONLY on historical load
        // ------------------------------------------

        chart
            .timeScale()
            .fitContent();

        return "HISTORICAL_LOADED";
    }
    catch(error)
    {
        console.error(
            "Historical chart error:",
            error
        );

        return "ERROR";
    }
};

// ==========================================
// LIVE CANDLE UPDATE
// ==========================================

window.updateLastCandle = function(candle)
{
    try
    {
        if (
            candle === null ||
            candle === undefined
        )
        {
            return "INVALID_CANDLE";
        }

        const incomingTime =
            Number(candle.time);

        const open =
            Number(candle.open);

        const high =
            Number(candle.high);

        const low =
            Number(candle.low);

        const close =
            Number(candle.close);

        if (
            !Number.isFinite(
                incomingTime
            )
        )
        {
            return "INVALID_TIME";
        }

        if (
            !Number.isFinite(open) ||
            !Number.isFinite(high) ||
            !Number.isFinite(low) ||
            !Number.isFinite(close)
        )
        {
            return "INVALID_OHLC";
        }

        // ==========================================
        // STALE PROTECTION
        // ==========================================

        if (
            jsLastCandleTime !== null &&
            incomingTime <
            jsLastCandleTime
        )
        {
            return "STALE";
        }

        // ==========================================
        // UPDATE CHART
        // ==========================================

        candleSeries.update({
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
        });

        // ==========================================
        // REGISTER LATEST
        // ==========================================

        jsLastCandleTime =
            incomingTime;

        return "UPDATED";
    }
    catch(error)
    {
        console.error(
            "Live candle update error:",
            error
        );

        return "ERROR";
    }
};

// ==========================================
// TRADE SIGNAL
// ==========================================

window.showTradeSignal = function(signal)
{
    try
    {
        if (!signal)
        {
            return;
        }

        const signalTime =
            Number(signal.time);

        if (
            !Number.isFinite(
                signalTime
            )
        )
        {
            return;
        }

        const direction =
            String(
                signal.direction || ""
            ).toUpperCase();

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
        // Sort markers
        // ------------------------------------------

        tradeMarkers.sort(
            (a, b) =>
                a.time - b.time
        );

        markerPlugin.setMarkers(
            tradeMarkers
        );
    }
    catch(error)
    {
        console.error(
            "Trade overlay error:",
            error
        );
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
        catch(error)
        {
            console.error(
                "Chart resize error:",
                error
            );
        }
    }
);

// ==========================================
// READY
// ==========================================

console.log(
    "Liquidity Hunter AI Chart Ready"
);

console.log(
    "Historical candles : ENABLED"
);

console.log(
    "Live candle update : ENABLED"
);

console.log(
    "GUI throttle       : 100ms"
);

console.log(
    "Chart reset        : PROTECTED"
);