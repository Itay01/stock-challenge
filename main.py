from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
from stockfollower import StockFollower
from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from datetime import date
from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from forms import RegisterForm, LoginForm, BuyForm, SellForm
from flask_apscheduler import APScheduler
from functools import wraps
import os
from datetime import datetime
from stockmessages import StockMessage
from updatedatabase import check_diff

STOCK_POINTS = 15000

# Configure App
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('APP_KEY')
Bootstrap(app)

# Set Scheduler
scheduler = BackgroundScheduler()

# Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///stock.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Import StockMessage Class from stockmessages.py
messages = StockMessage()

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Database Modals
class User(UserMixin, db.Model):  # User info + Stocks value
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100), unique=True)
    stock_points = db.Column(db.Integer, nullable=False)
    number = db.Column(db.String(100), unique=True, nullable=False)
    stocks_value = db.Column(db.Float, nullable=False)

    stocks = relationship("Stocks", back_populates="follower")


class Stocks(db.Model):  # Stock info + value.
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


class StocksTable(db.Model):  # Name and Symbol of all the stocks in the website.
    __tablename__ = "stocks_table"
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), unique=True, nullable=False)
    stock_symbol = db.Column(db.String(100), unique=True, nullable=False)


db.create_all()


def admin_only(f):  # Check if the user is the Admin.
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if current_user.id != 1:
                return abort(403)
        except AttributeError:
            return abort(403)
        return f(*args, **kwargs)

    return decorated_function


def login_only(f):  # Only user that are logged in.
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if not current_user.is_authenticated:
                return abort(403)  # Show 403 page if the user is not logged in.
        except AttributeError:
            return abort(403)  # Show 403 page if the user is not logged in.
        return f(*args, **kwargs)

    return decorated_function


def logout_only(f):  # Only user that are logged out.
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if current_user.is_authenticated:
                return abort(403)  # Show 403 page if the user is logged in.
        except AttributeError:
            return abort(403)  # Show 403 page if the user is logged in.
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
def get_all_stocks():
    if current_user.is_authenticated:  # Check if the user has logged in.
        if current_user.id == 1:
            stocks = Stocks.query.all()  # For Admin user only (shows all stocks).
        else:
            stocks = Stocks.query.filter_by(follower_id=current_user.id).all()  # All the stocks of the uesr.
    else:
        stocks = []  # In case the user has not logged in (no stocks).

    return render_template("index.html", all_stocks=stocks, current_user=current_user)


@app.route('/register', methods=["GET", "POST"])
@logout_only
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            # Redict the user to the login page, in case the user already exists.
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        elif User.query.filter_by(name=form.name.data).first():
            flash("You've already used this name!")
            return render_template("register.html", form=form, current_user=current_user)

        number_data = form.number.data
        number = number_data.replace("0", "+972", 1)
        if len(number_data) != 10 or number_data[0] != "0" or number_data[1] != '5':  # Validate phone format.
            flash("Invalid phone number format!")
            return render_template("register.html", form=form, current_user=current_user)
        elif User.query.filter_by(number=number).first():
            flash("You've already used this phone number!")
            return render_template("register.html", form=form, current_user=current_user)
        elif messages.check_number(number) is False:  # Check if the user verified his phone number.
            flash("Please verify your phone number!")
            return render_template("register.html", form=form, current_user=current_user)

        hash_and_salted_password = generate_password_hash(  # Encrypting the password of the user.
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )

        new_user = User(
            email=form.email.data,
            password=hash_and_salted_password,
            name=form.name.data,
            number=number,
            stock_points=STOCK_POINTS,
            stocks_value=0
        )
        db.session.add(new_user)  # Creating new user.
        db.session.commit()

        login_user(new_user)  # Login the user.
        return redirect(url_for("get_all_stocks"))

    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
@logout_only
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()

        if not user:  # Email doesn't exist.
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):  # Password incorrect.
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)  # Login the user and redict him to the main screen.
            return redirect(url_for('get_all_stocks'))
    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
@login_only
def logout():
    logout_user()  # Logout user.
    return redirect(url_for('get_all_stocks'))


@app.route("/stock/<int:stock_id>", methods=["GET", "POST"])
@login_only
def show_stock(stock_id):
    requested_stock = Stocks.query.get(stock_id)  # Get the stock, by his id.
    if requested_stock.follower_id != current_user.id and current_user.id != 1:
        # The user is not the holder/ owner of the stock.
        return redirect(url_for('get_all_stocks'))

    # Get the number of days the user has the stock.
    date_now = datetime.now()
    buying_date = datetime.strptime(requested_stock.date, "%B %d, %Y")
    diff_days = (date_now - buying_date).days

    # Calculate the profit of the user on the chosen stock.
    profit = requested_stock.stock_units * (requested_stock.stock_value - requested_stock.stock_price)

    return render_template("stock.html", stock=requested_stock, current_user=current_user, profit_points=profit,
                           diff_days=diff_days)


