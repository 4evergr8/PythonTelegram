from telethon import TelegramClient, functions
from telethon.tl import types


client = TelegramClient(
    "session",
    api_id,
    api_hash
)






async def main():
    result = await client(
        functions.messages.SearchGlobalRequest(
            q="测试",
            broadcasts_only=True,
            filter=types.InputMessagesFilterEmpty(),
            min_date=None,
            max_date=None,
            offset_rate=0,
            offset_peer= types.InputPeerEmpty(),
            offset_id=0,
            limit=5
        )
    )
    print(result)

    for msg in result.messages:
        print("ID:", msg.id)
        print("内容:", msg.message)
        print("---")




with client:
    client.loop.run_until_complete(main())