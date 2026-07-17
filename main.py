from data.market_data import MarketData
from indicators.liquidity_sweep import LiquiditySweep

print("=" * 40)
print("Liquidity Hunter AI v1 Started")
print("=" * 40)

market = MarketData("^NSEI", "5m")

data = market.load_data()

sweep = LiquiditySweep()

signals = sweep.detect(data)

print(signals)