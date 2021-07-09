import requests
#import datetime
from datetime import datetime, timedelta
from binance.client import Client
import pandas as pd
import matplotlib.pyplot as plt
import smtplib, ssl
from constants import *

import logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("crypto")
from twilio.rest import Client as twilioClient

"""
todo
1 support different kinds of coin/currency types
2 make function modular
3 not only compare 30 days moving average, consider 15 days, 45 days, 60days
4 run with a cron job with docker/windows
5 not only compare the average price vs current price, but consider current price as a -2% to +2% range


"""


"""
[
  [
    1499040000000,      // Open time
    "0.01634790",       // Open
    "0.80000000",       // High
    "0.01575800",       // Low
    "0.01577100",       // Close
    "148976.11427815",  // Volume
    1499644799999,      // Close time
    "2434.19055334",    // Quote asset volume
    308,                // Number of trades
    "1756.87402397",    // Taker buy base asset volume
    "28.46694368",      // Taker buy quote asset volume
    "17928899.62484339" // Ignore.
  ]
]
"""

class CryptoUtil(object):
    def __init__(self):
        self.client = Client(API_KEY, API_SECRET)
        self.messages = []
        self.send_email = False
        self.twilioClient = twilioClient("", "")


    def get_crypto_current_price(self, symbol):
        price = self.client.get_symbol_ticker(symbol=symbol)['price']
        return price

    def get_kline_row_data(self, symbol, interval="1hr"):
        today = datetime.now().strftime("%B %d, %Y")
        days_ago = (datetime.now() - timedelta(days=KLINE_DAYS)).strftime("%B %d, %Y")
        bars = None
        if interval == "1hr":
            bars = self.client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1HOUR, days_ago, today, limit=1000)
        return bars

    def calculate_moving_average(self, bars, interval="1hr"):
        new_bars = []
        for bar in bars:
            new_bar = []
            new_bar.append(str(datetime.fromtimestamp(bar[0] / 1000)))
            new_bar.append(bar[4])
            new_bars.append(new_bar)
        crypto_df = pd.DataFrame(new_bars, columns=['date', 'close'])
        if interval == "1hr":
            crypto_df['7MA'] = crypto_df.close.rolling(168).mean()
            crypto_df['15MA'] = crypto_df.close.rolling(360).mean()
            crypto_df['30MA'] = crypto_df.close.rolling(720).mean()
            crypto_df['45MA'] = crypto_df.close.rolling(1080).mean()
        return crypto_df

    def compare_prices(self, symbol, price, crypto_df):
        for ma_range in ["7MA", "15MA", "30MA", "45MA"]:
            self.compare_price(symbol, price, crypto_df, ma_range)

    def compare_price(self, symbol, price, crypto_df, ma_range):
        moving_average_price = str(crypto_df[ma_range].iloc[-1])
        if float(price) < float(moving_average_price):
            message = "cur {} price: {} is less than latest {} " \
                      "price {}".format(symbol, price, ma_range, moving_average_price)
            log.info(message)
            self.messages.append(message)
            self.send_email = True
        else:
            message = "cur {} price: {} is greater than latest {} " \
                      "price {}".format(symbol, price, ma_range, moving_average_price)
            log.info(message)
            self.messages.append(message)

        #crypto_df = crypto_df.astype({'close': float})
        #crypto_df.plot.line(x='date')
        #plt.show()

    def send_email_to_user(self):
        if self.send_email:
            port = 587  # For starttls
            smtp_server = "smtp.gmail.com"
            sender_email = ""  # Enter your address
            receiver_email = ""  # Enter receiver address
            email_password = ""
            header = 'To:' + receiver_email + '\n' + 'From: ' + sender_email + '\n' + 'Subject:crypto price update from pw\n'
            sorted_message1 = []
            sorted_message2 = []
            for message in self.messages:
                if "less than" in message:
                    sorted_message1.append(message)
                else:
                    sorted_message2.append(message)
            sorted_message = "\n\n\n".join(sorted_message1) + "\n\n\n######################\n\n\n" \
                             + "\n\n\n".join(sorted_message2)

            message = header + '\n {} \n\n'.format(sorted_message)

            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_server, port) as server:
                server.ehlo()  # Can be omitted
                server.starttls(context=context)
                server.ehlo()  # Can be omitted
                server.login(sender_email, email_password)
                server.sendmail(sender_email, receiver_email, message)

    def alert_price_change_via_sms(self):
        coin_value = 0.00003
        if float(self.get_crypto_current_price('SHIBUSDT')) > float(coin_value):
            self.twilioClient.messages.create(to="+1413",
                                          from_="+16109812328",
                                          body="shiba coin price is greater than {}".format(coin_value))


if __name__ == '__main__':

    cryptoUtil = CryptoUtil()
    for crypto_symbol in CRYPTO_SYMBOLS:
        price = cryptoUtil.get_crypto_current_price(crypto_symbol)
        bars = cryptoUtil.get_kline_row_data(crypto_symbol)
        crypto_df = cryptoUtil.calculate_moving_average(bars)
        cryptoUtil.compare_prices(crypto_symbol, price, crypto_df)
    cryptoUtil.send_email_to_user()
    cryptoUtil.alert_price_change_via_sms()

