import os
from twilio.rest import Client

VIRTUAL_TWILIO_NUMBER = os.environ.get("NUMBER")
TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_TOKEN")


class StockMessage:
    def __init__(self):
        self.client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

    def check_number(self, number):
        """Return True if the user verified his phone number, and False if he did not."""
        verified_numbers = []
        for msgs in self.client.messages.list():
            if "join" in msgs.body and msgs.from_ not in verified_numbers:
                verified_numbers.append(msgs.from_)

        if f"whatsapp:{number}" in verified_numbers:
            return True
        return False

    def send_message(self, number, send_message, diff_percent="0"):
        """Send message to the user in case the difference between the buying price and the current value,
        is bigger than 5%. """
        if float(diff_percent[1:-1]) > 5:
            message = self.client.messages.create(
                body=send_message,
                from_=f"whatsapp:{VIRTUAL_TWILIO_NUMBER}",
                to=f"whatsapp:{number}"
            )
