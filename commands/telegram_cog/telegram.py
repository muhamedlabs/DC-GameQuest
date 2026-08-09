import os
import asyncio
from typing import Optional
import disnake
from disnake.ext import commands
from disnake.errors import HTTPException
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaWebPage
from BANNED_FILES.config import api_id, api_hash, telegram_bot, TELEGRAM_ID, TELEGRAM_DISCORD_CHANNEL_ID, Embed_Color, Telegram_Gif, File_Telegram, Limit_Telegram, Telegram_Title, Telegram_Text

from commands.telegram_cog.text_formatting import format_telegram_message, escape_markdown
from commands.telegram_cog.media_download import download_media
from commands.telegram_cog.database_loading import RedisMessageMapper

telegram_client = TelegramClient("telegram_session", api_id, api_hash, timeout=120)


class TelegramBridge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_mapper = RedisMessageMapper(bot=self.bot)
        self.grouped_media = {}
        self.grouped_tasks = {}
        self.discord_channel = None
        self.telegram_chat_entity = None

        self.bot.loop.create_task(self.init_telegram())
        self.bot.loop.create_task(self.cache_discord_channel())

    async def cog_load(self):
        pass  # если нужно, добавь инициализацию здесь

    def cog_unload(self):
        # безопасное завершение через create_task
        asyncio.create_task(self.shutdown_telegram())
        asyncio.create_task(self.message_mapper.close())

    async def shutdown_telegram(self):
        try:
            await telegram_client.disconnect()
            print("Telegram client disconnected.")
        except Exception as e:
            print(f"Ошибка при отключении telegram_client: {e}")

    async def init_telegram(self):
        await self.bot.wait_until_ready()
        await telegram_client.start(bot_token=telegram_bot)

        try:
            self.telegram_chat_entity = await telegram_client.get_entity(TELEGRAM_ID)
        except Exception as e:
            print(f"Не удалось получить информацию о Telegram-чате для ссылок: {e}")

        telegram_client.add_event_handler(self.handle_new_message, events.NewMessage(chats=TELEGRAM_ID))
        telegram_client.add_event_handler(self.handle_edit, events.MessageEdited(chats=TELEGRAM_ID))
        telegram_client.add_event_handler(self.handle_delete, events.MessageDeleted(chats=TELEGRAM_ID))
        print("Telegram client started successfully!")
        asyncio.create_task(telegram_client.run_until_disconnected())

    async def cache_discord_channel(self):
        await self.bot.wait_until_ready()
        self.discord_channel = self.bot.get_channel(TELEGRAM_DISCORD_CHANNEL_ID)

    def build_telegram_link(self, message_id: int) -> Optional[str]:
        entity = self.telegram_chat_entity
        if not entity:
            return None
        username = getattr(entity, "username", None)
        if username:
            return f"https://t.me/{username}/{message_id}"
        entity_id = getattr(entity, "id", None)
        if entity_id is None:
            return None
        return f"https://t.me/c/{entity_id}/{message_id}"

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

    async def build_failed_media_components(self, failed_media, telegram_texts):
        original_text = telegram_texts[0] if telegram_texts else ""
        words = original_text.split()
        excerpt = " ".join(words[:Limit_Telegram])
        if len(words) > Limit_Telegram:
            excerpt += "…"
        excerpt = escape_markdown(excerpt) if excerpt else ""

        description = Telegram_Text
        if excerpt:
            description += f"\n\nФрагмент информационной сводки из Telegram-канала:\n«{excerpt}»"

        link = self.build_telegram_link(failed_media[0][0])

        container_children = [
            disnake.ui.TextDisplay(f"**{Telegram_Title}**"),
            disnake.ui.Separator(),
            disnake.ui.TextDisplay(description),
        ]

        gif_file = None
        if Telegram_Gif and os.path.isfile(Telegram_Gif):
            gif_filename = os.path.basename(Telegram_Gif)
            gif_file = disnake.File(Telegram_Gif, filename=gif_filename)
            container_children.append(
                disnake.ui.MediaGallery(disnake.MediaGalleryItem(media=f"attachment://{gif_filename}"))
            )
        elif Telegram_Gif:
            print(f"Telegram_Gif вказує на неіснуючий локальний файл: {Telegram_Gif}")

        container_children.append(disnake.ui.Separator())
        container_children.append(
            disnake.ui.TextDisplay("-# Благодарим за проявленный интерес к нашему спецпроекту!")
        )

        if link:
            container_children.append(
                disnake.ui.ActionRow(disnake.ui.Button(label="Переглянути в Telegram", url=link))
            )

        container = disnake.ui.Container(
            *container_children,
            accent_colour=disnake.Color(int(Embed_Color.lstrip("#"), 16)),
        )

        return [container], gif_file

    async def send_to_discord(self, events):
        channel = self.discord_channel or self.bot.get_channel(TELEGRAM_DISCORD_CHANNEL_ID)
        if not channel:
            return

        guild = getattr(channel, "guild", None)
        max_file_size = guild.filesize_limit if guild else File_Telegram

        raw_content = ""
        files = []
        telegram_message_ids = []
        telegram_texts = []
        failed_media = []  # список (telegram_message_id, reason)

        for event in events:
            msg = event.message
            telegram_message_ids.append(msg.id)

            if not raw_content and msg.message:
                raw_content = format_telegram_message(msg.message, msg.entities or [])
                telegram_texts.append(msg.message)
            elif msg.message:
                telegram_texts.append(msg.message)

            if msg.media and not isinstance(msg.media, MessageMediaWebPage):
                file_path, error_reason = await download_media(
                    msg, telegram_client, max_file_size=max_file_size
                )
                if file_path:
                    spoiler = bool(getattr(msg.media, "spoiler", False))
                    files.append(disnake.File(file_path, spoiler=spoiler))
                else:
                    failed_media.append((msg.id, error_reason))

        try:
            if failed_media and not files:
                components, gif_file = await self.build_failed_media_components(failed_media, telegram_texts)
                discord_msg = await channel.send(
                    components=components,
                    file=gif_file,
                    flags=disnake.MessageFlags(is_components_v2=True),
                )
            else:
                content = raw_content[:2000] if raw_content else None
                discord_msg = await channel.send(content=content, files=files[:10] or None)

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