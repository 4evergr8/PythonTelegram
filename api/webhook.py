import os
import json
import asyncio

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import SearchPostsRequest

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from aaa import blocked_channels


API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
TG_SESSION = os.environ["TG_SESSION"]


tg_client = TelegramClient(
    StringSession(TG_SESSION),
    API_ID,
    API_HASH
)


async def search_posts(
    chat_id,
    context,
    hashtag=None,
    query=None,
    offset_rate=0,
    offset_id=0
):

    await tg_client.connect()

    offset_peer = await tg_client.get_input_entity("telegram")


    result = await tg_client(
        SearchPostsRequest(
            hashtag=hashtag,
            query=query,
            offset_rate=offset_rate,
            offset_peer=offset_peer,
            offset_id=offset_id,
            limit=10
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

        text_list.append(
            f"频道ID:{channel_id}\n\n"
            f"[{content}]({link})"
        )


    if text_list:
        text = "\n\n----------------\n\n".join(text_list)
    else:
        text = "没有符合条件的结果"


    keyboard = None


    if result.next_rate:

        keyword = "#" + hashtag if hashtag else query

        callback_data = ",".join([
            keyword,
            str(result.next_rate),
            "0"
        ])


        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "下一页",
                        callback_data=callback_data
                    )
                ]
            ]
        )


    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )



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



async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    chat_id = update.message.chat.id

    text = update.message.text or ""


    search = parse_search_text(text)


    await search_posts(
        chat_id,
        context,
        hashtag=search["hashtag"],
        query=search["query"]
    )



async def callback_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query


    await context.bot.answer_callback_query(
        callback_query_id=query.id
    )


    chat_id = query.message.chat.id


    keyword, offset_rate, offset_id = query.data.split(",")


    search = parse_search_text(keyword)


    await search_posts(
        chat_id,
        context,
        hashtag=search["hashtag"],
        query=search["query"],
        offset_rate=int(offset_rate),
        offset_id=int(offset_id)
    )



application = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)


application.add_handler(
    MessageHandler(
        filters.TEXT,
        message_handler
    )
)


application.add_handler(
    CallbackQueryHandler(
        callback_handler
    )
)