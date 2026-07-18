from data.market_data import MarketData
from indicators.choch_v2 import CHoCHV2

print("=" * 50)
print("      CHoCH V2 TEST")
print("=" * 50)

# Load Market Data
market = MarketData("^NSEI")
data = market.load_data("5m")

# Initialize Engine
engine = CHoCHV2()

# Run Detection
result = engine.detect(data)

# Print Result
print("\n========== CHoCH V2 RESULT ==========")

for key, value in result.items():
    print(f"{key} : {value}")

print("=" * 50)
print("TEST COMPLETED")
print("=" * 50)