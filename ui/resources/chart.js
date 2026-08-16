// ==========================================
// Liquidity Hunter AI
// Chart JS V20.9.5
// Futures Live Synchronization Edition
// ==========================================

console.log(
    "Liquidity Hunter AI V20.9.5 Chart Loaded"
);

// ==========================================
// STATE
// ==========================================

let jsLastCandleTime = null;

let jsHistoricalLoaded = false;

let jsLiveUpdateCount = 0;

let jsRejectedStaleCount = 0;

let jsInvalidUpdateCount = 0;


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

            // ======================================
            // IMPORTANT
            //
            // Explicit sizing is handled below.
            // Do NOT use autoSize:true together with
            // width/height updates.
            // ======================================

            autoSize: false,

            width:
                document.getElementById(
                    "chart"
                ).clientWidth,

            height:
                document.getElementById(
                    "chart"
                ).clientHeight
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
            console.warn(
                "setChartData: invalid array"
            );

            return "INVALID_DATA";
        }

        if (candles.length === 0)
        {
            console.warn(
                "setChartData: empty data"
            );

            return "NO_DATA";
        }


        // ======================================
        // NORMALIZE
        // ======================================

        const normalizedCandles = [];

        for (
            const candle of candles
        )
        {
            if (!candle)
            {
                continue;
            }

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


            // ==================================
            // Lightweight Charts expects
            // Unix timestamp in SECONDS.
            // ==================================

            normalizedCandles.push({

                time:
                    time,

                open:
                    open,

                high:
                    high,

                low:
                    low,

                close:
                    close
            });
        }


        if (
            normalizedCandles.length === 0
        )
        {
            return "NO_VALID_DATA";
        }


        // ======================================
        // SORT
        // ======================================

        normalizedCandles.sort(
            (a, b) =>
                a.time - b.time
        );


        // ======================================
        // REMOVE DUPLICATES
        // ======================================

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

            uniqueCandles.push(
                candle
            );

            previousTime =
                candle.time;
        }


        if (
            uniqueCandles.length === 0
        )
        {
            return "NO_VALID_DATA";
        }


        // ======================================
        // SET HISTORICAL DATA
        // ======================================

        candleSeries.setData(
            uniqueCandles
        );


        // ======================================
        // REGISTER LATEST HISTORICAL CANDLE
        // ======================================

        const lastCandle =
            uniqueCandles[
                uniqueCandles.length - 1
            ];

        jsLastCandleTime =
            Number(
                lastCandle.time
            );

        jsHistoricalLoaded = true;


        // ======================================
        // RESET LIVE COUNTER
        // ======================================

        jsLiveUpdateCount = 0;

        jsRejectedStaleCount = 0;

        jsInvalidUpdateCount = 0;


        // ======================================
        // FIT ONLY AFTER HISTORICAL LOAD
        //
        // NEVER fitContent() during live updates.
        // ======================================

        chart
            .timeScale()
            .fitContent();


        console.log(
            "Chart historical data loaded:",
            uniqueCandles.length,
            "candles"
        );

        console.log(
            "Chart latest candle:",
            jsLastCandleTime
        );


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
     console.log(
        "[CHART JS UPDATE]",
        candle.time,
        candle.close
    );
    
    try
    {
        if (
            candle === null ||
            candle === undefined
        )
        {
            jsInvalidUpdateCount++;

            return "INVALID_CANDLE";
        }


        // ======================================
        // NORMALIZE
        // ======================================

        let incomingTime =
            Number(candle.time);

        const open =
            Number(candle.open);

        const high =
            Number(candle.high);

        const low =
            Number(candle.low);

        const close =
            Number(candle.close);


        // ======================================
        // VALIDATE TIMESTAMP
        // ======================================

        if (
            !Number.isFinite(
                incomingTime
            )
        )
        {
            jsInvalidUpdateCount++;

            return "INVALID_TIME";
        }


        // ======================================
        // VALIDATE OHLC
        // ======================================

        if (
            !Number.isFinite(open) ||
            !Number.isFinite(high) ||
            !Number.isFinite(low) ||
            !Number.isFinite(close)
        )
        {
            jsInvalidUpdateCount++;

            return "INVALID_OHLC";
        }


        // ======================================
        // TIMESTAMP NORMALIZATION
        //
        // Defensive protection:
        //
        // If Python accidentally sends milliseconds,
        // convert them to seconds.
        // ======================================

        if (
            incomingTime >
            10000000000
        )
        {
            incomingTime =
                Math.floor(
                    incomingTime / 1000
                );
        }


        // ======================================
        // STALE PROTECTION
        //
        // IMPORTANT:
        //
        // Same timestamp = VALID.
        //
        // It means the current candle is changing.
        //
        // Older timestamp = reject.
        // ======================================

        if (
            jsLastCandleTime !== null &&
            incomingTime <
            jsLastCandleTime
        )
        {
            jsRejectedStaleCount++;

            return "STALE";
        }


        // ======================================
        // BUILD CANDLE
        // ======================================

        const liveCandle = {

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


        // ======================================
        // UPDATE LIGHTWEIGHT CHARTS
        //
        // Same timestamp:
        //     update current candle
        //
        // New timestamp:
        //     create next candle
        // ======================================

        candleSeries.update(
            liveCandle
        );


        // ======================================
        // REGISTER LATEST TIMESTAMP
        // ======================================

        jsLastCandleTime =
            incomingTime;


        jsLiveUpdateCount++;


        // ======================================
        // LIGHT DEBUG
        //
        // Do not print every update.
        //
        // Print every 10th successful update.
        // ======================================

        if (
            jsLiveUpdateCount % 10 === 0
        )
        {
            console.log(
                "[CHART LIVE]",
                "updates:",
                jsLiveUpdateCount,
                "time:",
                incomingTime,
                "close:",
                close
            );
        }


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
            return "INVALID_SIGNAL";
        }


        const signalTime =
            Number(signal.time);


        if (
            !Number.isFinite(
                signalTime
            )
        )
        {
            return "INVALID_TIME";
        }


        const direction =
            String(
                signal.direction || ""
            ).toUpperCase();


        if (
            direction !== "BUY" &&
            direction !== "SELL"
        )
        {
            return "INVALID_DIRECTION";
        }


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


        // ======================================
        // SORT
        // ======================================

        tradeMarkers.sort(
            (a, b) =>
                a.time - b.time
        );


        // ======================================
        // UPDATE MARKERS
        // ======================================

        markerPlugin.setMarkers(
            tradeMarkers
        );


        return "SIGNAL_SHOWN";
    }
    catch(error)
    {
        console.error(
            "Trade overlay error:",
            error
        );

        return "ERROR";
    }
};


