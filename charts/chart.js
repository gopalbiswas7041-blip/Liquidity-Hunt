// ===========================================
// Liquidity Hunter AI
// TradingView Lightweight Chart
// V17.1
// ===========================================

console.log("chart.js loaded");

if (typeof LightweightCharts === "undefined") {
    console.error("LightweightCharts library not loaded.");
} else {

    const chart = LightweightCharts.createChart(
        document.getElementById("chart"),
        {
            width: window.innerWidth,
            height: window.innerHeight,

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
                    color: "#2B2B43"
                }
            },

            rightPriceScale: {
                borderColor: "#444"
            },

            timeScale: {
                borderColor: "#444",
                timeVisible: true,
                secondsVisible: false
            }
        }
    );

    const candleSeries = chart.addCandlestickSeries();

    candleSeries.setData([
        {
            time: "2026-07-22",
            open: 100,
            high: 110,
            low: 95,
            close: 108
        },
        {
            time: "2026-07-23",
            open: 108,
            high: 115,
            low: 105,
            close: 112
        },
        {
            time: "2026-07-24",
            open: 112,
            high: 118,
            low: 109,
            close: 111
        },
        {
            time: "2026-07-25",
            open: 111,
            high: 120,
            low: 108,
            close: 119
        }
    ]);

    window.addEventListener("resize", () => {
        chart.applyOptions({
            width: window.innerWidth,
            height: window.innerHeight
        });
    });

    console.log("Chart created successfully");
}