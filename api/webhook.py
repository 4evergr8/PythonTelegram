import os
import json
import urllib.request
from http.server import BaseHTTPRequestHandler


BOT_TOKEN = os.environ["BOT_TOKEN"]



def search_posts(chat_id, hashtag=None, query=None, offset_rate=0, offset_id=0):
    """
    搜索占位函数
    """

    text = (
        f"hashtag: {hashtag}\n"
        f"query: {query}\n"
        f"offset_rate: {offset_rate}\n"
        f"offset_id: {offset_id}"
    )


    next_offset_rate = offset_rate + 100
    next_offset_id = offset_id + 1


    callback_data = ",".join([
        hashtag if hashtag else query,
        str(next_offset_rate),
        str(next_offset_id)
    ])


    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


    data = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {
            "inline_keyboard": [
                [
                    {
                        "text": "下一页",
                        "callback_data": callback_data
                    }
                ]
            ]
        }
    }).encode()


    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json"
        }
    )


    urllib.request.urlopen(req)


    return {
        "offset_rate": next_offset_rate,
        "offset_id": next_offset_id
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