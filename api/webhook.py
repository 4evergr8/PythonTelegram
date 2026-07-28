import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler


BOT_TOKEN = os.environ["BOT_TOKEN"]


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    data = json.dumps({
        "chat_id": chat_id,
        "text": text
    }).encode()

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json"
        }
    )

    urllib.request.urlopen(req)


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        update = json.loads(body)

        message = update.get("message")

        if message:
            chat_id = message["chat"]["id"]
            text = message.get("text", "")

            send_message(
                chat_id,
                f"收到：{text}{chat_id}"
            )

        self.send_response(200)
        self.end_headers()

        self.wfile.write(
            b"OK"
        )