class FairValueGap:

    def __init__(self):
        print("Fair Value Gap Engine Initialized")

    def detect(self, data):
        print("Checking Fair Value Gaps...")

        fvg_list = []

        for i in range(2, len(data)):

            c1 = data.iloc[i - 2]
            c2 = data.iloc[i - 1]
            c3 = data.iloc[i]

            # Bullish FVG
            if c1["High"] < c3["Low"]:

                fvg_list.append({
                    "type": "Bullish FVG",
                    "top": float(c3["Low"]),
                    "bottom": float(c1["High"]),
                    "index": i,
                    "time": str(data.index[i])
                })

            # Bearish FVG
            elif c1["Low"] > c3["High"]:

                fvg_list.append({
                    "type": "Bearish FVG",
                    "top": float(c1["Low"]),
                    "bottom": float(c3["High"]),
                    "index": i,
                    "time": str(data.index[i])
                })

        print("FVG Found :", len(fvg_list))

        return fvg_list