from flask import Flask, request, jsonify
import requests
import logging
from dotenv import load_dotenv
import os

app = Flask(__name__)

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

# Enable logging
logging.basicConfig(level=logging.INFO)

# Meta/Instagram webhook verification
VERIFY_TOKEN = 'cosclub_indonesia_123'  # You define this in your Meta webhook settings

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # Verification challenge from Meta
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logging.info('WEBHOOK_VERIFIED')
            return challenge, 200   
        else:
            return 'Verification failed', 403

    elif request.method == 'POST':
        data = request.get_json()
        logging.info('Webhook Received: %s', data)

        # Optional: Do something with the data
        handle_webhook(data)

        return 'EVENT_RECEIVED', 200


def handle_webhook(data):
    if data.get('object') == 'instagram':
        for entry in data.get('entry', []):
            if 'messaging' in entry:
                for message_event in entry['messaging']:
                    if 'message' in message_event:
                        handle_message(message_event)
                    elif 'reaction' in message_event:
                        handle_reaction(message_event)
                    elif 'postback' in message_event:
                        handle_postback(message_event)
                    elif 'referral' in message_event:
                        handle_referral(message_event)
                    elif 'read' in message_event:
                        handle_read_receipt(message_event)
            elif entry.get('field') == 'comments':
                handle_comment(entry)


def handle_message(event):
    print("Message Event:", event)

def handle_reaction(event):
    print("Reaction Event:", event)

def handle_postback(event):
    print("Postback Event:", event)

def handle_referral(event):
    print("Referral Event:", event)

def handle_read_receipt(event):
    print("Read Receipt Event:", event)

def handle_comment(entry):
    print("Comment Event:", entry)


@app.route("/")
def index():
    auth_url = (
        f"https://www.instagram.com/oauth/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=instagram_business_basic,instagram_business_manage_comments,"
        f"instagram_business_manage_messages,instagram_business_content_publish"
        f"&response_type=code"
    )
    return f'<a href="{auth_url}">Login with Instagram</a>'

@app.route("/auth/callback")
def auth_callback():
    code = request.args.get('code')
    if not code:
        return "Authorization failed or denied", 400

    token_url = "https://api.instagram.com/oauth/access_token"
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code
    }

    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        return f"Token exchange failed: {response.json()}", 400

    data = response.json()
    return jsonify(data)

@app.route("/exchange-long-token", methods=["POST"])
def exchange_for_long_token():
    short_token = request.json.get("short_token")
    if not short_token:
        return jsonify({"error": "short_token is required"}), 400

    url = "https://graph.instagram.com/access_token"
    params = {
        "grant_type": "ig_exchange_token",
        "client_secret": CLIENT_SECRET,
        "access_token": short_token
    }

    res = requests.get(url, params=params)
    return jsonify(res.json())

@app.route("/refresh-token", methods=["POST"])
def refresh_token():
    long_token = request.json.get("long_token")
    if not long_token:
        return jsonify({"error": "long_token is required"}), 400

    url = "https://graph.instagram.com/refresh_access_token"
    params = {
        "grant_type": "ig_refresh_token",
        "access_token": long_token
    }

    res = requests.get(url, params=params)
    return jsonify(res.json())

if __name__ == '__main__':
    app.run(port=5000, debug=True)
