
from telethon import TelegramClient
from telethon.sessions import StringSession



# 加载现有的文件会话
with TelegramClient("session.session", api_id, api_hash) as client:
    # 将当前的会话导出为字符串
    session_string = StringSession.save(client.session)

    print("\n--- 转换成功！你的字符串登录凭证如下 ---")
    print(session_string)
    print("-------------------------------------------\n")
    print("提示：现在你可以复制这段字符串去其他地方使用了，原本的 .session 文件不会受到影响。")
