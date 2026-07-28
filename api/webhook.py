import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import SearchPostsRequest
from aaa import blocked_channels

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
TG_SESSION = os.environ["TG_SESSION"]

async def search_posts(
        chat_id,
        hashtag=None,
        query=None,
        offset_rate=0,
        offset_id=0
):
    try:
       print("xxx")

    except Exception as e:
        error_text = f"搜索出错:\n\n{str(e)}"

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        body = {
            "chat_id": chat_id,
            "text": error_text
        }

        data = json.dumps(body).encode()

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json"
            }
        )

        urllib.request.urlopen(req)

        return {
            "error": str(e)
        }

def parse_search_text(text):
    text = text.replace("\n", "")
    text = text.strip()

    if text.startswith("#"):
        return {
            "keyword": text,
            "hashtag": text[1:],
            "query": None
        }

    return {
        "keyword": text,
        "hashtag": None,
        "query": text
    }


class handler(BaseHTTPRequestHandler):

    def do_POST(self):

        length = int(
            self.headers.get("Content-Length", 0)
        )

        body = self.rfile.read(length)

        update = json.loads(body)

        message = update.get("message")

        if message:
            chat_id = message["chat"]["id"]

            text = message.get("text", "")

            search = parse_search_text(text)

            search_posts(
                chat_id,
                hashtag=search["hashtag"],
                query=search["query"]
            )

        callback_query = update.get("callback_query")

        if callback_query:
            chat_id = callback_query["message"]["chat"]["id"]

            data = callback_query["data"]

            keyword, offset_rate, offset_id = data.split(",")

            search = parse_search_text(keyword)

            search_posts(
                chat_id,
                hashtag=search["hashtag"],
                query=search["query"],
                offset_rate=int(offset_rate),
                offset_id=int(offset_id)
            )

        self.send_response(200)

        self.end_headers()

        self.wfile.write(
            b"OK"
        )
