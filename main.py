from data.market_data import MarketData
from strategy.signal_engine import SignalEngine
from strategy.trade_manager import TradeManager

print("=" * 50)
print("      LIQUIDITY HUNTER AI V10.4")
print("=" * 50)

# Load Market Data
market = MarketData("^NSEI", "5m")
data = market.load_data()

# Generate Trading Signal
engine = SignalEngine()
result = engine.generate_signal(data)

# Generate Trade Plan
trade_manager = TradeManager()
trade = trade_manager.generate_trade(result, data)

print("\n========== FINAL SIGNAL ==========")

print(f"Signal      : {result['signal']}")
print(f"Confidence  : {result['confidence']}%")
print(f"Quality     : {result['quality']}")
print(f"Status      : {result['status']}")

print("\nReasons:")

if result["reasons"]:
    for reason in result["reasons"]:
        print(f"  ✔️ {reason}")
else:
    print("  None")

print("\n========== TRADE PLAN ==========")

if trade["entry"] is not None:
    print(f"Entry Price : {trade['entry']:.2f}")
else:
    print("Entry Price : None")

if trade["stop_loss"] is not None:
    print(f"Stop Loss   : {trade['stop_loss']:.2f}")
else:
    print("Stop Loss   : None")

if trade["take_profit"] is not None:
    print(f"Take Profit : {trade['take_profit']:.2f}")
else:
    print("Take Profit : None")

if trade["risk"] is not None:
    print(f"Risk        : {trade['risk']:.2f}")
else:
    print("Risk        : None")

if trade["reward"] is not None:
    print(f"Reward      : {trade['reward']:.2f}")
else:
    print("Reward      : None")

if trade["risk_reward"] is not None:
    print(f"Risk Reward : 1 : {trade['risk_reward']}")
else:
    print("Risk Reward : None")

print("=" * 50)
print("V10.4 RUN COMPLETED")
print("=" * 50)