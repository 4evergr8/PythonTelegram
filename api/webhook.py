import asyncio
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
        client = TelegramClient(
            StringSession(TG_SESSION),
            API_ID,
            API_HASH
        )
        await client.connect()
        offset_peer = await client.get_input_entity("telegram")

        result = await client(
            SearchPostsRequest(
                hashtag=hashtag,
                query=query,
                offset_rate=offset_rate,
                offset_peer=offset_peer,
                offset_id=offset_id,
                limit=5
            )
        )

        chat_map = {
            chat.id: chat
            for chat in result.chats
        }

        text_list = []

        for msg in result.messages:

            if not hasattr(msg.peer_id, "channel_id"):
                continue

            channel_id = msg.peer_id.channel_id

            if channel_id in blocked_channels:
                continue

            chat = chat_map.get(channel_id)

            if not chat:
                continue

            username = getattr(chat, "username", None)

            if not username:
                continue

            link = f"https://t.me/{username}/{msg.id}"

            content = msg.message or ""

            content = html.escape(content)

            text_list.append(
                f"频道ID:{channel_id}\n\n"
                f'<a href="{link}">{content}</a>'
            )

        if not text_list:
            message_text = "没有符合条件的结果"
        else:
            message_text = "\n\n----------------\n\n".join(text_list)

        next_rate = result.next_rate

        callback_data = None

        if next_rate:
            keyword = "#" + hashtag if hashtag else query

            callback_data = ",".join([
                keyword,
                str(next_rate),
                str(0)
            ])

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        body = {
            "chat_id": chat_id,
            "text": message_text,
            "parse_mode": "HTML"
        }

        if callback_data:
            body["reply_markup"] = {
                "inline_keyboard": [
                    [
                        {
                            "text": "下一页",
                            "callback_data": callback_data
                        }
                    ]
                ]
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
            "offset_rate": next_rate
        }

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

            asyncio.run(
                search_posts(
                    chat_id,
                    hashtag=search["hashtag"],
                    query=search["query"]
                )
            )

        callback_query = update.get("callback_query")

        if callback_query:
            chat_id = callback_query["message"]["chat"]["id"]

            data = callback_query["data"]

            keyword, offset_rate, offset_id = data.split(",")

            search = parse_search_text(keyword)

            asyncio.run(
                search_posts(
                    chat_id,
                    hashtag=search["hashtag"],
                    query=search["query"],
                    offset_rate=int(offset_rate),
                    offset_id=int(offset_id)
                )
            )

        self.send_response(200)

        self.end_headers()

        self.wfile.write(
            b"OK"
        )
