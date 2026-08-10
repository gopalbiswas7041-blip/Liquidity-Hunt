// ==========================================
// Liquidity Hunter AI V20
// chart.js
// ==========================================

alert("NEW chart.js loaded");

console.log("Liquidity Hunter Chart Loaded");
console.log("LightweightCharts =", LightweightCharts);
console.log("Version =", LightweightCharts.version);

alert("Version = " + LightweightCharts.version);

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
            mode: LightweightCharts.CrosshairMode.Normal
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

const tradeMarkers = [];

const markerPlugin =
    LightweightCharts.createSeriesMarkers(
        candleSeries,
        []
    );

// ==========================================
// Historical Data
// ==========================================

window.setChartData = function(candles)
{
    try
    {
        console.log("Received candles :", candles.length);

        candleSeries.setData(candles);

        chart.timeScale().fitContent();
    }
    catch(err)
    {
        console.error(err);
    }
};

// ==========================================
// Live Candle Update
// ==========================================

let jsLastCandleTime = null;

window.updateLastCandle = function(candle)
{
    console.log("=================================");
    console.log("JS updateLastCandle CALLED");
    console.log("Incoming candle =", candle);

    try
    {
        const incomingTime = Number(candle.time);

        console.log(
            "JS Last Candle Time =",
            jsLastCandleTime
        );

        console.log(
            "JS Incoming Time =",
            incomingTime
        );

        console.log(
            "JS Time Type =",
            typeof candle.time
        );

        // ------------------------------------------
        // Basic validation
        // ------------------------------------------

        if (!Number.isFinite(incomingTime))
        {
            console.error(
                "❌ INVALID CANDLE TIME"
            );

            return "INVALID_TIME";
        }

        if (
            !Number.isFinite(Number(candle.open)) ||
            !Number.isFinite(Number(candle.high)) ||
            !Number.isFinite(Number(candle.low)) ||
            !Number.isFinite(Number(candle.close))
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
            time: incomingTime,
            open: Number(candle.open),
            high: Number(candle.high),
            low: Number(candle.low),
            close: Number(candle.close)
        };

        console.log(
            "Normalized Candle =",
            normalizedCandle
        );

        // ------------------------------------------
        // OLD CANDLE
        // ------------------------------------------

        if (
            jsLastCandleTime !== null &&
            incomingTime < jsLastCandleTime
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

        // ------------------------------------------
        // UPDATE CHART
        // ------------------------------------------

        candleSeries.update(
            normalizedCandle
        );

        // ------------------------------------------
        // Register latest timestamp
        // ------------------------------------------

        jsLastCandleTime = incomingTime;

        console.log(
            "✅ UPDATE SUCCESS"
        );

        console.log(
            "JS Latest Candle Time =",
            jsLastCandleTime
        );

        console.log("=================================");

        return "UPDATED";

    }
    catch(err)
    {
        console.error(
            "❌ UPDATE FAILED"
        );

        console.error(err);

        console.log("=================================");

        return "ERROR";
    }
};

// ==========================================
// AI Trade Signal Overlay
// ==========================================

window.showTradeSignal = function(signal)
{
    try
    {
        console.log("AI SIGNAL RECEIVED");
        console.log(signal);

        tradeMarkers.push({

            time: signal.time,

            position:
                signal.direction === "BUY"
                ? "belowBar"
                : "aboveBar",

            color:
                signal.direction === "BUY"
                ? "#00FF00"
                : "#FF0000",

            shape:
                signal.direction === "BUY"
                ? "arrowUp"
                : "arrowDown",

            text: signal.direction

        });

        markerPlugin.setMarkers(tradeMarkers);

        console.log("Signal Marker Added");
    }
    catch(err)
    {
        console.error("Overlay Error");
        console.error(err);
    }
};

// ==========================================
// Resize
// ==========================================

window.addEventListener("resize", () =>
{
    chart.applyOptions({
        width: window.innerWidth,
        height: window.innerHeight
    });
});

console.log("Chart Ready");