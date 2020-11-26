#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ~~~~~
# == Setup ==
# % pip3 install [--user] requests
# % pip3 install [--user] schedule
# % pip3 install [--user] yfinance
#
# Add and make Python-scripts executable:
# % chmod +x ./stock_notifications.py
# % chmod +x ./botconfigs.py
#
# == Usage ==
# one time (repeat every minute):
# % python3 ./stock_notifications.py "BTC-USD"
#
# running as a service (every 1 hour):
# % nohup python3 ./stock_notifications.py "TSLA" 3600 $
#
# ~~~~~
# Original source: https://codeburst.io/indian-stock-market-price-notifier-bot-telegram-92e376b0c33a
# Resources:
#  - Symbol: https://finance.yahoo.com/quote/TSLA?p=TSLA
#  - YF for Python: https://pypi.org/project/fix-yahoo-finance/0.1.30/
#  - YF4P docu: https://aroussi.com/post/python-yahoo-finance
#  - Telegram Bot API: https://core.telegram.org/bots/api#sendmessage
# ~~~~~
import sys
import requests
import time
import schedule
import datetime
import json
import yfinance as yf
import urllib.parse
import botconfigs as bot

# Check for stock symbol passed as script parameter
if len(sys.argv) <= 1:
    print("Missing a valid symbol as parameter. Use something like 'TSLA' or 'BTC-USD'...")
    quit()
else:
    symbol=sys.argv[1]

# Check for passed timer seconds parameter
if len(sys.argv) <= 2:
    # Default: 1 minute = 60 seconds
    repeat=60
elif int(sys.argv[2]) >= 1:
    repeat=int(sys.argv[2])
else:
    print("Invalid second parameter: must be a number representing seconds to re-run script.")
    quit()

def getStock():
    # Check for valid Telegram Bot Configs from botconfigs.py
    if len(bot.token) > 40 and len(bot.chat) > 5:
        bot_token=bot.token
        bot_chatID=bot.chat
    else:
        print("Missing botconfigs!")
        quit()

    currency=''
    price=0
    prev_price=0

    # Fetch the stock symbol Currency
    ticker_meta=yf.Ticker(symbol)
    ticker_dict=ticker_meta.info
    ticker_json=json.dumps(ticker_dict)
    ticker_json=json.loads(ticker_json)
    if ticker_json["currency"] != '':
        currency=ticker_json["currency"]

    # Fetch the stock symbol daily data
    ticker=yf.download(symbol, period="1d")
    #DEBUG: print(ticker)
    if prev_price == 0:
        prev_price=(ticker["Open"][0]).round(2)
    else:
        prev_price=price
    price=(ticker["Close"][0]).round(2)
    if prev_price == 0 or price == prev_price:
        price_change_str = ''
        price_diff_str = ''
    elif price > prev_price:
        price_diff = (price-prev_price).round(2)
        price_change_str = "surged"
        price_diff_str = "("+price_change_str+" +"+str("{0:,.2f}".format(price_diff)).replace(',', '\'')+")"
    else:
        price_diff = (prev_price-price).round(2)
        price_change_str = "dropped"
        price_diff_str = "("+price_change_str+" -"+str("{0:,.2f}".format(price_diff)).replace(',', '\'')+")"

    # Build message string with escaping url critical chars
    message=symbol+" @ *"+currency+" "+str("{0:,.2f}".format(price)).replace(',', '\'')+"* "+price_diff_str
    message=message.replace("-","\-")
    message=message.replace("+","\+")
    message=message.replace(".","\.")
    message=message.replace("(","\(")
    message=message.replace(")","\)")
    message=message.replace("?","\?")
    message=message.replace("^","\^")
    message=message.replace("$","\$")
    message=urllib.parse.quote_plus(message)
    #DEBUG: print(message)

    # Send GET request to Telegram Bot API
    send='https://api.telegram.org/bot' + bot_token + '/sendMessage?parse_mode=MarkdownV2&disable_notification=true&chat_id=' + bot_chatID + '&text=' + message
    #DEBUG: print(send)
    response=requests.get(send)
    #DEBUG: print(response)

import threading
while True:
    getStock()
    time.sleep(repeat)
