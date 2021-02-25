import krakenex
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import pandas_ta as ta

from pykrakenapi import KrakenAPI


api = krakenex.API()
k = KrakenAPI(api)
ohlc, last = k.get_ohlc_data("XDGUSD", interval=60)

ema10_ohlc4 = ta.ema(ta.ohlc4(ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"]), length=10)
ema21_ohlc4 = ta.ema(ta.ohlc4(ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"]), length=21)
ohlc = ohlc.join(ema10_ohlc4)
ohlc: pd.DataFrame = ohlc.join(ema21_ohlc4)
ohlc.EMA_10 = ohlc.EMA_10.shift(-10)
ohlc.EMA_21 = ohlc.EMA_21.shift(-21)


sns.set()
plt.figure(figsize=(10, 7))
ohlc = ohlc.iloc[0:100]
ohlc[['EMA_10', 'EMA_21', 'close']].plot()
#plt.plot(ohlc.close)
plt.legend()
plt.show()


print(ohlc)