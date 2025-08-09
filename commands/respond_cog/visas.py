import disnake
from disnake.ext import commands
import datetime
import logging

from BANNED_FILES.config import Embed_Color, ALLOWED_USER_IDS

logger = logging.getLogger(__name__)

class ResponseToCall(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        if not hasattr(self.bot, "start_time"):
            self.bot.start_time = datetime.datetime.utcnow()

    async def send_info_embed(self, target, author, guild):
        latency = round(self.bot.latency * 1000)
        now = datetime.datetime.utcnow()
        uptime = now - getattr(self.bot, "start_time", now)
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
                f">>> Мой военный пинг:  `{latency} мс`\n"
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
        help="Передача информации о сержанта (бота)"
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

        content = message.content.strip().lower()
        # Лучше ловить префиксы через commands.Bot, но если так:
        if content == "!game quest":
            ctx = await self.bot.get_context(message)
            if ctx.command is None:  # Чтобы не вызвать команду дважды, если уже существует
                await self.gamequest_command(ctx)
