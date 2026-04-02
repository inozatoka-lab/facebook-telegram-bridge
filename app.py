from flask import Flask, request
import requests
import os
import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")

def get_ai_response(user_text):
    prompt = f"""
    You are a shop assistant. Talk politely with the customer in Georgian.
    If the message is an order, confirm it and summarize.
    If it's just a question, answer helpfully.
    Message: "{user_text}"
    """
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150,
        temperature=0.7
    )
    return response.choices[0].text.strip()

app = Flask(__name__)

# Environment Variables (Render → Settings → Environment)
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_verify_token")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

@app.route("/", methods=["GET"])
def index():
    return "Facebook → Telegram Bridge is running."

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Facebook verification
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Verification failed", 403

    if request.method == "POST":
        data = request.get_json(silent=True)

        # Case 1: Sample test JSON (Test button)
        if "sample" in data:
            text = data["sample"]["value"]["message"].get("text", "")
            if text:
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                    json={"chat_id": CHAT_ID, "text": f"[SAMPLE] {text}"}
                )
            return "EVENT_RECEIVED", 200

        # Case 2: Real Messenger JSON (user messages)
        if "entry" in data:
            for entry in data["entry"]:
                for msg_event in entry.get("messaging", []):
                    if "message" in msg_event:
                        text = msg_event["message"].get("text", "")
                        if text:
                            requests.post(
                                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                                json={"chat_id": CHAT_ID, "text": f"[REAL] {text}"}
                            )
            return "EVENT_RECEIVED", 200

        return "No data", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
