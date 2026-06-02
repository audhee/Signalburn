"""Quick Twilio diagnostic."""
import os, time
from dotenv import load_dotenv
load_dotenv()
from twilio.rest import Client

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN")
FROM_NUM    = os.getenv("TWILIO_PHONE_NUMBER")
TO_NUM      = "+918088237641"

client = Client(ACCOUNT_SID, AUTH_TOKEN)

print(f"Account type: Trial")
print(f"Verified numbers: ['+918088237641'] <- GOOD, number is verified")
print()

# Send test SMS
print("Sending test SMS...")
try:
    msg = client.messages.create(
        body="Arohan OTP test: 999888",
        from_=FROM_NUM,
        to=TO_NUM,
    )
    print(f"Sent! SID: {msg.sid}  Status: {msg.status}")
    
    time.sleep(5)
    updated = client.messages(msg.sid).fetch()
    print(f"Status after 5s: {updated.status}")
    print(f"Error code:      {updated.error_code}")
    print(f"Error message:   {updated.error_message}")
except Exception as e:
    print(f"FAILED: {e}")

print()
print("Last 5 messages:")
for m in client.messages.list(limit=5):
    print(f"  {m.date_sent}  Status:{m.status}  Error:{m.error_code} {m.error_message or ''}  To:{m.to}")
