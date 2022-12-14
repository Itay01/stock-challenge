import json
import requests
from stockfollower import StockFollower
from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
import pandas as pd
import os
from stockmessages import StockMessage
# import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///stock.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100), unique=True)
    stock_points = db.Column(db.Float, nullable=False)
    number = db.Column(db.String(100), unique=True, nullable=False)
    stocks_value = db.Column(db.Float, nullable=False)

    stocks = relationship("Stocks", back_populates="follower")


class Stocks(db.Model):
    __tablename__ = "stocks"
    id = db.Column(db.Integer, primary_key=True)

    # Create Foreign Key, "users.id" the users refers to the tablename of User.
    follower_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    # Create reference to the User object, the "posts" refers to the posts' property in the User class.
    follower = relationship("User", back_populates="stocks")

    stock_name = db.Column(db.String(100), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    stock_price = db.Column(db.Float, nullable=False)
    stock_value = db.Column(db.Float, nullable=False)
    stock_units = db.Column(db.Float, nullable=False)
    stock_diff = db.Column(db.String(100), nullable=False)
    stock_units_value = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(250), nullable=False)


class StocksTable(db.Model):
    __tablename__ = "stocks_table"
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), unique=True, nullable=False)
    stock_symbol = db.Column(db.String(100), unique=True, nullable=False)


db.create_all()


def update_stocks_table():
    """Update all the stocks that are in the stock market."""
    # url = 'blob:https://www.tase.co.il/6ad9aeea-2511-4710-87e9-7a32bd135ff4'
    df = pd.read_csv('securitiesmarketdata.csv')

    db.session.query(StocksTable).delete()
    for name, symbol in zip(df['Name'], df['Symbol']):
        new_stock = StocksTable(
            stock_symbol=symbol,
            company_name=name
        )
        db.session.add(new_stock)

    db.session.commit()

    # # url = 'blob:https://www.tase.co.il/6ad9aeea-2511-4710-87e9-7a32bd135ff4'
    # df = pd.read_csv('securitiesmarketdata.csv')
    #
    # db.session.query(StocksTable).delete()
    # failed_update = []
    # for symbol in df['Symbol']:
    #     try:
    #         stock_follower = StockFollower(symbol)
    #         stock_follower.get_company_name()
    #     except:
    #         failed_update.append(symbol)
    #     else:
    #         new_stock = StocksTable(
    #             stock_symbol=symbol,
    #             company_name=stock_follower.company_name
    #         )
    #         db.session.add(new_stock)
    # print(failed_update)
    # db.session.commit()


def update_user_stocks(user_id):
    """Update the user's stocks, and values. Send notification message if needed."""
    messages = StockMessage()

    user = User.query.get(user_id)
    user.stocks_value = 0
    updates_left = [stock for stock in Stocks.query.filter_by(follower_id=user.id).all()]
    tries = 5
    while updates_left and tries > 0:
        for stock in updates_left:
            stock_follower = StockFollower(stock.stock_name)
            try:
                stock_follower.get_stock()
                stock_follower.get_stock_diff(stock.stock_price)
            except (TypeError, json.decoder.JSONDecodeError, requests.exceptions.ReadTimeout):
                if tries == 1:
                    user.stocks_value = user.stocks_value + stock.stock_units_value
            else:
                stock.stock_value = stock_follower.current_price
                stock.stock_diff = stock_follower.diff_percent
                stock.stock_units_value = stock.stock_value * stock.stock_units
                user.stocks_value = user.stocks_value + stock.stock_units_value

                updates_left.remove(stock)
        tries -= 1

    if updates_left:
        messages.send_message(os.environ.get("MYEMAIL"),
                              f"Error (update): {', '.join([stock.stock_name for stock in updates_left])}.")

    # if user.email != os.environ.get("UNEMAIL"):
    #     messages.send_message(user.email, f"{stock.stock_name}: {stock.stock_diff}", stock.stock_diff)


def check_diff():
    """Update all users stocks, and send notification messages if needed."""
    for user in User.query.all():
        update_user_stocks(user.id)
    db.session.commit()


def reset_user(user_id):
    user = User.query.get(user_id)
    for stock in Stocks.query.filter_by(follower_id=user.id).all():
        db.session.delete(stock)
    user.stock_points = 15000
    user.stocks_value = 0
    db.session.commit()


check_diff()
