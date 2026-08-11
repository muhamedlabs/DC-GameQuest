import sys 
import asyncio
import disnake
from disnake.ext import commands
from BANNED_FILES.config import ERROR_CHANNEL_ID, Embed_Color, Error_Timer
from commands.information_cog.time import current_time as get_current_time, parse_time
import aiohttp
import logging


class StreamDuplicator:
    def __init__(self, bot, channel_id):
        self.bot = bot
        self.channel_id = channel_id
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.buffer = ""

        self.webhook = None
        self.bot_avatar: bytes = b""
        self.start_time = None 
        self.last_message = None 

    def start(self):
        self.start_time = parse_time(get_current_time())
        sys.stdout = self
        sys.stderr = self

    def stop(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

    def write(self, text):
        self.original_stdout.write(text)
        self.original_stdout.flush()

        self.buffer += text
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            line = line.strip()
            if line:
                if self.start_time is not None:
                    elapsed = (parse_time(get_current_time()) - self.start_time).total_seconds()
                    if elapsed < Error_Timer:
                        continue
                try:
                    loop = asyncio.get_event_loop()
                    if not loop.is_closed():
                        loop.create_task(self.send_to_discord(line))
                except RuntimeError:
                    pass  

    def flush(self):
        self.original_stdout.flush()

    async def prepare(self):
        await self.bot.wait_until_ready()
        await self.cache_bot_avatar()

    async def cache_bot_avatar(self):
        url = self.bot.user.avatar.url if self.bot.user.avatar else self.bot.user.default_avatar.url
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    self.bot_avatar = await resp.read()
        except Exception as e:
            print(f"[ErrorLogger] Ошибка при загрузке аватарки бота: {e}")

    async def ensure_webhook(self):
        if self.webhook:
            return self.webhook

        if self.bot.is_closed():
            return None

        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            print("[ErrorLogger] Канал не найден")
            return None

        webhook_name = f"{self.bot.user.name}_Error"

        try:
            webhooks = await channel.webhooks()
            for wh in webhooks:
                if wh.name == webhook_name:
                    self.webhook = wh
                    return self.webhook

            self.webhook = await channel.create_webhook(name=webhook_name, avatar=self.bot_avatar)
            return self.webhook
        except disnake.Forbidden:
            print(f"[ErrorLogger] Нет прав на создание вебхука в канале {channel.id}")
        except Exception as e:
            print(f"[ErrorLogger] Ошибка при создании вебхука: {e}")
        return None

    async def send_to_discord(self, text):
        text = text.strip()
        if not text:
            return

        if text == self.last_message:
            return
        self.last_message = text

        try:
            await self.bot.wait_until_ready()
            webhook = await self.ensure_webhook()
            if not webhook:
                return

            max_len = 3900
            description = (
                text[:max_len] + "\n\n... продолжение в терминале"
                if len(text) > max_len else text
            )

            current_time = get_current_time()

            embed = disnake.Embed(
                title="<:cpusetting:1387061989179658271> Критический отчёт системы военной связи",
                description=f"```{description}```\n<:calendar:1390972430780203058> **Время отчёта:** {current_time} по МСК",
                color=disnake.Color(int(Embed_Color.lstrip("#"), 16))
            )

            await webhook.send(embed=embed, username=webhook.name)
        except Exception as e:
            print(f"[ErrorLogger] Ошибка отправки через вебхук: {e}")


class ErrorLogger(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.stream_duplicator = StreamDuplicator(bot, ERROR_CHANNEL_ID)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.stream_duplicator.prepare()
        self.stream_duplicator.start()

    def cog_unload(self):
        self.stream_duplicator.stop()