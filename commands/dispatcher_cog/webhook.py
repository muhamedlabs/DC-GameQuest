import re
import json
import aiohttp
import disnake
from disnake.ext import commands, tasks
from io import BytesIO
from datetime import datetime, timezone, timedelta

from BANNED_FILES.config import GROUP_MODER_IDS, RedisManager
from redis_storage.dispatcher_message import DispatcherMessage

MSK = timezone(timedelta(hours=3))
message_lifetime = timedelta(hours=48)

class WebhookFromDiscord(commands.Cog):
    def __init__(self, bot: commands.InteractionBot):
        self.bot = bot
        self.cached_payloads = {}  # кеш JSON + файлы
        self.watch_messages.start()  # запуск автообновления

    def parse_message_link(self, link: str) -> tuple[int, int]:
        match = re.match(r"https://discord\.com/channels/\d+/(\d+)/(\d+)", link)
        if not match:
            raise ValueError("Неверная ссылка Discord")
        return int(match.group(1)), int(match.group(2))

    async def fetch_payload_and_files(self, channel_id: int, message_id: int):
        if message_id in self.cached_payloads:
            return self.cached_payloads[message_id]

        channel = self.bot.get_channel(channel_id)
        if not channel:
            raise RuntimeError("Канал не найден")

        message = await channel.fetch_message(message_id)
        payload = None
        files = []

        async with aiohttp.ClientSession() as session:
            for att in message.attachments:
                if att.filename.endswith(".json"):
                    async with session.get(att.url) as resp:
                        text = await resp.text()
                        payload = json.loads(text)
                else:
                    async with session.get(att.url) as resp:
                        data = await resp.read()
                        files.append(disnake.File(BytesIO(data), filename=att.filename))

        if payload is None:
            match = re.search(r"```json(.*?)```", message.content, re.S)
            if not match:
                raise RuntimeError("JSON не найден в сообщении")
            payload = json.loads(match.group(1).strip())

        # замена attachment:// на файлы
        for embed in payload.get("embeds", []):
            if "image" in embed and embed["image"]["url"].startswith("attachment://"):
                filename = embed["image"]["url"].replace("attachment://", "")
                for f in files:
                    if f.filename == filename:
                        embed["image"]["url"] = f"attachment://{filename}"
            if "thumbnail" in embed and embed["thumbnail"]["url"].startswith("attachment://"):
                filename = embed["thumbnail"]["url"].replace("attachment://", "")
                for f in files:
                    if f.filename == filename:
                        embed["thumbnail"]["url"] = f"attachment://{filename}"

        self.cached_payloads[message_id] = (payload, files)
        return payload, files

    def build_embeds(self, embed_data: list) -> list:
        embeds = []
        for e in embed_data:
            embed = disnake.Embed(
                title=e.get("title"),
                description=e.get("description"),
                color=e.get("color")
            )
            if "image" in e:
                embed.set_image(url=e["image"]["url"])
            if "thumbnail" in e:
                embed.set_thumbnail(url=e["thumbnail"]["url"])
            if "footer" in e:
                embed.set_footer(text=e["footer"].get("text"))
            for field in e.get("fields", []):
                embed.add_field(
                    name=field["name"],
                    value=field["value"],
                    inline=field.get("inline", False)
                )
            embeds.append(embed)
        return embeds

    def build_components(self, components_data: list):
        rows = []
        for row in components_data:
            buttons = []
            for c in row.get("components", []):
                if c["type"] == 2:
                    buttons.append(
                        disnake.ui.Button(
                            label=c.get("label"),
                            url=c.get("url"),
                            style=disnake.ButtonStyle.link
                        )
                    )
            rows.append(disnake.ui.ActionRow(*buttons))
        return rows

    @commands.slash_command(
        name="webhook",
        description="Бот отправляет сообщение по Discohook JSON из Discord",
        default_member_permissions=disnake.Permissions(manage_messages=True)
    )
    async def send_from_message(
        self,
        inter: disnake.ApplicationCommandInteraction,
        message_link: str = commands.Param(
            name="ссылка",
            description="Ссылка на сообщение с Discohook JSON"
        ),
        target_channel: disnake.TextChannel = commands.Param(
            name="канал",
            description="Канал для отправки"
        )
    ):
        if not any(role.id in GROUP_MODER_IDS for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде", ephemeral=True)
            return

        await inter.response.defer(ephemeral=True)

        try:
            source_channel_id, file_id = self.parse_message_link(message_link)
            payload, files = await self.fetch_payload_and_files(source_channel_id, file_id)

            embeds = self.build_embeds(payload.get("embeds", []))
            components = self.build_components(payload.get("components", []))

            sent_message: disnake.Message = await target_channel.send(
                content=payload.get("content"),
                embeds=embeds,
                components=components,
                files=files
            )

            record = DispatcherMessage(
                id=str(sent_message.id)[:8],
                file_id=str(file_id),
                source_id=str(source_channel_id),
                message_id=str(sent_message.id),
                channel_id=str(target_channel.id),
                user_id=str(inter.author.id),
                username=inter.author.name,
                timestamp=datetime.now(MSK).strftime("%d.%m.%Y %H:%M:%S")
            )

            async with RedisManager() as redis:
                await redis.save(record, key=f"webhook:{record.id}", ttl=message_lifetime)

            await inter.edit_original_response(
                f"Сообщение успешно отправлено в {target_channel.mention}"
            )

        except Exception as e:
            await inter.edit_original_response(f"Ошибка: {e}")

    @tasks.loop(seconds=35)
    async def watch_messages(self):
        async with RedisManager() as redis:
            records = await redis.load_many(DispatcherMessage, "webhook:*")
            for record in records:
                try:
                    src_channel = self.bot.get_channel(int(record.source_id))
                    if not src_channel:
                        continue
                    # Проверяем, существует ли оригинальное сообщение
                    try:
                        await src_channel.fetch_message(int(record.file_id))
                    except disnake.NotFound:
                        # если оригинал удален — удаляем сообщение бота
                        target_channel = self.bot.get_channel(int(record.channel_id))
                        if target_channel:
                            try:
                                msg = await target_channel.fetch_message(int(record.message_id))
                                await msg.delete()
                            except:
                                pass
                        await redis.delete(DispatcherMessage, key=f"webhook:{record.id}")
                except:
                    continue

    @watch_messages.before_loop
    async def before_watch(self):
        await self.bot.wait_until_ready()
