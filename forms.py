from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    number = StringField("Phone Number", render_kw={'placeholder': 'Valid Format is 05xxxxxxxx'},
                         validators=[DataRequired()],
                         description='p tag')
    submit = SubmitField("Sign Me Up!")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


class BuyForm(FlaskForm):
    stock_name = StringField("Stock Symbol", validators=[DataRequired()])
    buy_value = StringField("Purchase Value ₪", validators=[DataRequired()])
    submit = SubmitField("Buy My Stock!", render_kw={"onclick": "loader()"})


class SellForm(FlaskForm):
    stocks_list = SelectField("Choose Stock:")
    sell_value = StringField("Sell Value ₪", validators=[DataRequired()])
    submit = SubmitField("Sell My stock!", render_kw={"onclick": "loader()"})

