import os
from twilio.rest import Client

class TwilioService:
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None

    def send_message(self, to_number, body):
        if not self.client:
            print(f"Twilio not configured. Would send to {to_number}: {body}")
            return None
            
        try:
            message = self.client.messages.create(
                from_=self.from_number,
                body=body,
                to=f"whatsapp:{to_number}" if not to_number.startswith('whatsapp:') else to_number
            )
            return message.sid
        except Exception as e:
            print(f"Error sending Twilio message: {e}")
            return None
