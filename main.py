from stockfollower import StockFollower
from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from datetime import date
from werkzeug.exceptions import abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from forms import RegisterForm, LoginForm, StockForm
from functools import wraps
import os

# Todo: show the money that is invested.


STOCK_POINTS = 50000

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('APP_KEY')
ckeditor = CKEditor(app)
Bootstrap(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", "sqlite:///stock.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100), unique=True)
    stock_points = db.Column(db.Integer, nullable=False)
    number = db.Column(db.String(100), unique=True, nullable=False)
    stocks_value = db.Column(db.Integer, nullable=False)

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
    stock_units_value = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(250), nullable=False)


db.create_all()


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if current_user.id != 1:
                return abort(403)
        except AttributeError:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


def login_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if not current_user.is_authenticated:
                return abort(403)
        except AttributeError:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


def logout_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if current_user.is_authenticated:
                return abort(403)
        except AttributeError:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def get_all_stocks():
    # Todo: Add user balance in the main screen.
    if current_user.is_authenticated:
        if current_user.id == 1:
            stocks = Stocks.query.all()
        else:
            stocks = Stocks.query.filter_by(follower_id=current_user.id).all()
    else:
        stocks = []

    return render_template("index.html", all_stocks=stocks, current_user=current_user)


@app.route('/register', methods=["GET", "POST"])
@logout_only
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        number_data = form.number.data
        if len(number_data) != 10 or number_data[0] != "0" or number_data[1] != '5':
            flash("Invalid phone number format!")
            return render_template("register.html", form=form, current_user=current_user)

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )

        number = number_data.replace("0", "+972", 1)
        new_user = User(
            email=form.email.data,
            password=hash_and_salted_password,
            name=form.name.data,
            number=number,
            stock_points=STOCK_POINTS,
            stocks_value=0
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
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
        # Email doesn't exist or password incorrect.
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_stocks'))
    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout')
@login_only
def logout():
    logout_user()
    return redirect(url_for('get_all_stocks'))


@app.route("/stock/<int:stock_id>", methods=["GET", "POST"])
@login_only
def show_stock(stock_id):
    requested_stock = Stocks.query.get(stock_id)
    if requested_stock.follower_id != current_user.id and current_user.id != 1:
        return redirect(url_for('get_all_stocks'))

    articles_list = requested_stock.articles.split("\n")[:-1]
    len_list = len(articles_list[1:])+1
    profit = requested_stock.stock_units * (requested_stock.stock_value - requested_stock.stock_price)

    return render_template("stock.html", stock=requested_stock, len_list=len_list,
                           articles_list=articles_list, current_user=current_user, profit_points=profit)


@app.route("/new-stock", methods=["GET", "POST"])
@login_only
def buy_new_stock():
    # Todo: Add current balance.
    form = StockForm()
    if form.validate_on_submit():
        try:
            stock_follower = set_follower(form.stock_name.data)
            stock_follower.get_stock()
        except KeyError:
            flash('Invalid stock symbol!')
            return redirect(url_for('buy_new_stock'))

        stock_price = float(stock_follower.closing_price)
        points_amount = float(form.points_amount.data)
        stock_units = points_amount / stock_price

        if current_user.stock_points - points_amount < 0:
            flash('You do not have enough money!')
            return redirect(url_for('buy_new_stock'))
        elif form.stock_name.data in [s.stock_name for s in Stocks.query.filter_by(follower_id=current_user.id).all()]:
            flash('You already bought this stock!')
            return redirect(url_for('buy_new_stock'))

        stock_follower.get_stock_diff(stock_follower.closing_price)
        stock_follower.get_articles()

        new_stock = Stocks(
            company_name=stock_follower.company_name,
            stock_name=form.stock_name.data,
            follower=current_user,
            stock_price=stock_price,
            stock_value=stock_price,
            stock_units=stock_units,
            stock_diff=stock_follower.diff_percent,
            stock_units_value=stock_units*stock_price,
            articles=stock_follower.message,
            date=date.today().strftime("%B %d, %Y")
        )

        current_user.stock_points = current_user.stock_points - points_amount
        current_user.stocks_value = current_user.stocks_value + new_stock.stock_units_value
        db.session.add(new_stock)
        db.session.commit()
        return redirect(url_for("get_all_stocks"))
    return render_template("buy-stock.html", form=form, current_user=current_user)


@app.route("/sell-stock/<int:stock_id>", methods=["GET", "POST"])
@login_only
def sell_stock(stock_id):
    stock_to_sell = Stocks.query.get(stock_id)
    if current_user.id != stock_to_sell.follower_id and current_user.id != 1:
        return redirect(url_for("get_all_stocks"))

    total_value = stock_to_sell.stock_units * stock_to_sell.stock_value
    current_user.stock_points = current_user.stock_points + total_value
    current_user.stocks_value = current_user.stocks_value - total_value
    db.session.delete(stock_to_sell)
    db.session.commit()
    return redirect(url_for("get_all_stocks"))


def set_follower(stock_name):
    stock_follower = StockFollower(stock_name)
    return stock_follower


if __name__ == "__main__":
    app.run(debug=True)
