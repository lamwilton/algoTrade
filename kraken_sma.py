import krakenex
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import pandas_ta as ta
import os
import time

from pykrakenapi import KrakenAPI


def get_prices(interval, fast, slow):
    """
    Return a ``pd.DataFrame`` of the OHLC data for a given pair and time interval (minutes) and the indicators
    :param slow:
    :param fast:
    :param interval:
    :return: OHLC dataframe with SMA
    """
    ohlc, last = k.get_ohlc_data("XBTUSD", interval=interval)
    ohlc = ohlc.sort_index()  # Sort by ascending dates for EMA
    _ = ohlc.ta.sma(length=fast, min_periods=None, append=True)
    _ = ohlc.ta.sma(length=slow, min_periods=None, append=True)
    ohlc = ohlc.sort_index(ascending=False)
    return ohlc


def plot_graph(ohlc):
    sns.set()
    plt.figure(figsize=(10, 7))
    ohlc = ohlc.iloc[0:100]
    ohlc[['MACDh_12_26_9']].plot()
    plt.legend()
    plt.show()


def buy_coin(volume):
    return k.add_standard_order(pair="XBTUSD", type="buy", ordertype="market", volume=volume, validate=False)


def sell_coin(volume):
    return k.add_standard_order(pair="XBTUSD", type="sell", ordertype="market", volume=volume, validate=False)


if __name__ == '__main__':
    """
    // The strategy goes long when the faster SMA 50 (the
    // simple moving average of the last 50 bars) crosses
    // above the SMA 200. Orders are closed when the SMA 50
    // crosses below SMA 200. The strategy does not short.
    """
    # =============================== Constants ===============================
    INTERVAL = 30
    FAST = 50
    SLOW = 200
    VOLUME = 0.0002
    keyfilepath = os.path.join(os.path.expanduser('~'), "Documents/kraken_credentials.txt")
    logfilepath = os.path.join(os.path.expanduser('~'), "Documents/kraken_log.txt")

    # =============================== Main program =================================

    with open(keyfilepath, 'r') as keyfile:
        key = keyfile.readline().strip('\n')
        b64secret = keyfile.readline().strip('\n')

    api = krakenex.API(key=key, secret=b64secret)
    k = KrakenAPI(api)

    fast_col = "SMA_{}".format(FAST)
    slow_col = "SMA_{}".format(SLOW)
    last_ohlc = get_prices(INTERVAL, FAST, SLOW)
    last_sma = last_ohlc[fast_col][0] > last_ohlc[slow_col][0]
    last_time = last_ohlc['time'][0]

    print("Starting SMA trading algorithm with interval={interval} fast={fast} slow={slow}"
          .format(interval=INTERVAL, fast=FAST, slow=SLOW))
    with open(logfilepath, 'a+') as logfile:
        logfile.write(
            "Starting SMA trading algorithm with interval={interval} fast={fast} slow={slow}"
            .format(interval=INTERVAL, fast=FAST, slow=SLOW))
        logfile.write("\n")

    while True:
        time.sleep(55)
        ohlc = get_prices(INTERVAL, FAST, SLOW)
        new_sma = ohlc[fast_col][0] > ohlc[slow_col][0]
        new_time = ohlc["time"][0]

        # Check if prices are updated. If not do not do anything
        out = ""
        action = False

        # Action if both SMA crosses
        if new_sma != last_sma and new_time != last_time:
            print(">> Detected SMA crossing")
            action = True
            last_sma = new_sma
            last_time = new_time

            if new_sma:
                out = buy_coin(VOLUME)
            elif not new_sma:
                out = sell_coin(VOLUME)

        with open(logfilepath, 'a+') as logfile:
            curr_time = str(k.get_server_time()[0].astimezone("US/Pacific"))

            if action:
                logfile.write("[" + curr_time + "] " + out['descr']['order'] + " Txid: " + out['txid'][0])
                logfile.write("\n")
                print("[" + curr_time + "] " + out['descr']['order'] + " Txid: " + out['txid'][0])

                out = k.get_closed_orders()
                logfile.write(str(out[0].iloc[0]))
                print(str(out[0].iloc[0]))
                logfile.write("\n")
            else:
                logfile.write("[" + curr_time + "] No action taken")
                logfile.write("\n")
                print("[" + curr_time + "] No action taken")