@app.route("/new-stock", methods=["GET", "POST"])
@login_only
def buy_new_stock():
    form = BuyForm()
    all_stocks = StocksTable.query.all()  # Get all the stocks in the stock market.

    # Add all the possible stock to the SelectBox in the BuyForm.
    possible_stocks = {i: all_stocks[i].company_name for i in range(len(all_stocks))}
    form.stock_name.choices = [("", "")] + [(uuid, name) for uuid, name in possible_stocks.items()]
    if form.validate_on_submit():
        stock_symbol = StocksTable.query.filter_by(company_name=possible_stocks[int(form.stock_name.data)]).first()
        stock_symbol = stock_symbol.stock_symbol
        try:  # Try to get the stock Price.
            stock_follower = StockFollower(stock_symbol)
            stock_follower.get_stock()
        except IndexError:  # The stock doesn't exists.
            flash('Invalid stock symbol!')
            return redirect(url_for('buy_new_stock'))

        stock_price = float(stock_follower.current_price)
        buy_value = float(form.buy_value.data)
        stock_units = buy_value / stock_price

        if current_user.stock_points - buy_value < 0:  # Check if the user has enough money to buy the stock.
            flash('You do not have enough money!')
            return redirect(url_for('buy_new_stock'))

        # Details/ info on the stock.
        stock_follower.get_company_name()
        stock_follower.get_stock_diff(stock_follower.current_price)

        new_stock = Stocks(
            company_name=stock_follower.company_name,
            stock_name=stock_symbol,
            follower=current_user,
            stock_price=stock_price,
            stock_value=stock_price,
            stock_units=stock_units,
            stock_diff=stock_follower.diff_percent,
            stock_units_value=stock_units * stock_price,
            date=date.today().strftime("%B %d, %Y")
        )

        current_user.stock_points = current_user.stock_points - buy_value  # Remove the money the stock cost.

        # Update the user stocks value.
        current_user.stocks_value = current_user.stocks_value + new_stock.stock_units_value

        # Add the stock to the database.
        db.session.add(new_stock)
        db.session.commit()

        return redirect(url_for("get_all_stocks"))
    return render_template("buy-modal.html", form=form)


@app.route("/sell-stock", methods=["GET", "POST"])
@login_only
def sell_stock():
    form = SellForm()

    user_stocks = Stocks.query.filter_by(follower_id=current_user.id).all()  # Get all the stock of the user.

    # Add the options to the SelectBox in the SellForm.
    stocks = [(stock.company_name, round(stock.stock_units_value, 2)) for stock in user_stocks]
    form.stocks_list.choices = [(str(i + 1), f"{stocks[i][0]} ({stocks[i][1]}₪)") for i in range(len(stocks))]

    if form.validate_on_submit():
        # Find the stock the user wants to sell.
        user_choice = form.stocks_list.data
        stock_to_sell = user_stocks[int(user_choice) - 1]

        stock_units_value = stock_to_sell.stock_units_value  # Value of the stock
        sell_value = float(form.sell_value.data)  # The specified money the user wants to sell.
        if stock_units_value < sell_value:
            # The stock worth less than the entered price the user wants to sell.
            flash(f"Your stock is worth only {round(stock_units_value, 2)}!")
            return redirect(url_for('sell_stock'))
        else:  # If the stock worth more than the specified value to sell.
            current_user.stock_points = current_user.stock_points + sell_value  # Add the money the user sold.
            current_user.stocks_value = current_user.stocks_value - sell_value  # Update the stocks value.

            if round(stock_units_value, 2) == sell_value:  # Float numbers are not accurate, and they must be rounded.
                db.session.delete(stock_to_sell)  # Delete the stock from the database.
            else:  # The user sold part of the stock.
                # Update the units that are left, and the units value.
                units_left = (stock_units_value - sell_value) / stock_to_sell.stock_value
                stock_to_sell.units = units_left
                stock_to_sell.stock_units_value = units_left * stock_to_sell.stock_value

            db.session.commit()
        return redirect(url_for("get_all_stocks"))
    return render_template("sell-modal.html", form=form, stocks=stocks)


def message_users():
    check_diff()  # update all the stocks + send messages in case of 5% change.


def run_scheduler():
    scheduler.add_job(message_users, 'interval', hours=1)
    scheduler.start()


scheduler_thread = Thread(target=run_scheduler)
scheduler_thread.start()

if __name__ == "__main__":
    app.run(debug=True)
