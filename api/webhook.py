from flask import Flask, request
import requests

app = Flask(__name__)


BOT_TOKEN = "8241984939:AAF8JilTNlf7ucl5s8JB2z3EzBiRYqFFx48"


@app.route("/", methods=["POST"])
def webhook():

    data = request.json

    if "message" in data:

        chat_id = data["message"]["chat"]["id"]

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "滚蛋"
            }
        )

    return "ok"


@app.route("/", methods=["GET"])
def index():
    return "running"