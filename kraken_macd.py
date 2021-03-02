import krakenex
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import pandas_ta as ta
import os
import time

from pykrakenapi import KrakenAPI


def get_prices(interval, fast, slow, signal, sma):
    """
    Return a ``pd.DataFrame`` of the OHLC data for a given pair and time interval (minutes) and the indicators
    :param sma: period of Simple Moving Average
    :param signal:
    :param slow:
    :param fast:
    :param interval:
    :return: OHLC dataframe with MACD and SMA
    """
    ohlc, last = k.get_ohlc_data("XDGUSD", interval=interval)
    ohlc = ohlc.sort_index()  # Sort by ascending dates for EMA
    _ = ohlc.ta.macd(fast=fast, slow=slow, signal=signal, min_periods=None, append=True)
    _ = ohlc.ta.sma(length=sma, min_periods=None, append=True)
    ohlc = ohlc.sort_index(ascending=False)
    return ohlc


def plot_graph(ohlc):
    sns.set()
    plt.figure(figsize=(10, 7))
    ohlc = ohlc.iloc[0:100]
    ohlc[['MACDh_12_26_9']].plot()
    plt.legend()
    plt.show()


def buy_doge(volume):
    return k.add_standard_order(pair="XDGUSD", type="buy", ordertype="market", volume=volume, validate=False)


def sell_doge(volume):
    return k.add_standard_order(pair="XDGUSD", type="sell", ordertype="market", volume=volume, validate=False)


if __name__ == '__main__':
    # =============================== Constants ===============================
    INTERVAL = 30
    FAST = 12
    SLOW = 26
    SIGNAL = 9
    SMA = 18
    keyfilepath = os.path.join(os.path.expanduser('~'), "Documents/kraken_credentials.txt")
    logfilepath = os.path.join(os.path.expanduser('~'), "Documents/kraken_log.txt")

    # =============================== Main program =================================

    with open(keyfilepath, 'r') as keyfile:
        key = keyfile.readline().strip('\n')
        b64secret = keyfile.readline().strip('\n')

    api = krakenex.API(key=key, secret=b64secret)
    k = KrakenAPI(api)

    macd_col = "MACDh_" + str(FAST) + "_" + str(SLOW) + "_" + str(SIGNAL)
    sma_col = "SMA_{}".format(SMA)
    last_ohlc = get_prices(INTERVAL, FAST, SLOW, SIGNAL, SMA)
    last_macd = last_ohlc[macd_col][0] > 0

    print("Starting MACD trading algorithm with interval = {interval} fast={fast} slow={slow} signal={signal}"
          .format(interval=INTERVAL, fast=FAST, slow=SLOW, signal=SIGNAL))
    with open(logfilepath, 'a+') as logfile:
        logfile.write(
            "Starting MACD trading algorithm with interval = {interval} fast={fast} slow={slow} signal={signal}"
            .format(interval=INTERVAL, fast=FAST, slow=SLOW, signal=SIGNAL))
        logfile.write("\n")

    while True:
        time.sleep(55)
        ohlc = get_prices(INTERVAL, FAST, SLOW, SIGNAL, SMA)
        new_macd = ohlc[macd_col][0] > 0
        sma = ohlc["high"][0] > ohlc[sma_col][0]
        # Check if prices are updated. If not do not do anything
        out = ""
        action = False

        # Action only if MACD changes sign as well as stock price is above SMA
        if new_macd != last_macd and sma:
            print(">> Detected MACD signal as well as stock price is above SMA")
            action = True
            last_macd = new_macd

            if new_macd:
                out = buy_doge(50)
            elif not new_macd:
                out = sell_doge(50)

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
