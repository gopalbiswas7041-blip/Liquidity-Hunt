from data.market_data import MarketData
from strategy.signal_engine import SignalEngine
from strategy.trade_manager import TradeManager
from indicators.atr import ATR

print("=" * 50)
print("      LIQUIDITY HUNTER AI V12")
print("=" * 50)

# -----------------------------------
# Market Data Engine
# -----------------------------------

market = MarketData("^NSEI")

print("\n========== LOADING 5 MIN DATA ==========")
data_5m = market.load_data("5m")

print("\n========== LOADING 15 MIN DATA ==========")
data_15m = market.load_data("15m")

# -----------------------------------
# ATR (5m)
# -----------------------------------

atr = ATR()

atr_data = atr.calculate(data_5m)
volatility = atr.get_volatility(data_5m)

print("\n========== ATR ==========")
print(atr_data[["Close", "ATR"]].tail())

print("\n========== MARKET VOLATILITY ==========")
print(f"Market Volatility : {volatility}")

# -----------------------------------
# Signal Engine
# -----------------------------------

engine = SignalEngine()

# এখন 5m এবং 15m দুটোই পাঠানো হচ্ছে
result = engine.generate_signal(
    data_5m,
    data_15m
)

# -----------------------------------
# Trade Manager
# -----------------------------------

trade_manager = TradeManager()
trade = trade_manager.generate_trade(result, data_5m)

# -----------------------------------
# Final Signal
# -----------------------------------

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

# -----------------------------------
# Trade Plan
# -----------------------------------

print("\n========== TRADE PLAN ==========")

print(f"Volatility : {trade['volatility']}")

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
print("V12 RUN COMPLETED")
print("=" * 50)