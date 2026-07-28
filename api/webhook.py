import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler


BOT_TOKEN = os.environ["BOT_TOKEN"]


def search_posts(hashtag=None, query=None, offset_rate=0, offset_id=0):
    """
    搜索占位函数
    """

    return {
        "text": (
            f"hashtag: {hashtag}\n"
            f"query: {query}\n"
            f"offset_rate: {offset_rate}\n"
            f"offset_id: {offset_id}"
        ),
        "offset_rate": offset_rate + 100,
        "offset_id": offset_id + 1
    }



def send_message(chat_id, text, callback_data=None):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


    data_body = {
        "chat_id": chat_id,
        "text": text
    }


    if callback_data:

        data_body["reply_markup"] = {
            "inline_keyboard": [
                [
                    {
                        "text": "下一页",
                        "callback_data": callback_data
                    }
                ]
            ]
        }


    data = json.dumps(data_body).encode()


    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json"
        }
    )


    urllib.request.urlopen(req)



def parse_search_text(text):

    # 去掉所有换行
    text = text.replace("\n", "")

    # 去掉首尾空格
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



        # 用户发送文本

        message = update.get("message")

        if message:

            chat_id = message["chat"]["id"]

            text = message.get("text", "")


            search = parse_search_text(text)


            result = search_posts(
                hashtag=search["hashtag"],
                query=search["query"]
            )


            callback_data = ",".join([
                search["keyword"],
                str(result["offset_rate"]),
                str(result["offset_id"])
            ])


            send_message(
                chat_id,
                result["text"],
                callback_data
            )



        # 用户点击下一页

        callback_query = update.get("callback_query")

        if callback_query:

            chat_id = callback_query["message"]["chat"]["id"]

            data = callback_query["data"]


            keyword, offset_rate, offset_id = data.split(",")


            search = parse_search_text(keyword)


            result = search_posts(
                hashtag=search["hashtag"],
                query=search["query"],
                offset_rate=int(offset_rate),
                offset_id=int(offset_id)
            )


            callback_data = ",".join([
                keyword,
                str(result["offset_rate"]),
                str(result["offset_id"])
            ])


            send_message(
                chat_id,
                result["text"],
                callback_data
            )



        self.send_response(200)

        self.end_headers()

        self.wfile.write(
            b"OK"
        )