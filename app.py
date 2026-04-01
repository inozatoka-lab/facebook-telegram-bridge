import requests
from flask import Flask, request
import os

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Verification failed", 403
    
    elif request.method == "POST":
        data = request.json
        if "message" in data["entry"][0]["messaging"][0]:
            message = data["entry"][0]["messaging"][0]["message"]["text"]
            
            # გადაგზავნა Telegram-ში
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": CHAT_ID, "text": message}
            requests.post(url, json=payload)
        
        return "ok", 200

if __name__ == "__main__":
    app.run()