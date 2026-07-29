import asyncio
import json
import os
import re
from http.server import BaseHTTPRequestHandler

import telebot
from telebot import types as bot_types

from telethon import TelegramClient, functions
from telethon.sessions import StringSession
from telethon.tl import types


def get_media_emoji(msg):
    emojis = []

    if not msg.media:
        return ""

    if isinstance(
            msg.media,
            types.MessageMediaPhoto
    ):
        emojis.append("🖼️")

    if isinstance(
            msg.media,
            types.MessageMediaDocument
    ):

        document = msg.media.document

        for attr in document.attributes:

            if isinstance(
                    attr,
                    types.DocumentAttributeVideo
            ):
                emojis.append("🎬")

            if isinstance(
                    attr,
                    types.DocumentAttributeAudio
            ):
                emojis.append("🎵")

        if not emojis:
            emojis.append("📁")

    return "".join(emojis)


API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
TG_SESSION = os.environ["TG_SESSION"]

bot = telebot.TeleBot(BOT_TOKEN)


def get_search_filter(file_type):
    if file_type == "image":
        return types.InputMessagesFilterPhotos()

    if file_type == "video":
        return types.InputMessagesFilterVideo()

    if file_type == "music":
        return types.InputMessagesFilterMusic()

    if file_type == "file":
        return types.InputMessagesFilterDocument()

    return types.InputMessagesFilterEmpty()


def create_keyboard(
        query,
        file_type,
        next_rate=None,
        next_id=0
):
    keyboard = bot_types.InlineKeyboardMarkup()

    keyboard.row(
    bot_types.InlineKeyboardButton(
            text="♾️",
            callback_data=f"{query},all,0,0"
        ),
        bot_types.InlineKeyboardButton(
            text="🖼",
            callback_data=f"{query},image,0,0"
        ),
        bot_types.InlineKeyboardButton(
            text="🎬",
            callback_data=f"{query},video,0,0"
        ),
        bot_types.InlineKeyboardButton(
            text="🎵",
            callback_data=f"{query},music,0,0"
        ),
        bot_types.InlineKeyboardButton(
            text="📁",
            callback_data=f"{query},file,0,0"
        ),

    )

    if next_rate:
        keyboard.row(
            bot_types.InlineKeyboardButton(
                text="➡️",
                callback_data=(
                    f"{query},"
                    f"{file_type},"
                    f"{next_rate},"
                    f"{next_id}"
                )
            )
        )

    return keyboard


async def search_posts(
        chat_id,
        query,
        file_type="all",
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
                filter=get_search_filter(file_type),
                min_date=None,
                max_date=None,
                offset_rate=offset_rate,
                offset_peer=types.InputPeerEmpty(),
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

                if not hasattr(
                        msg.peer_id,
                        "channel_id"
                ):
                    continue

                chat = chat_map.get(
                    msg.peer_id.channel_id
                )

                if not chat:
                    continue

                username = getattr(
                    chat,
                    "username",
                    None
                )

                if not username:
                    continue

                link = (
                    f"https://t.me/"
                    f"{username}/"
                    f"{msg.id}"
                )

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

                if re.search(
                        pattern,
                        content
                ):
                    continue

                content = content[:20]

                emoji = get_media_emoji(msg)

                prefix = (
                    emoji + " "
                    if emoji
                    else ""
                )

                text_list.append(
                    f"{prefix}[{content}]({link})"
                )

            if text_list:

                text = "\n".join(
                    text_list
                )

            else:

                text = "没有符合条件的结果"

            next_rate = getattr(
                result,
                "next_rate",
                None
            )

            next_id = 0

        keyboard = create_keyboard(
            query,
            file_type,
            next_rate,
            next_id
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



    except Exception as e:

        print(e)

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

        body = self.rfile.read(
            length
        )

        update = json.loads(
            body
        )

        message = update.get(
            "message"
        )

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

            query, file_type, offset_rate, offset_id = data.split(",")

            asyncio.run(
                search_posts(
                    chat_id,
                    query,
                    file_type=file_type,
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
