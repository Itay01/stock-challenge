import requests
from stockfollower import StockFollower

from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy.orm import relationship

STOCK_API_KEY = "5CG6W0ZGOUHWPAG0"
STOCK_ENDPOINT = "https://www.alphavantage.co/query"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('APP_KEY')

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///stock.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100), unique=True)
    stock_points = db.Column(db.Integer, nullable=False)
    number = db.Column(db.String(100), unique=True)

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
    articles = db.Column(db.String(250), nullable=False)
    stock_price = db.Column(db.Integer, nullable=False)
    stock_value = db.Column(db.Integer, nullable=False)
    stock_units = db.Column(db.Integer, nullable=False)
    stock_diff = db.Column(db.Integer, nullable=False)
    stock_units_rounded = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(250), nullable=False)


for stock in Stocks.query.all():
    user = User.query.get(stock.follower_id)
    stock_follower = StockFollower(stock.stock_name, user.number)
    stock_follower.get_stock()
    stock_follower.get_stock_diff(stock.stock_price)
    stock_follower.get_articles()

    stock.stock_value = stock_follower.closing_price
    stock.stock_diff = stock_follower.diff_percent
    stock.articles = stock_follower.message

    stock_follower.send_messages()

db.session.commit()
