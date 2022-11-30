from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    number = StringField("Phone Number")
    submit = SubmitField("Sign Me Up!")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


class StockForm(FlaskForm):
    stock_name = StringField("Stock Symbol", validators=[DataRequired()])
    points_amount = StringField("Purchase Value 💲", validators=[DataRequired()])
    submit = SubmitField("Buy My Stock!")
