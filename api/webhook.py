import asyncio
import json
import os
import re
from http.server import BaseHTTPRequestHandler

import telebot
from telebot import types as bot_types

from telethon import TelegramClient, functions
from telethon.sessions import StringSession
from telethon.tl import types as tg_types



API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
TG_SESSION = os.environ["TG_SESSION"]

bot = telebot.TeleBot(BOT_TOKEN)


async def search_posts(
        chat_id,
        query,
        offset_rate=0,
        offset_id=0,
        callback_query_id=None
):
    try:
        client = TelegramClient(
            StringSession(TG_SESSION),
            API_ID,
            API_HASH
        )

        await client.connect()

        result = await client(
            functions.messages.SearchGlobalRequest(
                q=query,
                broadcasts_only=True,
                filter=tg_types.InputMessagesFilterEmpty(),
                min_date=None,
                max_date=None,
                offset_rate=offset_rate,
                offset_peer=tg_types.InputPeerEmpty(),
                offset_id=offset_id,
                limit=100
            )
        )

        if not result.messages:
            text = "没有符合条件的结果"
            next_rate = None
            next_id = 0

        else:
            chat_map = {
                chat.id: chat
                for chat in result.chats
            }

            text_list = []

            for msg in result.messages:

                if not hasattr(msg.peer_id, "channel_id"):
                    continue

                channel_id = msg.peer_id.channel_id

                chat = chat_map.get(channel_id)

                if not chat:
                    continue

                username = getattr(
                    chat,
                    "username",
                    None
                )

                if not username:
                    continue

                link = f"https://t.me/{username}/{msg.id}"

                content = (
                    msg.message or ""
                ).replace(
                    "\n",
                    ""
                ).replace(
                    " ",
                    ""
                )

                pattern = re.compile(
                    r"[^\w\u4e00-\u9fff]{4,}"
                )

                if re.search(pattern, content):
                    continue

                content = content[:20]

                text_list.append(
                    f"[{content}]({link})"
                )

            if text_list:
                text = "\n".join(text_list)
            else:
                text = "没有符合条件的结果"

            next_rate = result.next_rate
            next_id = 0

        keyboard = None

        if next_rate:
            callback_data = ",".join(
                [
                    query,
                    str(next_rate),
                    str(next_id)
                ]
            )

            keyboard = bot_types.InlineKeyboardMarkup()

            keyboard.add(
                bot_types.InlineKeyboardButton(
                    text="下一页",
                    callback_data=callback_data
                )
            )

        if callback_query_id:
            bot.answer_callback_query(
                callback_query_id
            )

        bot.send_message(
            chat_id,
            text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )

        client.disconnect()
        raise 'fdcsfsgsgbs'

    except Exception as e:
        bot.send_message(
            chat_id,
            f"搜索出错:\n\n{str(e)}"
        )


def parse_search_text(text):
    return text.strip()


class handler(BaseHTTPRequestHandler):

    def do_POST(self):

        length = int(
            self.headers.get(
                "Content-Length",
                0
            )
        )

        body = self.rfile.read(length)

        update = json.loads(body)

        message = update.get("message")

        if message:
            chat_id = message["chat"]["id"]

            text = message.get(
                "text",
                ""
            )

            query = parse_search_text(
                text
            )

            asyncio.run(
                search_posts(
                    chat_id,
                    query
                )
            )

        callback_query = update.get(
            "callback_query"
        )

        if callback_query:

            chat_id = callback_query["message"]["chat"]["id"]

            data = callback_query["data"]

            query, offset_rate, offset_id = data.split(",")

            asyncio.run(
                search_posts(
                    chat_id,
                    query,
                    offset_rate=int(offset_rate),
                    offset_id=int(offset_id),
                    callback_query_id=callback_query["id"]
                )
            )

        self.send_response(200)

        self.end_headers()

        self.wfile.write(
            b"OK"
        )