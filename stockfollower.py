import yfinance as yf


class StockFollower:
    def __init__(self, stock_name):
        self.stock_name = stock_name
        self.up_down = None
        self.company_name = None
        self.closing_price = None
        self.diff_percent = None
        self.ticker = None
        self.close_price = None

    def get_stock(self):
        self.ticker = yf.Ticker(f"{self.stock_name}.TA")
        stock_last_day = self.ticker.history(period='2d')
        self.closing_price = stock_last_day['Close'][0]
        try:
            self.company_name = self.ticker.info['longName']
        except KeyError:
            self.company_name = self.stock_name

    def get_stock_diff(self, buying_price):
        difference = float(self.closing_price) - float(buying_price)
        if difference > 0:
            self.up_down = "🔺"
        else:
            self.up_down = "🔻"
        self.diff_percent = f"{self.up_down}{abs(round((difference / float(buying_price)) * 100, 2))} %"
