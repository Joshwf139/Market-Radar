import os
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

message = """
🚨 MARKET RADAR TEST

Your alert system is connected.

Next we'll make it monitor:
🇺🇸 US politics
🌎 Wars & geopolitics
📱 Social-media trends
📈 Market-moving events

This is only a test.
"""

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

response = requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": message
    }
)

print(response.json())
