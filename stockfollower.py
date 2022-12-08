import requests
import os
from twilio.rest import Client
import yfinance as yf

VIRTUAL_TWILIO_NUMBER = os.environ.get("NUMBER")

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

STOCK_API_KEY = os.environ.get("STOCK_KEY")
NEWS_API_KEY = os.environ.get("NEWS_KEY")
TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_TOKEN")


class StockFollower:
    def __init__(self, stock_name):
        self.stock_name = stock_name
        self.up_down = None
        self.company_name = None
        self.message = None
        self.closing_price = None
        self.diff_percent = None

    def get_stock(self):
        stock_last_day = yf.Ticker(f"{self.stock_name}.TA").history(period='1d')
        close_price = stock_last_day['Close'][0]
        self.closing_price = close_price

    def get_stock_diff(self, buying_price):
        difference = float(self.closing_price) - float(buying_price)
        up_down = None
        if difference > 0:
            up_down = "🔺"
        else:
            up_down = "🔻"

        diff_percent = abs(round((difference / float(buying_price)) * 100))
        self.diff_percent = diff_percent
        self.up_down = up_down

    def get_articles(self):
        self.message = "test"
        ticker = yf.Ticker(f"{self.stock_name}.TA")
        self.company_name = ticker.info['longName']

        return None
        up_down_message = f"{self.up_down}{self.diff_percent}%"
        formatted_articles = [f"Headline: {article['title']}. \n"
                              f"Brief: {article['description']}\n{article['url']}" for article in three_articles]

        message = f"{up_down_message}\n"
        for article in formatted_articles:
            list_article = article.split("\n")
            for info in list_article:
                message += f"{info}\n"
        self.message = message

    def send_messages(self, number):
        if self.diff_percent > 5 and number != "":
            send_message = f"{self.stock_name}: {self.up_down}{self.diff_percent}%\n"
            for i in range(1, len(self.message) + 1, 3):
                send_message += "\n".join(self.message[i:].split("\n")) + "\n"

            client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

            message = client.messages.create(
                body=send_message,
                from_=f"whatsapp:{VIRTUAL_TWILIO_NUMBER}",
                to=f"whatsapp:{number}"
            )
