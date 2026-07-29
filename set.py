import requests


url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"

response = requests.post(
    url,
    data={
        "url": WEBHOOK_URL
    }
)

print(response.json())