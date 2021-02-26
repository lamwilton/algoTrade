import krakenex
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import pandas_ta as ta
import os
import time

from pykrakenapi import KrakenAPI


def get_prices():
    ohlc, last = k.get_ohlc_data("XDGUSD", interval=60)
    ema10_ohlc4 = ta.ema(ta.ohlc4(ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"]), length=10)
    ema21_ohlc4 = ta.ema(ta.ohlc4(ohlc["open"], ohlc["high"], ohlc["low"], ohlc["close"]), length=21)
    ohlc = ohlc.join(ema10_ohlc4)
    ohlc: pd.DataFrame = ohlc.join(ema21_ohlc4)
    ohlc.EMA_10 = ohlc.EMA_10.shift(-10)
    ohlc.EMA_21 = ohlc.EMA_21.shift(-21)
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
    if ohlc.EMA_10[0] > ohlc.EMA_21[0] and ohlc.EMA_10[1] <= ohlc.EMA_21[1]:
        return 1
    if ohlc.EMA_10[0] < ohlc.EMA_21[0] and ohlc.EMA_10[1] >= ohlc.EMA_21[1]:
        return -1
    return 0


def buy_doge(volume):
    return k.add_standard_order(pair="XDGUSD", type="buy", ordertype="market", volume=volume, validate=False)


def sell_doge(volume):
    return k.add_standard_order(pair="XDGUSD", type="sell", ordertype="market", volume=volume, validate=False)


if __name__ == '__main__':
    keyfilepath = os.path.join(os.path.expanduser('~'), "Documents/kraken_credentials.txt")

    with open(keyfilepath, 'r') as keyfile:
        key = keyfile.readline().strip('\n')
        b64secret = keyfile.readline().strip('\n')

    api = krakenex.API(key=key, secret=b64secret)
    k = KrakenAPI(api)
    print()
    while True:
        time.sleep(50)
        ohlc = get_prices()
        buy = check_ema(ohlc)

        acc_balance = k.get_account_balance()

        out = ""
        if buy == 1:
            out = buy_doge(50)
        elif buy == -1:
            out = sell_doge(50)

        logfilepath = os.path.join(os.path.expanduser('~'), "Documents/kraken_log.txt")
        with open(logfilepath, 'a+') as logfile:
            logfile.write(str(k.get_server_time()[0].astimezone("US/Pacific")))
            logfile.write("\n")
            print(str(k.get_server_time()[0].astimezone("US/Pacific")))
            logfile.write(str(acc_balance))
            logfile.write("\n")
            print(str(acc_balance))

            if buy == 1 or buy == -1:
                logfile.write(out['descr']['order'] + " Txid: " + out['txid'][0])
                logfile.write("\n")
                print(out['descr']['order'] + " Txid: " + out['txid'][0])

                out = k.get_closed_orders()
                logfile.write(str(out[0].iloc[0]))
                print(str(out[0].iloc[0]))
                logfile.write("\n")

