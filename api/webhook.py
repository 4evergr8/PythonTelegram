import requests


BOT_TOKEN = "8241984939:AAF8JilTNlf7ucl5s8JB2z3EzBiRYqFFx48"


def handler(request):

    data = request.json()

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]

        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": "滚蛋"
            }
        )

    return {
        "statusCode": 200,
        "body": "ok"
    }