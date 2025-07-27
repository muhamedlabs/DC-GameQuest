import os
import uuid
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto

from BANNED_FILES.config import Download_Temp

async def download_media(message, client: TelegramClient):
    try:
        ext = ".jpg" if isinstance(message.media, MessageMediaPhoto) else ""
        filename = f"media_{message.id}_{uuid.uuid4().hex}{ext}"
        path = os.path.join(Download_Temp, filename)
        return await client.download_media(message, file=path)
    except Exception as e:
        print(f"Ошибка загрузки медиа: {e}")
        return None
