import os
from flask import Flask
from flask_mail import Mail, Message
from twilio.rest import Client

VIRTUAL_TWILIO_NUMBER = os.environ.get("NUMBER")
TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_TOKEN")


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('APP_KEY')
app.app_context()

mail = Mail(app)
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = os.environ.get('EMAIL')
app.config["MAIL_PASSWORD"] = os.environ.get('EMAIL_PASSWORD')
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True
mail = Mail(app)


class StockMessage:
    # def __init__(self):
        # self.client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

    # def check_number(self, number):
    #     """Return True if the user verified his phone number, and False if he did not."""
    #     verified_numbers = []
    #     for msgs in self.client.messages.list():
    #         if "join" in msgs.body and msgs.from_ not in verified_numbers:
    #             verified_numbers.append(msgs.from_)
    #
    #     if f"whatsapp:{number}" in verified_numbers:
    #         return True
    #     return False

    def send_message(self, email, send_message, diff_percent=" 6  "):
        """Send email to the user in case the difference between the buying price and the current value,
        is bigger than 5%. """
        if float(diff_percent[1:-2]) > 5:
            with app.app_context():
                msg = Message("Stock Update", sender=app.config["MAIL_USERNAME"], recipients=[email])
                msg.body = send_message
                mail.send(msg)

        #     message = self.client.messages.create(
        #         body=send_message,
        #         from_=f"{VIRTUAL_TWILIO_NUMBER}",
        #         to=f"{number}"
        #     )

    def contact_message(self, name, email, phone, message):
        with app.app_context():
            msg = Message("New Message", sender=app.config["MAIL_USERNAME"], recipients=[os.environ.get("MY_EMAIL")])
            msg.body = f"Name: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {message}"
            mail.send(msg)
