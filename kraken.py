import krakenex
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import pandas_ta as ta
import os
import time

from pykrakenapi import KrakenAPI


def get_prices(interval, short_ema, long_ema):
    """
    Return a ``pd.DataFrame`` of the OHLC data for a given pair and time interval (minutes). Also calculates the two
        EMAs for crossing over
    :param interval:
    :param short_ema:
    :param long_ema:
    :return:
    """
    ohlc, last = k.get_ohlc_data("XDGUSD", interval=interval)
    ohlc = ohlc.sort_index()  # Sort by ascending dates for EMA
    ema10_ohlc4 = ta.ema(ta.ohlc4(ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"]), length=short_ema)
    ema21_ohlc4 = ta.ema(ta.ohlc4(ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"]), length=long_ema)
    ohlc = ohlc.join(ema10_ohlc4)
    ohlc: pd.DataFrame = ohlc.join(ema21_ohlc4)
    ohlc = ohlc.sort_index(ascending=False)
    return ohlc


def plot_graph(ohlc):
    sns.set()
    plt.figure(figsize=(10, 7))
    ohlc = ohlc.iloc[0:100]
    ohlc[['EMA_10', 'EMA_21', 'close']].plot()
    plt.legend()
    plt.show()


def check_ema(ohlc):
    """
    return 1 for buy signal when EMA_10 crosses above EMA_21, -1 for sell signal, 0 for doing nothing
    :param ohlc:
    :return:
    """
    if ohlc.EMA_10[0] > ohlc.EMA_21[0]:
        return 1
    if ohlc.EMA_10[0] < ohlc.EMA_21[0]:
        return -1
    return 0


def buy_doge(volume):
    return k.add_standard_order(pair="XDGUSD", type="buy", ordertype="market", volume=volume, validate=False)


def sell_doge(volume):
    return k.add_standard_order(pair="XDGUSD", type="sell", ordertype="market", volume=volume, validate=False)


if __name__ == '__main__':
    # =============================== Constants ===============================
    INTERVAL = 5
    SHORT_EMA = 5
    LONG_EMA = 50
    keyfilepath = os.path.join(os.path.expanduser('~'), "Documents/kraken_credentials.txt")
    logfilepath = os.path.join(os.path.expanduser('~'), "Documents/kraken_log.txt")

    # =============================== Main program =================================

    with open(keyfilepath, 'r') as keyfile:
        key = keyfile.readline().strip('\n')
        b64secret = keyfile.readline().strip('\n')

    api = krakenex.API(key=key, secret=b64secret)
    k = KrakenAPI(api)

    short_ema_column = "EMA_" + str(SHORT_EMA)
    long_ema_column = "EMA_" + str(LONG_EMA)

    last_ohlc = get_prices(INTERVAL, SHORT_EMA, LONG_EMA)
    last_ema = last_ohlc[short_ema_column][0] > last_ohlc[long_ema_column][0]  # Record if EMA_10 is above EMA_21 or not

    print("Starting trading algorithm with interval = {interval} Short EMA = {short_EMA} Long EMA = {long_EMA}"
          .format(interval=INTERVAL, short_EMA=SHORT_EMA, long_EMA=LONG_EMA))
    with open(logfilepath, 'a+') as logfile:
        logfile.write(
            "Starting trading algorithm with interval = {interval} Short EMA = {short_EMA} Long EMA = {long_EMA}"
            .format(interval=INTERVAL, short_EMA=SHORT_EMA, long_EMA=LONG_EMA))
        logfile.write("\n")

    while True:
        time.sleep(55)
        ohlc = get_prices(INTERVAL, SHORT_EMA, LONG_EMA)
        new_ema = ohlc[short_ema_column][0] > ohlc[long_ema_column][0]
        # Check if prices are updated. If not do not do anything
        out = ""
        action = False
        if new_ema != last_ema:
            print(">> Detected EMA crossover")
            action = True
            last_ema = new_ema

            if new_ema:
                out = buy_doge(50)
            elif not new_ema:
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
