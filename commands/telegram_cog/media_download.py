import os
import uuid
import asyncio
from typing import Optional, Tuple
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto
from telethon.errors.rpcerrorlist import TimeoutError

from BANNED_FILES.config import Download_Temp, File_Telegram


async def download_media(
    message,
    client: TelegramClient,
    retries: int = 3,
    delay: int = 5,
    max_file_size: int = File_Telegram,
) -> Tuple[Optional[str], Optional[str]]:
    
    file_size = getattr(getattr(message, "file", None), "size", None)
    if file_size and file_size > max_file_size:
        print(f"Медиафайл слишком большой для Discord ({file_size} байт, лимит {max_file_size}) — пропускаем загрузку")
        return None, "too_large"

    ext = ".jpg" if isinstance(message.media, MessageMediaPhoto) else ""
    filename = f"media_{message.id}_{uuid.uuid4().hex}{ext}"
    path = os.path.join(Download_Temp, filename)

    for attempt in range(1, retries + 1):
        try:
            file_path = await client.download_media(message, file=path)
            if file_path:
                return file_path, None
        except TimeoutError:
            print(f"Таймаут при загрузке медиа (попытка {attempt}/{retries})")
        except Exception as e:
            print(f"Неожиданная ошибка при загрузке медиа: {e}")
            break

        if attempt < retries:
            await asyncio.sleep(delay)

    print("Не удалось загрузить медиа после всех попыток")
    return None, "download_error"
