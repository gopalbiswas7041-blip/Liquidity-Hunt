from datetime import datetime


class CandleSync:
    """
    Smart candle synchronization engine.

    Keeps track of the latest candle timestamp
    for every timeframe independently.
    """

    def __init__(self):

        self.last_candle = {}

    def is_new_candle(self, timeframe, data):

        if data is None or data.empty:
            return False

        latest = data.index[-1]

        if isinstance(latest, str):
            latest = datetime.fromisoformat(latest)

        previous = self.last_candle.get(timeframe)

        if previous is None:
            self.last_candle[timeframe] = latest
            return True

        if latest > previous:
            self.last_candle[timeframe] = latest
            return True

        return False

    def reset(self):

        self.last_candle.clear()