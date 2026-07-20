import requests

url = "https://public.coindcx.com/market_data/candles"

for interval in [
    "1m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h"
]:
    response = requests.get(
        url,
        params={
            "pair": "B-BTC_USDT",
            "interval": interval,
            "limit": 2
        }
    )

    print(interval, "->", response.status_code)