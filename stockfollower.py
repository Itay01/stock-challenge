import requests
from twilio.rest import Client
import yfinance as yf

VIRTUAL_TWILIO_NUMBER = "+14155238886"

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

STOCK_API_KEY = "5CG6W0ZGOUHWPAG0"
NEWS_API_KEY = "e1dfb3794fac4d5f918e1aaacbd7ab5e"
TWILIO_SID = "AC0d072a022d6c1935415814ce5f224292"
TWILIO_AUTH_TOKEN = "0cce5db19bcb5730b43dc0f399c7b098"


class StockFollower:
    def __init__(self, stock_name, number):
        self.stock_name = stock_name
        self.company_name = None
        self.number = number
        self.articles = None
        self.closing_price = None
        self.diff_percent = None
        self.up_down = None
        self.articles = None

    def get_stock_diff(self):
        stock_params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": self.stock_name,
            "apikey": STOCK_API_KEY,
        }

        response = requests.get(STOCK_ENDPOINT, params=stock_params)
        data = response.json()["Time Series (Daily)"]
        print(data)
        data_list = [value for (key, value) in data.items()]
        yesterday_data = data_list[0]
        yesterday_closing_price = yesterday_data["4. close"]
        self.closing_price = yesterday_closing_price
        # print(yesterday_closing_price)

        day_before_yesterday_data = data_list[1]
        day_before_yesterday_closing_price = day_before_yesterday_data["4. close"]
        # print(day_before_yesterday_closing_price)

        difference = float(yesterday_closing_price) - float(day_before_yesterday_closing_price)
        up_down = None
        if difference > 0:
            up_down = "🔺"
        else:
            up_down = "🔻"

        diff_percent = round((difference / float(yesterday_closing_price)) * 100)
        # print(diff_percent)
        self.diff_percent = diff_percent
        self.up_down = up_down

    def get_articles(self):
        self.company_name = yf.Ticker(self.stock_name).info['longName']
        news_params = {
            "apiKey": NEWS_API_KEY,
            "qInTitle": self.company_name
        }

        news_response = requests.get(NEWS_ENDPOINT, params=news_params)
        articles = news_response.json()["articles"]

        three_articles = articles[:3]
        # print(three_articles)
        self.articles = three_articles
        print(self.articles)

    def send_messages(self):
        formatted_articles = [f"{self.stock_name}: {self.up_down}{self.diff_percent}%\nHeadline: {article['title']}. \n"
                              f"Brief: {article['description']}" for article in self.articles]
        # print(formatted_articles)
        self.articles = formatted_articles

        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

        for article in formatted_articles:
            message = client.messages.create(
                body=article,
                from_=f"whatsapp:{VIRTUAL_TWILIO_NUMBER}",
                to=f"whatsapp:{self.number}"
            )

