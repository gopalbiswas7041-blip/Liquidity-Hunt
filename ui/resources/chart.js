// ==========================================
// Liquidity Hunter AI V18
// chart.js
// ==========================================

console.log("Liquidity Hunter Chart Loaded");

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

// Candlestick Series
const candleSeries = chart.addSeries(
    LightweightCharts.CandlestickSeries,
    {}
);

// Python → JavaScript
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

// Live Update
window.updateLastCandle = function(candle)
{
    try
    {
        candleSeries.update(candle);
    }
    catch(err)
    {
        console.error(err);
    }
};

// Resize
window.addEventListener("resize", () =>
{
    chart.applyOptions({

        width: window.innerWidth,

        height: window.innerHeight

    });
});

console.log("Chart Ready");