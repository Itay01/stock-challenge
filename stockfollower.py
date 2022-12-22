import yfinance as yf


class StockFollower:
    def __init__(self, stock_symbol):
        self.stock_symbol = stock_symbol
        self.company_name = None
        self.closing_price = None
        self.diff_percent = None
        self.ticker = None
        self.current_price = None

    def get_stock(self):
        """Update the stock current value."""
        self.ticker = yf.Ticker(f"{self.stock_symbol}.TA")
        self.current_price = self.ticker.info["regularMarketPrice"]

    def get_company_name(self):
        """Get the stock Company name by its symbol. In case the symbol is of an indicator,
        the company name will be the symbol."""
        try:
            self.company_name = self.ticker.info['longName']
        except KeyError:
            self.company_name = self.stock_symbol

    def get_stock_diff(self, buying_price):
        """Calculate the difference of the buying price and the current value (in percentage).
        Update the diff_percent to the text that is shown in the main screen, and the notification messages."""
        difference = float(self.current_price) - float(buying_price)
        if difference > 0:
            up_down = "🔺"
        else:
            up_down = "🔻"
        self.diff_percent = f"{up_down}{abs(round((difference / float(buying_price)) * 100, 2))} %"
