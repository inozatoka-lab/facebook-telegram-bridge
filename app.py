from flask import Flask, request
import requests
import os
import openai

# OpenAI API Key
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Env Variables
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_verify_token")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
PAGE_ACCESS_TOKEN = os.environ.get("PAGE_ACCESS_TOKEN")

app = Flask(__name__)

# --- AI ფუნქცია ---
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

# --- შეკვეთის ამოცნობა ---
def is_order_message(text):
    keywords = ["მინდა", "შეკვეთა", "დამიტოვე", "გავაკეთებ"]
    return any(word in text for word in keywords)

# --- Messenger‑ში პასუხის გაგზავნა ---
def send_to_messenger(recipient_id, text):
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    requests.post(url, json=payload)

@app.route("/", methods=["GET"])
def index():
    return "Facebook → Telegram AI Bridge is running."

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

        # Case 1: Sample test JSON
        if "sample" in data:
            text = data["sample"]["value"]["message"].get("text", "")
            if text:
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                    json={"chat_id": CHAT_ID, "text": f"[SAMPLE] {text}"}
                )
            return "EVENT_RECEIVED", 200

        # Case 2: Real Messenger JSON
        if "entry" in data:
            for entry in data["entry"]:
                for msg_event in entry.get("messaging", []):
                    if "message" in msg_event:
                        sender_id = msg_event["sender"]["id"]
                        text = msg_event["message"].get("text", "")

                        if text:
                            # Step 1: AI პასუხი
                            ai_response = get_ai_response(text)

                            # Step 2: Messenger‑ში გაგზავნა
                            send_to_messenger(sender_id, ai_response)

                            # Step 3: შეკვეთის შემოწმება
                            if is_order_message(text):
                                requests.post(
                                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                                    json={"chat_id": CHAT_ID, "text": f"[ORDER] {text}"}
                                )
            return "EVENT_RECEIVED", 200

        return "No data", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
