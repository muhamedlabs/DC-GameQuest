import disnake
from disnake.ext import commands
import datetime

from BANNED_FILES.config import Embed_Color, ALLOWED_USER_IDS

class ResponseToCall(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = disnake.Color(int(Embed_Color.lstrip("#"), 16))
        # Инициализация времени старта
        if not hasattr(self.bot, "start_time"):
            self.bot.start_time = datetime.datetime.utcnow()

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        # Игнорируем ботов и личные сообщения
        if message.author.bot or not message.guild:
            return

        # Проверка точной команды (без учета регистра и пробелов в начале/конце)
        if message.content.strip().lower() != "!game quest":
            return

        # Пинг бота в миллисекундах
        latency = round(self.bot.latency * 1000)

        now = datetime.datetime.utcnow()
        uptime = now - getattr(self.bot, "start_time", now)
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}д {hours}ч {minutes}м {seconds}с"

        owner_mentions = []
        for uid in ALLOWED_USER_IDS:
            member = message.guild.get_member(uid)
            owner_mentions.append(member.mention if member else f"<@{uid}>")

        embed = disnake.Embed(
            title=f"<:airdrop:1390972469073936414> Штаб зафиксировал ваше имя — {message.author.display_name}!",
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

        try:
            await message.channel.send(embed=embed)
        except disnake.Forbidden:
            # Нет прав на отправку сообщений в этот канал
            pass
        except Exception as e:
            print(f"Error sending embed in ResponseToCall: {e}")

        