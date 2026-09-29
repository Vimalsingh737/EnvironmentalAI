import os
from twilio.rest import Client

account_sid = os.environ["TWILIO_ACCOUNT_SID"]
auth_token = os.environ["TWILIO_AUTH_TOKEN"]

client = Client(account_sid, auth_token)

message = client.messages.create(
    body="sms_internal_alerts",
    from_="+17372212163",
    to="+917860578759"
)

print("SMS request sent!")
print("Message SID:", message.sid)
print("Status:", message.status)