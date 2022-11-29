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
        self.up_down = None
        self.company_name = None
        self.number = number
        self.message = None
        self.closing_price = None
        self.diff_percent = None

    def get_stock(self):
        stock_params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": self.stock_name,
            "apikey": STOCK_API_KEY,
        }

        response = requests.get(STOCK_ENDPOINT, params=stock_params)
        data = response.json()["Time Series (Daily)"]
        data_list = [value for (key, value) in data.items()]
        yesterday_data = data_list[0]
        yesterday_closing_price = yesterday_data["4. close"]
        self.closing_price = yesterday_closing_price

    def get_stock_diff(self, buying_price):
        difference = float(self.closing_price) - float(buying_price)
        up_down = None
        if difference > 0:
            up_down = "🔺"
        else:
            up_down = "🔻"

        diff_percent = abs(round((difference / float(buying_price)) * 100))
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

        # up_down_message = f"{self.stock_name}: {self.up_down}{self.diff_percent}%"
        up_down_message = f"{self.up_down}{self.diff_percent}%"
        formatted_articles = [f"Headline: {article['title']}. \n"
                              f"Brief: {article['description']}\n{article['url']}" for article in three_articles]
        # print(formatted_articles)

        message = f"{up_down_message}\n"
        for article in formatted_articles:
            list_article = article.split("\n")
            for info in list_article:
                message += f"{info}\n"
        self.message = message

    # def send_messages(self):
    #     send_message = f"{self.stock_name}: {self.up_down}{self.diff_percent}%\n"
    #     for i in range(1, len(self.message)+1, 3):
    #         send_message += "\n".join(self.message[i:].split("\n")) + "\n"
    #
    #     client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    #
    #     message = client.messages.create(
    #         body=send_message,
    #         from_=f"whatsapp:{VIRTUAL_TWILIO_NUMBER}",
    #         to=f"whatsapp:{self.number}"
    #     )