// ==========================================
// CHART RESIZE
// ==========================================
//
// autoSize is intentionally FALSE.
//
// Explicit resize is handled here.
//

function resizeChart()
{
    try
    {
        const container =
            document.getElementById(
                "chart"
            );

        if (!container)
        {
            return;
        }


        const width =
            container.clientWidth;

        const height =
            container.clientHeight;


        if (
            width <= 0 ||
            height <= 0
        )
        {
            return;
        }


        chart.applyOptions({

            width:
                width,

            height:
                height
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


// ==========================================
// WINDOW RESIZE
// ==========================================

window.addEventListener(
    "resize",
    resizeChart
);


// ==========================================
// RESIZE OBSERVER
// ==========================================
//
// Useful inside QWebEngineView because the
// actual chart container can resize without
// a normal browser window resize.
//

if (
    typeof ResizeObserver !==
    "undefined"
)
{
    const chartContainer =
        document.getElementById(
            "chart"
        );

    if (chartContainer)
    {
        const resizeObserver =
            new ResizeObserver(
                () =>
                {
                    resizeChart();
                }
            );

        resizeObserver.observe(
            chartContainer
        );
    }
}


// ==========================================
// INITIAL RESIZE
// ==========================================

setTimeout(
    () =>
    {
        resizeChart();
    },
    100
);


// ==========================================
// DEBUG STATUS
// ==========================================

window.getChartSyncStatus = function()
{
    return {

        historicalLoaded:
            jsHistoricalLoaded,

        lastCandleTime:
            jsLastCandleTime,

        liveUpdateCount:
            jsLiveUpdateCount,

        rejectedStaleCount:
            jsRejectedStaleCount,

        invalidUpdateCount:
            jsInvalidUpdateCount
    };
};


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
    "Same timestamp     : ACCEPTED"
);

console.log(
    "Stale protection   : ENABLED"
);

console.log(
    "Chart reset        : PROTECTED"
);

console.log(
    "AutoSize           : DISABLED"
);

console.log(
    "Explicit resize    : ENABLED"
);

console.log(
    "ResizeObserver     : ENABLED"
);

console.log(
    "GUI throttle       : Controller/Widget"
);