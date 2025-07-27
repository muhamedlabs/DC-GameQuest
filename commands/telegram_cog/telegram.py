import os
import asyncio
import disnake
from disnake.ext import commands
from disnake.errors import HTTPException
from telethon import TelegramClient, events
from BANNED_FILES.config import api_id, api_hash, telegram_bot, TELEGRAM_ID, TELEGRAM_DISCORD_CHANNEL_ID

from commands.telegram_cog.text_formatting import format_telegram_message
from commands.telegram_cog.media_download import download_media
from commands.telegram_cog.database_loading import RedisMessageMapper

telegram_client = TelegramClient("telegram_session", api_id, api_hash)


class TelegramBridge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_mapper = RedisMessageMapper(bot=self.bot)
        self.grouped_media = {}
        self.grouped_tasks = {}
        self.discord_channel = None

        self.bot.loop.create_task(self.init_telegram())
        self.bot.loop.create_task(self.cache_discord_channel())

    async def cog_load(self):
        pass  # если есть нужда, можно добавить

    async def cog_unload(self):
        pass  # если есть нужда, можно добавить

    async def init_telegram(self):
        await self.bot.wait_until_ready()
        await telegram_client.start(bot_token=telegram_bot)
        telegram_client.add_event_handler(self.handle_new_message, events.NewMessage(chats=TELEGRAM_ID))
        telegram_client.add_event_handler(self.handle_edit, events.MessageEdited(chats=TELEGRAM_ID))
        telegram_client.add_event_handler(self.handle_delete, events.MessageDeleted(chats=TELEGRAM_ID))
        print("Telegram client started successfully!")
        asyncio.create_task(telegram_client.run_until_disconnected())

    async def cache_discord_channel(self):
        await self.bot.wait_until_ready()
        self.discord_channel = self.bot.get_channel(TELEGRAM_DISCORD_CHANNEL_ID)

    async def handle_new_message(self, event):
        grouped_id = getattr(event.message, "grouped_id", None)

        if grouped_id:
            self.grouped_media.setdefault(grouped_id, []).append(event)
            if grouped_id in self.grouped_tasks:
                self.grouped_tasks[grouped_id].cancel()

            self.grouped_tasks[grouped_id] = asyncio.create_task(self.finalize_album(grouped_id))
        else:
            await self.send_to_discord([event])

    async def finalize_album(self, grouped_id):
        await asyncio.sleep(2.5)
        events = self.grouped_media.pop(grouped_id, [])
        self.grouped_tasks.pop(grouped_id, None)
        if events:
            await self.send_to_discord(events)

    async def send_to_discord(self, events):
        content = ""
        files = []
        telegram_message_ids = []
        telegram_texts = []

        for event in events:
            msg = event.message
            telegram_message_ids.append(msg.id)

            if not content and msg.message:
                formatted = format_telegram_message(msg.message, msg.entities or [])[:2000]
                content = formatted
                telegram_texts.append(msg.message)
            elif msg.message:
                telegram_texts.append(msg.message)

            if msg.media:
                file_path = await download_media(msg, telegram_client)
                if file_path:
                    files.append(disnake.File(file_path))

        channel = self.discord_channel or self.bot.get_channel(TELEGRAM_DISCORD_CHANNEL_ID)
        if not channel:
            return

        try:
            discord_msg = await channel.send(content=content or None, files=files[:10] or None)
            await self.message_mapper.add_message_mapping(telegram_message_ids, discord_msg.id, telegram_texts)
        except HTTPException as e:
            if e.code == 40005:
                print(f"Ошибка отправки в Discord: {e} — файл слишком большой или сообщение превышает лимит.")
            else:
                print(f"Ошибка отправки в Discord: {e}")
        except Exception as e:
            print(f"Ошибка отправки в Discord: {e}")
        finally:
            for f in files:
                try:
                    os.remove(f.fp.name)
                except Exception as e:
                    print(f"Ошибка удаления файла {f.fp.name}: {e}")

    async def handle_edit(self, event):
        discord_id = await self.message_mapper.get_discord_message_id(event.message.id)
        if not discord_id:
            return

        channel = self.discord_channel or self.bot.get_channel(TELEGRAM_DISCORD_CHANNEL_ID)
        if not channel:
            return

        try:
            content = format_telegram_message(event.message.message, event.message.entities or [])[:2000]
            msg = await channel.fetch_message(discord_id)
            await msg.edit(content=content)
        except Exception as e:
            print(f"Ошибка редактирования: {e}")

    async def handle_delete(self, event):
        channel = self.discord_channel or self.bot.get_channel(TELEGRAM_DISCORD_CHANNEL_ID)
        if not channel:
            return

        for msg_id in event.deleted_ids:
            discord_id = await self.message_mapper.remove_message_mapping(msg_id)
            if not discord_id:
                continue
            try:
                msg = await channel.fetch_message(discord_id)
                await msg.delete()
            except Exception as e:
                print(f"Ошибка удаления: {e}")
