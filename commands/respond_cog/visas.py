import disnake
from disnake.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta
import logging
from dataclasses import asdict

from BANNED_FILES.config import Embed_Color, ALLOWED_USER_IDS, RedisManager
from redis_storage.bot_information import BotInformation

logger = logging.getLogger(__name__)

class ResponseToCall(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        self.lock = asyncio.Lock()
        self.update_ping_task.start()

    async def cog_load(self):
        """Запускаем инициализацию после загрузки COG"""
        self.bot.loop.create_task(self.initialize_bot_info())

    def cog_unload(self):
        """Корректно останавливаем таск при выгрузке COG"""
        if self.update_ping_task.is_running():
            self.update_ping_task.cancel()

    def get_moscow_time_str(self):
        """Возвращает московское время в формате DD.MM.YYYYг HHч MMм SSс"""
        now = datetime.utcnow() + timedelta(hours=3)
        return f"{now.day:02}.{now.month:02}.{now.year}г {now.hour:02}ч {now.minute:02}м {now.second:02}с"

    async def initialize_bot_info(self):
        """Инициализация/обновление данных бота в Redis"""
        await self.bot.wait_until_ready()
        key = [str(self.bot.user.id)]

        async with self.lock:
            async with RedisManager() as redis:
                bot_record = BotInformation(
                    bot_id=str(self.bot.user.id),
                    username=str(self.bot.user),
                    uptime_time=self.get_moscow_time_str(),
                    latency=f"{round(self.bot.latency * 1000)} мс"
                )
                await redis.save(bot_record, key)
                logger.info(f"Bot info обновлён в Redis: {asdict(bot_record)}")

    async def get_bot_info(self) -> BotInformation:
        """Получение информации о боте из Redis"""
        key = [str(self.bot.user.id)]
        async with self.lock:
            async with RedisManager() as redis:
                data = await redis.load(BotInformation, key)
                if data is None:
                    await self.initialize_bot_info()
                    data = await redis.load(BotInformation, key)
        return data

    async def send_info_embed(self, target, author, guild):
        """Отправка эмбеда с информацией о боте"""
        bot_info = await self.get_bot_info()

        start_time = datetime.strptime(bot_info.uptime_time, "%d.%m.%Yг %Hч %Mм %Sс")
        now = datetime.utcnow() + timedelta(hours=3)
        uptime = now - start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}д {hours}ч {minutes}м {seconds}с"

        owner_mentions = []
        for uid in ALLOWED_USER_IDS:
            member = guild.get_member(uid)
            owner_mentions.append(member.mention if member else f"<@{uid}>")

        embed = disnake.Embed(
            title=f"<:airdrop:1390972469073936414> Штаб зафиксировал ваше имя — {author.display_name}!",
            description=(
                "Здравия желаю! Я на связи и всегда готов внести вклад в проект **Game Quest**.\n\n"
                f">>> Мой военный пинг: `{bot_info.latency}`\n"
                f"Время несения службы: `{uptime_str}`\n"
                f"Мои создатели: {', '.join(owner_mentions)}\n"
                f"Website Muhameda: https://muhamedlabs.pro"
            ),
            color=self.embed_color
        )

        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)

        await target.send(embed=embed)

    @commands.command(
        name="gamequest",
        aliases=["game_quest"],
        help="Передача информации о сержанте (боте)"
    )
    async def gamequest_command(self, ctx: commands.Context):
        try:
            await self.send_info_embed(ctx, ctx.author, ctx.guild)
        except disnake.Forbidden:
            logger.warning(f"Нет прав для отправки сообщения пользователю {ctx.author}")
        except Exception as e:
            logger.error(f"Ошибка в gamequest_command: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot or not message.guild:
            return
        if message.content.strip().lower() == "!game quest":
            ctx = await self.bot.get_context(message)
            if ctx.command is None:
                await self.gamequest_command(ctx)

    @tasks.loop(hours=5)
    async def update_ping_task(self):
        """Обновляем пинг и московское время каждые 5 часов"""
        key = [str(self.bot.user.id)]
        bot_info = await self.get_bot_info()
        bot_info.latency = f"{round(self.bot.latency * 1000)} мс"
        bot_info.uptime_time = self.get_moscow_time_str()

        async with self.lock:
            async with RedisManager() as redis:
                await redis.save(bot_info, key)
        logger.info(f"Bot ping и время обновлены в Redis: {bot_info.latency}, {bot_info.uptime_time}")

    @update_ping_task.before_loop
    async def before_update_ping_task(self):
        await self.bot.wait_until_ready()
