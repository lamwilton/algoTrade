import krakenex
import pandas as pd
import pandas_ta as ta
import os
import time

from pykrakenapi import KrakenAPI
from pykrakenapi.pykrakenapi import KrakenAPIError


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


def buy_coin(pair, volume):
    return k.add_standard_order(pair=pair, type="buy", ordertype="market", volume=volume, validate=False)


def sell_coin(pair, volume):
    try:
        out = k.add_standard_order(pair=pair, type="sell", ordertype="market", volume=volume, validate=False)
        return out
    except KrakenAPIError:
        print("Insufficient funds, order cancelled")
        return None


if __name__ == '__main__':
    # =============================== Constants ===============================
    INTERVAL = 1440
    FAST = 12
    SLOW = 26
    SIGNAL = 9
    SMA = 18
    keyfilepath = os.path.join(os.path.expanduser('~'), "Documents/kraken_credentials.txt")
    logfilepath = os.path.join(os.path.expanduser('~'), "Documents/kraken_daily_log.txt")

    # =============================== Main program =================================

    with open(keyfilepath, 'r') as keyfile:
        key = keyfile.readline().strip('\n')
        b64secret = keyfile.readline().strip('\n')

    api = krakenex.API(key=key, secret=b64secret)
    k = KrakenAPI(api)

    print("Starting daily MACD trading algorithm with interval = {interval} fast={fast} slow={slow} signal={signal}"
          .format(interval=INTERVAL, fast=FAST, slow=SLOW, signal=SIGNAL))
    with open(logfilepath, 'a+') as logfile:
        logfile.write(
            "Starting daily MACD trading algorithm with interval = {interval} fast={fast} slow={slow} signal={signal}"
            .format(interval=INTERVAL, fast=FAST, slow=SLOW, signal=SIGNAL))
        logfile.write("\n")

    pair_list = [("XBTUSD", 0.0002), ("ETHUSD", 0.005), ("LTCUSD", 0.05), ("BCHUSD", 0.05), ("EOSUSD", 2.5),
                 ("XDGUSD", 100)]  # List of cryptos and trade volumes

    for pair in pair_list:
        time.sleep(10)
        macd_col = "MACDh_" + str(FAST) + "_" + str(SLOW) + "_" + str(SIGNAL)
        sma_col = "SMA_{}".format(SMA)
        ohlc = get_prices(pair[0], INTERVAL, FAST, SLOW, SIGNAL)
        new_macd = ohlc[macd_col][0] > 0
        last_macd = ohlc[macd_col][1] > 0
        sma = ohlc["high"][0] > ohlc[sma_col][0]

        # Check if prices are updated. If not do not do anything
        out = ""
        action = False
        if new_macd != last_macd and sma:
            print(">> Detected MACD signal as well as stock price is above SMA")
            action = True

            if new_macd:
                out = buy_coin(pair[0], pair[1])
            elif not new_macd:
                out = sell_coin(pair[0], pair[1])

        with open(logfilepath, 'a+') as logfile:
            curr_time = str(k.get_server_time()[0].astimezone("US/Pacific"))

            if action and out is not None:
                logfile.write("[" + curr_time + "] " + out['descr']['order'] + " Txid: " + out['txid'][0])
                logfile.write("\n")
                print("[" + curr_time + "] " + out['descr']['order'] + " Txid: " + out['txid'][0])

                out = k.get_closed_orders()
                logfile.write(str(out[0].iloc[0]))
                print(str(out[0].iloc[0]))
                logfile.write("\n")
            else:
                logfile.write("[" + curr_time + "] {} No action taken".format(pair[0]))
                logfile.write("\n")
                print("[" + curr_time + "] {} No action taken".format(pair[0]))
